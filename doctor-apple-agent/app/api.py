"""Local REST API designed for later Copilot Studio custom-connector use."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from app.agnes import extract_chit
from app.clinic import (
    build_prefill,
    compare_coverage,
    extract_document,
    match_eligibility,
)
from app.config import settings
from app.database import (
    DuplicateRecord,
    StoreError,
    get_store,
    prepare_user,
    seed_patients,
)
from app.security import (
    create_token,
    decode_token,
    hash_password,
    mask_identifier,
    normalize_email,
    normalize_identifier,
    verify_password,
)

router = APIRouter(prefix="/doctor-apple", tags=["Doctor Apple"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: Literal["patient", "staff", "tpa"]


class RegistrationRequest(BaseModel):
    identifier: str
    insurer_code: str
    requested_tests: list[str] = Field(default_factory=list)
    form_type: Literal["general", "occupational"] = "general"


def current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return decode_token(
            authorization.removeprefix("Bearer "), settings.token_secret
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


CurrentUser = Annotated[dict[str, Any], Depends(current_user)]


def staff_user(user: CurrentUser) -> dict[str, Any]:
    if user.get("role") != "staff":
        raise HTTPException(status_code=403, detail="Staff role required")
    return user


StaffUser = Annotated[dict[str, Any], Depends(staff_user)]


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok" if get_store().health() else "degraded",
        "mongodb": get_store().health(),
        "agnes_configured": bool(settings.agnes_api_key),
        "offline_mode": settings.offline_mode,
    }


@router.post("/auth/register", status_code=201)
def register(credentials: Credentials) -> dict[str, str]:
    try:
        user = prepare_user(
            credentials.email,
            hash_password(credentials.password),
            credentials.role,
        )
        get_store().insert("users", user)
    except DuplicateRecord as exc:
        raise HTTPException(status_code=409, detail="Account already exists") from exc
    except StoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "created"}


@router.post("/auth/login")
def login(credentials: Credentials) -> dict[str, str]:
    try:
        user = get_store().find_one(
            "users", {"email_normalized": normalize_email(credentials.email)}
        )
    except StoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if (
        not user
        or user.get("role") != credentials.role
        or not verify_password(credentials.password, user["password_hash"])
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": create_token(
            user["email_normalized"], user["role"], settings.token_secret
        ),
        "token_type": "bearer",
    }


@router.post("/admin/seed")
def seed(user: StaffUser) -> dict[str, int]:
    del user
    csv_path = (
        Path(__file__).parents[2]
        / "Data"
        / "Data"
        / "patient_registration_synthetic.csv"
    )
    return {"patients_seeded": seed_patients(get_store(), csv_path)}


@router.post("/documents/extract")
async def process_document(
    file: Annotated[UploadFile, File()], user: CurrentUser
) -> dict[str, Any]:
    del user
    try:
        content = await file.read()
        text = extract_document(Path(file.filename or "upload").name, content)
        extraction = await extract_chit(text)
        result = extraction.model_dump()
        result["requires_manual_review"] = extraction.confidence < 0.8 or bool(
            extraction.discrepancies
        )
        if extraction.identifier:
            result["identifier"] = mask_identifier(extraction.identifier)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/registrations", status_code=201)
def create_registration(
    request: RegistrationRequest, user: CurrentUser
) -> dict[str, Any]:
    patient = get_store().find_one(
        "patients", {"identifier_normalized": normalize_identifier(request.identifier)}
    )
    if not patient:
        raise HTTPException(
            status_code=404, detail="Patient not found; manual registration required"
        )
    eligibility = match_eligibility(
        request.insurer_code,
        str(patient.get("Date of Birth (DD/MM/YY)", "")),
        str(patient.get("Sex", "")),
    )
    coverage = compare_coverage(request.requested_tests, eligibility["covered_tests"])
    allergy = str(patient.get("Drug Allergy", "")).strip()
    has_allergy = bool(allergy and allergy.casefold() not in {"none", "nil"})
    review = eligibility["requires_manual_review"] or bool(coverage["uncovered"])
    document = {
        "owner_email": user["sub"],
        "patient_identifier": normalize_identifier(request.identifier),
        "patient_identifier_masked": mask_identifier(request.identifier),
        "eligibility": eligibility,
        "coverage": coverage,
        "prefill": build_prefill(patient, request.form_type),
        "allergy_warning": f"WARNING — DRUG ALLERGY: {allergy}"
        if has_allergy
        else None,
        "status": "manual_review" if review else "pending_identity_verification",
        "identity_verified_in_person": False,
        "created_at": datetime.now(UTC),
    }
    registration_id = get_store().insert("registrations", document)
    get_store().insert(
        "audit_events",
        {
            "action": "registration_created",
            "registration_id": registration_id,
            "actor": user["sub"],
            "patient": document["patient_identifier_masked"],
            "created_at": datetime.now(UTC),
        },
    )
    return {
        "registration_id": registration_id,
        **{
            key: value for key, value in document.items() if key != "patient_identifier"
        },
    }


@router.post("/registrations/{registration_id}/staff-verify")
def staff_verify(registration_id: str, user: StaffUser) -> dict[str, str]:
    updated = get_store().update_one(
        "registrations",
        {"_id": registration_id},
        {
            "identity_verified_in_person": True,
            "status": "approved",
            "verified_by": user["sub"],
            "verified_at": datetime.now(UTC),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found"
        )
    get_store().insert(
        "audit_events",
        {
            "action": "identity_verified_in_person",
            "registration_id": registration_id,
            "actor": user["sub"],
            "created_at": datetime.now(UTC),
        },
    )
    return {"status": "approved"}

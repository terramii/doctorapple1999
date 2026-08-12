"""Local REST API designed for later Copilot Studio custom-connector use."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from app.agnes import extract_chit, extract_chit_image
from app.clinic import (
    build_prefill,
    compare_coverage,
    extract_document,
    match_eligibility,
)
from app.config import settings
from app.database import StoreError, get_store, seed_patients
from app.security import (
    create_token,
    decode_token,
    mask_identifier,
    normalize_email,
    normalize_identifier,
)

router = APIRouter(prefix="/doctor-apple", tags=["Doctor Apple"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["patient", "staff", "tpa"]


class RegistrationRequest(BaseModel):
    identifier: str
    insurer_code: str
    requested_tests: list[str] = Field(default_factory=list)
    form_type: Literal["general", "occupational"] = "general"
    appointment_type: Literal["prebooked", "walkin"] = "prebooked"
    appointment_date: str | None = None
    appointment_time: str | None = None
    questionnaire_answers: dict[str, Any] = Field(default_factory=dict)


class ClaimRequest(BaseModel):
    total_amount: float = Field(gt=0, le=100_000)
    performed_tests: list[str] = Field(default_factory=list)


TPA_LIMITS = {
    "MRDEB": 250.0,
    "BLPHS": 500.0,
    "BLPDE": 500.0,
    "MOL0199VME": 300.0,
    "NSTNBU": 200.0,
    "EVWME": 300.0,
    "EVWPA": 300.0,
}


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


@router.post("/auth/login")
def login(credentials: Credentials) -> dict[str, str]:
    expected_passwords = {
        "patient": settings.patient_password,
        "staff": settings.staff_password,
        "tpa": settings.tpa_password,
    }
    try:
        user = get_store().find_one(
            "users", {"email_normalized": normalize_email(credentials.email)}
        )
    except StoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if (
        not user
        or user.get("role") != credentials.role
        or credentials.password != expected_passwords[credentials.role]
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
        filename = Path(file.filename or "upload").name
        if (file.content_type or "").startswith("image/"):
            if not content or len(content) > 8 * 1024 * 1024:
                raise ValueError("Image must be non-empty and no larger than 8 MB")
            extraction = await extract_chit_image(content, file.content_type or "image/jpeg")
        else:
            text = extract_document(filename, content)
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
    permitted_emails = {normalize_email(str(patient.get("Email", "")))}
    permitted_emails.update(
        normalize_email(str(response.get("Email Address", "")))
        for response in patient.get("questionnaires", {}).values()
        if response
    )
    if user.get("role") == "patient" and user["sub"] not in permitted_emails:
        raise HTTPException(status_code=403, detail="Patient record does not belong to this account")
    if request.insurer_code == "SELF_PAY":
        eligibility = {
            "insurer": "Self-pay",
            "package_code": "SELF_PAY",
            "package_name": "Standard clinic services",
            "covered_tests": [],
            "requires_manual_review": False,
        }
    else:
        eligibility = match_eligibility(
            request.insurer_code,
            str(patient.get("Date of Birth (DD/MM/YY)", "")),
            str(patient.get("Sex", "")),
        )
    coverage = compare_coverage(request.requested_tests, eligibility["covered_tests"])
    allergy = str(patient.get("Drug Allergy", "")).strip()
    has_allergy = bool(allergy and allergy.casefold() not in {"none", "nil"})
    review = eligibility["requires_manual_review"] or bool(coverage["uncovered"])
    questionnaire_answers = dict(request.questionnaire_answers)
    questionnaire_answers.update(
        {
            "Name": patient.get("Full Name", ""),
            "ID Number": patient.get("NRIC/FIN/Passport Number", ""),
            "Date of Birth": patient.get("Date of Birth (DD/MM/YY)", ""),
            "Gender": patient.get("Sex", ""),
        }
    )
    document = {
        "owner_email": user["sub"],
        "patient_identifier": normalize_identifier(request.identifier),
        "patient_identifier_masked": mask_identifier(request.identifier),
        "eligibility": eligibility,
        "coverage": coverage,
        "prefill": build_prefill(patient, request.form_type),
        "form_type": request.form_type,
        "questionnaire_answers": questionnaire_answers,
        "appointment_type": request.appointment_type,
        "appointment_date": request.appointment_date,
        "appointment_time": request.appointment_time,
        "allergy_warning": f"WARNING — DRUG ALLERGY: {allergy}"
        if has_allergy
        else None,
        "status": "manual_review" if review else "pending_identity_verification",
        "identity_verified_in_person": False,
        "created_at": datetime.now(UTC),
    }
    registration_id = get_store().insert("registrations", document)
    questionnaires = dict(patient.get("questionnaires", {}))
    questionnaires[request.form_type] = {
        **questionnaire_answers,
        "submitted_by": user["sub"],
        "submitted_at": datetime.now(UTC),
        "registration_id": registration_id,
    }
    get_store().update_one(
        "patients",
        {"identifier_normalized": normalize_identifier(request.identifier)},
        {"questionnaires": questionnaires},
    )
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
    get_store().insert(
        "audit_events",
        {
            "action": "questionnaire_submitted",
            "registration_id": registration_id,
            "form_type": request.form_type,
            "actor": user["sub"],
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


@router.post("/registrations/{registration_id}/submit-claim")
def submit_claim(
    registration_id: str, request: ClaimRequest, user: StaffUser
) -> dict[str, Any]:
    registration = get_store().find_one("registrations", {"_id": registration_id})
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    if not registration.get("identity_verified_in_person"):
        raise HTTPException(status_code=409, detail="Physical identity verification is required before claim submission")
    package_code = str(registration.get("eligibility", {}).get("package_code", ""))
    insurer_code = str(registration.get("eligibility", {}).get("insurer_code") or registration.get("eligibility", {}).get("code") or package_code)
    if package_code == "SELF_PAY":
        decision = "not_applicable"
        reasons = ["Self-pay visit: no insurance claim is sent to a TPA"]
    else:
        uncovered = compare_coverage(request.performed_tests, registration.get("eligibility", {}).get("covered_tests", []))["uncovered"]
        limit = TPA_LIMITS.get(insurer_code)
        if registration.get("status") == "manual_review" or uncovered or limit is None:
            decision = "manual_review"
            reasons = []
            if registration.get("status") == "manual_review":
                reasons.append("Eligibility or document discrepancies require assessor review")
            if uncovered:
                reasons.append(f"Uncovered services: {', '.join(uncovered)}")
            if limit is None:
                reasons.append("No automated payout limit is configured for this policy")
        elif request.total_amount > limit:
            decision = "rejected"
            reasons = [f"Claim amount ${request.total_amount:.2f} exceeds the ${limit:.2f} policy limit"]
        else:
            decision = "approved"
            reasons = ["Identity verified in person", "Policy and package are recognised", "All performed services are covered", f"Claim amount is within the ${limit:.2f} policy limit"]
    status_by_decision = {"approved": "tpa_auto_approved", "rejected": "tpa_auto_rejected", "manual_review": "pending_manual_tpa_review", "not_applicable": "self_pay_completed"}
    status_value = status_by_decision[decision]
    get_store().update_one("registrations", {"_id": registration_id}, {"status": status_value, "claim": {"decision": decision, "reasons": reasons, "total_amount": request.total_amount, "performed_tests": request.performed_tests, "submitted_by": user["sub"], "decided_at": datetime.now(UTC)}})
    get_store().insert("audit_events", {"action": "tpa_claim_decided", "registration_id": registration_id, "decision": decision, "reasons": reasons, "actor": user["sub"], "created_at": datetime.now(UTC)})
    return {"status": status_value, "decision": decision, "reasons": reasons}

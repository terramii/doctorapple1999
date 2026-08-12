"""ADK tools that expose only deterministic administrative operations."""

from __future__ import annotations

from typing import Any

from app.clinic import build_prefill, compare_coverage, match_eligibility
from app.database import get_store
from app.security import mask_identifier, normalize_identifier


def find_patient(identifier: str) -> dict[str, Any]:
    """Find a synthetic patient by exact NRIC, FIN, or passport identifier."""
    patient = get_store().find_one(
        "patients", {"identifier_normalized": normalize_identifier(identifier)}
    )
    if not patient:
        return {"status": "manual_review", "reason": "Patient not found"}
    safe_patient = dict(patient)
    safe_patient["NRIC/FIN/Passport Number"] = mask_identifier(identifier)
    safe_patient.pop("_id", None)
    return {"status": "success", "patient": safe_patient}


def resolve_eligibility(
    insurer_code: str, date_of_birth: str, gender: str
) -> dict[str, Any]:
    """Resolve package eligibility using authoritative local rules."""
    return match_eligibility(insurer_code, date_of_birth, gender)


def check_requested_tests(
    requested_tests: list[str], covered_tests: list[str]
) -> dict[str, Any]:
    """Compare requested tests with the resolved package and flag uncovered items."""
    result = compare_coverage(requested_tests, covered_tests)
    result["requires_manual_review"] = bool(result["uncovered"])
    return result


def generate_questionnaire_prefill(identifier: str, form_type: str) -> dict[str, Any]:
    """Generate a questionnaire prefill for a matched synthetic patient."""
    patient = get_store().find_one(
        "patients", {"identifier_normalized": normalize_identifier(identifier)}
    )
    if not patient:
        return {"status": "manual_review", "reason": "Patient not found"}
    if form_type not in {"general", "occupational"}:
        return {"status": "manual_review", "reason": "Unknown form type"}
    saved_response = patient.get("questionnaires", {}).get(form_type)
    return {
        "status": "success",
        "prefill": build_prefill(patient, form_type),
        "saved_response": saved_response,
        "response_available": saved_response is not None,
        "requires_manual_review": bool(patient.get("questionnaire_discrepancies")),
        "discrepancies": patient.get("questionnaire_discrepancies", []),
    }

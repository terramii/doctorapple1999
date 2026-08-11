from datetime import date

from app.clinic import calculate_age, compare_coverage, match_eligibility
from app.security import (
    create_token,
    decode_token,
    hash_password,
    mask_identifier,
    verify_password,
)


def test_age_uses_birthday_and_two_digit_year() -> None:
    assert calculate_age("25/01/85", date(2026, 1, 24)) == 40
    assert calculate_age("25/01/85", date(2026, 1, 25)) == 41


def test_package_boundaries() -> None:
    assert match_eligibility("BLPHS", "31/12/87")["package_code"] == "WELL1"
    assert match_eligibility("BLPHS", "31/12/67")["package_code"] == "WELL2"
    assert match_eligibility("BLPHS", "31/12/66")["package_code"] == "WELL3"
    assert match_eligibility("MOL0199VME", "31/12/02")["package_code"] == "PEE225"
    assert match_eligibility("MOL0199VME", "31/12/01")["package_code"] == "PEE226"


def test_unknown_code_and_uncovered_test_require_review() -> None:
    assert match_eligibility("NOTREAL", "01/01/90")["requires_manual_review"] is True
    comparison = compare_coverage(["Resting ECG", "Dental"], ["Resting ECG"])
    assert comparison == {"covered": ["Resting ECG"], "uncovered": ["Dental"]}


def test_password_token_and_identifier_security() -> None:
    encoded = hash_password("safe-password-123")
    assert "safe-password-123" not in encoded
    assert verify_password("safe-password-123", encoded)
    assert not verify_password("wrong-password", encoded)
    token = create_token("patient@example.com", "patient", "test-secret")
    assert decode_token(token, "test-secret")["role"] == "patient"
    assert mask_identifier("S8536477Z") == "S******7Z"

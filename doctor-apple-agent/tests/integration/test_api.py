from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router
from app.database import MemoryStore, prepare_user, set_store
from app.security import hash_password


def client_with_data() -> TestClient:
    store = MemoryStore()
    store.insert(
        "users",
        prepare_user("staff@example.com", hash_password("StaffApple"), "staff"),
    )
    store.insert(
        "users", prepare_user("amir@example.com", hash_password("PatientApple"), "patient")
    )
    store.insert(
        "users", prepare_user("tpa@example.com", hash_password("placeholder"), "tpa")
    )
    store.upsert_patient(
        {
            "Full Name": "Loh Amir",
            "NRIC/FIN/Passport Number": "S8536477Z",
            "Sex": "M",
            "Date of Birth (DD/MM/YY)": "25/01/85",
            "Drug Allergy": "Sulfa drugs",
            "Email": "amir@example.com",
            "Contact - Mobile": "91234567",
            "Address": "Synthetic address",
            "Postal Code": "123456",
        }
    )
    set_store(store)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_patient_login_and_safe_prebooked_registration() -> None:
    client = client_with_data()
    credentials = {
        "email": "amir@example.com",
        "password": "PatientApple",
        "role": "patient",
    }
    login = client.post("/doctor-apple/auth/login", json=credentials)
    token = login.json()["access_token"]
    result = client.post(
        "/doctor-apple/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "identifier": "S8536477Z",
            "insurer_code": "BLPHS",
            "requested_tests": ["Dental"],
            "questionnaire_answers": {
                "Name": "Tampered Name",
                "Date of Birth": "01/01/01",
                "Smoking Status": "No",
            },
        },
    )
    assert result.status_code == 201
    body = result.json()
    assert body["patient_identifier_masked"] == "S******7Z"
    assert body["allergy_warning"] == "WARNING — DRUG ALLERGY: Sulfa drugs"
    assert body["status"] == "manual_review"
    assert body["identity_verified_in_person"] is False
    assert "patient_identifier" not in body
    assert body["appointment_type"] == "prebooked"
    store = __import__("app.database", fromlist=["get_store"]).get_store()
    patient = store.find_one("patients", {"identifier_normalized": "S8536477Z"})
    assert patient["questionnaires"]["general"]["registration_id"] == body["registration_id"]
    assert patient["questionnaires"]["general"]["submitted_by"] == "amir@example.com"
    assert patient["questionnaires"]["general"]["Name"] == "Loh Amir"
    assert patient["questionnaires"]["general"]["Date of Birth"] == "25/01/85"
    assert patient["questionnaires"]["general"]["Smoking Status"] == "No"


def test_patient_cannot_submit_for_another_patient() -> None:
    client = client_with_data()
    store = __import__("app.database", fromlist=["get_store"]).get_store()
    store.upsert_patient(
        {
            "Full Name": "Other Patient",
            "NRIC/FIN/Passport Number": "S1234567A",
            "Email": "other@example.com",
            "Date of Birth (DD/MM/YY)": "01/01/90",
            "Sex": "F",
            "questionnaires": {"general": None, "occupational": None},
        }
    )
    token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "amir@example.com", "password": "PatientApple", "role": "patient"},
    ).json()["access_token"]
    response = client.post(
        "/doctor-apple/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "identifier": "S1234567A",
            "insurer_code": "SELF_PAY",
            "form_type": "general",
            "appointment_type": "walkin",
            "questionnaire_answers": {"Smoking Status": "No"},
        },
    )
    assert response.status_code == 403


def test_patient_cannot_mark_identity_verified() -> None:
    client = client_with_data()
    credentials = {
        "email": "amir@example.com",
        "password": "PatientApple",
        "role": "patient",
    }
    token = client.post("/doctor-apple/auth/login", json=credentials).json()[
        "access_token"
    ]
    response = client.post(
        "/doctor-apple/registrations/1/staff-verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_all_roles_require_their_shared_password() -> None:
    client = client_with_data()
    for email, password, role in (
        ("amir@example.com", "PatientApple", "patient"),
        ("staff@example.com", "StaffApple", "staff"),
        ("tpa@example.com", "TPAApple", "tpa"),
    ):
        response = client.post(
            "/doctor-apple/auth/login",
            json={"email": email, "password": password, "role": role},
        )
        assert response.status_code == 200
        wrong = client.post(
            "/doctor-apple/auth/login",
            json={"email": email, "password": "WrongApple", "role": role},
        )
        assert wrong.status_code == 401


def test_tpa_claim_requires_identity_then_auto_approves_with_reasons() -> None:
    client = client_with_data()
    patient_token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "amir@example.com", "password": "PatientApple", "role": "patient"},
    ).json()["access_token"]
    staff_token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "staff@example.com", "password": "StaffApple", "role": "staff"},
    ).json()["access_token"]
    registration = client.post(
        "/doctor-apple/registrations",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={
            "identifier": "S8536477Z",
            "insurer_code": "BLPHS",
            "form_type": "general",
            "appointment_type": "prebooked",
            "questionnaire_answers": {},
        },
    ).json()
    registration_id = registration["registration_id"]
    claim = {"total_amount": 250, "performed_tests": []}
    blocked = client.post(
        f"/doctor-apple/registrations/{registration_id}/submit-claim",
        headers={"Authorization": f"Bearer {staff_token}"},
        json=claim,
    )
    assert blocked.status_code == 409
    assert client.post(
        f"/doctor-apple/registrations/{registration_id}/staff-verify",
        headers={"Authorization": f"Bearer {staff_token}"},
    ).status_code == 200
    approved = client.post(
        f"/doctor-apple/registrations/{registration_id}/submit-claim",
        headers={"Authorization": f"Bearer {staff_token}"},
        json=claim,
    )
    assert approved.status_code == 200
    assert approved.json()["decision"] == "approved"
    assert approved.json()["status"] == "tpa_auto_approved"
    assert len(approved.json()["reasons"]) == 4


def test_tpa_auto_rejects_claim_above_policy_limit() -> None:
    client = client_with_data()
    patient_token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "amir@example.com", "password": "PatientApple", "role": "patient"},
    ).json()["access_token"]
    staff_token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "staff@example.com", "password": "StaffApple", "role": "staff"},
    ).json()["access_token"]
    registration_id = client.post(
        "/doctor-apple/registrations",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={"identifier": "S8536477Z", "insurer_code": "BLPHS", "questionnaire_answers": {}},
    ).json()["registration_id"]
    client.post(
        f"/doctor-apple/registrations/{registration_id}/staff-verify",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    rejected = client.post(
        f"/doctor-apple/registrations/{registration_id}/submit-claim",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"total_amount": 501, "performed_tests": []},
    )
    assert rejected.json()["decision"] == "rejected"
    assert "exceeds" in rejected.json()["reasons"][0]

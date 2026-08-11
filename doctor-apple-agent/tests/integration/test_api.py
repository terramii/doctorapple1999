from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router
from app.database import MemoryStore, prepare_user, set_store
from app.security import hash_password


def client_with_data() -> TestClient:
    store = MemoryStore()
    store.insert(
        "users",
        prepare_user("staff@example.com", hash_password("staff-password-123"), "staff"),
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


def test_signup_login_and_safe_registration() -> None:
    client = client_with_data()
    credentials = {
        "email": "patient@example.com",
        "password": "patient-password-123",
        "role": "patient",
    }
    assert (
        client.post("/doctor-apple/auth/register", json=credentials).status_code == 201
    )
    login = client.post("/doctor-apple/auth/login", json=credentials)
    token = login.json()["access_token"]
    result = client.post(
        "/doctor-apple/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "identifier": "S8536477Z",
            "insurer_code": "BLPHS",
            "requested_tests": ["Dental"],
        },
    )
    assert result.status_code == 201
    body = result.json()
    assert body["patient_identifier_masked"] == "S******7Z"
    assert body["allergy_warning"] == "WARNING — DRUG ALLERGY: Sulfa drugs"
    assert body["status"] == "manual_review"
    assert body["identity_verified_in_person"] is False
    assert "patient_identifier" not in body


def test_patient_cannot_mark_identity_verified() -> None:
    client = client_with_data()
    credentials = {
        "email": "patient2@example.com",
        "password": "patient-password-123",
        "role": "patient",
    }
    client.post("/doctor-apple/auth/register", json=credentials)
    token = client.post("/doctor-apple/auth/login", json=credentials).json()[
        "access_token"
    ]
    response = client.post(
        "/doctor-apple/registrations/1/staff-verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

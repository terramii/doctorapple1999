from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agnes import ChitExtraction
from app.api import QUESTIONNAIRE_FIELDS, router
from app.config import settings
from app.database import MemoryStore, prepare_user, set_store
from app.security import hash_password


def client_with_data() -> TestClient:
    store = MemoryStore()
    store.insert(
        "users",
        prepare_user("staff@example.com", hash_password("staff-password-123"), "staff"),
    )
    for email in ("amir@example.com", "patient2@example.com"):
        store.insert(
            "users",
            prepare_user(email, hash_password(settings.patient_password), "patient"),
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


def test_seeded_patient_login_and_safe_registration() -> None:
    client = client_with_data()
    credentials = {
        "email": "amir@example.com",
        "password": settings.patient_password,
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
            "questionnaire_answers": dict.fromkeys(
                QUESTIONNAIRE_FIELDS["general"], "No"
            ),
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
        "password": settings.patient_password,
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


def complete_general_answers() -> dict[str, str]:
    return dict.fromkeys(QUESTIONNAIRE_FIELDS["general"], "No")


def test_patient_signup_creates_linked_profile_and_login() -> None:
    client = client_with_data()
    payload = {
        "full_name": "New Patient", "identifier": "S1111111A", "sex": "F",
        "nationality": "Singaporean", "date_of_birth": "01/02/90",
        "address": "1 Test Street", "postal_code": "123456", "contact_home": "",
        "contact_office": "", "contact_mobile": "81234567", "email": "new@example.com",
        "drug_allergy": "None", "password": settings.patient_password,
    }
    assert client.post("/doctor-apple/auth/register", json=payload).status_code == 201
    login = client.post(
        "/doctor-apple/auth/login",
        json={"email": "new@example.com", "password": settings.patient_password, "role": "patient"},
    )
    assert login.status_code == 200
    profile = client.get(
        "/doctor-apple/patients/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert profile.json()["Full Name"] == "New Patient"


def test_questionnaire_is_required_and_appointments_are_retained() -> None:
    client = client_with_data()
    token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "amir@example.com", "password": settings.patient_password, "role": "patient"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    incomplete = client.post(
        "/doctor-apple/registrations",
        headers=headers,
        json={"identifier": "S8536477Z", "insurer_code": "SELF_PAY", "questionnaire_answers": {}},
    )
    assert incomplete.status_code == 422
    for day in ("20/08/2026", "21/08/2026"):
        response = client.post(
            "/doctor-apple/registrations",
            headers=headers,
            json={
                "identifier": "S8536477Z", "insurer_code": "SELF_PAY",
                "appointment_date": day, "questionnaire_answers": complete_general_answers(),
            },
        )
        assert response.status_code == 201
    history = client.get("/doctor-apple/appointments", headers=headers)
    assert len(history.json()) == 2


def test_uploaded_chit_is_matched_to_authenticated_patient(monkeypatch) -> None:
    client = client_with_data()

    async def fake_extract(_: str) -> ChitExtraction:
        return ChitExtraction(
            full_name="Loh Amir", identifier="S8536477Z", date_of_birth="25/01/85",
            gender="M", insurer_code="BLPHS", requested_tests=["Full Blood Count"],
            confidence=0.99,
        )

    monkeypatch.setattr("app.api.extract_chit", fake_extract)
    token = client.post(
        "/doctor-apple/auth/login",
        json={"email": "amir@example.com", "password": settings.patient_password, "role": "patient"},
    ).json()["access_token"]
    response = client.post(
        "/doctor-apple/documents/extract",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("referral.txt", b"synthetic referral", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["patient_matched"] is True
    assert response.json()["eligibility"]["package_code"] == "WELL2"

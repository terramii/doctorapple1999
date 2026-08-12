"""MongoDB persistence with an explicit in-memory test mode."""

from __future__ import annotations

import csv
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import settings
from app.security import normalize_email, normalize_identifier


class StoreError(RuntimeError):
    pass


class DuplicateRecord(StoreError):
    pass


class MongoStore:
    def __init__(self) -> None:
        self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1500)
        self.db = self.client[settings.mongodb_database]

    def initialize(self) -> None:
        self.client.admin.command("ping")
        self.db.users.create_index([("email_normalized", ASCENDING)], unique=True)
        self.db.patients.create_index(
            [("identifier_normalized", ASCENDING)], unique=True
        )
        self.db.registrations.create_index([("owner_email", ASCENDING)])

    def health(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def insert(self, collection: str, document: dict[str, Any]) -> str:
        try:
            result = self.db[collection].insert_one(deepcopy(document))
            return str(result.inserted_id)
        except DuplicateKeyError as exc:
            raise DuplicateRecord("Record already exists") from exc
        except PyMongoError as exc:
            raise StoreError("Database operation failed") from exc

    def find_one(self, collection: str, query: dict[str, Any]) -> dict[str, Any] | None:
        try:
            result = self.db[collection].find_one(query)
            if result:
                result["_id"] = str(result["_id"])
            return result
        except PyMongoError as exc:
            raise StoreError("Database operation failed") from exc

    def update_one(
        self, collection: str, query: dict[str, Any], update: dict[str, Any]
    ) -> bool:
        try:
            if isinstance(query.get("_id"), str) and ObjectId.is_valid(query["_id"]):
                query = {**query, "_id": ObjectId(query["_id"])}
            return (
                self.db[collection].update_one(query, {"$set": update}).modified_count
                == 1
            )
        except PyMongoError as exc:
            raise StoreError("Database operation failed") from exc

    def upsert_patient(self, patient: dict[str, Any]) -> None:
        identifier = normalize_identifier(str(patient["NRIC/FIN/Passport Number"]))
        copy = deepcopy(patient)
        copy["identifier_normalized"] = identifier
        self.db.patients.update_one(
            {"identifier_normalized": identifier}, {"$set": copy}, upsert=True
        )


class MemoryStore:
    def __init__(self) -> None:
        self.collections: dict[str, list[dict[str, Any]]] = {
            "users": [],
            "patients": [],
            "registrations": [],
            "audit_events": [],
        }
        self.lock = threading.Lock()

    def initialize(self) -> None:
        return None

    def health(self) -> bool:
        return True

    def insert(self, collection: str, document: dict[str, Any]) -> str:
        with self.lock:
            if collection == "users" and self.find_one(
                "users", {"email_normalized": document["email_normalized"]}
            ):
                raise DuplicateRecord("Record already exists")
            copy = deepcopy(document)
            copy["_id"] = str(len(self.collections[collection]) + 1)
            self.collections[collection].append(copy)
            return copy["_id"]

    def find_one(self, collection: str, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.collections[collection]:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None

    def update_one(
        self, collection: str, query: dict[str, Any], update: dict[str, Any]
    ) -> bool:
        with self.lock:
            for document in self.collections[collection]:
                if all(document.get(key) == value for key, value in query.items()):
                    document.update(deepcopy(update))
                    return True
        return False

    def upsert_patient(self, patient: dict[str, Any]) -> None:
        identifier = normalize_identifier(str(patient["NRIC/FIN/Passport Number"]))
        copy = deepcopy(patient)
        copy["identifier_normalized"] = identifier
        existing = self.find_one("patients", {"identifier_normalized": identifier})
        if existing:
            self.update_one("patients", {"identifier_normalized": identifier}, copy)
        else:
            self.insert("patients", copy)


_store: MongoStore | MemoryStore | None = None


def get_store() -> MongoStore | MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore() if settings.offline_mode else MongoStore()
    return _store


def set_store(store: MongoStore | MemoryStore) -> None:
    global _store
    _store = store


def seed_patients(store: MongoStore | MemoryStore, csv_path: Path) -> int:
    questionnaire_files = {
        "general": csv_path.with_name("general_health_questionnaire_mock_patients.csv"),
        "occupational": csv_path.with_name(
            "occupational_health_questionnaire_mock_patients.csv"
        ),
    }
    questionnaires: dict[str, dict[str, dict[str, Any]]] = {
        form_type: {} for form_type in questionnaire_files
    }
    for form_type, questionnaire_path in questionnaire_files.items():
        with questionnaire_path.open(encoding="utf-8-sig", newline="") as handle:
            for response in csv.DictReader(handle):
                identifier = normalize_identifier(response.get("ID Number", ""))
                if identifier:
                    questionnaires[form_type][identifier] = response
    count = 0
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        for patient in csv.DictReader(handle):
            identifier = normalize_identifier(
                patient["NRIC/FIN/Passport Number"]
            )
            patient["questionnaires"] = {
                form_type: responses.get(identifier)
                for form_type, responses in questionnaires.items()
            }
            patient["questionnaire_discrepancies"] = [
                f"{form_type} questionnaire email differs from registration email"
                for form_type, response in patient["questionnaires"].items()
                if response
                and normalize_email(response.get("Email Address", ""))
                != normalize_email(patient.get("Email", ""))
            ]
            store.upsert_patient(patient)
            count += 1
    registered_ids = {
        normalize_identifier(patient["NRIC/FIN/Passport Number"])
        for patient in store.collections["patients"]
    } if isinstance(store, MemoryStore) else {
        normalize_identifier(row["NRIC/FIN/Passport Number"])
        for row in csv.DictReader(csv_path.open(encoding="utf-8-sig", newline=""))
    }
    for form_type, responses in questionnaires.items():
        for identifier, response in responses.items():
            if identifier in registered_ids:
                continue
            patient = {
                "Full Name": response.get("Name", ""),
                "NRIC/FIN/Passport Number": response.get("ID Number", ""),
                "Sex": response.get("Gender", ""),
                "Nationality": "",
                "Date of Birth (DD/MM/YY)": response.get("Date of Birth", ""),
                "Address": response.get("Address", ""),
                "Postal Code": response.get("Postal Code", ""),
                "Contact - Home": "",
                "Contact - Office": "",
                "Contact - Mobile": response.get("Phone Number", ""),
                "Email": response.get("Email Address", ""),
                "Drug Allergy": response.get("Drug Allergy Details", ""),
                "questionnaires": {"general": None, "occupational": None},
                "questionnaire_discrepancies": [],
                "registration_source": f"{form_type}_questionnaire",
            }
            patient["questionnaires"][form_type] = response
            store.upsert_patient(patient)
            registered_ids.add(identifier)
            count += 1
    return count


def prepare_user(email: str, password_hash: str, role: str) -> dict[str, Any]:
    return {
        "email": email.strip(),
        "email_normalized": normalize_email(email),
        "password_hash": password_hash,
        "role": role,
    }

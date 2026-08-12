"""Seed synthetic patients and role accounts for the local prototype."""

import csv
from pathlib import Path

from app.config import settings
from app.database import get_store, prepare_user, seed_patients
from app.security import hash_password, normalize_email


def main() -> None:
    store = get_store()
    store.initialize()
    csv_path = (
        Path(__file__).parents[2]
        / "Data"
        / "Data"
        / "patient_registration_synthetic.csv"
    )
    count = seed_patients(store, csv_path)
    accounts = [
        ("staff@doctorapple.com", settings.staff_password, "staff"),
        ("tpa@doctorapple.com", settings.tpa_password, "tpa"),
    ]
    account_files = (
        (csv_path, "Email"),
        (csv_path.with_name("general_health_questionnaire_mock_patients.csv"), "Email Address"),
        (csv_path.with_name("occupational_health_questionnaire_mock_patients.csv"), "Email Address"),
    )
    for account_path, email_column in account_files:
        with account_path.open(encoding="utf-8-sig", newline="") as handle:
            accounts.extend(
                (email, settings.patient_password, "patient")
                for row in csv.DictReader(handle)
                if (email := row.get(email_column, "").strip())
            )
    created = 0
    for email, password, role in accounts:
        if not store.find_one("users", {"email_normalized": normalize_email(email)}):
            store.insert("users", prepare_user(email, hash_password(password), role))
            created += 1
    print(f"Seeded {count} synthetic patients and created {created} role accounts.")


if __name__ == "__main__":
    main()

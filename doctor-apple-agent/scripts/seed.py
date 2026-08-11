"""Seed synthetic patients and a local staff account."""

import os
from pathlib import Path

from app.database import get_store, prepare_user, seed_patients
from app.security import hash_password


def main() -> None:
    email = os.getenv("STAFF_EMAIL", "staff@doctor-apple.local")
    password = os.getenv("STAFF_PASSWORD")
    if not password:
        raise SystemExit("Set STAFF_PASSWORD to at least 10 characters before seeding")
    store = get_store()
    store.initialize()
    csv_path = (
        Path(__file__).parents[2]
        / "Data"
        / "Data"
        / "patient_registration_synthetic.csv"
    )
    count = seed_patients(store, csv_path)
    if not store.find_one("users", {"email_normalized": email.casefold()}):
        store.insert("users", prepare_user(email, hash_password(password), "staff"))
    print(
        f"Seeded {count} synthetic patients and ensured staff account {email} exists."
    )


if __name__ == "__main__":
    main()

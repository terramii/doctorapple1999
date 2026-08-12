# Doctor Apple Agent

Local Hack4Health prototype for clinic pre-registration, synthetic patient lookup, eligibility/package matching, questionnaire prefill, and mandatory staff verification. Agnes AI performs schema-validated chit extraction; deterministic Python rules remain authoritative for coverage and billing decisions.

## Safety boundary

- Physical identity and e-card verification always happen in person.
- The agent provides administrative assistance only, never clinical advice.
- Unknown codes, conflicts, low confidence, and uncovered tests go to manual review.
- Full identifiers and secrets are excluded from logs and agent responses.
- This prototype uses synthetic data and is not production-ready for patient data.

## Local setup

1. Copy `.env.example` to `.env` and enter `AGNES_AI_API_KEY`. Do not commit `.env`.
2. Set `APP_TOKEN_SECRET` to a long random value.
3. Start MongoDB:

   ```powershell
   docker compose up -d mongodb
   ```

4. Install dependencies:

   ```powershell
   agents-cli install
   ```

5. Seed synthetic patients and the patient, staff, and TPA accounts:

   ```powershell
   uv run python scripts/seed.py
   ```

6. Start the local API and ADK playground:

   ```powershell
   uv run uvicorn app.fast_api_app:app --reload
   ```

Open `http://127.0.0.1:8000/docs` for the REST API and `http://127.0.0.1:8000/dev-ui/` for the agent UI.

## Key endpoints

- `POST /doctor-apple/auth/login`
- `POST /doctor-apple/documents/extract`
- `POST /doctor-apple/registrations`
- `POST /doctor-apple/registrations/{id}/staff-verify`
- `GET /doctor-apple/health`

All endpoints except health and login require a bearer token. Patient accounts use their synthetic-data email with `PatientApple`; the demo staff and TPA accounts are `staff@doctorapple.com` / `StaffApple` and `tpa@doctorapple.com` / `TPAApple`. Only staff tokens can seed data or confirm in-person identity verification.

## Offline tests

The deterministic suite does not call Agnes or require MongoDB:

```powershell
uv run pytest tests/unit tests/integration
agents-cli lint
```

Live agent runs require the Agnes key and a valid `AGNES_AI_MODEL` identifier:

```powershell
agents-cli run "Find the package for BLPHS, DOB 25/01/85, male"
```

## Architecture

```text
Patient/Staff UI
      |
FastAPI + ADK/A2A
      |---------------- Agnes API (chit extraction/orchestration)
      |---------------- MongoDB (accounts, patients, registrations, audit)
      `---------------- Deterministic clinic rules (eligibility/safety/prefill)
```

See [COPILOT_STUDIO.md](COPILOT_STUDIO.md) for the later Microsoft integration path.

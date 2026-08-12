# Doctor Apple

Clinic pre-registration prototype with three portals: **Patient**, **Clinic Staff**, and **TPA Assessor**. Agnes AI extracts medical-chit details; deterministic rules handle eligibility, coverage, questionnaire prefill, allergy warnings, and staff identity-verification gates.

## Hack4Health submission

- Required technical-track write-up: [TECHNICAL_TRACK_SUBMISSION.md](TECHNICAL_TRACK_SUBMISSION.md)
- Mandatory-field and judging-evidence audit: [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)

The submission still contains clearly marked placeholders for institution, team members, and contact person; complete those fields and verify the exported PDF stays within four pages before submitting.

## Local setup (Windows)

### 1. Install prerequisites

- [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Install and start [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) (recommended for MongoDB)

### 2. Configure the app

```powershell
Set-Location doctor-apple-agent
Copy-Item .env.example .env
uv sync
```

Edit `.env` and add your Agnes key:

```env
AGNES_AI_API_KEY=your_key
APP_TOKEN_SECRET=your_random_secret
```

Generate the token secret with:

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes)
```

### 3. Start MongoDB

```powershell
docker compose up -d mongodb
```

This starts MongoDB at `mongodb://localhost:27017`. To install it without Docker, follow the [MongoDB Community Windows guide](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-windows/) and keep the same URI in `.env`.

### 4. Seed synthetic data

```powershell
$env:STAFF_PASSWORD='choose-a-strong-password'
uv run python scripts/seed.py
```

Default staff email: `staff@doctor-apple.local`.

### 5. Run locally

```powershell
uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000
```

Open:

- App: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

Stop the server with `Ctrl+C`; stop MongoDB with `docker compose down`.

## Tests

```powershell
uv run pytest tests/unit tests/integration -q
uv run python scripts/local_eval.py
```

> Synthetic-data hackathon prototype only. Physical identity and e-card verification must remain in person.

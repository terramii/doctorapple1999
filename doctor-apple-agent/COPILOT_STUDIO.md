# Microsoft Copilot Studio Integration Guide

The local prototype already exposes the stable HTTP actions needed by Copilot Studio. Keep Agnes, MongoDB, passwords, and clinic rules behind this API; do not reproduce sensitive logic inside conversational prompts.

## 1. Prepare a hosted backend

After prototype validation, deploy the FastAPI service to an approved HTTPS host. Configure secrets in the host's secret manager:

- `AGNES_AI_API_KEY`
- `AGNES_AI_BASE_URL=https://apihub.agnes-ai.com/v1`
- `AGNES_AI_MODEL`
- `MONGODB_URI`
- `MONGODB_DATABASE`
- `APP_TOKEN_SECRET`

Use an allowlist for Copilot origins and add production encryption, retention, consent, monitoring, and PDPA controls before using real patient data.

## 2. Export the OpenAPI document

With the service running, download:

```text
https://YOUR_HOST/openapi.json
```

The Doctor Apple operations are grouped under the `Doctor Apple` tag. Give every production operation a stable `operationId` before importing if your connector governance requires fixed action names.

## 3. Create a custom connector

1. In Power Apps or Copilot Studio, open **Custom connectors**.
2. Choose **New custom connector → Import an OpenAPI file**.
3. Import the service's `openapi.json`.
4. Set the HTTPS host and base path.
5. Configure bearer authentication or replace the prototype token flow with Microsoft Entra ID for production.
6. Test health, login, document extraction, registration creation, and staff verification separately.

## 4. Add actions to the copilot

Add connector actions for:

- Register/sign in patient
- Extract uploaded chit
- Create pending registration
- Retrieve review status (add a read endpoint before production)
- Staff correction/approval

Require explicit staff authentication for `staff-verify`. A phrase such as “I verified the patient” must never substitute for an authorized API call by a staff identity.

## 5. Topic and orchestration design

Recommended topic flow:

1. Obtain patient consent and authenticate.
2. Capture the chit or walk-in details.
3. Call document extraction.
4. Show extracted fields for confirmation.
5. Create a pending registration.
6. If the response is `manual_review`, route to staff and show the reason.
7. Otherwise, ask the patient to complete the prefilled questionnaire.
8. At the clinic counter, staff inspect the physical ID/e-card and invoke `staff-verify`.

## 6. Data-loss prevention and governance

- Configure Copilot Studio data policies so the connector cannot send health data to unapproved connectors.
- Mask NRIC/FIN/passport identifiers in conversation transcripts and telemetry.
- Use environment-specific connector references for development, test, and production.
- Retain the API audit trail for every correction and approval.
- Add rate limiting, malware scanning for uploads, encrypted storage, and formal threat/privacy reviews before production.

## 7. Migration boundary

Copilot Studio becomes the conversational front end and workflow coordinator. Doctor Apple's backend remains the system enforcing deterministic eligibility rules, role authorization, auditability, and the mandatory in-person verification gate. This avoids prompt-only enforcement of healthcare safety constraints.


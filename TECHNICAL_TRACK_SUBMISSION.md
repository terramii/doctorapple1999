# Doctor Apple — Hack4Health 2026 Technical Track Submission

> Submission length: maximum four pages, excluding the appendix. Replace the bracketed team fields before submission.

## 1. Team Information

- Team name: **Doctor Apple**
- Institution(s): **[REQUIRED — add institution]**
- Members (1–5): **[REQUIRED — add member names]**
- Contact person: **[REQUIRED — add name and email]**

## 2. Executive Summary (200 words maximum)

Doctor Apple is an AI-assisted clinic pre-registration system connecting patients, clinic staff, and third-party administrators (TPAs). Patients sign in with the email already attached to their synthetic patient record, choose a booked or walk-in visit, upload a referral chit or insurance voucher from a phone or computer, and review a questionnaire prefilled from existing general or occupational-health records. Agnes AI extracts document fields, while deterministic rules—not the language model—match identity, policy, package eligibility, covered services, and claim limits. Uncertain, inconsistent, or unsupported cases are routed to a human with an explicit reason. Immutable identity fields remain protected, while permitted questionnaire answers can be corrected and saved back to the patient record. Clinic staff must verify physical identity and the insurance e-card in person before approval. After services are recorded, eligible claims can be automatically approved or rejected with reasons and reflected in the TPA and clinic views; exceptions remain in manual review. The prototype provides role-based portals, mobile-responsive upload and forms, audit events, masked identifiers, MongoDB persistence with an offline test store, and a documented path to Microsoft Copilot Studio. It aims to reduce repetitive counter entry and avoid preventable coverage errors without replacing clinical or final human judgment.

## 3. Problem Understanding

Clinic pre-registration currently requires patients and counter staff to repeatedly transcribe identity, referral, policy, appointment, and health-questionnaire information across disconnected steps. Walk-ins add queue pressure; booked patients can still arrive with incomplete or mismatched documents. Staff must interpret different insurers' package codes and then communicate claim status to the TPA and clinic.

The root causes are fragmented records, manual document reading, policy variation, and absent end-to-end status synchronization. These cause longer queues, duplicate entry, privacy exposure, incorrect billing, and avoidable manual follow-up. In health screening, mistakes can also hide allergies or send a patient to the wrong package, making reliable exception handling essential.

## 4. Proposed AI Solution

The patient authenticates, selects walk-in or prebooked care, chooses general or occupational screening, and supplies a local PDF/photo or chooses self-pay. Agnes AI performs schema-constrained document extraction. Doctor Apple's deterministic services then confirm that the document belongs to the signed-in patient, resolve the insurer/package, compare requested services with coverage, prefill the appropriate Parkway Shenton questionnaire, and explain the outcome.

Patients may edit and save questionnaire answers except protected name, identifier, date of birth, and gender. Staff see the registration and must complete physical identity/e-card verification. Following service delivery, the rules engine sends an eligible claim into the simulated TPA workflow and returns `approved`, `rejected`, or `manual review`, together with reasons, to both TPA and clinic views. Self-pay is labelled **No insurance / self-pay** and bypasses the TPA.

```text
Patient (mobile/desktop)
  -> authenticate -> upload/select self-pay -> review questionnaire -> submit
  -> Agnes extraction -> deterministic identity/eligibility/coverage checks
  -> Clinic staff physical verification -> service completion
  -> deterministic TPA decision -> TPA status -> clinic status
                         \-> human review for uncertainty or conflict
```

## 5. Technical Architecture

- **Interfaces:** responsive three-role web app for patient, clinic staff, and TPA assessor.
- **API/orchestration:** FastAPI plus Google ADK/A2A agent tooling; bearer-token role authorization.
- **AI:** Agnes OpenAI-compatible multimodal model for schema-validated text/image extraction and orchestration. The LLM cannot decide coverage or override safety gates.
- **Rules:** Python functions for patient matching, package eligibility, coverage comparison, questionnaire prefill, claim limits, and exception routing.
- **Data:** MongoDB collections for users, patients, registrations, questionnaires, and audit events; synthetic CSV sources seed the prototype. An in-memory adapter supports deterministic tests.
- **Microsoft implementation:** import the generated OpenAPI schema as a Copilot Studio custom connector, use Entra ID in production, apply Power Platform data-loss-prevention policies, and keep protected rules server-side.
- **Clinic Assist/NEHR concept:** an approved integration layer would read appointment/demographic context and write only consented registration status or structured questionnaire results. Production integration requires vendor APIs, data mapping, authentication, reconciliation, and formal clinical/privacy approval; the prototype does not claim live access.

## 6. Operational Impact

The prototype is designed to reduce repeated transcription, incomplete forms, and policy lookups. Pilot targets (to validate rather than present as measured results) are: at least 50% less counter data-entry time per pre-registered patient, at least 30% shorter pre-registration handling time, and 100% of low-confidence, identity-conflict, uncovered-service, and unknown-policy cases routed to an explained review state. Audit events cover registration, questionnaire submission, physical verification, and TPA decision. A clinic pilot should baseline median handling time, correction rate, manual-review rate, and claim turnaround, then compare four weeks before and after rollout.

## 7. Feasibility

The current local prototype already implements authentication, seeded patient lookup, mobile upload, general/occupational questionnaire prefill and write-back, booked/walk-in registration, staff verification, deterministic claim decisions, and role-specific UI. Copilot Studio can call these functions through the documented OpenAPI connector instead of duplicating protected logic in prompts.

A realistic pilot is 8–12 weeks: two weeks for workflow/data mapping, three for connector and identity integration, two for security and user acceptance testing, two for a limited clinic pilot, and one to three for remediation. Dependencies include approved hosting, Entra ID, MongoDB or an approved clinical datastore, Clinic Assist/NEHR and insurer API access, data-protection review, clinic champions, and TPA rule ownership.

## 8. Governance & Safety

Doctor Apple is an administrative assistant, not a diagnostic tool. Physical ID/e-card verification and human exception handling remain mandatory. Deterministic code is authoritative for coverage and billing; malformed files, low extraction confidence, conflicting identity data, unknown codes, uncovered services, and missing limits cannot be silently approved.

The prototype uses synthetic data only. Production requires explicit consent and purpose limitation, least-privilege role access, encryption in transit and at rest, managed secrets, retention/deletion rules, upload malware scanning, rate limits, incident handling, access reviews, and a PDPA data-protection impact assessment. Identifiers are masked in responses and audit records. Material actions create timestamped audit events with actor, decision, and reasons. Human reviewers can resolve exceptions, and rule/model versions should be stored with every production decision.

## 9. Scalability

The API/rules/UI separation allows Parkway Shenton clinics to share a governed service while configuring clinic locations, packages, insurers, limits, and questionnaires as versioned data. Stateless API replicas and a managed database can scale horizontally. Expansion across IHH should proceed by country and workflow because privacy law, identifiers, insurers, terminology, and clinical-system interfaces differ. New rules require tests and staged approval; aggregate operational metrics should avoid exposing patient data.

## 10. Appendix (optional; excluded from page limit)

- Source and setup: `README.md` and `doctor-apple-agent/README.md`
- Copilot Studio integration: `doctor-apple-agent/COPILOT_STUDIO.md`
- Agent manifest: `doctor-apple-agent/agents-cli-manifest.yaml`
- Automated evidence: `doctor-apple-agent/tests/`
- Prototype UI: `sample app/doctor-apple-sage.html`
- Judging evidence map: `SUBMISSION_CHECKLIST.md`


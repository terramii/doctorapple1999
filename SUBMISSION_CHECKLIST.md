# Hack4Health 2026 Submission Checklist

Source of truth: `Resources/3. Hack4Health Judging Criteria.docx`.

## Mandatory technical-track artifact

- [x] Technical-track written submission created: `TECHNICAL_TRACK_SUBMISSION.md`
- [x] Maximum-four-page instruction is stated and the main body follows the required ten-section template.
- [x] Executive summary is below 200 words.
- [x] Problem understanding included.
- [x] Proposed AI solution, workflow, and user journey included.
- [x] Technical architecture covers LLM/model, APIs, database, Microsoft path, and conceptual Clinic Assist/NEHR integration.
- [x] Operational impact includes explicit pilot targets and a measurement plan; targets are not misrepresented as measured results.
- [x] Feasibility includes Copilot Studio implementation, resources, timeline, and dependencies.
- [x] Governance and safety cover PDPA, human oversight, hallucination mitigation, audit trail, and security.
- [x] Scalability covers Parkway Shenton and IHH.
- [ ] **Submission blocker:** replace institution, team-member, and contact-person placeholders in `TECHNICAL_TRACK_SUBMISSION.md`.
- [ ] Export the completed main submission to PDF and confirm it is no more than four pages excluding the appendix. Page count depends on the final export layout.

## Criterion evidence

| Criterion | Repository evidence |
|---|---|
| Problem Understanding | `TECHNICAL_TRACK_SUBMISSION.md` sections 2–3; synthetic source data under `Data/` |
| Operational Impact | Submission section 6; registration and claim workflow in `doctor-apple-agent/app/api.py` |
| Technical Feasibility & Integration | `doctor-apple-agent/app/`, `agents-cli-manifest.yaml`, `COPILOT_STUDIO.md`, Docker and lock files |
| Innovation | Multimodal extraction plus deterministic eligibility/claim controls and cross-role status flow |
| User Experience | Responsive role portals and device upload in `sample app/doctor-apple-sage.html` |
| Governance & Safety | Authorization, identifier masking, staff verification, exception reasons, and audit writes in `doctor-apple-agent/app/` |
| Scalability | Submission section 9 and connector boundary in `COPILOT_STUDIO.md` |

## Optional appendix items

The judging document labels prototype, GitHub, video, screenshots, and poster as optional. Include them if available, but do not delay the mandatory written submission for them.

- [x] Working local prototype and source tree
- [x] Git-ready repository configuration (`.gitignore` excludes `.env` and runtime artifacts)
- [ ] Public GitHub URL
- [ ] Demo video URL
- [ ] Screenshots or poster

## Final quality gate

Run from `doctor-apple-agent/`:

```powershell
uv run pytest tests/unit tests/integration -q
uv run ruff check app tests scripts
```

Before sharing the repository, rotate any key ever displayed or committed, confirm `.env` is not tracked, and use only `.env.example` for configuration documentation.

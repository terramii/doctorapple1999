"""Doctor Apple ADK agent backed by Agnes's OpenAI-compatible API."""

from __future__ import annotations

import re

from google.adk.agents import Agent
from google.adk.apps import App, ResumabilityConfig
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_response import LlmResponse

from app.config import settings
from app.tools import (
    check_requested_tests,
    find_patient,
    generate_questionnaire_prefill,
    resolve_eligibility,
)


def redact_model_output(
    callback_context, llm_response: LlmResponse
) -> LlmResponse | None:
    """Mask Singapore-style identifiers if a model attempts to emit one."""
    del callback_context
    if not llm_response.content or not llm_response.content.parts:
        return None
    changed = False
    for part in llm_response.content.parts:
        if not part.text:
            continue
        redacted = re.sub(
            r"\b([STFGM])\d{7}([A-Z])\b", r"\1******\2", part.text, flags=re.I
        )
        if redacted != part.text:
            part.text = redacted
            changed = True
    return llm_response if changed else None


agnes_model = LiteLlm(
    model=f"openai/{settings.agnes_model}",
    api_base=settings.agnes_base_url,
    api_key=settings.agnes_api_key or "not-configured",
)

root_agent = Agent(
    name="doctor_apple",
    description="Administrative clinic pre-registration and eligibility assistant.",
    model=agnes_model,
    instruction="""
You are Doctor Apple, an administrative clinic intake assistant using synthetic data.

Rules:
- Use tools for patient lookup, package eligibility, coverage comparison, and questionnaire prefill. Never invent their results.
- You do not diagnose, interpret clinical results, or recommend treatment.
- Physical identity and e-card verification must be completed in person by clinic staff. Never claim it is complete.
- Unknown codes, conflicting demographics, low-confidence extraction, uncovered tests, or uncertain costs require manual staff review.
- Always display a drug allergy as: WARNING — DRUG ALLERGY: <allergy>.
- Never reveal full NRIC, FIN, passport, password, API key, token, or database credential.
- Clearly separate covered tests from uncovered tests.
- Keep responses concise and suitable for clinic counter staff.
""",
    tools=[
        find_patient,
        resolve_eligibility,
        check_requested_tests,
        generate_questionnaire_prefill,
    ],
    after_model_callback=redact_model_output,
)

app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True),
)

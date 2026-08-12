"""Minimal OpenAI-compatible Agnes client with schema validation."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.config import settings


class ChitExtraction(BaseModel):
    full_name: str | None = None
    identifier: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    insurer_code: str | None = None
    requested_tests: list[str] = Field(default_factory=list)
    form_type: str = "general"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    discrepancies: list[str] = Field(default_factory=list)


def _json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    return json.loads(cleaned)


async def extract_chit(text: str) -> ChitExtraction:
    if not settings.agnes_api_key:
        raise RuntimeError("AGNES_AI_API_KEY is not configured")
    prompt = (
        """Extract administrative fields from this synthetic medical chit. Return JSON only with keys: full_name, identifier, date_of_birth, gender, insurer_code, requested_tests, form_type, confidence, discrepancies. Never infer a missing identifier, insurer code, allergy, or clinical fact. form_type is general or occupational. confidence is 0 to 1.\n\nCHIT:\n"""
        + text
    )
    payload = {
        "model": settings.agnes_model,
        "messages": [
            {
                "role": "system",
                "content": "You extract clinic administrative data. Output one valid JSON object only.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{settings.agnes_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.agnes_api_key}"},
                json=payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return ChitExtraction.model_validate(_json_object(content))
    except (
        httpx.HTTPError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise RuntimeError(
            "Agnes extraction failed; manual review is required"
        ) from exc

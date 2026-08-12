"""Environment-backed configuration for the local prototype."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    agnes_api_key: str = os.getenv("AGNES_AI_API_KEY", "")
    agnes_base_url: str = os.getenv(
        "AGNES_AI_BASE_URL", "https://apihub.agnes-ai.com/v1"
    ).rstrip("/")
    agnes_model: str = os.getenv("AGNES_AI_MODEL", "agnes-2.5-flash")
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "doctor_apple")
    token_secret: str = os.getenv("APP_TOKEN_SECRET", "local-development-only")
    offline_mode: bool = os.getenv("OFFLINE_MODE", "false").lower() == "true"


settings = Settings()

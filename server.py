"""Lightweight Vercel entry point for the Doctor Apple web app and REST API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent
AGENT_DIR = ROOT_DIR / "doctor-apple-agent"
sys.path.insert(0, str(AGENT_DIR))

from app.api import router as doctor_apple_router

SAMPLE_APP_DIR = ROOT_DIR / "sample app"
DATA_DIR = ROOT_DIR / "Data"

app = FastAPI(
    title="Doctor Apple",
    description="Patient registration, clinic workflow, and TPA prototype API",
)
origins = [origin.strip() for origin in os.getenv("ALLOW_ORIGINS", "").split(",") if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(doctor_apple_router)
app.mount("/Data", StaticFiles(directory=DATA_DIR), name="doctor-apple-data")


@app.get("/", include_in_schema=False)
def doctor_apple_ui() -> FileResponse:
    return FileResponse(SAMPLE_APP_DIR / "doctor-apple-sage.html")


@app.get("/db.js", include_in_schema=False)
def doctor_apple_synthetic_database() -> FileResponse:
    return FileResponse(SAMPLE_APP_DIR / "db.js", media_type="application/javascript")

"""Password, token, and sensitive-identifier helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def normalize_identifier(value: str) -> str:
    return "".join(value.upper().split())


def mask_identifier(value: str) -> str:
    clean = normalize_identifier(value)
    if len(clean) <= 4:
        return "*" * len(clean)
    return f"{clean[:1]}{'*' * (len(clean) - 3)}{clean[-2:]}"


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return (
        "pbkdf2_sha256$600000$"
        + base64.urlsafe_b64encode(salt).decode()
        + "$"
        + base64.urlsafe_b64encode(derived).decode()
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_token(
    subject: str, role: str, secret: str, ttl_seconds: int = 28_800
) -> str:
    payload = {"sub": subject, "role": role, "exp": int(time.time()) + ttl_seconds}
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=")
    signature = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return (
        body.decode() + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    )


def decode_token(token: str, secret: str) -> dict[str, Any]:
    try:
        body_text, signature_text = token.split(".", 1)
        body = body_text.encode()
        signature = base64.urlsafe_b64decode(
            signature_text + "=" * (-len(signature_text) % 4)
        )
        expected = hmac.new(secret.encode(), body, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid token")
        payload = json.loads(
            base64.urlsafe_b64decode(body_text + "=" * (-len(body_text) % 4))
        )
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("Expired token")
        return payload
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid or expired token") from exc

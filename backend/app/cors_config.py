from __future__ import annotations

import os
from urllib.parse import urlsplit


DEFAULT_DEVELOPMENT_ORIGINS = (
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
)


def configured_cors_origins() -> list[str]:
    """Return exact trusted browser origins; never allow wildcard credentials."""
    raw = os.getenv("WURI_CORS_ORIGINS")
    if raw is None or not raw.strip():
        environment = os.getenv("WURI_ENVIRONMENT", "development").strip().lower()
        return list(DEFAULT_DEVELOPMENT_ORIGINS) if environment in {"", "development", "dev", "test"} else []

    origins: list[str] = []
    seen: set[str] = set()
    for candidate in raw.split(","):
        origin = candidate.strip()
        if not origin:
            continue
        try:
            parsed = urlsplit(origin)
            # Access .port so malformed ports are rejected by urllib.
            _ = parsed.port
        except ValueError as error:
            raise ValueError("WURI_CORS_ORIGINS contains a malformed origin.") from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or "*" in parsed.netloc
        ):
            raise ValueError("WURI_CORS_ORIGINS must contain exact HTTP(S) origins only.")
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        if normalized not in seen:
            seen.add(normalized)
            origins.append(normalized)
    return origins

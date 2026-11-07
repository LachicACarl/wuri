import json
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Any

from .malware_scanning import scanner_configuration_status
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_REQUEST_BODY_BYTES = MAX_UPLOAD_BYTES + 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def build_readiness_report() -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    scanner_status, scanner_detail = scanner_configuration_status()
    checks.append(_check("malware_scanner", scanner_status, scanner_detail))

    storage_path = Path(os.getenv("WURI_STORAGE_PATH") or Path(__file__).resolve().parents[1] / "private")
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        probe = storage_path / ".readiness-probe"
        probe.write_bytes(b"")
        probe.unlink()
        checks.append(_check("private_storage", "manual_verification_required",
                             "Storage is writable; deployment isolation and backup controls require review."))
    except OSError:
        checks.append(_check("private_storage", "blocked", "Private storage is not writable."))

    try:
        requested = os.getenv("SESSION_COOKIE_SECURE", "true").strip().lower()
        if requested not in {"true", "false"}:
            raise ValueError("invalid cookie setting")
        if requested == "false" and os.getenv("WURI_ENVIRONMENT", "").strip().lower() != "development":
            raise ValueError("insecure cookie outside development")
        secure = requested == "true"
        checks.append(_check(
            "secure_session_cookies", "ready" if secure else "blocked",
            "Session cookies use Secure." if secure else "Secure cookies are disabled.",
        ))
    except Exception:
        checks.append(_check("secure_session_cookies", "blocked", "Cookie security configuration is invalid."))

    database_path = Path(os.getenv("WURI_DATABASE_PATH") or Path(__file__).resolve().parents[1] / "data" / "wuri.sqlite3")
    try:
        connection = sqlite3.connect(database_path)
        try:
            migrations = {
                row[0] for row in connection.execute(
                    "SELECT migration_name FROM schema_migrations"
                )
            }
        finally:
            connection.close()
        required = {f"{index:03d}_{name}.sql" for index, name in (
            (1, "initial"), (2, "research_validation"),
            (3, "research_execution"), (4, "research_import_and_annotations"),
            (5, "five_expert_panel"), (6, "institution_registry_readiness"),
            (7, "secure_evidence_provenance"), (8, "malware_scan_state"),
            (9, "auth_sessions_and_login_limits"),
        )}
        missing = required - migrations
        checks.append(_check(
            "database_migrations", "ready" if not missing else "blocked",
            "Required migrations are applied." if not missing else "Required migrations are missing.",
        ))
    except (OSError, sqlite3.Error):
        checks.append(_check("database_migrations", "blocked", "The database migration state is unavailable."))

    checks.append(_check(
        "upload_parser_limits", "ready",
        f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}; limit: {MAX_UPLOAD_BYTES} bytes.",
    ))
    checks.append(_check(
        "application_request_body_limit", "ready",
        f"ASGI middleware enforces a total request-body ceiling of {MAX_REQUEST_BODY_BYTES} bytes.",
    ))
    checks.append(_check(
        "ingress_body_limit", "manual_verification_required",
        "Reverse-proxy or hosting ingress request-body limits must be configured and verified separately.",
    ))
    checks.append(_check(
        "parser_process_isolation", "blocked",
        "Document parsing does not yet run in a separately resource-limited worker process.",
    ))
    checks.append(_check(
        "authorization_workflow", "manual_verification_required",
        "Human verification is required for institutional authorization, research use, DUA, ethics, privacy, and source rights.",
    ))
    checks.append(_check(
        "audit_logging", "manual_verification_required",
        "Audit events are recorded; retention, access, backup, and recovery procedures require deployment review.",
    ))
    checks.append(_check(
        "operational_recovery", "manual_verification_required",
        "Backups, deletion retention, restore testing, and incident response require deployment review.",
    ))
    return {"intake_gate": "ready" if all(item["status"] == "ready" for item in checks) else "blocked",
            "checks": checks}


def main() -> int:
    report = build_readiness_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["intake_gate"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())

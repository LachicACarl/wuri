import json
import math
import os
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "wuri.sqlite3"


class Database:
    def __init__(self, path: str | Path | None = None):
        configured = path or os.getenv("WURI_DATABASE_PATH") or DEFAULT_DB_PATH
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.connection() as connection:
            migration_root = Path(__file__).resolve().parents[1] / "migrations"
            connection.execute(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                       migration_name TEXT PRIMARY KEY,
                       applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                   )"""
            )
            for migration in sorted(migration_root.glob("[0-9][0-9][0-9]_*.sql")):
                if connection.execute(
                    "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                    (migration.name,),
                ).fetchone():
                    continue
                connection.executescript(migration.read_text(encoding="utf-8"))
                foreign_key_violations = connection.execute(
                    "PRAGMA foreign_key_check"
                ).fetchall()
                if foreign_key_violations:
                    raise sqlite3.IntegrityError(
                        f"Migration {migration.name} caused foreign-key violations."
                    )
                connection.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                    (migration.name,),
                )

    def ensure_admin(self, username: str, password_hash: str):
        with self.connection() as connection:
            row = connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                return row["id"]
            user_id = _id("usr")
            connection.execute(
                "INSERT INTO users (id, username, password_hash, status) VALUES (?, ?, ?, 'active')",
                (user_id, username, password_hash),
            )
            institution_id = _id("inst")
            connection.execute(
                "INSERT INTO institutions (id, name, metadata_json) VALUES (?, ?, ?)",
                (institution_id, "Default development institution", "{}"),
            )
            connection.execute(
                "INSERT INTO institution_memberships (user_id, institution_id, role, status) VALUES (?, ?, 'administrator', 'active')",
                (user_id, institution_id),
            )
            return user_id

    def user(self, user_id: str):
        with self.connection() as connection:
            return connection.execute(
                "SELECT id, username, password_hash, status FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

    def user_by_username(self, username: str):
        with self.connection() as connection:
            return connection.execute(
                "SELECT id, username, password_hash, status FROM users WHERE username = ?",
                (username.strip().lower(),),
            ).fetchone()

    def create_session(self, session_id: str, user_id: str, expires_at: int):
        import time
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO auth_sessions (session_id, user_id, created_at, expires_at)
                   VALUES (?, ?, ?, ?)""",
                (session_id, user_id, int(time.time()), int(expires_at)),
            )

    def session_is_active(self, session_id: str, user_id: str, now: int | None = None) -> bool:
        import time
        timestamp = int(time.time()) if now is None else int(now)
        with self.connection() as connection:
            return connection.execute(
                """SELECT 1 FROM auth_sessions
                   WHERE session_id = ? AND user_id = ? AND revoked_at IS NULL
                     AND expires_at > ?""",
                (session_id, user_id, timestamp),
            ).fetchone() is not None

    def revoke_session(self, session_id: str, now: int | None = None) -> bool:
        import time
        timestamp = int(time.time()) if now is None else int(now)
        with self.connection() as connection:
            cursor = connection.execute(
                """UPDATE auth_sessions SET revoked_at = ?
                   WHERE session_id = ? AND revoked_at IS NULL""",
                (timestamp, session_id),
            )
            return cursor.rowcount == 1

    def login_rate_limit_status(self, rate_key: str, now: int | None = None) -> int:
        import time
        timestamp = int(time.time()) if now is None else int(now)
        window_seconds = 900
        with self.connection() as connection:
            row = connection.execute(
                "SELECT window_started_at, locked_until FROM login_rate_limits WHERE rate_key = ?",
                (rate_key,),
            ).fetchone()
            if not row:
                return 0
            if row["locked_until"] is not None and row["locked_until"] > timestamp:
                return row["locked_until"] - timestamp
            if row["window_started_at"] + window_seconds <= timestamp:
                connection.execute("DELETE FROM login_rate_limits WHERE rate_key = ?", (rate_key,))
                return 0
            return 0

    def record_login_failure(
        self, rate_key: str, now: int | None = None, max_attempts: int = 5,
        window_seconds: int = 900,
    ) -> int:
        import time
        timestamp = int(time.time()) if now is None else int(now)
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT window_started_at, failed_attempts, locked_until
                   FROM login_rate_limits WHERE rate_key = ?""",
                (rate_key,),
            ).fetchone()
            if row and row["locked_until"] is not None and row["locked_until"] > timestamp:
                return row["locked_until"] - timestamp
            if not row or row["window_started_at"] + window_seconds <= timestamp:
                window_started = timestamp
                attempts = 1
                locked_until = None
            else:
                window_started = row["window_started_at"]
                attempts = row["failed_attempts"] + 1
                locked_until = row["locked_until"]
            if attempts >= max_attempts:
                locked_until = timestamp + window_seconds
            connection.execute(
                """INSERT INTO login_rate_limits
                   (rate_key, window_started_at, failed_attempts, locked_until)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(rate_key) DO UPDATE SET
                     window_started_at = excluded.window_started_at,
                     failed_attempts = excluded.failed_attempts,
                     locked_until = excluded.locked_until""",
                (rate_key, window_started, attempts, locked_until),
            )
            return max(0, locked_until - timestamp) if locked_until else 0

    def clear_login_failures(self, rate_key: str):
        with self.connection() as connection:
            connection.execute("DELETE FROM login_rate_limits WHERE rate_key = ?", (rate_key,))

    def memberships(self, user_id: str):
        with self.connection() as connection:
            return connection.execute(
                "SELECT institution_id, role FROM institution_memberships WHERE user_id = ? AND status = 'active'",
                (user_id,),
            ).fetchall()

    def institutions_for_user(self, user_id: str):
        with self.connection() as connection:
            return connection.execute(
                """SELECT i.id, i.name, i.display_name, i.country, i.region,
                          i.institution_type, i.campus_name, i.parent_institution_id,
                          i.status, i.provenance, i.created_at, i.updated_at,
                          m.role, m.status AS membership_status
                   FROM institutions i
                   JOIN institution_memberships m ON m.institution_id = i.id
                   WHERE m.user_id = ? AND m.status = 'active'
                   ORDER BY COALESCE(i.display_name, i.name), i.id""",
                (user_id,),
            ).fetchall()

    def create_institution(self, user_id: str, institution: dict[str, Any]) -> str:
        institution_id = _id("inst")
        with self.connection() as connection:
            membership = connection.execute(
                """SELECT 1 FROM institution_memberships
                   WHERE user_id = ? AND role = 'administrator' AND status = 'active'""",
                (user_id,),
            ).fetchone()
            if not membership:
                raise PermissionError("Administrator membership required.")
            connection.execute(
                """INSERT INTO institutions
                   (id, name, display_name, country, region, institution_type,
                    campus_name, parent_institution_id, status, provenance)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (institution_id, institution["name"], institution.get("display_name"),
                 institution.get("country") or "Philippines", institution.get("region"),
                 institution.get("institution_type"), institution.get("campus_name"),
                 institution.get("parent_institution_id"), institution.get("status") or "active",
                 institution.get("provenance")),
            )
            connection.execute(
                """INSERT INTO institution_memberships
                   (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (user_id, institution_id),
            )
            _event(connection, institution_id, None, user_id, "institution.created", {})
        return institution_id

    def update_institution(self, user_id: str, institution_id: str, changes: dict[str, Any]):
        allowed = {
            "name", "display_name", "country", "region", "institution_type",
            "campus_name", "parent_institution_id", "status", "provenance",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            raise ValueError("At least one institution field is required.")
        if values.get("status") not in {None, "active", "inactive"}:
            raise ValueError("Unsupported institution status.")
        with self.connection() as connection:
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (user_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator":
                raise PermissionError("Administrator access to this institution is required.")
            assignments = ", ".join(f"{key} = ?" for key in values)
            connection.execute(
                f"UPDATE institutions SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (*values.values(), institution_id),
            )
            _event(connection, institution_id, None, user_id, "institution.updated", {"fields": sorted(values)})

    def evidence_readiness(self, user_id: str, institution_id: str, framework_id: str, edition: str):
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            return connection.execute(
                """SELECT * FROM evidence_readiness
                   WHERE institution_id = ? AND framework_id = ? AND framework_edition = ?
                   ORDER BY criterion_id""",
                (institution_id, framework_id, edition),
            ).fetchall()

    def upsert_evidence_readiness(
        self, user_id: str, institution_id: str, item: dict[str, Any]
    ) -> str:
        with self.connection() as connection:
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (user_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] not in {"administrator", "evaluator"}:
                raise PermissionError("Institution evidence access denied.")
            existing = connection.execute(
                """SELECT id FROM evidence_readiness
                   WHERE institution_id = ? AND framework_id = ?
                     AND framework_edition = ? AND criterion_id = ?""",
                (institution_id, item["framework_id"], item["framework_edition"], item["criterion_id"]),
            ).fetchone()
            if existing:
                assignments = [
                    "eligibility_status", "authorization_status", "provenance_status",
                    "evidence_status", "privacy_status", "expert_review_status",
                    "evidence_title", "evidence_type", "source_reference", "source_date",
                    "collection_date", "description", "limitations", "reviewer_id",
                ]
                connection.execute(
                    f"""UPDATE evidence_readiness
                        SET {", ".join(f"{field} = ?" for field in assignments)},
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND institution_id = ?""",
                    tuple(item.get(field) for field in assignments)
                    + (existing["id"], institution_id),
                )
                record_id = existing["id"]
            else:
                record_id = _id("ready")
                connection.execute(
                    """INSERT INTO evidence_readiness
                       (id, institution_id, framework_id, framework_edition, criterion_id,
                        eligibility_status, authorization_status, provenance_status,
                        evidence_status, privacy_status, expert_review_status,
                        evidence_title, evidence_type, source_reference, source_date,
                        collection_date, description, limitations, reviewer_id, created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (record_id, institution_id, item["framework_id"], item["framework_edition"],
                     item["criterion_id"], item.get("eligibility_status", "unknown"),
                     item.get("authorization_status", "unknown"), item.get("provenance_status", "unknown"),
                     item.get("evidence_status", "unknown"), item.get("privacy_status", "unknown"),
                     item.get("expert_review_status", "not_required"), item.get("evidence_title"),
                     item.get("evidence_type"), item.get("source_reference"), item.get("source_date"),
                     item.get("collection_date"), item.get("description"), item.get("limitations"),
                     item.get("reviewer_id"), user_id),
                )
            _event(connection, institution_id, None, user_id, "evidence.readiness.updated",
                   {"readiness_id": record_id, "framework_id": item["framework_id"],
                    "criterion_id": item["criterion_id"]})
            return record_id

    def create_assessment(self, user_id: str, institution_id: str, status: str):
        assessment_id = _id("asm")
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            connection.execute(
                "INSERT INTO assessments (id, institution_id, created_by, status) VALUES (?, ?, ?, ?)",
                (assessment_id, institution_id, user_id, status),
            )
            _event(connection, institution_id, assessment_id, user_id, "assessment.created", {})
        return assessment_id

    def record_upload_failure(
        self,
        user_id: str,
        institution_id: str,
        assessment_id: str,
        reason: str,
        *,
        fail_assessment: bool,
    ):
        """Preserve an auditable upload failure without deleting its assessment."""
        with self.connection() as connection:
            if not _assessment_access(connection, user_id, institution_id, assessment_id):
                raise PermissionError("Assessment access denied.")
            if fail_assessment:
                updated = connection.execute(
                    """UPDATE assessments
                       SET status = 'failed', failure_reason = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE id = ? AND institution_id = ? AND created_by = ?""",
                    (reason, assessment_id, institution_id, user_id),
                )
                if updated.rowcount != 1:
                    raise PermissionError("Assessment failure update is not permitted.")
                event_type = "assessment.failed"
            else:
                event_type = "document.upload_failed"
            _event(
                connection,
                institution_id,
                assessment_id,
                user_id,
                event_type,
                {"reason": reason},
            )

    def persist_document(self, user_id: str, institution_id: str, assessment_id: str, document: dict, passages: list[dict], matches: list[dict]):
        document_id = document["document_id"]
        with self.connection() as connection:
            if not _assessment_access(connection, user_id, institution_id, assessment_id):
                raise PermissionError("Assessment access denied.")
            connection.execute(
                """INSERT INTO documents
                (id, institution_id, assessment_id, filename, file_type, file_size, checksum,
                 storage_key, extraction_status, title, source_reference, collection_date,
                 reporting_period, provenance, authorization_status, research_permission_status,
                 review_status, limitations, malware_scan_status, malware_scanned_at,
                 malware_scanner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (document_id, institution_id, assessment_id, document["filename"], document["file_type"],
                 document["file_size"], document["checksum"], document["storage_key"],
                 document["extraction_status"], document.get("title") or document["filename"],
                 document.get("source_reference"), document.get("collection_date"),
                 document.get("reporting_period"), document.get("provenance"),
                 document.get("authorization_status", "unknown"),
                 document.get("research_permission_status", "unknown"),
                 "pending_review" if document.get("mapping") else "uploaded",
                 document.get("limitations"), document.get("malware_scan_status", "not_scanned"),
                 document.get("malware_scanned_at"), document.get("malware_scanner")),
            )
            mapping = document.get("mapping")
            if mapping:
                connection.execute(
                    """INSERT INTO document_framework_mappings
                       (document_id, institution_id, framework_id, framework_edition,
                        criterion_id, created_by)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (document_id, institution_id, mapping["framework_id"],
                     mapping["framework_edition"], mapping["criterion_id"], user_id),
                )
            for passage in passages:
                connection.execute(
                    """INSERT INTO evidence_passages
                    (id, document_id, assessment_id, institution_id, passage_index, text, page_number, section_title, start_offset, end_offset, extraction_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (passage["passage_id"], document_id, assessment_id, institution_id, passage["passage_index"],
                     passage["text"], passage["page_number"], passage["section_title"], passage["start_offset"],
                     passage["end_offset"], passage["extraction_method"]),
                )
            for match in matches:
                connection.execute(
                    """INSERT INTO indicator_matches
                    (id, passage_id, framework, indicator, similarity, retrieval_version)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (_id("mat"), match["passage_id"], match["framework"], match["indicator"],
                     match["similarity"], "sentence-transformers-configured"),
                )
            connection.execute(
                "UPDATE assessments SET status = 'evidence_retrieved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (assessment_id,),
            )
            _event(connection, institution_id, assessment_id, user_id, "document.processed", {
                "document_id": document_id, "passage_count": len(passages), "match_count": len(matches),
            })

    def assessments(self, user_id: str):
        with self.connection() as connection:
            return connection.execute(
                """SELECT a.id, a.institution_id, i.name AS institution_name, a.status, a.failure_reason, a.created_at, a.updated_at
                   FROM assessments a JOIN institutions i ON i.id = a.institution_id
                   WHERE EXISTS (SELECT 1 FROM institution_memberships m WHERE m.institution_id = a.institution_id AND m.user_id = ? AND m.status = 'active')
                   ORDER BY a.created_at DESC""",
                (user_id,),
            ).fetchall()

    def assessment_detail(self, user_id: str, assessment_id: str):
        with self.connection() as connection:
            row = connection.execute(
                """SELECT a.id, a.institution_id, i.name AS institution_name, a.status,
                          a.failure_reason, a.created_at, a.updated_at
                   FROM assessments a JOIN institutions i ON i.id = a.institution_id
                   WHERE a.id = ? AND EXISTS (
                       SELECT 1 FROM institution_memberships m
                       WHERE m.institution_id = a.institution_id AND m.user_id = ? AND m.status = 'active'
                   )""",
                (assessment_id, user_id),
            ).fetchone()
            if not row:
                return None
            documents = connection.execute(
                """SELECT id, filename, title, file_type, file_size, checksum, extraction_status,
                          authorization_status, research_permission_status, review_status,
                          source_reference, collection_date, reporting_period, provenance,
                          limitations, malware_scan_status, malware_scanned_at, malware_scanner,
                          created_at
                   FROM documents WHERE assessment_id = ? ORDER BY created_at""",
                (assessment_id,),
            ).fetchall()
            passages = connection.execute(
                """SELECT id, document_id, passage_index, text, page_number, section_title,
                          start_offset, end_offset, extraction_method
                   FROM evidence_passages WHERE assessment_id = ? ORDER BY document_id, passage_index""",
                (assessment_id,),
            ).fetchall()
            matches = connection.execute(
                """SELECT m.id, m.passage_id, m.framework, m.indicator, m.similarity, m.retrieval_version
                   FROM indicator_matches m JOIN evidence_passages p ON p.id = m.passage_id
                   WHERE p.assessment_id = ? ORDER BY m.passage_id, m.similarity DESC""",
                (assessment_id,),
            ).fetchall()
            mappings = connection.execute(
                """SELECT document_id, framework_id, framework_edition, criterion_id
                   FROM document_framework_mappings
                   WHERE institution_id = ? AND document_id IN
                     (SELECT id FROM documents WHERE assessment_id = ?)
                   ORDER BY document_id, criterion_id""",
                (row["institution_id"], assessment_id),
            ).fetchall()
            return {"assessment": dict(row), "documents": [dict(item) for item in documents],
                    "passages": [dict(item) for item in passages], "matches": [dict(item) for item in matches],
                    "mappings": [dict(item) for item in mappings]}

    def update_document_metadata(
        self, user_id: str, document_id: str, changes: dict[str, Any]
    ):
        editable = {
            "title", "source_reference", "collection_date", "reporting_period",
            "provenance", "limitations", "review_status",
        }
        permission_fields = {"authorization_status", "research_permission_status"}
        values = {key: value for key, value in changes.items() if key in editable or key in permission_fields}
        with self.connection() as connection:
            row = connection.execute(
                """SELECT d.institution_id, m.role FROM documents d
                   JOIN institution_memberships m ON m.institution_id = d.institution_id
                   WHERE d.id = ? AND m.user_id = ? AND m.status = 'active'""",
                (document_id, user_id),
            ).fetchone()
            if not row:
                raise PermissionError("Document access denied.")
            if permission_fields.intersection(values) and row["role"] != "administrator":
                raise PermissionError("Only an institution administrator may verify document permissions.")
            if values.get("review_status") == "verified" and row["role"] != "administrator":
                raise PermissionError("Only an institution administrator may verify a document.")
            if not values:
                raise ValueError("At least one document field is required.")
            if permission_fields.intersection(values) or "review_status" in values:
                approved = connection.execute(
                    """SELECT 1
                       FROM research_examples e
                       JOIN research_datasets d ON d.id = e.dataset_id
                       WHERE e.source_document_id = ? AND d.verification_status = 'approved'
                       LIMIT 1""",
                    (document_id,),
                ).fetchone()
                if approved:
                    raise ValueError(
                        "Document verification metadata cannot change while an approved research dataset references it."
                    )
            assignments = ", ".join(f"{field} = ?" for field in values)
            connection.execute(
                f"UPDATE documents SET {assignments} WHERE id = ?",
                (*values.values(), document_id),
            )
            _event(connection, row["institution_id"], None, user_id, "document.metadata.updated",
                   {"document_id": document_id, "fields": sorted(values)})

    def document_storage_key_for_deletion(
        self, user_id: str, document_id: str,
    ) -> tuple[str, str]:
        """Authorize deletion and return storage key and institution without mutation."""
        with self.connection() as connection:
            row = connection.execute(
                """SELECT d.storage_key, d.institution_id, m.role
                   FROM documents d JOIN institution_memberships m
                     ON m.institution_id = d.institution_id
                   WHERE d.id = ? AND m.user_id = ? AND m.status = 'active'""",
                (document_id, user_id),
            ).fetchone()
            if not row or row["role"] != "administrator":
                raise PermissionError("Administrator document access is required.")
            approved_reference = connection.execute(
                """SELECT 1
                   FROM research_examples e
                   JOIN research_datasets d ON d.id = e.dataset_id
                   WHERE e.source_document_id = ? AND d.verification_status = 'approved'
                   LIMIT 1""",
                (document_id,),
            ).fetchone()
            if approved_reference:
                raise ValueError(
                    "A document referenced by an approved research dataset cannot be deleted."
                )
            return row["storage_key"], row["institution_id"]

    def delete_document(self, user_id: str, document_id: str) -> str:
        with self.connection() as connection:
            row = connection.execute(
                """SELECT d.institution_id, d.storage_key, m.role
                   FROM documents d JOIN institution_memberships m
                     ON m.institution_id = d.institution_id
                   WHERE d.id = ? AND m.user_id = ? AND m.status = 'active'""",
                (document_id, user_id),
            ).fetchone()
            if not row or row["role"] != "administrator":
                raise PermissionError("Administrator document access is required.")
            approved_reference = connection.execute(
                """SELECT 1
                   FROM research_examples e
                   JOIN research_datasets d ON d.id = e.dataset_id
                   WHERE e.source_document_id = ? AND d.verification_status = 'approved'
                   LIMIT 1""",
                (document_id,),
            ).fetchone()
            if approved_reference:
                raise ValueError(
                    "A document referenced by an approved research dataset cannot be deleted."
                )
            connection.execute(
                """DELETE FROM indicator_matches
                   WHERE passage_id IN (SELECT id FROM evidence_passages WHERE document_id = ?)""",
                (document_id,),
            )
            connection.execute("DELETE FROM evidence_passages WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            _event(connection, row["institution_id"], None, user_id, "document.deleted",
                   {"document_id": document_id})
            return row["storage_key"]

    def enqueue_storage_cleanup(
        self, user_id: str, institution_id: str, document_id: str,
        storage_key: str, reason: str,
    ) -> str:
        """Persist a quarantined object so cleanup survives process restarts."""
        if not _is_staged_storage_key(storage_key):
            raise ValueError("Invalid staged storage key.")
        cleanup_id = _id("scq")
        with self.connection() as connection:
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (user_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator":
                raise PermissionError("Administrator document access is required.")
            connection.execute(
                """INSERT INTO storage_cleanup_queue
                   (id, institution_id, document_id, storage_key, reason, status)
                   VALUES (?, ?, ?, ?, ?, 'pending')
                   ON CONFLICT(storage_key) DO UPDATE SET
                     reason = excluded.reason,
                     status = 'pending',
                     updated_at = CURRENT_TIMESTAMP,
                     completed_at = NULL""",
                (cleanup_id, institution_id, document_id, storage_key, reason[:500]),
            )
            _event(
                connection, institution_id, None, user_id,
                "document.storage_cleanup_pending",
                {"document_id": document_id, "cleanup_id": cleanup_id},
            )
        return cleanup_id

    def pending_storage_cleanups(
        self, user_id: str, limit: int = 50,
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """SELECT q.id, q.institution_id, q.document_id, q.storage_key,
                          q.reason, q.attempts, q.created_at, q.updated_at
                   FROM storage_cleanup_queue q
                   JOIN institution_memberships m
                     ON m.institution_id = q.institution_id
                   WHERE m.user_id = ? AND m.status = 'active'
                     AND m.role = 'administrator'
                     AND (
                       q.status = 'pending'
                       OR (q.status = 'processing'
                           AND q.claimed_at < datetime('now', '-5 minutes'))
                     )
                   ORDER BY q.created_at ASC LIMIT ?""",
                (user_id, max(1, min(int(limit), 100))),
            ).fetchall()
            return [dict(row) for row in rows]

    def claim_storage_cleanup(self, user_id: str, cleanup_id: str) -> bool:
        """Atomically lease one pending or abandoned cleanup item to an admin."""
        with self.connection() as connection:
            cursor = connection.execute(
                """UPDATE storage_cleanup_queue
                   SET status = 'processing', claimed_at = CURRENT_TIMESTAMP,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?
                     AND (
                       status = 'pending'
                       OR (status = 'processing'
                           AND claimed_at < datetime('now', '-5 minutes'))
                     )
                     AND EXISTS (
                       SELECT 1 FROM institution_memberships m
                       WHERE m.user_id = ? AND m.institution_id =
                             storage_cleanup_queue.institution_id
                         AND m.status = 'active' AND m.role = 'administrator'
                     )""",
                (cleanup_id, user_id),
            )
            return cursor.rowcount == 1

    def record_storage_cleanup_failure(
        self, user_id: str, cleanup_id: str, safe_reason: str,
    ) -> None:
        with self.connection() as connection:
            cursor = connection.execute(
                """UPDATE storage_cleanup_queue
                   SET status = 'pending', claimed_at = NULL,
                       attempts = attempts + 1, reason = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND status = 'processing'
                     AND EXISTS (
                       SELECT 1 FROM institution_memberships m
                       WHERE m.user_id = ? AND m.institution_id =
                             storage_cleanup_queue.institution_id
                         AND m.status = 'active' AND m.role = 'administrator'
                     )""",
                (safe_reason[:500], cleanup_id, user_id),
            )
            if cursor.rowcount != 1:
                raise PermissionError("Administrator document access is required.")

    def complete_storage_cleanup(self, user_id: str, cleanup_id: str) -> None:
        with self.connection() as connection:
            cursor = connection.execute(
                """UPDATE storage_cleanup_queue
                   SET status = 'completed', claimed_at = NULL,
                       completed_at = CURRENT_TIMESTAMP,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND status = 'processing'
                     AND EXISTS (
                       SELECT 1 FROM institution_memberships m
                       WHERE m.user_id = ? AND m.institution_id =
                             storage_cleanup_queue.institution_id
                         AND m.status = 'active' AND m.role = 'administrator'
                     )""",
                (cleanup_id, user_id),
            )
            if cursor.rowcount != 1:
                raise PermissionError("Administrator document access is required.")

    def remove_empty_assessment(self, user_id: str, assessment_id: str):
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM assessments WHERE id = ? AND created_by = ? AND NOT EXISTS (SELECT 1 FROM documents WHERE assessment_id = ?)",
                (assessment_id, user_id, assessment_id),
            )

    def create_research_dataset(
        self, user_id: str, institution_id: str, dataset: dict[str, Any],
        records: list[dict[str, Any]], split: dict[str, Any],
    ) -> str:
        dataset_id = _id("ds")
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            for record in records:
                passage_id = record.get("source_passage_id")
                if passage_id:
                    passage = connection.execute(
                        """SELECT p.document_id, d.authorization_status,
                                  d.research_permission_status, d.review_status,
                                  d.malware_scan_status
                           FROM evidence_passages p
                           JOIN documents d ON d.id = p.document_id
                           WHERE p.id = ? AND p.institution_id = ? AND d.institution_id = ?""",
                        (passage_id, institution_id, institution_id),
                    ).fetchone()
                    if not passage:
                        raise PermissionError("Referenced evidence passage is not accessible.")
                    _require_research_document(passage)
                    if record.get("source_document_id") and record["source_document_id"] != passage["document_id"]:
                        raise ValueError("Referenced passage and document do not match.")
                elif record.get("source_document_id"):
                    document = connection.execute(
                        """SELECT institution_id, authorization_status,
                                  research_permission_status, review_status,
                                  malware_scan_status
                           FROM documents WHERE id = ?""",
                        (record["source_document_id"],),
                    ).fetchone()
                    if document and document["institution_id"] != institution_id:
                        raise PermissionError("Referenced source document is not accessible.")
                    if document:
                        _require_research_document(document)
                    if not document and not (record.get("text") or "").strip():
                        raise ValueError("An unregistered source document requires traceable evidence text.")
            connection.execute(
                """INSERT INTO research_datasets
                   (id, institution_id, dataset_version, annotation_version, provenance,
                    split_seed, split_version, split_config_json, split_summary_json, created_by,
                    review_design)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'five_expert_panel')""",
                (dataset_id, institution_id, dataset["dataset_version"], dataset["annotation_version"],
                 dataset["provenance"], split["seed"], split["split_version"],
                 json.dumps(split["proportions"], sort_keys=True), json.dumps(split, sort_keys=True), user_id),
            )
            for record in records:
                connection.execute(
                    """INSERT INTO research_examples
                       (id, dataset_id, example_id, framework, indicator, major_indicator_group,
                        label, text, source_document_id, source_passage_id, annotation_version,
                        annotation_provenance, annotation_status, partition_name)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (_id("ex"), dataset_id, record["example_id"], record["framework"],
                     record["indicator"], record.get("major_indicator_group"), str(record["label"]),
                     record.get("text"), record.get("source_document_id"), record.get("source_passage_id"),
                     record["annotation_version"], record["annotation_provenance"],
                     record["annotation_status"], split["assignments"][record["example_id"]]),
                )
                connection.execute(
                    """INSERT INTO research_example_metadata
                       (dataset_id, example_id, institution_group_id, leakage_group_id,
                        original_prediction_json, source_line)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (dataset_id, record["example_id"],
                     record.get("institution_group_id") or institution_id,
                     record.get("leakage_group_id"), record.get("original_prediction_json"),
                     record.get("source_line")),
                )
            _event(
                connection, institution_id, None, user_id, "research.dataset.submitted",
                {"dataset_id": dataset_id, "dataset_version": dataset["dataset_version"],
                 "example_count": len(records), "split_version": split["split_version"]},
            )
        return dataset_id

    def prepare_research_records(
        self, user_id: str, institution_id: str, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        prepared = [dict(record) for record in records]
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            for record in prepared:
                passage_id = record.get("source_passage_id")
                if passage_id:
                    passage = connection.execute(
                        """SELECT document_id, text FROM evidence_passages
                           WHERE id = ? AND institution_id = ?""",
                        (passage_id, institution_id),
                    ).fetchone()
                    if not passage:
                        raise PermissionError("Referenced evidence passage is not accessible.")
                    if record.get("source_document_id") and record["source_document_id"] != passage["document_id"]:
                        raise ValueError("Referenced passage and document do not match.")
                    record["source_document_id"] = passage["document_id"]
                    if record.get("text") is None:
                        record["text"] = passage["text"]
                elif record.get("source_document_id"):
                    document = connection.execute(
                        "SELECT institution_id FROM documents WHERE id = ?",
                        (record["source_document_id"],),
                    ).fetchone()
                    if document and document["institution_id"] != institution_id:
                        raise PermissionError("Referenced source document is not accessible.")
                    if not document and not (record.get("text") or "").strip():
                        raise ValueError("An unregistered source document requires traceable evidence text.")
        return prepared

    def research_datasets(self, user_id: str, institution_id: str):
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            return connection.execute(
                """SELECT d.id, d.dataset_version, d.annotation_version, d.provenance,
                          d.split_seed, d.split_version, d.split_summary_json, d.verification_status,
                          d.verification_note, d.reviewed_at, d.created_at,
                          COUNT(e.id) AS example_count,
                          SUM(CASE WHEN e.partition_name = 'train' THEN 1 ELSE 0 END) AS train_count,
                          SUM(CASE WHEN e.partition_name = 'validation' THEN 1 ELSE 0 END) AS validation_count,
                          SUM(CASE WHEN e.partition_name = 'test' THEN 1 ELSE 0 END) AS test_count
                   FROM research_datasets d LEFT JOIN research_examples e ON e.dataset_id = d.id
                   WHERE d.institution_id = ? GROUP BY d.id ORDER BY d.created_at DESC""",
                (institution_id,),
            ).fetchall()

    def research_counts(self, user_id: str, institution_id: str) -> dict[str, int]:
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            return {
                "datasets": connection.execute(
                    "SELECT COUNT(*) FROM research_datasets WHERE institution_id = ?", (institution_id,)
                ).fetchone()[0],
                "expert_labeled_examples": connection.execute(
                    """SELECT COUNT(*) FROM research_examples e JOIN research_datasets d ON d.id = e.dataset_id
                       WHERE d.institution_id = ? AND d.verification_status = 'approved'
                         AND EXISTS (SELECT 1 FROM research_annotation_consensus c
                           WHERE c.dataset_id = e.dataset_id AND c.example_id = e.example_id)""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_ratings": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_eqam_ratings": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved' AND r.dimension IN (
                           'semantic_relevance', 'model_confidence', 'evidence_completeness',
                           'source_reliability', 'evidence_strength'
                       )""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_eqam_dimensions": connection.execute(
                    """SELECT COUNT(DISTINCT r.dimension) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND r.dimension IN ('semantic_relevance', 'model_confidence',
                           'evidence_completeness', 'source_reliability', 'evidence_strength')""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_eqam_raters": connection.execute(
                    """SELECT COUNT(DISTINCT r.expert_reference) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND r.dimension IN ('semantic_relevance', 'model_confidence',
                           'evidence_completeness', 'source_reliability', 'evidence_strength')""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_eqam_min_raters_per_dimension": connection.execute(
                    """SELECT COALESCE(MIN(raters), 0) FROM (
                       SELECT COUNT(DISTINCT r.expert_reference) AS raters
                       FROM research_expert_ratings r JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND r.dimension IN ('semantic_relevance', 'model_confidence',
                           'evidence_completeness', 'source_reliability', 'evidence_strength')
                       GROUP BY r.dimension)""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_reference_scores": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND (r.dimension = 'arrs' OR r.dimension LIKE 'rrs:%')""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_reference_dimensions": connection.execute(
                    """SELECT COUNT(DISTINCT r.dimension) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND (r.dimension = 'arrs' OR r.dimension LIKE 'rrs:%')""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_reference_raters": connection.execute(
                    """SELECT COUNT(DISTINCT r.expert_reference) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND (r.dimension = 'arrs' OR r.dimension LIKE 'rrs:%')""",
                    (institution_id,),
                ).fetchone()[0],
                "expert_reference_min_raters_per_dimension": connection.execute(
                    """SELECT COALESCE(MIN(raters), 0) FROM (
                       SELECT COUNT(DISTINCT r.expert_reference) AS raters
                       FROM research_expert_ratings r JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND (r.dimension = 'arrs' OR r.dimension LIKE 'rrs:%')
                       GROUP BY r.dimension)""",
                    (institution_id,),
                ).fetchone()[0],
                "xai_ratings": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND r.dimension LIKE 'xai:%'""",
                    (institution_id,),
                ).fetchone()[0],
                "xai_dimensions": connection.execute(
                    """SELECT COUNT(DISTINCT r.dimension) FROM research_expert_ratings r
                       JOIN research_datasets d ON d.id = r.dataset_id
                       WHERE r.institution_id = ? AND d.verification_status = 'approved'
                         AND r.review_status = 'approved'
                         AND r.dimension LIKE 'xai:%'""",
                    (institution_id,),
                ).fetchone()[0],
                "locked_thresholds": connection.execute(
                    """SELECT COUNT(*) FROM research_thresholds t JOIN research_datasets d ON d.id = t.dataset_id
                       WHERE d.institution_id = ?""",
                    (institution_id,),
                ).fetchone()[0],
                "experiments": connection.execute(
                    "SELECT COUNT(*) FROM research_experiments WHERE institution_id = ?", (institution_id,)
                ).fetchone()[0],
                "completed_experiments": connection.execute(
                    """SELECT COUNT(*) FROM research_experiments e
                       JOIN research_experiment_details x ON x.experiment_id = e.id
                       JOIN research_datasets d ON d.id = e.dataset_id
                       WHERE e.institution_id = ?
                         AND x.execution_state IN ('completed', 'completed_with_limitations')
                         AND json_extract(e.configuration_json, '$.evaluation_scope') = 'readiness'
                         AND d.verification_status = 'approved'""",
                    (institution_id,),
                ).fetchone()[0],
                "completed_retrieval_experiments": connection.execute(
                    """SELECT COUNT(*) FROM research_experiments e
                       JOIN research_experiment_details x ON x.experiment_id = e.id
                       JOIN research_datasets d ON d.id = e.dataset_id
                       WHERE e.institution_id = ?
                         AND x.execution_state IN ('completed', 'completed_with_limitations')
                         AND json_extract(e.configuration_json, '$.evaluation_scope') = 'retrieval'
                         AND d.verification_status = 'approved'""",
                    (institution_id,),
                ).fetchone()[0],
            }

    def research_experiments(self, user_id: str, institution_id: str):
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            return connection.execute(
                """SELECT e.id, e.dataset_id, e.experiment_type, e.configuration_id,
                          e.configuration_json, e.model_version, e.method_version, e.random_seed,
                          e.status, e.result_json, e.warnings_json, e.error_summary,
                          e.created_at, e.completed_at, d.execution_state, d.preflight_json,
                          d.sample_counts_json, d.evaluation_config_json, d.started_at
                   FROM research_experiments e
                   LEFT JOIN research_experiment_details d ON d.experiment_id = e.id
                   WHERE e.institution_id = ? ORDER BY e.created_at DESC LIMIT 50""",
                (institution_id,),
            ).fetchall()

    def research_dataset_bundle(
        self, user_id: str, institution_id: str, dataset_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            dataset = connection.execute(
                """SELECT id, dataset_version, annotation_version, split_seed, split_version,
                          split_summary_json, verification_status, verification_note, review_design,
                          consensus_procedure_id, source_use_clearance_reference,
                          institutional_approval_reference
                   FROM research_datasets WHERE id = ? AND institution_id = ?""",
                (dataset_id, institution_id),
            ).fetchone()
            if not dataset:
                return None
            rows = connection.execute(
                """SELECT e.example_id, e.framework, e.indicator, e.major_indicator_group,
                          e.label AS original_label, COALESCE(c.final_label, e.label) AS label,
                          COALESCE(e.text, p.text) AS text, e.source_document_id,
                          e.source_passage_id, e.annotation_version,
                          e.annotation_status AS source_annotation_status,
                          CASE WHEN c.resolution = 'adjudicated' THEN 'adjudicated'
                               WHEN c.resolution = 'agreement' THEN 'expert_reviewed'
                               ELSE e.annotation_status END AS annotation_status,
                          e.partition_name, m.institution_group_id, m.leakage_group_id,
                          m.original_prediction_json, c.resolution AS annotation_resolution
                   FROM research_examples e
                   LEFT JOIN research_annotation_consensus c
                     ON c.dataset_id = e.dataset_id AND c.example_id = e.example_id
                   LEFT JOIN research_example_metadata m
                     ON m.dataset_id = e.dataset_id AND m.example_id = e.example_id
                   LEFT JOIN evidence_passages p
                     ON p.id = e.source_passage_id AND p.institution_id = ?
                   WHERE e.dataset_id = ? ORDER BY e.example_id""",
                (institution_id, dataset_id),
            ).fetchall()
            return {
                "dataset": dict(dataset),
                "records": [dict(row) for row in rows],
            }

    def dataset_run_requirements(
        self, user_id: str, institution_id: str, dataset_id: str
    ) -> dict[str, Any]:
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            dataset = connection.execute(
                "SELECT 1 FROM research_datasets WHERE id = ? AND institution_id = ?",
                (dataset_id, institution_id),
            ).fetchone()
            if not dataset:
                raise PermissionError("Research dataset access denied.")
            return {
                "locked_threshold": connection.execute(
                    "SELECT 1 FROM research_thresholds WHERE dataset_id = ? LIMIT 1",
                    (dataset_id,),
                ).fetchone() is not None,
                "eqam_rating_count": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings
                       WHERE dataset_id = ? AND review_status = 'approved'
                         AND dimension IN ('semantic_relevance', 'model_confidence',
                           'evidence_completeness', 'source_reliability', 'evidence_strength')""",
                    (dataset_id,),
                ).fetchone()[0],
                "eqam_dimensions": [
                    row["dimension"] for row in connection.execute(
                        """SELECT DISTINCT dimension FROM research_expert_ratings
                           WHERE dataset_id = ? AND review_status = 'approved'
                             AND dimension IN ('semantic_relevance', 'model_confidence',
                               'evidence_completeness', 'source_reliability', 'evidence_strength')""",
                        (dataset_id,),
                    ).fetchall()
                ],
                "eqam_min_raters_per_dimension": connection.execute(
                    """SELECT COALESCE(MIN(rater_count), 0) FROM (
                       SELECT COUNT(DISTINCT expert_reference) AS rater_count
                       FROM research_expert_ratings
                       WHERE dataset_id = ? AND review_status = 'approved'
                         AND dimension IN ('semantic_relevance', 'model_confidence',
                           'evidence_completeness', 'source_reliability', 'evidence_strength')
                       GROUP BY dimension)""",
                    (dataset_id,),
                ).fetchone()[0],
                "readiness_reference_count": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings
                       WHERE dataset_id = ? AND review_status = 'approved'
                         AND (dimension = 'arrs' OR dimension LIKE 'rrs:%')""",
                    (dataset_id,),
                ).fetchone()[0],
                "readiness_reference_dimensions": [
                    row["dimension"] for row in connection.execute(
                        """SELECT DISTINCT dimension FROM research_expert_ratings
                           WHERE dataset_id = ? AND review_status = 'approved'
                             AND (dimension = 'arrs' OR dimension LIKE 'rrs:%')""",
                        (dataset_id,),
                    ).fetchall()
                ],
                "readiness_min_raters_per_dimension": connection.execute(
                    """SELECT COALESCE(MIN(rater_count), 0) FROM (
                       SELECT COUNT(DISTINCT expert_reference) AS rater_count
                       FROM research_expert_ratings
                       WHERE dataset_id = ? AND review_status = 'approved'
                         AND (dimension = 'arrs' OR dimension LIKE 'rrs:%')
                       GROUP BY dimension)""",
                    (dataset_id,),
                ).fetchone()[0],
                "xai_rating_count": connection.execute(
                    """SELECT COUNT(*) FROM research_expert_ratings
                       WHERE dataset_id = ? AND review_status = 'approved'
                         AND dimension LIKE 'xai:%'""",
                    (dataset_id,),
                ).fetchone()[0],
                "xai_dimensions": [
                    row["dimension"] for row in connection.execute(
                        """SELECT DISTINCT dimension FROM research_expert_ratings
                           WHERE dataset_id = ? AND review_status = 'approved'
                             AND dimension LIKE 'xai:%'""",
                        (dataset_id,),
                    ).fetchall()
                ],
                "xai_min_raters_per_dimension": connection.execute(
                    """SELECT COALESCE(MIN(rater_count), 0) FROM (
                       SELECT COUNT(DISTINCT expert_reference) AS rater_count
                       FROM research_expert_ratings
                       WHERE dataset_id = ? AND review_status = 'approved'
                         AND dimension LIKE 'xai:%'
                       GROUP BY dimension)""",
                    (dataset_id,),
                ).fetchone()[0],
            }

    def get_research_experiment(
        self, user_id: str, institution_id: str, experiment_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            row = connection.execute(
                """SELECT e.id, e.dataset_id, e.experiment_type, e.configuration_id,
                          e.configuration_json, e.model_version, e.method_version,
                          e.random_seed, e.status, e.result_json, e.warnings_json,
                          e.error_summary, e.created_at, e.completed_at,
                          d.execution_state, d.preflight_json, d.sample_counts_json,
                          d.evaluation_config_json, d.started_at
                   FROM research_experiments e
                   LEFT JOIN research_experiment_details d ON d.experiment_id = e.id
                   WHERE e.id = ? AND e.institution_id = ?""",
                (experiment_id, institution_id),
            ).fetchone()
            return dict(row) if row else None

    def persist_research_execution(
        self,
        user_id: str,
        institution_id: str,
        *,
        dataset_id: str | None,
        ablation_id: str,
        seed: int,
        model_version: str | None,
        execution_state: str,
        preflight: dict[str, Any],
        warnings: list[str] | None = None,
        safe_error: str | None = None,
        results: dict[str, Any] | None = None,
        predictions: list[dict[str, Any]] | None = None,
        sample_counts: dict[str, int] | None = None,
        evaluation_config: dict[str, Any] | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ) -> str:
        allowed_states = {
            "blocked_missing_data", "blocked_missing_model", "blocked_methodology_review",
            "not_implemented", "failed", "completed", "completed_with_limitations",
        }
        if execution_state not in allowed_states:
            raise ValueError("Unsupported research execution state.")
        predictions = predictions or []
        if execution_state in {"completed", "completed_with_limitations"}:
            if results is None or not predictions:
                raise ValueError("Completed experiments require real results and held-out predictions.")
        elif results is not None or predictions:
            raise ValueError("Blocked or failed experiments cannot contain results or predictions.")
        run_id = _id("exp")
        detail_status = (
            execution_state if execution_state in {"failed", "completed", "completed_with_limitations"}
            else "blocked_missing_data" if execution_state == "blocked_missing_data"
            else "not_implemented"
        )
        stored_config = {
            "dataset_id": dataset_id,
            "ablation_id": ablation_id,
            "dataset_version": (
                preflight.get("dataset", {}).get("dataset_version")
                if preflight.get("dataset") else None
            ),
            "partition_manifest_version": (
                preflight.get("dataset", {}).get("partition_manifest_version")
                if preflight.get("dataset") else None
            ),
            "protocol_version": preflight.get("protocol_version"),
            "protocol_manifest_sha256": preflight.get("protocol_manifest_sha256"),
            "evaluation_scope": preflight.get("evaluation_scope", "readiness"),
            "model_artifact_sha256": preflight.get("model", {}).get("artifact_sha256"),
            "random_seed": seed,
        }
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            if dataset_id:
                dataset = connection.execute(
                    "SELECT verification_status FROM research_datasets WHERE id = ? AND institution_id = ?",
                    (dataset_id, institution_id),
                ).fetchone()
                if not dataset:
                    raise PermissionError("Research dataset access denied.")
                stored_config["dataset_review_status"] = dataset["verification_status"]
            connection.execute(
                """INSERT INTO research_experiments
                   (id, institution_id, dataset_id, experiment_type, configuration_id,
                    configuration_json, model_version, method_version, random_seed, status,
                    result_json, warnings_json, error_summary, created_by, completed_at)
                   VALUES (?, ?, ?, 'ablation', ?, ?, ?, 'research-runner-v1', ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, institution_id, dataset_id, ablation_id, json.dumps(stored_config, sort_keys=True),
                 model_version, seed, detail_status,
                 json.dumps(results, sort_keys=True) if results is not None else None,
                 json.dumps(warnings or [], sort_keys=True), safe_error, user_id, completed_at),
            )
            if predictions:
                if not dataset_id:
                    raise ValueError("Held-out predictions require an approved research dataset.")
                for prediction in predictions:
                    source = connection.execute(
                        """SELECT e.partition_name, COALESCE(c.final_label, e.label) AS label
                           FROM research_examples e
                           LEFT JOIN research_annotation_consensus c
                             ON c.dataset_id = e.dataset_id AND c.example_id = e.example_id
                           WHERE e.dataset_id = ? AND e.example_id = ?""",
                        (dataset_id, prediction["example_id"]),
                    ).fetchone()
                    ground_truth = prediction.get("ground_truth")
                    if (
                        not source
                        or source["partition_name"] != prediction.get("partition_name")
                        or not isinstance(ground_truth, dict)
                        or str(ground_truth.get("label")) != source["label"]
                    ):
                        raise ValueError("Stored prediction must match its immutable dataset partition and label.")
                    connection.execute(
                        """INSERT INTO research_predictions
                           (id, experiment_id, example_id, partition_name, prediction_json, ground_truth_json)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (_id("pred"), run_id, prediction["example_id"], prediction["partition_name"],
                         json.dumps(prediction["prediction"], sort_keys=True),
                         json.dumps(ground_truth, sort_keys=True)),
                    )
            connection.execute(
                """INSERT INTO research_experiment_details
                   (experiment_id, execution_state, preflight_json, sample_counts_json,
                    evaluation_config_json, started_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (run_id, execution_state, json.dumps(preflight, sort_keys=True),
                 json.dumps(sample_counts or {}, sort_keys=True),
                 json.dumps(evaluation_config or {}, sort_keys=True), started_at),
            )
            _event(
                connection, institution_id, None, user_id, "research.experiment.execution_recorded",
                {"experiment_id": run_id, "configuration_id": ablation_id,
                 "execution_state": execution_state},
            )
        return run_id

    def persist_expert_ratings(
        self, user_id: str, institution_id: str, dataset_id: str, ratings: list[dict[str, Any]]
    ) -> list[str]:
        rating_ids = []
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            dataset = connection.execute(
                """SELECT 1 FROM research_datasets WHERE id = ? AND institution_id = ?
                   AND verification_status = 'approved'""",
                (dataset_id, institution_id),
            ).fetchone()
            if not dataset:
                raise PermissionError("Research dataset access denied.")
            for rating in ratings:
                source = connection.execute(
                    """SELECT partition_name FROM research_examples
                       WHERE dataset_id = ? AND example_id = ?""",
                    (dataset_id, rating["case_id"]),
                ).fetchone()
                if not source:
                    raise ValueError("Expert ratings must reference a case in the selected dataset.")
                rating_id = _id("rating")
                connection.execute(
                    """INSERT INTO research_expert_ratings
                       (id, institution_id, dataset_id, case_id, expert_reference, dimension,
                        score, partition_name, rating_scale_json, rating_provenance, annotation_version,
                        status, created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (rating_id, institution_id, dataset_id, rating["case_id"],
                     rating["expert_reference"], rating["dimension"], rating["score"],
                     source["partition_name"], json.dumps(rating["rating_scale"], sort_keys=True),
                     rating["provenance"], rating["annotation_version"], rating["status"], user_id),
                )
                rating_ids.append(rating_id)
            _event(
                connection, institution_id, None, user_id, "research.expert_ratings.stored",
                {"dataset_id": dataset_id, "rating_count": len(ratings)},
            )
        return rating_ids

    def review_expert_rating(
        self, reviewer_id: str, institution_id: str, rating_id: str, decision: str, note: str
    ):
        with self.connection() as connection:
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (reviewer_id, institution_id),
            ).fetchone()
            rating = connection.execute(
                """SELECT created_by, review_status FROM research_expert_ratings
                   WHERE id = ? AND institution_id = ?""",
                (rating_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator" or not rating:
                raise PermissionError("Administrator access to this rating is required.")
            if rating["created_by"] == reviewer_id:
                raise PermissionError("An expert rating must be reviewed by someone other than its submitter.")
            if rating["review_status"] != "submitted":
                raise ValueError("Only submitted expert ratings can be reviewed.")
            if decision not in {"approved", "rejected"} or not note.strip():
                raise ValueError("A review decision and rationale are required.")
            connection.execute(
                """UPDATE research_expert_ratings
                   SET review_status = ?, review_note = ?, reviewed_by = ?,
                       reviewed_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (decision, note.strip(), reviewer_id, rating_id),
            )
            _event(
                connection, institution_id, None, reviewer_id, "research.expert_rating.reviewed",
                {"rating_id": rating_id, "decision": decision},
            )

    def review_research_dataset(
        self,
        reviewer_id: str,
        institution_id: str,
        dataset_id: str,
        decision: str,
        note: str,
        *,
        source_use_clearance_reference: str | None = None,
        institutional_approval_reference: str | None = None,
    ):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (reviewer_id, institution_id),
            ).fetchone()
            dataset = connection.execute(
                """SELECT created_by, verification_status, review_design FROM research_datasets
                   WHERE id = ? AND institution_id = ?""",
                (dataset_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator" or not dataset:
                raise PermissionError("Administrator access to this dataset is required.")
            if dataset["created_by"] == reviewer_id:
                raise PermissionError("A dataset must be reviewed by someone other than its submitter.")
            if dataset["verification_status"] != "submitted":
                raise ValueError("Only submitted datasets can be reviewed.")
            if decision not in {"approved", "rejected"} or not note.strip():
                raise ValueError("A review decision and rationale are required.")
            if decision == "approved":
                if dataset["review_design"] != "five_expert_panel":
                    raise ValueError(
                        "Legacy two-review datasets cannot receive research approval; create a five-expert-panel dataset."
                    )
                source_clearance = (source_use_clearance_reference or "").strip()
                institutional_approval = (institutional_approval_reference or "").strip()
                if not source_clearance or not institutional_approval:
                    raise ValueError(
                        "Source-use clearance and institutional approval references are required."
                    )
                examples = connection.execute(
                    "SELECT example_id FROM research_examples WHERE dataset_id = ?",
                    (dataset_id,),
                ).fetchall()
                if not examples:
                    raise ValueError("An empty dataset cannot be approved.")
                panel_reviewer_ids: set[str] | None = None
                consensus_procedures: set[tuple[str, str]] = set()
                for example in examples:
                    source = connection.execute(
                        """SELECT e.source_document_id, e.source_passage_id
                           FROM research_examples e
                           WHERE e.dataset_id = ? AND e.example_id = ?""",
                        (dataset_id, example["example_id"]),
                    ).fetchone()
                    if not source or not source["source_document_id"]:
                        raise ValueError(
                            f"Example {example['example_id']} has no verifiable source-document provenance."
                        )
                    document = connection.execute(
                        """SELECT id, checksum, extraction_status, authorization_status,
                                  research_permission_status, review_status, malware_scan_status
                           FROM documents
                           WHERE id = ? AND institution_id = ?""",
                        (source["source_document_id"], institution_id),
                    ).fetchone()
                    if (
                        not document or not document["checksum"]
                        or document["extraction_status"] not in {"success", "completed"}
                    ):
                        raise ValueError(
                            f"Example {example['example_id']} source document is not an extracted, checksummed institutional document."
                        )
                    try:
                        _require_research_document(document)
                    except ValueError as error:
                        raise ValueError(
                            f"Example {example['example_id']} source document is not authorized for research use."
                        ) from error
                    if source["source_passage_id"]:
                        passage = connection.execute(
                            """SELECT 1 FROM evidence_passages
                               WHERE id = ? AND document_id = ? AND institution_id = ?""",
                            (
                                source["source_passage_id"], source["source_document_id"],
                                institution_id,
                            ),
                        ).fetchone()
                        if not passage:
                            raise ValueError(
                                f"Example {example['example_id']} has inconsistent source-passage provenance."
                            )
                    reviews = connection.execute(
                        """SELECT r.reviewer_id, r.rubric_version
                           FROM research_expert_panel_reviews r
                           JOIN research_expert_qualifications q
                             ON q.expert_id = r.reviewer_id AND q.institution_id = ?
                            AND q.qualification_status = 'verified'
                           WHERE r.dataset_id = ? AND r.example_id = ?""",
                        (institution_id, dataset_id, example["example_id"]),
                    ).fetchall()
                    current_panel_ids = {row["reviewer_id"] for row in reviews}
                    rubric_versions = {row["rubric_version"] for row in reviews}
                    if len(current_panel_ids) != 5 or len(rubric_versions) != 1:
                        raise ValueError(
                            f"Example {example['example_id']} requires five distinct, qualified expert ratings under one rubric version."
                        )
                    if panel_reviewer_ids is None:
                        panel_reviewer_ids = current_panel_ids
                    elif panel_reviewer_ids != current_panel_ids:
                        raise ValueError("Every case must be reviewed by the same five qualified experts.")
                    consensus = connection.execute(
                        """SELECT final_label, resolution, procedure_id, procedure_version
                           FROM research_expert_panel_consensus
                           WHERE dataset_id = ? AND example_id = ? AND institution_id = ?""",
                        (dataset_id, example["example_id"], institution_id),
                    ).fetchone()
                    if not consensus:
                        raise ValueError(
                            f"Example {example['example_id']} requires consensus under a recorded procedure."
                        )
                    if (
                        connection.execute(
                            """SELECT 1 FROM research_consensus_procedures
                               WHERE institution_id = ? AND procedure_id = ?
                                 AND procedure_version = ?""",
                            (institution_id, consensus["procedure_id"], consensus["procedure_version"]),
                        ).fetchone() is None
                    ):
                        raise ValueError("The consensus procedure approval is no longer available.")
                    consensus_procedures.add(
                        (consensus["procedure_id"], consensus["procedure_version"])
                    )
                    connection.execute(
                        """INSERT INTO research_annotation_consensus
                           (dataset_id, example_id, final_label, resolution)
                           VALUES (?, ?, ?, ?)""",
                        (
                            dataset_id, example["example_id"], consensus["final_label"],
                            "adjudicated" if consensus["resolution"] == "adjudicated" else "agreement",
                        ),
                    )
                if len(consensus_procedures) != 1:
                    raise ValueError("All cases must use one consistent approved consensus procedure version.")
            connection.execute(
                """UPDATE research_datasets
                   SET verification_status = ?, verification_note = ?, reviewed_by = ?,
                       reviewed_at = CURRENT_TIMESTAMP,
                       source_use_clearance_reference = ?,
                       institutional_approval_reference = ?,
                       consensus_procedure_id = (
                           SELECT procedure_id || ':' || procedure_version
                           FROM research_expert_panel_consensus
                           WHERE dataset_id = ? LIMIT 1
                       )
                   WHERE id = ?""",
                (
                    decision, note.strip(), reviewer_id,
                    source_use_clearance_reference.strip() if source_use_clearance_reference else None,
                    institutional_approval_reference.strip() if institutional_approval_reference else None,
                    dataset_id, dataset_id,
                ),
            )
            _event(
                connection, institution_id, None, reviewer_id, "research.dataset.reviewed",
                {"dataset_id": dataset_id, "decision": decision},
            )
            if decision == "approved":
                _event(
                    connection, institution_id, None, reviewer_id, "research.dataset.approved",
                    {"dataset_id": dataset_id},
                )

    def create_research_import(
        self,
        user_id: str,
        institution_id: str,
        filename: str,
        storage_key: str,
        sha256: str,
        byte_count: int,
    ) -> str:
        import_id = _id("imp")
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            connection.execute(
                """INSERT INTO research_dataset_imports
                   (id, institution_id, created_by, original_filename, storage_key,
                    sha256, byte_count, status, report_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'processing', '{}')""",
                (import_id, institution_id, user_id, filename[:255], storage_key,
                 sha256, byte_count),
            )
        return import_id

    def finish_research_import(
        self,
        import_id: str,
        institution_id: str,
        status: str,
        report: dict[str, Any],
        dataset_id: str | None = None,
    ):
        if status not in {"accepted", "rejected"}:
            raise ValueError("Unsupported research import status.")
        with self.connection() as connection:
            updated = connection.execute(
                """UPDATE research_dataset_imports
                   SET status = ?, report_json = ?, dataset_id = ?
                   WHERE id = ? AND institution_id = ?""",
                (status, json.dumps(report, sort_keys=True), dataset_id, import_id, institution_id),
            ).rowcount
            if updated != 1:
                raise ValueError("Research import record was not found.")

    def get_research_import(
        self, user_id: str, institution_id: str, import_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            row = connection.execute(
                """SELECT id, dataset_id, original_filename, sha256, byte_count,
                          status, report_json, created_at
                   FROM research_dataset_imports
                   WHERE id = ? AND institution_id = ?""",
                (import_id, institution_id),
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            result["report"] = json.loads(result.pop("report_json"))
            return result

    def annotation_review_queue(
        self, reviewer_id: str, institution_id: str, dataset_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (reviewer_id, institution_id),
            ).fetchone()
            dataset = connection.execute(
                """SELECT created_by, verification_status, review_design FROM research_datasets
                   WHERE id = ? AND institution_id = ?""",
                (dataset_id, institution_id),
            ).fetchone()
            if (
                not membership or membership["role"] not in {"administrator", "evaluator"}
                or not dataset
            ):
                raise PermissionError("Authorized institutional research access is required.")
            if dataset["created_by"] == reviewer_id:
                raise PermissionError("The dataset submitter cannot review annotations in their import.")
            if (
                dataset["verification_status"] != "submitted"
                or dataset["review_design"] != "five_expert_panel"
            ):
                raise ValueError("The expert-panel queue is available only for pending five-expert datasets.")
            qualification = connection.execute(
                """SELECT qualification_status FROM research_expert_qualifications
                   WHERE institution_id = ? AND expert_id = ?""",
                (institution_id, reviewer_id),
            ).fetchone()
            if not qualification or qualification["qualification_status"] != "verified":
                raise PermissionError("Verified expert qualification is required to review this panel.")
            rows = connection.execute(
                """SELECT e.example_id, e.framework, e.indicator,
                          COALESCE(e.text, p.text) AS text, e.source_document_id,
                          e.source_passage_id
                   FROM research_examples e
                   LEFT JOIN evidence_passages p
                     ON p.id = e.source_passage_id AND p.institution_id = ?
                   WHERE e.dataset_id = ?
                     AND NOT EXISTS (
                         SELECT 1 FROM research_expert_panel_reviews r
                         WHERE r.dataset_id = e.dataset_id
                           AND r.example_id = e.example_id AND r.reviewer_id = ?
                     )
                   ORDER BY e.example_id LIMIT 50""",
                (institution_id, dataset_id, reviewer_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def verify_expert_qualification(
        self,
        verifier_id: str,
        institution_id: str,
        expert_id: str,
        qualification_reference: str,
        note: str,
        status: str = "verified",
    ) -> None:
        if status not in {"verified", "rejected"}:
            raise ValueError("Qualification status must be verified or rejected.")
        reference = qualification_reference.strip()
        rationale = note.strip()
        if not reference or not rationale:
            raise ValueError("Qualification evidence reference and rationale are required.")
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            verifier = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (verifier_id, institution_id),
            ).fetchone()
            expert = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (expert_id, institution_id),
            ).fetchone()
            if (
                not verifier or verifier["role"] != "administrator" or not expert
                or expert["role"] not in {"administrator", "evaluator"}
            ):
                raise PermissionError("An institutional administrator must verify an active member's qualification.")
            if verifier_id == expert_id:
                raise PermissionError("Reviewers cannot verify their own expert qualification.")
            connection.execute(
                """INSERT INTO research_expert_qualifications
                   (institution_id, expert_id, qualification_status,
                    qualification_reference, verification_note, verified_by)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(institution_id, expert_id) DO UPDATE SET
                     qualification_status = excluded.qualification_status,
                     qualification_reference = excluded.qualification_reference,
                     verification_note = excluded.verification_note,
                     verified_by = excluded.verified_by,
                     verified_at = CURRENT_TIMESTAMP""",
                (institution_id, expert_id, status, reference, rationale, verifier_id),
            )
            _event(
                connection, institution_id, None, verifier_id,
                "research.expert_qualification.recorded",
                {"expert_id": expert_id, "status": status},
            )

    def register_consensus_procedure(
        self,
        approver_id: str,
        institution_id: str,
        procedure_id: str,
        procedure_version: str,
        approval_reference: str,
        approving_authority: str,
        rationale: str,
    ) -> None:
        values = [
            procedure_id.strip(), procedure_version.strip(), approval_reference.strip(),
            approving_authority.strip(), rationale.strip(),
        ]
        if not all(values):
            raise ValueError("Procedure identity, version, approval reference, authority, and rationale are required.")
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (approver_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator":
                raise PermissionError("Institution administrator access is required.")
            connection.execute(
                """INSERT INTO research_consensus_procedures
                   (institution_id, procedure_id, procedure_version, approval_reference,
                    approving_authority, rationale, approved_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (institution_id, *values, approver_id),
            )
            _event(
                connection, institution_id, None, approver_id,
                "research.consensus_procedure.recorded",
                {"procedure_id": values[0], "procedure_version": values[1]},
            )

    def submit_expert_panel_reviews(
        self,
        reviewer_id: str,
        institution_id: str,
        dataset_id: str,
        reviews: list[dict[str, Any]],
    ) -> int:
        if not reviews or len({item.get("example_id") for item in reviews}) != len(reviews):
            raise ValueError("A non-empty submission must contain each example at most once.")
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (reviewer_id, institution_id),
            ).fetchone()
            dataset = connection.execute(
                """SELECT created_by, verification_status, review_design
                   FROM research_datasets WHERE id = ? AND institution_id = ?""",
                (dataset_id, institution_id),
            ).fetchone()
            qualification = connection.execute(
                """SELECT qualification_status FROM research_expert_qualifications
                   WHERE institution_id = ? AND expert_id = ?""",
                (institution_id, reviewer_id),
            ).fetchone()
            if (
                not membership or membership["role"] not in {"administrator", "evaluator"}
                or not dataset
            ):
                raise PermissionError("Authorized institutional research access is required.")
            if dataset["created_by"] == reviewer_id:
                raise PermissionError("The dataset submitter cannot review annotations in their import.")
            if not qualification or qualification["qualification_status"] != "verified":
                raise PermissionError("Verified expert qualification is required to submit panel ratings.")
            if dataset["verification_status"] != "submitted":
                raise ValueError("Panel reviews can only be submitted while the dataset is pending review.")
            if dataset["review_design"] != "five_expert_panel":
                raise ValueError("This legacy dataset does not support the five-expert panel workflow.")
            for item in reviews:
                example_id = str(item.get("example_id", "")).strip()
                rubric_version = str(item.get("rubric_version", "")).strip()
                note = str(item.get("note", "")).strip()
                if not example_id or not rubric_version or not note:
                    raise ValueError("Each panel review requires an evidence ID, rubric version, and rationale.")
                example = connection.execute(
                    "SELECT 1 FROM research_examples WHERE dataset_id = ? AND example_id = ?",
                    (dataset_id, example_id),
                ).fetchone()
                if not example:
                    raise ValueError(f"Example {example_id} is not in this dataset.")
                existing = connection.execute(
                    """SELECT reviewer_id, rubric_version FROM research_expert_panel_reviews
                       WHERE dataset_id = ? AND example_id = ?""",
                    (dataset_id, example_id),
                ).fetchall()
                if len(existing) >= 5:
                    raise ValueError(f"Example {example_id} already has five expert judgments.")
                if any(row["reviewer_id"] == reviewer_id for row in existing):
                    raise ValueError(f"Reviewer has already submitted an independent judgment for {example_id}.")
                if any(row["rubric_version"] != rubric_version for row in existing):
                    raise ValueError(f"Example {example_id} has judgments under a different rubric version.")
                label = _canonical_relevance_label(item.get("label"))
                continuous_ratings = item.get("continuous_ratings") or {}
                if not isinstance(continuous_ratings, dict):
                    raise ValueError("Continuous ratings must be a mapping of rubric dimension to score.")
                for dimension, score in continuous_ratings.items():
                    if not isinstance(dimension, str) or not dimension.strip():
                        raise ValueError("Continuous rating dimensions must be named.")
                    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
                        raise ValueError("Continuous rubric scores must be finite numbers.")
                    if not 0 <= score <= 1:
                        raise ValueError("Continuous rubric scores must be normalized to [0, 1].")
                connection.execute(
                    """INSERT INTO research_expert_panel_reviews
                       (dataset_id, example_id, reviewer_id, rubric_version,
                        categorical_label, continuous_ratings_json, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (dataset_id, example_id, reviewer_id, rubric_version, label,
                     json.dumps(continuous_ratings, sort_keys=True), note),
                )
            _event(
                connection, institution_id, None, reviewer_id,
                "research.expert_panel_reviews.submitted",
                {"dataset_id": dataset_id, "review_count": len(reviews)},
            )
        return len(reviews)

    def expert_panel_agreement(
        self, requester_id: str, institution_id: str, dataset_id: str
    ) -> dict[str, Any]:
        from .research_validation import fleiss_kappa, icc_2_1

        with self.connection() as connection:
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (requester_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator":
                raise PermissionError("Institution administrator access is required for panel statistics.")
            dataset = connection.execute(
                "SELECT 1 FROM research_datasets WHERE id = ? AND institution_id = ?",
                (dataset_id, institution_id),
            ).fetchone()
            if not dataset:
                raise PermissionError("Research dataset access denied.")
            rows = connection.execute(
                """SELECT e.example_id, r.reviewer_id, r.categorical_label,
                          r.continuous_ratings_json
                   FROM research_examples e
                   LEFT JOIN (
                       SELECT p.*
                       FROM research_expert_panel_reviews p
                       JOIN research_expert_qualifications q
                         ON q.expert_id = p.reviewer_id AND q.institution_id = ?
                        AND q.qualification_status = 'verified'
                       WHERE p.dataset_id = ?
                   ) r ON r.dataset_id = e.dataset_id AND r.example_id = e.example_id
                   WHERE e.dataset_id = ?
                   ORDER BY e.example_id, r.reviewer_id""",
                (institution_id, dataset_id, dataset_id),
            ).fetchall()
        by_case: dict[str, list[Any]] = defaultdict(list)
        for row in rows:
            by_case[row["example_id"]].append(row)
        complete_cases = [
            case_rows for case_rows in by_case.values()
            if len({row["reviewer_id"] for row in case_rows}) == 5
        ]
        categorical = fleiss_kappa([
            [row["categorical_label"] for row in case_rows]
            for case_rows in complete_cases
        ])
        dimensions = sorted({
            dimension
            for case_rows in complete_cases
            for row in case_rows
            for dimension in json.loads(row["continuous_ratings_json"])
        })
        continuous: dict[str, Any] = {}
        for dimension in dimensions:
            complete_dimension_cases = []
            for case_rows in complete_cases:
                scores = [
                    json.loads(row["continuous_ratings_json"]).get(dimension)
                    for row in case_rows
                ]
                if all(score is not None for score in scores):
                    complete_dimension_cases.append(scores)
            continuous[dimension] = {
                "complete_case_count": len(complete_dimension_cases),
                "icc_2_1_candidate": (
                    icc_2_1(complete_dimension_cases)
                    if len(complete_dimension_cases) >= 2 else None
                ),
                "status": (
                    "requires_researcher_decision"
                    if len(complete_dimension_cases) >= 2
                    else "undefined_insufficient_complete_cases"
                ),
            }
        return {
            "dataset_id": dataset_id,
            "required_raters_per_case": 5,
            "complete_categorical_case_count": len(complete_cases),
            "incomplete_case_count": len(by_case) - len(complete_cases),
            "missing_rating_policy": "complete_cases_only",
            "fleiss_kappa": categorical,
            "continuous_ratings": continuous,
            "icc_model_status": (
                "requires_researcher_decision"
                if any(item["complete_case_count"] >= 2 for item in continuous.values())
                else "undefined_insufficient_complete_cases"
            ),
            "icc_note": "ICC(2,1) values are diagnostic candidates only; the dissertation does not specify the ICC model.",
        }

    def record_expert_panel_consensus(
        self,
        resolver_id: str,
        institution_id: str,
        dataset_id: str,
        example_id: str,
        final_label: str | bool,
        resolution: str,
        procedure_id: str,
        procedure_version: str,
        note: str,
    ) -> None:
        if resolution not in {"consensus", "adjudicated"}:
            raise ValueError("Resolution must be consensus or adjudicated.")
        rationale = note.strip()
        if not rationale:
            raise ValueError("A consensus rationale is required.")
        label = _canonical_relevance_label(final_label)
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (resolver_id, institution_id),
            ).fetchone()
            if not membership or membership["role"] != "administrator":
                raise PermissionError("Institution administrator access is required to record consensus.")
            procedure = connection.execute(
                """SELECT 1 FROM research_consensus_procedures
                   WHERE institution_id = ? AND procedure_id = ? AND procedure_version = ?""",
                (institution_id, procedure_id, procedure_version),
            ).fetchone()
            if not procedure:
                raise ValueError("The cited consensus procedure has no recorded institutional approval.")
            example = connection.execute(
                """SELECT verification_status, review_design FROM research_datasets
                   WHERE id = ? AND institution_id = ?""",
                (dataset_id, institution_id),
            ).fetchone()
            if not example or example["review_design"] != "five_expert_panel":
                raise PermissionError("A five-expert-panel dataset is required.")
            if example["verification_status"] != "submitted":
                raise ValueError("Consensus can only be recorded before dataset approval or rejection.")
            reviews = connection.execute(
                """SELECT r.reviewer_id, r.rubric_version
                   FROM research_expert_panel_reviews r
                   JOIN research_expert_qualifications q
                     ON q.expert_id = r.reviewer_id AND q.institution_id = ?
                    AND q.qualification_status = 'verified'
                   WHERE r.dataset_id = ? AND r.example_id = ?""",
                (institution_id, dataset_id, example_id),
            ).fetchall()
            if len({row["reviewer_id"] for row in reviews}) != 5:
                raise ValueError("Five distinct, currently qualified expert judgments are required.")
            if len({row["rubric_version"] for row in reviews}) != 1:
                raise ValueError("All five expert judgments must use the same rubric version.")
            connection.execute(
                """INSERT INTO research_expert_panel_consensus
                   (dataset_id, example_id, institution_id, final_label, resolution,
                    procedure_id, procedure_version, resolved_by, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (dataset_id, example_id, institution_id, label, resolution, procedure_id,
                 procedure_version, resolver_id, rationale),
            )
            _event(
                connection, institution_id, None, resolver_id,
                (
                    "research.expert_panel_consensus.adjudicated"
                    if resolution == "adjudicated"
                    else "research.expert_panel_consensus.recorded"
                ),
                {"dataset_id": dataset_id, "example_id": example_id, "resolution": resolution},
            )

    def submit_annotation_reviews(
        self,
        reviewer_id: str,
        institution_id: str,
        dataset_id: str,
        reviews: list[dict[str, Any]],
    ) -> int:
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            membership = connection.execute(
                """SELECT role FROM institution_memberships
                   WHERE user_id = ? AND institution_id = ? AND status = 'active'""",
                (reviewer_id, institution_id),
            ).fetchone()
            dataset = connection.execute(
                """SELECT created_by, verification_status FROM research_datasets
                   WHERE id = ? AND institution_id = ?""",
                (dataset_id, institution_id),
            ).fetchone()
            if (
                not membership or membership["role"] not in {"administrator", "evaluator"}
                or not dataset
            ):
                raise PermissionError("Authorized institutional research access is required.")
            if dataset["created_by"] == reviewer_id:
                raise PermissionError("The dataset submitter cannot review annotations in their import.")
            if dataset["verification_status"] != "submitted":
                raise ValueError("Annotations can only be reviewed before dataset approval or rejection.")
            if len({item["example_id"] for item in reviews}) != len(reviews):
                raise ValueError("An example can appear only once in a review submission.")
            for item in reviews:
                example = connection.execute(
                    "SELECT label FROM research_examples WHERE dataset_id = ? AND example_id = ?",
                    (dataset_id, item["example_id"]),
                ).fetchone()
                if not example:
                    raise ValueError(f"Example {item['example_id']} is not in this dataset.")
                existing = connection.execute(
                    """SELECT reviewer_id, review_stage, label FROM research_annotation_reviews
                       WHERE dataset_id = ? AND example_id = ?""",
                    (dataset_id, item["example_id"]),
                ).fetchall()
                independent = [row for row in existing if row["review_stage"] == "independent"]
                reviewers = {row["reviewer_id"] for row in independent}
                labels = {row["label"] for row in independent}
                decision = item["decision"]
                label = _canonical_relevance_label(item["label"])
                note = item["note"].strip()
                if not note:
                    raise ValueError("Each annotation review requires a rationale.")
                if decision in {"confirm", "correct"}:
                    if len(reviewers) >= 2 or reviewer_id in reviewers:
                        raise ValueError("This example already has two independent reviews.")
                    if (decision == "confirm") != (
                        label == _canonical_relevance_label(example["label"])
                    ):
                        raise ValueError("The review decision must match whether the label is confirmed or corrected.")
                    stage = "independent"
                elif decision == "adjudicate":
                    if (
                        len(reviewers) != 2 or len(labels) < 2 or reviewer_id in reviewers
                        or any(row["review_stage"] == "adjudication" for row in existing)
                    ):
                        raise ValueError("Adjudication requires two disagreeing reviewers and a third independent reviewer.")
                    stage = "adjudication"
                else:
                    raise ValueError("Unsupported annotation review decision.")
                connection.execute(
                    """INSERT INTO research_annotation_reviews
                       (id, dataset_id, example_id, reviewer_id, review_stage, label, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (_id("arv"), dataset_id, item["example_id"], reviewer_id, stage, label, note),
                )
                if decision == "correct":
                    _event(
                        connection, institution_id, None, reviewer_id,
                        "research.annotation.corrected",
                        {"dataset_id": dataset_id, "example_id": item["example_id"]},
                    )
            _event(
                connection, institution_id, None, reviewer_id, "research.annotations.reviewed",
                {"dataset_id": dataset_id, "review_count": len(reviews)},
            )
        return len(reviews)

    def persist_research_experiment(self, user_id: str, institution_id: str, run: dict[str, Any]) -> str:
        run_id = _id("exp")
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            if run.get("dataset_id"):
                dataset = connection.execute(
                    """SELECT 1 FROM research_datasets
                       WHERE id = ? AND institution_id = ? AND verification_status = 'approved'""",
                    (run["dataset_id"], institution_id),
                ).fetchone()
                if not dataset:
                    raise PermissionError("An independently approved research dataset is required.")
            connection.execute(
                """INSERT INTO research_experiments
                   (id, institution_id, dataset_id, experiment_type, configuration_id,
                    configuration_json, model_version, method_version, random_seed, status,
                    result_json, warnings_json, error_summary, created_by, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, institution_id, run.get("dataset_id"), run["experiment_type"],
                 run["configuration_id"], json.dumps(run["configuration"], sort_keys=True),
                 run.get("model_version"), run["method_version"], run["random_seed"],
                 run["status"], json.dumps(run["results"], sort_keys=True) if run.get("results") is not None else None,
                 json.dumps(run.get("warnings", []), sort_keys=True), run.get("error_summary"),
                 user_id, run.get("completed_at")),
            )
            _event(
                connection, institution_id, None, user_id, "research.experiment.stored",
                {"experiment_id": run_id, "configuration_id": run["configuration_id"],
                 "status": run["status"]},
            )
        return run_id

    def persist_research_predictions(
        self, user_id: str, institution_id: str, experiment_id: str, predictions: list[dict[str, Any]]
    ):
        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            experiment = connection.execute(
                """SELECT e.dataset_id, e.status, d.verification_status
                   FROM research_experiments e JOIN research_datasets d ON d.id = e.dataset_id
                   WHERE e.id = ? AND e.institution_id = ?""",
                (experiment_id, institution_id),
            ).fetchone()
            if (
                not experiment
                or not experiment["dataset_id"]
                or experiment["verification_status"] != "approved"
            ):
                raise PermissionError("Research experiment access denied.")
            if experiment["status"] not in {"running", "completed", "completed_with_limitations"}:
                raise ValueError("Predictions can only be stored for an active or completed experiment.")
            for prediction in predictions:
                source = connection.execute(
                    """SELECT e.partition_name, COALESCE(c.final_label, e.label) AS label
                       FROM research_examples e
                       LEFT JOIN research_annotation_consensus c
                         ON c.dataset_id = e.dataset_id AND c.example_id = e.example_id
                       WHERE e.dataset_id = ? AND e.example_id = ?""",
                    (experiment["dataset_id"], prediction["example_id"]),
                ).fetchone()
                if not source or source["partition_name"] != prediction["partition_name"]:
                    raise ValueError("Prediction partition does not match its immutable dataset assignment.")
                ground_truth = prediction["ground_truth"]
                if not isinstance(ground_truth, dict) or (
                    "acceptable" in ground_truth
                    and _canonical_relevance_label(ground_truth["acceptable"])
                    != _canonical_relevance_label(source["label"])
                ) or (
                    "label" in ground_truth
                    and _canonical_relevance_label(ground_truth["label"])
                    != _canonical_relevance_label(source["label"])
                ):
                    raise ValueError("Prediction ground truth must match the approved dataset label.")
                connection.execute(
                    """INSERT INTO research_predictions
                       (id, experiment_id, example_id, partition_name, prediction_json, ground_truth_json)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (_id("pred"), experiment_id, prediction["example_id"],
                     prediction["partition_name"], json.dumps(prediction["prediction"], sort_keys=True),
                     json.dumps(prediction["ground_truth"], sort_keys=True)),
                )
            _event(
                connection, institution_id, None, user_id, "research.predictions.stored",
                {"experiment_id": experiment_id, "prediction_count": len(predictions)},
            )

    def lock_threshold_from_validation_predictions(
        self, user_id: str, institution_id: str, experiment_id: str
    ) -> dict[str, Any]:
        from .research_validation import threshold_from_validation

        with self.connection() as connection:
            if not _member(connection, user_id, institution_id):
                raise PermissionError("Institution membership required.")
            experiment = connection.execute(
                """SELECT e.dataset_id, e.status, d.dataset_version, d.verification_status
                   FROM research_experiments e JOIN research_datasets d ON d.id = e.dataset_id
                   WHERE e.id = ? AND e.institution_id = ?""",
                (experiment_id, institution_id),
            ).fetchone()
            if (
                not experiment
                or experiment["status"] != "completed"
                or experiment["verification_status"] != "approved"
            ):
                raise PermissionError("A completed, institution-authorized experiment is required.")
            rows = connection.execute(
                """SELECT p.prediction_json, p.ground_truth_json
                   FROM research_predictions p
                   JOIN research_examples e ON e.dataset_id = ?
                       AND e.example_id = p.example_id
                       AND e.partition_name = p.partition_name
                   WHERE p.experiment_id = ? AND p.partition_name = 'validation'""",
                (experiment["dataset_id"], experiment_id),
            ).fetchall()
            expected_count = connection.execute(
                """SELECT COUNT(*) FROM research_examples
                   WHERE dataset_id = ? AND partition_name = 'validation'""",
                (experiment["dataset_id"],),
            ).fetchone()[0]
            if len(rows) != expected_count:
                raise ValueError("Threshold calibration requires predictions for every validation example.")
            predictions = [json.loads(row["prediction_json"]) for row in rows]
            references = [json.loads(row["ground_truth_json"]) for row in rows]
            if any("aes" not in prediction or "acceptable" not in reference for prediction, reference in zip(predictions, references)):
                raise ValueError("Validation predictions require AES values and expert acceptable labels.")
            result = threshold_from_validation(
                [prediction["aes"] for prediction in predictions],
                [reference["acceptable"] for reference in references],
                experiment["dataset_version"],
            )
            if result["status"] != "locked_from_validation":
                return result
            connection.execute(
                """INSERT INTO research_thresholds
                   (id, dataset_id, threshold, selection_metric, validation_metrics_json, locked_by)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (_id("thr"), experiment["dataset_id"], result["threshold"],
                 result["selection_metric"], json.dumps(result["metrics"], sort_keys=True), user_id),
            )
            _event(
                connection, institution_id, None, user_id, "research.threshold.locked",
                {"experiment_id": experiment_id, "dataset_version": experiment["dataset_version"],
                 "threshold_version": result["threshold_version"]},
            )
            return result


def _canonical_relevance_label(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    normalized = str(value).strip().casefold()
    if normalized in {"true", "1", "yes", "positive", "relevant"}:
        return "true"
    if normalized in {"false", "0", "no", "negative", "not_relevant"}:
        return "false"
    raise ValueError("Annotation reviews require a supported binary relevance label.")


def _is_staged_storage_key(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == len(".wuri-delete-") + 32
        and value.startswith(".wuri-delete-")
        and all(character in "0123456789abcdef" for character in value[len(".wuri-delete-"):])
    )


def _id(prefix: str) -> str:
    import uuid
    return f"{prefix}_{uuid.uuid4()}"


def _member(connection, user_id, institution_id):
    return connection.execute(
        "SELECT 1 FROM institution_memberships WHERE user_id = ? AND institution_id = ? AND status = 'active'",
        (user_id, institution_id),
    ).fetchone() is not None


def _require_research_document(document):
    if (
        document["authorization_status"] != "verified"
        or document["research_permission_status"] != "verified"
        or document["review_status"] != "verified"
        or document["malware_scan_status"] != "clean"
    ):
        raise ValueError(
            "Institutional authorization, research-use permission, and document review must be verified."
        )


def _assessment_access(connection, user_id, institution_id, assessment_id):
    return _member(connection, user_id, institution_id) and connection.execute(
        "SELECT 1 FROM assessments WHERE id = ? AND institution_id = ?",
        (assessment_id, institution_id),
    ).fetchone() is not None


def _event(connection, institution_id, assessment_id, user_id, event_type, metadata):
    connection.execute(
        "INSERT INTO audit_events (id, institution_id, assessment_id, user_id, event_type, metadata_json) VALUES (?, ?, ?, ?, ?, ?)",
        (_id("evt"), institution_id, assessment_id, user_id, event_type, json.dumps(metadata)),
    )

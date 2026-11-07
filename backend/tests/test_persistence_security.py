import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.research_validation import split_evidence_dataset
from app.security import create_session_token, hash_password, read_session_claims, read_session_token, validate_session_secret, verify_password
from app.storage import PrivateStorage
from research_fixtures import approve_synthetic_panel_dataset


class PersistenceSecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.database = Database(self.root / "test.sqlite3")

    def tearDown(self):
        self.directory.cleanup()

    def test_passwords_are_hashed_and_sessions_are_signed(self):
        password = "correct horse battery staple"
        encoded = hash_password(password)
        self.assertNotEqual(encoded, password)
        self.assertTrue(verify_password(password, encoded))
        self.assertFalse(verify_password("wrong password", encoded))
        secret = "s" * 32
        token = create_session_token("user-1", secret)
        self.assertEqual(read_session_token(token, secret), "user-1")
        self.assertIsNone(read_session_token(token, "w" * 32))
        claims = read_session_claims(token, secret)
        self.assertEqual(claims["user_id"], "user-1")
        self.assertTrue(claims["session_id"])
        with self.assertRaises(ValueError):
            validate_session_secret("short")

    def test_sessions_are_persistently_revocable_and_expire(self):
        user_id = self.database.ensure_admin(
            "session-owner", hash_password("session owner password")
        )
        session_id = "synthetic-session-id"
        self.database.create_session(session_id, user_id, 2_000)
        self.assertTrue(self.database.session_is_active(session_id, user_id, now=1_000))
        self.assertFalse(self.database.session_is_active(session_id, user_id, now=2_000))
        self.database.create_session("revoke-me", user_id, 3_000)
        self.assertTrue(self.database.revoke_session("revoke-me", now=1_500))
        self.assertFalse(self.database.session_is_active("revoke-me", user_id, now=1_501))

    def test_login_rate_limit_is_atomic_persistent_and_windowed(self):
        rate_key = "synthetic-hashed-client-key"
        for attempt in range(4):
            self.assertEqual(self.database.record_login_failure(rate_key, now=10_000 + attempt), 0)
        retry_after = self.database.record_login_failure(rate_key, now=10_004)
        self.assertGreater(retry_after, 0)
        reopened = Database(self.root / "test.sqlite3")
        self.assertGreater(reopened.login_rate_limit_status(rate_key, now=10_005), 0)
        self.assertEqual(reopened.login_rate_limit_status(rate_key, now=11_000), 0)
        reopened.clear_login_failures(rate_key)
        self.assertEqual(reopened.login_rate_limit_status(rate_key, now=10_005), 0)

    def test_records_survive_new_database_connection(self):
        user_id = self.database.ensure_admin("admin", hash_password("correct horse battery staple"))
        with self.database.connection() as connection:
            institution_id = connection.execute("SELECT institution_id FROM institution_memberships WHERE user_id = ?", (user_id,)).fetchone()["institution_id"]
        assessment_id = self.database.create_assessment(user_id, institution_id, "document_extracted")
        reopened = Database(self.root / "test.sqlite3")
        rows = reopened.assessments(user_id)
        self.assertEqual(rows[0]["id"], assessment_id)

    def test_dataset_run_requirements_rejects_another_institution_dataset(self):
        user_id = self.database.ensure_admin("dataset-owner", hash_password("dataset-owner password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (user_id,),
            ).fetchone()["institution_id"]
        records = [
            {
                "example_id": f"dataset-isolation-{index}",
                "text": f"Synthetic dataset isolation fixture {index}.",
                "framework": "WURI",
                "indicator": "isolation-fixture",
                "label": bool(index % 2),
                "annotation_version": "dataset-isolation-v1",
                "annotation_provenance": "synthetic dataset isolation fixture",
                "annotation_status": "expert_reviewed",
            }
            for index in range(3)
        ]
        split = split_evidence_dataset(records, "dataset-isolation-v1", 17)
        dataset_id = self.database.create_research_dataset(
            user_id,
            institution_id,
            {
                "dataset_version": "dataset-isolation-v1",
                "annotation_version": "dataset-isolation-v1",
                "provenance": "synthetic dataset isolation fixture",
            },
            records,
            split.as_dict(),
        )
        other_user = "other-institution-user"
        other_institution = "other-institution"
        with self.database.connection() as connection:
            connection.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                (other_user, other_user, hash_password("other institution password")),
            )
            connection.execute(
                "INSERT INTO institutions (id, name) VALUES (?, ?)",
                (other_institution, "Other synthetic institution"),
            )
            connection.execute(
                """INSERT INTO institution_memberships
                   (user_id, institution_id, role) VALUES (?, ?, 'administrator')""",
                (other_user, other_institution),
            )
        with self.assertRaisesRegex(PermissionError, "dataset access denied"):
            self.database.dataset_run_requirements(
                other_user, other_institution, dataset_id
            )

    def test_institution_registry_and_readiness_are_scoped(self):
        user_id = self.database.ensure_admin("registry-owner", hash_password("registry password"))
        institution_id = self.database.create_institution(
            user_id,
            {
                "name": "Synthetic Registry Institution",
                "region": "Test Region",
                "institution_type": "synthetic",
                "provenance": "test fixture only",
            },
        )
        institutions = self.database.institutions_for_user(user_id)
        self.assertTrue(any(row["id"] == institution_id for row in institutions))
        readiness_id = self.database.upsert_evidence_readiness(
            user_id,
            institution_id,
            {
                "framework_id": "WURI",
                "framework_edition": "2026",
                "criterion_id": "Industrial Application",
                "evidence_status": "unknown",
                "limitations": "Synthetic fixture; not research evidence.",
            },
        )
        records = self.database.evidence_readiness(
            user_id, institution_id, "WURI", "2026"
        )
        self.assertEqual(records[0]["id"], readiness_id)

        with self.database.connection() as connection:
            connection.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                ("registry-other", "registry-other", hash_password("other password")),
            )
            connection.execute(
                "INSERT INTO institutions (id, name) VALUES (?, ?)",
                ("registry-other-inst", "Other registry institution"),
            )
            connection.execute(
                """INSERT INTO institution_memberships
                   (user_id, institution_id, role) VALUES (?, ?, 'administrator')""",
                ("registry-other", "registry-other-inst"),
            )
        with self.assertRaises(PermissionError):
            self.database.evidence_readiness(
                "registry-other", institution_id, "WURI", "2026"
            )

    def test_document_provenance_mapping_and_permission_updates_are_scoped(self):
        user_id = self.database.ensure_admin("evidence-owner", hash_password("evidence password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (user_id,),
            ).fetchone()["institution_id"]
        assessment_id = self.database.create_assessment(user_id, institution_id, "document_extracted")
        self.database.persist_document(
            user_id,
            institution_id,
            assessment_id,
            {
                "document_id": "evidence-doc-1",
                "filename": "authorized.txt",
                "file_type": "txt",
                "file_size": 12,
                "checksum": "a" * 64,
                "storage_key": "evidence-key-1",
                "extraction_status": "success",
                "source_reference": "institutional archive",
                "provenance": "synthetic fixture only",
                "mapping": {
                    "framework_id": "WURI",
                    "framework_edition": "2026",
                    "criterion_id": "Industrial Application",
                },
            },
            [],
            [],
        )
        detail = self.database.assessment_detail(user_id, assessment_id)
        self.assertEqual(detail["mappings"][0]["criterion_id"], "Industrial Application")
        self.database.update_document_metadata(
            user_id,
            "evidence-doc-1",
            {
                "authorization_status": "verified",
                "research_permission_status": "pending",
                "review_status": "verified",
            },
        )
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT authorization_status, research_permission_status, review_status FROM documents WHERE id = ?",
                ("evidence-doc-1",),
            ).fetchone()
        self.assertEqual(tuple(row), ("verified", "pending", "verified"))

    def test_private_storage_rejects_path_traversal(self):
        storage = PrivateStorage(self.root / "private")
        key, checksum = storage.save(b"fixture", ".txt")
        self.assertEqual(len(checksum), 64)
        storage.delete(key)
        with self.assertRaises(ValueError):
            storage.delete("../outside.txt")

    def test_source_passage_documents_are_derived_before_dataset_splitting(self):
        user_id = self.database.ensure_admin("source-check", hash_password("source-check password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?", (user_id,)
            ).fetchone()["institution_id"]
        assessment_id = self.database.create_assessment(user_id, institution_id, "document_extracted")
        records = []
        with self.database.connection() as connection:
            for doc_index in range(3):
                document_id = f"source-doc-{doc_index}"
                connection.execute(
                    """INSERT INTO documents
                       (id, institution_id, assessment_id, filename, file_type, file_size,
                        checksum, storage_key, extraction_status, authorization_status,
                        research_permission_status, review_status, malware_scan_status)
                       VALUES (?, ?, ?, ?, 'text/plain', 1, ?, ?, 'completed',
                               'verified', 'verified', 'verified', 'clean')""",
                    (document_id, institution_id, assessment_id, f"source-{doc_index}.txt",
                     f"checksum-{doc_index}", f"private/{doc_index}"),
                )
                for passage_index in range(2):
                    passage_id = f"source-passage-{doc_index}-{passage_index}"
                    connection.execute(
                        """INSERT INTO evidence_passages
                           (id, document_id, assessment_id, institution_id, passage_index,
                            text, extraction_method)
                           VALUES (?, ?, ?, ?, ?, ?, 'fixture')""",
                        (passage_id, document_id, assessment_id, institution_id, passage_index,
                         f"Unique source passage text {doc_index}-{passage_index}."),
                    )
                    records.append({
                        "example_id": passage_id,
                        "source_passage_id": passage_id,
                        "framework": "WURI",
                        "indicator": f"indicator-{doc_index}-{passage_index}",
                        "label": bool(passage_index),
                        "annotation_version": "passage-fixture-v1",
                        "annotation_provenance": "synthetic source passage fixture",
                        "annotation_status": "expert_reviewed",
                    })

        prepared = self.database.prepare_research_records(user_id, institution_id, records)
        self.assertEqual(
            [record["text"] for record in prepared],
            [
                f"Unique source passage text {doc_index}-{passage_index}."
                for doc_index in range(3)
                for passage_index in range(2)
            ],
        )
        split = split_evidence_dataset(prepared, "source-doc-fixture-v1", 31)
        dataset_id = self.database.create_research_dataset(
            user_id,
            institution_id,
            {
                "dataset_version": "source-doc-fixture-v1",
                "annotation_version": "passage-fixture-v1",
                "provenance": "synthetic source passage fixture",
            },
            prepared,
            split.as_dict(),
        )
        bundle = self.database.research_dataset_bundle(user_id, institution_id, dataset_id)
        self.assertEqual(
            {record["example_id"]: record["text"] for record in bundle["records"]},
            {record["example_id"]: record["text"] for record in prepared},
        )
        for doc_index in range(3):
            pair = [
                split.assignments[f"source-passage-{doc_index}-{passage_index}"]
                for passage_index in range(2)
            ]
            self.assertEqual(pair[0], pair[1])

    def test_dataset_creation_requires_verified_registered_source_documents(self):
        user_id = self.database.ensure_admin("evidence-state-check", hash_password("evidence state password"))
        other_user_id = self.database.ensure_admin("other-evidence-state-check", hash_password("other evidence password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?", (user_id,)
            ).fetchone()["institution_id"]
            other_institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?", (other_user_id,)
            ).fetchone()["institution_id"]
        assessment_id = self.database.create_assessment(user_id, institution_id, "document_extracted")
        record_template = {
            "example_id": "document-state-example",
            "text": "Traceable document state fixture.",
            "framework": "WURI",
            "indicator": "state-check",
            "label": True,
            "annotation_version": "state-check-v1",
            "annotation_provenance": "synthetic security fixture",
            "annotation_status": "submitted",
        }
        split = {
            "dataset_version": "state-check-v1",
            "seed": 7,
            "split_version": "synthetic-state-check-v1",
            "proportions": {"train": 1.0, "validation": 0.0, "test": 0.0},
            "assignments": {"document-state-example": "train"},
            "counts": {"train": 1, "validation": 0, "test": 0},
            "group_counts": {"train": 1, "validation": 0, "test": 0},
            "warnings": ["Synthetic security fixture; not a research split."],
        }
        for index, field in enumerate(
            ("authorization_status", "research_permission_status", "review_status")
        ):
            invalid_values = {
                "authorization_status": ("unknown", "pending", "unavailable"),
                "research_permission_status": ("unknown", "pending", "unavailable"),
                "review_status": ("uploaded", "processing_failed", "pending_review", "rejected"),
            }[field]
            for value in invalid_values:
                document_id = f"invalid-state-{index}-{value}"
                with self.database.connection() as connection:
                    connection.execute(
                        """INSERT INTO documents
                           (id, institution_id, assessment_id, filename, file_type, file_size,
                            checksum, storage_key, extraction_status, authorization_status,
                            research_permission_status, review_status, malware_scan_status)
                           VALUES (?, ?, ?, ?, 'text/plain', 1, ?, ?, 'completed',
                                   'verified', 'verified', 'verified', 'clean')""",
                        (document_id, institution_id, assessment_id, f"{document_id}.txt",
                         f"checksum-{document_id}", f"private/{document_id}"),
                    )
                    connection.execute(
                        f"UPDATE documents SET {field} = ? WHERE id = ?",
                        (value, document_id),
                    )
                record = {**record_template, "source_document_id": document_id}
                with self.assertRaisesRegex(ValueError, "verified"):
                    self.database.create_research_dataset(
                        user_id, institution_id,
                        {"dataset_version": document_id, "annotation_version": "state-check-v1",
                         "provenance": "synthetic security fixture"},
                        [record], split,
                    )

        valid_id = "fully-verified-document"
        with self.database.connection() as connection:
            connection.execute(
                """INSERT INTO documents
                   (id, institution_id, assessment_id, filename, file_type, file_size,
                    checksum, storage_key, extraction_status, authorization_status,
                    research_permission_status, review_status, malware_scan_status)
                   VALUES (?, ?, ?, ?, 'text/plain', 1, ?, ?, 'success',
                           'verified', 'verified', 'verified', 'clean')""",
                (valid_id, institution_id, assessment_id, "valid.txt", "valid-checksum", "private/valid"),
            )
        valid_record = {**record_template, "source_document_id": valid_id}
        valid_dataset_id = self.database.create_research_dataset(
            user_id, institution_id,
            {"dataset_version": "valid-state-check", "annotation_version": "state-check-v1",
             "provenance": "synthetic security fixture"},
            [valid_record], split,
        )
        self.assertIsNotNone(valid_dataset_id)
        review_user_id = self.database.ensure_admin(
            "document-state-reviewer", hash_password("document state reviewer password")
        )
        with self.database.connection() as connection:
            connection.execute(
                """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (review_user_id, institution_id),
            )
            connection.execute(
                "UPDATE documents SET research_permission_status = 'pending' WHERE id = ?",
                (valid_id,),
            )
        with self.assertRaisesRegex(ValueError, "authorized"):
            self.database.review_research_dataset(
                review_user_id, institution_id, valid_dataset_id, "approved",
                "Permission downgrade must block approval.",
                source_use_clearance_reference="test-only clearance",
                institutional_approval_reference="test-only approval",
            )

        other_assessment_id = self.database.create_assessment(
            other_user_id, other_institution_id, "document_extracted"
        )
        with self.database.connection() as connection:
            connection.execute(
                """INSERT INTO documents
                   (id, institution_id, assessment_id, filename, file_type, file_size,
                    checksum, storage_key, extraction_status, authorization_status,
                    research_permission_status, review_status, malware_scan_status)
                   VALUES ('cross-institution-document', ?, ?, 'other.txt', 'text/plain', 1,
                           'other-checksum', 'private/other', 'completed',
                           'verified', 'verified', 'verified', 'clean')""",
                (other_institution_id, other_assessment_id),
            )
        with self.assertRaises(PermissionError):
            self.database.create_research_dataset(
                user_id, institution_id,
                {"dataset_version": "cross-institution-check", "annotation_version": "state-check-v1",
                 "provenance": "synthetic security fixture"},
                [{**record_template, "source_document_id": "cross-institution-document"}],
                split,
            )

    def test_annotation_migration_can_be_retried_with_referencing_rows(self):
        user_id = self.database.ensure_admin("migration-check", hash_password("migration password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (user_id,),
            ).fetchone()["institution_id"]
        records = [
            {
                "example_id": f"migration-example-{index}",
                "text": f"Synthetic migration fixture record {index}.",
                "framework": "WURI",
                "indicator": "migration-fixture",
                "label": bool(index % 2),
                "annotation_version": "migration-fixture-v1",
                "annotation_provenance": "synthetic migration fixture only",
                "annotation_status": "submitted",
            }
            for index in range(3)
        ]
        split = split_evidence_dataset(records, "migration-fixture-v1", 9).as_dict()
        dataset_id = self.database.create_research_dataset(
            user_id,
            institution_id,
            {
                "dataset_version": "migration-fixture-v1",
                "annotation_version": "migration-fixture-v1",
                "provenance": "synthetic migration fixture only",
            },
            records,
            split,
        )
        with self.database.connection() as connection:
            connection.execute(
                """INSERT INTO research_annotation_reviews
                   (id, dataset_id, example_id, reviewer_id, review_stage, label, note)
                   VALUES ('migration-review', ?, 'migration-example-0', ?, 'independent', 'true', 'fixture')""",
                (dataset_id, user_id),
            )
            connection.execute(
                """INSERT INTO research_annotation_consensus
                   (dataset_id, example_id, final_label, resolution)
                   VALUES (?, 'migration-example-0', 'true', 'agreement')""",
                (dataset_id,),
            )
            connection.execute(
                "DELETE FROM schema_migrations WHERE migration_name = '004_research_import_and_annotations.sql'"
            )

        reopened = Database(self.root / "test.sqlite3")
        with reopened.connection() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM research_annotation_reviews WHERE dataset_id = ?",
                    (dataset_id,),
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM research_annotation_consensus WHERE dataset_id = ?",
                    (dataset_id,),
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM research_examples WHERE dataset_id = ?",
                    (dataset_id,),
                ).fetchone()[0],
                3,
            )
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_research_dataset_is_versioned_and_requires_independent_review(self):
        submitter_id = self.database.ensure_admin("submitter", hash_password("submitter password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (submitter_id,),
            ).fetchone()["institution_id"]
        records = [
            {
                "example_id": f"fixture-{index}",
                "text": f"Controlled research software fixture content {index} with unique topic token{index}.",
                "framework": "WURI" if index % 2 else "THE",
                "indicator": f"indicator-{index % 3}",
                "major_indicator_group": f"group-{index % 2}",
                "label": bool(index % 2),
                "source_document_id": None,
                "source_passage_id": None,
                "annotation_version": "fixture-annotation-v1",
                "annotation_provenance": "synthetic unit-test fixture; not research evidence",
                "annotation_status": "expert_reviewed",
            }
            for index in range(30)
        ]
        split = split_evidence_dataset(records, "fixture-dataset-v1", 33).as_dict()
        dataset_id = self.database.create_research_dataset(
            submitter_id,
            institution_id,
            {
                "dataset_version": "fixture-dataset-v1",
                "annotation_version": "fixture-annotation-v1",
                "provenance": "synthetic software test only",
            },
            records,
            split,
        )
        self.assertEqual(self.database.research_counts(submitter_id, institution_id)["expert_labeled_examples"], 0)
        with self.assertRaisesRegex(PermissionError, "someone other than"):
            self.database.review_research_dataset(
                submitter_id, institution_id, dataset_id, "approved", "Independent dataset review."
            )

        reviewer_id = self.database.ensure_admin("reviewer", hash_password("reviewer password"))
        second_reviewer_id = self.database.ensure_admin(
            "second-reviewer", hash_password("second reviewer password")
        )
        with self.database.connection() as connection:
            connection.execute(
                """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (reviewer_id, institution_id),
            )
            connection.execute(
                """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (second_reviewer_id, institution_id),
            )
        with self.assertRaises(PermissionError):
            self.database.research_datasets(reviewer_id, "not-an-institution")
        reviews = [
            {
                "example_id": record["example_id"], "label": record["label"],
                "decision": "confirm", "note": "Synthetic annotation review fixture.",
            }
            for record in records
        ]
        self.database.submit_annotation_reviews(reviewer_id, institution_id, dataset_id, reviews)
        self.database.submit_annotation_reviews(second_reviewer_id, institution_id, dataset_id, reviews)
        with self.assertRaisesRegex(ValueError, "no verifiable source-document provenance"):
            self.database.review_research_dataset(
                reviewer_id, institution_id, dataset_id, "approved",
                "Missing source provenance must block approval.",
                source_use_clearance_reference="test-only source clearance",
                institutional_approval_reference="test-only institutional approval",
            )
        approve_synthetic_panel_dataset(
            self.database, institution_id, dataset_id, submitter_id, records,
            "persistence-panel",
        )
        with self.assertRaisesRegex(ValueError, "approved research dataset"):
            self.database.update_document_metadata(
                submitter_id,
                "persistence-panel-source-fixture-0",
                {"research_permission_status": "pending"},
            )
        with self.assertRaisesRegex(ValueError, "approved research dataset"):
            self.database.delete_document(
                submitter_id, "persistence-panel-source-fixture-0"
            )
        self.assertEqual(
            self.database.research_counts(submitter_id, institution_id)["expert_labeled_examples"],
            len(records),
        )
        dimensions = (
            "semantic_relevance", "model_confidence", "evidence_completeness",
            "source_reliability", "evidence_strength",
        )
        ratings = [
            {
                "case_id": records[0]["example_id"],
                "expert_reference": expert,
                "dimension": dimension,
                "score": 0.75,
                "rating_scale": {"minimum": 0.0, "maximum": 1.0},
                "provenance": "independent synthetic fixture rating",
                "annotation_version": "fixture-rating-v1",
                "status": "independent",
            }
            for expert in ("expert-a", "expert-b")
            for dimension in dimensions
        ]
        rating_ids = self.database.persist_expert_ratings(
            submitter_id, institution_id, dataset_id, ratings
        )
        self.assertEqual(self.database.research_counts(submitter_id, institution_id)["expert_ratings"], 0)
        for rating_id in rating_ids:
            self.database.review_expert_rating(
                reviewer_id, institution_id, rating_id, "approved", "Fixture-only independent review."
            )
        rating_counts = self.database.research_counts(submitter_id, institution_id)
        self.assertEqual(rating_counts["expert_eqam_dimensions"], 5)
        self.assertEqual(rating_counts["expert_eqam_min_raters_per_dimension"], 2)

    def test_research_threshold_is_selected_from_validation_partition_only(self):
        submitter_id = self.database.ensure_admin("researcher", hash_password("researcher password"))
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (submitter_id,),
            ).fetchone()["institution_id"]
        records = [
            {
                "example_id": f"threshold-{index}",
                "text": f"Unique validation fixture text with subject token{index} item{index * 3}.",
                "framework": "WURI" if index % 2 else "THE",
                "indicator": f"indicator-{index % 4}",
                "major_indicator_group": f"group-{index % 2}",
                "label": bool(index % 2),
                "annotation_version": "fixture-v1",
                "annotation_provenance": "synthetic test fixture only",
                "annotation_status": "expert_reviewed",
            }
            for index in range(60)
        ]
        split = split_evidence_dataset(records, "threshold-fixture-v1", 42).as_dict()
        dataset_id = self.database.create_research_dataset(
            submitter_id,
            institution_id,
            {
                "dataset_version": "threshold-fixture-v1",
                "annotation_version": "fixture-v1",
                "provenance": "synthetic software test only",
            },
            records,
            split,
        )
        with self.database.connection() as connection:
            reviewer_id = self.database.ensure_admin(
                "independent-reviewer", hash_password("independent reviewer password")
            )
            # Membership writes are kept in one database transaction below.
            connection.execute(
                """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (reviewer_id, institution_id),
            )
        second_reviewer_id = self.database.ensure_admin(
            "independent-second-reviewer", hash_password("second reviewer password long")
        )
        with self.database.connection() as connection:
            connection.execute(
                """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (second_reviewer_id, institution_id),
            )
        reviews = [
            {
                "example_id": record["example_id"], "label": record["label"],
                "decision": "confirm", "note": "Synthetic threshold annotation review.",
            }
            for record in records
        ]
        self.database.submit_annotation_reviews(reviewer_id, institution_id, dataset_id, reviews)
        self.database.submit_annotation_reviews(second_reviewer_id, institution_id, dataset_id, reviews)
        approve_synthetic_panel_dataset(
            self.database, institution_id, dataset_id, submitter_id, records,
            "threshold-panel",
        )
        run_id = self.database.persist_research_experiment(
            submitter_id,
            institution_id,
            {
                "dataset_id": dataset_id,
                "experiment_type": "unit_test",
                "configuration_id": "fixture-threshold",
                "configuration": {"synthetic_fixture": True},
                "model_version": "test-only",
                "method_version": "test-only",
                "random_seed": 42,
                "status": "completed",
                "results": {"fixture_only": True},
            },
        )
        predictions = []
        for record in records:
            partition = split["assignments"][record["example_id"]]
            predictions.append({
                "example_id": record["example_id"],
                "partition_name": partition,
                "prediction": {"aes": 0.5 if partition == "test" else (0.9 if record["label"] else 0.1)},
                "ground_truth": {"acceptable": bool(record["label"])},
            })
        invalid_label = dict(predictions[0])
        invalid_label["ground_truth"] = {
            "acceptable": not invalid_label["ground_truth"]["acceptable"]
        }
        with self.assertRaisesRegex(ValueError, "must match the approved dataset label"):
            self.database.persist_research_predictions(
                submitter_id, institution_id, run_id, [invalid_label]
            )
        self.database.persist_research_predictions(submitter_id, institution_id, run_id, predictions)
        result = self.database.lock_threshold_from_validation_predictions(
            submitter_id, institution_id, run_id
        )
        self.assertEqual(result["status"], "locked_from_validation")
        self.assertEqual(result["threshold"], 0.9)
        self.assertFalse(result["test_labels_used"])
        self.assertEqual(self.database.research_counts(submitter_id, institution_id)["locked_thresholds"], 1)


if __name__ == "__main__":
    unittest.main()

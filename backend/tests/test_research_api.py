import os
import csv
import io
import json
import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.database import Database
from app.indicators import FRAMEWORK_INDICATORS
from app.research_import import parse_research_upload, validate_research_records
from app.research_validation import split_evidence_dataset
from app.storage import PrivateStorage


class ResearchApiTests(unittest.TestCase):
    def test_api_routes_do_not_call_raw_institutional_scoring_helpers(self):
        source_path = Path(main.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        raw_helpers = {
            "calculate_aes", "calculate_ahp", "fixed_reference_topsis",
            "calculate_arrs", "select_best_fit",
        }
        route_functions = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            is_route = any(
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "app"
                for decorator in node.decorator_list
            )
            if is_route:
                route_functions.append(node)
        self.assertTrue(route_functions)
        for route in route_functions:
            referenced = {
                node.id for node in ast.walk(route) if isinstance(node, ast.Name)
            } | {
                node.attr for node in ast.walk(route) if isinstance(node, ast.Attribute)
            }
            self.assertFalse(
                raw_helpers & referenced,
                f"Route {route.name} calls raw scoring helpers directly.",
            )

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.directory.name) / "api.sqlite3")
        self.environment = patch.dict(os.environ, {
            "WURI_ADMIN_USERNAME": "research-admin",
            "WURI_ADMIN_PASSWORD": "local-test-password-long",
            "WURI_SESSION_SECRET": "research-test-session-secret",
            "WURI_SBERT_MODEL_PATH": "",
            "WURI_ENVIRONMENT": "development",
            "SESSION_COOKIE_SECURE": "false",
        })
        self.environment.start()
        self.database_patch = patch.object(main, "database", self.database)
        self.database_patch.start()
        self.storage = PrivateStorage(Path(self.directory.name) / "private")
        self.storage_patch = patch.object(main, "storage", self.storage)
        self.storage_patch.start()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.database_patch.stop()
        self.storage_patch.stop()
        self.environment.stop()
        self.directory.cleanup()

    def login(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "research-admin", "password": "local-test-password-long"},
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_session_status_restores_authenticated_user_without_exposing_password(self):
        self.login()
        response = self.client.get("/api/auth/session")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["user"]["username"], "research-admin")
        self.assertNotIn("password_hash", response.json()["user"])

    def test_session_status_rejects_missing_or_expired_session(self):
        self.assertEqual(self.client.get("/api/auth/session").status_code, 401)
        self.client.cookies.set(
            main.SESSION_COOKIE,
            main.create_session_token(
                "missing-user", os.environ["WURI_SESSION_SECRET"]
            ),
        )
        self.assertEqual(self.client.get("/api/auth/session").status_code, 401)

    def test_logout_clears_session_cookie_and_requires_login(self):
        self.login()
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(self.client.get("/api/auth/session").status_code, 401)

    def test_session_cookie_is_secure_by_default_and_local_override_is_explicit(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(main.session_cookie_secure())
        with patch.dict(
            os.environ,
            {"WURI_ENVIRONMENT": "development", "SESSION_COOKIE_SECURE": "false"},
            clear=True,
        ):
            self.assertFalse(main.session_cookie_secure())
        with patch.dict(os.environ, {"SESSION_COOKIE_SECURE": "false"}, clear=True):
            with self.assertRaises(main.HTTPException):
                main.session_cookie_secure()

    def test_upload_requires_clean_scan_before_extraction(self):
        self.login()
        user_id = self.database.user_by_username("research-admin")["id"]
        institution_id = self.database.institutions_for_user(user_id)[0]["id"]

        class Scanner:
            def __init__(self, status):
                self.status = status

            def scan(self, path):
                return type("Result", (), {"status": self.status, "scanner": "synthetic-test"})()

        with patch.object(main, "malware_scanner", Scanner("unavailable")):
            blocked = self.client.post(
                "/api/upload",
                params={"institution_id": institution_id},
                files={"file": ("evidence.txt", b"synthetic evidence", "text/plain")},
            )
        self.assertEqual(blocked.status_code, 503)
        self.assertEqual(list(self.storage.root.iterdir()), [])

        with patch.object(main, "malware_scanner", Scanner("clean")):
            uploaded = self.client.post(
                "/api/upload",
                params={"institution_id": institution_id},
                files={"file": ("evidence.txt", b"synthetic evidence", "text/plain")},
            )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        upload_result = uploaded.json()
        document_id = upload_result["document"]["document_id"]
        self.assertEqual(upload_result["readiness_assessment_status"], "not_implemented")
        self.assertEqual(upload_result["matches"], [])
        self.assertTrue(any("no valid local model artifact" in warning for warning in upload_result["warnings"]))
        self.assertEqual(
            upload_result["assessment_status"]["state"],
            "institution_authorization_required",
        )
        self.assertFalse(upload_result["assessment_status"]["final_scoring_allowed"])
        self.assertFalse({"rrs", "arrs", "best_fit", "readiness_score"} & upload_result.keys())
        with self.database.connection() as connection:
            row = connection.execute(
                """SELECT malware_scan_status, malware_scanner, malware_scanned_at, provenance
                   FROM documents WHERE id = ?""",
                (document_id,),
            ).fetchone()
        self.assertEqual(row["malware_scan_status"], "clean")
        self.assertEqual(row["malware_scanner"], "synthetic-test")
        self.assertTrue(row["malware_scanned_at"])
        self.assertIsNone(row["provenance"])

    def test_synthetic_end_to_end_intake_isolation_and_cleanup(self):
        self.login()
        owner_id = self.database.user_by_username("research-admin")["id"]
        institution_id = self.database.institutions_for_user(owner_id)[0]["id"]
        criterion_id = next(iter(main.FRAMEWORK_DEFINITIONS["WURI"].criteria))

        class Scanner:
            def __init__(self, status):
                self.status = status

            def scan(self, path):
                return type("Result", (), {"status": self.status, "scanner": "synthetic-acceptance"})()

        for rejected_status in ("unavailable", "error", "infected"):
            with patch.object(main, "malware_scanner", Scanner(rejected_status)):
                response = self.client.post(
                    "/api/upload",
                    params={"institution_id": institution_id},
                    files={"file": ("rejected.txt", b"synthetic rejected content", "text/plain")},
                )
            self.assertIn(response.status_code, (422, 503))
            self.assertEqual(list(self.storage.root.iterdir()), [])

        with patch.object(main, "malware_scanner", Scanner("clean")):
            response = self.client.post(
                "/api/upload",
                params={
                    "institution_id": institution_id,
                    "framework_id": "WURI",
                    "framework_edition": "2026",
                    "criterion_id": criterion_id,
                    "title": "Synthetic acceptance evidence",
                },
                files={"file": ('acceptance"bad.txt', b"Synthetic acceptance evidence.", "text/plain")},
            )
        self.assertEqual(response.status_code, 200, response.text)
        document_id = response.json()["document"]["document_id"]
        assessment_id = response.json()["assessment_id"]
        self.assertEqual(response.json()["passages"][0]["text"], "Synthetic acceptance evidence.")

        with self.database.connection() as connection:
            document = connection.execute(
                """SELECT malware_scan_status, review_status, authorization_status,
                          research_permission_status
                   FROM documents WHERE id = ?""",
                (document_id,),
            ).fetchone()
        self.assertEqual(tuple(document), ("clean", "pending_review", "unknown", "unknown"))

        other_id = self.database.ensure_admin(
            "synthetic-other-user", main.hash_password("synthetic other password")
        )
        with self.database.connection() as connection:
            other_institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (other_id,),
            ).fetchone()["institution_id"]
        self._act_as(other_id)
        self.assertEqual(
            self.client.get(f"/api/institutions/{institution_id}/documents").status_code,
            403,
        )
        self.assertEqual(
            self.client.get(f"/api/documents/{document_id}/download").status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/documents/{document_id}",
                json={"title": "cross-institution mutation"},
            ).status_code,
            403,
        )
        self._act_as(owner_id)

        updated = self.client.patch(
            f"/api/documents/{document_id}",
            json={
                "authorization_status": "verified",
                "research_permission_status": "verified",
                "review_status": "verified",
            },
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        downloaded = self.client.get(f"/api/documents/{document_id}/download")
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(
            downloaded.headers["content-disposition"],
            "attachment; filename*=UTF-8''acceptance%22bad.txt",
        )
        deleted = self.client.delete(f"/api/documents/{document_id}")
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(self.client.get(f"/api/assessments/{assessment_id}").status_code, 200)
        self.assertFalse(list(self.storage.root.iterdir()))
        with self.database.connection() as connection:
            self.assertIsNone(
                connection.execute("SELECT 1 FROM documents WHERE id = ?", (document_id,)).fetchone()
            )

    def _act_as(self, user_id):
        token = main.create_session_token(
            user_id, os.environ["WURI_SESSION_SECRET"]
        )
        self.client.cookies.set(main.SESSION_COOKIE, token)

    def test_csv_parser_rejects_malformed_rows_and_integer_labels_are_normalized(self):
        records, errors = parse_research_upload(
            "malformed.csv", b"example_id,text\nvalid,record\n\"unterminated"
        )
        self.assertEqual(records, [])
        self.assertEqual(errors[-1], {"line": 3, "message": "Malformed CSV."})

        indicator = next(iter(FRAMEWORK_INDICATORS["WURI"]))
        source_record = {
            "example_id": "integer-label",
            "framework": "WURI",
            "indicator": indicator,
            "label": 1,
            "source_document_id": "source-1",
            "institution_group_id": "institution-1",
            "text": "Synthetic evidence record.",
        }
        prepared, validation_errors = validate_research_records(
            [source_record],
            dataset_version="integer-label-fixture-v1",
            annotation_version="fixture-v1",
            provenance="synthetic unit test only",
        )
        self.assertEqual(validation_errors, [])
        self.assertEqual(prepared[0]["label"], "1")

        source_record["label"] = True
        prepared, validation_errors = validate_research_records(
            [source_record],
            dataset_version="boolean-label-fixture-v1",
            annotation_version="fixture-v1",
            provenance="synthetic unit test only",
        )
        self.assertEqual(validation_errors, [])
        self.assertIs(prepared[0]["label"], True)

    def test_status_is_protected_and_reports_missing_empirical_data(self):
        self.assertEqual(self.client.get("/api/research/validation/status").status_code, 401)
        self.login()
        response = self.client.get("/api/research/validation/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["empirical_results_available"])
        self.assertEqual(data["dataset_counts"]["expert_labeled_examples"], 0)
        self.assertTrue(all(
            item["status"] == "blocked_missing_data" for item in data["ablations"]
        ))

    def test_dataset_import_persists_a_split_but_requires_second_person_review(self):
        self.login()
        records = [
            {
                "example_id": f"api-fixture-{index}",
                "text": f"API synthetic test fixture unique content indicator token{index}.",
                "framework": "WURI" if index % 2 else "THE",
                "indicator": tuple(FRAMEWORK_INDICATORS[
                    "WURI" if index % 2 else "THE"
                ])[index % 4],
                "major_indicator_group": f"group-{index % 2}",
                "label": bool(index % 2),
                "annotation_provenance": "synthetic API test fixture only",
                "annotation_status": "expert_reviewed",
            }
            for index in range(30)
        ]
        response = self.client.post(
            "/api/research/datasets",
            json={
                "dataset_version": "synthetic-api-fixture-v1",
                "annotation_version": "synthetic-test-v1",
                "provenance": "synthetic API test fixture; not research data",
                "random_seed": 9,
                "records": records,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        dataset_id = response.json()["dataset_id"]
        self.assertEqual(set(response.json()["split"]["counts"]), {"train", "validation", "test"})
        status = self.client.get("/api/research/validation/status").json()
        self.assertEqual(status["dataset_counts"]["expert_labeled_examples"], 0)
        self.assertEqual(status["datasets"][0]["verification_status"], "submitted")
        review = self.client.post(
            f"/api/research/datasets/{dataset_id}/review",
            json={"decision": "approved", "note": "Self-review must not be allowed."},
        )
        self.assertEqual(review.status_code, 403)
        run = self.client.post(
            "/api/research/experiments",
            json={
                "dataset_id": dataset_id,
                "configuration_id": "A0",
                "random_seed": 9,
            },
        )
        self.assertEqual(run.status_code, 201, run.text)
        self.assertEqual(run.json()["preflight"]["state"], "blocked_missing_data")
        self.assertIsNone(run.json()["results"])
        stored = self.database.get_research_experiment(
            self.database.user_by_username("research-admin")["id"],
            self.database.memberships(self.database.user_by_username("research-admin")["id"])[0]["institution_id"],
            run.json()["experiment_id"],
        )
        self.assertIsNone(stored["result_json"])

    def test_experiment_preflight_hides_datasets_from_other_institutions(self):
        self.login()
        other_user = self.database.ensure_admin(
            "dataset-owner", main.hash_password("dataset owner password long")
        )
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (other_user,),
            ).fetchone()["institution_id"]
        response = self.client.get(
            "/api/research/experiments/preflight",
            params={"institution_id": institution_id, "dataset_id": "not-visible", "configuration_id": "A0"},
        )
        self.assertEqual(response.status_code, 403)

    def test_research_status_rejects_an_unrelated_institution(self):
        self.login()
        other_user = self.database.ensure_admin(
            "unrelated", main.hash_password("unrelated password long")
        )
        with self.database.connection() as connection:
            other_institution = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (other_user,),
            ).fetchone()["institution_id"]
        response = self.client.get(
            "/api/research/validation/status",
            params={"institution_id": other_institution},
        )
        self.assertEqual(response.status_code, 403)

    def test_csv_import_report_and_annotation_adjudication(self):
        self.login()
        stream = io.StringIO(newline="")
        fields = [
            "example_id", "framework", "indicator", "label", "source_document_id",
            "institution_group_id", "text", "model_prediction",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        indicator = next(iter(FRAMEWORK_INDICATORS["WURI"]))
        for index in range(30):
            writer.writerow({
                "example_id": f"csv-example-{index}",
                "framework": "WURI",
                "indicator": indicator,
                "label": "relevant" if index % 2 else "not_relevant",
                "source_document_id": f"source-document-{index}",
                "institution_group_id": "source-institution-fixture",
                "text": f"Independent source {index} describes distinct university research evidence token{index}.",
                "model_prediction": json.dumps({"score": index / 30}),
            })
        source_bytes = stream.getvalue().encode("utf-8")
        response = self.client.post(
            "/api/research/datasets/import",
            files={"file": ("dataset.csv", source_bytes, "text/csv")},
            data={
                "dataset_version": "csv-review-fixture-v1",
                "annotation_version": "human-label-v1",
                "provenance": "Synthetic API workflow fixture, not research evidence.",
                "random_seed": "71",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        imported = response.json()
        report_response = self.client.get(f"/api/research/imports/{imported['import_id']}")
        self.assertEqual(report_response.status_code, 200)
        self.assertEqual(report_response.json()["report"]["sha256"], imported["report"]["sha256"])
        with self.database.connection() as connection:
            storage_key = connection.execute(
                "SELECT storage_key FROM research_dataset_imports WHERE id = ?",
                (imported["import_id"],),
            ).fetchone()["storage_key"]
        self.assertEqual(self.storage.read(storage_key), source_bytes)

        invalid = self.client.post(
            "/api/research/datasets/import",
            files={
                "file": (
                    "invalid.jsonl",
                    b'{"example_id":"bad","framework":"UNKNOWN"}\n',
                    "application/x-ndjson",
                )
            },
            data={
                "dataset_version": "invalid-import-v1",
                "annotation_version": "human-label-v1",
                "provenance": "Synthetic API workflow fixture.",
                "random_seed": "1",
            },
        )
        self.assertEqual(invalid.status_code, 422)
        detail = invalid.json()["detail"]
        self.assertEqual(detail["report"]["errors"][0]["line"], 1)
        self.assertEqual(detail["status"], "rejected")
        self.assertEqual(
            self.client.get(f"/api/research/imports/{detail['import_id']}").json()["status"],
            "rejected",
        )

        submitter_id = self.database.user_by_username("research-admin")["id"]
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (submitter_id,),
            ).fetchone()["institution_id"]
        reviewers = [
            self.database.ensure_admin(f"annotation-reviewer-{index}", f"reviewer-password-{index}")
            for index in range(3)
        ]
        with self.database.connection() as connection:
            for reviewer_id in reviewers:
                connection.execute(
                    """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                       VALUES (?, ?, 'administrator', 'active')""",
                    (reviewer_id, institution_id),
                )

        first_reviews = []
        second_reviews = []
        for index in range(30):
            relevant = bool(index % 2)
            first_reviews.append({
                "example_id": f"csv-example-{index}", "label": relevant,
                "decision": "confirm", "note": "Independent review of source evidence.",
            })
            second_review = dict(first_reviews[-1])
            if index == 0:
                second_review.update({"label": not relevant, "decision": "correct"})
            second_reviews.append(second_review)

        def act_as(reviewer_id):
            token = main.create_session_token(
                reviewer_id, os.environ["WURI_SESSION_SECRET"]
            )
            self.client.cookies.set(main.SESSION_COOKIE, token)

        act_as(reviewers[0])
        first_response = self.client.post(
            f"/api/research/datasets/{imported['dataset_id']}/annotation-reviews",
            json={"reviews": first_reviews},
            params={"institution_id": institution_id},
        )
        self.assertEqual(first_response.status_code, 201, first_response.text)
        act_as(reviewers[1])
        second_response = self.client.post(
            f"/api/research/datasets/{imported['dataset_id']}/annotation-reviews",
            json={"reviews": second_reviews},
            params={"institution_id": institution_id},
        )
        self.assertEqual(second_response.status_code, 201, second_response.text)
        act_as(reviewers[2])
        adjudication = self.client.post(
            f"/api/research/datasets/{imported['dataset_id']}/annotation-reviews",
            json={"reviews": [{
                "example_id": "csv-example-0", "label": False,
                "decision": "adjudicate",
                "note": "Third-party resolution of independent disagreement.",
            }]},
            params={"institution_id": institution_id},
        )
        self.assertEqual(adjudication.status_code, 201, adjudication.text)
        act_as(reviewers[0])
        approval = self.client.post(
            f"/api/research/datasets/{imported['dataset_id']}/review",
            json={"decision": "approved", "note": "Every example has independent review."},
            params={"institution_id": institution_id},
        )
        self.assertEqual(approval.status_code, 409, approval.text)
        self.assertIn("clearance and institutional approval references", approval.text)
        # The legacy two-review route cannot authorize research approval.
        bundle = self.database.research_dataset_bundle(
            reviewers[0], institution_id, imported["dataset_id"]
        )
        disputed = next(row for row in bundle["records"] if row["example_id"] == "csv-example-0")
        self.assertEqual(disputed["label"], "not_relevant")
        self.assertEqual(disputed["original_label"], "not_relevant")
        self.assertEqual(disputed["annotation_status"], "submitted")

    def test_five_expert_panel_privacy_agreement_and_approval_gates(self):
        self.login()
        submitter_id = self.database.user_by_username("research-admin")["id"]
        with self.database.connection() as connection:
            institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (submitter_id,),
            ).fetchone()["institution_id"]
        coordinator_id = self.database.ensure_admin(
            "panel-coordinator", "panel coordinator password long"
        )
        expert_ids = [
            self.database.ensure_admin(f"panel-expert-{index}", f"panel expert {index} password long")
            for index in range(5)
        ]
        with self.database.connection() as connection:
            for user_id in [coordinator_id, *expert_ids]:
                connection.execute(
                    """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                       VALUES (?, ?, 'administrator', 'active')""",
                    (user_id, institution_id),
                )
        records = [
            {
                "example_id": f"panel-case-{index}",
                "framework": "WURI",
                "indicator": next(iter(FRAMEWORK_INDICATORS["WURI"])),
                "label": bool(index % 2),
                "text": f"Private panel evidence text {index} unique evidence token {index * 13}.",
                "source_document_id": f"panel-doc-{index}",
                "annotation_version": "panel-import-v1",
                "annotation_provenance": "Synthetic test provenance only.",
                "annotation_status": "submitted",
                "original_prediction_json": json.dumps({"score": 0.99}),
            }
            for index in range(3)
        ]
        split = split_evidence_dataset(records, "panel-api-v1", 29).as_dict()
        dataset_id = self.database.create_research_dataset(
            submitter_id,
            institution_id,
            {
                "dataset_version": "panel-api-v1",
                "annotation_version": "panel-import-v1",
                "provenance": "Synthetic software test fixture, not research data.",
            },
            records,
            split,
        )
        assessment_id = self.database.create_assessment(
            coordinator_id, institution_id, "document_extracted"
        )
        with self.database.connection() as connection:
            for index, record in enumerate(records):
                connection.execute(
                    """INSERT INTO documents
                       (id, institution_id, assessment_id, filename, file_type, file_size,
                        checksum, storage_key, extraction_status, authorization_status,
                        research_permission_status, review_status, malware_scan_status)
                       VALUES (?, ?, ?, ?, 'text/plain', 1, ?, ?, 'completed',
                               'verified', 'verified', 'verified', 'clean')""",
                    (
                        record["source_document_id"], institution_id, assessment_id,
                        f"panel-{index}.txt", f"{index:064x}",
                        f"test-only/panel/{index}.txt",
                    ),
                )

        self._act_as(coordinator_id)
        insufficient_reviews = self.client.post(
            f"/api/research/datasets/{dataset_id}/review",
            params={"institution_id": institution_id},
            json={
                "decision": "approved",
                "note": "Insufficient panel judgments must block approval.",
                "source_use_clearance_reference": "Synthetic test clearance only.",
                "institutional_approval_reference": "Synthetic test approval only.",
            },
        )
        self.assertEqual(insufficient_reviews.status_code, 409)
        self.assertIn("five distinct, qualified expert ratings", insufficient_reviews.text)

        self._act_as(expert_ids[0])
        unverified_queue = self.client.get(
            f"/api/research/datasets/{dataset_id}/annotations",
            params={"institution_id": institution_id},
        )
        self.assertEqual(unverified_queue.status_code, 403)

        self._act_as(coordinator_id)
        for expert_id in expert_ids:
            response = self.client.post(
                "/api/research/expert-qualifications",
                params={"institution_id": institution_id},
                json={
                    "expert_id": expert_id,
                    "qualification_reference": f"reviewer credential record {expert_id}",
                    "note": "Qualification record used only for this synthetic software test.",
                    "status": "verified",
                },
            )
            self.assertEqual(response.status_code, 201, response.text)

        self._act_as(expert_ids[0])
        queue_response = self.client.get(
            f"/api/research/datasets/{dataset_id}/annotations",
            params={"institution_id": institution_id},
        )
        self.assertEqual(queue_response.status_code, 200, queue_response.text)
        queue = queue_response.json()["annotations"]
        self.assertEqual(len(queue), 3)
        self.assertNotIn("imported_label", queue[0])
        self.assertNotIn("original_prediction_json", queue[0])
        self.assertNotIn("reviewer_id", queue[0])

        invalid_score = self.client.post(
            f"/api/research/datasets/{dataset_id}/expert-panel-reviews",
            params={"institution_id": institution_id},
            json={"reviews": [{
                "example_id": records[0]["example_id"],
                "label": records[0]["label"],
                "rubric_version": "panel-rubric-v1",
                "continuous_ratings": {"evidence_strength": True},
                "note": "Invalid boolean score must be rejected.",
            }]},
        )
        self.assertEqual(invalid_score.status_code, 422)

        for expert_index, expert_id in enumerate(expert_ids):
            self._act_as(expert_id)
            panel_reviews = [
                {
                    "example_id": record["example_id"],
                    "label": record["label"],
                    "rubric_version": "panel-rubric-v1",
                    "continuous_ratings": {
                        "evidence_strength": 0.25 if index % 2 == 0 else 0.75,
                    },
                    "note": "Independent synthetic reviewer judgment for test coverage.",
                }
                for index, record in enumerate(records)
            ]
            response = self.client.post(
                f"/api/research/datasets/{dataset_id}/expert-panel-reviews",
                params={"institution_id": institution_id},
                json={"reviews": panel_reviews},
            )
            self.assertEqual(response.status_code, 201, response.text)
            if expert_id == expert_ids[0]:
                duplicate = self.client.post(
                    f"/api/research/datasets/{dataset_id}/expert-panel-reviews",
                    params={"institution_id": institution_id},
                    json={"reviews": panel_reviews},
                )
                self.assertEqual(duplicate.status_code, 422)
            if expert_index == 0:
                self._act_as(coordinator_id)
                partial_stats = self.client.get(
                    f"/api/research/datasets/{dataset_id}/expert-panel-agreement",
                    params={"institution_id": institution_id},
                ).json()
                self.assertEqual(partial_stats["complete_categorical_case_count"], 0)
                self.assertEqual(partial_stats["incomplete_case_count"], 3)
                self.assertIsNone(partial_stats["fleiss_kappa"]["kappa"])
                self.assertEqual(
                    partial_stats["fleiss_kappa"]["status"],
                    "undefined_no_complete_cases",
                )
                self._act_as(expert_ids[1])
                peer_queue = self.client.get(
                    f"/api/research/datasets/{dataset_id}/annotations",
                    params={"institution_id": institution_id},
                ).json()["annotations"]
                self.assertEqual(len(peer_queue), 3)
                self.assertNotIn("categorical_label", peer_queue[0])
                self.assertNotIn("reviewer_id", peer_queue[0])

        self._act_as(coordinator_id)
        stats_response = self.client.get(
            f"/api/research/datasets/{dataset_id}/expert-panel-agreement",
            params={"institution_id": institution_id},
        )
        self.assertEqual(stats_response.status_code, 200, stats_response.text)
        stats = stats_response.json()
        self.assertEqual(stats["complete_categorical_case_count"], 3)
        self.assertEqual(stats["fleiss_kappa"]["kappa"], 1)
        self.assertEqual(
            stats["continuous_ratings"]["evidence_strength"]["icc_2_1_candidate"],
            1,
        )
        self.assertEqual(stats["icc_model_status"], "requires_researcher_decision")

        procedure_response = self.client.post(
            "/api/research/consensus-procedures",
            params={"institution_id": institution_id},
            json={
                "procedure_id": "panel-consensus-v1",
                "procedure_version": "1",
                "approval_reference": "Synthetic test reference only.",
                "approving_authority": "Software test fixture",
                "rationale": "This procedure record exists only in a synthetic software test.",
            },
        )
        self.assertEqual(procedure_response.status_code, 201, procedure_response.text)
        for record in records:
            response = self.client.post(
                f"/api/research/datasets/{dataset_id}/expert-panel-consensus",
                params={"institution_id": institution_id},
                json={
                    "example_id": record["example_id"],
                    "final_label": record["label"],
                    "resolution": "consensus",
                    "procedure_id": "panel-consensus-v1",
                    "procedure_version": "1",
                    "note": "Synthetic explicit consensus record for software testing.",
                },
            )
            self.assertEqual(response.status_code, 201, response.text)

        approval = self.client.post(
            f"/api/research/datasets/{dataset_id}/review",
            params={"institution_id": institution_id},
            json={
                "decision": "approved",
                "note": "Synthetic test-only approval after panel fixture setup.",
                "source_use_clearance_reference": "Synthetic test clearance only.",
                "institutional_approval_reference": "Synthetic test approval only.",
            },
        )
        self.assertEqual(approval.status_code, 200, approval.text)
        with self.database.connection() as connection:
            event_types = {
                row["event_type"] for row in connection.execute(
                    "SELECT event_type FROM audit_events WHERE institution_id = ?",
                    (institution_id,),
                )
            }
        self.assertIn("research.expert_qualification.recorded", event_types)
        self.assertIn("research.expert_panel_reviews.submitted", event_types)
        self.assertIn("research.expert_panel_consensus.recorded", event_types)


if __name__ == "__main__":
    unittest.main()

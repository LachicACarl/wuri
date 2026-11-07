import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.deployment_readiness import build_readiness_report


class DeploymentReadinessTests(unittest.TestCase):
    def test_report_exposes_request_ingress_and_parser_isolation_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "WURI_DATABASE_PATH": str(Path(directory) / "missing.sqlite3"),
                    "WURI_STORAGE_PATH": str(Path(directory) / "private"),
                },
                clear=True,
            ):
                report = build_readiness_report()

        checks = {item["name"]: item["status"] for item in report["checks"]}
        self.assertEqual(checks["application_request_body_limit"], "ready")
        self.assertEqual(checks["ingress_body_limit"], "manual_verification_required")
        self.assertIn(checks["parser_worker_resource_limits"], {"ready", "blocked"})
        self.assertEqual(checks["parser_worker_container_isolation"], "manual_verification_required")
        self.assertEqual(report["intake_gate"], "blocked")

    def test_default_report_blocks_without_scanner_and_does_not_expose_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "WURI_DATABASE_PATH": str(Path(directory) / "missing.sqlite3"),
                    "WURI_STORAGE_PATH": str(Path(directory) / "private"),
                },
                clear=True,
            ):
                report = build_readiness_report()
        self.assertEqual(report["intake_gate"], "blocked")
        self.assertEqual(
            next(item for item in report["checks"] if item["name"] == "malware_scanner")["status"],
            "blocked",
        )
        serialized = str(report)
        self.assertNotIn("missing.sqlite3", serialized)


if __name__ == "__main__":
    unittest.main()

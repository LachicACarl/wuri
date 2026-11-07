import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.deployment_readiness import build_readiness_report
from app.cors_config import configured_cors_origins


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

    def test_cors_origin_configuration_uses_allowlist_and_blocks_production_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                configured_cors_origins(),
                [
                    "http://localhost:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:5174",
                ],
            )
        with patch.dict(os.environ, {"WURI_ENVIRONMENT": "production"}, clear=True):
            self.assertEqual(configured_cors_origins(), [])
        with patch.dict(
            os.environ,
            {
                "WURI_ENVIRONMENT": "production",
                "WURI_CORS_ORIGINS": "https://wuri.example, https://admin.wuri.example",
            },
            clear=True,
        ):
            self.assertEqual(
                configured_cors_origins(),
                ["https://wuri.example", "https://admin.wuri.example"],
            )

    def test_cors_configuration_rejects_wildcards_and_non_origin_urls(self):
        for value in ("*", "https://trusted.example/path", "javascript://trusted.example"):
            with self.subTest(origin=value), patch.dict(
                os.environ, {"WURI_CORS_ORIGINS": value}, clear=True
            ):
                with self.assertRaises(ValueError):
                    configured_cors_origins()

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

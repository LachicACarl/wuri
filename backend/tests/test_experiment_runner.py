import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.database import Database
from app.experiment_runner import (
    ResearchExperimentRunner, indicator_catalog_sha256, label_is_relevant,
    local_artifact_sha256, RETRIEVAL_METRIC_DEFINITIONS,
)
from app.indicators import FRAMEWORK_INDICATORS
from app.research_validation import split_evidence_dataset
from app.security import hash_password
from research_fixtures import approve_synthetic_panel_dataset


class ResearchExperimentRunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.database = Database(self.root / "research.sqlite3")
        self.user_id = self.database.ensure_admin("runner", hash_password("runner password long"))
        with self.database.connection() as connection:
            self.institution_id = connection.execute(
                "SELECT institution_id FROM institution_memberships WHERE user_id = ?",
                (self.user_id,),
            ).fetchone()["institution_id"]
        self.dataset_id = self._approved_fixture_dataset()

    def tearDown(self):
        self.directory.cleanup()

    def test_label_relevance_rejects_values_outside_binary_mapping(self):
        self.assertTrue(label_is_relevant(" relevant "))
        self.assertFalse(label_is_relevant("not_relevant"))
        with self.assertRaisesRegex(ValueError, "binary relevance labels"):
            label_is_relevant("uncertain")

    def _approved_fixture_dataset(self):
        records = [
            {
                "example_id": f"runner-fixture-{index}",
                "text": f"Synthetic software test fixture evidence record {index} unique token {index * 13}.",
                "framework": "WURI",
                "indicator": tuple(FRAMEWORK_INDICATORS["WURI"])[index % 4],
                "label": bool(index % 2),
                "source_document_id": f"runner-doc-{index}",
                "annotation_version": "synthetic-fixture-v1",
                "annotation_provenance": "synthetic software test fixture only",
                "annotation_status": "expert_reviewed",
            }
            for index in range(30)
        ]
        split = split_evidence_dataset(records, "synthetic-runner-fixture-v1", 41).as_dict()
        dataset_id = self.database.create_research_dataset(
            self.user_id,
            self.institution_id,
            {
                "dataset_version": "synthetic-runner-fixture-v1",
                "annotation_version": "synthetic-fixture-v1",
                "provenance": "synthetic software fixture; not research data",
            },
            records,
            split,
        )
        approve_synthetic_panel_dataset(
            self.database, self.institution_id, dataset_id, self.user_id, records,
            "runner-panel",
        )
        return dataset_id

    def _ready_protocol_environment(self):
        model_path = self.root / "test-model"
        model_path.mkdir()
        (model_path / "modules.json").write_text("[]", encoding="utf-8")
        (model_path / "config.json").write_text("{}", encoding="utf-8")
        protocol_path = self.root / "protocol.json"
        protocol_path.write_text(json.dumps({
            "approval_status": "approved",
            "chapter3_verified": True,
            "protocol_version": "fixture-protocol-v1",
            "approved_by": "test-reviewer",
            "approval_reference": "synthetic-test-only",
            "models": {
                "baseline": {
                    "approved": True,
                    "version": "fixture-model-v1",
                    "artifact_sha256": local_artifact_sha256(str(model_path)),
                    "configuration": {"max_seq_length": 256},
                },
            },
            "retrieval_evaluation": {
                "approved": True,
                "version": "fixture-retrieval-v1",
                "k_values": [1, 3, 5],
                "relevant_labels": sorted({"true", "1", "yes", "positive", "relevant"}),
                "non_relevant_labels": sorted({"false", "0", "no", "negative", "not_relevant"}),
                "model_parameters": {"normalize_embeddings": True, "batch_size": 32},
                "metric_definitions": RETRIEVAL_METRIC_DEFINITIONS,
            },
            "indicator_configuration": {
                "approved": True,
                "version": "fixture-indicators-v1",
                "catalog_sha256": indicator_catalog_sha256(),
            },
            "criterion_aggregation_policy": {"approved": True, "version": "fixture-only"},
            "conventional_ahp_topsis": {
                "approved": True,
                "version": "fixture-only",
                "pairwise_comparison_matrices": {"WURI": [[1]]},
                "topsis_method": "fixture-only",
            },
        }), encoding="utf-8")
        return {
            "WURI_BASELINE_MODEL_PATH": str(model_path),
            "WURI_BASELINE_MODEL_VERSION": "fixture-model-v1",
            "WURI_RESEARCH_PROTOCOL_PATH": str(protocol_path),
        }

    def test_preflight_blocks_missing_dataset(self):
        runner = ResearchExperimentRunner(self.database)
        report = runner.preflight(self.user_id, self.institution_id, None, "A0")
        self.assertEqual(report["state"], "blocked_missing_data")
        self.assertFalse(report["execution_allowed"])

    def test_preflight_blocks_unreviewed_dataset(self):
        original = self.database.research_dataset_bundle

        def unreviewed(*args, **kwargs):
            bundle = original(*args, **kwargs)
            bundle["dataset"]["verification_status"] = "submitted"
            return bundle

        with patch.object(self.database, "research_dataset_bundle", side_effect=unreviewed):
            report = ResearchExperimentRunner(self.database).preflight(
                self.user_id, self.institution_id, self.dataset_id, "A0"
            )
        self.assertEqual(report["state"], "blocked_missing_data")
        self.assertEqual(report["checks"][0]["status"], "blocked_missing_data")

    def test_preflight_blocks_missing_model_artifact(self):
        report = ResearchExperimentRunner(self.database, environment={}).preflight(
            self.user_id, self.institution_id, self.dataset_id, "A0"
        )
        self.assertEqual(report["state"], "blocked_missing_model")

    def test_preflight_blocks_unresolved_scoring_and_methodology(self):
        model_path = self.root / "configured-model"
        model_path.mkdir()
        (model_path / "modules.json").write_text("[]", encoding="utf-8")
        (model_path / "config.json").write_text("{}", encoding="utf-8")
        environment = {
            "WURI_BASELINE_MODEL_PATH": str(model_path),
            "WURI_BASELINE_MODEL_VERSION": "fixture-only",
        }
        report = ResearchExperimentRunner(self.database, environment=environment).preflight(
            self.user_id, self.institution_id, self.dataset_id, "A0", "readiness"
        )
        self.assertEqual(report["state"], "blocked_methodology_review")
        self.assertIn(
            "conventional_ahp_topsis_configuration",
            {check["name"] for check in report["checks"]},
        )

    def test_a0_dispatches_only_its_registered_executor(self):
        calls = []

        def baseline_executor(bundle, context):
            calls.append((
                "A0",
                context["seed"],
                any(
                    any(key in row for key in (
                        "label", "original_label", "original_prediction_json",
                        "annotation_resolution", "source_annotation_status",
                    ))
                    for row in bundle["test_records"]
                ),
                "preflight" in context,
            ))
            return {
                "predictions": [
                    {
                        "example_id": row["example_id"],
                        "prediction": int(row["example_id"].rsplit("-", 1)[1]) / 30,
                        "partition_name": "test",
                    }
                    for row in bundle["test_records"]
                ],
            }

        def enhanced_executor(bundle, context):
            calls.append(("A1", context["seed"]))
            return {"results": {"unexpected": True}}

        runner = ResearchExperimentRunner(
            self.database,
            executors={"A0": baseline_executor, "A1": enhanced_executor},
            environment=self._ready_protocol_environment(),
        )
        result = runner.run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 41
        )
        self.assertTrue(result["preflight"]["execution_allowed"])
        self.assertEqual(calls, [("A0", 41, False, False)])
        stored = self.database.get_research_experiment(
            self.user_id, self.institution_id, result["experiment_id"]
        )
        self.assertEqual(stored["execution_state"], "completed")
        result_json = json.loads(stored["result_json"])
        self.assertEqual(result_json["evaluation_type"], "held_out_evidence_retrieval")
        bundle = self.database.research_dataset_bundle(
            self.user_id, self.institution_id, self.dataset_id
        )
        test_records = [row for row in bundle["records"] if row["partition_name"] == "test"]
        for cutoff in (1, 3, 5):
            precisions = []
            recalls = []
            for framework, indicator in {
                (row["framework"], row["indicator"]) for row in test_records
            }:
                group = [
                    row for row in test_records
                    if row["framework"] == framework and row["indicator"] == indicator
                ]
                relevant = {row["example_id"] for row in group if label_is_relevant(row["label"])}
                if not relevant:
                    continue
                ranked = sorted(
                    group,
                    key=lambda row: (
                        -int(row["example_id"].rsplit("-", 1)[1]) / 30,
                        row["example_id"],
                    ),
                )
                hits = len({row["example_id"] for row in ranked[:cutoff]} & relevant)
                precisions.append(hits / cutoff)
                recalls.append(hits / len(relevant))
            self.assertAlmostEqual(
                result_json["retrieval_metrics"]["aggregate"][f"precision@{cutoff}"],
                sum(precisions) / len(precisions),
            )
            self.assertAlmostEqual(
                result_json["retrieval_metrics"]["aggregate"][f"recall@{cutoff}"],
                sum(recalls) / len(recalls),
            )
        counts = json.loads(stored["sample_counts_json"])
        self.assertEqual(counts["test_evaluated"], counts["test"])
        self.assertEqual(
            counts["eligible_test_queries"],
            result_json["retrieval_metrics"]["aggregate"]["evaluated_queries@1"],
        )
        runtime_versions = json.loads(stored["evaluation_config_json"])["runtime_dependency_versions"]
        self.assertEqual(
            set(runtime_versions),
            {"sentence-transformers", "transformers", "torch", "numpy"},
        )
        self.assertTrue(all(isinstance(value, str) and value for value in runtime_versions.values()))

    def test_a0_preflight_requires_approved_metric_definitions(self):
        environment = self._ready_protocol_environment()
        protocol_path = Path(environment["WURI_RESEARCH_PROTOCOL_PATH"])
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        protocol["retrieval_evaluation"].pop("metric_definitions")
        protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
        report = ResearchExperimentRunner(
            self.database, environment=environment
        ).preflight(self.user_id, self.institution_id, self.dataset_id, "A0")
        self.assertFalse(report["execution_allowed"])
        self.assertIn(
            "approved_retrieval_evaluation",
            {check["name"] for check in report["checks"] if check["status"] != "passed"},
        )

    def test_a0_preflight_rejects_unapplied_model_configuration(self):
        environment = self._ready_protocol_environment()
        protocol_path = Path(environment["WURI_RESEARCH_PROTOCOL_PATH"])
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        protocol["models"]["baseline"]["configuration"]["unapplied_setting"] = "fixture"
        protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
        report = ResearchExperimentRunner(
            self.database, environment=environment
        ).preflight(self.user_id, self.institution_id, self.dataset_id, "A0")
        self.assertFalse(report["execution_allowed"])
        self.assertIn(
            "recorded_model_configuration",
            {check["name"] for check in report["checks"] if check["status"] != "passed"},
        )

    def test_a0_run_rejects_protocol_changes_after_preflight(self):
        environment = self._ready_protocol_environment()
        runner = ResearchExperimentRunner(
            self.database,
            executors={"A0": lambda payload, context: {"predictions": []}},
            environment=environment,
        )
        original_preflight = runner.preflight

        def mutate_protocol(*args, **kwargs):
            report = original_preflight(*args, **kwargs)
            protocol_path = Path(environment["WURI_RESEARCH_PROTOCOL_PATH"])
            protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
            protocol["protocol_version"] = "changed-after-preflight"
            protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
            return report

        runner.preflight = mutate_protocol
        result = runner.run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 46
        )
        self.assertEqual(result["execution_state"], "failed")
        self.assertIsNone(result["results"])

    def test_a0_readiness_scope_does_not_fall_back_to_retrieval_completion(self):
        runner = ResearchExperimentRunner(
            self.database, environment=self._ready_protocol_environment()
        )
        report = runner.preflight(
            self.user_id, self.institution_id, self.dataset_id, "A0", "readiness"
        )
        self.assertEqual(report["state"], "not_implemented")
        self.assertFalse(report["execution_allowed"])
        self.assertIn(
            "conventional_ahp_topsis_configuration",
            {check["name"] for check in report["checks"]},
        )

    def test_retrieval_prediction_validation_allows_small_rounding_error_only(self):
        def make_executor(score):
            def run(executor_bundle, context):
                return {
                    "predictions": [
                        {
                            "example_id": record["example_id"],
                            "prediction": score,
                            "partition_name": "test",
                        }
                        for record in executor_bundle["test_records"]
                    ],
                }
            return run

        runner = ResearchExperimentRunner(
            self.database, environment=self._ready_protocol_environment()
        )
        runner.executors["A0"] = make_executor(1.0000005)
        accepted = runner.run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 42
        )
        self.assertEqual(accepted["execution_state"], "completed")

        runner.executors["A0"] = make_executor(1.01)
        rejected = runner.run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 43
        )
        self.assertEqual(rejected["execution_state"], "failed")

    def test_a1_through_a4_block_without_enhanced_artifact(self):
        runner = ResearchExperimentRunner(
            self.database,
            executors={key: lambda *_: {"results": {"fixture": True}}
                       for key in ("A1", "A2", "A3", "A4")},
            environment={},
        )
        for ablation_id in ("A1", "A2", "A3", "A4"):
            with self.subTest(ablation_id=ablation_id):
                report = runner.preflight(
                    self.user_id, self.institution_id, self.dataset_id, ablation_id
                )
                self.assertEqual(report["state"], "blocked_missing_model")
                self.assertFalse(report["execution_allowed"])

    def test_blocked_runs_have_no_results_and_record_reproducibility_context(self):
        runner = ResearchExperimentRunner(self.database, environment={})
        result = runner.run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 41
        )
        stored = self.database.get_research_experiment(
            self.user_id, self.institution_id, result["experiment_id"]
        )
        self.assertIsNone(stored["result_json"])
        self.assertEqual(stored["execution_state"], "blocked_missing_model")
        config = json.loads(stored["configuration_json"])
        self.assertEqual(config["dataset_id"], self.dataset_id)
        self.assertEqual(config["random_seed"], 41)
        self.assertEqual(config["dataset_review_status"], "approved")

    def test_failed_executor_is_persisted_without_stack_trace_or_metrics(self):
        def broken_executor(*_):
            raise RuntimeError("private model path should not be returned")

        runner = ResearchExperimentRunner(
            self.database,
            executors={"A0": broken_executor},
            environment=self._ready_protocol_environment(),
        )
        result = runner.run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 41
        )
        stored = self.database.get_research_experiment(
            self.user_id, self.institution_id, result["experiment_id"]
        )
        self.assertEqual(stored["execution_state"], "failed")
        self.assertIsNone(stored["result_json"])
        self.assertNotIn("private model path", stored["error_summary"])

    def test_experiment_record_survives_database_reopen(self):
        result = ResearchExperimentRunner(self.database, environment={}).run(
            self.user_id, self.institution_id, self.dataset_id, "A0", 41
        )
        reopened = Database(self.root / "research.sqlite3")
        stored = reopened.get_research_experiment(
            self.user_id, self.institution_id, result["experiment_id"]
        )
        self.assertEqual(stored["execution_state"], "blocked_missing_model")


if __name__ == "__main__":
    unittest.main()

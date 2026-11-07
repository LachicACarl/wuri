from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib.metadata import version as package_version
import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Callable

from .ahp import calculate_ahp
from .indicators import FRAMEWORK_INDICATORS
from .research_validation import (
    ABLATIONS, classification_metrics, retrieval_metrics, split_evidence_dataset,
)


Executor = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
LOGGER = logging.getLogger(__name__)
EQAM_DIMENSIONS = {
    "semantic_relevance", "model_confidence", "evidence_completeness",
    "source_reliability", "evidence_strength",
}
READINESS_REFERENCE_DIMENSIONS = {"arrs", "rrs:WURI", "rrs:THE", "rrs:QS", "rrs:UI GreenMetric"}
XAI_DIMENSIONS = {
    "xai:clarity", "xai:interpretability", "xai:traceability",
    "xai:usefulness", "xai:numerical_consistency", "xai:user_confidence",
}
FRAMEWORKS = ("WURI", "THE", "QS", "UI GreenMetric")
RELEVANT_LABELS = {"true", "1", "yes", "positive", "relevant"}
NON_RELEVANT_LABELS = {"false", "0", "no", "negative", "not_relevant"}
RETRIEVAL_METRIC_DEFINITIONS = {
    "query_unit": "framework_indicator_pair",
    "candidate_pool": "test_partition_records_matching_framework_and_indicator",
    "eligible_query_rule": "at_least_one_relevant_candidate",
    "precision_denominator": "k",
    "recall_denominator": "relevant_candidates_in_query_pool",
    "per_framework_aggregation": "macro_mean_over_eligible_queries",
    "overall_aggregation": "macro_mean_over_all_eligible_queries",
    "undefined_metric_policy": "null_when_no_eligible_queries",
    "ranking_tie_break": "example_id_ascending",
}


def indicator_catalog_sha256() -> str:
    encoded = json.dumps(FRAMEWORK_INDICATORS, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _manifest_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def label_is_relevant(label: Any) -> bool:
    if isinstance(label, bool):
        return label
    normalized = str(label).strip().casefold()
    if normalized in RELEVANT_LABELS:
        return True
    if normalized in NON_RELEVANT_LABELS:
        return False
    raise ValueError("Approved annotations must use the documented binary relevance labels.")


def _valid_baseline_model_configuration(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"max_seq_length"}
        and isinstance(value["max_seq_length"], int)
        and not isinstance(value["max_seq_length"], bool)
        and value["max_seq_length"] > 0
    )


def local_artifact_sha256(path: str | None) -> str | None:
    if not path or not has_local_sentence_transformer_artifact(path):
        return None
    root = Path(path)
    digest = hashlib.sha256()
    try:
        for candidate in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(candidate.relative_to(root).as_posix().encode("utf-8") + b"\0")
            with candidate.open("rb") as artifact_file:
                while chunk := artifact_file.read(1024 * 1024):
                    digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _sentence_bert_retrieval_executor(
    payload: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    from sentence_transformers import SentenceTransformer, util

    model = SentenceTransformer(context["model_artifact_path"], local_files_only=True)
    protocol = context["approved_protocol"]
    model_config = protocol["models"]["baseline"]["configuration"]
    model.max_seq_length = model_config["max_seq_length"]
    evaluation = protocol["retrieval_evaluation"]
    parameters = evaluation["model_parameters"]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in payload["test_records"]:
        groups.setdefault((record["framework"], record["indicator"]), []).append(record)

    predictions: list[dict[str, Any]] = []
    for (framework, indicator), candidates in sorted(groups.items()):
        query = FRAMEWORK_INDICATORS[framework][indicator]
        query_embedding = model.encode(
            query, convert_to_tensor=True,
            normalize_embeddings=parameters["normalize_embeddings"],
            show_progress_bar=False,
        )
        candidate_embeddings = model.encode(
            [record["text"] for record in candidates],
            convert_to_tensor=True,
            normalize_embeddings=parameters["normalize_embeddings"],
            batch_size=parameters["batch_size"],
            show_progress_bar=False,
        )
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].tolist()
        predictions.extend(
            {"example_id": record["example_id"], "prediction": float(score)}
            for record, score in zip(candidates, scores)
        )
    return {
        "predictions": predictions,
        "warnings": [],
        "limitations": [
            "Held-out evidence retrieval only; no AES, AHP–TOPSIS, RRS, or ARRS scores are calculated."
        ],
    }


def _check(name: str, passed: bool, reason: str, *, missing_state: str = "blocked_missing_data") -> dict[str, str]:
    return {
        "name": name,
        "status": "passed" if passed else missing_state,
        "reason": reason,
    }


def has_local_sentence_transformer_artifact(path: str | None) -> bool:
    if not path:
        return False
    root = Path(path)
    if not root.is_dir():
        return False
    return (
        (root / "modules.json").is_file()
        and any((root / filename).is_file()
                for filename in ("config.json", "sentence_bert_config.json"))
    )


def _valid_pairwise_matrices(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    try:
        return all(
            isinstance(matrix, list) and calculate_ahp(matrix).accepted
            for matrix in value.values()
        )
    except (TypeError, ValueError):
        return False


class ResearchExperimentRunner:
    """Preflight and persist reproducible runs; execution requires an explicit pipeline."""

    def __init__(
        self,
        database,
        executors: dict[str, Executor] | None = None,
        environment: dict[str, str] | None = None,
    ):
        self.database = database
        self.executors = (
            {"A0": _sentence_bert_retrieval_executor}
            if executors is None else executors
        )
        self.environment = os.environ if environment is None else environment

    def preflight(
        self,
        user_id: str,
        institution_id: str,
        dataset_id: str | None,
        ablation_id: str,
        evaluation_scope: str = "retrieval",
    ) -> dict[str, Any]:
        if ablation_id not in ABLATIONS:
            raise ValueError("Unsupported ablation configuration.")
        if evaluation_scope not in {"retrieval", "readiness"}:
            raise ValueError("Unsupported research evaluation scope.")
        if evaluation_scope == "retrieval" and ablation_id != "A0":
            evaluation_scope = "readiness"
        checks: list[dict[str, str]] = []
        bundle = None
        if dataset_id:
            bundle = self.database.research_dataset_bundle(user_id, institution_id, dataset_id)
        dataset = bundle["dataset"] if bundle else None
        records = bundle["records"] if bundle else []
        dataset_approved = bool(
            dataset
            and dataset["verification_status"] == "approved"
            and dataset.get("review_design") == "five_expert_panel"
            and dataset.get("consensus_procedure_id")
            and dataset.get("source_use_clearance_reference")
            and dataset.get("institutional_approval_reference")
        )
        checks.append(_check(
            "approved_dataset",
            dataset_approved,
            "An independently approved dataset version is required."
            if not dataset_approved else "The selected dataset has independent administrator approval.",
        ))

        annotations_reviewed = bool(records) and all(
            row["annotation_status"] in {"expert_reviewed", "adjudicated"}
            and row["annotation_version"]
            and row["annotation_resolution"] in {"agreement", "adjudicated"}
            for row in records
        )
        checks.append(_check(
            "reviewed_annotations",
            annotations_reviewed,
            "Every example must have a reviewed annotation status and annotation version."
            if not annotations_reviewed else "All selected examples have reviewed annotations.",
        ))
        if ablation_id == "A0" and evaluation_scope == "retrieval":
            retrieval_query_counts = _retrieval_query_counts(records)
            retrieval_data_valid = bool(records) and all(
                row.get("framework") in FRAMEWORK_INDICATORS
                and row.get("indicator") in FRAMEWORK_INDICATORS.get(row.get("framework"), {})
                and isinstance(row.get("text"), str) and bool(row["text"].strip())
                and isinstance(row.get("source_document_id"), str)
                and bool(row["source_document_id"].strip())
                and row.get("annotation_resolution") in {"agreement", "adjudicated"}
                for row in records
            )
            if retrieval_data_valid:
                try:
                    for row in records:
                        label_is_relevant(row["label"])
                except ValueError:
                    retrieval_data_valid = False
            checks.append(_check(
                "retrieval_dataset_schema",
                retrieval_data_valid,
                "Every approved example must have a reviewed binary relevance label, known framework/indicator, traceable source-document ID, and resolved evidence text."
                if not retrieval_data_valid else "The approved held-out retrieval records satisfy the required schema.",
            ))
            has_eligible_queries = retrieval_query_counts["eligible_test_queries"] > 0
            checks.append(_check(
                "eligible_test_queries",
                has_eligible_queries,
                "At least one test query must contain a consensus-relevant candidate."
                if not has_eligible_queries else "The test partition contains eligible relevance queries.",
            ))
        else:
            retrieval_query_counts = {
                "test_queries": 0,
                "eligible_test_queries": 0,
                "by_framework": {},
            }

        manifest_valid = False
        partition_counts: dict[str, int] = {"train": 0, "validation": 0, "test": 0}
        if dataset and records:
            try:
                recomputed = split_evidence_dataset(
                    [
                        {
                            **row,
                            "label": row["original_label"],
                            "annotation_status": row["source_annotation_status"],
                        }
                        for row in records
                    ],
                    dataset["dataset_version"], dataset["split_seed"]
                ).as_dict()
                persisted = json.loads(dataset["split_summary_json"])
                manifest_valid = (
                    dataset["split_version"] == recomputed["split_version"]
                    and persisted.get("assignments") == recomputed["assignments"]
                    and persisted.get("counts") == recomputed["counts"]
                    and persisted.get("group_counts") == recomputed["group_counts"]
                    and persisted.get("seed") == dataset["split_seed"]
                    and persisted.get("proportions") == recomputed["proportions"]
                    and all(row["partition_name"] == recomputed["assignments"][row["example_id"]]
                            for row in records)
                    and sum(recomputed["counts"].values()) == len(records)
                )
                partition_counts = recomputed["counts"]
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                manifest_valid = False
        checks.append(_check(
            "partition_manifest",
            manifest_valid,
            "The stored split manifest is missing, inconsistent, or cannot be reproduced."
            if not manifest_valid else "The immutable grouped split manifest was reproduced and verified.",
        ))

        model_path_key = "WURI_BASELINE_MODEL_PATH" if ablation_id == "A0" else "WURI_ENHANCED_MODEL_PATH"
        model_version_key = "WURI_BASELINE_MODEL_VERSION" if ablation_id == "A0" else "WURI_ENHANCED_MODEL_VERSION"
        model_path = self.environment.get(model_path_key)
        model_version = self.environment.get(model_version_key)
        artifact_sha256 = local_artifact_sha256(model_path)
        model_ready = bool(
            model_version and artifact_sha256
        )
        checks.append(_check(
            "model_artifact",
            model_ready,
            "A versioned local Sentence-BERT artifact is required; no remote or fallback model is loaded."
            if not model_ready else "A versioned local model artifact is configured.",
            missing_state="blocked_missing_model",
        ))

        protocol = self._load_protocol()
        protocol_approved = bool(
            protocol
            and protocol.get("approval_status") == "approved"
            and protocol.get("chapter3_verified") is True
            and protocol.get("protocol_version")
            and protocol.get("approved_by")
            and protocol.get("approval_reference")
        )
        protocol_manifest_sha256 = (
            _manifest_sha256(protocol) if protocol_approved else None
        )
        checks.append(_check(
            "approved_evaluation_protocol",
            protocol_approved,
            "A versioned, independently approved Chapter 3 protocol manifest is required."
            if not protocol_approved else "The evaluation protocol manifest records independent approval.",
            missing_state="blocked_methodology_review",
        ))
        model_role = "baseline" if ablation_id == "A0" else "enhanced"
        model_registry = protocol.get("models", {}) if protocol else {}
        if not isinstance(model_registry, dict):
            model_registry = {}
        recorded_model = model_registry.get(model_role, {})
        if not isinstance(recorded_model, dict):
            recorded_model = {}
        model_config_recorded = bool(
            protocol_approved
            and recorded_model.get("approved") is True
            and recorded_model.get("version") == model_version
            and recorded_model.get("artifact_sha256") == artifact_sha256
            and _valid_baseline_model_configuration(recorded_model.get("configuration"))
        )
        checks.append(_check(
            "recorded_model_configuration",
            model_config_recorded,
            "The approved protocol must record the exact version selected for this model role."
            if not model_config_recorded else "The model version matches its protocol record.",
            missing_state="blocked_methodology_review",
        ))
        aggregation_policy = protocol.get("criterion_aggregation_policy") if protocol else None
        aggregation_approved = bool(
            isinstance(aggregation_policy, dict)
            and aggregation_policy.get("approved") is True
            and aggregation_policy.get("version")
        )
        conventional = protocol.get("conventional_ahp_topsis", {}) if protocol else {}
        if not isinstance(conventional, dict):
            conventional = {}
        framework_protocol = protocol.get("framework_scoring", {}) if protocol else {}
        if not isinstance(framework_protocol, dict):
            framework_protocol = {}
        conventional_scoring = bool(
            protocol_approved
            and conventional.get("approved") is True
            and conventional.get("version")
            and _valid_pairwise_matrices(conventional.get("pairwise_comparison_matrices"))
            and conventional.get("topsis_method")
            and aggregation_approved
        )
        retrieval_config = protocol.get("retrieval_evaluation", {}) if protocol else {}
        if not isinstance(retrieval_config, dict):
            retrieval_config = {}
        indicator_config = protocol.get("indicator_configuration", {}) if protocol else {}
        if not isinstance(indicator_config, dict):
            indicator_config = {}
        if ablation_id == "A0" and evaluation_scope == "retrieval":
            retrieval_ready = bool(
                protocol_approved
                and retrieval_config.get("approved") is True
                and retrieval_config.get("version")
                and retrieval_config.get("k_values") == [1, 3, 5]
                and retrieval_config.get("relevant_labels") == sorted(RELEVANT_LABELS)
                and retrieval_config.get("non_relevant_labels") == sorted(NON_RELEVANT_LABELS)
                and retrieval_config.get("model_parameters") == {
                    "normalize_embeddings": True, "batch_size": 32,
                }
                and retrieval_config.get("metric_definitions") == RETRIEVAL_METRIC_DEFINITIONS
            )
            checks.append(_check(
                "approved_retrieval_evaluation",
                retrieval_ready,
                "The protocol must approve binary labels, cutoffs and encoding, plus the exact query, aggregation, tie-break, and undefined-metric definitions."
                if not retrieval_ready else "The retrieval metric and encoding configuration matches the approved protocol.",
                missing_state="blocked_methodology_review",
            ))
            indicator_ready = bool(
                protocol_approved
                and indicator_config.get("approved") is True
                and indicator_config.get("version")
                and indicator_config.get("catalog_sha256") == indicator_catalog_sha256()
            )
            checks.append(_check(
                "approved_indicator_configuration",
                indicator_ready,
                "The protocol must approve the exact framework-indicator catalog version and digest."
                if not indicator_ready else "The approved indicator catalog digest matches this installation.",
                missing_state="blocked_methodology_review",
            ))
        if evaluation_scope == "readiness" and ablation_id in {"A0", "A1", "A2"}:
            checks.append(_check(
                "conventional_ahp_topsis_configuration",
                conventional_scoring,
                "An approved, versioned conventional AHP–TOPSIS configuration is required."
                if not conventional_scoring else "The conventional AHP–TOPSIS configuration is approved.",
                missing_state="blocked_methodology_review",
            ))

        requirements = self.database.dataset_run_requirements(
            user_id, institution_id, dataset_id
        ) if dataset_id and dataset else {}
        if ablation_id in {"A2", "A3", "A4"}:
            checks.append(_check(
                "expert_eqam_validation",
                set(requirements.get("eqam_dimensions", [])) == EQAM_DIMENSIONS
                and requirements.get("eqam_min_raters_per_dimension", 0) >= 2,
                "Two independently reviewed expert raters must cover all five EQAM dimensions for this dataset.",
            ))
            checks.append(_check(
                "locked_validation_threshold",
                bool(requirements.get("locked_threshold")),
                "A threshold locked using validation-partition predictions and labels is required.",
            ))
        if ablation_id in {"A3", "A4"}:
            framework_config = framework_protocol
            verified_weights = framework_config.get("verified_weights")
            framework_matrices = framework_config.get("pairwise_comparison_matrices")
            framework_ready = bool(
                protocol_approved
                and framework_config.get("approved") is True
                and aggregation_approved
                and isinstance(verified_weights, dict)
                and set(verified_weights) == set(FRAMEWORKS)
                and _valid_pairwise_matrices(framework_matrices)
                and set(framework_matrices) == set(FRAMEWORKS)
            )
            checks.append(_check(
                "approved_framework_scoring",
                framework_ready,
                "Approved criterion aggregation and verified framework weights are required."
                if not framework_ready else "Framework scoring policy and weights are approved.",
                missing_state="blocked_methodology_review",
            ))
            checks.append(_check(
                "expert_readiness_references",
                set(requirements.get("readiness_reference_dimensions", [])) == READINESS_REFERENCE_DIMENSIONS
                and requirements.get("readiness_min_raters_per_dimension", 0) >= 2,
                "Two independently reviewed references must cover ARRS and all four framework RRS dimensions.",
            ))
        if ablation_id == "A4":
            xai_config = protocol.get("xai", {}) if protocol else {}
            if not isinstance(xai_config, dict):
                xai_config = {}
            xai_ready = bool(
                protocol_approved and xai_config.get("approved") is True
                and xai_config.get("instrument_version")
                and set(requirements.get("xai_dimensions", [])) == XAI_DIMENSIONS
                and requirements.get("xai_min_raters_per_dimension", 0) >= 2
            )
            checks.append(_check(
                "approved_xai_instrument_and_ratings",
                xai_ready,
                "An approved XAI instrument and independently reviewed ratings are required."
                if not xai_ready else "The XAI instrument and ratings are available.",
                missing_state="blocked_methodology_review",
            ))

        executor_ready = (
            evaluation_scope == "retrieval" and ablation_id == "A0"
            and "A0" in self.executors
        )
        checks.append(_check(
            "implemented_pipeline",
            executor_ready,
            "A full readiness-scoring executor is not implemented; the A0 executor evaluates retrieval only."
            if not executor_ready and evaluation_scope == "readiness"
            else "This A1–A4 pipeline has no registered executor."
            if not executor_ready
            else "The A0 Sentence-BERT held-out retrieval evaluator is registered.",
            missing_state="not_implemented",
        ))

        state = "ready_to_run"
        if not dataset_approved or not manifest_valid:
            state = "blocked_missing_data"
        else:
            for candidate in (
                "blocked_missing_model", "blocked_methodology_review",
                "blocked_missing_data", "not_implemented",
            ):
                if any(item["status"] == candidate for item in checks):
                    state = candidate
                    break
        return {
            "configuration_id": ablation_id,
            "configuration_name": ABLATIONS[ablation_id]["name"],
            "evaluation_scope": evaluation_scope,
            "state": state,
            "execution_allowed": state == "ready_to_run",
            "checks": checks,
            "dataset": ({
                "dataset_id": dataset["id"],
                "dataset_version": dataset["dataset_version"],
                "partition_manifest_version": dataset["split_version"],
                "partition_counts": partition_counts,
            } if dataset else None),
            "retrieval_query_counts": retrieval_query_counts,
            "model": {
                "artifact_configured": model_ready,
                "artifact_hash_verified": model_ready,
                "version": model_version if model_ready else None,
                "artifact_sha256": artifact_sha256 if model_ready else None,
                "role": "baseline" if ablation_id == "A0" else "enhanced",
            },
            "protocol_version": protocol.get("protocol_version") if protocol_approved else None,
            "protocol_manifest_sha256": protocol_manifest_sha256,
            "evaluation_configuration": {
                "protocol_version": protocol.get("protocol_version") if protocol_approved else None,
                "conventional_ahp_topsis_version": (
                    conventional.get("version") if conventional_scoring else None
                ),
                "framework_scoring_version": (
                    framework_protocol.get("version")
                    if protocol_approved and ablation_id in {"A3", "A4"} else None
                ),
                "criterion_aggregation_policy_version": (
                    aggregation_policy.get("version") if aggregation_approved else None
                ),
                "threshold_selection_partition": "validation",
                "test_partition_used_for_calibration": False,
                "criterion_aggregation_policy": (
                    protocol.get("criterion_aggregation_policy") if protocol_approved else None
                ),
                "retrieval_evaluation": (
                    retrieval_config if protocol_approved and evaluation_scope == "retrieval" else None
                ),
                "indicator_configuration": (
                    indicator_config if protocol_approved and evaluation_scope == "retrieval" else None
                ),
                "model_configuration": (
                    recorded_model.get("configuration") if model_config_recorded else None
                ),
            },
        }

    def run(
        self,
        user_id: str,
        institution_id: str,
        dataset_id: str | None,
        ablation_id: str,
        seed: int,
        evaluation_scope: str = "retrieval",
    ) -> dict[str, Any]:
        report = self.preflight(
            user_id, institution_id, dataset_id, ablation_id, evaluation_scope
        )
        if not report["execution_allowed"]:
            experiment_id = self.database.persist_research_execution(
                user_id,
                institution_id,
                dataset_id=dataset_id if report["dataset"] else None,
                ablation_id=ablation_id,
                seed=seed,
                model_version=report["model"]["version"],
                execution_state=report["state"],
                preflight=report,
            )
            return {
                "experiment_id": experiment_id,
                "execution_state": report["state"],
                "preflight": report,
                "results": None,
            }

        executor = self.executors[ablation_id]
        started_at = datetime.now(timezone.utc).isoformat()
        try:
            approved_protocol = self._load_protocol()
            if (
                not approved_protocol
                or _manifest_sha256(approved_protocol) != report["protocol_manifest_sha256"]
            ):
                raise ValueError("Approved protocol changed after preflight.")
            bundle = self.database.research_dataset_bundle(user_id, institution_id, dataset_id)
            payload = self._partition_executor_input(
                bundle, retrieval_only=evaluation_scope == "retrieval"
            )
            model_path_key = (
                "WURI_BASELINE_MODEL_PATH" if ablation_id == "A0"
                else "WURI_ENHANCED_MODEL_PATH"
            )
            model_path = self.environment.get(model_path_key)
            if local_artifact_sha256(model_path) != report["model"]["artifact_sha256"]:
                raise ValueError("Approved model artifact changed after preflight.")
            outcome = executor(payload, {
                "seed": seed,
                "model_artifact_path": model_path,
                "approved_protocol": approved_protocol,
            })
            predictions = outcome.get("predictions") if isinstance(outcome, dict) else None
            test_records = [
                row for row in bundle["records"] if row["partition_name"] == "test"
            ]
            expected_ids = {row["example_id"] for row in test_records}
            retrieval_run = evaluation_scope == "retrieval"
            invalid_prediction = any(
                not isinstance(item, dict)
                or item.get("partition_name", "test") != "test"
                or (
                    not isinstance(item.get("prediction"), (int, float))
                    or isinstance(item.get("prediction"), bool)
                    or not math.isfinite(item["prediction"])
                    or not -1.0 - 1e-6 <= item["prediction"] <= 1.0 + 1e-6
                    if retrieval_run
                    else not isinstance(item.get("prediction"), (str, bool))
                )
                for item in predictions
            ) if isinstance(predictions, list) else True
            if (
                not isinstance(predictions, list)
                or {item.get("example_id") for item in predictions if isinstance(item, dict)} != expected_ids
                or len(predictions) != len(expected_ids)
                or invalid_prediction
            ):
                raise ValueError("Experiment executor must return exactly one prediction for every held-out test example.")
            if local_artifact_sha256(model_path) != report["model"]["artifact_sha256"]:
                raise ValueError("Model artifact changed during inference.")
            if any(
                not isinstance(outcome.get(key, []), list)
                or any(not isinstance(value, str) for value in outcome.get(key, []))
                for key in ("warnings", "limitations")
            ):
                raise ValueError("Experiment executor returned invalid warnings or limitations.")
            prediction_by_id = {item["example_id"]: item for item in predictions}
            stored_predictions = []
            if retrieval_run:
                relevant_by_query: dict[str, set[str]] = {}
                ranked_by_query: dict[str, list[str]] = {}
                for record in test_records:
                    query_id = f"{record['framework']}:{record['indicator']}"
                    relevant_by_query.setdefault(query_id, set())
                    ranked_by_query.setdefault(query_id, []).append(record["example_id"])
                    if label_is_relevant(record["label"]):
                        relevant_by_query[query_id].add(record["example_id"])
                    score = prediction_by_id[record["example_id"]]["prediction"]
                    stored_predictions.append({
                        "example_id": record["example_id"],
                        "partition_name": "test",
                        "prediction": {"cosine_similarity": score},
                        "ground_truth": {"label": record["label"]},
                    })
                for query_id, example_ids in ranked_by_query.items():
                    example_ids.sort(
                        key=lambda example_id: (
                            -prediction_by_id[example_id]["prediction"], example_id
                        )
                    )
                results = {
                    "evaluation_type": "held_out_evidence_retrieval",
                    "retrieval_metrics": retrieval_metrics(
                        relevant_by_query, ranked_by_query, (1, 3, 5)
                    ),
                    "test_labels_used_for_fitting_or_selection": False,
                    "comparison_key": f"{report['dataset']['dataset_id']}:{report['dataset']['partition_manifest_version']}",
                    "limitations": outcome.get("limitations", []),
                }
            else:
                test_rows = []
                for record in test_records:
                    prediction = prediction_by_id[record["example_id"]]["prediction"]
                    test_rows.append({
                        "example_id": record["example_id"],
                        "framework": record["framework"],
                        "label": record["label"],
                        "prediction": prediction,
                    })
                    stored_predictions.append({
                        "example_id": record["example_id"],
                        "partition_name": "test",
                        "prediction": {"label": prediction},
                        "ground_truth": {"label": record["label"]},
                    })
                results = {
                    "test_classification": classification_metrics(test_rows),
                    "test_labels_used_for_fitting_or_selection": False,
                    "comparison_key": f"{report['dataset']['dataset_id']}:{report['dataset']['partition_manifest_version']}",
                    "limitations": outcome.get("limitations", []),
                }
            completed_at = datetime.now(timezone.utc).isoformat()
            runtime_dependencies = {}
            if retrieval_run:
                for package in ("sentence-transformers", "transformers", "torch", "numpy"):
                    try:
                        runtime_dependencies[package] = package_version(package)
                    except Exception:
                        # Record optional runtime dependencies explicitly when
                        # a custom/test executor does not require the ML stack.
                        runtime_dependencies[package] = "not-installed"
            experiment_id = self.database.persist_research_execution(
                user_id,
                institution_id,
                dataset_id=dataset_id,
                ablation_id=ablation_id,
                seed=seed,
                model_version=report["model"]["version"],
                execution_state="completed",
                preflight=report,
                warnings=outcome.get("warnings", []),
                results=results,
                predictions=stored_predictions,
                sample_counts={
                    **report["dataset"]["partition_counts"],
                    "test_evaluated": len(test_records),
                    "test_queries": report["retrieval_query_counts"]["test_queries"],
                    "eligible_test_queries": report["retrieval_query_counts"]["eligible_test_queries"],
                    **{
                        f"{framework}_test_queries": counts["test_queries"]
                        for framework, counts in report["retrieval_query_counts"]["by_framework"].items()
                    },
                    **{
                        f"{framework}_eligible_test_queries": counts["eligible_test_queries"]
                        for framework, counts in report["retrieval_query_counts"]["by_framework"].items()
                    },
                },
                evaluation_config={
                    **report["evaluation_configuration"],
                    "runtime_dependency_versions": runtime_dependencies,
                },
                started_at=started_at,
                completed_at=completed_at,
            )
            return {
                "experiment_id": experiment_id,
                "execution_state": "completed",
                "preflight": report,
                "results": results,
            }
        except Exception as error:
            LOGGER.exception("Research experiment executor failed for %s.", ablation_id)
            completed_at = datetime.now(timezone.utc).isoformat()
            experiment_id = self.database.persist_research_execution(
                user_id,
                institution_id,
                dataset_id=dataset_id,
                ablation_id=ablation_id,
                seed=seed,
                model_version=report["model"]["version"],
                execution_state="failed",
                preflight=report,
                safe_error="Experiment execution failed. Review server diagnostics; sensitive details are not exposed.",
                started_at=started_at,
                completed_at=completed_at,
            )
            return {
                "experiment_id": experiment_id,
                "execution_state": "failed",
                "preflight": report,
                "results": None,
                "error": "Experiment execution failed.",
            }

    def _load_protocol(self) -> dict[str, Any] | None:
        protocol_path = self.environment.get("WURI_RESEARCH_PROTOCOL_PATH")
        if not protocol_path:
            return None
        try:
            parsed = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _partition_executor_input(
        bundle: dict[str, Any], *, retrieval_only: bool = False
    ) -> dict[str, Any]:
        partitions = {
            "train_records": [],
            "validation_records": [],
            "test_records": [],
        }
        partition_keys = {
            "train": "train_records",
            "validation": "validation_records",
            "test": "test_records",
        }
        for record in bundle["records"]:
            if retrieval_only and record["partition_name"] != "test":
                continue
            if retrieval_only:
                partitions["test_records"].append({
                    key: record[key]
                    for key in ("example_id", "framework", "indicator", "text", "partition_name")
                })
                continue
            public_record = dict(record)
            public_record.pop("original_label", None)
            public_record.pop("source_annotation_status", None)
            public_record.pop("annotation_resolution", None)
            if record["partition_name"] == "test":
                public_record.pop("label", None)
            partitions[partition_keys[record["partition_name"]]].append(public_record)
        return {"dataset": bundle["dataset"], **partitions}


def _retrieval_query_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_query: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        if record["partition_name"] != "test":
            continue
        key = (record["framework"], record["indicator"])
        by_query.setdefault(key, []).append(record)

    by_framework: dict[str, dict[str, int]] = {}
    for (framework, _), candidates in by_query.items():
        counts = by_framework.setdefault(
            framework, {"test_queries": 0, "eligible_test_queries": 0}
        )
        counts["test_queries"] += 1
        try:
            eligible = any(label_is_relevant(record["label"]) for record in candidates)
        except ValueError:
            eligible = False
        if eligible:
            counts["eligible_test_queries"] += 1
    return {
        "test_queries": len(by_query),
        "eligible_test_queries": sum(
            counts["eligible_test_queries"] for counts in by_framework.values()
        ),
        "by_framework": by_framework,
    }

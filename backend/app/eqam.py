from dataclasses import dataclass
import math
from typing import Iterable


EQAM_WEIGHTS = {
    "semantic_relevance": 0.20,
    "model_confidence": 0.20,
    "evidence_completeness": 0.20,
    "source_reliability": 0.20,
    "evidence_strength": 0.20,
}
SCORING_METHOD_VERSION = "eqam-primary-equal-weights-v1-provisional"


def _is_finite_number(value) -> bool:
    try:
        return math.isfinite(value)
    except (TypeError, OverflowError):
        return False


def _validate_score(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not _is_finite_number(value):
        raise ValueError(f"{name} must be a finite number.")
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1.")
    return float(value)


@dataclass(frozen=True)
class EQAMResult:
    dimensions: dict[str, float]
    weights: dict[str, float]
    aes: float
    method_version: str
    validation_status: str

    def as_dict(self) -> dict:
        return {
            "dimensions": self.dimensions,
            "weights": self.weights,
            "aes": self.aes,
            "method_version": self.method_version,
            "validation_status": self.validation_status,
        }


def calculate_aes(
    dimensions: dict[str, float],
    weights: dict[str, float] | None = None,
    method_version: str = SCORING_METHOD_VERSION,
) -> EQAMResult:
    if not isinstance(dimensions, dict):
        raise ValueError("EQAM dimensions must be a named mapping.")
    if weights is not None and not isinstance(weights, dict):
        raise ValueError("EQAM weights must be a named mapping.")
    if not isinstance(method_version, str) or not method_version.strip():
        raise ValueError("EQAM method version must be a non-empty string.")
    applied_weights = dict(EQAM_WEIGHTS if weights is None else weights)
    if set(applied_weights) != set(EQAM_WEIGHTS):
        raise ValueError("All five EQAM dimensions must have weights.")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not _is_finite_number(value) or value < 0
        for value in applied_weights.values()
    ):
        raise ValueError("EQAM weights must be finite non-negative numbers.")
    if not math.isclose(sum(applied_weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("EQAM weights must sum to 1.")
    if any(not math.isclose(applied_weights[name], EQAM_WEIGHTS[name], abs_tol=1e-12) for name in EQAM_WEIGHTS):
        raise ValueError("Only the provisional equal 0.20 EQAM weights are defined.")
    if set(dimensions) != set(EQAM_WEIGHTS):
        raise ValueError("All five EQAM dimensions must be present.")
    validated = {name: _validate_score(name, dimensions[name]) for name in EQAM_WEIGHTS}
    aes = sum(validated[name] * applied_weights[name] for name in EQAM_WEIGHTS)
    return EQAMResult(
        validated, applied_weights, round(aes, 12), method_version,
        "provisional_pending_expert_validation",
    )


def evidence_completeness(found_elements: Iterable[str], required_elements: Iterable[str]) -> dict:
    if isinstance(found_elements, (str, bytes)) or isinstance(required_elements, (str, bytes)):
        raise ValueError("Evidence elements must be supplied as collections of identifiers.")
    try:
        required_values = list(required_elements)
        found_values = list(found_elements)
    except TypeError as error:
        raise ValueError("Evidence element collections must be iterable.") from error
    if any(not isinstance(item, str) or not item.strip() for item in required_values + found_values):
        raise ValueError("Evidence elements must be non-empty strings.")
    required = list(dict.fromkeys(required_values))
    found = set(found_values)
    if not required:
        return {"status": "unassessable", "score": None, "missing": [], "found": []}
    matched = [item for item in required if item in found]
    return {
        "status": "assessed",
        "score": len(matched) / len(required),
        "missing": [item for item in required if item not in found],
        "found": matched,
    }


def calibrate_threshold(cases: Iterable[tuple[float, bool]]) -> dict:
    try:
        values = list(cases)
    except TypeError as error:
        raise ValueError("Threshold calibration cases must be iterable.") from error
    if not values:
        return {"status": "threshold_calibration_required", "threshold": None, "metrics": {}}
    if any(
        not isinstance(case, (tuple, list)) or len(case) != 2
        or isinstance(case[0], bool) or not isinstance(case[0], (int, float))
        or not _is_finite_number(case[0]) or not 0 <= case[0] <= 1
        or not isinstance(case[1], bool)
        for case in values
    ):
        raise ValueError("Each calibration case must contain a finite [0,1] AES and a boolean expert label.")
    if not {label for _, label in values} >= {True, False}:
        return {"status": "threshold_calibration_required", "threshold": None, "metrics": {}}

    candidates = sorted({0.0, 1.0, *[score for score, _ in values]})
    evaluations = []
    for threshold in candidates:
        predicted = [score >= threshold for score, _ in values]
        tp = sum(p and y for p, (_, y) in zip(predicted, values))
        fp = sum(p and not y for p, (_, y) in zip(predicted, values))
        fn = sum(not p and y for p, (_, y) in zip(predicted, values))
        tn = sum(not p and not y for p, (_, y) in zip(predicted, values))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        negative_recall = tn / (tn + fp) if tn + fp else 0.0
        macro_f1 = (
            (2 * precision * recall / (precision + recall) if precision + recall else 0.0)
            + (2 * negative_recall * (tn / (tn + fn) if tn + fn else 0.0) /
               (negative_recall + (tn / (tn + fn) if tn + fn else 0.0))
               if negative_recall + (tn / (tn + fn) if tn + fn else 0.0) else 0.0)
        ) / 2
        evaluations.append({
            "threshold": threshold,
            "macro_f1": macro_f1,
            "precision": precision,
            "recall": recall,
            "balanced_accuracy": (recall + negative_recall) / 2,
        })
    return {
        "status": "threshold_selection_requires_researcher_approval",
        "threshold": None,
        "metrics": {},
        "candidate_metrics": evaluations,
        "selection_requires_researcher_approval": True,
    }

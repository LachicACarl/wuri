from dataclasses import dataclass
import math

FRAMEWORKS = ("WURI", "THE", "QS", "UI GreenMetric")
CLOSE_ALTERNATIVE_MARGIN = 5.0


@dataclass(frozen=True)
class BestFitResult:
    arrs: float
    best_fit: str
    close_alternative: str | None
    margin: float
    expert_review_required: bool
    status: str


def calculate_arrs(rrs_by_framework: dict[str, float]) -> float:
    if not isinstance(rrs_by_framework, dict):
        raise ValueError("ARRS requires a framework-to-RRS mapping.")
    if set(rrs_by_framework) != set(FRAMEWORKS):
        raise ValueError("ARRS requires one valid RRS for each framework.")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not 0 <= value <= 100 or not math.isfinite(value)
        for value in rrs_by_framework.values()
    ):
        raise ValueError("RRS values must be finite numbers between 0 and 100.")
    result = sum(rrs_by_framework.values()) / len(FRAMEWORKS)
    if not math.isfinite(result):
        raise ValueError("ARRS calculation produced a non-finite result.")
    return result


def select_best_fit(
    rrs_by_framework: dict[str, float],
    close_margin: float = 5.0,
) -> BestFitResult:
    if (
        isinstance(close_margin, bool) or not isinstance(close_margin, (int, float))
        or close_margin != CLOSE_ALTERNATIVE_MARGIN or not math.isfinite(close_margin)
    ):
        raise ValueError("The provisional dissertation close-alternative margin is fixed at 5 points.")
    arrs = calculate_arrs(rrs_by_framework)
    ranked = sorted(rrs_by_framework.items(), key=lambda item: (-item[1], item[0]))
    margin = ranked[0][1] - ranked[1][1]
    if margin == 0:
        raise ValueError("Best-Fit is tied; no unique highest framework can be selected.")
    close_alternative = margin < close_margin
    expert_review_required = close_alternative
    return BestFitResult(
        arrs=arrs,
        best_fit=ranked[0][0],
        close_alternative=ranked[1][0] if close_alternative else None,
        margin=margin,
        expert_review_required=expert_review_required,
        status="provisional_pending_expert_validation",
    )


def readiness_category(score: float) -> str:
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100 or not math.isfinite(score):
        raise ValueError("Readiness score must be finite and between 0 and 100.")
    if score < 25:
        return "Low"
    if score < 50:
        return "Developing"
    if score < 75:
        return "Moderate"
    return "High"

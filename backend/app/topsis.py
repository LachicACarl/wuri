from dataclasses import dataclass
import math


@dataclass(frozen=True)
class TOPSISResult:
    weighted_values: list[float]
    ideal_reference: list[float]
    anti_ideal_reference: list[float]
    distance_positive: float
    distance_negative: float
    closeness: float
    rrs: float
    status: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _is_finite_number(value) -> bool:
    try:
        return math.isfinite(value)
    except (TypeError, OverflowError):
        return False


def fixed_reference_topsis(values: list[float], weights: list[float]) -> TOPSISResult:
    if not isinstance(values, (list, tuple)) or not isinstance(weights, (list, tuple)):
        raise ValueError("TOPSIS values and weights must be sequences.")
    if not values or len(values) != len(weights):
        raise ValueError("TOPSIS values and weights must be non-empty and have equal length.")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1 or not _is_finite_number(value) for value in values):
        raise ValueError("TOPSIS criterion values must be finite and between 0 and 1.")
    if any(isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0 or not _is_finite_number(weight) for weight in weights):
        raise ValueError("TOPSIS weights must be finite and non-negative.")
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
        raise ValueError("TOPSIS weights must sum to 1.")
    weighted = [value * weight for value, weight in zip(values, weights)]
    ideal = list(weights)
    anti_ideal = [0.0] * len(weights)
    distance_positive = math.sqrt(sum((value - reference) ** 2 for value, reference in zip(weighted, ideal)))
    distance_negative = math.sqrt(sum(value ** 2 for value in weighted))
    denominator = distance_positive + distance_negative
    if not all(_is_finite_number(value) for value in [*weighted, distance_positive, distance_negative, denominator]):
        raise ValueError("TOPSIS distance calculation produced a non-finite result.")
    if denominator <= 0:
        raise ValueError("TOPSIS fixed references produced an undefined zero-distance result.")
    closeness = distance_negative / denominator
    if not 0 <= closeness <= 1 or not _is_finite_number(closeness):
        raise ValueError("TOPSIS closeness coefficient is invalid.")
    return TOPSISResult(
        weighted_values=weighted,
        ideal_reference=ideal,
        anti_ideal_reference=anti_ideal,
        distance_positive=distance_positive,
        distance_negative=distance_negative,
        closeness=closeness,
        rrs=100 * closeness,
        status="calculated_fixed_reference",
    )

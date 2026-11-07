from dataclasses import dataclass
import math


RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def _is_finite_number(value) -> bool:
    try:
        return math.isfinite(value)
    except (TypeError, OverflowError):
        return False


@dataclass(frozen=True)
class AHPResult:
    weights: list[float]
    geometric_means: list[float]
    lambda_max: float
    consistency_index: float
    consistency_ratio: float | None
    accepted: bool
    status: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def calculate_ahp(matrix: list[list[float]], max_consistency_ratio: float = 0.10) -> AHPResult:
    if (
        isinstance(max_consistency_ratio, bool)
        or not isinstance(max_consistency_ratio, (int, float))
        or not 0 <= max_consistency_ratio <= 0.10
        or not _is_finite_number(max_consistency_ratio)
    ):
        raise ValueError("AHP consistency limit must be finite and between 0 and 0.10.")
    if not isinstance(matrix, (list, tuple)):
        raise ValueError("AHP matrix must be a non-empty square sequence.")
    size = len(matrix)
    if size < 1 or any(not isinstance(row, (list, tuple)) or len(row) != size for row in matrix):
        raise ValueError("AHP matrix must be non-empty and square.")
    if size not in RI_TABLE:
        raise ValueError("AHP consistency is undefined for matrix sizes above 10.")
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not _is_finite_number(value) or value <= 0:
                raise ValueError("AHP comparisons must be positive finite values.")
            if row_index == column_index and not math.isclose(value, 1.0):
                raise ValueError("AHP matrix diagonal must contain 1.")
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if not math.isclose(value, 1 / matrix[column_index][row_index], rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError("AHP matrix must be reciprocal.")
    try:
        geometric_means = [math.exp(sum(math.log(value) for value in row) / size) for row in matrix]
    except (OverflowError, ValueError) as error:
        raise ValueError("AHP geometric means are outside the supported numeric range.") from error
    total = sum(geometric_means)
    if not _is_finite_number(total) or total <= 0 or any(value <= 0 for value in geometric_means):
        raise ValueError("AHP geometric means cannot be normalized safely.")
    try:
        weights = [value / total for value in geometric_means]
        weighted_sums = [sum(matrix[i][j] * weights[j] for j in range(size)) for i in range(size)]
        lambda_max = sum(weighted_sums[i] / weights[i] for i in range(size)) / size
        consistency_index = (lambda_max - size) / (size - 1) if size > 1 else 0.0
    except (OverflowError, ZeroDivisionError) as error:
        raise ValueError("AHP calculation is outside the supported numeric range.") from error
    random_index = RI_TABLE.get(size)
    consistency_ratio = None if random_index in (None, 0.0) else consistency_index / random_index
    if any(
        not _is_finite_number(value)
        for value in [*geometric_means, *weights, *weighted_sums, lambda_max, consistency_index]
    ) or (consistency_ratio is not None and not _is_finite_number(consistency_ratio)):
        raise ValueError("AHP calculation produced a non-finite result.")
    accepted = consistency_ratio is None or consistency_ratio <= max_consistency_ratio
    return AHPResult(
        weights=weights,
        geometric_means=geometric_means,
        lambda_max=lambda_max,
        consistency_index=consistency_index,
        consistency_ratio=consistency_ratio,
        accepted=accepted,
        status="accepted" if accepted else "expert_review_required",
    )

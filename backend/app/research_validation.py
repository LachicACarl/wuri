from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import math
import random
import re
from typing import Any, Iterable, Sequence


SPLIT_PROPORTIONS = {"train": 0.70, "validation": 0.15, "test": 0.15}
SPLIT_VERSION = "grouped-stratified-70-15-15-v3-approved-leakage-groups"
NEAR_DUPLICATE_JACCARD = 0.90
EQAM_DIMENSIONS = (
    "semantic_relevance",
    "model_confidence",
    "evidence_completeness",
    "source_reliability",
    "evidence_strength",
)


@dataclass(frozen=True)
class SplitResult:
    dataset_version: str
    seed: int
    split_version: str
    proportions: dict[str, float]
    assignments: dict[str, str]
    counts: dict[str, int]
    group_counts: dict[str, int]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normal_text(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold(), flags=re.UNICODE))


def _shingles(text: str, width: int = 5) -> frozenset[str]:
    tokens = _normal_text(text).split()
    if not tokens:
        return frozenset()
    if len(tokens) < width:
        return frozenset({" ".join(tokens)})
    return frozenset(" ".join(tokens[i:i + width]) for i in range(len(tokens) - width + 1))


def _connected_groups(records: Sequence[dict[str, Any]], threshold: float) -> list[list[int]]:
    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    by_document: dict[str, int] = {}
    by_leakage_group: dict[str, int] = {}
    by_exact_text: dict[str, int] = {}
    shingle_index: dict[str, list[int]] = defaultdict(list)
    record_shingles: list[frozenset[str]] = []
    for index, record in enumerate(records):
        document_id = record.get("source_document_id")
        if document_id:
            if document_id in by_document:
                union(index, by_document[document_id])
            else:
                by_document[document_id] = index
        leakage_group_id = record.get("leakage_group_id")
        if leakage_group_id:
            if leakage_group_id in by_leakage_group:
                union(index, by_leakage_group[leakage_group_id])
            else:
                by_leakage_group[leakage_group_id] = index
        text = record.get("text") or ""
        normalized = _normal_text(text)
        exact_duplicate = False
        if normalized:
            if normalized in by_exact_text:
                union(index, by_exact_text[normalized])
                exact_duplicate = True
            else:
                by_exact_text[normalized] = index
        shingles = _shingles(text)
        record_shingles.append(shingles)
        if exact_duplicate:
            continue
        candidates: set[int] = set()
        for shingle in shingles:
            candidates.update(shingle_index[shingle])
        for candidate in candidates:
            if find(index) == find(candidate):
                continue
            other = record_shingles[candidate]
            if len(shingles | other) and len(shingles & other) / len(shingles | other) >= threshold:
                union(index, candidate)
        for shingle in shingles:
            shingle_index[shingle].append(index)

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        groups[find(index)].append(index)
    return list(groups.values())


def split_evidence_dataset(
    records: Iterable[dict[str, Any]],
    dataset_version: str,
    seed: int,
    *,
    proportions: dict[str, float] | None = None,
    near_duplicate_threshold: float = NEAR_DUPLICATE_JACCARD,
) -> SplitResult:
    rows = list(records)
    requested = dict(SPLIT_PROPORTIONS if proportions is None else proportions)
    if set(requested) != set(SPLIT_PROPORTIONS):
        raise ValueError("Splits must be named train, validation, and test.")
    if any(
        not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
        for value in requested.values()
    ):
        raise ValueError("All split proportions must be positive finite values.")
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise ValueError("Dataset version must be a non-empty string.")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("Split seed must be an integer.")
    if not math.isclose(sum(requested.values()), 1.0, abs_tol=1e-9):
        raise ValueError("Split proportions must sum to 1.0.")
    if not math.isclose(requested["train"], 0.70) or not math.isclose(requested["validation"], 0.15) or not math.isclose(requested["test"], 0.15):
        raise ValueError("This protocol requires the prescribed 70:15:15 split.")
    if not rows:
        raise ValueError("Cannot split an empty dataset.")
    ids = [row.get("example_id") for row in rows]
    if (
        any(not isinstance(item, str) or not item.strip() for item in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError("Every example must have a unique, non-empty example_id.")
    rows.sort(key=lambda row: row["example_id"])
    if not 0.0 < near_duplicate_threshold <= 1.0:
        raise ValueError("Near-duplicate threshold must be within (0, 1].")
    for record in rows:
        if not record.get("framework") or not record.get("indicator"):
            raise ValueError("Every example requires a framework and indicator identifier.")
        if record.get("label") is None:
            raise ValueError(f"Example {record['example_id']} has no expert label.")
        if not isinstance(record["label"], (str, bool)) or (
            isinstance(record["label"], str) and not record["label"].strip()
        ):
            raise ValueError(f"Example {record['example_id']} has an invalid expert label.")
        if record.get("annotation_status") not in {"submitted", "expert_reviewed", "adjudicated"}:
            raise ValueError(
                f"Example {record['example_id']} is not expert-reviewed or an accepted submitted annotation."
            )
        if not (record.get("text") or record.get("source_passage_id")):
            raise ValueError(f"Example {record['example_id']} requires text or a passage reference.")

    groups = _connected_groups(rows, near_duplicate_threshold)
    if len(groups) < 3:
        raise ValueError(
            f"At least three independent document/near-duplicate groups are required; found {len(groups)}."
        )

    strata_by_group: list[Counter[tuple[str, str, str]]] = []
    all_strata: Counter[tuple[str, str, str]] = Counter()
    for group in groups:
        counts: Counter[tuple[str, str, str]] = Counter()
        for index in group:
            row = rows[index]
            stratum = (
                str(row["framework"]),
                str(row.get("major_indicator_group") or row["indicator"]),
                str(row["label"]),
            )
            counts[stratum] += 1
            all_strata[stratum] += 1
        strata_by_group.append(counts)

    rng = random.Random(seed)
    order = list(range(len(groups)))
    rng.shuffle(order)
    order.sort(key=lambda index: -len(groups[index]))
    split_names = list(SPLIT_PROPORTIONS)
    total_count = len(rows)
    target_total = {name: total_count * requested[name] for name in split_names}
    target_strata = {
        (stratum, name): count * requested[name]
        for stratum, count in all_strata.items()
        for name in split_names
    }
    totals = Counter()
    strata_totals: dict[str, Counter[tuple[str, str, str]]] = {
        name: Counter() for name in split_names
    }
    group_totals = Counter()
    assignments: dict[str, str] = {}

    for position, group_index in enumerate(order):
        remaining_groups = len(order) - position
        empty = [name for name in split_names if group_totals[name] == 0]
        candidates = empty if remaining_groups <= len(empty) else split_names
        group_size = len(groups[group_index])
        features = strata_by_group[group_index]

        def cost(candidate: str) -> float:
            result = 0.0
            for name in split_names:
                proposed = totals[name] + (group_size if name == candidate else 0)
                scale = max(1.0, target_total[name])
                result += ((proposed - target_total[name]) / scale) ** 2
                for feature in all_strata:
                    feature_count = features[feature] if name == candidate else 0
                    proposed_feature = strata_totals[name][feature] + feature_count
                    feature_scale = max(1.0, target_strata[(feature, name)])
                    result += ((proposed_feature - target_strata[(feature, name)]) / feature_scale) ** 2
            return result

        selected = min(candidates, key=lambda name: (cost(name), split_names.index(name)))
        group_totals[selected] += 1
        totals[selected] += group_size
        strata_totals[selected].update(features)
        for record_index in groups[group_index]:
            assignments[str(rows[record_index]["example_id"])] = selected

    warnings = []
    if any(group_totals[name] == 0 for name in split_names):
        raise ValueError("Unable to create non-empty train, validation, and test partitions.")
    for stratum, count in all_strata.items():
        represented = sum(strata_totals[name][stratum] > 0 for name in split_names)
        if represented < 3:
            warnings.append(
                f"Stratum {stratum[0]}/{stratum[1]}/{stratum[2]} has {count} examples in "
                f"{represented} partition(s); full stratification is not possible."
            )
    for name in split_names:
        observed = totals[name] / total_count
        if abs(observed - requested[name]) > 0.02:
            warnings.append(
                f"Document/near-duplicate grouping constrained {name} to {totals[name]}/{total_count} "
                f"({observed:.3f}) rather than its requested {requested[name]:.3f} share."
            )
    return SplitResult(
        dataset_version=dataset_version,
        seed=seed,
        split_version=SPLIT_VERSION,
        proportions=requested,
        assignments=assignments,
        counts=dict(totals),
        group_counts=dict(group_totals),
        warnings=tuple(warnings),
    )


def _per_class_metrics(labels: Sequence[str], predictions: Sequence[str], classes: Sequence[str]) -> dict[str, Any]:
    output = {}
    for label in classes:
        tp = sum(actual == label and predicted == label for actual, predicted in zip(labels, predictions))
        fp = sum(actual != label and predicted == label for actual, predicted in zip(labels, predictions))
        fn = sum(actual == label and predicted != label for actual, predicted in zip(labels, predictions))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        output[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return output


def classification_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    data = list(rows)
    if any(row.get("label") is None or row.get("prediction") is None for row in data):
        raise ValueError("Classification metrics require a label and prediction for every row.")

    def summarize(selected: list[dict[str, Any]]) -> dict[str, Any]:
        if not selected:
            return {"sample_count": 0, "accuracy": None, "macro_precision": None,
                    "macro_recall": None, "macro_f1": None, "per_class": {}}
        labels = [str(row["label"]) for row in selected]
        predictions = [str(row["prediction"]) for row in selected]
        classes = sorted(set(labels) | set(predictions))
        per_class = _per_class_metrics(labels, predictions, classes)
        return {
            "sample_count": len(selected),
            "accuracy": sum(a == p for a, p in zip(labels, predictions)) / len(selected),
            "macro_precision": sum(item["precision"] for item in per_class.values()) / len(classes),
            "macro_recall": sum(item["recall"] for item in per_class.values()) / len(classes),
            "macro_f1": sum(item["f1"] for item in per_class.values()) / len(classes),
            "per_class": per_class,
        }

    by_framework = {
        framework: summarize([row for row in data if row.get("framework") == framework])
        for framework in sorted({str(row.get("framework")) for row in data})
    }
    return {"aggregate": summarize(data), "by_framework": by_framework}


def retrieval_metrics(
    relevant_by_query: dict[str, set[str]],
    ranked_by_query: dict[str, Sequence[str]],
    k_values: Sequence[int] = (1, 3, 5),
) -> dict[str, Any]:
    if any(k < 1 for k in k_values):
        raise ValueError("Retrieval cutoffs must be positive.")
    if set(relevant_by_query) != set(ranked_by_query):
        raise ValueError("Every query must have both a relevance set and a ranking.")

    def score_queries(query_ids: Sequence[str]) -> dict[str, Any]:
        output = {"query_count": len(query_ids)}
        for k in k_values:
            precisions, recalls = [], []
            for query_id in query_ids:
                relevant = relevant_by_query[query_id]
                if not relevant:
                    continue
                ranked = ranked_by_query[query_id][:k]
                hits = len(set(ranked) & relevant)
                precisions.append(hits / k)
                recalls.append(hits / len(relevant))
            output[f"precision@{k}"] = sum(precisions) / len(precisions) if precisions else None
            output[f"recall@{k}"] = sum(recalls) / len(recalls) if recalls else None
            output[f"evaluated_queries@{k}"] = len(precisions)
        return output

    aggregate = score_queries(sorted(relevant_by_query))
    frameworks = sorted({query.split(":", 1)[0] for query in relevant_by_query})
    return {
        "aggregate": aggregate,
        "by_framework": {
            framework: score_queries(
                [query for query in relevant_by_query if query.split(":", 1)[0] == framework]
            )
            for framework in frameworks
        },
        "relevance_convention": "A retrieved indicator is relevant exactly when it is in the expert-labeled relevant set.",
    }


def _rank(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average_rank = (cursor + 1 + end) / 2
        for index in order[cursor:end]:
            ranks[index] = average_rank
        cursor = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) < 2:
        return None
    left_mean, right_mean = sum(left) / len(left), sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_sum = sum((x - left_mean) ** 2 for x in left)
    right_sum = sum((y - right_mean) ** 2 for y in right)
    denominator = math.sqrt(left_sum * right_sum)
    return numerator / denominator if denominator else None


def agreement_metrics(system_scores: Sequence[float], reference_scores: Sequence[float]) -> dict[str, Any]:
    if len(system_scores) != len(reference_scores):
        raise ValueError("System and reference score arrays must have equal length.")
    if any(not math.isfinite(value) for value in [*system_scores, *reference_scores]):
        raise ValueError("Scores must be finite.")
    count = len(system_scores)
    if not count:
        return {"sample_count": 0, "mae": None, "rmse": None, "spearman_rho": None, "icc_2_1": None}
    differences = [system - reference for system, reference in zip(system_scores, reference_scores)]
    rho = _pearson(_rank(system_scores), _rank(reference_scores)) if count >= 2 else None
    icc = None
    if count >= 2:
        rows = list(zip(system_scores, reference_scores))
        grand = sum(sum(row) for row in rows) / (2 * count)
        row_means = [sum(row) / 2 for row in rows]
        column_means = [sum(row[column] for row in rows) / count for column in range(2)]
        ms_rows = 2 * sum((mean - grand) ** 2 for mean in row_means) / (count - 1)
        ms_columns = count * sum((mean - grand) ** 2 for mean in column_means)
        ms_error = sum(
            (rows[i][j] - row_means[i] - column_means[j] + grand) ** 2
            for i in range(count) for j in range(2)
        ) / (count - 1)
        denominator = ms_rows + ms_error + 2 * (ms_columns - ms_error) / count
        icc = (ms_rows - ms_error) / denominator if denominator else None
    return {
        "sample_count": count,
        "mae": sum(abs(value) for value in differences) / count,
        "rmse": math.sqrt(sum(value * value for value in differences) / count),
        "spearman_rho": rho,
        "icc_2_1": icc,
        "agreement_note": "ICC(2,1) assumes complete paired ratings and is not interpreted as validated without a suitable expert-rating design.",
    }


def cohen_kappa(actual: Sequence[str], predicted: Sequence[str]) -> dict[str, Any]:
    if len(actual) != len(predicted):
        raise ValueError("Categorical rating arrays must have equal length.")
    if not actual:
        return {"sample_count": 0, "kappa": None}
    classes = set(actual) | set(predicted)
    observed = sum(left == right for left, right in zip(actual, predicted)) / len(actual)
    expected = sum(
        (actual.count(label) / len(actual)) * (predicted.count(label) / len(predicted))
        for label in classes
    )
    return {
        "sample_count": len(actual),
        "exact_agreement": observed,
        "kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
    }


def fleiss_kappa(ratings_by_case: Sequence[Sequence[str]]) -> dict[str, Any]:
    if not ratings_by_case:
        return {
            "status": "undefined_no_complete_cases",
            "sample_count": 0,
            "raters_per_case": None,
            "categories": [],
            "observed_agreement": None,
            "expected_agreement": None,
            "kappa": None,
        }
    rater_count = len(ratings_by_case[0])
    if rater_count < 2 or any(len(ratings) != rater_count for ratings in ratings_by_case):
        raise ValueError("Fleiss' kappa requires the same two or more raters for every case.")
    if any(not isinstance(label, str) or not label.strip()
           for ratings in ratings_by_case for label in ratings):
        raise ValueError("Fleiss' kappa ratings must be non-empty categorical strings.")

    normalized_ratings = [
        [label.strip() for label in ratings]
        for ratings in ratings_by_case
    ]
    categories = sorted({label for ratings in normalized_ratings for label in ratings})
    category_proportions = {
        category: sum(ratings.count(category) for ratings in normalized_ratings)
        / (len(normalized_ratings) * rater_count)
        for category in categories
    }
    per_case_agreement = []
    for ratings in normalized_ratings:
        counts = [ratings.count(category) for category in categories]
        per_case_agreement.append(
            (sum(count * count for count in counts) - rater_count)
            / (rater_count * (rater_count - 1))
        )
    observed = sum(per_case_agreement) / len(normalized_ratings)
    expected = sum(proportion * proportion for proportion in category_proportions.values())
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    return {
        "status": "defined" if kappa is not None else "undefined_degenerate_marginals",
        "sample_count": len(normalized_ratings),
        "raters_per_case": rater_count,
        "categories": categories,
        "observed_agreement": observed,
        "expected_agreement": expected,
        "kappa": kappa,
    }


def icc_2_1(ratings_by_case: Sequence[Sequence[float]]) -> float | None:
    """Return two-way random-effects, absolute-agreement, single-measure ICC."""
    if not ratings_by_case:
        return None
    rater_count = len(ratings_by_case[0])
    if (
        len(ratings_by_case) < 2
        or rater_count < 2
        or any(len(ratings) != rater_count for ratings in ratings_by_case)
    ):
        raise ValueError("ICC(2,1) requires at least two complete cases and two raters.")
    if any(
        isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score)
        for ratings in ratings_by_case for score in ratings
    ):
        raise ValueError("ICC ratings must be finite numeric values.")

    case_count = len(ratings_by_case)
    grand_mean = sum(sum(row) for row in ratings_by_case) / (case_count * rater_count)
    case_means = [sum(row) / rater_count for row in ratings_by_case]
    rater_means = [
        sum(row[index] for row in ratings_by_case) / case_count
        for index in range(rater_count)
    ]
    mean_square_cases = (
        rater_count * sum((mean - grand_mean) ** 2 for mean in case_means)
        / (case_count - 1)
    )
    mean_square_raters = (
        case_count * sum((mean - grand_mean) ** 2 for mean in rater_means)
        / (rater_count - 1)
    )
    residual_sum = sum(
        (
            ratings_by_case[case][rater] - case_means[case] - rater_means[rater]
            + grand_mean
        ) ** 2
        for case in range(case_count)
        for rater in range(rater_count)
    )
    mean_square_error = residual_sum / ((case_count - 1) * (rater_count - 1))
    denominator = (
        mean_square_cases
        + (rater_count - 1) * mean_square_error
        + rater_count * (mean_square_raters - mean_square_error) / case_count
    )
    if denominator == 0:
        return None
    return (mean_square_cases - mean_square_error) / denominator


def best_fit_agreement(
    system_by_case: dict[str, str],
    expert_by_case: dict[str, str],
    system_margin_by_case: dict[str, float],
    close_margin: float = 5.0,
) -> dict[str, Any]:
    if not math.isfinite(close_margin) or close_margin <= 0:
        raise ValueError("Close-alternative margin must be positive and finite.")
    common = sorted(set(system_by_case) & set(expert_by_case) & set(system_margin_by_case))
    kappa = cohen_kappa(
        [expert_by_case[case] for case in common],
        [system_by_case[case] for case in common],
    )
    close_cases = [
        case for case in common
        if abs(system_margin_by_case[case]) < close_margin
    ]
    return {
        "sample_count": len(common),
        "exact_agreement_rate": kappa["exact_agreement"],
        "cohen_kappa": kappa["kappa"],
        "close_margin_cutoff": close_margin,
        "system_cases_below_close_margin": len(close_cases),
        "system_close_margin_case_ids": close_cases,
        "agreement_for_close_margin_cases": (
            sum(system_by_case[case] == expert_by_case[case] for case in close_cases) / len(close_cases)
            if close_cases else None
        ),
    }


def audit_explanation_traceability(
    explanations: Sequence[dict[str, Any]],
    *,
    available_passage_ids: set[str],
    expected_contributions: dict[str, float],
    reported_score: float,
    expected_score: float,
    tolerance: float = 1e-8,
) -> dict[str, Any]:
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Numerical tolerance must be finite and non-negative.")
    if not math.isfinite(reported_score) or not math.isfinite(expected_score):
        raise ValueError("Reported and expected scores must be finite.")
    if any(not math.isfinite(value) for value in expected_contributions.values()):
        raise ValueError("Expected contributions must be finite.")
    seen = set()
    traceable = 0
    consistent = 0
    details = []
    for item in explanations:
        criterion = item.get("criterion_id")
        references = item.get("source_passage_ids")
        contribution = item.get("contribution")
        valid_references = (
            isinstance(references, list) and bool(references)
            and all(reference in available_passage_ids for reference in references)
        )
        expected = expected_contributions.get(criterion)
        numeric_match = (
            isinstance(contribution, (int, float)) and math.isfinite(contribution)
            and expected is not None and math.isclose(contribution, expected, rel_tol=0, abs_tol=tolerance)
        )
        details.append({
            "criterion_id": criterion,
            "evidence_traceable": valid_references,
            "contribution_matches_calculation": numeric_match,
        })
        if valid_references:
            traceable += 1
        if numeric_match:
            consistent += 1
        if criterion:
            seen.add(criterion)
    score_consistent = math.isclose(reported_score, expected_score, rel_tol=0, abs_tol=tolerance)
    duplicate_criteria = len(seen) != len(explanations)
    return {
        "explanation_count": len(explanations),
        "expected_contribution_count": len(expected_contributions),
        "missing_criteria": sorted(set(expected_contributions) - seen),
        "duplicate_criteria": duplicate_criteria,
        "traceable_explanation_count": traceable,
        "numerically_consistent_contribution_count": consistent,
        "reported_score_matches_calculation": score_consistent,
        "details": details,
        "status": (
            "passed_fidelity_checks"
            if len(seen) == len(expected_contributions) and not duplicate_criteria
            and traceable == len(explanations)
            and consistent == len(explanations) and score_consistent
            else "failed_fidelity_checks"
        ),
        "note": "Fidelity checks do not measure clarity, usefulness, interpretability, or user confidence.",
    }


def threshold_from_validation(
    scores: Sequence[float], acceptable_labels: Sequence[bool], dataset_version: str
) -> dict[str, Any]:
    if len(scores) != len(acceptable_labels):
        raise ValueError("Validation scores and labels must have equal length.")
    if any(not isinstance(label, bool) for label in acceptable_labels):
        raise ValueError("Expert acceptable labels must be boolean.")
    if not scores or set(acceptable_labels) != {False, True}:
        return {"status": "blocked_missing_data", "threshold": None, "dataset_version": dataset_version}
    if any(not math.isfinite(score) or score < 0 or score > 1 for score in scores):
        raise ValueError("Threshold scores must be finite and within [0, 1].")
    candidates = sorted({0.0, 1.0, *scores})
    evaluations = []
    for threshold in candidates:
        predictions = [score >= threshold for score in scores]
        metrics = classification_metrics(
            [{"label": str(label), "prediction": str(prediction)} for label, prediction in zip(acceptable_labels, predictions)]
        )["aggregate"]
        evaluations.append({"threshold": threshold, **metrics})
    selected = max(evaluations, key=lambda row: (
        row["macro_f1"], row["macro_recall"], row["macro_precision"], -row["threshold"]
    ))
    return {
        "status": "locked_from_validation",
        "threshold": selected["threshold"],
        "selection_metric": "macro_f1_then_macro_recall",
        "validation_dataset_version": dataset_version,
        "metrics": selected,
        "test_labels_used": False,
        "threshold_version": hashlib.sha256(
            f"{dataset_version}:{selected['threshold']:.12g}".encode()
        ).hexdigest(),
    }


def descriptive_statistics(values: Sequence[float]) -> dict[str, Any]:
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Descriptive statistics require finite values.")
    if not values:
        return {"sample_count": 0, "mean": None, "standard_deviation": None, "median": None}
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    median = ordered[midpoint] if len(ordered) % 2 else (ordered[midpoint - 1] + ordered[midpoint]) / 2
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
    return {
        "sample_count": len(values),
        "mean": mean,
        "standard_deviation": math.sqrt(variance),
        "median": median,
    }


def eqam_expert_agreement(
    system_by_case: dict[str, dict[str, float]],
    expert_by_case: dict[str, dict[str, float]],
) -> dict[str, Any]:
    common_cases = sorted(set(system_by_case) & set(expert_by_case))
    dimensions = {}
    for dimension in EQAM_DIMENSIONS:
        paired = [
            (system_by_case[case].get(dimension), expert_by_case[case].get(dimension))
            for case in common_cases
        ]
        paired = [(system, expert) for system, expert in paired if system is not None and expert is not None]
        if any(not math.isfinite(value) or not 0 <= value <= 1 for pair in paired for value in pair):
            raise ValueError(f"{dimension} ratings must be finite values within [0, 1].")
        system_values = [pair[0] for pair in paired]
        expert_values = [pair[1] for pair in paired]
        dimensions[dimension] = {
            "system": descriptive_statistics(system_values),
            "expert": descriptive_statistics(expert_values),
            "agreement": agreement_metrics(system_values, expert_values),
            "validation_claim_allowed": False,
        }
    return {
        "paired_case_count": len(common_cases),
        "dimensions": dimensions,
        "interpretation": "Agreement statistics are descriptive until the expert-rating design and protocol are verified.",
    }


def xai_rating_summary(ratings: Iterable[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for rating in ratings:
        dimension = str(rating.get("dimension", ""))
        score = rating.get("score")
        if not dimension.startswith("xai:"):
            continue
        if not isinstance(score, (int, float)) or not math.isfinite(score):
            raise ValueError("XAI ratings must be finite numeric values.")
        grouped[dimension.removeprefix("xai:")].append(float(score))
    return {
        "instrument_version": None,
        "ratings_by_dimension": {
            dimension: descriptive_statistics(scores)
            for dimension, scores in sorted(grouped.items())
        },
        "empirical_quality_claim_allowed": False,
    }


def eqam_rss_association(
    rows: Iterable[dict[str, Any]],
    *,
    minimum_sample_size: int | None,
    significance_alpha: float,
) -> dict[str, Any]:
    from scipy import stats
    import numpy as np

    if minimum_sample_size is None or minimum_sample_size < len(EQAM_DIMENSIONS) + 2:
        return {
            "status": "blocked_missing_data",
            "reason": "Supply a preregistered minimum sample size from an a-priori power analysis.",
        }
    if not 0 < significance_alpha < 1:
        raise ValueError("Significance alpha must be within (0, 1).")
    source = list(rows)
    complete = []
    for row in source:
        values = [row.get(dimension) for dimension in EQAM_DIMENSIONS] + [row.get("rrs")]
        if all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
            complete.append(row)
    if len(complete) < minimum_sample_size:
        return {
            "status": "blocked_missing_data",
            "sample_count": len(complete),
            "required_minimum_sample_size": minimum_sample_size,
            "complete_case_rows_dropped": len(source) - len(complete),
        }
    identifiers = [row.get("case_id") for row in complete]
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError("Each complete EQAM/RRS row must have a unique case_id.")

    matrix = np.asarray([[float(row[key]) for key in EQAM_DIMENSIONS] for row in complete], dtype=float)
    outcome = np.asarray([float(row["rrs"]) for row in complete], dtype=float)
    if np.any((matrix < 0) | (matrix > 1)) or np.any((outcome < 0) | (outcome > 100)):
        raise ValueError("EQAM values must be in [0, 1] and RRS values in [0, 100].")
    if np.any(np.std(matrix, axis=0, ddof=1) == 0) or np.std(outcome, ddof=1) == 0:
        return {
            "status": "blocked_missing_data",
            "sample_count": len(complete),
            "reason": "At least one predictor or the outcome has no variance.",
        }

    standardized = (matrix - matrix.mean(axis=0)) / matrix.std(axis=0, ddof=1)
    standardized_outcome = (outcome - outcome.mean()) / outcome.std(ddof=1)
    design = np.column_stack([np.ones(len(complete)), standardized])
    rank = int(np.linalg.matrix_rank(design))
    degrees_freedom = len(complete) - rank
    if rank < design.shape[1] or degrees_freedom < 1:
        return {
            "status": "blocked_missing_data",
            "sample_count": len(complete),
            "reason": "The predictor design matrix is rank-deficient or has no residual degrees of freedom.",
        }
    coefficients = np.linalg.lstsq(design, standardized_outcome, rcond=None)[0]
    residuals = standardized_outcome - design @ coefficients
    residual_sum_squares = float(residuals @ residuals)
    total_sum_squares = float(((standardized_outcome - standardized_outcome.mean()) ** 2).sum())
    r_squared = 1 - residual_sum_squares / total_sum_squares
    adjusted_r_squared = 1 - (1 - r_squared) * (len(complete) - 1) / degrees_freedom
    covariance = (residual_sum_squares / degrees_freedom) * np.linalg.inv(design.T @ design)
    standard_errors = np.sqrt(np.diag(covariance))
    t_statistics = coefficients / standard_errors
    critical = float(stats.t.ppf(1 - significance_alpha / 2, degrees_freedom))
    coefficient_output = {}
    for index, dimension in enumerate(EQAM_DIMENSIONS, start=1):
        p_value = float(2 * stats.t.sf(abs(t_statistics[index]), degrees_freedom))
        coefficient_output[dimension] = {
            "standardized_coefficient": float(coefficients[index]),
            "p_value": p_value,
            "confidence_interval": [
                float(coefficients[index] - critical * standard_errors[index]),
                float(coefficients[index] + critical * standard_errors[index]),
            ],
            "significant_at_supplied_alpha": p_value < significance_alpha,
        }

    vif = {}
    for column, dimension in enumerate(EQAM_DIMENSIONS):
        target = standardized[:, column]
        other = np.delete(standardized, column, axis=1)
        auxiliary = np.column_stack([np.ones(len(complete)), other])
        fitted = auxiliary @ np.linalg.lstsq(auxiliary, target, rcond=None)[0]
        denominator = float(((target - target.mean()) ** 2).sum())
        auxiliary_r_squared = 1 - float(((target - fitted) ** 2).sum()) / denominator
        vif[dimension] = 1 / (1 - auxiliary_r_squared) if auxiliary_r_squared < 1 else None

    association = {}
    raw_p_values = []
    for dimension, column in zip(EQAM_DIMENSIONS, matrix.T):
        rho, p_value = stats.spearmanr(column, outcome)
        raw_p_values.append(float(p_value))
        association[dimension] = {"spearman_rho": float(rho), "unadjusted_p_value": float(p_value)}
    ordered_p = sorted(enumerate(raw_p_values), key=lambda pair: pair[1])
    previous = 0.0
    adjusted = [0.0] * len(raw_p_values)
    for rank_index, (original_index, p_value) in enumerate(ordered_p):
        value = min(1.0, (len(raw_p_values) - rank_index) * p_value)
        adjusted[original_index] = max(previous, value)
        previous = adjusted[original_index]
    for dimension, p_value in zip(EQAM_DIMENSIONS, adjusted):
        association[dimension]["holm_adjusted_p_value"] = p_value

    shapiro_p = float(stats.shapiro(residuals).pvalue) if 3 <= len(complete) <= 5000 else None
    squared_residuals = residuals ** 2
    bp_design = np.column_stack([np.ones(len(complete)), standardized])
    bp_fitted = bp_design @ np.linalg.lstsq(bp_design, squared_residuals, rcond=None)[0]
    bp_total = float(((squared_residuals - squared_residuals.mean()) ** 2).sum())
    bp_r_squared = 1 - float(((squared_residuals - bp_fitted) ** 2).sum()) / bp_total if bp_total else 0.0
    bp_lm = len(complete) * bp_r_squared
    bp_p = float(stats.chi2.sf(bp_lm, len(EQAM_DIMENSIONS)))
    return {
        "status": "completed_with_limitations",
        "sample_count": len(complete),
        "complete_case_rows_dropped": len(source) - len(complete),
        "missing_data_policy": "Complete-case analysis; rows missing any dimension, case_id-independent value, or RRS are excluded.",
        "required_minimum_sample_size": minimum_sample_size,
        "minimum_sample_size_source": "caller-supplied a-priori power analysis",
        "spearman_associations": association,
        "regression": {
            "outcome": "framework-specific RRS",
            "standardized_coefficients": coefficient_output,
            "adjusted_r_squared": float(adjusted_r_squared),
            "vif": vif,
            "residual_shapiro_p": shapiro_p,
            "breusch_pagan_lm": float(bp_lm),
            "breusch_pagan_p": bp_p,
            "significance_alpha": significance_alpha,
        },
        "interpretation": (
            "EQAM dimensions contribute mathematically to AES and the readiness pipeline. "
            "These associations are descriptive and do not establish independent causal effects."
        ),
        "multiple_comparison_adjustment": "Holm adjustment across five Spearman tests.",
        "limitations": [
            "The exact dissertation analysis protocol and minimum sample size require Chapter 3 verification.",
            "Observational mathematical coupling prevents causal interpretation.",
            "The report does not establish model superiority or practical importance.",
        ],
    }


def paired_score_comparison(
    first: Sequence[float],
    second: Sequence[float],
    *,
    significance_alpha: float,
    seed: int,
) -> dict[str, Any]:
    if len(first) != len(second):
        raise ValueError("Paired score arrays must have equal length.")
    if not 0 < significance_alpha < 1:
        raise ValueError("Significance alpha must be within (0, 1).")
    if any(not math.isfinite(value) for value in [*first, *second]):
        raise ValueError("Paired score arrays must contain finite values.")
    differences = [left - right for left, right in zip(first, second)]
    if len(differences) < 3:
        return {
            "status": "blocked_missing_data",
            "sample_count": len(differences),
            "reason": "At least three paired observations are required for the implemented inferential test.",
        }
    if all(value == 0 for value in differences):
        return {
            "status": "completed",
            "paired": True,
            "method": "identical_paired_observations",
            "sample_count": len(differences),
            "mean_paired_difference": 0.0,
            "mean_difference_bootstrap_95_ci": [0.0, 0.0],
            "effect_size": 0.0,
            "p_value": 1.0,
            "significance_alpha": significance_alpha,
            "statistically_significant": False,
            "seed": seed,
            "limitations": ["No observed differences; no inferential superiority claim is warranted."],
        }

    from scipy import stats

    normality = stats.shapiro(differences)
    alpha_for_normality = 0.05
    if normality.pvalue >= alpha_for_normality:
        test = stats.ttest_rel(first, second)
        method = "paired_t_test"
        sd = math.sqrt(sum((value - sum(differences) / len(differences)) ** 2 for value in differences) / (len(differences) - 1))
        effect_size = (sum(differences) / len(differences)) / sd if sd else None
    else:
        test = stats.wilcoxon(first, second, alternative="two-sided", zero_method="wilcox")
        method = "wilcoxon_signed_rank"
        nonzero_differences = [value for value in differences if value != 0]
        signed_ranks = stats.rankdata([abs(value) for value in nonzero_differences])
        positive_rank_sum = sum(
            rank for rank, difference in zip(signed_ranks, nonzero_differences) if difference > 0
        )
        negative_rank_sum = sum(
            rank for rank, difference in zip(signed_ranks, nonzero_differences) if difference < 0
        )
        rank_total = positive_rank_sum + negative_rank_sum
        effect_size = (positive_rank_sum - negative_rank_sum) / rank_total if rank_total else None
    rng = random.Random(seed)
    bootstrap_means = []
    for _ in range(2_000):
        sample = [differences[rng.randrange(len(differences))] for _ in differences]
        bootstrap_means.append(sum(sample) / len(sample))
    bootstrap_means.sort()
    lower = bootstrap_means[int(0.025 * len(bootstrap_means))]
    upper = bootstrap_means[min(len(bootstrap_means) - 1, int(0.975 * len(bootstrap_means)))]
    return {
        "status": "completed",
        "paired": True,
        "method": method,
        "sample_count": len(differences),
        "mean_paired_difference": sum(differences) / len(differences),
        "mean_difference_bootstrap_95_ci": [lower, upper],
        "effect_size": effect_size,
        "effect_size_definition": "Cohen dz for paired t-test; rank-biserial correlation for Wilcoxon.",
        "normality_shapiro_p": float(normality.pvalue),
        "normality_alpha": alpha_for_normality,
        "p_value": float(test.pvalue),
        "significance_alpha": significance_alpha,
        "statistically_significant": bool(test.pvalue < significance_alpha),
        "seed": seed,
        "limitations": ["The authoritative dissertation significance criterion was not available for verification."],
    }


def run_robustness_scenarios(
    framework_inputs: dict[str, dict[str, Sequence[float]]],
    scenarios: Sequence[dict[str, dict[str, Sequence[float]]]],
    *,
    variable_weight_indices: dict[str, set[int]] | None = None,
    variable_criterion_indices: dict[str, set[int]] | None = None,
) -> dict[str, Any]:
    from .topsis import fixed_reference_topsis
    from .readiness import FRAMEWORKS, select_best_fit

    if not isinstance(scenarios, (list, tuple)):
        raise ValueError("Robustness scenarios must be a sequence.")
    allowed_weights = variable_weight_indices or {}
    allowed_criteria = variable_criterion_indices or {}

    def calculate(inputs: dict[str, dict[str, Sequence[float]]]) -> dict[str, float]:
        if not isinstance(inputs, dict) or set(inputs) != set(FRAMEWORKS):
            raise ValueError("Robustness inputs must contain exactly one vector set for each framework.")
        scores = {}
        for framework, values in inputs.items():
            if not isinstance(values, dict) or set(values) != {"weights", "criteria"}:
                raise ValueError(f"{framework} inputs must contain weights and criteria vectors.")
            if any(not isinstance(values[key], (list, tuple)) for key in ("weights", "criteria")):
                raise ValueError(f"{framework} weights and criteria must be sequences.")
            weights, criteria = list(values["weights"]), list(values["criteria"])
            if len(weights) != len(criteria):
                raise ValueError(f"{framework} weight and criterion vector lengths differ.")
            scores[framework] = fixed_reference_topsis(criteria, weights).rrs
        return scores

    baseline_scores = calculate(framework_inputs)
    baseline_best = select_best_fit(baseline_scores)
    scenario_scores = []
    for scenario in scenarios:
        if not isinstance(scenario, dict) or set(scenario) != set(framework_inputs):
            raise ValueError("Every robustness scenario must include the same frameworks as baseline.")
        for framework, base in framework_inputs.items():
            proposed = scenario[framework]
            if not isinstance(proposed, dict) or set(proposed) != {"weights", "criteria"}:
                raise ValueError(f"{framework} scenario must contain weights and criteria vectors.")
            for key in ("weights", "criteria"):
                if not isinstance(proposed[key], (list, tuple)):
                    raise ValueError(f"{framework} scenario {key} must be a sequence.")
                if len(base[key]) != len(proposed[key]):
                    raise ValueError("Robustness scenario vector length differs from baseline.")
            if any(
                index not in allowed_weights.get(framework, set())
                and proposed["weights"][index] != base["weights"][index]
                for index in range(len(base["weights"]))
            ):
                raise ValueError(f"Scenario changed a fixed, non-permitted {framework} weight.")
            if any(
                index not in allowed_criteria.get(framework, set())
                and proposed["criteria"][index] != base["criteria"][index]
                for index in range(len(base["criteria"]))
            ):
                raise ValueError(f"Scenario changed a criterion that is not permitted to vary for {framework}.")
        scores = calculate(scenario)
        best_fit = select_best_fit(scores)
        scenario_scores.append({
            "framework_scores": scores,
            "rrs_change_by_framework": {
                framework: scores[framework] - baseline_scores[framework]
                for framework in baseline_scores
            },
            "arrs": best_fit.arrs,
            "arrs_change": best_fit.arrs - baseline_best.arrs,
            "best_fit": best_fit.best_fit,
            "margin": best_fit.margin,
            "margin_change": best_fit.margin - baseline_best.margin,
            "close_alternative": best_fit.close_alternative,
        })
    best_fit_counts = Counter(item["best_fit"] for item in scenario_scores)
    return {
        "baseline": {
            "framework_scores": baseline_scores,
            "arrs": baseline_best.arrs,
            "best_fit": baseline_best.best_fit,
            "margin": baseline_best.margin,
            "close_alternative": baseline_best.close_alternative,
        },
        "scenario_count": len(scenario_scores),
        "scenarios": scenario_scores,
        "best_fit_stability": (
            sum(item["best_fit"] == baseline_best.best_fit for item in scenario_scores) / len(scenario_scores)
            if scenario_scores else None
        ),
        "best_fit_frequency": dict(best_fit_counts),
        "close_alternative_frequency": (
            sum(item["close_alternative"] is not None for item in scenario_scores) / len(scenario_scores)
            if scenario_scores else None
        ),
        "empirical_claim_allowed": False,
        "note": "Results describe only the supplied perturbation scenarios; fixed-reference TOPSIS uses no cross-institution ideal point.",
    }


ABLATIONS = {
    "A0": {
        "name": "Conventional SBERT + AHP-TOPSIS baseline",
        "components": {"sentence_encoder": "pretrained_sbert", "eqam": False,
                       "framework_constrained_ahp": False, "fixed_reference_topsis": False, "xai": False},
        "requirements": ("genuine_expert_labeled_dataset", "baseline_model_version",
                         "approved_conventional_weights", "methodology_chapter3_verified"),
    },
    "A1": {
        "name": "Enhanced SBERT + conventional AHP-TOPSIS",
        "components": {"sentence_encoder": "domain_adapted_sbert", "eqam": False,
                       "framework_constrained_ahp": False, "fixed_reference_topsis": False, "xai": False},
        "requirements": ("genuine_expert_labeled_dataset", "enhanced_model_artifact",
                         "approved_conventional_weights", "methodology_chapter3_verified"),
    },
    "A2": {
        "name": "Enhanced SBERT + EQAM + conventional AHP-TOPSIS",
        "components": {"sentence_encoder": "domain_adapted_sbert", "eqam": True,
                       "framework_constrained_ahp": False, "fixed_reference_topsis": False, "xai": False},
        "requirements": ("genuine_expert_labeled_dataset", "enhanced_model_artifact",
                         "expert_eqam_ratings", "locked_validation_threshold",
                         "approved_conventional_weights", "methodology_chapter3_verified"),
    },
    "A3": {
        "name": "A2 + framework-constrained AHP + fixed-reference TOPSIS",
        "components": {"sentence_encoder": "domain_adapted_sbert", "eqam": True,
                       "framework_constrained_ahp": True, "fixed_reference_topsis": True, "xai": False},
        "requirements": ("genuine_expert_labeled_dataset", "enhanced_model_artifact",
                         "expert_eqam_ratings", "locked_validation_threshold",
                         "approved_criterion_aggregation", "verified_framework_criteria_and_weights",
                         "expert_reference_readiness_scores", "methodology_chapter3_verified"),
    },
    "A4": {
        "name": "A3 + evaluated explainability",
        "components": {"sentence_encoder": "domain_adapted_sbert", "eqam": True,
                       "framework_constrained_ahp": True, "fixed_reference_topsis": True, "xai": True},
        "requirements": ("genuine_expert_labeled_dataset", "enhanced_model_artifact",
                         "expert_eqam_ratings", "locked_validation_threshold",
                         "approved_criterion_aggregation", "verified_framework_criteria_and_weights",
                         "expert_reference_readiness_scores", "xai_evaluation_instrument_and_ratings",
                         "methodology_chapter3_verified"),
    },
}


def ablation_statuses(
    available: set[str], implemented_runners: set[str] | None = None
) -> list[dict[str, Any]]:
    runners = implemented_runners or set()
    results = []
    for ablation_id, definition in ABLATIONS.items():
        missing = [requirement for requirement in definition["requirements"] if requirement not in available]
        if not missing and ablation_id not in runners:
            missing.append("implemented_experiment_runner")
        results.append({
            "id": ablation_id,
            "name": definition["name"],
            "components": definition["components"],
            "status": (
                "blocked_missing_data"
                if any(item != "implemented_experiment_runner" for item in missing)
                else "not_implemented" if missing else "ready_to_run"
            ),
            "missing_prerequisites": missing,
        })
    return results

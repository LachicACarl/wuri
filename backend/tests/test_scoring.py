import unittest

from app.ahp import calculate_ahp
from app.eqam import calculate_aes, calibrate_threshold, evidence_completeness
from app.readiness import calculate_arrs, readiness_category, select_best_fit
from app.topsis import fixed_reference_topsis


class ScoringTests(unittest.TestCase):
    def test_equal_eqam_scores_produce_equal_aes(self):
        result = calculate_aes({dimension: 0.8 for dimension in (
            "semantic_relevance", "model_confidence", "evidence_completeness",
            "source_reliability", "evidence_strength",
        )})
        self.assertEqual(result.aes, 0.8)

    def test_eqam_rejects_missing_or_invalid_dimension(self):
        with self.assertRaises(ValueError):
            calculate_aes({"semantic_relevance": 0.5})
        with self.assertRaises(ValueError):
            calculate_aes({dimension: 1.1 for dimension in (
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength",
            )})

    def test_completeness_is_explicitly_unassessable_without_checklist(self):
        self.assertEqual(evidence_completeness([], [])["status"], "unassessable")
        with self.assertRaises(ValueError):
            evidence_completeness("item", ["item"])

    def test_threshold_requires_both_validation_classes(self):
        self.assertEqual(calibrate_threshold([(0.8, True)])["status"], "threshold_calibration_required")
        result = calibrate_threshold([(0.8, True), (0.2, False)])
        self.assertEqual(result["status"], "threshold_selection_requires_researcher_approval")
        self.assertIsNone(result["threshold"])
        self.assertTrue(result["candidate_metrics"])

    def test_numeric_helpers_reject_bool_nan_and_infinity(self):
        dimensions = {
            name: 0.5 for name in (
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength",
            )
        }
        for bad in (True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    calculate_aes({**dimensions, "semantic_relevance": bad})
                with self.assertRaises(ValueError):
                    fixed_reference_topsis([bad], [1.0])
                with self.assertRaises(ValueError):
                    calculate_arrs({"WURI": bad, "THE": 1, "QS": 1, "UI GreenMetric": 1})
                with self.assertRaises(ValueError):
                    calibrate_threshold([(bad, True), (0.2, False)])

    def test_eqam_rejects_invalid_weight_vector(self):
        dimensions = {
            name: 0.5 for name in (
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength",
            )
        }
        with self.assertRaises(ValueError):
            calculate_aes(dimensions, {name: 0.1 for name in dimensions})
        with self.assertRaises(ValueError):
            calculate_aes(dimensions, {**{name: 0.2 for name in dimensions}, "extra": 0})

    def test_ahp_equal_matrix(self):
        result = calculate_ahp([[1, 1], [1, 1]])
        self.assertEqual(result.weights, [0.5, 0.5])
        self.assertTrue(result.accepted)

    def test_ahp_rejects_nonreciprocal_matrix(self):
        with self.assertRaises(ValueError):
            calculate_ahp([[1, 2], [2, 1]])

    def test_ahp_rejects_malformed_values_and_unapproved_limit(self):
        for matrix in ([], [[1, 2], [0.5]], [[1, True], [1, 1]], [[1, float("nan")], [1, 1]]):
            with self.subTest(matrix=matrix):
                with self.assertRaises(ValueError):
                    calculate_ahp(matrix)
        with self.assertRaises(ValueError):
            calculate_ahp([[1, 1], [1, 1]], max_consistency_ratio=0.2)

    def test_ahp_consistency_above_point_one_requires_review(self):
        result = calculate_ahp([[1, 9, 1 / 9], [1 / 9, 1, 9], [9, 1 / 9, 1]])
        self.assertGreater(result.consistency_ratio, 0.10)
        self.assertFalse(result.accepted)

    def test_fixed_reference_topsis_boundaries(self):
        worst = fixed_reference_topsis([0, 0], [0.5, 0.5])
        best = fixed_reference_topsis([1, 1], [0.5, 0.5])
        self.assertEqual(worst.rrs, 0)
        self.assertEqual(worst.distance_negative, 0)
        self.assertEqual(best.rrs, 100)
        self.assertEqual(best.distance_positive, 0)

    def test_fixed_reference_topsis_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            fixed_reference_topsis([1.1, 0], [0.5, 0.5])

    def test_topsis_rejects_empty_mismatched_and_invalid_weights(self):
        for values, weights in (([], []), ([0.5], []), ([0.5], [-0.1]), ([0.5], [0.9])):
            with self.subTest(values=values, weights=weights):
                with self.assertRaises(ValueError):
                    fixed_reference_topsis(values, weights)
        for invalid_weight in (True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid_weight=invalid_weight):
                with self.assertRaises(ValueError):
                    fixed_reference_topsis([0.5], [invalid_weight])

    def test_arrs_requires_all_frameworks(self):
        values = {framework: 50 for framework in ("WURI", "THE", "QS", "UI GreenMetric")}
        self.assertEqual(calculate_arrs(values), 50)
        with self.assertRaises(ValueError):
            calculate_arrs({"WURI": 50})

    def test_best_fit_rejects_ties_and_uses_strict_five_point_boundary(self):
        tied = {"WURI": 80, "THE": 80, "QS": 50, "UI GreenMetric": 40}
        with self.assertRaisesRegex(ValueError, "tied"):
            select_best_fit(tied)
        for margin, expected_review in ((4.99, True), (5.0, False), (5.01, False)):
            scores = {"WURI": 80, "THE": 80 - margin, "QS": 50, "UI GreenMetric": 40}
            result = select_best_fit(scores)
            self.assertEqual(result.expert_review_required, expected_review)
            self.assertEqual(result.status, "provisional_pending_expert_validation")

    def test_best_fit_close_alternative_boundary(self):
        base = {"WURI": 80, "THE": 76, "QS": 50, "UI GreenMetric": 40}
        close = select_best_fit(base)
        self.assertEqual(close.close_alternative, "THE")
        self.assertTrue(close.expert_review_required)
        self.assertEqual(close.status, "provisional_pending_expert_validation")
        base["THE"] = 75
        clear_fit = select_best_fit(base)
        self.assertIsNone(clear_fit.close_alternative)
        self.assertFalse(clear_fit.expert_review_required)

    def test_best_fit_rejects_non_dissertation_close_margin(self):
        with self.assertRaisesRegex(ValueError, "fixed at 5 points"):
            select_best_fit(
                {"WURI": 80, "THE": 70, "QS": 60, "UI GreenMetric": 50},
                close_margin=0,
            )

    def test_readiness_category_boundaries(self):
        self.assertEqual(readiness_category(24.99), "Low")
        self.assertEqual(readiness_category(25), "Developing")
        self.assertEqual(readiness_category(50), "Moderate")
        self.assertEqual(readiness_category(75), "High")


if __name__ == "__main__":
    unittest.main()

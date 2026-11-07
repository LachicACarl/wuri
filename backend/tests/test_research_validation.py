import unittest
import random

from app.research_validation import (
    ABLATIONS,
    ablation_statuses,
    audit_explanation_traceability,
    agreement_metrics,
    best_fit_agreement,
    classification_metrics,
    cohen_kappa,
    descriptive_statistics,
    eqam_rss_association,
    eqam_expert_agreement,
    fleiss_kappa,
    icc_2_1,
    paired_score_comparison,
    retrieval_metrics,
    run_robustness_scenarios,
    split_evidence_dataset,
    threshold_from_validation,
    xai_rating_summary,
)


def synthetic_fixture():
    rows = []
    for index in range(24):
        text = (
            "A controlled example about regional innovation outcomes and verified institutional evidence."
            if index in (0, 1)
            else f"Unique controlled fixture topic token{index} measure{index * 3} outcome{index * 7}."
        )
        rows.append({
            "example_id": f"fixture-{index}",
            "text": text,
            "framework": "WURI" if index % 2 else "THE",
            "indicator": f"indicator-{index % 4}",
            "major_indicator_group": f"group-{index % 2}",
            "label": bool(index % 2),
            "source_document_id": f"doc-{index}",
            "annotation_status": "expert_reviewed",
        })
    return rows


class ResearchValidationTests(unittest.TestCase):
    def test_fleiss_kappa_computes_agreement_for_multiple_raters(self):
        result = fleiss_kappa([
            ["yes", "yes", "no"],
            ["no", "no", "no"],
            ["yes", "yes", "yes"],
            ["no", "no", "yes"],
        ])
        self.assertEqual(result["sample_count"], 4)
        self.assertEqual(result["raters_per_case"], 3)
        self.assertAlmostEqual(result["observed_agreement"], 2 / 3)
        self.assertAlmostEqual(result["kappa"], 1 / 3)

    def test_fleiss_kappa_rejects_incomplete_or_inconsistent_rater_counts(self):
        with self.assertRaisesRegex(ValueError, "same two or more raters"):
            fleiss_kappa([["yes"], ["no"]])
        with self.assertRaisesRegex(ValueError, "same two or more raters"):
            fleiss_kappa([["yes", "no"], ["no"]])

    def test_fleiss_kappa_handles_perfect_agreement_and_empty_input(self):
        result = fleiss_kappa([["yes", "yes"], ["no", "no"]])
        self.assertEqual(result["kappa"], 1)
        self.assertIsNone(fleiss_kappa([])["kappa"])

    def test_fleiss_kappa_rejects_empty_categorical_labels(self):
        with self.assertRaisesRegex(ValueError, "non-empty categorical strings"):
            fleiss_kappa([["yes", " "]])

    def test_fleiss_kappa_known_five_rater_panel_and_undefined_degenerate_case(self):
        result = fleiss_kappa([
            ["yes", "yes", "yes", "no", "no"],
            ["no", "no", "no", "no", "no"],
            ["yes", "yes", "yes", "yes", "yes"],
        ])
        self.assertEqual(result["raters_per_case"], 5)
        self.assertAlmostEqual(result["observed_agreement"], 0.8)
        self.assertAlmostEqual(result["kappa"], 67 / 112)
        self.assertIsNone(fleiss_kappa([["yes", "yes"], ["yes", "yes"]])["kappa"])

    def test_icc_2_1_known_values_and_invalid_or_degenerate_inputs(self):
        self.assertAlmostEqual(icc_2_1([[1, 1], [2, 2], [3, 3]]), 1.0)
        self.assertAlmostEqual(
            icc_2_1([[1, 1.5], [2, 2.5], [3, 3.5]]),
            0.8888888888888888,
        )
        self.assertIsNone(icc_2_1([[1, 1], [1, 1]]))
        self.assertIsNone(icc_2_1([]))
        with self.assertRaisesRegex(ValueError, "at least two complete cases"):
            icc_2_1([[1, 1]])
        with self.assertRaisesRegex(ValueError, "at least two complete cases"):
            icc_2_1([[1, 2], [3]])
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            icc_2_1([[1, float("nan")], [2, 3]])

    def test_split_is_reproducible_and_groups_exact_near_duplicates(self):
        rows = synthetic_fixture()
        first = split_evidence_dataset(rows, "fixture-v1", 71)
        second = split_evidence_dataset(rows, "fixture-v1", 71)
        permuted = split_evidence_dataset(list(reversed(rows)), "fixture-v1", 71)
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(first.as_dict(), permuted.as_dict())
        self.assertEqual(first.proportions, {"train": 0.70, "validation": 0.15, "test": 0.15})
        self.assertEqual(first.assignments["fixture-0"], first.assignments["fixture-1"])
        self.assertEqual(sum(first.counts.values()), len(rows))
        self.assertEqual(set(first.counts), {"train", "validation", "test"})

    def test_split_groups_explicit_leakage_group_across_documents(self):
        rows = synthetic_fixture()
        rows[0]["leakage_group_id"] = "linked-institution-batch"
        rows[7]["leakage_group_id"] = "linked-institution-batch"
        split = split_evidence_dataset(rows, "fixture-leakage-v1", 23)
        self.assertEqual(split.assignments["fixture-0"], split.assignments["fixture-7"])
        self.assertEqual(split.split_version, "grouped-stratified-70-15-15-v3-approved-leakage-groups")

    def test_split_rejects_custom_proportions_and_too_few_groups(self):
        with self.assertRaisesRegex(ValueError, "prescribed 70:15:15"):
            split_evidence_dataset(synthetic_fixture(), "fixture-v1", 1,
                                  proportions={"train": 0.6, "validation": 0.2, "test": 0.2})
        with self.assertRaisesRegex(ValueError, "At least three independent"):
            split_evidence_dataset([
                {**synthetic_fixture()[0], "example_id": "one"},
                {**synthetic_fixture()[1], "example_id": "two"},
            ], "tiny", 1)

    def test_split_rejects_unreviewed_records(self):
        rows = synthetic_fixture()
        rows[0]["annotation_status"] = "model_predicted"
        with self.assertRaisesRegex(ValueError, "not expert-reviewed"):
            split_evidence_dataset(rows, "fixture-v1", 1)

    def test_classification_metrics_match_independent_fixture_calculation(self):
        result = classification_metrics([
            {"framework": "WURI", "label": "yes", "prediction": "yes"},
            {"framework": "WURI", "label": "yes", "prediction": "no"},
            {"framework": "THE", "label": "no", "prediction": "no"},
            {"framework": "THE", "label": "no", "prediction": "yes"},
        ])
        self.assertEqual(result["aggregate"]["accuracy"], 0.5)
        self.assertEqual(result["aggregate"]["macro_precision"], 0.5)
        self.assertEqual(result["aggregate"]["macro_recall"], 0.5)
        self.assertEqual(result["aggregate"]["macro_f1"], 0.5)
        self.assertEqual(result["by_framework"]["WURI"]["sample_count"], 2)

    def test_retrieval_precision_and_recall_at_k(self):
        result = retrieval_metrics(
            {"WURI:q1": {"a"}, "THE:q2": {"d"}},
            {"WURI:q1": ["b", "a", "c"], "THE:q2": ["d", "e", "f"]},
        )
        self.assertAlmostEqual(result["aggregate"]["precision@1"], 0.5)
        self.assertAlmostEqual(result["aggregate"]["precision@3"], 1 / 3)
        self.assertAlmostEqual(result["aggregate"]["recall@3"], 1.0)
        self.assertEqual(result["aggregate"]["query_count"], 2)

    def test_threshold_uses_validation_labels_and_locks_reproducible_result(self):
        result = threshold_from_validation(
            [0.9, 0.8, 0.2, 0.1], [True, True, False, False], "approved-v1"
        )
        self.assertEqual(result["status"], "locked_from_validation")
        self.assertEqual(result["validation_dataset_version"], "approved-v1")
        self.assertFalse(result["test_labels_used"])
        self.assertEqual(result["threshold"], 0.8)
        self.assertEqual(
            threshold_from_validation([0.8], [True], "approved-v1")["status"],
            "blocked_missing_data",
        )

    def test_expert_agreement_and_descriptive_statistics(self):
        values = agreement_metrics([1, 2, 3], [1, 2, 4])
        self.assertAlmostEqual(values["mae"], 1 / 3)
        self.assertAlmostEqual(values["rmse"], (1 / 3) ** 0.5)
        self.assertAlmostEqual(values["spearman_rho"], 1.0)
        self.assertEqual(descriptive_statistics([1, 2, 3])["mean"], 2)
        quality = eqam_expert_agreement(
            {"case": {dimension: 0.8 for dimension in (
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength",
            )}},
            {"case": {dimension: 0.7 for dimension in (
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength",
            )}},
        )
        self.assertFalse(quality["dimensions"]["semantic_relevance"]["validation_claim_allowed"])
        self.assertEqual(cohen_kappa(["yes", "no"], ["yes", "yes"])["exact_agreement"], 0.5)

    def test_paired_comparison_is_seeded_and_handles_no_difference(self):
        result = paired_score_comparison(
            [3, 4, 5, 8, 10, 12], [1, 2, 3, 5, 6, 8], significance_alpha=0.05, seed=17
        )
        repeated = paired_score_comparison(
            [3, 4, 5, 8, 10, 12], [1, 2, 3, 5, 6, 8], significance_alpha=0.05, seed=17
        )
        self.assertEqual(result, repeated)
        self.assertEqual(result["status"], "completed")
        identical = paired_score_comparison([1, 2, 3], [1, 2, 3],
                                            significance_alpha=0.05, seed=1)
        self.assertFalse(identical["statistically_significant"])

    def test_eqam_rss_association_reports_coupling_and_requires_power_plan(self):
        self.assertEqual(
            eqam_rss_association([], minimum_sample_size=None, significance_alpha=0.05)["status"],
            "blocked_missing_data",
        )
        rng = random.Random(19)
        rows = []
        dimensions = (
            "semantic_relevance", "model_confidence", "evidence_completeness",
            "source_reliability", "evidence_strength",
        )
        for index in range(60):
            values = {dimension: rng.random() for dimension in dimensions}
            rows.append({
                "case_id": f"synthetic-case-{index}",
                **values,
                "rrs": 100 * (0.35 * values["semantic_relevance"]
                              + 0.15 * values["model_confidence"]
                              + 0.2 * values["evidence_completeness"]
                              + 0.15 * values["source_reliability"]
                              + 0.15 * values["evidence_strength"]),
            })
        result = eqam_rss_association(
            rows, minimum_sample_size=40, significance_alpha=0.05
        )
        self.assertEqual(result["status"], "completed_with_limitations")
        self.assertEqual(result["sample_count"], 60)
        self.assertIn("do not establish", result["interpretation"])
        self.assertIn("holm_adjusted_p_value", result["spearman_associations"]["semantic_relevance"])

    def test_ablation_definitions_keep_baseline_components_isolated(self):
        self.assertFalse(ABLATIONS["A0"]["components"]["eqam"])
        self.assertFalse(ABLATIONS["A0"]["components"]["xai"])
        self.assertEqual(ABLATIONS["A3"]["components"]["sentence_encoder"], "domain_adapted_sbert")
        self.assertTrue(ABLATIONS["A4"]["components"]["xai"])
        self.assertTrue(all(item["status"] == "blocked_missing_data"
                            for item in ablation_statuses(set())))
        self.assertEqual(xai_rating_summary([])["ratings_by_dimension"], {})

    def test_robustness_uses_fixed_reference_method_and_protects_weights(self):
        frameworks = ("WURI", "THE", "QS", "UI GreenMetric")
        baseline = {
            framework: {"criteria": [0.9 - index * 0.1, 0.6], "weights": [0.5, 0.5]}
            for index, framework in enumerate(frameworks)
        }
        scenario = {
            framework: {"criteria": [0.88 - index * 0.1, 0.6], "weights": [0.4, 0.6]}
            for index, framework in enumerate(frameworks)
        }
        result = run_robustness_scenarios(
            baseline,
            [scenario],
            variable_weight_indices={framework: {0, 1} for framework in frameworks},
            variable_criterion_indices={framework: {0} for framework in frameworks},
        )
        self.assertEqual(result["scenario_count"], 1)
        self.assertIn("fixed-reference", result["note"])
        with self.assertRaisesRegex(ValueError, "fixed, non-permitted"):
            run_robustness_scenarios(baseline, [scenario])

    def test_robustness_rejects_missing_framework_or_malformed_vectors(self):
        frameworks = ("WURI", "THE", "QS", "UI GreenMetric")
        baseline = {
            framework: {"criteria": [0.9 - index * 0.1], "weights": [1.0]}
            for index, framework in enumerate(frameworks)
        }
        with self.assertRaisesRegex(ValueError, "exactly one vector set"):
            run_robustness_scenarios({"WURI": baseline["WURI"]}, [])
        malformed = {**baseline, "WURI": {"criteria": [], "weights": []}}
        with self.assertRaisesRegex(ValueError, "non-empty and have equal length"):
            run_robustness_scenarios(malformed, [])

    def test_best_fit_agreement_reports_close_margin_cases_separately(self):
        result = best_fit_agreement(
            {"case-1": "WURI", "case-2": "THE"},
            {"case-1": "WURI", "case-2": "WURI"},
            {"case-1": 7.0, "case-2": 4.9},
        )
        self.assertEqual(result["exact_agreement_rate"], 0.5)
        self.assertEqual(result["system_cases_below_close_margin"], 1)
        self.assertEqual(result["agreement_for_close_margin_cases"], 0.0)

    def test_explanation_fidelity_audit_checks_traceability_and_numeric_values(self):
        result = audit_explanation_traceability(
            [
                {"criterion_id": "criterion-1", "source_passage_ids": ["passage-1"],
                 "contribution": 2.5},
            ],
            available_passage_ids={"passage-1"},
            expected_contributions={"criterion-1": 2.5},
            reported_score=55.0,
            expected_score=55.0,
        )
        self.assertEqual(result["status"], "passed_fidelity_checks")
        self.assertIn("do not measure clarity", result["note"])
        invalid = audit_explanation_traceability(
            [
                {"criterion_id": "criterion-1", "source_passage_ids": ["missing"],
                 "contribution": 2.5},
            ],
            available_passage_ids={"passage-1"},
            expected_contributions={"criterion-1": 2.5},
            reported_score=55.1,
            expected_score=55.0,
        )
        self.assertEqual(invalid["status"], "failed_fidelity_checks")


if __name__ == "__main__":
    unittest.main()

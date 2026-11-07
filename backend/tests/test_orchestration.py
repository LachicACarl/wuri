import unittest
from dataclasses import replace
from unittest.mock import patch

from app.orchestration import AssessmentState, determine_status
from app.frameworks import FRAMEWORK_DEFINITIONS


APPROVED_DOCUMENT_PREREQUISITES = {
    "institution_authorized": True,
    "source_provenance_complete": True,
    "model_artifact_available": True,
    "research_protocol_approved": True,
}


class OrchestrationTests(unittest.TestCase):
    def _fully_ready_inputs(self):
        verified = {
            framework: replace(
                definition, criteria_status="verified", weight_status="verified"
            )
            for framework, definition in FRAMEWORK_DEFINITIONS.items()
        }
        values = {
            framework: {criterion: 0.5 for criterion in definition.criteria}
            for framework, definition in verified.items()
        }
        kwargs = {
            "has_passages": True,
            "has_matches": True,
            **APPROVED_DOCUMENT_PREREQUISITES,
            "has_model_confidence": True,
            "threshold_status": "calibrated_on_validation_data",
            "criterion_aggregation_policy": "approved-policy-id",
            "framework_criteria_locked": True,
            "framework_weights_verified": True,
            "ahp_status": "accepted",
            "criterion_values": values,
            "scoring_method_version": "test-only-v1",
        }
        return verified, kwargs

    def test_missing_institutional_authorization_blocks_scoring(self):
        result = determine_status(has_passages=True, has_matches=True)
        self.assertEqual(result.state, AssessmentState.INSTITUTION_AUTHORIZATION_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_non_boolean_prerequisite_claim_is_blocked(self):
        result = determine_status(
            has_passages=True, has_matches=True, institution_authorized="verified",
        )
        self.assertFalse(result.final_scoring_allowed)

    def test_missing_source_provenance_blocks_scoring(self):
        result = determine_status(
            has_passages=True, has_matches=True, institution_authorized=True,
        )
        self.assertEqual(result.state, AssessmentState.SOURCE_PROVENANCE_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_missing_model_artifact_blocks_scoring(self):
        result = determine_status(
            has_passages=True,
            has_matches=True,
            institution_authorized=True,
            source_provenance_complete=True,
        )
        self.assertEqual(result.state, AssessmentState.MODEL_ARTIFACT_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_unapproved_research_protocol_blocks_scoring(self):
        result = determine_status(
            has_passages=True,
            has_matches=True,
            institution_authorized=True,
            source_provenance_complete=True,
            model_artifact_available=True,
        )
        self.assertEqual(result.state, AssessmentState.RESEARCH_PROTOCOL_APPROVAL_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_missing_confidence_blocks_eqam(self):
        result = determine_status(
            has_passages=True, has_matches=True, **APPROVED_DOCUMENT_PREREQUISITES,
        )
        self.assertEqual(result.state, AssessmentState.EQAM_PENDING)
        self.assertFalse(result.final_scoring_allowed)

    def test_missing_threshold_blocks_scoring(self):
        result = determine_status(
            has_passages=True,
            has_matches=True,
            **APPROVED_DOCUMENT_PREREQUISITES,
            has_model_confidence=True,
        )
        self.assertEqual(result.state, AssessmentState.THRESHOLD_CALIBRATION_REQUIRED)

    def test_missing_aggregation_policy_blocks_scoring(self):
        result = determine_status(
            has_passages=True,
            has_matches=True,
            **APPROVED_DOCUMENT_PREREQUISITES,
            has_model_confidence=True,
            threshold_status="calibrated_on_validation_data",
        )
        self.assertEqual(result.state, AssessmentState.CRITERION_AGGREGATION_POLICY_REQUIRED)

    def test_unlocked_provisional_framework_criteria_block_scoring(self):
        result = determine_status(
            has_passages=True,
            has_matches=True,
            **APPROVED_DOCUMENT_PREREQUISITES,
            has_model_confidence=True,
            threshold_status="calibrated_on_validation_data",
            criterion_aggregation_policy="approved-policy-id",
        )
        self.assertEqual(result.state, AssessmentState.FRAMEWORK_CRITERIA_LOCK_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_unverified_framework_weights_block_scoring(self):
        verified_criteria = {
            framework: replace(definition, criteria_status="verified")
            for framework, definition in FRAMEWORK_DEFINITIONS.items()
        }
        with patch("app.orchestration.FRAMEWORK_DEFINITIONS", verified_criteria):
            result = determine_status(
                has_passages=True,
                has_matches=True,
                **APPROVED_DOCUMENT_PREREQUISITES,
                has_model_confidence=True,
                threshold_status="calibrated_on_validation_data",
                criterion_aggregation_policy="approved-policy-id",
                framework_criteria_locked=True,
            )
        self.assertEqual(result.state, AssessmentState.FRAMEWORK_WEIGHTS_VERIFICATION_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_provisional_criteria_block_even_with_supplied_scoring_inputs(self):
        result = determine_status(
            has_passages=True,
            has_matches=True,
            **APPROVED_DOCUMENT_PREREQUISITES,
            has_model_confidence=True,
            threshold_status="calibrated_on_validation_data",
            criterion_aggregation_policy="approved-policy-id",
            framework_criteria_locked=True,
            framework_weights_verified=True,
            ahp_status="accepted",
            criterion_values={"WURI": [0.5]},
            scoring_method_version="test-v1",
        )
        self.assertEqual(result.state, AssessmentState.FRAMEWORK_CRITERIA_LOCK_REQUIRED)
        self.assertFalse(result.final_scoring_allowed)

    def test_criterion_identifiers_and_normalized_values_are_validated(self):
        verified, kwargs = self._fully_ready_inputs()
        with patch("app.orchestration.FRAMEWORK_DEFINITIONS", verified):
            malformed = {**kwargs, "criterion_values": {**kwargs["criterion_values"]}}
            framework = next(iter(verified))
            malformed["criterion_values"][framework] = {"not-a-criterion": 0.5}
            result = determine_status(**malformed)
            self.assertFalse(result.final_scoring_allowed)

            for invalid_value in (-0.01, 1.01, float("nan"), float("inf"), True):
                invalid = {**kwargs, "criterion_values": {
                    key: dict(values) for key, values in kwargs["criterion_values"].items()
                }}
                first_framework = next(iter(verified))
                first_criterion = next(iter(verified[first_framework].criteria))
                invalid["criterion_values"][first_framework][first_criterion] = invalid_value
                result = determine_status(**invalid)
                self.assertFalse(result.final_scoring_allowed)

    def test_missing_criterion_value_is_blocked(self):
        verified, kwargs = self._fully_ready_inputs()
        with patch("app.orchestration.FRAMEWORK_DEFINITIONS", verified):
            framework = next(iter(verified))
            kwargs["criterion_values"][framework].pop(next(iter(verified[framework].criteria)))
            result = determine_status(**kwargs)
        self.assertFalse(result.final_scoring_allowed)


if __name__ == "__main__":
    unittest.main()

from dataclasses import dataclass
from enum import StrEnum
import math

from .frameworks import FRAMEWORK_DEFINITIONS


class AssessmentState(StrEnum):
    DOCUMENT_EXTRACTED = "document_extracted"
    EVIDENCE_RETRIEVED = "evidence_retrieved"
    INSTITUTION_AUTHORIZATION_REQUIRED = "institution_authorization_required"
    SOURCE_PROVENANCE_REQUIRED = "source_provenance_required"
    MODEL_ARTIFACT_REQUIRED = "model_artifact_required"
    RESEARCH_PROTOCOL_APPROVAL_REQUIRED = "research_protocol_approval_required"
    EQAM_PENDING = "eqam_pending"
    THRESHOLD_CALIBRATION_REQUIRED = "threshold_calibration_required"
    CRITERION_AGGREGATION_POLICY_REQUIRED = "criterion_aggregation_policy_required"
    FRAMEWORK_CRITERIA_LOCK_REQUIRED = "framework_criteria_lock_required"
    FRAMEWORK_WEIGHTS_VERIFICATION_REQUIRED = "framework_weights_verification_required"
    AHP_REVIEW_REQUIRED = "ahp_review_required"
    SCORING_READY = "scoring_ready"
    ASSESSMENT_CALCULATED = "assessment_calculated"
    RESEARCH_VALIDATION_PENDING = "research_validation_pending"


@dataclass(frozen=True)
class AssessmentStatus:
    state: AssessmentState
    reason: str
    final_scoring_allowed: bool
    scoring_method_version: str | None = None

    def as_dict(self) -> dict:
        return {
            "state": self.state.value,
            "reason": self.reason,
            "final_scoring_allowed": self.final_scoring_allowed,
            "scoring_method_version": self.scoring_method_version,
        }


def determine_status(
    *,
    has_passages: bool,
    has_matches: bool,
    institution_authorized: bool = False,
    source_provenance_complete: bool = False,
    model_artifact_available: bool = False,
    research_protocol_approved: bool = False,
    has_model_confidence: bool = False,
    threshold_status: str = "threshold_calibration_required",
    criterion_aggregation_policy: str | None = None,
    framework_criteria_locked: bool = False,
    framework_weights_verified: bool = False,
    ahp_status: str | None = None,
    criterion_values: dict[str, dict[str, float]] | None = None,
    scoring_method_version: str | None = None,
) -> AssessmentStatus:
    boolean_inputs = (
        has_passages, has_matches, institution_authorized, source_provenance_complete,
        model_artifact_available, research_protocol_approved, has_model_confidence,
        framework_criteria_locked, framework_weights_verified,
    )
    if any(not isinstance(value, bool) for value in boolean_inputs):
        return AssessmentStatus(
            AssessmentState.DOCUMENT_EXTRACTED,
            "Assessment prerequisite flags must be explicit boolean values.",
            False,
        )
    if not has_passages:
        return AssessmentStatus(
            AssessmentState.DOCUMENT_EXTRACTED,
            "No traceable passages are available for assessment.",
            False,
        )
    if not institution_authorized:
        return AssessmentStatus(
            AssessmentState.INSTITUTION_AUTHORIZATION_REQUIRED,
            "Institutional authorization has not been verified.",
            False,
        )
    if not source_provenance_complete:
        return AssessmentStatus(
            AssessmentState.SOURCE_PROVENANCE_REQUIRED,
            "Verified source metadata and provenance are required before assessment.",
            False,
        )
    if not model_artifact_available:
        return AssessmentStatus(
            AssessmentState.MODEL_ARTIFACT_REQUIRED,
            "A configured local model artifact is unavailable; no assessment can be calculated.",
            False,
        )
    if not research_protocol_approved:
        return AssessmentStatus(
            AssessmentState.RESEARCH_PROTOCOL_APPROVAL_REQUIRED,
            "The research protocol is not approved; empirical assessment is disabled.",
            False,
        )
    if not has_matches:
        return AssessmentStatus(
            AssessmentState.DOCUMENT_EXTRACTED,
            "Passages were extracted, but no indicator matches are available.",
            False,
        )
    if not has_model_confidence:
        return AssessmentStatus(
            AssessmentState.EQAM_PENDING,
            "Calibrated model confidence is unavailable; semantic similarity cannot substitute for it.",
            False,
        )
    if threshold_status != "calibrated_on_validation_data":
        return AssessmentStatus(
            AssessmentState.THRESHOLD_CALIBRATION_REQUIRED,
            "An expert-labeled validation set must calibrate and lock the evidence threshold.",
            False,
        )
    if not isinstance(criterion_aggregation_policy, str) or not criterion_aggregation_policy.strip():
        return AssessmentStatus(
            AssessmentState.CRITERION_AGGREGATION_POLICY_REQUIRED,
            "An approved rule for combining accepted evidence into criterion values is required.",
            False,
        )
    if not framework_criteria_locked or any(
        definition.criteria_status != "verified" for definition in FRAMEWORK_DEFINITIONS.values()
    ):
        return AssessmentStatus(
            AssessmentState.FRAMEWORK_CRITERIA_LOCK_REQUIRED,
            "Framework criteria are provisional or have not been approved and locked.",
            False,
        )
    if not framework_weights_verified or any(
        definition.weight_status != "verified" for definition in FRAMEWORK_DEFINITIONS.values()
    ):
        return AssessmentStatus(
            AssessmentState.FRAMEWORK_WEIGHTS_VERIFICATION_REQUIRED,
            "Framework criteria and applicable weights are not verified against authoritative sources.",
            False,
        )
    if ahp_status not in {"accepted", "not_required"}:
        return AssessmentStatus(
            AssessmentState.AHP_REVIEW_REQUIRED,
            "AHP judgments must be accepted or a verified fixed-weight path must be documented.",
            False,
        )
    if not isinstance(criterion_values, dict) or set(criterion_values) != set(FRAMEWORK_DEFINITIONS):
        return AssessmentStatus(
            AssessmentState.SCORING_READY,
            "All prerequisite configurations exist, but complete criterion vectors are still required.",
            False,
        )
    for framework, definition in FRAMEWORK_DEFINITIONS.items():
        values = criterion_values[framework]
        if not isinstance(values, dict) or set(values) != set(definition.criteria):
            return AssessmentStatus(
                AssessmentState.SCORING_READY,
                f"Criterion identifiers for {framework} do not match the locked framework catalog.",
                False,
            )
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not 0 <= value <= 1 or not math.isfinite(value)
            for value in values.values()
        ):
            return AssessmentStatus(
                AssessmentState.SCORING_READY,
                f"Criterion values for {framework} must be finite numbers between 0 and 1.",
                False,
            )
    if not isinstance(scoring_method_version, str) or not scoring_method_version.strip():
        return AssessmentStatus(
            AssessmentState.SCORING_READY,
            "A scoring-method version must be recorded before calculation.",
            False,
        )
    return AssessmentStatus(
        AssessmentState.SCORING_READY,
        "All guarded scoring prerequisites are satisfied.",
        True,
        scoring_method_version,
    )

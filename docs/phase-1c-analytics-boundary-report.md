# Phase 1C — Analytics Boundary Hardening

Review date: 2026-10-22 (Asia/Manila)

## Scope and safeguards

Changes were limited to the analytics helpers, their backend regression tests, and this report. Work used the current local tree only. No cached remote revision or Vite configuration was loaded or evaluated. No tests, application runtime, Vite, npm script, frontend test, or build was run. No institutional scoring route was added or connected, no research gate was opened, and no research result was generated.

The protocol draft remains `pending_researcher_approval`; sampling remains proposed and the HEI population frame remains unfrozen.

## Helpers inspected and contracts

| Function | Actual contract after this phase | Boundary/reachability |
|---|---|---|
| `calculate_aes` / `evidence_completeness` | AES accepts exactly the five named EQAM dimensions, finite non-boolean `[0,1]` scores, and the provisional equal 0.20 weights. Completeness reports `unassessable` for an empty required checklist; otherwise it reports the exact matched/missing identifiers. | Pure calculations; no institutional route calls them. AES is explicitly tagged provisional and pending expert validation. No evidence acceptance threshold or criterion aggregation is authorized here. |
| `calibrate_threshold` | Accepts iterable `(AES, bool expert label)` cases, validates finite `[0,1]` values and both classes, and returns candidate metrics only. It returns no selected threshold and marks selection as requiring researcher approval. | Mathematical candidate evaluation only; it cannot establish that labels/data are genuine or approved. No route calls it. |
| `calculate_ahp` | Accepts a non-empty square positive finite numeric matrix with diagonal 1 and reciprocal entries; checks the maximum CR limit is finite and no greater than 0.10. Computes geometric-mean weights, CI and CR, and marks CR above 0.10 for expert review. AHP RI is only defined for supported matrix sizes 1–10; larger sizes reject. | Generic pure AHP utility. It does not constrain AHP to subcriteria or preserve official framework weights. The research runner uses it only to validate protocol pairwise matrices. No institutional assessment route calls it. |
| `fixed_reference_topsis` | Accepts non-empty equally sized criterion and weight sequences; scores must be finite non-boolean `[0,1]`, weights finite/non-negative and sum to 1 within `1e-9`. Uses fixed ideal=weight and anti-ideal=0 anchors; checks finite distances and closeness in `[0,1]`. | Pure calculation only; vector order must be supplied consistently by a caller. The orchestration layer now validates framework-keyed criterion IDs against the framework definition before it can mark prerequisites ready. No API route invokes this helper. |
| `calculate_arrs` | Requires exactly one finite non-boolean RRS in `[0,100]` for each of WURI, THE, QS, and UI GreenMetric; computes the equal-weight mean. | Pure arithmetic; not an authorization or validation result. No institutional route calls it. |
| `select_best_fit` / `readiness_category` | Best-Fit uses the dissertation's proposed 5-point close margin; ties reject because there is no unique highest framework. A margin strictly below five flags expert review; at five or above it does not. Results are marked `provisional_pending_expert_validation`. Readiness category validates finite `[0,100]` input; category cutoffs remain provisional. | Pure helpers. The margin still needs expert validation and categories need approval. No route calls these functions. |
| `run_robustness_scenarios` | Requires exactly the four framework inputs, each with non-empty equal-length criterion/weight sequences; each candidate is validated by fixed-reference TOPSIS and the provisional Best-Fit helper. Scenario vectors must match baseline shape and changes must be allowed by the supplied index sets. Empty scenarios yield `None` for stability/frequency summaries and the result explicitly sets `empirical_claim_allowed: false`. | Research-validation utility, not a route or institutional assessment service. It can compute test/robustness RRS/ARRS values from supplied vectors, but those are not authorized institutional results. |
| `determine_status` | Requires actual boolean prerequisite flags, all four registered frameworks, and for each framework exactly its currently registered criterion IDs with finite non-boolean `[0,1]` values; also requires a non-empty aggregation-policy identifier and scoring-method version. Invalid/missing vectors return `final_scoring_allowed: false`. | Prerequisite status helper, not a scorer or a persisted approval record. No institutional route currently calls it with a complete authorization set or invokes the analytics helpers afterward. |

No active criterion-aggregation function was found. Combining multiple, contradictory, missing, duplicate, or stale passages into a criterion value remains unresolved and was not implemented.

## Validations added

- Rejected booleans as numeric inputs, as well as NaN, positive/negative infinity, out-of-range normalized scores, malformed collection inputs, and malformed numeric weights.
- Kept EQAM's primary weights fixed at equal 0.20 values; invalid alternative vectors now reject rather than silently substitute.
- Removed automatic threshold selection using the unapproved macro-F1/balanced-accuracy/lower-threshold tie-break. Candidate metrics remain inspectable, but no calibrated threshold is issued.
- Hardened AHP matrix and CR-limit validation, limited CR claims to RI-supported matrix sizes, and reject non-finite calculated outputs.
- Hardened TOPSIS vector lengths, weight non-negativity and sum tolerance, finite distance calculations, and closeness bounds. No padding, truncation, renormalization or clamping is performed.
- Hardened ARRS completeness and RRS bounds. Best-Fit rejects a top-score tie and does not allow a caller to substitute a different close-margin value.
- Hardened robustness input shape and framework completeness before candidate calculations; preserved its explicit non-empirical status.
- Tightened orchestration criterion values to framework-keyed criterion-ID mappings with exact registered IDs and normalized finite values.
- Added a static AST regression test that fails if an API route directly references a raw institutional scoring helper. Existing upload API assertions already check that the blocked response has no RRS/ARRS/Best-Fit/readiness-score fields.

## Mathematical validation versus research authorization

The helper validations establish only that supplied numbers satisfy mathematical shape and bounds. They do not show that a source document is authorized, provenance is verified, a model is approved, labels are genuine, a protocol is approved, or criteria/weights are authoritative. `calculate_aes`, AHP, TOPSIS, ARRS and Best-Fit therefore remain pure provisional utilities. Threshold candidates explicitly do not yield a selected threshold.

The orchestration function checks boolean prerequisite claims and criterion mappings, but there is not yet a guarded assessment service that binds those claims to persisted approvals, calls the calculations, and controls any result serialization. That service and any user-facing scoring integration remain out of scope; no API route directly calls the pure scoring helpers.

## Regression tests added or updated (not executed)

`backend/tests/test_scoring.py` now covers invalid bool/NaN/infinite values, EQAM weight shape, threshold approval state, malformed AHP matrices and CR limit, CR above 0.10, TOPSIS empty/mismatched/invalid vectors and zero-distance boundaries, missing ARRS frameworks, tied Best-Fit, and margins below/equal/above five points. `backend/tests/test_research_validation.py` covers malformed/missing robustness inputs.

`backend/tests/test_orchestration.py` now covers exact criterion identifiers and normalized finite values, including missing IDs and out-of-range/non-finite/bool inputs, in addition to the existing missing authorization, provenance, model, protocol, criteria, and weights gates.

`backend/tests/test_research_api.py` adds static route-source inspection to detect direct calls from API handlers to raw scoring helpers. Existing API coverage asserts no success-shaped score fields when upload prerequisites are missing and blocked research execution has no results.

These tests are source additions only. They have not been run and must not be described as passing.

## Routes and code paths

Static search found no institutional API route calling the raw AES, AHP, TOPSIS, ARRS or Best-Fit helpers. `/api/upload` returns extracted passages and retrieval candidates, not ranking scores. The framework and manual evidence-readiness routes explicitly keep scoring disabled. The research experiment route is separate and subject to preflight; the only registered A0 executor is retrieval-only and states that it produces no AES/AHP-TOPSIS/RRS/ARRS.

The remaining architectural gap is internal: pure helpers can be called directly by future Python code without a prerequisite service. The orchestration status helper does not itself execute calculations, persist approvals, or serialize a score response. Before an assessment path is connected, create a service boundary that consumes verifiable authorization/provenance/protocol/model/catalog states, validates all per-framework criterion IDs, calls helpers only after those checks, and returns blocked/errors without score-shaped success payloads. A raw calculation helper should not be exposed as a route.

## Unresolved methodological decisions

- Approval and provenance checks for actual institutional documents and DUAs.
- Exact approved model identity, artifact checksum and training provenance.
- Expert-approved EQAM rubrics, confidence calibration, and genuine expert-labeled validation data.
- Threshold selection tie-break and the operational meaning of balanced precision/recall behavior.
- Official framework catalog/weight sources and locked versions; published weights must remain fixed where applicable.
- Approved criterion aggregation across multiple or conflicting evidence passages.
- Expert validation of the five-point Best-Fit close-margin rule and readiness interpretation bands.
- Full Chapter 3 A0–A4 methodology and the difference between retrieval-only A0 and the dissertation's readiness baseline.

The five-point margin remains a provisional implementation of the stated dissertation rule; this code does not treat that rule as researcher-approved. No alternative aggregation policy, EQAM threshold, or framework weight was invented.

## Before scoring can be connected

1. Complete the independent security review of the suspicious cached Vite configuration before any Vite-driven runtime validation.
2. Keep A0–A4 disabled until the researcher approves and versions the protocol and required datasets, model, expert labels, framework catalogs/weights, aggregation and interpretation decisions.
3. Implement the guarded assessment service described above, with approvals sourced from controlled/persisted records rather than caller-supplied booleans alone; derive every ordered numeric vector from the same locked criterion-ID catalog.
4. Resolve and document the remaining mathematical/methodological policies, then add service/API contract tests and run the backend regression suite only after the security gate is cleared and runtime checks are authorized.

## Files changed

- `backend/app/eqam.py`
- `backend/app/ahp.py`
- `backend/app/topsis.py`
- `backend/app/readiness.py`
- `backend/app/orchestration.py`
- `backend/app/research_validation.py`
- `backend/tests/test_scoring.py`
- `backend/tests/test_orchestration.py`
- `backend/tests/test_research_api.py`
- `backend/tests/test_research_validation.py`
- `docs/phase-1c-analytics-boundary-report.md` (this report)

Existing `App.jsx` work, untracked backend/docs, snapshots, and unrelated changes remain preserved. The protocol is still pending approval, no score/result was generated, and runtime behavior and the new regression tests remain unverified.

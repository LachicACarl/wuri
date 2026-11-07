# Phase 1B — Static Review and Dissertation Alignment

Review date: 2026-10-22 (Asia/Manila)

## Scope and limits

Reviewed the current local working tree and local `HEAD` only. No application code, Vite configuration, test runner, build, model, or cached remote revision was executed or loaded. The seven preserved `App.jsx` snapshots and all pre-existing changes were left untouched. The A0 protocol draft remains `pending_researcher_approval`.

Files reviewed include:

- `university-ranking-dss/src/App.jsx`, `university-ranking-dss/src/main.jsx`
- `backend/app/main.py`, `orchestration.py`, `database.py`, `storage.py`, `security.py`, `experiment_runner.py`, `frameworks.py`, `document_processing.py`, `retrieval.py`, `eqam.py`, `ahp.py`, `topsis.py`, `readiness.py`, and `research_validation.py`
- `backend/tests/test_orchestration.py`, `test_research_api.py`, and related research/persistence test definitions
- `docs/phase-1a-synthetic-result-audit.md`, `docs/a0-retrieval-protocol-draft.json`, and `docs/research-methodology-traceability.md`

## Assessment path and findings

1. The active frontend imports `App.jsx` from `src/main.jsx`. Search found the old `buildLocalEvaluation` function only in the seven `.backup` / `.before-*` snapshots; none is imported or called by the active module graph.
2. `DocumentUpload` posts the selected file to `/api/upload`. A non-2xx response or network error is shown as an unavailable assessment and does not call `onEvaluation`. A 2xx response is shown as extracted evidence with an explicit no-readiness-score notice.
3. The backend requires an authenticated user with institution membership, validates the file, malware-scans it, extracts passages, and persists document/passages/matches. It stores caller-supplied metadata as metadata, while new uploads explicitly set `authorization_status` and `research_permission_status` to `unknown`. `provenance` may be supplied by a client, but is not itself treated as verified authorization or complete provenance by the active upload path.
4. Retrieval runs only if `WURI_SBERT_MODEL_PATH` points to a locally present Sentence-Transformers artifact; loading is requested with `local_files_only=True`. Missing or unloadable artifacts produce no matches and a warning. This checks local presence, not an approved model identity/checksum; the result remains retrieval candidates only.
5. The upload response contains passages, optional retrieval matches, warnings, workflow state and `readiness_assessment_status: not_implemented`. It contains no RRS, ARRS, Best-Fit, or readiness-score field. `determine_status` receives no authorization, provenance, or protocol approvals from this route, so its default-false gates block scoring.
6. `/api/frameworks` reports `scoring_enabled: false`; institution evidence-readiness records also report scoring disabled. Those records are workflow metadata, not calculated rankings.
7. `/api/assessments` returns persisted assessment/institution identifiers, status and timestamps. The history view displays those fields only and has explicit empty/error states. Document download returns the uploaded source document, not an assessment report. No active institutional score/report export route or caller of the ranking calculators was found.
8. Research experiment execution is a separate route. The runner returns `results: null` when preflight disallows execution and requires approved protocol/model/data conditions before executing; it verifies protocol and model artifact consistency around inference. The current protocol is pending approval. The registered A0 executor is retrieval-only; it is not the full Chapter 3 readiness baseline.

### Confirmed fail-closed behavior

- Static source shows no synthetic scoring fallback in the active upload path and no ranking fields in its response.
- Unverified authorization/research permission remain `unknown` on upload. Research data-source checks require verified authorization, research permission, review status and clean malware scan before a document is eligible as a research source.
- Missing authorization, provenance, local model, approved protocol, calibrated confidence/threshold, aggregation policy, locked/verified criteria and verified weights are represented as blocking states in `determine_status`.
- HTTP upload errors are shown as errors, not successful evaluation records. History fetch checks `response.ok` and reports failure.
- `App.jsx` has no synthetic fallback; historical snapshots remain inactive and untouched.

### Remaining bypasses and ambiguous branches

- The orchestration guard is currently not called by any institutional scoring endpoint because no such endpoint is connected. Its `final_scoring_allowed` value is therefore a status helper, not an enforced authorization boundary around the pure calculation helpers. Direct internal calls to `calculate_ahp`, `fixed_reference_topsis`, or readiness helpers can calculate caller-provided numbers. Static review found no active API/UI route that exposes these calculations as institutional scores.
- `determine_status` checks criterion vectors for non-empty finite numbers, but does not check their lengths against each framework's registered criteria or constrain values to the expected `[0,1]` range. No active caller supplies vectors, so this does not currently create an apparent institutional result; it should be tightened before connecting scoring.
- Local retrieval model availability is a filesystem-presence check rather than an approved artifact identity/checksum check. It can produce retrieval candidates, not readiness scores. UI copy labels matches as candidates and the research runner has stricter model-manifest checks.
- Document permission verification is restricted to institution administrators, but the static workflow records a user's verified metadata assertion; it does not independently validate a DUA or source authenticity. No ranking operation consumes that metadata in the active upload route.
- The upload screen's initial institution/framework `Promise.all` parses JSON without checking each `response.ok`; this can leave the form in an empty state after an API error. It does not display a successful result, and the upload endpoint independently rejects invalid/missing selections.

**Answer to the key question:** No active institutional assessment path was found that produces or displays an apparent ranking-readiness result when prerequisites are missing. Active upload yields extraction/retrieval workflow output only. The internal scoring helpers are callable without the orchestration gate, so a future scoring endpoint must bind prerequisite enforcement to the calculation boundary and validate vector dimensions/ranges before exposing results.

## Dissertation alignment matrix

Statuses describe the active end-to-end capability, not whether a helper or label exists. Nothing in this review establishes runtime correctness.

| Chapter 3 requirement | Status | Static basis |
|---|---|---|
| Authorized institutional documents and traceable evidence passages | `blocked_missing_data` | Upload, extraction, passage metadata and review storage exist, but no authorized HEI evidence corpus/DUA is present; uploaded documents begin unverified. |
| Enhanced Sentence-BERT | `blocked_researcher_approval` | Optional local retrieval exists, but no approved enhanced artifact/training provenance or locked protocol is available; no end-to-end enhanced assessment path. |
| Five-dimensional EQAM | `partially_implemented` | Calculation/validation utilities and research workflow exist; calibrated confidence, approved rubric anchors and real expert ratings are absent, and upload does not calculate EQAM. |
| Validation-selected evidence-acceptance threshold | `partially_implemented` | Validation-only calibration helper exists, but real expert-labeled validation data and researcher-approved tie-break/operational definition are missing; not connected to upload. |
| Framework-constrained AHP and CR <= 0.10 | `partially_implemented` | AHP helper enforces a CR threshold; official framework criteria/weights are not locked and no institutional path invokes it. |
| Fixed-reference TOPSIS | `partially_implemented` | Fixed-anchor TOPSIS helper exists; no approved criterion aggregation/weights or active assessment invocation. |
| RRS, equal-weight ARRS and Best-Fit close-margin rule | `partially_implemented` | Helpers exist, but no authorized institutional score vectors or active assessment result path; close-margin expert validation remains pending. |
| XAI traceability and research evaluation | `not_implemented` | UI explicitly reports explanations unavailable without validated scores; no active score-to-evidence explanation/evaluation workflow produces institutional explanations. |

The protocol state remains `pending_researcher_approval`. Sampling remains proposed, the HEI population frame is unfrozen, and A0–A4 readiness results are not authorized or available.

## Regression tests reviewed

The added orchestration tests cover missing authorization, provenance, model, protocol approval, confidence, threshold, aggregation policy, unlocked criteria, and unverified weights. API tests inspect no-model upload behavior, blocked status, absent score fields, absent fabricated provenance, document review states, and a blocked experiment with no result persistence. Tests were read only and were not run.

Coverage gaps to address before or alongside runtime validation:

- Add an explicit API case proving caller-supplied provenance alone does not change the blocked state, and that client upload metadata cannot mark authorization/review verified.
- Add a positive-shape guard test for malformed criterion vectors: missing/extra framework keys, wrong vector lengths, out-of-range values, and non-finite values. Current code checks only keys, non-empty vectors and finiteness.
- Add an all-prerequisites-satisfied orchestration case and verify its exact state/meaning; separately establish that this helper result cannot itself create or persist a score.
- Exercise the configured-local-model retrieval path with a controlled stub and confirm matches remain candidate-only and no score fields are emitted; separately cover model identity/approval policy once defined.
- Assert that API/execution errors never persist a successful result and that assessment detail/history contain workflow metadata only. No score export exists to test today; add a negative/contract test if such a route is introduced.
- Add coverage for frontend error rendering or a manual UI check after the security gate is cleared. No frontend test harness was identified in the reviewed files.

Existing software fixtures intentionally use synthetic data. They are test inputs, not research outputs; their presence is not evidence that the empirical workflow is complete.

## Functionality preserved or affected

- Institution management, authenticated document upload, document metadata/review, source-document download, evidence readiness records and research expert-review workflows remain present in the active code.
- Upload errors, extraction failures, unavailable retrieval, empty history and history fetch failures have explicit states. Review remains a separate metadata workflow.
- History now shows persisted workflow records instead of fabricated rank rows. Evidence and framework screens show provisional/unavailable states rather than simulated scores.
- Potential usability issue: initial institution/framework loading parses response bodies without checking HTTP status, which may appear as an empty form on an API error. This is not a false-positive assessment result.

## Findings requiring runtime validation

Static review cannot establish whether the current API, database schema/migrations, browser rendering, file processing, local-model loading, authorization cookies, or failure recovery behave correctly at runtime. No behavior is claimed as tested.

## Prerequisites for safely resuming runtime validation

1. Complete and document the independent security investigation of the suspicious cached Vite configuration; do not load it before that review clears the risk.
2. Keep the A0 protocol at `pending_researcher_approval` unless/until the researcher approves and versions it. Do not run empirical A0–A4 readiness evaluation without approved protocol, authorized data, locked official criteria/weights, approved model artifact, calibrated threshold, criterion aggregation and required expert validation.
3. Once the security issue is cleared, obtain authorization to resume software-only runtime checks, first with synthetic fixtures; report those as software tests, not research results.
4. Before adding a production scoring endpoint, enforce the guard at the calculation boundary and validate criterion vector cardinality/ranges; bind model approval to a version/checksum rather than local presence alone.

## Validation and files changed

Permitted static searches and source review were used. `src/main.jsx` imports only the active `App.jsx`; all seven legacy snapshots containing `buildLocalEvaluation` remain unmodified and unimported. No tests, scripts, Vite, builds, or runtime checks were executed. No application code was changed. This phase added only `docs/phase-1b-static-review.md`.

Runtime behavior and regression tests remain unverified. The cached remote Vite security finding remains unresolved.

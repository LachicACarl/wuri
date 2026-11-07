# Phase 1A — Synthetic assessment result audit

Audit date: 2026-10-22 (Asia/Manila)

This phase inspected and changed only the current local working tree. It did not inspect or load the cached remote revision, run Vite/npm, run application code, or execute tests. The security disposition in [security-triage-report.md](./security-triage-report.md) remains in force.

## Findings in the active workflow

| Path | Original behavior and reach | Change and current behavior |
|---|---|---|
| Upload request: `university-ranking-dss/src/App.jsx`, `DocumentUpload.handleFileChange`; `backend/app/main.py`, `upload_document` | Frontend sends the selected file to `/api/upload`. HTTP failures and network errors already ended in an explicit unavailable message; there was no local score fallback in the current `App.jsx`. Backend rejects empty/unreadable/unextractable uploads and removes temporary storage on extraction failure. Successful responses contain extracted passages and optional retrieval candidates, `readiness_assessment_status: not_implemented`, and a guarded assessment status; they contain no RRS, ARRS, Best-Fit, or readiness score. | Preserved the fail-closed error path. UI now explains that matches are candidates only, institutional authorization and provenance are unverified, and no readiness score was generated. It displays the backend guard reason. Removed automatically generated “Institution-submitted …” provenance; absent provenance remains absent in storage. |
| Model fallback: `backend/app/main.py`, upload retrieval block | The upload path used `all-MiniLM-L6-v2` by default through `SentenceTransformer(model_name)`, which could resolve/download an implicit model. Those matches were not EQAM scores, but the choice was not a locked research artifact. | Retrieval now runs only when `WURI_SBERT_MODEL_PATH` identifies a valid local Sentence-Transformers artifact; loading uses `local_files_only=True`. With no artifact or load failure, the response contains no matches and an explicit warning. Assessment remains blocked independently. |
| Assessment guard: `backend/app/orchestration.py`, `determine_status` | The function defaulted to blocking on confidence, threshold, aggregation, framework weights, and AHP, but did not require institution authorization, source provenance, local model availability, protocol approval, or locked/verified criteria. The upload caller supplied only passage/match flags, so it did not calculate scores. | Added default-false gates for authorization, provenance, model artifact, protocol approval, and framework criteria lock/verification. Each missing prerequisite returns a blocked state with a reason; all must be explicitly satisfied before this helper can return `final_scoring_allowed: true`. Current framework catalog remains provisional, and upload supplies none of these approvals. |
| Framework analysis: `university-ranking-dss/src/App.jsx`, `FrameworkAnalysis` | A hardcoded frontend array showed 25% framework weights and indicator percentages as fixed/official, independent of the backend catalog. | Removed the hardcoded weights/indicator score bars. The screen now reads the backend catalog, displays its provisional criteria and verification states, and reports unavailable catalog/scoring states. |
| Evidence and XAI views: `university-ranking-dss/src/App.jsx`, `EvidenceView` and `ExplainableAI` | Evidence copy claimed five-dimensional EQAM scoring and a fixed `tau = 0.70` even though upload returns passages/matches only. XAI copy implied generated score drivers and gaps. | Reworded these screens to describe retrieval candidates and unavailable EQAM/readiness scoring. The evidence view displays the backend guard reason and an explicit no-score/auth/provenance notice; XAI has an unavailable state when no traceable score exists. |
| Assessment history: `university-ranking-dss/src/App.jsx`, `handleEvaluation` and `HistoryView` | Upload responses were inserted into in-memory “rank history” by reading `filename`, `school_name`, `best_fit`, and `arrs` from the response root. The API supplies `document.filename` and no ranking fields, so this created rows presented as ranked assessments with missing values. The rows were not persisted. | Removed upload-response history construction and ranking presentation. History now calls authenticated `/api/assessments` and displays only persisted institution, assessment ID, workflow status, and timestamps. Fetch failures show an unavailable state; no local mock fallback exists. |
| Checklist, architecture, validation, report-artifact cards: `university-ranking-dss/src/App.jsx` | Static UI copy/checkmarks implied the workflow, report outputs, and validation were implemented or evaluated. | Reframed these as proposed requirements/plans and marked validation as “Not evaluated.” Report cards now state that scoring reports are unavailable and that no empirical results exist. |

## Other paths inspected

- The active `App.jsx` has no `buildLocalEvaluation`, synthetic sample passages, seed-based scoring, filename-derived institution name, or local substitute on API failure.
- Seven preserved, untracked `App.jsx` snapshot files under `university-ranking-dss/src/` still contain the older `buildLocalEvaluation` implementation, including seeded EQAM/RRS-like values, sample passages, metadata-derived dates, and a backend-failure fallback. They use `.backup` / `.before-*` names, are not imported by `src/main.jsx`, and are not part of the active frontend module graph. They were left untouched because the user explicitly required preserving snapshots. Treat them as historical source only; do not restore or import them.
- `backend/app/eqam.py`, `ahp.py`, `topsis.py`, and `readiness.py` contain calculation helpers. Static inspection found no institutional upload API calling those helpers to create RRS/ARRS results. Existing unit tests use synthetic values for isolated software tests. The retrieval-only A0 runner documents that it produces no AES, AHP–TOPSIS, RRS, or ARRS results and is gated by protocol/data/model preflight.
- Persisted upload documents start with `authorization_status` and `research_permission_status` as `unknown`; the API's document review flow remains separate. Existing API tests already assert the unverified states. The upload UI no longer fabricates a provenance string.
- No frontend readiness report/export operation was found. The document download endpoint returns source documents, not computed ranking reports. Research experiment records are separate from institutional assessment results and remain subject to the research preflight gate.
- `docs/research-methodology-traceability.md`, `docs/research-validation-status.md`, `docs/a0-dependency-readiness.md`, and `docs/a0-retrieval-protocol-draft.json` were inspected. The protocol remains `pending_researcher_approval`; no research-status document or protocol was changed. Sampling remains proposed, the Philippine HEI frame remains unfrozen, and empirical A0–A4 remain unauthorized.

## Regression coverage added or updated

- `backend/tests/test_orchestration.py` now covers absent institutional authorization, source provenance, model artifact, protocol approval, and locked/verified framework criteria. It also retains checks for missing confidence, threshold calibration, criterion aggregation, and framework-weight verification.
- `backend/tests/test_research_api.py` now asserts that a successful extraction response remains `not_implemented`, returns `final_scoring_allowed: false`, includes no RRS/ARRS/Best-Fit/readiness score fields, produces no matches without a configured local model, and does not persist a generated provenance value.
- The frontend package has no test script or frontend test harness. No frontend test was added or run. Backend regression tests were written but **not run**, as this phase required static inspection only.

## Static validation and limits

- Inspected the edited call paths and exact source diff; searched active `App.jsx` for the former generator, hardcoded framework weights, and in-memory ranking history. The active generator, fallback, and ranking fields are absent.
- Reviewed the backend route response and persistence path, orchestration guard, framework catalog statuses, research runner gates, and cited research status documents.
- Parsed `a0-retrieval-protocol-draft.json` as JSON; its approval state remains pending.
- `git diff --check` reported no whitespace errors. It emitted only the existing CRLF/LF working-copy warning for the modified `App.jsx`.
- No Vite config, frontend executable, npm script, test runner, model artifact, or application code was loaded. No build, runtime, UI, database, or end-to-end behavior is claimed as verified.

## Files changed in this phase

- `university-ranking-dss/src/App.jsx`
- `backend/app/main.py`
- `backend/app/orchestration.py`
- `backend/tests/test_orchestration.py`
- `backend/tests/test_research_api.py`
- `docs/phase-1a-synthetic-result-audit.md` (this report)

Existing uncommitted App changes, backend/docs, and snapshots were preserved. The Vite security finding remains unresolved. Continue source-only work on the current local config; keep Vite-driven checks paused pending independent review of the suspicious cached revision.

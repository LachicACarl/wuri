# WURI system remediation baseline

Audit date: 2026-10-22 (Asia/Manila)

This Phase 0 baseline records the local checkout and source material inspected before any application remediation. No application code, data, or Git history was changed for this audit. The only file created is this report.

## Repository state

- Current branch and commit: `main`, `aafc995a937bc64e473ffe4206ed203635e4f21b` (`updated system`). The recent local history contains `aafc995`, `dd71002`, and `2fed291`.
- Configured remote: `origin` points to `https://github.com/LachicACarl/wuri.git`.
- Available remote-tracking commit: `origin/main` at `8595267641138faf240e9bd0a27b9f565bf3734f` (`updated system`). The local branch is one commit ahead and one behind that cached ref. No fetch was performed, so this is not confirmation of the live remote's current state.
- The only committed local-versus-cached-remote difference is `university-ranking-dss/vite.config.js`. Local `main` contains a short Vite config; the cached `origin/main` version has an appended, heavily obfuscated executable payload. Do not execute the remote version. The local commit appears to remove that payload. This is a material source-integrity discrepancy for investigation before any merge or deployment.
- Existing user work before this baseline: `university-ranking-dss/src/App.jsx` has a large uncommitted change (1,567 insertions and 268 deletions); `backend/` and `docs/` are untracked; six `App.jsx` backup/snapshot files are untracked. Preserve all of these. The App change alone does not include the untracked backend/docs in Git status.
- `git diff --check` reported no whitespace errors; it emitted a line-ending warning for `App.jsx` only.

## Required source inventory

| Area | Local finding | Git state |
|---|---|---|
| Frontend source and manifest | `university-ranking-dss/src/App.jsx`, `App.css`, and `package.json` exist. The Vite app uses React Router. | Tracked; `App.jsx` has user edits. |
| Backend application | FastAPI modules exist under `backend/app/`, including auth, institution/document APIs, ingestion, research validation, scoring helpers, and deployment readiness. | Entire backend tree is currently untracked. |
| Backend tests and migrations | `backend/tests/` contains tests for scoring, research APIs/validation, security, orchestration, ingestion, malware scanning, and readiness; eight SQL migrations exist. | Untracked. Tests were not run in Phase 0. |
| Research documentation | The methodology traceability, validation status, methodology decisions, and A0 protocol draft named in the audit request exist, along with additional readiness and data-governance documents. | Entire `docs/` tree is untracked. |
| Dissertation | `backend/private/research-input/UniversityRanking_V3.1.docx` exists locally. Its parent `backend/.gitignore` excludes `private/`; the dissertation is not tracked. Existing traceability documentation records it as reviewed. This report does not reproduce private dissertation contents. | Present and ignored locally. |
| Local-only artifacts | `backend/data/`, `backend/venv/`, Python caches, frontend `dist/` and `node_modules/` are ignored by nested ignore files. | Not tracked. The root has no `.gitignore`; protection currently depends on nested ignores. |
| Required report | `docs/system-remediation-baseline.md` | Created by this Phase 0 audit; currently untracked with the rest of `docs/`. |

No `.gitignore` exists at repository root. `university-ranking-dss/.gitignore` excludes its `node_modules/` and generated build directories. `backend/.gitignore` excludes local data, private inputs, `.env`, and Python caches. Because these ignore rules are in untracked files, they will not protect future clones unless the relevant files are added to version control.

## Active application and service shape

- Frontend routes currently include dashboard (`/`), login, upload, evidence, analysis, XAI, history, architecture, checklist, validation, research validation, and institution registry screens.
- Frontend API calls use `fetch` with credentials included. The current source restores auth from `/api/auth/session` and calls backend endpoints for login, institutions, readiness metadata, documents, assessments, and research workflows.
- Backend routes are implemented directly in `backend/app/main.py`; SQLite/database, private storage, auth/security, ingestion, malware scanning, assessment orchestration, research validation, and analytics helpers are separate Python modules. SQL persistence setup is represented by migrations.
- Auth uses a backend login endpoint and an HttpOnly, SameSite=Lax cookie; cookie Secure behavior is configuration-controlled and production checks are present. This source review does not establish deployment configuration or production security.
- `buildLocalEvaluation()` is absent from the current working `App.jsx`; the current diff removes the old local seeded evaluation and sample passages from that file. The UI still contains score-oriented analysis labels and evaluation-dependent screens. Whether every reachable assessment path fails closed remains unverified and is the first implementation audit priority.
- The current research docs report that no readiness scoring is enabled from the upload flow; scoring helpers are present but prerequisites and evidence aggregation remain gates. This is a source/document finding, not independent runtime verification.

## Research gate recorded in local documents

The local research status and protocol documents consistently describe the A0 protocol as `pending_researcher_approval`, with no approved research dataset/model/framework lock, and prohibit treating the retrieval-only A0 executor as the full A0 baseline. Methodology and readiness notes state that sampling/frame decisions, official framework criteria, authorized institutional evidence, expert judgments, and several aggregation and validation decisions remain unresolved. No real assessment results or empirical findings were produced in this baseline pass. These status statements have not been independently revalidated against the dissertation's full Chapter 3 text.

The local file inventory also contains population-frame planning and reconciliation drafts. This Phase 0 did not acquire, construct, freeze, or reconcile a Philippine HEI population frame, and no contact with CHED was made.

## Prioritized remediation plan

1. **Resolve source integrity and versioning.** Preserve the user-edited `App.jsx`, snapshots, backend, and docs. Review the obfuscated code in the cached remote Vite config without executing it; establish the intended upstream state and ensure required source, migrations, tests, and ignore rules are versioned before considering synchronization. Do not reset, clean, commit, or push automatically.
2. **Audit real assessment entry points.** Trace the current upload-to-assessment path and all dashboard, history, analysis, evidence, XAI, and report consumers. Confirm each unavailable prerequisite produces an explicit blocked/error state, with no local mock fallback or apparent real RRS/ARRS/Best-Fit result. Add focused regression coverage after defects are confirmed.
3. **Verify authentication, authorization, ingestion, and persistence.** Review institution scoping, session restoration and cookie configuration, upload validation, scanner fail-closed behavior, private storage/provenance, and audit events; distinguish source implementation from deployment verification.
4. **Map code to Chapter 3 with gates intact.** Inspect EQAM, AHP, TOPSIS, RRS/ARRS, experiment orchestration, and validation modules against the dissertation and traceability matrix. Keep empirical execution and user-facing scoring blocked until approved protocol, data, model, criteria, and researcher decisions exist.
5. **Verify in small phases.** Run only the relevant checks after a concrete remediation phase; report exact commands/results, changed files, remaining research decisions, and the updated Git state. Do not run A0–A4 or claim empirical findings as part of remediation.

## Phase 0 verification limits

No lint, build, backend test suite, Python compilation, browser workflow, or analytics test was run. The audit did not fetch from GitHub, execute code from the cached remote branch, inspect credentials or database contents, or independently validate deployment controls. The exact live remote state and runtime behavior therefore remain unverified.

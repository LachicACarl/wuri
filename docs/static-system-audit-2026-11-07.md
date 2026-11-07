# WURI DSS Static System Audit — 2026-11-07

**Target:** `security/recovery-remove-obfuscated-vite-config`  
**Audit type:** GitHub source/tree inspection only  
**Status:** HOLD — NO-GO; not a runtime test, penetration test, build, lint, or database audit  
**Current branch head at audit start:** `7b69fe7233074659ec7b0439f88920ecf7f5574d`

## Executive finding

The repository is currently a frontend-only React/Vite prototype. The inspected tree contains no backend/server/API source, no implemented assessment engine, no database migrations/schema, no Supabase client integration, and no test files. The frontend makes a request to `POST /api/upload`, but no handler exists in this repository tree. The login is deliberately fail-closed; as written, all protected workspace routes are inaccessible. Therefore the system is not operational or connected end-to-end.

This is a static code finding, not proof that no external service exists elsewhere. No runtime behavior was tested.

## Severity-ranked findings

### CRITICAL — F-01: No backend handler for upload API

- **Location:** `university-ranking-dss/src/App.jsx`, `DocumentUpload` component; call to `fetch('/api/upload', ...)`.
- **Evidence:** frontend posts multipart fields `file` and `document_type`; recursive repository tree contains no backend/API/server directory or handler.
- **Impact:** upload cannot produce a system assessment through this repository. Depending on hosting, the request will fail or be handled by a generic frontend fallback.
- **Required fix after authorization:** create an explicitly approved backend service, implement authenticated upload, private object storage, extraction, evidence provenance, approved scoring, and typed API responses. Add contract tests and safe error mapping.
- **Current status:** NOT IMPLEMENTED.

### CRITICAL — F-02: Authentication permanently blocks all protected routes

- **Location:** `university-ranking-dss/src/App.jsx`, `App()`.
- **Evidence:** `isAuthenticated` initializes as `false`; no session check/provider is present; no code path sets it to `true`. The wildcard route redirects every non-login URL to `/login`. Login component explicitly says authentication service is not configured.
- **Impact:** dashboard, upload, evidence, analysis, XAI, history, architecture, checklist, and validation pages cannot be accessed through normal routing.
- **Required fix after authorization:** integrate reviewed server-side identity/session flow; initialize frontend state from a session endpoint; protect backend routes independently; enforce roles, membership, institution scope, CSRF, and expiry. Do not set a client boolean as authentication.
- **Current status:** intentionally locked; replacement not implemented.

### HIGH — F-03: Frontend claims more research-method implementation than exists

- **Location:** `university-ranking-dss/src/App.jsx`; `FRAMEWORKS`, `EQAM_DIMENSIONS`, `FrameworkAnalysis`, `EvidenceView`, `ValidationView`.
- **Evidence:** constants define framework/indicator weights; UI describes EQAM/AES threshold, AHP consistency, fixed-reference TOPSIS, RRS/ARRS, validation metrics. No scoring/model implementation or research calculation modules exist in the tree. The only score data path is the external API response.
- **Impact:** displayed weights/method language can be mistaken for a validated implementation or official methodology. This is especially risky for dissertation/research reporting.
- **Required fix:** reconcile every constant, indicator label, weight, threshold, formula, anchor, and decision rule with the approved methodology/data dictionary and authoritative framework editions. Version the methodology and cite source documents in the UI/report. Implement only after researcher approval and independent validation.
- **Current status:** display-only constants; methodology not independently verified in this audit.

### HIGH — F-04: Frontend response validator does not establish authenticity or methodological correctness

- **Location:** `university-ranking-dss/src/App.jsx`, `isUsableBackendEvaluation`.
- **Evidence:** checks data shape, score ranges, required strings, evidence fields, split labels, AES and EQAM value ranges. It does not verify a trusted signature, request/assessment ID, methodology/model version, calculation provenance, evidence hash linkage, completeness thresholds, or that the server used the uploaded file.
- **Impact:** any server response with matching shape could be rendered as a “validated backend assessment”, even if the content is fabricated or methodologically invalid.
- **Required fix:** make server authoritative; include request ID, assessment ID, document hash, extraction run, methodology/model versions, evidence/source IDs, and server-side validation state. Frontend validator is UX defense only. Add schema and provenance contract tests.
- **Current status:** shape validation only; not cryptographic or methodological verification.

### HIGH — F-05: Framework configuration is hardcoded in frontend

- **Location:** `university-ranking-dss/src/App.jsx`, `FRAMEWORKS` and `EQAM_DIMENSIONS`.
- **Evidence:** fixed weights and indicator lists are embedded in the component source.
- **Impact:** no effective configuration versioning, audit trail, administrator governance, or safe updating when official frameworks/methodology change.
- **Required fix:** after approving source/methodology, move configuration into versioned server-managed records or reviewed immutable configuration package; attach source edition, effective date, version, and approval metadata. Never let arbitrary client values change research results.
- **Current status:** hardcoded display data.

### HIGH — F-06: "Official" and "fixed" weighting terminology is unsupported by code evidence

- **Location:** `FRAMEWORKS[*].officialWeight`, `FrameworkAnalysis` labels "fixed".
- **Evidence:** every framework is assigned 0.25; indicator weights are embedded as numeric literals. No source citation or configuration provenance accompanies them in the UI.
- **Impact:** a user may interpret these as official ranking-body weightings or approved cross-framework aggregation.
- **Required fix:** verify each item against the exact official framework methodology and dissertation method. Label them "proposed research configuration" until evidence/approval exists. Do not use 25% equal weighting unless the research protocol explicitly approves it.
- **Current status:** unverified in this static audit.

### HIGH — F-07: History is volatile session memory, not persistent or auditable history

- **Location:** `university-ranking-dss/src/App.jsx`, `App()` and `HistoryView`.
- **Evidence:** `history` starts as `[]` and updates via `useState`; there is no persistence/API retrieval. The UI copy does say "session-only" and "not an official university ranking".
- **Impact:** refresh/navigation lifecycle or new browser session loses history; no audit/reproducibility record.
- **Required fix:** retain session-only label or implement a protected server-side assessment history endpoint with tenant authorization, immutable run identifiers, methodology versions, and audit events. Do not call it ranking history unless true ranking data exists.
- **Current status:** session-only, explicitly not persistent.

### MEDIUM — F-08: Nested route layout and wildcard routing deserve correction/verification

- **Location:** `university-ranking-dss/src/App.jsx`, `App()`.
- **Evidence:** a top-level `/login` route and wildcard `/*` route; the wildcard element conditionally renders a shell containing a second `<Routes>` tree with absolute paths.
- **Impact:** route matching is harder to reason about; direct deep links, 404 handling, and route protection are not explicit. Authentication lock currently masks most behavior.
- **Required fix:** after session design is approved, use a single route tree with a protected layout route and explicit index/child routes plus a not-found route. Add tests for direct navigation, refresh, unknown paths, unauthenticated redirects, and role denial.
- **Current status:** static review only; no router behavior test run.

### MEDIUM — F-09: Upload control lacks visible client-side size and robust interaction/error handling

- **Location:** `DocumentUpload`.
- **Evidence:** file input accepts extensions PDF/DOCX/TXT but no client max-size check; clickable drop-zone is a generic `div`; no disabled/busy state prevents repeated submission; input is reset in finally.
- **Impact:** poor accessibility/UX and avoidable requests. Client controls cannot replace server validation.
- **Required fix:** use a keyboard-accessible label/button/dropzone, explicit busy state, visible file size/type constraints, cancellation and retry states, request ID/error code display. Validate all limits/signatures server-side.
- **Current status:** static UI shortcomings; server enforcement absent.

### MEDIUM — F-10: UI result validator and renderers can disagree on data contract

- **Location:** `isUsableBackendEvaluation`, `Dashboard`, `EvidenceView`, `FrameworkAnalysis`, `ExplainableAI`, `HistoryView`.
- **Evidence:** validator accepts fields such as `metadata`, `scores`, `evidence`, `strengths`, `weaknesses`; some views also optionally read `sub_scores`, while history derives timestamp client-side. Proposed API contract is not versioned and has no explicit `schema_version`, `request_id`, or server-produced run timestamp.
- **Impact:** backend/frontend drift and ambiguous provenance/history.
- **Required fix:** create a versioned shared schema and generated/contract-tested types; explicit response schema version, run timestamps, ids, and methodology provenance. Reject unsupported versions.
- **Current status:** no backend to validate against.

### MEDIUM — F-11: Error feedback is only a raw status string

- **Location:** `DocumentUpload`.
- **Evidence:** catch block concatenates an exception message into a status sentence; no structured error codes, request ID, retryability, or sanitized mapping.
- **Impact:** fragile UX; once backend exists, raw server error text could disclose internal details if returned carelessly.
- **Required fix:** map safe client-facing error codes; log details only server-side with correlation IDs and secret redaction.

### MEDIUM — F-12: Dependency provenance and compatibility remain unverified

- **Location:** `university-ranking-dss/package.json`, `package-lock.json`.
- **Evidence:** manifest declares React 18, React Router 7, Vite 6+ plugin, Tailwind 4, ESLint 10 and supporting plugins using ranges. No install/audit/compatibility/build/lint was run under the security hold.
- **Impact:** dependency compatibility, advisories, postinstall behavior, lockfile integrity, and build reproducibility remain unknown.
- **Required fix:** after dependency-security clearance and explicit runtime authorization, perform a lockfile/provenance review, use a pinned supported Node LTS, clean install, audit, lint, build, and tests in an isolated disposable environment. Do not run unreviewed lifecycle scripts before clearance.
- **Current status:** NOT VERIFIED; no claim of a vulnerability is made.

### LOW — F-13: Browser document metadata and session state are not persisted

- **Location:** `App()`, `DocumentUpload`.
- **Evidence:** evaluation and history are React state only. No Supabase SDK, API base URL configuration, auth SDK, or persistence adapter appears in the frontend source.
- **Impact:** data disappears on reload; no resumable processing or cross-device session.
- **Required fix:** implement only through approved server contracts; avoid direct privileged database access from the browser.

### LOW — F-14: Default app metadata is generic starter content

- **Location:** `university-ranking-dss/index.html`, `src/assets`.
- **Evidence:** title remains `university-ranking-dss`; assets include Vite/React starter SVGs.
- **Impact:** unfinished product identity/metadata, not a functional blocker.
- **Required fix:** set an approved product title/description/icon and remove unused starter assets after UI owner approval.

## Structural inventory

Inspected recursive tree under `university-ranking-dss/`:

- `package.json`, `package-lock.json`, Vite config, ESLint config, HTML entry point.
- `src/main.jsx`, `src/App.jsx`, `src/App.css`, `src/index.css`.
- Static assets including `hero.png`, React/Vite SVGs, favicon/icons.
- No backend/API/server directory.
- No test directory or test files.
- No migrations/SQL schema in the frontend app tree.
- No Supabase client package or import identified in inspected frontend source.
- No environment variable references or configured API base URL identified; upload path is relative `/api/upload`.

## Suggested resolution order after clearance

1. **Security gate:** independent review of suspicious history, credential containment evidence, dependency provenance, exact commit approval.
2. **Runtime gate:** separately authorize isolated dependency review/install, lint/build/tests; keep production and real data out of scope.
3. **BE-01:** approved identity/session flow and server-side tenant/role authorization.
4. **BE-02:** private upload/storage and validation.
5. **BE-03:** extraction with page/section/source hash provenance.
6. **BE-04:** researcher-approved, versioned methodology and scoring engine.
7. **BE-05:** versioned API contract, request/assessment retrieval, UI integration.
8. **BE-06:** reviewed schema, RLS/least-privilege, audit, backup and recovery.
9. End-to-end tests with synthetic fixtures; independent security and research review; only then separate production authorization.

## Not performed

- No package installation, scripts, lint, build, tests, server startup, or code execution.
- No GitHub Actions run/trigger/re-run.
- No Supabase database/table/schema/storage/log/credential access or change.
- No key rotation or revocation.
- No migrations or deployment.
- No real institutional/research data processing.
- No change to `main`.

**This report records static findings only. It does not clear the security hold or authorize code/runtime changes.**

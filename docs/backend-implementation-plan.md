# Backend Implementation Plan — WURI DSS

**Status:** BLOCKED — SECURITY HOLD / NO-GO  
**Document type:** Planning artifact only. This file does not authorize implementation or execution.

## 1. Current verified repository boundary

The current clean-root snapshot (`security/clean-root-quarantine-2026-11-07`) contains a React/Vite frontend under `university-ranking-dss/` that renders only a static security-hold screen. No backend, API, or server source directory is present in the inspected tree.

The earlier prototype had a `POST /api/upload` integration, but that request, file input, and upload form were removed from the current clean-root snapshot. The current frontend does not call `/api/upload`; no handler exists. Login and authentication are unavailable because no reviewed server-side authentication service is implemented.

## 2. Implementation workstreams (in dependency order)

### BE-01 — Authentication and authorization

- Select an approved server-side identity/session approach.
- Define login, logout, session refresh, expiry, CSRF protection, and secure cookie behavior.
- Define server-enforced roles: Administrator, Evaluator, Viewer.
- Enforce authorization on every protected API route; never trust frontend route guards as security controls.
- Define account recovery, audit events, rate limits, and lockout policy.
- Do not add demo credentials, client-side passwords, or local-storage bearer tokens.

**Acceptance evidence:** reviewed threat model, route/role matrix, session tests, and independent security review.

### BE-02 — Document intake and private storage

- Define allowed formats and maximum file size.
- Validate extension, MIME type, and file signature on the server.
- Generate server-side object identifiers; do not use user filenames as storage paths.
- Store documents in private storage with least-privilege access and retention/deletion policy.
- Record uploader, institution, document type, timestamp, content hash, extraction state, and provenance.
- Define malware scanning and quarantine behavior before extraction.

**Acceptance evidence:** upload validation tests, private-storage policy, access-control tests, audit trail, and retention policy.

### BE-03 — Extraction and evidence provenance

- Extract text while preserving page and section references.
- Track extraction tool/version, document hash, and extraction status.
- Reject empty, corrupt, encrypted, or unsupported documents with explicit errors.
- Store each evidence passage with a stable ID, source document ID, page, section, and exact text span.
- Never fabricate passages, page numbers, split labels, or source metadata.

**Acceptance evidence:** extraction fixtures, traceability checks back to source files, and failure-case tests.

### BE-04 — Research assessment pipeline

- Freeze and version the approved research methodology before scoring.
- Define framework indicators and approved weights for WURI, THE, QS, and UI GreenMetric.
- Version the Enhanced SBERT model, preprocessing, embedding configuration, and retrieval parameters.
- Implement EQAM dimensions and AES only from the approved operational definitions.
- Implement framework-constrained AHP and TOPSIS only from approved formulas, consistency rules, and fixed anchors.
- Derive RRS, ARRS, and best-fit decisions from the approved specification.
- Separate development/test corpora from research evaluation data; prevent data leakage.

**Acceptance evidence:** methodology-to-code traceability, reproducible calculations, baseline/ablation results, expert-validation records, and independent research review.

### BE-05 — API contract and frontend integration

- Implement `POST /api/upload` only after BE-01 through BE-04 have approved contracts.
- Return typed, versioned responses matching `docs/assessment-api-contract-proposed.md`.
- Include explicit request IDs, assessment IDs, methodology/model/extractor/contract versions, processing status, and source provenance references. The current contract draft prefers asynchronous acceptance with no scores returned until completion; finalize state names, polling/notification, idempotency, typed error envelopes, and retry semantics before implementation.
- Return non-success responses when extraction, evidence, or scoring is incomplete; never return placeholder scores.
- Add authenticated endpoints for assessment retrieval, evidence, history, and XAI only when each is authorized.

**Acceptance evidence:** contract tests, authorization tests, malformed-response tests, and traceability tests.

### BE-06 — Database and operations

- Design PostgreSQL schema and migrations only after data ownership, retention, and access requirements are approved.
- Use least-privilege database roles and server-side secret management.
- Never expose service-role credentials to browser code.
- Add backup, restore, audit, monitoring, and incident-response procedures.
- Keep production and research datasets separated where required.

**Acceptance evidence:** reviewed schema, migration plan, least-privilege review, restore test, and owner approval.

## 3. Reviewable design artifacts now available

These specifications were added for review while the hold remains active:

- `docs/authentication-contract-proposed.md`: proposed server-managed sessions, endpoint surface, role checks, CSRF/CORS, and fail-closed behavior.
- `docs/database-schema-proposed.md`: proposed logical tenant-scoped entities, evidence provenance, assessment versioning, audit events, and server-enforced access matrix.
- `docs/assessment-api-contract-proposed.md`: a proposed future upload request/response shape and required failure semantics; it is not a current frontend contract.

They are deliberately logical/proposed designs. They do not establish an approved identity provider, database, storage service, methodology, or runtime.

## 4. Required authorization gates

| Gate | Required evidence | Current status |
|---|---|---|
| Security clearance | Independent assessment of suspicious commit, provenance, and possible prior execution | OPEN |
| Credential containment | Supabase owner confirms exposed key revoked and dependent services updated | OPEN |
| Dependency approval | Independent review of manifests, lockfiles, and dependency provenance | OPEN |
| Implementation authorization | Written approval for backend source changes on a specified isolated branch | NOT GRANTED |
| Runtime authorization | Separate written approval for dependency installation, local startup, lint, tests, and builds | NOT GRANTED |
| Research-data authorization | Approved methodology, corpus, privacy, and data-processing permission | NOT GRANTED |
| Production authorization | Independent release review and explicit deployment approval | NOT GRANTED |

## 5. Safe next actions

While the hold remains active, permitted work is limited to static repository inspection and documentation that does not execute project code or trigger workflows. Preserve the suspicious history as evidence. Do not merge this recovery branch into `main`.

Once security clearance is independently documented, request each authorization separately and record the exact commit, scope, environment, and permitted commands. A general request to continue work is not a substitute for those approvals.

## 6. Definition of done

The backend is not complete merely because endpoints respond. Completion requires:
- server-enforced authentication and authorization;
- secure document intake and private storage;
- source-traceable extraction and evidence;
- approved, versioned research calculations;
- API contract and automated tests run under explicit authorization;
- independent security and research review;
- separately approved deployment.

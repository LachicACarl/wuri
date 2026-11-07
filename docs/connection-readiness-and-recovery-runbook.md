# WURI Connection Readiness and Recovery Runbook

**Status: HOLD — NOT CONNECTED END-TO-END**  
**Original remediation branch:** `security/recovery-remove-obfuscated-vite-config` (historical; not the current isolated clean-root snapshot)  
**Current isolated review snapshot:** `security/clean-root-quarantine-2026-11-07`  
**Supabase project ref:** `oxvejessjvlsyptqfyyc`  
**This document is a static planning artifact. It does not authorize runtime execution, database access, migrations, or deployment.**

## 1. What has been verified

- The Supabase account named `wuri` lists project `oxvejessjvlsyptqfyyc`.
- The project was reported as `ACTIVE_HEALTHY`, region `ap-northeast-2`, PostgreSQL 17.
- The frontend exists under `university-ranking-dss/`.
- The earlier frontend prototype expected `POST /api/upload`; that request, form, and file input were subsequently removed from the current clean-root snapshot. No upload endpoint exists. The route appears only as a proposed future backend target in design documents.
- No backend/API implementation was found in the inspected recovery-branch tree.
- Authentication remains intentionally locked pending an approved server-side implementation.
- The original recovery branch inherits suspicious history and must not be merged. The separate clean-root snapshot was created with an orphan root commit, but copied source remains unreviewed and is not cleared to execute.

Project listing/status confirms account access and project existence only. It does not confirm application connectivity, database schema readiness, RLS correctness, storage policies, auth configuration, API availability, or key rotation.

## 2. Connection architecture required

Browser (React/Vite)
  -> approved HTTPS backend API
  -> server-side authentication and authorization
  -> private document storage + PostgreSQL access using least-privilege server credentials
  -> extraction and traceable evidence pipeline
  -> approved methodology/model pipeline
  -> typed assessment API response (proposed; contract not finalized)
  -> frontend results/evidence views (not present in current snapshot)

The browser may use a Supabase publishable/anon key only where appropriate under reviewed RLS policies. A service-role/secret key must never be bundled into frontend code, Vite environment variables exposed to the browser, or checked into Git.

## 3. Gate zero — security and authorization (currently OPEN)

Before backend code or runtime testing:
1. Independent reviewer documents review of commit `8595267641138faf240e9bd0a27b9f565bf3734f`, its Vite config payload, provenance, and possible prior execution.
2. Authorized Supabase owner confirms the previously exposed service-role key was revoked/disabled.
3. Owner confirms replacement secrets are newly generated, stored server-side, and dependent services have been updated or disabled.
4. Reviewer/owner records exact permitted branch, commit, environment, data class, allowed commands, and stop conditions.
5. Separate approval authorizes implementation and runtime testing. This is distinct from security clearance.
6. Separate approval is obtained before any real institutional/research data, production database changes, or deployment.

Until all relevant approvals exist, do not install packages, execute scripts, run the Vite app, run tests/builds, trigger CI, inspect database tables/logs/storage, configure Supabase Auth, apply SQL, or deploy.

## 4. Backend implementation sequence after authorization

### BE-01 — Authentication and authorization
- Select an institution-approved identity provider/session model.
- Enforce identity, membership, role, institution scope, resource ownership, CSRF, origin, and rate limiting server-side.
- Keep frontend locked until a real session endpoint confirms identity.
- Add tests for unauthenticated, unauthorized, cross-institution, expired-session, and privilege-escalation cases.

### BE-02 — Upload and private storage
- Define file types and limits.
- Validate size, extension, MIME, and file signature server-side.
- Quarantine/scan as required by approved policy.
- Store files in a private bucket under server-generated object keys.
- Record hash, uploader, institution, type, size, and processing state.
- Test cross-tenant access denial and unauthorized downloads.

### BE-03 — Extraction and provenance
- Extract only from the uploaded bytes.
- Preserve page/section references and content hashes.
- Version extractor and record status/errors.
- Never fabricate school names, passages, pages, metadata, or evidence splits.

### BE-04 — Approved scoring
- Freeze the research method, indicators, weights, anchors, thresholds, model versions, and evaluation partitions before implementation.
- Calculate only from traceable evidence and the approved algorithm.
- Return no scores when required inputs or evidence are missing.
- Keep synthetic development fixtures separate from real research data.

### BE-05 — API integration (proposed; not implemented)
- After separate approvals, finalize the proposed asynchronous API lifecycle, request/assessment IDs, idempotency semantics, status model, typed errors, and completed-result schema.
- Only then implement authenticated upload and approved retrieval routes.
- Version request/response schemas and include source provenance plus extractor/model/methodology/contract versions.
- Do not return scores in an accepted/processing response. Publish a result only after all approved evidence and methodology requirements pass.
- Fail closed on incomplete extraction or assessment; no placeholder results.
- Add API contract, authorization, malformed payload, retry/idempotency, and provenance tests.

### BE-06 — Database and operations
- Review the logical schema before creating migrations.
- Use least-privilege database roles, reviewed RLS policies, private storage policies, server-side secrets, audit records, backup/restore, retention, and incident response.
- Apply migrations only to an expressly authorized isolated environment after backup/rollback review.

## 5. Post-approval connection verification

Only after explicit runtime/database authorization, verify in this order:
1. Confirm configured backend URL and browser-safe public Supabase key without printing secrets.
2. Verify backend health endpoint and version.
3. Verify authentication session and protected-route denial.
4. Verify database connectivity with a non-sensitive readiness check.
5. Verify RLS denies anonymous and cross-institution access.
6. Verify private bucket access denies public/unauthorized reads.
7. Upload a synthetic fixture and trace its hash -> stored object -> extraction -> evidence references.
8. Run only approved synthetic-data scoring fixtures and compare deterministic outputs to reviewed golden cases.
9. Verify frontend receives the real API response and renders evidence/assessment records.
10. Capture sanitized logs and test results; do not use real institutional data until separately approved.

## 6. Current acceptance status

| Component | Status |
|---|---|
| WURI Supabase project visible to connected account | VERIFIED |
| Supabase application credentials/rotation | UNVERIFIED |
| Database schema and migrations | NOT INSPECTED / NOT IMPLEMENTED |
| RLS and storage policy | NOT INSPECTED / NOT VERIFIED |
| Backend API | NOT FOUND / NOT IMPLEMENTED |
| Server-side authentication | NOT IMPLEMENTED |
| Document upload/extraction | NOT IMPLEMENTED |
| Assessment pipeline | NOT IMPLEMENTED / REQUIRES METHODOLOGY APPROVAL |
| Frontend-to-backend integration | NOT VERIFIED |
| End-to-end runtime test | NOT AUTHORIZED |
| Production deployment | NOT AUTHORIZED |

## 7. Stop conditions

Stop immediately if a secret is found in source/logs, unexpected project identity is observed, RLS permits cross-tenant access, storage is public unexpectedly, document provenance is incomplete, or a result appears without a validated assessment run. Preserve evidence and notify the authorized reviewer/owner.

**No implementation, runtime connection, database inspection/change, credential operation, CI execution, or deployment has been performed by adding this runbook.**


## Current clean-root snapshot correction — 2026-11-07

The current isolated snapshot is `security/clean-root-quarantine-2026-11-07`, not the original recovery branch named above. Its frontend is a static security-hold page only. It contains no upload request or file input, no backend/API handler, no authentication service, no Supabase client, and no assessment implementation. This snapshot is a source-review artifact and is not an operational system.

All implementation, dependency installation, source execution, build/lint/test, CI, Supabase access, migration, real-data processing, and deployment remain unauthorized pending the gates in issue #1.

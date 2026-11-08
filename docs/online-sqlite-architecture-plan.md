# WURI Online + SQLite Architecture Plan

**Status:** PROPOSED — DOCUMENTATION ONLY  
**Branch:** `docs/online-sqlite-architecture-plan`  
**Runtime / implementation authorization:** NOT GRANTED  
**Production authorization:** NOT GRANTED

## 1. Architecture decision

The target is an online React application backed by a FastAPI service. SQLite and uploaded files reside on the backend host's persistent private storage. The browser never connects directly to the database or filesystem.

- Frontend: existing React + Vite application in `university-ranking-dss/`.
- Backend: proposed FastAPI service (not present in the inspected recovery-branch tree).
- Database: SQLite on one persistent backend volume.
- ORM/migrations: SQLAlchemy and Alembic are proposed, subject to dependency and design review.
- Files: private filesystem directory on the same persistent volume or a separately mounted persistent volume.
- Transport: HTTPS to a same-origin or explicitly allowlisted API.
- Supabase: no runtime dependency in the target design.

This plan does not create a backend, database, migration, credential, deployment, or connection.

## 2. Repository facts and discrepancies

Static inspection of `security/recovery-remove-obfuscated-vite-config` found:

- The frontend is under `university-ranking-dss/`.
- Its package manifest contains React, Vite, React Router, Recharts, Tailwind, and ESLint dependencies.
- The documented backend endpoint `POST /api/upload` has no handler in the inspected tree.
- No `backend/app/main.py`, `backend/data/wuri.sqlite3`, or eight SQLite migrations were found at the inspected paths on this branch.
- Existing proposed database and backend documents describe PostgreSQL and must be treated as superseded design proposals, not implemented infrastructure.

The earlier project context mentioned a FastAPI backend, SQLite file, and eight migrations. Their current location and provenance must be established from an authorized trusted source or separate branch before any migration or overwrite. Do not assume they are present in this repository revision.

## 3. Deployment topology

1. Browser loads the static React frontend over HTTPS.
2. Frontend calls FastAPI over HTTPS.
3. FastAPI authenticates the request and enforces role and institution scope.
4. FastAPI reads/writes SQLite on a persistent disk mounted only to the backend.
5. FastAPI stores uploaded files under a private persistent directory using server-generated identifiers.
6. Backups are encrypted and copied off-host; restore is periodically tested.

SQLite must not be placed on an ephemeral filesystem. Start with one backend instance and one writer boundary. Do not horizontally scale multiple application instances that each have a separate SQLite file. If concurrent writes or availability requirements exceed SQLite's practical limits, stop and reassess the database choice rather than silently adding a paid service.

## 4. Proposed backend structure (not created)

```text
backend/
  app/
    main.py
    api/
      routes/
    core/
      config.py
      security.py
    db/
      base.py
      session.py
      models/
    services/
    schemas/
  migrations/
  tests/
  data/                 # runtime only; never commit
  storage/              # runtime only; never commit
```

The actual structure should be reconciled with any trusted existing backend before creation.

## 5. Data and migration principles

- Preserve all source databases and migration files before any conversion.
- Establish the authoritative schema and migration history from the trusted source revision.
- Do not recreate, squash, reorder, or silently skip existing migrations.
- Enable SQLite foreign-key enforcement on every connection.
- Use transactions and explicit migration versioning.
- Use WAL only after workload and backup implications are reviewed.
- Keep runtime database and uploaded files outside public/static directories and out of Git.
- Use server-generated opaque file identifiers; never construct storage paths from user filenames.
- Record SHA-256, uploader, institution, content type, byte size, timestamp, and provenance for uploads.
- Never fabricate institutional evidence, page references, assessment values, or scores.

No real institutional data may be imported or processed until data-owner and research approvals are recorded.

## 6. Authentication and authorization

Use server-managed sessions with opaque, revocable identifiers in Secure, HttpOnly cookies and a reviewed SameSite/CSRF policy. Password-based identity, if approved, must use a current password-hashing implementation such as Argon2id. Do not store passwords, bearer tokens, or session identifiers in browser localStorage.

Every protected endpoint must enforce identity, active membership, role, institution ownership, and relevant research authorization on the server. Frontend route guards are presentation only. Login and recovery endpoints require rate limiting, generic error messages, audit logging, and session invalidation behavior.

No demo administrator account or default password is permitted.

## 7. File intake controls

- Allowlist formats and enforce request/file size limits.
- Check extension, detected MIME type, and file signature.
- Generate opaque storage names and prevent path traversal.
- Store files privately, outside the web root.
- Quarantine and scan uploads according to an independently reviewed malware-scanning policy.
- Do not extract or process a file until the required validation/scanning gate passes.
- Enforce institution-level access on every download.
- Define retention, deletion, legal hold, backup, and restore rules before production use.

## 8. API integration plan

The frontend currently expects `POST /api/upload`. Before implementing it, approve a versioned request/response contract covering:

- authenticated uploader and institution context (derived server-side, not trusted from request body);
- file validation and upload receipt;
- extraction status and source provenance;
- assessment status and methodology/model version;
- explicit failure codes for unsupported, corrupt, empty, or unscannable files;
- request/correlation identifiers.

Return no RRS/ARRS/EQAM or framework score unless an approved, versioned research pipeline has completed with traceable evidence. Incomplete work must remain pending/failed, not receive placeholder values.

## 9. Operational requirements

- Persistent disk mounted to the backend service.
- Restrictive filesystem permissions for database, storage, and backups.
- HTTPS and explicit CORS allowlist.
- Secret management through the hosting provider's private environment configuration; no secrets in source or browser bundles.
- Encrypted off-host backups with documented retention and tested restoration.
- Health/readiness endpoints that do not disclose secrets, filesystem paths, or sensitive configuration.
- Monitoring for failed authentication, authorization denials, upload abuse, database errors, disk capacity, and backup failures.

Free-tier hosting must be checked for persistent-disk availability, limits, sleeping behavior, and backup feasibility before selection. Do not assume a free plan is production-suitable.

## 10. Ordered implementation gates

| Gate | Work | Required approval |
|---|---|---|
| G0 | Independent security clearance for suspicious revision, forced-update provenance, and prior-execution assessment | Independent security reviewer |
| G1 | Confirm trusted backend source and existing SQLite/migration provenance | Repository owner + reviewer |
| G2 | Approve schema, auth, upload, and assessment contracts | Technical/data owners |
| G3 | Authorize backend/frontend source changes on a named isolated branch | Written implementation authorization |
| G4 | Authorize dependency installation and isolated synthetic-data tests | Separate runtime authorization |
| G5 | Authorize real-data processing and research scoring | Research/data owner |
| G6 | Authorize production deployment and persistent storage | Explicit production approval |

A user request to continue is not independent security clearance. No gate is implied by completion of an earlier gate.

## 11. Current hold and stop conditions

The repository's existing security hold remains active. This documentation branch does not lift it.

Until the relevant approvals are recorded, do not install dependencies, run builds/tests, start services, execute historical revisions, trigger CI, access providers, create/modify databases, migrate data, process real institutional evidence, or deploy.

Stop if a secret is discovered in source/history, unexpected code or repository identity appears, a migration cannot be reconciled, institution boundaries are ambiguous, or any assessment output lacks approved provenance. Preserve evidence and refer the issue to the authorized security/data owner.

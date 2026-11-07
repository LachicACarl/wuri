# WURI University Ranking Readiness DSS

This repository currently contains a React/Vite frontend in `university-ranking-dss/`.

## Frontend location

- Application entry: `university-ranking-dss/src/main.jsx`
- Main routes and views: `university-ranking-dss/src/App.jsx`
- Vite configuration: `university-ranking-dss/vite.config.js`
- Dependencies: `university-ranking-dss/package.json`
- Dependency lockfile: `university-ranking-dss/package-lock.json`

Install/build/test commands are intentionally not documented as approved execution steps while the repository security hold is active.

## Current security and integrity status

**HOLD — NO-GO.** This recovery branch is an isolated remediation candidate, not a security-cleared or production-ready branch.

- The suspicious obfuscated code was removed from the current recovery branch's Vite configuration. The original commit and `main` history remain preserved for investigation.
- The tracked root `node_modules/` directory was removed from the current recovery branch tree. Dependencies must be reviewed and restored only from the committed lockfiles after explicit authorization.
- A root `.gitignore` excludes dependency directories, build output, local environment files, and logs.
- The frontend no longer generates readiness scores from hardcoded sample passages and file metadata. It requires a structured response from the assessment API.
- The frontend's hardcoded demo login was removed. Sign-in is disabled until an approved server-side authentication service is implemented and reviewed.

## Assessment integrity

The frontend must not present sample passages, filename-derived institution names, simulated EQAM values, or deterministic placeholder calculations as actual institutional evidence or Ranking Readiness Scores (RRS/ARRS).

A backend response is not automatically valid research output merely because it is returned by an API. Assessment methodology, data provenance, expert validation, authorization, and research gates must be independently approved before real scoring or reporting.

## Connection readiness and recovery

- `docs/connection-readiness-and-recovery-runbook.md` — verified connection boundary, security gates, backend implementation order, and post-approval end-to-end verification sequence. The WURI Supabase project is visible to the connected account, but this does not mean the application is connected to a working backend.

## Proposed backend design artifacts

The following documents define reviewable designs only; none is implemented or approved for execution:

- `docs/authentication-contract-proposed.md` — server-side identity, sessions, authorization, and browser protections.
- `docs/database-schema-proposed.md` — logical PostgreSQL entities, tenant boundaries, provenance, and access matrix.
- `docs/assessment-api-contract-proposed.md` — current frontend upload-response expectations and failure behavior.
- `docs/backend-implementation-plan.md` — dependency-ordered backend workstreams and authorization gates.
- `docs/security-hold-clearance-evidence-checklist.md` — external evidence required to reconsider the security hold.

## Recovery restrictions

Until written security clearance and separate implementation/runtime authorization are recorded:

- Do not merge this branch into `main`.
- Do not execute the suspicious historical revision.
- Do not install dependencies, start the application, run builds/tests, or trigger CI workflows.
- Do not connect to Supabase, use exposed credentials, migrate real data, or deploy.
- Do not treat this repository README or recovery commits as independent security clearance.

## Next required evidence

1. Independent review of suspicious commit provenance, behavior, and possible prior execution.
2. Owner-confirmed revocation of the exposed Supabase service-role key and confirmation that dependent services no longer use it.
3. Independent review of the remaining dependency manifests and lockfiles.
4. Approved server-side authentication and assessment API contracts.
5. Separate written authorization for implementation, isolated synthetic-data testing, real-data work, and production deployment.

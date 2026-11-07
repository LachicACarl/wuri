# WURI University Ranking Readiness DSS

This repository currently contains a quarantined React/Vite frontend snapshot in `university-ranking-dss/`. Its application entry is intentionally a non-operational security-hold screen. It is not a functioning ranking readiness system.

## Frontend location

- Application entry: `university-ranking-dss/src/main.jsx`
- Main routes and views: `university-ranking-dss/src/App.jsx`
- Vite configuration: `university-ranking-dss/vite.config.js`
- Dependencies: `university-ranking-dss/package.json`
- Dependency lockfile: intentionally excluded from this quarantine snapshot pending dependency provenance review

Install/build/test commands are intentionally not documented as approved execution steps while the repository security hold is active.

## Current security and integrity status

**HOLD — NO-GO.** This recovery branch is an isolated remediation candidate, not a security-cleared or production-ready branch.

- The current clean-root snapshot contains a declarative Vite configuration without the previously identified obfuscated loader. The original suspicious commit remains preserved in `main` history for independent investigation. The original commit and `main` history remain preserved for investigation.
- The clean-root snapshot contains no tracked `node_modules/` directory. Dependencies must be independently reviewed and a lockfile generated only after explicit authorization.
- A root `.gitignore` excludes dependency directories, build output, local environment files, and logs.
- The current `src/App.jsx` contains only a static security-hold screen. It has no upload control, API request, result renderer, session state, scoring constants, or Supabase client.
- Do not use this snapshot to upload documents or enter credentials. Authentication and all operational features are unavailable.

## Assessment integrity

The frontend must not present sample passages, filename-derived institution names, simulated EQAM values, or deterministic placeholder calculations as actual institutional evidence or Ranking Readiness Scores (RRS/ARRS).

A backend response is not automatically valid research output merely because it is returned by an API. Assessment methodology, data provenance, expert validation, authorization, and research gates must be independently approved before real scoring or reporting.

## Connection readiness and recovery

- `docs/connection-readiness-and-recovery-runbook.md` — verified connection boundary, security gates, backend implementation order, and post-approval end-to-end verification sequence. The WURI Supabase project is visible to the connected account, but this does not mean the application is connected to a working backend.
- `docs/static-system-audit-2026-11-07.md` — static frontend/architecture audit with severity-ranked findings, evidence locations, structural inventory, and remediation order. No runtime commands were executed.

## Proposed backend design artifacts

The following documents are proposals and review artifacts only. They are not deployed API specifications, migrations, or implemented backend features:

- `docs/authentication-contract-proposed.md` — server-side identity, sessions, authorization, and browser protections.
- `docs/database-schema-proposed.md` — logical PostgreSQL entities, tenant boundaries, provenance, and access matrix.
- `docs/assessment-api-contract-proposed.md` — proposed future assessment API contract; no corresponding endpoint is implemented.
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


## Current implementation boundary

Only the static React security-hold screen is present in this branch. The proposal documents describe future work and must not be treated as implemented services. The frontend contains no live backend, login, upload, scoring, or Supabase operations. This branch is not approved for production use.

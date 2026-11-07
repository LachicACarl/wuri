# WURI current source and verification index

**Branch:** `security/clean-root-quarantine-2026-11-07`  
**Review model:** moving branch reference; reviewers must record the live commit SHA they actually inspect.

## Current application source

- `university-ranking-dss/src/main.jsx` — React DOM entry, browser router, and CSS import.
- `university-ranking-dss/src/App.jsx` — non-operational security-hold screen.
- `university-ranking-dss/src/index.css` — global CSS and Tailwind import.
- `university-ranking-dss/vite.config.js` — declarative React/Tailwind Vite plugins.
- `university-ranking-dss/eslint.config.js` — lint configuration.
- `university-ranking-dss/package.json` — frontend package manifest; lockfile intentionally absent.

## Current status

This branch contains a quarantined JavaScript/React frontend only. There is no server/API, authentication, upload, database adapter, Supabase client, private storage, extraction pipeline, ranking engine, or persistent history.

## Reports and proposals

- [Static audit](static-system-audit-2026-11-07.md)
- [Static diagnostics](static-diagnostics-2026-11-07.md)
- [Security clearance checklist](security-hold-clearance-evidence-checklist.md)
- [Connection runbook](connection-readiness-and-recovery-runbook.md)
- [Backend implementation plan](backend-implementation-plan.md)
- [Proposed assessment API](assessment-api-contract-proposed.md)
- [Proposed authentication contract](authentication-contract-proposed.md)
- [Proposed database schema](database-schema-proposed.md)

All four backend design artifacts are unapproved proposals. In particular, the assessment API’s asynchronous `202` acceptance pattern is illustrative; session policy, idempotency scope, record state machines, identity mapping, completed-result schema, scoring formulas, and retention rules remain open decisions.

## Review cautions

The project-specific Supabase status recorded in older issue/runbook notes is historical context, not a current provider verification. Do not infer that the project is active, connected, rotated, or safe from this repository snapshot. The API, authentication, database, and backend documents are proposals and not approved specifications.

## What has not been verified

No JavaScript parse/compile, dependency install, lockfile generation, dependency advisory scan, ESLint, Vite build, browser test, unit/integration/E2E test, GitHub Actions, Supabase inspection, migration, or deployment has been performed.

Do not treat static checks as runtime acceptance. Keep `main` unchanged until independent security review, key-containment evidence, and separate runtime/implementation authorization are documented.


## Reproducible review handoff

The current clean-root branch is a static quarantine snapshot, not a runnable release candidate. Reviewers should record the exact branch head SHA and the file blob SHAs they inspect; a branch name alone is not an immutable review target. The last recorded baseline in this index is not a substitute for reading the live ref.

The frontend manifest currently declares development, build, lint, and preview scripts, but no lockfile or automated test script exists. Their presence is not evidence of a working application, and none was executed during static review. Dependency restoration, lockfile creation, lint/build, local startup, CI, and tests require separate written authorization after security clearance.

A review of this snapshot must not be described as a review of the historical `main` code, and clearing the historical configuration must not automatically authorize this orphan-lineage snapshot to run. Record the exact implementation branch/base commit and allowed commands separately before any executable work.

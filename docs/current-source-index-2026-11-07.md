# WURI current source and verification index

**Branch:** `security/clean-root-quarantine-2026-11-07`  
**Review model:** moving branch reference; reviewers must record the live commit SHA they actually inspect.

## Current application source

- `university-ranking-dss/index.html` — standalone static HTML/CSS security-hold page; contains no module script or React mount.
- `university-ranking-dss/src/main.jsx` — **absent from the tracked tree**; no React DOM entrypoint exists.
- `university-ranking-dss/src/App.jsx` — hold-screen React component, currently unmounted and not loaded by `index.html`.
- `university-ranking-dss/src/index.css` — global CSS and Tailwind import.
- `university-ranking-dss/vite.config.js` — declarative React/Tailwind Vite plugins.
- `university-ranking-dss/eslint.config.js` — lint configuration.
- `university-ranking-dss/package.json` — frontend package manifest; lockfile intentionally absent.

## Current status

This branch actively serves a standalone static HTML/CSS hold page. A React component and Vite configuration are also tracked, but the React component is not mounted: `src/main.jsx` is absent and `index.html` contains no module script. Do not describe the current page as a functioning React frontend. There is no server/API, authentication, upload, database adapter, Supabase client, private storage, extraction pipeline, ranking engine, or persistent history.

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


## Last reconciled static review — 2026-11-08

The live HTML still has no favicon link; `public/favicon.svg` exists but is not referenced by `index.html`. The active page is standalone HTML/CSS and the tracked React hold component remains unmounted. The security-hold issue still has no independent reviewer or authorized Supabase-owner confirmation in its comments as of this review. No implementation/runtime authorization is evidenced by this documentation update. See `docs/static-diagnostics-2026-11-07.md` for the source-level limitation and `docs/security-hold-clearance-evidence-checklist.md` for required evidence.

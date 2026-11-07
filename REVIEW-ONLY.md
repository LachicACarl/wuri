# WURI Clean-Root Review Package

**Review status:** Draft / review only  
**Snapshot branch:** `security/clean-root-quarantine-2026-11-07`  
**Snapshot branch:** `security/clean-root-quarantine-2026-11-07` (review the live branch head; do not rely on a pinned historical SHA in this handoff)  
**Main branch:** must remain unchanged pending security clearance.

## PR scope warning

This PR changes **only this `REVIEW-ONLY.md` file**. It does not carry the clean-root source snapshot or its remediation commits as a PR diff. The snapshot is a separate orphan-lineage branch and must be reviewed directly using the branch tree and its source index. This PR is not a complete code-review bundle and is not mergeable into `main` by intent.

## Review entry points

- [Repository overview](README.md)
- [Frontend technology inventory](university-ranking-dss/README.md)
- [Static system audit](docs/static-system-audit-2026-11-07.md)
- [Static diagnostics and unperformed checks](docs/static-diagnostics-2026-11-07.md)
- [Security hold clearance checklist](docs/security-hold-clearance-evidence-checklist.md)
- [Connection readiness runbook](docs/connection-readiness-and-recovery-runbook.md)
- [Proposed backend implementation plan](docs/backend-implementation-plan.md)
- [Proposed authentication contract](docs/authentication-contract-proposed.md)
- [Proposed assessment API contract](docs/assessment-api-contract-proposed.md)
- [Proposed database schema](docs/database-schema-proposed.md)

## Current source state

The clean-root branch currently contains a non-operational React/JavaScript frontend security-hold screen. It has no implemented backend, authentication, upload, private storage, document extraction, Supabase integration, assessment algorithms, or persistent history.

The proposed backend/auth/database files are design artifacts only. The dependency lockfile is absent; no dependency installation, build, lint, test, or runtime validation has been performed.

## Review checklist

- [ ] Independently inspect the suspicious historical Vite configuration and its provenance.
- [ ] Assess possible prior execution on developer machines, CI, and deployment environments.
- [ ] Confirm through the authorized Supabase owner that the exposed service-role key has been revoked and replacement custody is secure.
- [ ] Review the exact clean-root tree and identify any residual source or dependency concerns.
- [ ] State whether isolated implementation is approved and list permitted commands/environment.
- [ ] Keep real institutional data, Supabase writes, production, and deployment separately gated.

## Merge restriction

This review package is not a request to merge into `main`. Do not merge the clean-root branch or this review branch into `main` until independent security clearance, credential containment evidence, and separate implementation/runtime authorization are documented in issue #1.

No credentials, tokens, or private institutional data belong in review comments.

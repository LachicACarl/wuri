# WURI Static Diagnostics and Error-Check Status

**Date:** 2026-11-07  
**Branch:** `security/clean-root-quarantine-2026-11-07`  
**Classification:** Static source/config review only — not a runtime test report.

## Executive result

The current branch is a quarantined React/Vite frontend snapshot. The application intentionally renders a security-hold screen. The initial audit report described the older prototype in parts; this report is the current-state source inventory.

## Confirmed source-level findings

| Severity | Finding | Evidence / effect | Status |
|---|---|---|---|
| BLOCKER | No backend/API implementation | No backend/server source tree or API route is present | Confirmed absent |
| BLOCKER | Authentication is unavailable | No auth client, session endpoint, or server authorization exists | Confirmed absent |
| BLOCKER | Document upload is unavailable | Current UI contains no file input, FormData, or upload request | Confirmed absent |
| BLOCKER | Assessment pipeline is unavailable | The current app contains no score result objects, score fields, algorithm imports, or calculation functions | Confirmed absent by static source inspection |
| BLOCKER | Database integration is unavailable | No Supabase client, SQL migration, or DB adapter exists in this snapshot | Confirmed absent |
| HIGH | Dependency reproducibility is incomplete | `university-ranking-dss/package.json` exists but no lockfile is tracked | Confirmed |
| HIGH | Toolchain compatibility is unverified | React 18, Vite 8, `@vitejs/plugin-react` 6, ESLint 10, and Tailwind 4 are declared; package resolution and peer/runtime compatibility have not been checked because dependencies were not installed and no lockfile exists | Not tested |
| MEDIUM | No test suite is present | Current tree contains no tracked test source or test script | Static tree/manifest observation |
| HIGH | Runtime/build state is unknown | Dependencies are not installed; scripts have not been run | Not tested |
| HIGH | Security approval is pending | Issue #1 has no independent reviewer or authorized Supabase-owner approval comment | Pending |
| HIGH | Exposed credential containment is unverified | No owner confirmation of revocation/replacement is recorded | Pending |
| MEDIUM | Frontend is intentionally non-operational | App.jsx renders a hold message on all routes | By design |
| MEDIUM | Remaining hero asset is not referenced by current App.jsx | Binary asset retained; no safe binary editing performed through text-only operations | Static observation |

## Checks performed in this review

- Re-read the tracked application source/configuration files and relevant review documentation in the current tree. Some binary assets were identified by tree metadata only.
- Confirmed the app entry imports React, React DOM, React Router, and the global CSS file.
- Confirmed the Vite config contains the standard React and Tailwind plugins, without the previously observed dynamic code-loader pattern in this branch's current Vite config.
- Confirmed there is no TypeScript source, Python source, backend directory, Supabase client import, upload handler, file input, or score computation in the current app source.
- Confirmed HTML metadata title, description, and noindex directive are present.
- Confirmed the dependency lockfile and node_modules are absent.
- Read the package manifest and noted declared React/Vite/ESLint/Tailwind major versions; compatibility is intentionally unverified because no dependency installation or package-manager resolution was performed.
- Confirmed the package manifest has dev/build/lint/preview scripts but no test script; the current tree contains no test source files.
- Confirmed proposed design documents are not implementation artifacts.
- Confirmed the `main` ref has not been changed by this review.
- Confirmed the source-review branch head at this check is recorded in the GitHub ref; this report should be reviewed together with the live branch, not treated as a pinned immutable snapshot.

## Checks not performed — do not interpret as passed

- JavaScript/JSX parsing or compilation.
- Dependency installation, integrity/advisory audit, or lockfile generation.
- ESLint, Vite build, preview, or application startup.
- Unit, integration, API, browser, accessibility, or end-to-end tests.
- GitHub Actions execution or workflow reruns.
- Supabase authentication, database, table, RLS, storage, logs, or credential inspection.
- Key revocation/rotation, migrations, real data processing, or deployment.

## Required next steps

1. Obtain independent written review of the suspicious historical Vite configuration and possible prior execution.
2. Obtain written confirmation from the authorized Supabase owner that the exposed service-role key is revoked and replacement credentials are stored securely.
3. Obtain explicit authorization naming the exact clean-root branch/commit, isolated environment, permitted dependency install and test commands, data class, and stop conditions.
4. Only after authorization, resolve the declared toolchain against an approved runtime version, review peer-dependency compatibility and advisories, restore dependencies from an independently reviewed lockfile, then run lint/build and add an authorized test suite before claiming test coverage.
5. Keep production, real institutional data, database writes, and deployment separately gated.
6. Re-verify the current branch SHA before external review; the snapshot branch may advance after this report.

**Conclusion:** This review found no new executable defect that can responsibly be confirmed without running the project. It did find and correct stale documentation in this branch. The application itself remains intentionally unavailable. 


## Contract review boundary — 2026-11-07

The backend implementation plan, assessment API, authentication, and database schema documents are design proposals only. The proposed asynchronous `202 Accepted` response is illustrative, not an approved HTTP contract. Completed-result fields, score units/ranges, required-framework completeness, status names/transitions, polling/notification, idempotency scope/retention/conflict behavior, identity-provider issuer mapping, session lifetimes/revocation propagation, physical DB constraints, retention/deletion, and research methodology remain unresolved. Do not implement from example JSON or treat example values/roles as institution-approved decisions.

## Review package / pull-request comparison note — 2026-11-07

PR #2 currently targets `security/clean-root-quarantine-2026-11-07` and its head branch adds only `REVIEW-ONLY.md`; GitHub reports one changed file. It does not contain the full source remediation diff. The clean-root branch advances independently of this report; reviewers must verify the live branch head before review and inspect the complete clean-root tree directly. Do not rely on an old pinned SHA in this report. PR #2 is a reviewer-index handoff only, not a source-remediation PR. Do not merge it into `main`.


## Historical suspicious configuration — exact static evidence

The historical `main` file `university-ranking-dss/vite.config.js` at commit
`8595267641138faf240e9bd0a27b9f565bf3734f` has blob SHA
`fd3346ae65a2bea4b58014fff39b09668628bc39`.
Static inspection confirms that this file imports Node's `createRequire`, constructs an obfuscated loader,
and invokes `BrW(2333)` at module evaluation time. The complete payload is not reproduced here.
This is a high-risk opaque execution path; its exact behavior and any prior execution remain undetermined.

The current clean-root branch's `university-ranking-dss/vite.config.js` is a separate declarative
configuration (blob SHA `c676acd6ef3824d7097dc60fa655881a040d39d3`). The clean-root branch is
an orphan-lineage review snapshot, not proof that the historical revision is safe or that the copied
application source is approved to execute.

**Required independent review:** preserve and inspect the full historical commit/tree/blob using
non-executing methods; establish provenance, identify the loader's complete behavior and any network,
filesystem, process, credential, or persistence actions; examine relevant CI, workstation, account,
and deployment evidence for possible prior execution; document evidence sources and limitations.
Do not execute the file, install its dependencies, or use an online/deobfuscation service that runs it.


## Execution-readiness handoff

The current `university-ranking-dss/` tree is a hold-screen snapshot, not the earlier operational prototype. Do not describe it as an application with repairable login/upload/scoring flows: those flows are absent by design. The current source-level limitation is architectural incompleteness, not a diagnosed runtime defect.

The package manifest declares four scripts (`dev`, `build`, `lint`, `preview`) but this review did not invoke them. No lockfile is tracked, so the dependency graph is not pinned. A future authorized validation must use an isolated disposable environment, review and pin exact dependency versions first, produce a lockfile through the approved package manager, inspect the resulting diff, and then run lint/build against the exact reviewed commit. Record tool versions, command, exit code, and log reference; do not infer success from a manifest or static source inspection.

The current page is intentionally non-operational. Returning the UI to an active product requires a separately approved implementation plan for identity/session management, server-side authorization, private document intake, evidence extraction/provenance, approved scoring methodology, database design, API contracts, and automated tests. The proposal documents in this branch are not implementation authorization.

**Do not create a lockfile, install packages, run scripts, or trigger CI as part of this static-only review.**

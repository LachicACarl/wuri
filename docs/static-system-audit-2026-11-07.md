# WURI DSS Static System Audit — 2026-11-07

**Target:** `security/clean-root-quarantine-2026-11-07`  
**Historical context:** `security/recovery-remove-obfuscated-vite-config` (legacy branch; not current source)  
**Audit type:** GitHub source/tree inspection only  
**Status:** HOLD — NO-GO; not a runtime test, penetration test, build, lint, or database audit  
**Current state:** security-hold frontend snapshot only

## Executive finding

The inspected clean-root branch contains a minimal React/Vite frontend that renders a security-hold notice on every route. It contains no backend, API handler, authentication service, Supabase client, database migrations, document upload, extraction pipeline, assessment algorithms, or automated tests. It is intentionally non-operational.

The earlier audit findings below describe the pre-quarantine prototype and must not be read as current source findings. The historical main commit and suspicious configuration require independent investigation; the clean-root snapshot is a separate orphan-lineage review candidate, not security-cleared code.

## Current source inventory

| Area | Current finding |
|---|---|
| App entry | React 18 / JSX, React Router |
| Build/tooling config | Vite with React and Tailwind plugins |
| Styles | Tailwind CSS import and global CSS |
| Frontend authentication | Not implemented |
| Upload/file handling | Not present |
| API/backend | Not present |
| Supabase/database | Not present |
| Extraction/evidence provenance | Not present |
| Scoring and reporting | Not present |
| Tests | No test source files in current tree |
| Dependency lockfile | Absent; reproducibility not established |
| Installed dependencies | Absent from tracked tree; no install permitted |
| Runtime/build/lint | Not executed |

## Historical findings — pre-quarantine prototype only

The following sections from the initial audit described the earlier frontend prototype, before the clean-root quarantine. They are retained for historical remediation context, not as claims about the current `App.jsx`:

- F-01: the old document upload component posted to `/api/upload` without a backend handler.
- F-02: the old protected routes used an authentication flag that could never become true.
- F-03 onward: framework score display, response validation, session-only history, error feedback, and other dormant views were found in the pre-quarantine code.

Those components and associated upload/result logic were subsequently removed from the current clean-root snapshot. Do not use old line references or component names as current source evidence without re-verification.

## Repository entrypoint and static-hosting boundary

The HTML entry `university-ranking-dss/index.html` loads `/src/main.jsx` and references `/favicon.svg`. The tracked favicon exists at `university-ranking-dss/public/favicon.svg`, which matches Vite's public-directory convention by source layout. This is a static path/layout observation only; the path has not been checked by a Vite build or browser request. The favicon artwork is still the Vite starter-style purple/blue mark and is not WURI institutional branding; it is cosmetic cleanup, not a security blocker.

The HTML contains `noindex, nofollow`, but this metadata is not an access-control boundary. The security-hold page must not be treated as private or as protection for confidential content; no confidential content should be hosted in this snapshot.

## Current static security observations

1. Current `src/App.jsx` renders only the hold notice.
2. Current `src/main.jsx` mounts React, React Router, and `src/index.css`.
3. Current `vite.config.js` contains declarative React and Tailwind plugins; no previously identified dynamic code-loader pattern is present in this branch's current file.
4. Current source has no upload endpoint call, file input, FormData, authentication state, Supabase client, score result model, or assessment calculation.
5. `index.html` includes the WURI security-hold title, description, and noindex directive.
6. The package manifest declares React/Vite/Tailwind/Router/icon dependencies, but without a lockfile these are not reproducibly resolved or verified.
7. `src/assets/hero.png` remains in the tree but is not referenced by the current hold-page source; no decision to permanently remove the binary asset is implied.
8. Proposed API, authentication, and database documents are planning artifacts only.

## Severity and disposition

| Severity | Finding | Disposition |
|---|---|---|
| BLOCKER | No operational backend/API | Confirmed absent; implementation not authorized |
| BLOCKER | No authentication/authorization | Confirmed absent |
| BLOCKER | No safe document intake/storage/extraction | Confirmed absent |
| BLOCKER | No approved ranking assessment engine | Confirmed absent; requires methodology approval |
| BLOCKER | No database integration or migrations | Confirmed absent |
| HIGH | Dependency lockfile absent | Not reproducible; review/generation requires approval |
| HIGH | Runtime correctness unknown | Build/lint/tests not run |
| HIGH | Independent security review pending | External evidence required |
| HIGH | Exposed key revocation/replacement unconfirmed | Authorized Supabase-owner evidence required |
| MEDIUM | Unused hero asset remains | Static observation; cleanup decision pending |

## Checks performed

- Inspected the current recursive tree and application/config/documentation source.
- Checked app entry imports, HTML entrypoint references, favicon reference, Vite plugin configuration, package scripts, and package dependency declarations.
- Checked current UI for upload, auth, Supabase, score/result, and dormant prototype constructs.
- Checked documentation against current source and corrected stale historical language.
- Confirmed current branch remains separate from `main`.

## Checks not performed

These checks are **not passed**; they were not run:

- JavaScript/JSX parser or compiler.
- Package installation, dependency resolution, advisory audit, integrity audit, or lockfile generation.
- ESLint or Vite build/preview.
- Browser startup, accessibility, responsive, or manual UI checks.
- Unit, integration, API, E2E, or security tests.
- GitHub Actions execution.
- Supabase Auth, schema, tables, RLS, storage, logs, credentials, or data inspection.
- Key revocation/rotation, migrations, real-data handling, or deployment.

## Required next steps

1. Independent review of suspicious historical commit, forced-update provenance, and possible prior execution.
2. Authorized Supabase-owner confirmation that the exposed service-role credential was revoked and replacement custody is secure.
3. Written approval specifying exact clean-root branch/commit, isolated environment, allowed dependency/runtime commands, synthetic-data boundary, and stop conditions.
4. After authorization, review dependency provenance, create the lockfile, then run lint/build/tests and remediate actual errors.
5. Obtain separate research-method approval before implementing the extraction and assessment pipeline.
6. Obtain separate database and deployment authorizations before any Supabase changes or production activity.

**Conclusion:** This audit records source-level facts only. It does not certify the app as buildable, secure, or operational. The current frontend remains deliberately locked.

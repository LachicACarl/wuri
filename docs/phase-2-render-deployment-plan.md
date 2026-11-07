# Phase 2 — Render Deployment Plan

Status: proposed architecture only. No WURI Render service was found in the
five Render workspaces inspected during the November 2026 read-only account
review. No WURI service was created, no build or deploy was run, and the
security hold remains **NO-GO**.

## Current repository state relevant to deployment

- Frontend is React/Vite under `university-ranking-dss/`. Its package manifest
  defines `npm run build` as `vite build`; a `package-lock.json` is present.
  The checked local Vite config has no custom output directory in the
  inspected text. The normal Vite output is expected to be `dist`, but no
  build has been run to confirm it.
- Backend is FastAPI in `backend/app/main.py`; dependencies are declared in
  `backend/requirements.txt`. The README's command is a local development
  command, `uvicorn app.main:app --reload --port 8000`, and is not a
  production Render start configuration.
- Importing `main.py` constructs `Database()` and `PrivateStorage()` at
  module scope. The current database initializer creates/uses a local SQLite
  path and applies migrations; local storage creates a directory. Deploying
  this version unchanged would therefore not use Supabase and would rely on
  the service filesystem.
- `GET /` returns `{"status": "Backend active"}`. This is a liveness-style
  response and does not check PostgreSQL or object storage.
  `backend/app/deployment_readiness.py` is a command-line preflight, not an
  HTTP readiness endpoint; it writes a storage probe and opens SQLite, so it
  was not run against a production service.
- No Render Blueprint, Dockerfile, Procfile, PostgreSQL config, Supabase
  integration, or production start command was found in the inspected
  project files.

## Render account inspection

The confirmed Render workspace and the four other accessible workspaces were
inspected read-only. The returned services belonged to other repositories
(OFFICIAL-RECORD-BOOK, PLM alumni accountancy, PeakMap, TruthLens, OFWAS, and
htmlfornow). No service was configured to deploy `LachicACarl/wuri`. No
Render service, environment variable, deploy, log, or production setting was
changed during that inspection. This is an account inspection result, not a
guarantee that no service exists in an inaccessible workspace or Render
account.

## Proposed service split

1. **Render Static Site:** React/Vite frontend rooted at
   `university-ranking-dss/`.
2. **Render Web Service:** FastAPI API rooted at `backend/`.
3. **PostgreSQL:** separate development and production projects, after the
   PostgreSQL rewrite and migrations exist.
4. **Private object storage:** separate workstream for uploaded documents and
   research-import files. Do not depend on a Render web service's default
   filesystem for durable uploads.

The package manifest defines `npm run build` as `vite build`; a frontend
lockfile is present. A likely static-site configuration after clearance uses
`university-ranking-dss` as root, runs `npm ci && npm run build`, and
publishes Vite's expected `dist` output. React Router is present, so
client-side route fallback behavior must be configured for the selected host.
Output and rewrite behavior have not been verified by a build or deployment.

For the API, the repository does not define a production start command. The
README command is local development only and includes `--reload`; the source
does not configure a deployment host or port. A production command must be
chosen from the hosting provider's requirements, reviewed against app startup
behavior, and authorized before use. Do not treat a proposed `uvicorn`
command as verified configuration.

## Configuration inventory

### Present in WURI source

- Authentication/session: `WURI_ADMIN_USERNAME`,
  `WURI_ADMIN_PASSWORD`, `WURI_SESSION_SECRET`,
  `SESSION_COOKIE_SECURE`, `WURI_ENVIRONMENT`.
- Current local persistence: `WURI_DATABASE_PATH`,
  `WURI_STORAGE_PATH` — these are SQLite/local-filesystem settings and must
  not be presented as a PostgreSQL/object-storage integration.
- Other source configuration: `WURI_SBERT_MODEL_PATH`,
  `WURI_BASELINE_MODEL_PATH`, `WURI_BASELINE_MODEL_VERSION`,
  `WURI_ENHANCED_MODEL_PATH`, `WURI_ENHANCED_MODEL_VERSION`,
  `WURI_RESEARCH_PROTOCOL_PATH`, `WURI_XAI_EVALUATION_INSTRUMENT`,
  and `WURI_MALWARE_SCANNER_COMMAND`.
- `WURI_MALWARE_SCANNER_VERIFIED` is not accepted by the current readiness
  implementation and must not be set or documented as proof of scanner
  verification. A present executable remains manual-verification-required
  until independently verified.
- Frontend: `VITE_API_BASE_URL`, defaulting to the local API URL. A
  production API URL is a public build-time frontend value. Never put database
  passwords, session secrets, Supabase secret/service-role keys, or other
  backend credentials in a `VITE_*` variable.

### Not implemented; names below are design candidates only

- `DATABASE_URL` or another server-only PostgreSQL connection setting.
- Any Supabase project URL/API key configuration.
- Object-storage endpoint, bucket, access identity, and credential names.
- Render health-check path, instance policy, database pool size, and
  production process count.

Use the hosting provider's private environment/secret mechanism for server
secrets. Do not commit real values to source or deployment manifests. Confirm
the provider's secret handling and separate dev/prod values before setup.

## Network and connection selection

No PostgreSQL client exists in WURI yet. Do not add a connection string until
the database adapter and role design are implemented. Whether the selected
host can reach a Supabase direct endpoint or requires a pooler is unresolved
and must be checked against the actual host network and project connection
details after authorization. Do not invent a pooler hostname. Require
encrypted database connections and use the WURI database role, not a browser
API key.

The correct pool mode is unresolved. Select it only after the hosting
pattern, database driver, transaction lifecycle, prepared-statement behavior,
and application pool size are designed.

## CORS, cookies, and health checks

- Current CORS is configured through exact origins in
  `WURI_CORS_ORIGINS`; production/staging readiness requires explicit
  configuration. The application currently permits `GET`, `POST`,
  `PATCH`, and `DELETE`, and permits the `Content-Type` request header.
  Verify the actual frontend/API origins, credentials, required headers, and
  all route methods after a deployment is explicitly approved. Do not replace
  the allow list with `*`.
- Auth uses a custom signed session cookie with `HttpOnly`,
  `SameSite=Lax`, a one-hour max age, and Secure default `true`. Verify the
  deployed frontend/API site relationship and cookie behavior. If cross-site
  cookie settings are required, use `Secure` plus an explicit CSRF strategy;
  CORS alone is not CSRF protection.
- The existing root route is not a dependency readiness check. Add
  separately designed liveness/readiness behavior only after implementation
  authorization. Readiness must not expose secrets or private topology. A
  database outage should not be misreported as ready if the application
  cannot serve authenticated requests.
- Keep logs redacted. Do not log request bodies, passwords, hashes, session
  cookies, database strings, object URLs, or research document names/content.

## Storage durability and operations

The current `PrivateStorage` writes uploaded files to a local path. Whether
the selected hosting plan preserves that filesystem across restart/deploy
cannot be established from repository source. Until durability, backup, and
access isolation are established for the chosen host, this implementation is
not acceptable for durable institutional documents. A persistent disk
option, if any, would still need backup, isolation, and recovery review.

Use a private object store with authorization enforced by the backend. Keep
object keys and checksums in PostgreSQL; define retry/reconciliation,
deletion/retention, audit, backup, and restore behavior. Database backup and
object backup are separate. Do not make institutional or research documents
public.

## Deployment and rollback gates

Before any deployment:

1. Obtain explicit written security clearance for runtime and deployment
   work; do not activate or fetch the suspicious revision.
2. Resolve Supabase service-role key exposure. Rotation status is
   **UNCONFIRMED**; do not use the exposed key. Confirm deactivation privately
   and review available project logs.
3. Complete and review the SQLite-to-PostgreSQL code and schema migration;
   create a separate isolated dev project and use only synthetic/authorized
   data.
4. Complete private object storage migration and failure/recovery design.
5. Pin/review backend and frontend dependencies and choose verified build/start
   commands, output path, Python runtime, health path, and pool settings.
6. Configure exact CORS origins, HTTPS, secure cookies, CSRF approach if
   needed, secrets, backups, and monitoring.
7. Verify the trusted malware scanner binary, signature-update process, and
   clean/infected fixture behavior. Do not rely on a boolean environment flag.
8. Verify external ingress request-body limits and container-level parser
   isolation independently from the ASGI and process resource limits.
9. Run the authorized post-clearance test plan in an isolated dev environment.
   No production data or research experiments are permitted by this plan.
10. Obtain separate security, data-owner, and research-owner sign-off before
    actual university uploads.

Rollback must retain the original SQLite-based deployment and data as an
unchanged fallback until PostgreSQL and object-storage cutover reconciliation
is accepted. Once PostgreSQL accepts authoritative writes, returning to the
old SQLite database would lose those writes without a separately designed
reverse-data path. Document the recovery point, object recovery, cutover
owner, and rollback cutoff before deployment.

## Status

This is a design document, not a deployment record. No WURI Render service
or Supabase resource was created or accessed; no build, test, migration, or
application process was run. Runtime and migration work remain **NO-GO**.

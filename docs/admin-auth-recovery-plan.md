# WURI Admin Authentication Diagnosis and Recovery Plan

Status: static source review only. Runtime checks remain **NO-GO** until written authorization from an authorized security reviewer.

## Scope and evidence

This plan is based on a read-only inspection of `backend/app/main.py`, `backend/app/security.py`, `backend/app/database.py`, `backend/README.md`, `backend/.env.example`, and the login/session code in `university-ranking-dss/src/App.jsx`. No database, environment values, password hashes, or session tokens were read. No application code was run.

The reported browser observations are `POST /api/auth/login` returning 503 and `GET /api/auth/session` returning 401. They are not sufficient to identify the process environment, database state, or cookie behavior that caused the responses.

## Diagnosis

| Observation | Source-level causes | Evidence needed after runtime clearance |
|---|---|---|
| `POST /api/auth/login` returns 503 | `WURI_ADMIN_USERNAME` or `WURI_ADMIN_PASSWORD` missing/empty; `WURI_ADMIN_PASSWORD` shorter than 12 characters (caught from `hash_password`); the submitted credentials are valid but `WURI_SESSION_SECRET` is missing; or `SESSION_COOKIE_SECURE` is not `true`/`false`, or is `false` while `WURI_ENVIRONMENT` is not `development`. | Inspect only whether required variables are set and whether password length meets the requirement; never print values. Check the exact response detail and backend logs for secret leakage. Confirm the secure-cookie flags and environment setting without printing secret values. A 503 alone does not show which condition occurred. |
| `POST /api/auth/login` returns 401 | Submitted username does not resolve to an active user, or the submitted password does not verify against that user's stored scrypt hash. Username comparison trims and lowercases the configured and submitted names. | Confirm the locally stored username is the one configured and submitted; ask an authorized operator to establish whether the account exists and is active without disclosing hashes. Changing the environment password does not update an existing account's hash. |
| `GET /api/auth/session` returns 401 | No session cookie; invalid, expired, or incorrectly signed token; missing session secret; or the token identifies no active user. An unauthenticated initial browser request is expected to return 401. | After an authorized login attempt, inspect cookie presence and attributes in browser developer tools without copying its value. Check whether the browser accepted and sent it, and whether the same backend secret and database are used by both requests. Do not treat this response as proof of a wrong password. |
| Login returns success, but a later session request returns 401 | Cookie may not be stored or sent, may have expired, may be signed under a different session secret, or the corresponding user may not be active/present in the database used by that request. | Compare request origin/host, cookie attributes, API destination, backend process configuration, and database path. Never expose the cookie value or secret. |

The frontend sends JSON `{ username, password }` to `/api/auth/login` and sets `credentials: 'include'`. It also includes credentials on the shared `apiFetch` helper used for `/api/auth/session`. The backend uses the cookie name `wuri_session`, sets it HttpOnly with `SameSite=Lax`, a one-hour max age, and a Secure flag controlled by `SESSION_COOKIE_SECURE`. Backend CORS allows credentials for specific localhost and 127.0.0.1 development origins. The frontend's default API origin is `http://127.0.0.1:8000`; the actual page origin was not inspected. For the Lax cookie, use a consistent local hostname for frontend and API after clearance. With plain HTTP, the default Secure cookie may not be accepted; source permits `SESSION_COOKIE_SECURE=false` only when `WURI_ENVIRONMENT=development`.

The login component reads an error response detail and then its broad `catch` replaces it with a generic message. This makes the page's displayed error less diagnostic, but does not explain the server's 503 by itself; the HTTP response remains observable in developer tools. No authentication protocol defect was established by this source review.

`Database` selects its path in this order: explicitly supplied path, `WURI_DATABASE_PATH`, then `backend/data/wuri.sqlite3` (resolved from the source file location). A relative configured path is interpreted relative to the backend process's current working directory. The example path is `./data/wuri.sqlite3`; the README setup changes directory to `backend` first. This review did not inspect or open any database file.

The backend reads configuration with `os.getenv`. No dotenv loader or `env_file` configuration was found in the inspected backend source, requirements, or README. The README says to set admin credentials in the server process environment. Copying `.env.example` to `.env` alone should not be assumed to load the values.

## Authentication requirements from source

- The submitted identifier is a username, not an email-specific field.
- `WURI_ADMIN_USERNAME` and `WURI_ADMIN_PASSWORD` must be set in the backend process environment.
- Admin username is trimmed and lowercased before initialization; the submitted username is also trimmed and lowercased for lookup.
- Admin password must be at least 12 characters. Password hashes use scrypt.
- `WURI_SESSION_SECRET` must be set for login to create a signed session and for session verification.
- The cookie is `wuri_session`, HttpOnly, `SameSite=Lax`, and valid for one hour. `SESSION_COOKIE_SECURE` defaults to `true`. Setting it to `false` requires `WURI_ENVIRONMENT=development`.
- During a login request, initialization creates an admin only if the configured normalized username is absent. Creation happens before the submitted request credentials are checked, so that request can still end in 401 if its submitted username/password do not match the configured admin credentials. The new user is active, receives an administrator membership, and initialization creates a default development institution. If that username already exists, `ensure_admin` returns the existing ID without updating its password hash.
- No password recovery/reset workflow was found in the inspected backend application code. There is no supported reset procedure documented in the backend README.

## Safe administrator configuration (after written runtime clearance only)

An authorized operator should choose the username and generate a unique, random password and session-signing secret with a trusted local password manager or cryptographic generator. Use a password substantially longer than the 12-character minimum. Store both values only in an approved local secrets manager. Do not put real values in source, `.env.example`, documentation, command history, screenshots, Git, logs, or chat.

The following is a **proposed example only; it was not executed**. Run it only after written runtime clearance, in the same dedicated PowerShell process that will start the backend. Retrieve the password and secret locally from the approved password manager; enter them at the masked prompts. These variables exist in that PowerShell process environment for child processes, and should not be printed:

```powershell
$env:WURI_ADMIN_USERNAME = '<chosen-local-admin-username>'
$adminPassword = Read-Host 'Admin password from local password manager' -AsSecureString
$secretValue = Read-Host 'Session secret from local password manager' -AsSecureString
$adminPasswordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword)
$secretValuePtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretValue)
try {
    $env:WURI_ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($adminPasswordPtr)
    $env:WURI_SESSION_SECRET = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretValuePtr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($adminPasswordPtr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretValuePtr)
    Remove-Variable adminPassword, secretValue, adminPasswordPtr, secretValuePtr
}
```

For local HTTP development only, the source requires `WURI_ENVIRONMENT=development` before `SESSION_COOKIE_SECURE=false` is accepted. Keep Secure cookies enabled for HTTPS deployments. Do not set the insecure development option outside the isolated local development environment. Do not start the backend or use these examples before clearance.

## Existing-account handling

Changing `WURI_ADMIN_PASSWORD` does **not** change a password hash for an existing username. If that account exists and its password is lost, do not guess, delete, replace, or reset the database, and do not bypass password verification. Ask the authorized system owner to approve a documented password-reset mechanism that preserves the database, records who authorized and performed the reset, and protects the new credential. No such application workflow was found in this review; a recovery mechanism would need separate design and authorization.

## Fresh-database handling

Source supports creating the configured admin during a login request when that normalized username does not exist. It also creates a default development institution and administrator membership at that point. This does not establish that the current database is fresh or that the username is absent. Do not delete, move, replace, or reset a database to force initialization. An authorized operator must first establish which configured database path the backend would use, without exposing database contents.

Because initialization precedes credential verification, ensure the configured username and password are the credentials being submitted. An unsuccessful request can still create the configured account if it was absent.

## Post-clearance verification checklist

Perform only after written security authorization explicitly permits runtime checks, and only against the reviewed clean local tree:

1. Configure credentials and the database/storage paths in the backend process environment without displaying or logging values.
2. Start the backend using the approved procedure. Confirm required authentication configuration is present using redacted checks; do not print values.
3. Attempt login with the locally stored administrator username/password. Do not place credentials in command-line arguments or logs.
4. Confirm a successful response and that the browser stores the HttpOnly `wuri_session` cookie with the expected Secure/SameSite settings. Never copy or disclose the cookie value.
5. Confirm `/api/auth/session` succeeds when the browser sends that cookie.
6. Confirm invalid credentials are rejected, and responses/logs do not include passwords, hashes, session secrets, or tokens.
7. Stop if the observed database path or account state is unexpected. Do not use database deletion or replacement as troubleshooting.

These checks do not authorize research scoring, A0–A4 experiments, or use of institutional evidence. Research approvals and data requirements remain separate.

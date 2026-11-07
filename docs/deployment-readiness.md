# Deployment readiness gate

The evidence-intake gate is separate from application startup. Run this
preflight from the backend environment:

```powershell
Push-Location backend
.\\venv\\Scripts\\python.exe -m app.deployment_readiness
Pop-Location
```

The command emits non-secret JSON checks and exits `0` only when every check
is `ready`. Any `blocked` or `manual_verification_required` result keeps real
institutional intake blocked. The output does not include commands, paths,
tokens, document names, or institutional data.

**Important distinction:** the current preflight intentionally reports
independent scanner verification, ingress configuration, container isolation,
authorization, audit retention, and recovery as manual checks. Consequently,
the overall intake gate remains blocked until those checks have a separately
documented and accepted evidence process. An administrator must not change
the program or environment to force a green result. A future implementation
may add a reviewed, auditable deployment-attestation workflow; none exists
today.

## Configuration and persistence boundaries

- `WURI_DATABASE_PATH`: path to the application's **local SQLite database**.
  It is not a PostgreSQL connection setting and does not configure Supabase.
  Do not treat a local SQLite file on an ephemeral hosting filesystem as a
  production database.
- `WURI_STORAGE_PATH`: path to the application's **local private filesystem
  storage**. It is not object storage and does not by itself provide durable
  storage, backups, or recovery.
- `WURI_SESSION_SECRET`: strong secret managed outside source control.
- `WURI_ADMIN_USERNAME` and `WURI_ADMIN_PASSWORD`: initial administrator
  credentials; set privately and never commit real values.
- `SESSION_COOKIE_SECURE=true` (the default outside local development).
- `WURI_ENVIRONMENT=production` and exact approved
  `WURI_CORS_ORIGINS` values for a production deployment.
- `WURI_MALWARE_SCANNER_COMMAND`: administrator-managed scanner executable
  or wrapper. Its presence is not proof that it is a legitimate or correctly
  configured malware scanner.

A PostgreSQL/Supabase adapter and private object-storage integration are not
implemented by these local path settings. They require separately reviewed
code, schema/migration work, credentials, and recovery design before
production deployment.

## Malware scanner contract and verification

The scanner command is parsed into an argument list and invoked without a
shell. The generated private storage path is passed as the final argument;
document filenames and contents are never interpolated into a command.
The wrapper contract is explicit:

- exit code `0` means clean;
- exit code `1` means infected;
- timeout, unavailable executable, malformed configuration, and every other
  exit code mean an error and fail closed.

The application suppresses scanner output because scanner output may contain
paths or sensitive metadata. The wrapper must be a trusted administrator-owned
executable, isolated from the web process where possible, and maintained with
current signatures or detection rules.

**Important:** `WURI_MALWARE_SCANNER_VERIFIED` is not accepted as evidence and
must not be used as a readiness bypass. The application rejects a missing,
malformed, or non-executable configured command. Even when an executable is
present, readiness remains `manual_verification_required` until an
administrator independently verifies the actual binary, its provenance,
version/signature update process, and documented clean/infected test behavior.
A configured test command or environment boolean cannot prove production
malware scanning is active.

The scanner command is a privileged deployment setting: configuring an
arbitrary executable that returns exit code `0` can cause the upload path to
receive a `clean` result. Therefore, do not configure a placeholder, test
program, shell utility, or unreviewed executable as the production scanner.
Only an independently verified scanner wrapper may be configured by an
authorized deployment administrator. Until that verification and the
application's separate security gate are accepted, real document intake
remains prohibited. This documentation does not itself enforce scanner
identity at runtime; that limitation must not be mistaken for a completed
security control.

## Gate checks

The preflight reports:

- whether a scanner executable is configured and can be located; independent
  trust and behavior verification remains manual;
- private storage writability, with isolation and backup review still manual;
- Secure cookie configuration and exact CORS configuration;
- required SQLite schema migrations;
- supported formats, per-file upload size, and application request-body limit;
- external ingress body limit, parser worker resource limits, and container
  isolation as separate checks;
- the authorization and research-use workflow;
- audit retention and operational recovery.

The software records institutional authorization, research-use permission,
DUA decisions, ethics determinations, privacy review, provenance, and human
document review separately. Human reviewers and institutional authorities
remain responsible for confirming those decisions. Software status fields do
not independently establish legal source rights, DUA validity, ethics
approval, or privacy compliance.

## Operations and recovery

Production deployment must use HTTPS, private durable storage permissions,
encrypted and access-controlled backups, documented deletion and retention
periods, restore testing, audit-event retention, restricted audit access,
upload-size and parser resource limits, scanner timeout monitoring, and an
incident response procedure. A failed scan or interrupted upload must not
create an approved evidence record; a document referenced by an approved
research dataset cannot be deleted or have its verification metadata
downgraded.

The current local SQLite and filesystem storage implementation is not, by
itself, a production persistence architecture. Do not enable institutional
document intake on an ephemeral filesystem or treat a successful local
preflight as proof of durable storage, PostgreSQL availability, or backup
recoverability.

## Final enablement checklist

Before enabling real institutional evidence intake, an administrator must
confirm and retain evidence for each item:

1. All automated preflight checks pass, and every manual check has been
   separately reviewed and accepted by its accountable owner. The current
   CLI reports manual checks explicitly and therefore cannot, by itself,
   attest that these external controls are complete.
2. The real scanner binary/wrapper passes its documented clean and infected
   tests and its update process is operational.
3. HTTPS, Secure cookies, exact CORS origins, private durable storage, backup,
   restore, retention, and audit controls are operational.
4. The database and storage architecture is durable, access-controlled, and
   independently recoverable; local SQLite/filesystem settings are not
   mistaken for PostgreSQL/object storage.
5. External ingress limits and container isolation are independently
   verified in addition to application-level controls.
6. Participating institutions have supplied authorization and research-use
   permission through the approved human process.
7. DUA, ethics, privacy, and source-rights responsibilities have been reviewed
   by the responsible authorities.
8. The A0 protocol remains researcher-approved before any research experiment.

The current development environment has no configured production scanner, so
the real-evidence gate remains blocked. Mocked scanner tests demonstrate
software behavior only and do not constitute scanner integration verification.

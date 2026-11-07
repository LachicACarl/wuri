# Deployment readiness gate

The evidence-intake gate is separate from application startup. Run this
preflight from the backend environment:

```powershell
Push-Location backend
.\venv\Scripts\python.exe -m app.deployment_readiness
Pop-Location
```

The command emits non-secret JSON checks and exits `0` only when every check
is `ready`. Any `blocked` or `manual_verification_required` result keeps real
institutional intake blocked. The output does not include commands, paths,
tokens, document names, or institutional data.

## Required configuration

- `WURI_DATABASE_PATH`: production database location.
- `WURI_STORAGE_PATH`: private document-storage location.
- `WURI_SESSION_SECRET`: strong secret managed outside source control.
- `SESSION_COOKIE_SECURE=true` (the default outside local development).
- `WURI_MALWARE_SCANNER_COMMAND`: trusted server-side scanner wrapper.
- `WURI_MALWARE_SCANNER_VERIFIED=true`: set only after an administrator has
  tested the wrapper against the real scanner's documented safe clean and
  infected test procedure.

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
current signatures or detection rules. A configured test command is not
evidence that production malware scanning is active.

## Gate checks

The preflight reports:

- scanner configuration and administrator verification;
- private storage writability, with isolation and backup review still manual;
- Secure cookie configuration;
- required database migrations;
- supported formats and upload size;
- the authorization and research-use workflow;
- audit retention and operational recovery.

The software records institutional authorization, research-use permission,
DUA decisions, ethics determinations, privacy review, provenance, and human
document review separately. Human reviewers and institutional authorities
remain responsible for confirming those decisions. Software status fields do
not independently establish legal source rights, DUA validity, ethics
approval, or privacy compliance.

## Operations and recovery

Production deployment must use HTTPS, private storage permissions, encrypted
and access-controlled backups, documented deletion and retention periods,
restore testing, audit-event retention, restricted audit access, upload-size
and parser resource limits, scanner timeout monitoring, and an incident
response procedure. A failed scan or interrupted upload must not create an
approved evidence record; a document referenced by an approved research
dataset cannot be deleted or have its verification metadata downgraded.

## Final enablement checklist

Before enabling real institutional evidence intake, an administrator must
confirm:

1. The preflight exits successfully in the deployment environment.
2. The real scanner wrapper passes its documented clean and infected tests.
3. HTTPS, Secure cookies, private storage, backup, restore, retention, and
   audit controls are operational.
4. Participating institutions have supplied authorization and research-use
   permission through the approved human process.
5. DUA, ethics, privacy, and source-rights responsibilities have been reviewed
   by the responsible authorities.
6. The A0 protocol remains researcher-approved before any research experiment.

The current development environment has no configured production scanner, so
the real-evidence gate remains blocked. Mocked scanner tests demonstrate
software behavior only and do not constitute scanner integration verification.

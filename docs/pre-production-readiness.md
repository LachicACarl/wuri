# Pre-production evidence intake requirements

Phase 16G adds a malware-scanning boundary but does not provide a scanner.
The upload path stores a file privately as quarantine, invokes the configured
scanner before extraction, and deletes the file when scanning or extraction
fails. A document is accepted only after a scanner returns `clean`; scanner
errors, timeouts, unavailable services, and unknown results fail closed.

Configure a production scanner with `WURI_MALWARE_SCANNER_COMMAND`. The
command is invoked with the private quarantined file path as its final
argument. Exit code `0` means clean, `1` means infected, and any other result
is an error. The command must be a trusted server-side executable, enforce
its own signature/database update policy, and be isolated from the web
process. No scanner is configured in the current environment, so real
institutional intake remains blocked.

Production requirements also include:

- HTTPS and the default `Secure` session cookie configuration.
- Private storage with backups, access controls, and documented deletion
  retention.
- Upload-size and parser resource limits, with monitoring and recovery for
  partial failures.
- Audit-event retention and restricted audit access.
- A human workflow that records institutional authorization, research-use
  permission, data-use agreement decisions, ethics determination, privacy
  review, provenance, and document review separately.
- External confirmation of source rights and approvals; software status
  fields do not establish legal validity.

The WURI pilot corpus remains candidate program data. No A0-A4 experiment or
ranking calculation is enabled by this intake boundary.

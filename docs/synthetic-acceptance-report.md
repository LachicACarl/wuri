# Phase 16I synthetic acceptance report

## Scope

This acceptance pass used disposable SQLite databases, private temporary
storage, synthetic users, synthetic institutions, and synthetic TXT content.
It did not access private research inputs, collect institutional documents, or
run A0-A4 experiments.

## Workflows exercised

- Authenticated upload to private storage.
- Scanner outcomes of `unavailable`, `error` (timeout/error contract), and
  `infected`, each rejected before extraction and cleaned up.
- Explicit synthetic clean scanner adapter followed by extraction, passage
  persistence, and WURI 2026 criterion mapping.
- Unknown authorization and research-use states after upload.
- Authorized metadata transitions through the existing administrator route.
- Same-institution download and deletion.
- Cross-institution listing, download, and metadata mutation rejection.
- Dataset creation and approval-state revalidation, including permission
  downgrade and approved-document deletion protection through the persistence
  security suite.
- Deployment preflight output and blocked intake gate.

## Scanner coverage

The clean, infected, unavailable, error, and timeout cases use a clearly
identified `synthetic-acceptance` or mocked scanner result. They verify
application behavior only. No actual antivirus or production scanner is
configured or verified in this environment, so scanner integration remains
blocked for deployment.

## Defects and fixes

The acceptance workflow found no new defect after the Phase 16G quarantine
cleanup fix. The integrated test confirms that rejected scans leave no
private files, clean files produce passages and mappings, and institution B
cannot access institution A's document.

## Validation

- Full backend suite: 85 tests passed.
- Python compilation: passed.
- Framework catalog JSON: valid.
- A0 protocol JSON: valid and still
  `pending_researcher_approval`.
- `git diff --check`: passed.
- Frontend lint/build: not run because frontend files were unchanged.
- Deployment preflight: exits `1`; real evidence intake remains blocked.

## Remaining gaps

Production readiness has not been established. A trusted scanner wrapper must
be configured and administrator-verified against a real scanner procedure.
Storage isolation, backups, restore testing, retention, audit access,
institutional authorization, research-use permission, DUA, ethics, privacy,
and source-rights procedures require deployment and human verification.

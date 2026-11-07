# WURI Review-Only Branch

This branch is a review base created from the clean-root quarantine snapshot. It is deliberately separate from `main` and must not be merged into `main` until the security hold in issue #1 is independently cleared.

Source snapshot: `security/clean-root-quarantine-2026-11-07`  
Snapshot commit: `ff22bb0f5d73d5d62402f2d4c66eab957513e698`

## Scope

This review branch contains only the non-operational React security-hold screen and documentation. It does not implement backend API, authentication, document uploads, Supabase access, extraction, scoring, or persistence.

## Review requirements

- Review source and documentation changes.
- Do not run the project or install packages until runtime authorization is explicitly recorded.
- Do not connect to Supabase or process institutional data.
- Do not merge this review line into `main` while the security hold remains open.
- Keep credentials and secrets out of issues, commits, and pull requests.

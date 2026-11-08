# WURI Security Hold — Clearance Evidence Checklist

**Decision: HOLD — NO-GO**  
**Scope:** Historical remediation branch `security/recovery-remove-obfuscated-vite-config` and isolated review snapshot `security/clean-root-quarantine-2026-11-07`  
**Purpose:** Track evidence required before the security hold can be reconsidered. This document is a checklist, not a security clearance.

## 1. Repository-side remediation observed

The current clean-root review snapshot contains the following source-level observations (static review only):

- The clean-root Vite configuration is declarative and contains React/Tailwind plugins; historical suspicious commits remain preserved outside this orphan lineage for independent review.
- Root `node_modules/` is absent from the current branch tree; root ignore rules exclude dependencies, build outputs, local environment files, and logs.
- The clean-root frontend now contains only a static security-hold screen. No upload control, API request, results renderer, scoring constants, frontend authentication state, or Supabase client remains in the current UI.
- No client-side sign-in is implemented. Authentication is unavailable until an approved server-side service is built and reviewed.
- Root README and source-index documents describe the project structure, hold, and restrictions. The active HTML is a standalone static page; no React entrypoint is present.

These changes do **not** establish that historical commits or dependency artifacts were safe, that the suspicious code was never executed, or that any credential was revoked. Older project-listing notes are not live provider-state evidence and must be re-confirmed directly by the authorized owner.

## 2. Mandatory external security evidence

| ID | Required evidence | Acceptable closure evidence | Current status |
|---|---|---|---|
| SEC-01 | Forced update authorization and provenance | Dated maintainer statement identifying actor, authorization, source revision, and reason for the forced update | OPEN |
| SEC-02 | Suspicious Vite configuration review | Independent reviewer report identifying exact commit/tree/blob, complete behavior, and any follow-on behavior | OPEN |
| SEC-03 | Possible prior execution assessment | Reviewer/incident handler statement describing host, account, CI, workstation, and deployment evidence examined, plus limitations | OPEN |
| SEC-04 | Exposed Supabase service-role key | Authorized Supabase owner confirmation that the exposed key is revoked/disabled and cannot be used; verify against the correct WURI project, not another project with a similar label | OPEN |
| SEC-05 | Replacement credential custody | Confirmation that any replacement is newly generated, stored only in an approved server-side secret store, and not shared in source/chat | OPEN |
| SEC-06 | Dependent service update | Inventory of authorized services using the replacement secret, with confirmation each has been updated or disabled | OPEN |
| SEC-07 | Provider log review | Dated owner/security review of available authentication, API, database, and project activity logs; note retention/visibility limits | OPEN |
| SEC-08 | Independent clearance decision | Signed/delivered finding naming reviewer, reviewed commit/tree, residual risks, and exact permitted next activities | OPEN |

Do not paste credentials, secret values, recovery tokens, or private log contents into this repository issue/document. Record only owner, date, confirmation reference, and redacted evidence location.

## 3. Maintainer acceptance record

The authorized maintainer must complete this section after receiving the evidence above:

- Maintainer:
- Decision date (UTC):
- Reviewed branch and commit:
- Security reviewer and report reference:
- SEC-01 through SEC-08 evidence references:
- Residual risks accepted (if any):
- Permitted next phase:
- Explicitly prohibited activities:
- Approval/sign-off reference:

An empty field is not approval. A verbal statement or this checklist's presence is not approval.

## 4. Separate technical authorization gates

Security clearance does not automatically authorize engineering or research activity. Obtain separate written approval for each:

| Gate | Scope | Status |
|---|---|---|
| AUTH-01 | Static source review and documentation | CURRENT LIMITED SCOPE |
| AUTH-02 | Dependency restoration/install in an isolated environment | NOT AUTHORIZED |
| AUTH-03 | Local startup, builds, lint, and automated tests | NOT AUTHORIZED |
| AUTH-04 | Isolated synthetic-data backend/API tests | NOT AUTHORIZED |
| AUTH-05 | Supabase project access, schema changes, migrations, or storage tests | NOT AUTHORIZED |
| AUTH-06 | Real institutional data acquisition, processing, or research scoring | NOT AUTHORIZED |
| AUTH-07 | Production deployment or DNS/service changes | NOT AUTHORIZED |

For every newly authorized gate, record the approving person, date, exact commit, environment, data classification, scope, and stop conditions before acting.

## 5. Technical follow-up after clearance

These are not completed:

1. Independent dependency provenance review for `university-ranking-dss/package.json` and all referenced tooling; regenerate a reviewed lockfile only after authorization.
2. Confirm whether any root-level package manifest exists; the current clean-root tree has only `university-ranking-dss/package.json`.
3. Finalize and approve the server-side authentication/session policy, including provider/issuer identity mapping, session lifetimes, revocation, and propagation behavior.
4. Finalize and approve the asynchronous assessment API contract, including acceptance/completion lifecycle, status model, idempotency, typed errors, provenance, and completed-result schema; the proposed endpoint is not implemented and the current frontend does not send uploads.
5. Finalize database state machines, idempotency constraints, version registries, identity mapping, and retention/deletion semantics before any physical schema or migration design.
6. Private document storage access, retention, and recovery design review, if formally approved.
7. Isolated testing with synthetic data only after explicit AUTH-02 through AUTH-04 authorization.
8. Research-method approval that specifies framework indicators, score units/ranges, aggregation rules, missing-data behavior, model versions, validation partitions, and permitted claims before any scoring implementation.

## 6. Current disposition

**HOLD — NO-GO remains in effect.**

Do not merge this branch, rewrite or delete historical evidence, execute the suspicious historical revision, install dependencies, start the application, run builds/tests, trigger CI, connect to Supabase, rotate credentials through an unconfirmed actor, migrate data, or deploy until the relevant approvals are documented.

This checklist is an internal tracking aid. It is not a forensic report, credential-rotation confirmation, independent review, or authorization.


## 7. Latest evidence reconciliation — 2026-11-08

A fresh read of GitHub Issue #1 found no new comments from an independent security reviewer or authorized Supabase owner; the comments available for this review are authored by the repository owner. Therefore SEC-02 through SEC-08 remain OPEN, and AUTH-02 through AUTH-07 remain NOT AUTHORIZED. A general maintainer request to continue does not close those gates. This dated note is a repository-status observation only, not a reviewer finding or key-rotation verification.

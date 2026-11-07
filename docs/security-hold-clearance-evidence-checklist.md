# WURI Security Hold — Clearance Evidence Checklist

**Decision: HOLD — NO-GO**  
**Scope:** Repository remediation branch `security/recovery-remove-obfuscated-vite-config`  
**Purpose:** Track evidence required before the security hold can be reconsidered. This document is a checklist, not a security clearance.

## 1. Repository-side remediation observed

The current recovery branch contains the following changes:

- Standard Vite configuration replaces the obfuscated configuration in the current branch tree.
- Root `node_modules/` is absent from the current branch tree; root ignore rules exclude dependencies, build outputs, local environment files, and logs.
- The frontend no longer creates synthetic EQAM/RRS/ARRS results from sample passages and file metadata.
- The frontend rejects incomplete backend assessment responses and does not substitute local placeholder scores.
- The hardcoded browser-side `admin / admin123` login was removed. Sign-in fails closed because a reviewed server-side authentication implementation is not present.
- Root README documents the project structure, hold, and restrictions.

These changes do **not** establish that historical commits or dependency artifacts were safe, that the suspicious code was never executed, or that any credential was revoked.

## 2. Mandatory external security evidence

| ID | Required evidence | Acceptable closure evidence | Current status |
|---|---|---|---|
| SEC-01 | Forced update authorization and provenance | Dated maintainer statement identifying actor, authorization, source revision, and reason for the forced update | OPEN |
| SEC-02 | Suspicious Vite configuration review | Independent reviewer report identifying exact commit/tree/blob, complete behavior, and any follow-on behavior | OPEN |
| SEC-03 | Possible prior execution assessment | Reviewer/incident handler statement describing host, account, CI, workstation, and deployment evidence examined, plus limitations | OPEN |
| SEC-04 | Exposed Supabase service-role key | Authorized Supabase owner confirmation that the exposed key is revoked/disabled and cannot be used | OPEN |
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

1. Independent dependency/lockfile provenance review for both root and `university-ranking-dss/` package manifests.
2. Decision on whether the root package manifest/lockfile is an intentional separate project or obsolete duplicate.
3. Server-side authentication/session contract and authorization model.
4. Assessment API contract, response schema, evidence provenance, and error behavior.
5. PostgreSQL adapter/schema/migration/rollback design, if formally approved.
6. Private document storage access, retention, and recovery design, if formally approved.
7. Isolated testing with synthetic data after explicit AUTH-02 through AUTH-04 authorization.

## 6. Current disposition

**HOLD — NO-GO remains in effect.**

Do not merge this branch, rewrite or delete historical evidence, execute the suspicious historical revision, install dependencies, start the application, run builds/tests, trigger CI, connect to Supabase, rotate credentials through an unconfirmed actor, migrate data, or deploy until the relevant approvals are documented.

This checklist is an internal tracking aid. It is not a forensic report, credential-rotation confirmation, independent review, or authorization.

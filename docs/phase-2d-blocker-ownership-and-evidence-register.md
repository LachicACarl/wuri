# WURI Phase 2D — Blocker Ownership and Evidence Register

**Assessment date:** 2026-10-23  
**Scope:** Static documentation review and blocker tracking  
**Security hold:** **NO-GO**  
**Implementation gate:** **NO-GO**

## Executive summary

This register consolidates the unresolved security, credential, design, approval, test, and deployment blockers from Phases 1D–1F and 2A–2C. It assigns accountable roles, next responsible parties, required closure evidence, dependencies, acceptance criteria, and the consequence of non-closure. It does not assign names or dates that are not in evidence.

The available documents report an October 22, 2026 local `origin/main` reflog entry labeled `fetch: forced-update` to a suspicious cached revision. The actor, authorization, trusted provenance, complete code behavior, and any prior execution remain unresolved. No authorized independent reviewer’s written clearance is documented. Supabase service-role key revocation, replacement custody, service dependency updates, and project-log review are also unconfirmed. Therefore, implementation, runtime checks, Supabase access, migration, and deployment remain **NO-GO**.

This is a closure checklist, not evidence that any blocker is resolved. A plan, checklist, or report written by this project does not substitute for the owner or independent reviewer evidence specified below.

## Evidence basis and status meanings

Documents inspected as text:

- `docs/phase-2c-security-and-migration-readiness-gate.md`
- `docs/phase-2b-remediation-register.md`
- `docs/phase-2a-design-review-report.md`
- `docs/phase-1d-independent-security-review.md`
- `docs/phase-1e-provenance-containment-report.md`
- `docs/phase-1f-security-hold-maintainer-handoff.md`

The suspicious cached revision was not inspected. No Git commands, provider access, network request, database access, or credential inspection was performed for this register.

- **VERIFIED** means the cited local document or source text was present and states the cited fact. It does not certify an external event or security outcome.
- **REPORTED BUT UNVERIFIED** is used for historical/ref-log observations recorded by prior reports but not independently reproduced in this assessment.
- **OPEN** means an action/evidence item remains outstanding and no external prerequisite necessarily prevents work on it.
- **BLOCKED** means the dependent action cannot proceed until an upstream authorization, evidence item, or decision is supplied.
- **UNCONFIRMED** means the available documentation does not establish whether the condition is true or complete.

## Blocker register

Severity describes potential impact if unresolved. “Next responsible party” names a role, not an assumed person. No deadline is assigned because none was authorized or supplied.

### Security clearance and credential remediation

| ID | Description; severity/risk | Current evidence and source | Status | Accountable role | Required action and completion evidence | Dependencies | Acceptance criteria | GO/NO-GO consequence | Next responsible party |
|---|---|---|---|---|---|---|---|---|---|
| SEC-01 | Resolve suspicious Vite code provenance and behavior; **Critical**—unresolved code provenance and possible prior execution prevent a defensible runtime decision. | Phase 1D reports an obfuscated dynamic chain, behavior and intent unresolved, and execution unknown (`phase-1d-independent-security-review.md:35,45-53`). Phase 1E reports the cached commit/ref observations and unresolved identity (`phase-1e-provenance-containment-report.md:38,46-48,65-73`). Phase 1F repeats the unknowns (`phase-1f-security-hold-maintainer-handoff.md:35,43-50`). | BLOCKED | Authorized independent security reviewer; repository maintainer supplies authorized audit records. | Independently assess the complete generated-code behavior without executing the suspicious revision, establish trusted provenance or exact intended change, assess available evidence of prior execution, and document findings and limitations. Evidence: signed/attributed written review with reviewed object/tree identity, methods, conclusions, unresolved items, and any required containment. | Reviewer authority and access to trusted evidence; maintainer investigation SEC-02. | Written findings cover provenance, reachable behavior, prior-execution assessment, reviewed code identity, and limitations; no unresolved opaque behavior is represented as cleared. | Any unresolved material provenance/behavior/execution question: **NO-GO** for runtime, tests, builds, install, provider access, migration, and deployment. | Authorized independent security reviewer, coordinated by repository owner/maintainer. |
| SEC-02 | Establish whether October 22 forced update was authorized and identify initiating account/process; **Critical**—local evidence does not establish actor or authorization. | Phase 1E reports a local reflog entry at `2026-10-22T17:30:15+08:00` labeled `fetch: forced-update`, and expressly says actor/reason are unknown (`phase-1e-provenance-containment-report.md:38,61,65-67`). Phase 1F repeats the request (`phase-1f-security-hold-maintainer-handoff.md:19,39,54-62`). | REPORTED BUT UNVERIFIED | Repository owner or authorized maintainer. | Review authorized repository-host, reference-history, client and automation audit records. Document who/what initiated the update, whether it was expected/authorized, and any gaps, without exposing credentials. | Authorized maintainer access to host/client records; SEC-01 uses result. | Written response identifies actor/process and authorization or explains why it cannot be established, cites trusted audit evidence, and records remaining risk. | Unexplained or unauthorized update, or insufficient evidence: **NO-GO**. Clearance cannot be inferred from the reflog label alone. | Repository owner/authorized maintainer. |
| SEC-03 | Obtain written security clearance and define its scope; **Critical**—no project-authored report can authorize itself. | Phase 2C says no independent reviewer decision was found and the reviewer is not identified in reviewed evidence (`phase-2c-security-and-migration-readiness-gate.md:45,49`). Phase 1D/1F maintain NO-GO (`phase-1d-independent-security-review.md:55-69`; `phase-1f-security-hold-maintainer-handoff.md:66-75`). | BLOCKED | Authorized independent security reviewer; repository maintainer confirms code/tree scope. | Issue explicit written decision identifying reviewer authority, reviewed tree, exact permitted activity (if any), limitations, stop conditions, and whether runtime, tests, builds, dependency installation, provider connection, implementation, or deployment are separately authorized. | SEC-01 and SEC-02; reviewer must have sufficient evidence to decide. | Dated written clearance addresses the identified risks and names the exact next permitted action. A runtime-only clearance is not implementation or deployment authorization. | Until explicit written clearance exists: **NO-GO** for all prohibited activities. Any activity outside its scope remains **NO-GO**. | Authorized independent reviewer, through the repository owner/security contact. |
| SEC-04 | Revoke exposed Supabase service-role credential and confirm replacement handling; **Critical**—privileged credential must be presumed compromised. | Phase 2C records revocation and replacement status as UNCONFIRMED (`phase-2c-security-and-migration-readiness-gate.md:51-60`). Phase 2B/Render plan also says rotation unconfirmed (`phase-2b-remediation-register.md:16-21`; `phase-2-render-deployment-plan.md:65-66`). | UNCONFIRMED | Authorized Supabase project owner. | Use the authorized Dashboard credential-management workflow to revoke/rotate the exposed credential; create/store any replacement only through approved private secret handling; update dependent authorized services. Evidence: private owner confirmation with date, credential class/key slot (not value), dependent services updated, and confirmation old value is inactive. | Project-owner authority; no WURI provider connection is needed for this remediation. | Owner confirms old credential revoked/inactive, replacement custody and service updates completed; no secret value is copied into report/chat/source. | Until confirmed: **NO-GO** for Supabase connection, application secrets configuration, migration, or deployment. | Authorized Supabase project owner. |
| SEC-05 | Review available Supabase project/access logs; **High**—potential unauthorized use remains unassessed. | Phase 2C says no log review record was found (`phase-2c-security-and-migration-readiness-gate.md:58-60`). Phase 1E notes no auth logs were inspected and recommends owner review (`phase-1e-provenance-containment-report.md:75-77`). | UNCONFIRMED | Authorized Supabase project owner/security incident owner. | Review available project/access/auth logs for the relevant period through authorized Dashboard/process; route suspicious events to incident response. Evidence: dated summary of log sources, window, conclusion and limitations, without tokens or secret data. | SEC-04 should be coordinated; access authority. | Owner records which logs exist/were reviewed, meaningful findings, response actions, and unavailable evidence. | Material unexplained activity or incomplete required incident review: **NO-GO** for provider use until security owner decides. | Supabase project owner, with security incident owner if warranted. |

### Documentation ownership and design decisions

| ID | Description; severity/risk | Current evidence and source | Status | Accountable role | Required action and completion evidence | Dependencies | Acceptance criteria | GO/NO-GO consequence | Next responsible party |
|---|---|---|---|---|---|---|---|---|---|
| DOC-01 | Add per-item accountable owner and explicit GO/NO-GO consequence to Phase 2B; **Medium**—work cannot be reliably assigned or gated at row level. | Phase 2C identifies these gaps (`phase-2c-security-and-migration-readiness-gate.md:80-91`). Phase 2B has IDs/evidence/dependencies/risk/acceptance/verification, phase gates and broad approvals, but not consistent row-level owners/consequences (`phase-2b-remediation-register.md:16-74,75-101`). | OPEN | Phase 2B document owner; approvals remain with named authority roles. | Update each register row to identify accountable role, implementer, approver/verifier as applicable, and the exact downstream gate blocked by non-acceptance. Evidence: reviewed register with no fabricated names or approvals. | None for documentation; do not modify application code. | Every blocker has an owner role, completion evidence, and a binary consequence; unknown people/dates remain marked unknown. | Until corrected, design closure lacks traceable accountability; **NO-GO** for claiming Phase 2 design gate complete. Security gate remains independently NO-GO. | Phase 2B document owner. |
| PG-01 | Close PostgreSQL query, transaction, generated-ID, exception, and schema decisions; **High**—unmapped semantics can corrupt data, authorization, or API behavior. | Phase 2A findings 1, 2, 6, 7 and Phase 2B `PG-01`–`PG-05` identify missing `BEGIN IMMEDIATE`, route `randomblob`, SQLite exception mapping, migration map and conversion choices (`phase-2a-design-review-report.md:28-42`; `phase-2b-remediation-register.md:26-38`). | BLOCKED | Application/database owner; security reviewer and research/data owners approve impacted security/meaning decisions. | Complete SQL-site inventory; choose driver, transaction/locking/pool behavior, error mapping, IDs, JSON/time/numeric types, constraints, and per-migration PostgreSQL semantics. Evidence: approved traceability matrix and migration/data-effects plan. | SEC-01/03 before implementation; researcher/data-owner approval where research meaning changes; DOC-01. | Every SQL/transaction/exception/migration behavior has a reviewed equivalent and explicit conversion/acceptance rule; no SQLite-specific behavior is silently carried over. | Unmapped semantics or unapproved data meaning: **NO-GO** for PostgreSQL implementation and test. | Application/database owner. |
| AUTH-01 | Approve authentication, membership, database-role and RLS boundary; **Critical**—tenant data could cross institutions if identity context or grants fail. | Phase 2A finding 4 and Phase 2B `AUTH-01`–`AUTH-04` require preserving custom HMAC session/password checks and defining trusted tenant context/role grants (`phase-2a-design-review-report.md:32-36`; `phase-2b-remediation-register.md:40-47`). | BLOCKED | Security owner and application/database owner; institutional privacy owner approves access policy. | Document endpoint/role/institution matrix, session/password invariants, least-privilege DB role, backend-only vs RLS choice, tenant context lifecycle, pool reset and fail-closed rules. Evidence: signed design and grants/policy review. | SEC-01/03; PG-01/02; actual domain decisions for cookie settings. | Existing checks remain enforced; no browser privileged credentials; RLS protections (if relied on) cannot be bypassed by application role and tenant context cannot leak across pooled requests. | Unresolved tenant/auth boundary: **NO-GO** for implementation, test, or data transfer. | Application security owner. |
| STOR-01 | Define private document/import storage lifecycle and partial-failure recovery; **Critical**—partial uploads/deletes can orphan bytes, lose metadata, or expose objects. | Phase 2A finding 3 and Phase 2B `STOR-01`–`STOR-04` identify state machine, idempotency, retries, authorization, retention and restore gaps (`phase-2a-design-review-report.md:30,44-48`; `phase-2b-remediation-register.md:49-56`). | BLOCKED | Storage/application owner; institutional data custodian and research owner approve lifecycle. | Specify upload/delete state transitions, keys/idempotency, retry owner, crash recovery, reconciliation, audit, retention, research-import access/deletion, private provider policy and object/DB recovery. Evidence: approved failure matrix/state machine and metadata map. | SEC-01/03/04; PG-01/03; AUTH-01; DOC-01. | Every partial failure has safe deterministic recovery; authorization is checked server-side; data remains private; retries cannot duplicate or mis-delete; retention and restore are approved. | Unresolved object consistency, access or recovery: **NO-GO** for storage implementation or test. | Storage/application owner. |
| RB-01 | Approve complete cutover and rollback runbook; **Critical**—post-cutover writes cannot safely fall back to unchanged SQLite without a reverse path. | Phase 2A finding 5; Phase 2B `RB-01/RB-02`; current migration plan warns that PostgreSQL authoritative writes are lost by simply switching back (`phase-2-database-migration-and-rollback.md:24-30`; `phase-2b-remediation-register.md:70-73,118-126`). | BLOCKED | Database/application owner and institutional data custodian. | Define all writers, freeze window, backup/restore proof, resumable export, reconciliation tolerances, authority-switch moment, rollback cutoff, forward-fix vs reverse export, post-cutover write handling, and synchronized object recovery. Evidence: owner-approved runbook and later isolated rehearsal record. | PG-01/03/04; STOR-01; approvals for any non-synthetic data; SEC-03. | Source SQLite remains unchanged; every phase has a declared authority and abort path; database and objects have compatible restore points; rollback does not silently discard authoritative writes. | Incomplete runbook or rehearsal: **NO-GO** for migration cutover/deployment. | Database/application owner. |
| TEST-01 | Approve synthetic-data integration test plan and isolated project prerequisites; **High**—documentation does not prove runtime safety or correctness. | Phase 2C requires test prerequisites and reports no tests; Phase 2B `VER-01/VER-02` describes later checks (`phase-2c-security-and-migration-readiness-gate.md:128-137`; `phase-2b-remediation-register.md:68-73,103-116`). | BLOCKED | Test operator and security approver; Supabase owner approves isolated project. | After implementation authorization, define exact synthetic fixtures/assertions, isolation, credentials path, failure cases, stop conditions, cleanup, evidence retention, and restore path. Evidence: approved test plan and separate result report after authorized execution. | SEC-01/03/04; PG-01 through PG-05; AUTH-01; STOR-01 if storage tested; RB-01. | Project is verified isolated and synthetic-only; test has explicit written runtime/provider scope; pass/fail criteria and cleanup are approved. | Missing any prerequisite: **NO-GO** for connection or test. A successful test does not authorize production or real data. | Test operator, after the security approver and project owner authorize. |
| REND-01 | Verify Render configuration and production readiness; **High**—commands, domains, health, filesystem, CORS/cookies and network are not provider-verified. | Phase 2A findings 8–9 and Phase 2B `REND-01`–`REND-05` describe unresolved start/build/health/storage/network/CORS/cookie settings (`phase-2a-design-review-report.md:42-46`; `phase-2b-remediation-register.md:58-65`). | BLOCKED | Deployment owner; security reviewer approves security settings. | Use actual authorized provider configuration to specify frontend/backend roots and commands, versions, SPA fallback, HTTPS domains, CORS, cookies/CSRF, secrets, health/readiness, database endpoint/pool, persistent/private storage, logs and recovery. Evidence: reviewed staging configuration and authorized staging results. | SEC-01/03/04; PG and storage implementations; TEST-01; RB-01. | No guessed provider settings; staging behavior and restore/security controls pass separately authorized verification; no privileged secret reaches frontend. | Until verified and explicitly approved: **NO-GO** for Render deployment. | Deployment owner. |
| DATA-01 | Obtain researcher/institutional approvals for applicable data and research operations; **Critical** for non-synthetic data/research—deployment/security clearance is not data-use approval. | Phase 1F maintains separate research gate (`phase-1f-security-hold-maintainer-handoff.md:9,73-75`); Phase 2B lists data/research approvals (`phase-2b-remediation-register.md:90-101`). Phase 2C reports no approval evidence (`phase-2c-security-and-migration-readiness-gate.md:107,120`). | UNCONFIRMED | Institutional data custodian/privacy owner; research owner/researcher for experiments. | Obtain written approvals identifying purpose, data classes, access, location, retention/deletion, migration, recovery and authorized personnel; separately approve research protocol and any A0–A4/readiness work. Evidence: approval records scoped to each operation. | Security clearance; storage/data lifecycle; deployment scope. | Every proposed data use is covered by explicit approval; synthetic test approval does not imply real-data or research approval. | Without applicable approval: **NO-GO** for real institutional data, document transfer, or research scoring/experiments. | Institutional data custodian; research owner for research-specific approval. |

## Evidence checklist for closure

Do not mark an item VERIFIED until its required evidence is received and reviewed by the appropriate role.

- [ ] **SEC-01:** Independent security review documents suspicious-code behavior/provenance and prior-execution assessment, with scope and limitations.
- [ ] **SEC-02:** Authorized maintainer documents forced-update actor/process, authorization and audit basis, or states what remains unknowable.
- [ ] **SEC-03:** Written clearance identifies reviewed tree and explicitly allowed activity, limits and stop conditions.
- [ ] **SEC-04:** Authorized Supabase owner privately confirms exposed credential revocation, replacement custody and service updates without sharing values.
- [ ] **SEC-05:** Authorized owner records available project-log sources/window, review outcome and limitations.
- [ ] **DOC-01:** Phase 2B register has a responsible role and per-item GO/NO-GO consequence for every row.
- [ ] **PG-01:** Complete SQL/transaction/ID/error/migration traceability and approved PostgreSQL equivalents.
- [ ] **AUTH-01:** Approved session, membership, role grants and RLS/backend authorization boundary.
- [ ] **STOR-01:** Approved private storage lifecycle, partial-failure recovery, retention, object metadata and restore behavior.
- [ ] **RB-01:** Approved cutover, freeze, reconciliation, rollback/forward-recovery and object restore runbook.
- [ ] **TEST-01:** Explicitly authorized synthetic-only isolated integration test plan and (later) separate test result.
- [ ] **REND-01:** Actual provider settings verified and deployment separately authorized.
- [ ] **DATA-01:** Institutional/research approvals for each applicable data class/use.

## Clearance gate: evidence required before implementation is reconsidered

Implementation may only be reconsidered after all of the following are documented:

1. An authorized independent security reviewer has reviewed the exact source tree intended for future work and supplied written findings on suspicious-code behavior/provenance and the forced update, including prior-execution assessment and limitations.
2. An authorized repository maintainer has corroborated the forced-update event from trusted audit records and documented whether it was authorized; unresolved material concerns are explicitly dispositioned by the authorized security owner.
3. The independent reviewer’s written decision explicitly authorizes the next specific activity and its scope. Security review completion without permission is not authorization; runtime permission is not automatically permission to edit code, connect to providers, migrate data, deploy, or perform research.
4. The authorized Supabase project owner confirms privately that the exposed service-role key is inactive/revoked, replacements are held through approved secret management, dependent services no longer use the old credential, and available relevant logs have been reviewed.
5. Phase 2B row-level owners and GO/NO-GO consequences are completed; migration/auth/storage/rollback designs have accountable owner approvals and no unresolved decision that could affect integrity, confidentiality, authorization, or recovery.
6. Any required institutional or research approvals are separately documented for the intended data and purpose.

Passing this documentary gate permits only a new readiness decision by the authorized parties. It is not proof that application code is safe, PostgreSQL is compatible, or integration works.

## Post-clearance sequence (not authorization)

1. Obtain and review SEC-01–SEC-05 evidence; retain NO-GO until the authorized reviewer makes a scoped decision.
2. Close per-item ownership and approve PostgreSQL migration, auth/authorization, object lifecycle, and rollback designs.
3. Obtain explicit implementation authorization; implement PostgreSQL compatibility while preserving the SQLite source and rollback artifact.
4. Implement private object storage and durable failure recovery under the approved authorization and retention model.
5. Obtain separate explicit runtime/provider authorization; test only with synthetic data in an isolated development project.
6. Verify rollback, tenant/security controls, transaction behavior, partial-failure recovery, and database/object restoration; publish evidence separately from design documents.
7. Deploy to Render staging only after actual settings are verified and staging is separately authorized.
8. Conduct production readiness review and obtain explicit deployment/data approvals. Real institutional uploads and research experiments remain independently gated.

No step in this sequence is permission to execute it.

## Explicit decisions

- **Independent written clearance exists:** **NO — none was documented in the inspected files. Status: BLOCKED.**
- **Supabase credential revocation is confirmed:** **NO — status remains UNCONFIRMED.**
- **PostgreSQL implementation:** **NO-GO.**
- **Supabase connection or migration:** **NO-GO.**
- **Runtime checks/tests/builds:** **NO-GO.**
- **Render deployment:** **NO-GO.**
- **Real data and research scoring:** **NO-GO pending their separate approvals.**

## Activity record

- **Files inspected:** the six Phase 2C, 2B, 2A, 1D, 1E, and 1F documents listed above.
- **File created:** `docs/phase-2d-blocker-ownership-and-evidence-register.md` (new file; it did not exist before creation).
- **Open blockers:** SEC-01–SEC-05, DOC-01, PG-01, AUTH-01, STOR-01, RB-01, TEST-01, REND-01, DATA-01.
- **Runtime operations:** NONE.
- **Tests/builds:** NONE.
- **Supabase connections:** NONE.
- **Application code and schemas changed:** NONE.

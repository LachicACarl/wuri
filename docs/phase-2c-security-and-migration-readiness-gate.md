# WURI Phase 2C — Security Clearance and Migration Readiness Gate

**Assessment date:** 2026-10-23  
**Assessment method:** Static inspection of local documents and source references  
**Implementation gate:** **NO-GO**  
**Runtime operations performed:** NONE  
**Tests/builds executed:** NONE  
**Supabase connections made:** NONE  
**Application code or database schemas changed:** NONE

## 1. Executive summary

The requested Phase 1 and Phase 2 documents are present in the local repository, including the Phase 2A audit and Phase 2B remediation register. Their contents consistently describe plans and unresolved prerequisites; they do not contain an authorized independent reviewer’s written clearance, evidence that the October 22 forced update was authorized, a conclusive independent resolution of the suspicious cached Vite code, or confirmation that the exposed Supabase service-role credential has been revoked.

The security and implementation gates therefore remain **NO-GO**. Migration readiness is also **BLOCKED**: the Phase 2 documents identify the principal workstreams, but the remediation register is a planning artifact, not proof of implementation or test success. No Supabase connection or Render deployment is authorized by this assessment.

This assessment distinguishes what the reports say from what is independently established here. It inspected the listed local text files and relevant source references; it did not inspect the suspicious cached revision, contact a maintainer, access provider settings, inspect credentials, or query Git or a database.

## 2. Documents and evidence reviewed

The following requested files were present and read as text:

- `docs/phase-1d-independent-security-review.md`
- `docs/phase-1e-provenance-containment-report.md`
- `docs/phase-1f-security-hold-maintainer-handoff.md`
- `docs/phase-2-postgresql-compatibility-design.md`
- `docs/phase-2-database-migration-and-rollback.md`
- `docs/phase-2-private-document-storage-design.md`
- `docs/phase-2-render-deployment-plan.md`
- `docs/phase-2a-design-review-report.md`
- `docs/phase-2b-remediation-register.md`

Relevant static source references include `backend/app/database.py`, `backend/app/main.py`, `backend/app/storage.py`, `backend/app/deployment_readiness.py`, and `backend/migrations/001_initial.sql` through `008_malware_scan_state.sql`, as referenced and assessed in the Phase 2A report. The Phase 2C target file did not exist before this report was created.

No written maintainer or independent reviewer decision was present among the reviewed documents. No repository-host audit records, Supabase Dashboard evidence, provider configuration, or credential values were accessed.

## 3. Security evidence and provenance status

| Question | Status | Evidence and assessment |
|---|---|---|
| What is reported about the suspicious cached Vite configuration? | **REPORTED BUT UNVERIFIED** | Phase 1D and 1F describe an added `node:module`/`createRequire` binding and a long obfuscated top-level dynamic call chain in the cached revision. Phase 1D says ultimate behavior remains unresolved (`phase-1d-independent-security-review.md:35,45-47`; `phase-1f-security-hold-maintainer-handoff.md:35`). The suspicious revision itself was not inspected in this Phase 2C assessment. |
| Is malicious intent or specific network/filesystem/process/credential activity established? | **UNCONFIRMED** | The reports explicitly do not establish malicious intent or those effects; obfuscation and exposed Node capability are treated as reasons for review, not proof (`phase-1d-independent-security-review.md:35,45-46`; `phase-1f-security-hold-maintainer-handoff.md:35`). |
| What is reported about the October 22 forced update? | **REPORTED BUT UNVERIFIED** | Phase 1E/1F report a local `origin/main` reflog entry `fetch: forced-update` at `2026-10-22T17:30:15+08:00` pointing at the suspicious cached commit. Those reports say the record does not identify the initiating person/process, authorization, transport details, or reason (`phase-1e-provenance-containment-report.md:38,56,61-67`; `phase-1f-security-hold-maintainer-handoff.md:19,39,43-48`). This report did not run Git commands or inspect the cached object. |
| Is provenance/behavior conclusively established? | **BLOCKED** | The reports state the actor, authorization, trusted provenance, complete behavior, and whether the revision ran remain unknown or unresolved (`phase-1e-provenance-containment-report.md:65-73,79-91`; `phase-1f-security-hold-maintainer-handoff.md:43-50`). No independent resolution was supplied. |
| Is written clearance from an authorized independent reviewer present? | **BLOCKED** | No such decision was found in the reviewed Phase 1/2 documents. Phase 1D/1F retain NO-GO and specify conditions to reconsider runtime checks (`phase-1d-independent-security-review.md:55-69`; `phase-1f-security-hold-maintainer-handoff.md:66-75`). The authorized reviewer has not been identified by name/contact in the evidence reviewed. |
| Does a clean local Vite configuration resolve the concern? | **VERIFIED as a documented distinction** | Phase 1 reports say the checked-out local config was clean while explicitly stating that this does not resolve cached revision behavior/provenance or prior execution (`phase-1e-provenance-containment-report.md:79-81`; `phase-1f-security-hold-maintainer-handoff.md:9`). It is not evidence that the remote concern is cleared. |
| Has prior execution or compromise been established? | **UNCONFIRMED** | Phase 1D says execution is unknown and Phase 1E/1F say there is no evidence claimed, while requesting an authorized assessment (`phase-1d-independent-security-review.md:47,53`; `phase-1e-provenance-containment-report.md:81`; `phase-1f-security-hold-maintainer-handoff.md:49-50`). Absence of evidence in these reports is not proof of non-execution. |

**Security gate:** **NO-GO.** Required evidence is a documented authorized maintainer investigation of the forced update, independent reviewer assessment of provenance and complete behavior (or a trusted authenticated explanation establishing the exact safe tree), an assessment of possible prior execution, and explicit written authorization for the specific next runtime activity. Runtime authorization would not approve research scoring or real-data transfer by itself.

## 4. Credential-remediation status

| Requirement | Status | Evidence and assessment |
|---|---|---|
| Exposed service-role credential deactivated/revoked | **UNCONFIRMED** | The Phase 2 PostgreSQL and Render plans explicitly say rotation status is unconfirmed (`phase-2-postgresql-compatibility-design.md:64-65`; `phase-2-render-deployment-plan.md:65-66`). No Dashboard confirmation or owner evidence was present. |
| Replacement credential configured privately | **UNCONFIRMED** | No documentary evidence establishes that a replacement was created or placed in an approved secret manager. A proposed secret-handling plan is not evidence of configuration. |
| Authorized services no longer depend on old credential | **UNCONFIRMED** | No provider/service inventory or owner confirmation was present. Do not test or reuse the exposed credential. |
| Relevant project logs reviewed | **UNCONFIRMED** | The plans request that an authorized owner review available logs, but no review record or result was found. |

The authorized Supabase project owner must use the approved Dashboard workflow to revoke/rotate the exposed key and privately document completion, replacement handling, service dependency updates, and available log review. Do not share either credential value. This assessment did not access Supabase or attempt revocation.

## 5. Phase 2A/2B remediation-register coverage

### Phase 2A findings traced

The 14 Phase 2A findings are materially represented in Phase 2B:

- SQLite transaction/function/query inventory and exception mapping: `PG-01`, `PG-02`.
- Storage/database recoverability and state protocol: `STOR-01`.
- Cutover, freeze, rollback and restore: `RB-01`, `RB-02`.
- Per-migration mapping, conflict semantics, conversion policy: `PG-03`, `PG-04`.
- RLS, trusted identity, tenant context, role grants: `AUTH-02`.
- Startup and health behavior: `PG-05`, `REND-02`.
- Provider, CORS/cookies, network/persistence and deployment assumptions: `AUTH-04`, `REND-01` through `REND-05`.
- Research-import lifecycle and object metadata: `STOR-02`, `STOR-03`.
- Security clearance, credential remediation and separate data/research approvals: `SEC-01` through `SEC-04`.
- Post-clearance verification: `VER-01`, `VER-02`.
- Duplicate credential warning and non-readiness claims are effectively covered by `SEC-02` and the executive/phase-gate language.

The register includes unique IDs, evidence references, dependencies, risk, acceptance criteria, and verification methods for its entries (`phase-2b-remediation-register.md:16-74`). It also has phase-level GO/NO-GO criteria (`:75-88`) and a broad approvals section (`:90-101`).

### Register gaps and status

| Gap | Status | Required correction/evidence |
|---|---|---|
| A named responsible owner for every individual remediation item is not consistently included in the register rows. Some rows identify an approval role in prose or dependencies, but that is not a row-level accountable owner. | **BLOCKED** | Add an accountable owner/role column per row and distinguish responsible implementer, decision approver, and verifier where they differ. Do not assign people without authorization. |
| A clear GO/NO-GO consequence is defined primarily by phase, not for each remediation item. Row acceptance criteria exist, but passing/failing one row is not always tied to a gate decision. | **BLOCKED** | Add per-item gate consequence: which later task is blocked by failure, which authority can accept a limitation, and whether any exception is allowed. No exception may override the current security hold. |
| External owner evidence and approvals are placeholders, not attached evidence. | **UNCONFIRMED** | Attach or reference dated authorized decisions when received; keep open until then. |
| Acceptance/verification often distinguishes later testing but is not a result. | **VERIFIED as plan-only** | Preserve the distinction; do not report runtime readiness until authorized tests are actually completed and reviewed. |

Overall, Phase 2B provides broad coverage of Phase 2A, but it is not fully complete against the requested per-item owner and GO/NO-GO traceability requirements. This is a documentation correction, not security clearance.

## 6. Migration-readiness findings

| Area | Status | Finding |
|---|---|---|
| SQLite-to-PostgreSQL schema/query compatibility | **BLOCKED** | Design identifies placeholders, row shape, JSON/time/numeric choices, migration 004/005 semantics, and several application issues, while Phase 2A found omitted application `BEGIN IMMEDIATE` sites and route-level SQLite `randomblob` SQL. Exact query-by-query mapping remains pending. See `phase-2a-design-review-report.md:28,64`; `phase-2b-remediation-register.md:26-37`. |
| Transaction and rollback behavior | **BLOCKED** | Plans correctly disclose that old SQLite is a rollback target only before PostgreSQL authoritative writes, but a complete freeze/cutover/restore/reverse-export runbook and rehearsed recovery are absent (`phase-2-database-migration-and-rollback.md:24-30`; `phase-2b-remediation-register.md:70-73,118-126`). |
| Preservation of existing SQLite database | **REPORTED BUT UNVERIFIED** | Documents require keeping the source and backup unchanged (`phase-2-database-migration-and-rollback.md:13,16,22,26`), but no backup/restore verification was performed or evidenced in this gate. |
| Authentication and institution-level authorization | **BLOCKED** | Existing custom session and membership checks are identified for preservation; database role/RLS identity, tenant context, pool reset, and complete route authorization mapping remain design decisions (`phase-2-postgresql-compatibility-design.md:52,60-67`; `phase-2b-remediation-register.md:40-47`). |
| Private object storage and partial-failure recovery | **BLOCKED** | Private storage is a design only. Upload/delete state machines, idempotency, retries, import-file retention, metadata mapping, provider policy, and restore remain unresolved (`phase-2-private-document-storage-design.md:14-46`; `phase-2b-remediation-register.md:49-56`). |
| Supabase connection and least privilege | **BLOCKED** | No driver, connection role, endpoint/pool configuration, or RLS decision is implemented or provider-verified; exposed key revocation remains unconfirmed (`phase-2-render-deployment-plan.md:33-46,65-68`). |
| Render frontend/backend configuration | **BLOCKED** | Proposed split is not deployed. Build/output, production backend start command, health behavior, service settings, persistent storage, network and domains are unverified (`phase-2-render-deployment-plan.md:5-22,42-59`). |
| CORS, secure cookies, HTTPS and secrets | **BLOCKED** | Current source has local-only origins and GET/POST CORS methods; production origins, route methods/headers, site relationship, CSRF design, HTTPS and secret configuration remain to be decided and later tested (`backend/app/main.py:33-45`; `phase-2-render-deployment-plan.md:48-53`). |
| Synthetic-data integration tests | **BLOCKED** | Test scenarios and prerequisites are planned, but no tests were run; they require explicit runtime/provider authorization first (`phase-2b-remediation-register.md:103-116`). |
| Backup, recovery and deployment rollback | **BLOCKED** | Risks and desired checks are documented, but no backup restore, object restore, cutover rehearsal, or provider recovery evidence exists (`phase-2-database-migration-and-rollback.md:24-30,53-62`). |
| Researcher/institution approvals | **UNCONFIRMED** | Plans correctly require separate data/research-owner approvals; no actual approval evidence was present. Security clearance alone would not authorize real-data use or A0–A4/readiness scoring (`phase-1f-security-hold-maintainer-handoff.md:9,73-75`; `phase-2b-remediation-register.md:90-101`). |

**Migration readiness:** **NO-GO.** The documents are useful design inputs but do not establish implementation compatibility, provider readiness, successful testing, or safe production rollback.

## 7. Outstanding blockers, owners, and required evidence

| Blocker | Required owner/approver | Evidence required to close | Current status |
|---|---|---|---|
| Forced-update actor, authorization, and provenance | Repository owner/authorized maintainer | Trusted repository-host and client/automation audit review with documented conclusion | **BLOCKED** |
| Complete suspicious-code behavior and prior-execution assessment | Authorized independent security reviewer and incident owner as applicable | Written independent review of provenance/behavior and documented assessment of any execution evidence | **BLOCKED** |
| Runtime clearance scope | Authorized independent reviewer plus maintainer where repository authorization is required | Explicit dated written permission naming reviewed tree, permitted activity, limits, and stop conditions | **BLOCKED** |
| Exposed Supabase key revocation and service updates | Authorized Supabase project owner | Private Dashboard completion confirmation, replacement secret custody, dependent-service update confirmation, and available log-review record | **UNCONFIRMED** |
| PostgreSQL implementation decisions | Application/database owner and security reviewer | Closed query/transaction/error/schema/role design with approved migration and rollback decisions | **BLOCKED** |
| Object and real-data lifecycle | Institutional data custodian and research owner | Approved access, purpose, retention/deletion, backup, and recovery policy per object/data class | **UNCONFIRMED** |
| Hosting and deployment configuration | Deployment owner and security reviewer | Actual authorized Render/project details for commands, domains, network, health, persistence, CORS/cookies, secrets, and recovery | **UNCONFIRMED** |
| Phase 2B row-level traceability | Phase 2B document owner and relevant approvers | Register updated with accountable owner and explicit per-item gate consequence; no implementation implied | **BLOCKED** |

The role labels above identify the authority needed; this review does not know or invent the individuals’ identities. The independent reviewer’s identity and authorization evidence remain outstanding.

## 8. Conditions before the first authorized Supabase test

All of the following must be satisfied before a connection is attempted:

1. Written independent security clearance and maintainer decision resolve the repository concern and explicitly authorize the named runtime/provider test against a specified reviewed tree.
2. The authorized Supabase owner privately confirms revocation of the exposed service-role key, replacement/secret custody, dependent-service updates, and available project-log review. No key value is shared.
3. A separate isolated development Supabase project is selected and verified by its owner; it contains synthetic data only and is segregated from production.
4. PostgreSQL implementation and schema decisions are approved; the selected driver, connection mode, role grants, transaction behavior, migration runner and failure policy are specified.
5. The app’s custom HMAC session and membership checks are preserved or any separately approved identity change is explicit. If RLS is used, trusted tenant context, least-privilege role, pool cleanup and fail-closed behavior are reviewed.
6. Storage behavior for this test is scoped. If object storage is exercised, its private access, role scope, state machine and cleanup/recovery plan are approved; otherwise no real or private documents are included.
7. A written test plan states synthetic fixtures, exact operations, expected results, negative authorization cases, failure injection, stop criteria, cleanup, evidence handling and rollback. It cannot touch the local SQLite source database or real institutional/research data.
8. The authorized operator and security approver sign off on the exact test environment and credentials path. Secrets remain server-side and are not placed in frontend variables, source, logs, or chat.

Passing a narrowly scoped test would verify only the tested behavior in that isolated configuration. It would not itself authorize Render production deployment, real-data migration, or research experiments.

## 9. Conditions before Render deployment

- Security clearance explicitly covers deployment, and SEC credential remediation is confirmed privately.
- PostgreSQL adapter/migrations and private storage implementation are complete and pass the separately authorized isolated verification plan.
- Actual Render service/runtime configuration is verified: roots, commands, versions, frontend output/fallback, backend process, port, health semantics and environment variables.
- Persistent document storage and coordinated database/object backups have defined access controls, recovery objectives, and restore evidence; deployment filesystem durability is not assumed.
- Production HTTPS/domain topology, exact CORS origins/methods/headers, secure cookie/SameSite behavior, CSRF approach, and server-only secrets are approved and verified in authorized staging.
- Connection endpoint/pool mode, least-privilege credentials, network reachability, TLS, worker/pool bounds, monitoring, redaction and incident ownership are documented from actual approved configuration.
- The source SQLite database and backups remain preserved; cutover freeze, reconciliation thresholds, authority switch, rollback cutoff and post-cutover write treatment have been rehearsed in an isolated environment.
- Security, deployment, data-owner and (for relevant data) institutional/research approvals explicitly cover the intended deployment and operations. Real university uploads and A0–A4/readiness scoring require their own separate approvals.

## 10. Next actions in dependency order

1. **Keep NO-GO and preserve state.** No runtime, tests, builds, database/provider access, migration or deployment.
2. **Identify and engage authorized reviewers through approved channels.** Provide the Phase 1D–1F handoff and obtain the written repository/security decision; do not infer the reviewer or clearance.
3. **Have the authorized Supabase owner revoke/rotate the exposed credential in the Dashboard.** Obtain private confirmation and service/log review evidence without sharing credential values.
4. **Correct Phase 2B traceability.** Add per-row accountable owner/approval, explicit blocking consequence, and evidence status; leave all unapproved items open. This is documentation work only and does not clear security gates.
5. **Close design decisions and approvals.** Complete SQL/migration mapping, auth/RLS role model, object recovery/lifecycle, cutover/rollback, Render settings and data/research approvals.
6. **Request explicit implementation authorization.** Only after security clearance and design closure should Phase 3 code changes be considered.
7. **Request separate runtime/provider authorization for the first synthetic Supabase test.** Implement first, then test only the approved isolated scope; record actual results separately.
8. **Consider Render staging/deployment only after integration, object recovery, security, and rollback gates pass** and deployment is explicitly authorized.

## 11. Readiness decision

**Implementation gate: NO-GO.** The security hold remains unresolved. There is no documented authorized independent reviewer clearance, no conclusive provenance/behavior resolution, and no credential-revocation confirmation. Phase 2B is a remediation plan, not proof that its gates have passed. Do not proceed to Phase 3, connect to Supabase, run the application, or deploy to Render.

**Runtime operations performed: NONE.**  
**Tests/builds executed: NONE.**  
**Supabase connections made: NONE.**  
**Application code or database schemas changed: NONE.**

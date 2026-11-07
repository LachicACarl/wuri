# WURI current security and readiness status addendum

**Assessment date:** 2026-11-08  
**Base revision reviewed:** `4a2bb736f68ffba66c9c15c96656c442f8d04e5f`  
**Scope:** Read-only GitHub metadata and documentation review; documentation-only change  
**Security / implementation / real-intake decision:** **NO-GO**

## Purpose

This addendum records material repository-readiness findings after the Phase 2D blocker register was written on 2026-10-23. It supplements, and does not replace or silently rewrite, the historical security reports and blocker register. It is not an independent security clearance, deployment attestation, or authorization to process institutional data.

## Verified repository and CI evidence

| Item | Current evidence | Interpretation |
|---|---|---|
| PR #4 | Merged 2026-11-07; merge commit `4dad0785b38417a1bbbaf387c770ba6f6edacbe0`; post-merge validation run #121 passed. | Parser, upload, authentication, CORS and readiness hardening is present in the merged code. CI success is not an external security review. |
| PR #5 | Merged 2026-11-07; merge commit `a6a9f2b668c0d111aed8259bc4b2beedc1212ab5`. | Documentation accurately distinguishes local SQLite/local filesystem configuration from managed PostgreSQL/durable object storage and records the read-only Render inspection limitation. |
| PR #6 | Merged 2026-11-07; merge commit `4a2bb736f68ffba66c9c15c96656c442f8d04e5f`. | Deployment documentation now explicitly says manual controls cannot be certified by the current preflight and that no signed/auditable attestation workflow exists. |
| PR #6 validation | Workflow run #124 completed successfully: backend tests and Python compilation; frontend npm audit, ESLint and build. | These are code/CI checks only. They do not establish scanner trust, deployment isolation, provider configuration, security clearance, or data-use approval. |
| Main branch protection | GitHub branch metadata reported `protected: false` and protection disabled at the time of this read-only inspection. | Required reviews/status checks are not enforced by branch protection at this observation. Enabling rules is a separate repository-settings change and has not been performed or authorized here. |
| Render service discovery | The five accessible Render workspaces previously inspected contained no WURI service. | No WURI deployment was identified in those accessible workspaces. This does not prove no service exists in any other account/workspace. |

## Additional security finding: scanner executable identity

The merged application readiness logic does not independently attest the identity or integrity of the configured malware-scanner executable. The upload path can interpret a configured executable's exit code `0` as a clean scan result. A malicious, substituted, placeholder, or otherwise untrusted executable could therefore falsely report clean content.

PR #6 documents this limitation but does not enforce scanner identity at runtime. Treat this as an **OPEN, HIGH-PRIORITY SECURITY BLOCKER**. Do not configure an arbitrary shell utility, test command, placeholder, or unreviewed executable as the production scanner. Do not accept the scanner check as complete merely because a path exists or a command exits successfully.

Required closure evidence, before any real intake:
1. An authorized security reviewer approves the scanner threat model and the exact scanner identity/integrity verification design.
2. An authorized deployment owner identifies the approved scanner binary or wrapper, its trusted provenance, version/update process, execution permissions, and expected failure behavior.
3. The implementation is changed only under explicit written security and implementation authorization.
4. Authorized tests demonstrate clean, infected, timeout, crash, unavailable, tampered/substituted-binary, and malformed-output cases; failures must fail closed.
5. Independent review accepts the implementation and the deployment-specific evidence. Test results alone do not attest the production binary.

## Updated blocker status

The following items remain open unless and until the specified authority supplies the evidence:

- **SEC-01 to SEC-03 — BLOCKED:** suspicious cached Vite revision provenance/behavior, forced-update actor/authorization, and explicit independent security clearance remain unresolved in the existing handoff evidence.
- **SEC-04 to SEC-05 — UNCONFIRMED:** exposed Supabase service-role credential revocation/replacement custody, dependent-service updates, and project/access-log review have not been confirmed. Do not connect to Supabase or inspect credentials.
- **SEC-SCAN-01 — OPEN / HIGH:** scanner executable identity and integrity are not enforced at runtime; PR #6 is documentation only.
- **BRANCH-01 — OPEN:** GitHub reports `main` branch protection disabled at the observation time. Repository owner must decide whether to enable required review/status-check rules. No settings were changed.
- **PG-01, AUTH-01, STOR-01, RB-01, TEST-01, REND-01 — BLOCKED:** PostgreSQL compatibility, tenant/auth model, private object storage/recovery, cutover/rollback, isolated synthetic integration tests, and deployment configuration still require approved design, implementation and evidence.
- **DATA-01 / research gate — BLOCKED or UNCONFIRMED as applicable:** authorized institution-level source material and applicable data/research approvals remain prerequisites. No CHED institution-level source artifact was received or inspected as part of this addendum.

## Explicit work boundary

This addendum was prepared from repository documentation and read-only GitHub metadata. No application code, tests, builds, dependency installation, provider connections, Supabase credentials, database, Render settings, deployments, or research data were accessed or changed.

The following remain prohibited until their respective written approvals are received:
- Runtime execution, test/build/install activity, and security-sensitive implementation while the repository security hold remains active.
- Supabase access, migrations, or credential inspection.
- Production deployment or changes to Render/provider settings.
- Real institutional document intake, CHED data acquisition/transformation, readiness scoring, or Phase 17G.

A written security clearance must identify the exact reviewed tree and permitted activity. A clearance for one activity does not imply authorization for another. The CHED source-data gate remains separate from the software security gate.

## Current decision

**Security clearance: NOT DOCUMENTED.**  
**Scanner trust: NOT VERIFIED; runtime identity enforcement remains an open issue.**  
**Main branch protection: DISABLED at the observed GitHub metadata snapshot.**  
**Supabase credential remediation: UNCONFIRMED.**  
**Production deployment and real institutional intake: NO-GO.**  
**Research data acquisition / Phase 17G: ON HOLD pending authorized, dated institution-level source artifact and provenance review.**

This addendum records status; it does not close any blocker or grant authorization.

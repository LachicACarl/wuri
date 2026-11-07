# Phase 1F — Security Hold and Maintainer Handoff

Prepared: 2026-10-23 (Asia/Manila)

## Purpose and current decision

This handoff summarizes the local evidence for an authorized repository maintainer. It does not allege malicious intent or attribute the ref update to a person or process.

**Containment remains in effect. Runtime testing/builds: NO-GO.** Treat cached commit `8595267641138faf240e9bd0a27b9f565bf3734f` as untrusted until its provenance and generated-code behavior are independently resolved. The clean local Vite config does not clear the risk associated with the cached revision. The separate research gate also remains closed: the A0 protocol is `pending_researcher_approval`; A0–A4 experiments and institutional readiness scoring are not authorized by this handoff.

## Timeline from existing reports

| Time recorded | Documented event | Qualification |
|---|---|---|
| 2026-08-06 04:08:21 +08:00 | Local path history includes commit `2fed291e51f8fb971ed7d1b17774494414bc697c`; the Vite config is the clean 204-byte blob. | Earlier point in the locally available config history; not evidence of the file's first-ever creation. |
| 2026-09-01 14:38:14 +08:00 | Suspicious commit `8595267…` records author date and introduces the 7,057-byte Vite config; parent is `dd710029…`. | Committer timestamp is recorded as `2026-09-01 07:38:14 +01:00`, which is the same UTC instant expressed at a different offset. Git author/committer values are metadata, not verified identity. |
| 2026-09-01 14:38:21 +08:00 | The `origin/main` reflog records an update by push to local sibling commit `aafc995…`. | This is a local reflog entry; actor/authorization is not independently established here. |
| 2026-10-22 (report date) | Phase 0A triage and Phase 1D static review document that their reviewers did not fetch or run the suspicious revision. | These statements describe the actions of those reviews, not every process that may have touched refs at another time. |
| 2026-10-22 17:30:15 +08:00 | Phase 1E reports an `origin/main` reflog entry `fetch: forced-update` to `8595267…`. | Local reflog event time. The initiating user/process, authorization, transport details, and reason are unknown. |
| 2026-10-23 | Phase 1E records that current local `main` remains `aafc995…`; it and `8595267…` are siblings with common parent `dd710029…`. | Neither is an ancestor of the other based on local objects. No external repository state was checked. |

## Evidence inventory

### Directly reported Git evidence

- Current local `HEAD`: `aafc995a937bc64e473ffe4206ed203635e4f21b`; current local Vite config is reported as 204 bytes, blob `9930e284bb6a16e1cabf33494775a29d43b3e36f`.
- Suspicious cached commit: `8595267641138faf240e9bd0a27b9f565bf3734f`, parent `dd710029dc03996a19f208fcb10823cadb51e0cb`, subject `updated system`.
- Cached config: 7,057 bytes, blob `fd3346ae65a2bea4b58014fff39b09668628bc39`; available through local `origin/main` and `origin/HEAD` refs.
- Local `main` and the suspicious commit are sibling commits. The suspicious commit is not established as part of local `main` ancestry.
- The raw commit object, as inspected in Phase 1E, has no embedded `gpgsig` header. This does not establish wrongdoing.
- `origin/main`'s local reflog records `fetch: forced-update` to the suspicious commit at `2026-10-22T17:30:15+08:00`.

### Static source observations

The Phase 0A/1D reports describe the cached `university-ranking-dss/vite.config.js` as adding `node:module`/`createRequire`, appending a long obfuscated top-level line, mutating globals, and exposing `require` plus available module/path values under computed keys. Phase 1D's independent read confirms an unconditional obfuscated dynamic call chain, while explicitly distinguishing the exact generated behavior as unresolved. The earlier Phase 0A static transformation reported a decoded `constructor` and nested `eval`; Phase 1D did not independently derive those identifiers from raw text. No report establishes network, filesystem, process, credential, environment, persistence, or exfiltration behavior. Malicious intent is not established.

### Inferences requiring confirmation

- The reflog label is consistent with a fetch updating the remote-tracking ref by forced update; it does not identify who/what initiated it or why.
- The suspicious commit may have arrived in the object database as part of that ref update, but the reports do not contain a transport/object-transfer audit proving this path.
- The date and self-asserted author/committer metadata do not establish the contributor's identity or the intended change.

### Unknowns requiring authorized records or review

- Initiating actor/process, authorization, client, and exact mechanism for the October 22 update.
- Repository-host audit events and server-side reference history around the forced update.
- Trusted provenance, source, review history, and intended changes for the suspicious commit.
- Full behavior and all capabilities reachable through the generated code.
- Whether this revision was ever checked out, imported, or executed in any environment.
- Whether repository access or credential exposure requires a separate response. The existing evidence warrants review by the appropriate security owner but does not prove credential compromise.

## Requested maintainer investigation

Using authorized repository-host and client audit records, please determine:

1. Who or what initiated the forced update, and when? Was it expected and authorized?
2. Which account, workflow, credential identity, or automation was involved? Please record identity metadata without exposing secret values.
3. What repository-host audit events and reference history are available around `2026-10-22T17:30:15+08:00`?
4. Can the suspicious commit's source, author identity, review history, and intended changes be independently verified through trusted records or the author/maintainer?
5. Can an independent security reviewer resolve the generated-code chain and all reachable side effects without executing it?
6. Is a separate repository-access or credential-exposure review warranted, and which security owner should perform it?
7. Is there authorized evidence that the revision was run? If so, route host/process review through the appropriate incident process.

Please do not share credential values in the handoff or response. This report does not request a fetch, ref repair, access change, or credential rotation.

## Containment and criteria for reconsidering the hold

Until the questions above are resolved:

- Keep the suspicious cached revision untrusted; do not check it out, merge, deploy, import, or execute it.
- Keep Vite/npm commands, builds, frontend tests, application servers, and other runtime validation at **NO-GO**.
- Preserve the current local worktree, user edits, untracked backend/docs, and snapshots.
- Keep A0–A4 and actual readiness scoring blocked independently of the code-integrity review.

Reconsider runtime validation only after an authorized maintainer explains and validates the forced update from trusted audit records; an independent security reviewer establishes the payload's complete behavior and provenance (or confirms the exact clean code to be used); any evidence of prior execution has been assessed by the security owner; and the next validation is explicitly authorized against the reviewed clean local tree. An opaque or unexplained dynamic-execution chain means the hold remains in place. Clearing the code-integrity hold would not approve research execution or scoring.

## Scope and actions

This is a documentation handoff based on the existing Phase 0A, Phase 1D, and Phase 1E reports. No repository-host contact or external audit lookup was performed. No fetch, pull, push, checkout, merge, rebase, reset, clean, ref mutation, credential inspection, access change, application edit, test, build, script, Vite command, or runtime check was performed. The only file created is `docs/phase-1f-security-hold-maintainer-handoff.md`; repository state, application code, and runtime behavior were not changed or tested.

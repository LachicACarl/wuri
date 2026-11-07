# Phase 1D — Independent Vite Configuration Security Review

Review date: 2026-10-22 (Asia/Manila)

## Scope and methods

This was a read-only static review of the current local Vite config and the already-cached commit object identified in `docs/security-triage-report.md`. I read the triage report, inspected local source text, used read-only Git object/ref/blob/diff queries, and obtained an independent second static reading of the cached blob. No source or generated JavaScript was imported, evaluated, or executed. No network access, fetch, checkout, merge, Vite/npm command, test, build, application server, or repository script was used.

## Files and revisions inspected

| Item | Identity/evidence | Result |
|---|---|---|
| Current local file | `university-ranking-dss/vite.config.js`, 204 bytes; blob `9930e284bb6a16e1cabf33494775a29d43b3e36f` | Plain Vite configuration: imports `defineConfig`, React, and Tailwind at lines 1–3; exports the React/Tailwind plugin config at lines 5–10. No appended payload is present. |
| Current local `HEAD` | `aafc995a937bc64e473ffe4206ed203635e4f21b`; config blob matches working tree | Clean config. `HEAD` and the cached commit share parent `dd710029dc03996a19f208fcb10823cadb51e0cb`; they are sibling commits. |
| Cached revision | `8595267641138faf240e9bd0a27b9f565bf3734f`, available through cached `refs/remotes/origin/main` and `refs/remotes/origin/HEAD`; config blob `fd3346ae65a2bea4b58014fff39b09668628bc39`, 7,057 bytes | The cached config starts with `node:module`/`createRequire` at lines 1–2, retains the ordinary Vite config, then appends a 6,761-character obfuscated line 12 after `});`. The cached commit's parent has the same clean config blob as local `HEAD`. |
| Prior triage | `docs/security-triage-report.md` | Records the earlier static string-table transformation that identified a decoded `constructor` property and nested `eval`, while leaving final effects and intent unresolved. |

The local config still matches the previously reported clean 204-byte state. A read-only diff reports the cached change as 3 insertions and 1 deletion; most of the payload occupies the appended single long source line. No branch activation or worktree change was made.

## Evidence-based findings

### Directly visible in the cached source

- Lines 1–2 import Node's `createRequire` and create a `require` binding.
- On line 12, the payload sets `global.o` to a fixed string, defines character permutation/string substitution routines, and writes `require` and conditionally available `module`, `__dirname`, and `__filename` values onto `global` using computed property names.
- The line contains a fixed encoded string table and numeric permutation seeds. It derives a computed property key from that material, obtains a value through `yIr[IuG]`, aliases that value as `NAN`, calls it to produce `Izd`, calls `Izd` with another decoded string, then invokes `NAN(HfA, soR)` and calls the returned `BrW` with fixed argument `2333`. These calls occur in the top-level expression appended to the Vite config.
- In the raw blob, the `AST` lookup begins around character 2,740 of line 12 and the final `BrW(2333)` invocation around character 6,736. The exact execution semantics depend on the computed key and generated string contents.

This is strong direct evidence of an obfuscated, unconditional dynamic function-construction/invocation chain during config module evaluation. The raw line contains no literal `eval` or `eval(` token. The earlier triage reports that a separate static string-table transformation exposed a nested `eval` call and decoded `constructor`; the independent second reading confirmed the indirect construction/invocation shape but did not independently decode those final identifiers or generated body. Accordingly, this review treats the exact `Function`/`eval` interpretation as prior static-analysis evidence, not as directly readable raw source.

### Side effects and capability limits

The visible source definitely mutates global state and makes Node module/path values available to the generated code under computed global keys. If the Vite loader imports this config, JavaScript evaluates its top-level expression; this is a source-level consequence, not a runtime test performed here.

No literal URL, network API, filesystem API, process/child-process API, or environment-variable name was found in the visible payload text during direct text checks. Because the relevant names and generated body are obfuscated, their absence from visible text does **not** establish that the final code avoids those capabilities. The wrapper exposes `require`, which can provide access to Node modules. The final generated behavior, including any network, filesystem, process, credential, environment, persistence, or exfiltration activity, remains unresolved.

## Confirmed behavior versus hypotheses

| Claim | Assessment |
|---|---|
| The current local config contains the payload | **Not supported**; local file and `HEAD` use the clean 204-byte blob. |
| Cached config appends top-level obfuscated calls and mutates globals | **Confirmed by raw source text.** |
| The chain is intended to construct and execute generated code | **Strongly indicated by the computed function-property lookup and call sequence; exact constructor resolution is not decoded in this independent reading.** |
| A nested `eval` call exists | **Recorded by the earlier triage's static transformation; not independently rederived from the raw line in this review.** |
| Network, filesystem, process, credential, environment, or exfiltration behavior occurs | **Not established.** These remain possibilities because of obfuscation and exposed Node capability, not observed facts. |
| The code is benign or malicious | **Unresolved.** Obfuscation and dynamic execution alone do not establish intent. |
| The cached revision was executed | **Unknown.** No execution evidence was assessed here; code presence is not execution evidence. |

## Provenance and remaining risk

The cached commit object records author/committer metadata, a timestamp, a subject, and parent `dd710029…`. These Git fields are self-asserted metadata; this review did not authenticate the contributor, verify a trusted signature, contact an upstream maintainer, or establish why the payload was added. The suspicious commit is locally cached under the remote-tracking ref names, but that alone does not authenticate its origin. The clean local commit is a sibling of it, not a descendant that removed the payload.

The exact purpose and full behavior remain opaque, and the cached ref's provenance is not independently established. No evidence of prior execution or compromise is claimed. Risk remains unresolved and high enough to retain the execution restriction.

## Recommendation: NO-GO for runtime testing

Do not run Vite, npm scripts, builds, frontend tests, or application runtime checks yet. The local config is clean, but this does not resolve the suspicious cached object's behavior or provenance, nor does it establish whether it was previously executed. The research gate is separate and remains closed: A0–A4 and actual readiness scoring remain disabled pending researcher approval and authorized source data. The Phase 1C decision to reject tied Best-Fit results remains a fail-closed policy choice requiring researcher review; this security review does not treat it as dissertation-approved.

### Criteria to reconsider the runtime restriction

All of the following should be documented before lifting the restriction:

1. An independent security reviewer resolves the complete generated-code chain from the cached source without executing it, or an authenticated trusted source establishes the exact intended change and its provenance.
2. The decoded behavior and all reachable capabilities/side effects are understood. Any opaque dynamic execution must be removed or otherwise explicitly justified and reviewed before that revision is considered safe to use.
3. The exact tree/config to be tested is confirmed to use the clean reviewed local config, with no merge or activation of the suspicious cached revision.
4. The review records whether there is evidence of prior execution and, if evidence is found, routes host/process/credential investigation through the appropriate security process.
5. Runtime validation is limited to the cleared local tree and software fixtures; it is not treated as authorization for empirical scoring. Research approvals, authorized evidence, model artifacts, framework locks, expert labels, and unresolved methodology decisions remain separate prerequisites.

If provenance or behavior cannot be established, retain the NO-GO recommendation.

## Actions performed and avoided

Performed: read the triage report and local config; inspected cached Git metadata, refs, blobs, parent and read-only diff; searched the suspicious source as text; obtained an independent static second reading; recorded this report.

Avoided: fetching, checking out, merging, activating, importing, evaluating, or executing the cached revision or payload; running Vite, npm, tests, builds, servers, or scripts; editing application/config files; changing the index or Git history; printing credential values.

Only `docs/phase-1d-independent-security-review.md` was created. Existing App.jsx edits, untracked backend/docs, snapshots, and unrelated work remain preserved. This review does not clear the security gate and does not claim runtime behavior or repository safety has been verified.

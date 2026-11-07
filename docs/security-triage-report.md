# WURI Phase 0A security triage

Audit date: 2026-10-22 (Asia/Manila)

## Executive risk assessment

**Risk: high; treat the cached remote Vite configuration as untrusted.** Static analysis confirms that its appended code reconstructs and executes generated JavaScript using the `Function` constructor and `eval`. The code is heavily obfuscated and has additional decoding layers, so this review does not establish its final effects or intent. The code is suspicious and unsafe to run; malicious behavior is **not confirmed**.

The checked-out worktree and local `HEAD` contain a short, ordinary Vite configuration with no payload. The suspicious 7,057-byte version is in cached `origin/main` at `8595267641138faf240e9bd0a27b9f565bf3734f` (and the `origin/HEAD` alias). No evidence that it has been executed was found; code presence alone is not execution evidence.

## Revisions and affected file

Path: `university-ranking-dss/vite.config.js`

| Source | Revision or state | Blob / size | Finding |
|---|---|---|---|
| Working tree | Current local file | `9930e284bb6a16e1cabf33494775a29d43b3e36f`, 204 bytes | Clean Vite config; no appended code. |
| Local commit | `HEAD` `aafc995a937bc64e473ffe4206ed203635e4f21b` | Same clean blob, 204 bytes | No payload. |
| Cached remote | `origin/main` `8595267641138faf240e9bd0a27b9f565bf3734f` | `fd3346ae65a2bea4b58014fff39b09668628bc39`, 7,057 bytes | Suspicious appended code. `origin/HEAD` points to this same commit. |
| Cached remote parent | `dd710029dc03996a19f208fcb10823cadb51e0cb` | Clean 204-byte version | No payload. |
| Earlier local revision | `2fed291e51f8fb971ed7d1b17774494414bc697c` | Same clean blob, 204 bytes | No payload. |

The payload first appears in the locally available history at remote commit `8595267`, dated 2026-09-01 14:38:14 +08:00, whose parent is `dd71002`. Local commit `aafc995` is a sibling of `8595267` with the same parent and retains the clean config; the local branch did not merge or check out the suspicious revision. The cached refs inspected contain only two config blob versions: the clean version and the suspicious version, with the latter reachable through the `origin/main` and `origin/HEAD` refs.

## Location and static behavior

In `origin/main`, lines 1–2 add the Node built-in import `node:module` and create a `require` binding. Line 12 appends roughly 6,700 characters after the normal `defineConfig` expression. It begins by assigning a global property, then defines character-permutation and string-decoding routines. It also assigns `require`, `module`, `__dirname`, and `__filename` to dynamically named global properties.

Static transformation of the embedded string tables, without executing the payload, exposed the property name `constructor` and the following behavior:

- The code obtains a function constructor through a decoded property lookup.
- It constructs functions from decoded strings and invokes them at module top level (`BrW(2333)`).
- A further decoded layer contains an `eval(...)` call.

These are confirmed dynamic code execution mechanisms. The final generated code remains obfuscated, so its effects cannot be reliably determined from the present review. The visible wrapper does not contain literal network URLs, environment-variable names, child-process API names, or filesystem API names. Their absence from visible or partially transformed text does not rule out computed access in the remaining decoded layers. The code makes Node module facilities available globally, increasing what the hidden code could access.

The appended expression is at top level and is not guarded by a Vite command or environment check. It runs if Node imports this config. Vite normally loads `vite.config.js` for Vite commands such as `dev`, `build`, and `preview`; none were run in this triage. The added `node:module` import is a Node built-in, not evidence of a new third-party package dependency.

## Exposure and scope

- The worktree config and local `HEAD` config are clean. The index is clean.
- The payload is present in the cached `origin/main` commit and the alias `origin/HEAD`; it is not in the current local commit or working-tree config.
- All 48 locally available refs were checked for this path. They resolve to only the clean or suspicious blob; only the cached remote commit and its alias point to the suspicious blob.
- A first-party source search under `university-ranking-dss/src`, `backend`, and the Vite config found no matching dynamic-code indicators outside the affected config. Dependencies were excluded from this statement; this was not a full malware scan of dependencies or the machine.
- The existing uncommitted `App.jsx` change remains present at 1,567 insertions and 268 deletions. The backend and documentation trees, and six `App.jsx` snapshots, remain untracked as they were before triage.
- No evidence of execution was discovered. This read-only review did not inspect process telemetry, antivirus logs, shell history, or endpoint records, and cannot determine whether someone ran the suspicious revision before this audit.

The Phase 0 baseline correctly called out the obfuscated remote Vite payload and the local/remote commit divergence. This report adds the exact blob and commit identities and confirms dynamic code construction/evaluation. The earlier baseline's wording that the local commit “appears to remove” the payload should be read as a content comparison only: `aafc995` is a sibling commit retaining the clean version, not a descendant that removes code from `8595267`.

## Evidence and commands

Inspection used cached Git objects and local files only. No fetch or network access was performed. Commands included:

- `git status --short`, `git diff --numstat`, and `git diff --cached --numstat`
- `git rev-parse` and `git cat-file -s` for the current, remote, and historical Vite config blobs
- `git show <revision>:university-ranking-dss/vite.config.js` for static source reads
- `git log` and `git show -s` for local commit ancestry and timestamps
- `git for-each-ref` plus read-only blob comparisons for locally available refs
- `git grep -l` on first-party frontend/backend source paths for dynamic-code and payload-signature indicators
- Static string-table transformations implemented in PowerShell to inspect decoded identifiers and generated-code structure; the resulting JavaScript was not evaluated, imported, or executed

No Vite, npm script, JavaScript file from the suspicious revision, frontend/backend test, or application command was run. No fetch, merge, checkout, reset, rebase, staging, commit, or push was performed.

## Containment and recommended next steps

1. Keep cached `origin/main`'s Vite config unexecuted and do not merge or deploy that revision.
2. Preserve the existing worktree, index, untracked backend/docs, and `App.jsx` snapshots. Do not clean or reset the repository.
3. Before using Vite commands, have a second reviewer inspect the decoded layers and establish the provenance and intended contents of commit `8595267` from a trusted source. Do not rely on a fresh fetch alone as proof of safety.
4. If independent evidence shows the suspicious revision was executed, investigate the relevant host, process, credential, and filesystem history through the appropriate security process. This triage has no such evidence and makes no compromise claim.
5. Resume Phase 1 source review or edits only against the current clean local config, preserving the worktree changes. Keep Vite-driven build/dev/preview checks paused until the payload's provenance and full behavior have been independently resolved.

## Handoff decision

**Safe to resume non-executing source review and carefully scoped Phase 1 edits on the current local branch: yes. Safe to run Vite, merge the cached remote revision, or declare the repository security question resolved: no.** The local config itself is confirmed clean, but the remote payload's final behavior and any prior execution remain unresolved. Confidence is **high** that the cached remote config contains top-level dynamic code execution, **high** that the current local config does not, and **low** regarding the payload's ultimate purpose or side effects.

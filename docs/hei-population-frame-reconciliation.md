# Philippine HEI population-frame reconciliation

## Status and scope

This document defines a reproducible reconciliation plan for a candidate
Philippine higher education institution (HEI) population frame. It does not
freeze a population, establish a national institution count, approve the
sampling design, or authorize recruitment.

The platform is intended to support Philippine HEIs. The dissertation's
institutional evidence sample remains a separate, unresolved research
decision. Membership in a candidate population frame, eligibility for a
ranking framework, evidence authorization, and participation are separate
states.

The current leading sampling proposal remains **stratified purposive
sampling, not approved**. The A0 protocol remains
`pending_researcher_approval`.

## Dissertation boundary

The available copy of `UniversityRanking_V3.1.docx` was inspected directly.
Chapter 3, Section 3.3.3, specifies purposive sampling for specialized
respondents: five domain experts and at least 30 system evaluators. It does
not specify a national CHED frame, an HEI sampling unit, an HEI sample size,
or a probability design for institutional evidence. The five experts, 30
system evaluators, and the 70:15:15 labeled-case split must not be used as an
institution sample-size calculation.

The dissertation's framework scope remains WURI 2026, THE World University
Rankings 2026, QS World University Rankings 2026, and UI GreenMetric 2025.
Eligibility and assessment units must be verified separately for each
edition.

## Candidate source assessment

The following sources are candidates, not interchangeable evidence of a
complete frame.

| Source | Issuer and reference information | Unit likely represented | Access finding on 2026-10-16 | Frame value and limitations |
|---|---|---|---|---|
| [CHED Statistics](https://ched.gov.ph/statistics/) | CHED's published statistics report 2,334 HEIs as of June 26, 2025 | Aggregate HEI distribution table; not established as institution-level records | Published aggregate and exclusions are documented, but no raw machine-readable institution-level artifact was retained | Historical coverage reference only. The table includes BARMM SUC main and satellite campuses and excludes 85 BARMM private HEIs and 7 other government HEIs; it is not a complete sampling frame. |
| [CHED HEIDA](https://heida.ched.gov.ph/) | CHED Higher Education Institution Data Analytics service; the landing page identifies a public HEI directory and describes time-aware data features | HEI directory records, with campus/region fields to be confirmed from a retained export | Landing page was reachable and linked to the public directory; no dated export or API response was obtained | Promising primary candidate if an authorized, dated export can be retained. Completeness, identifier semantics, campus hierarchy, update date, and access terms remain unresolved. |
| [CHED list of HEIs](https://legacy.ched.gov.ph/list-of-higher-education-institutions-2/) | CHED legacy publication; publication date and file version were not established | Likely a list of institution or campus entries; exact unit requires inspection of the retained file | Page was reachable, but the fetched content was an accessibility shell and did not provide a usable list snapshot | Useful historical cross-check only after the actual list/file and publication metadata are retained. Legacy naming and coverage may be stale or inconsistent with HEIDA. |

The repository currently contains URLs and notes about these sources, but no
immutable snapshot, machine-readable export, or source-file hash for them.
Therefore, no reproducible source-derived record count is reported here.
The Phase 17E acquisition status is tracked in
[`hei-population-source-inventory.md`](./hei-population-source-inventory.md).

CHED's published 2,334 figure is retained as a verified historical aggregate
with its exact date and exclusions. It must not be treated as the current
population count or converted into a complete institution frame by simply
adding categories. A permitted institution-level artifact is still required.

## Unit definitions

The reconciliation must preserve these distinct levels:

1. **Institution:** a legally or administratively distinct HEI record and the
   proposed primary recruitment unit, subject to approval.
2. **Campus or branch:** a subordinate location linked to an institution when
   the source identifies that relationship.
3. **Institution-framework assessment:** an institution's eligibility,
   evidence, and assessment state for one framework edition.
4. **WURI program/case:** an innovation program or case nested within an
   institution; it is not an institution or institution-wide ranking
   observation.

Source records must retain their original unit labels. A name match alone
must not merge institutions, campuses, branches, or programs.

## Reproducible reconciliation procedure

### 1. Acquire and preserve source snapshots

For every source actually used:

- record the exact URL or approved local path;
- retain the original downloaded file or response without edits;
- record retrieval timestamp, publication/update date, reporting period, and
  access method;
- calculate a content hash and record file type and size;
- record access restrictions, terms, and any failed retrieval;
- assign a versioned `source_snapshot_id`.

If a source cannot be downloaded or exported under permitted access, record it
as identified but unavailable. Do not reconstruct records from search
snippets, screenshots, or an aggregate count.

### 2. Normalize without overwriting

Create derived fields for trimmed names, Unicode normalization, case-folded
comparison, standardized region labels, sector/type values, and status
values. Preserve every raw source value beside its derived value. Record the
normalization rules and software/version used.

No missing identifier, region, type, campus relationship, or status may be
filled with an inferred value without a documented decision and evidence.

### 3. Reconcile identity and hierarchy

Use official identifiers first. Where identifiers are absent or conflict:

- compare name, location, sector/type, source status, and campus information;
- classify exact matches, probable matches, conflicts, and unresolved pairs;
- require manual review for probable merges;
- retain all source memberships and competing values;
- create an internal stable ID only for a documented reconciled entity;
- link campuses and branches only when the relationship is supported.

Similar names are not sufficient evidence of institutional identity. Absence
from one source is not evidence of ineligibility or closure.

### 4. Classify lifecycle and coverage

Record inactive, closed, merged, renamed, duplicate, or ambiguous status only
when supported by source evidence. Distinguish source absence, missing data,
and confirmed non-membership. Flag geographic gaps, including any BARMM
coverage limitation, rather than silently excluding affected records.

### 5. Record decisions and produce a candidate frame

Every inclusion, exclusion, merge, split, status classification, unresolved
match, and manual override must have a change-log entry containing the
affected source records, decision, rationale, evidence reference, reviewer,
and timestamp.

The candidate frame must be generated from a named set of source snapshot
IDs and a versioned reconciliation procedure. It must report counts by
reconciliation status, source, region, sector/type, campus relationship,
and unresolved issue state. Counts are reportable only when they can be
reproduced from retained snapshots.

### 6. Freeze only after review

A frame version may be marked `frozen` only after:

- all source snapshots and hashes are retained;
- identity and campus rules are approved;
- unresolved records have a documented disposition or explicit exclusion
  from the frozen frame;
- coverage limitations and source scope are reported;
- researcher/adviser approval is recorded with the frame version;
- the sampling unit, eligibility rules, strata, and generalization boundary
  are approved.

Until then, the frame status must remain `candidate` or `under_review`.

## Separating population and study states

The frame schema must not collapse these questions:

| Question | Required state |
|---|---|
| Is the entity in the broad candidate Philippine HEI frame? | Frame membership and reconciliation status |
| Can it be recruited under the approved study? | Study eligibility and recruitment status |
| Is it eligible for WURI 2026, THE 2026, QS 2026, or UI GreenMetric 2025? | Separate framework-edition eligibility records |
| Is evidence authorized and usable? | Authorization, research-use permission, provenance, review, and extraction states |
| Did it participate and complete an assessment? | Recruitment, participation, withdrawal, and completion states |

No candidate frame record implies consent, evidence authorization, framework
eligibility, participation, or a readiness score.

## Framework-specific follow-up

The four framework editions must be evaluated independently. The frame
reconciliation may provide institution identity and classifications, but it
does not establish:

- WURI program/case eligibility or complete WURI scoring requirements;
- THE 2026 provider eligibility or data-submission conditions;
- QS 2026 provider eligibility or data-submission conditions;
- UI GreenMetric 2025 institution/campus submission requirements.

These criteria require authoritative edition-specific sources and researcher
approval before data collection or scoring.

## Current findings and limitations

- No institution-level source snapshot was obtained from CHED Statistics,
  HEIDA, or the legacy list during this phase.
- No institution-level or campus-level records were reconciled.
- No national institution count is established.
- The 2,334 figure is a verified historical aggregate as of June 26, 2025,
  with explicit BARMM exclusions; it is not a frozen population size.
- CHED Statistics was not readable through the current fetch because of HTTP
  403.
- HEIDA was reachable, but no dated directory export was retained.
- The legacy page was reachable, but the retrieved content did not expose a
  usable list snapshot.
- Identifier semantics, campus hierarchy, lifecycle status, duplicate
  resolution, BARMM coverage, and geographic completeness remain unresolved.
- No institution was enrolled, contacted, or assigned an evidence status.

## Frame-freezing checklist

- [ ] Obtain permitted snapshots or exports for each source used.
- [ ] Record source URLs, publication/reporting periods, retrieval timestamps,
      hashes, access method, and scope.
- [ ] Confirm whether each record is an institution, campus, branch, or other
      unit.
- [ ] Preserve raw fields and document normalization rules.
- [ ] Reconcile identifiers and probable duplicates with manual review.
- [ ] Establish supported institution-campus relationships.
- [ ] Record lifecycle, coverage gaps, BARMM limitations, and unresolved
      records.
- [ ] Generate reproducible counts and a versioned candidate frame.
- [ ] Approve the primary sampling unit, strata, framework eligibility, and
      generalization boundary.
- [ ] Record researcher/adviser approval before marking the frame frozen.

Until this checklist is satisfied, the population frame remains a candidate
frame and the research protocol remains pending.

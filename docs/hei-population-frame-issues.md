# HEI population-frame issue register

## Status

This register records blockers and review questions discovered while
reconciling candidate Philippine HEI population sources. It is not a list of
institutions and does not approve a frame, sampling method, sample size, or
recruitment.

Statuses:

- **open:** requires source acquisition, analysis, or researcher decision.
- **blocked:** work cannot proceed with the available source access.
- **deferred:** depends on an approved frame or protocol decision.
- **resolved:** supported by retained evidence and a documented decision.

## Issues

| ID | Status | Area | Finding | Required resolution |
|---|---|---|---|---|
| HEI-FR-001 | open | CHED institution-level artifact | The official statistics page and its historical aggregate are now documented, but no raw institution-level CSV/XLSX/JSON/list artifact, source hash, or row-level identifiers was retained. | Obtain a permitted dated institution-level listing/export and record publication/reporting period, unit, exclusions, and hash. |
| HEI-FR-002 | open | HEIDA snapshot | The HEIDA landing page was reachable and identifies a public HEI directory, but no dated directory export or API response was obtained. | Determine permitted export/API access, retain an immutable snapshot, and document update date and identifier semantics. |
| HEI-FR-003 | open | Legacy list snapshot | The legacy CHED page was reachable, but the fetched content exposed an accessibility shell rather than a usable institution list. | Locate and retain the actual list/file and its publication date; identify whether rows are institutions, campuses, or branches. |
| HEI-FR-004 | open | Source scope | CHED Statistics, HEIDA, and the legacy list may enumerate different units and reference periods. They must not be treated as interchangeable. | Compare retained snapshots field-by-field and document each source's scope and unit. |
| HEI-FR-005 | resolved | Historical aggregate interpretation | CHED's published statistics report 2,334 HEIs as of June 26, 2025, including BARMM SUC main and satellite campuses and excluding 85 BARMM private HEIs and 7 other government HEIs. This resolves the prior description error, but does not create an institution-level frame. | Preserve the exact date and exclusions whenever the statistic is cited; use HEI-FR-001 for the remaining artifact requirement. |
| HEI-FR-006 | open | Identifiers | No source snapshot with CHED identifiers is currently available for reconciliation. | Determine identifier fields, persistence across updates, and conflict-resolution rules. |
| HEI-FR-007 | open | Institution/campus hierarchy | The repository has no reconciled records establishing main-campus, satellite-campus, branch, or institution relationships. | Preserve raw unit labels and manually review relationships before creating stable internal IDs. |
| HEI-FR-008 | open | Duplicate and merge handling | Duplicate names, renamed entities, and probable matches cannot be evaluated without source records and locations/status fields. | Use identifier-first matching, retain duplicate groups, and log every merge/split decision. |
| HEI-FR-009 | open | Lifecycle status | Active, inactive, closed, merged, and renamed classifications are not supported by retained source evidence. | Define authoritative lifecycle evidence and record source date and decision provenance. |
| HEI-FR-010 | open | Geographic coverage | Coverage limitations, including the previously noted BARMM-related concern, have not been tested against a retained source snapshot. | Compare geographic coverage and explicitly report missing or uncertain areas; do not infer exclusion from absence. |
| HEI-FR-011 | deferred | Classification | Public/private sector, institution type, region, and location fields have not been reconciled across sources. | Approve normalization mappings after source acquisition and preserve raw values. |
| HEI-FR-012 | deferred | Framework eligibility | A candidate HEI frame cannot establish eligibility for WURI 2026, THE 2026, QS 2026, or UI GreenMetric 2025. | Verify edition-specific criteria and maintain separate framework eligibility records. |
| HEI-FR-013 | deferred | Study eligibility | Population membership is not the same as recruitment eligibility or evidence availability. | Approve inclusion/exclusion, authorization, evidence, privacy, ethics, and retention rules. |
| HEI-FR-014 | deferred | Sampling unit | Institution as primary unit and campus/framework/WURI nesting remain proposals. | Obtain adviser/researcher approval and define the analysis unit for each outcome. |
| HEI-FR-015 | deferred | Strata | Regional, sector, institution-type, and framework strata cannot be finalized before frame reconciliation. | Derive candidate strata from retained frame fields and approve final strata/allocation. |
| HEI-FR-016 | deferred | Sample size | No institution sample size or precision/power rationale is established. | Specify estimand, analysis, accessible eligible population, expected participation, and feasibility/precision rationale. |
| HEI-FR-017 | deferred | Frame approval | No source snapshots, reconciled counts, issue dispositions, or approval record exists for a frozen frame. | Complete the frame-freezing checklist and record approval against a versioned frame. |
| HEI-FR-018 | blocked | JSON Schema validation | The available AJV 6.15.0 validator does not support the schema's declared Draft 2020-12 meta-schema; no compatible validator is installed. | Run a Draft-2020-12-compatible validator in an approved validation environment; do not equate JSON parsing with schema conformance. |
| HEI-FR-019 | resolved | Published CHED request procedure and contact route | The 2025 first-edition Citizen's Charter publishes the Request for CHED Statistical Data/Information procedure, and the official Contact Us page publishes `info@ched.gov.ph`, `(02) 8441-1260`, and `0999-4445-996`. | Researcher must confirm the current submission route and requirements before sending the prepared brief; no request has been sent. |

## Required decision-log fields

Each future issue disposition or reconciliation decision should include:

- issue or record IDs affected;
- source snapshot IDs and raw record keys;
- decision (`include`, `exclude`, `merge`, `split`, `retain_unresolved`, or
  another approved value);
- rationale and supporting evidence;
- reviewer identity and review timestamp;
- procedure version;
- researcher/adviser approval reference where required;
- resulting frame version.

Until the open and blocked source issues are addressed, the candidate frame
must remain unfrozen. No issue disposition authorizes institutional contact,
evidence collection, or A0–A4 execution.

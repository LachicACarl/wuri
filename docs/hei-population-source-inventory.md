# HEI population source inventory

## Status

This inventory records source acquisition status for Phases 17E–17F. A landing
page or URL is not treated as an acquired dataset. No source file listed
below has been used to create institution records or a population count.

Status values:

- `identified_not_acquired`: the source is known, but no usable artifact was
  retained.
- `acquired_not_inspected`: an original artifact was retained but its
  structure has not yet been inspected.
- `inspected_candidate`: an original artifact was retained and inspected as a
  possible source.
- `blocked`: permitted acquisition or validation could not proceed.
- `superseded`: an older artifact is retained for provenance but is not the
  current candidate.

## Inventory

| Source ID | Official source | Status | Artifact retained | Evidence and next action |
|---|---|---|---|---|
| `ched-statistics` | [CHED Statistics](https://ched.gov.ph/statistics/) | `inspected_candidate` | No raw machine-readable artifact | CHED's published table reports **2,334 HEIs as of June 26, 2025**, including BARMM SUC main and satellite campuses, while excluding **85 BARMM private HEIs and 7 other government HEIs**. This verifies the historical aggregate and its exclusions, but not an institution-level frame. Obtain a permitted dated listing/export for reconciliation. |
| `ched-heida` | [CHED HEIDA](https://heida.ched.gov.ph/) and its linked public directory | `identified_not_acquired` | None | The landing page was reachable and described a public HEI directory, but no dated export, API response, or machine-readable directory snapshot was obtained. Confirm permitted export/API access and retain the original response or file. |
| `ched-legacy-hei-list` | [Legacy CHED list of HEIs](https://legacy.ched.gov.ph/list-of-higher-education-institutions-2/) | `blocked` | None | The fetched page exposed an accessibility shell rather than a usable list snapshot. No underlying file, publication date, or hash was obtained. Locate an official downloadable list or request an authorized copy. |
| `ched-statistical-data-request-procedure` | [CHED Citizen's Charter 2025, 1st edition (PDF)](https://ched.gov.ph/wp-content/uploads/CHED-Updated-CC-2025-1st-edition-033125.pdf) | `inspected_candidate` | Published procedure; no requested HEI data artifact | The published 2025 procedure identifies the responsible CHED unit, individual/client request eligibility, formal letter purpose/usage/contact requirements, online request and email/fax release, and no fee. Confirm the current route before sending; this is procedure evidence, not population data. |

## Source-artifact recording requirements

When an artifact is acquired, add a row or linked artifact record containing:

- source URL or approved local path;
- issuing organization;
- publication/update date and reference period;
- retrieval timestamp and permitted access method;
- original filename and file type;
- byte size and SHA-256 hash;
- documented unit and scope;
- access restrictions or terms;
- preservation location outside the committed source-code tree when the
  source is private or sensitive.

The original artifact must remain unchanged. Derived inspection outputs must
identify the source-artifact hash and must not replace the source.

## Acquisition-plan reference

The editable, unsent request preparation is recorded in
[`ched-hei-data-request-brief.md`](./ched-hei-data-request-brief.md). It
records the published 2025 request procedure and published contact details,
while requiring the researcher to confirm the current submission instructions
before sending anything.

## Inspection command

No institution-level source artifact was acquired in Phases 17E–17F, so no
source-specific row or column count or institution count is reported. The
published 2,334 figure is an aggregate table value, not a raw file count.
Once a permitted CSV/XLSX/XLS/JSON artifact is
retained, inspection should be performed with a read-only script that:

1. reports file type, size, hash, and source metadata;
2. reports worksheet names or delimited-file columns;
3. reports raw row and column counts;
4. identifies candidate identifier, name, type, region, location, status, and
   unit fields without renaming or changing values;
5. reports missing values and duplicate identifiers;
6. preserves the original file and writes only a separate inspection report.

The inspection must not merge, exclude, normalize in place, or infer
institution/campus relationships.

## Validation tooling

The repository has AJV 6.15.0 available under the frontend dependency tree.
It does not support the schema's declared JSON Schema Draft 2020-12
meta-schema, so compilation fails before validation. Python `jsonschema`,
`fastjsonschema`, and `referencing` are not installed, and no standalone
`check-jsonschema` or compatible `ajv` command is available.

Consequently, Phase 17E validation establishes:

- the schema is syntactically valid JSON;
- the available AJV version was checked and found incompatible with Draft
  2020-12;
- full JSON Schema conformance has not been established.

No dependency was installed solely to perform this validation. Use a
Draft-2020-12-compatible validator in a later validation environment.

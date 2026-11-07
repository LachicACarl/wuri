# Philippine higher-education population and sampling frame

## Intended population

The platform is intended to support Philippine higher education institutions
(HEIs), not elementary or secondary schools. An HEI record must be separated
from its main campus, satellite campus, and individual program where the
source provides those distinctions.

This is a population definition for platform and research planning. It is not
an assertion that every Philippine HEI has enrolled, supplied evidence, or is
eligible for every ranking framework.

## Candidate official sources and current access findings

| Source | Retrieval/reporting information | Use | Limitation |
|---|---|---|---|
| [CHED Statistics](https://ched.gov.ph/statistics/) | CHED publishes a 2025 HEI distribution table with a grand total of **2,334 HEIs as of June 26, 2025** | Historical aggregate and regional/type coverage reference | The table includes BARMM SUC main and satellite campuses but excludes **85 BARMM private HEIs and 7 other government HEIs**. It is not an institution-level sampling frame. |
| [CHED HEIDA](https://heida.ched.gov.ph/) | Landing page checked 2026-10-16; public directory service | Candidate institution names, region, type, and campus identifiers where exposed | The landing page was reachable, but no dated export/API response or completeness evidence was obtained. |
| [CHED list of HEIs](https://legacy.ched.gov.ph/list-of-higher-education-institutions-2/) | Page checked 2026-10-16; publication date and list file were not established | Cross-check of institution listings | The fetched page was an accessibility shell, not a usable list snapshot; legacy naming/campus coverage requires reconciliation with HEIDA. |

CHED's published statistics report **2,334 HEIs as of June 26, 2025**. The
table includes BARMM SUC main and satellite campuses and explicitly excludes
**85 BARMM private HEIs and 7 other government HEIs**. This is a verified
historical aggregate with documented exclusions, not a complete
institution-level sampling frame or current national population count.

## Required frozen population manifest

Before sampling, the researcher must retain a dated, immutable manifest with:

- source URL and retrieval timestamp;
- reporting period/publication date;
- CHED institution identifier, if available;
- official institution name and normalized display name;
- institution type/sector and region;
- main/satellite campus designation and campus identifier;
- duplicate and merge decisions with provenance;
- missing-field and coverage flags.

No such frozen manifest is currently present in the repository. No permitted
institution-level source snapshot was obtained during the population-frame
reconciliation or CHED data-request planning phases.
Nationwide scraping, automatic enrollment, and bulk evidence collection are
out of scope for this phase.

## Known data-quality checks

The manifest review must identify duplicate names, campus-versus-institution
records, inconsistent spelling, renamed institutions, missing identifiers,
and institutions appearing in one CHED source but not another. Programs and
WURI cases must not be counted as HEI records.

## Current conclusion

The Philippine HEI population is a candidate population only. The source
access findings, reconciliation procedure, proposed record schema, and issue
register are documented in
[`hei-population-frame-reconciliation.md`](./hei-population-frame-reconciliation.md),
[`hei-population-frame-schema.json`](./hei-population-frame-schema.json), and
[`hei-population-frame-issues.md`](./hei-population-frame-issues.md).
Phase 17E source-acquisition status is recorded in
[`hei-population-source-inventory.md`](./hei-population-source-inventory.md).
The unsent acquisition request preparation is recorded in
[`ched-hei-data-request-brief.md`](./ched-hei-data-request-brief.md).
Completeness, deduplication, BARMM coverage, campus hierarchy, and the dated
source freeze remain unresolved researcher/data-management tasks.

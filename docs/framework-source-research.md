# Framework source research and verification register

This register records the framework-source review for Phase 16B. It separates
official ranking methodology from this study's operational readiness mappings.
The supplied framework research report was not present in the repository, so
the claims in that report were treated as leads and checked against provider
sources where possible.

## Verification rules

- A framework is not marked fully verified unless the edition-specific
  criteria, scoring rules, weights, and source provenance are available.
- A published weight is not sufficient to reproduce a provider's ranking when
  proprietary normalization, surveys, bibliometrics, or provider-submitted
  data are also required.
- The catalog does not authorize use of institutional evidence and does not
  approve the pending research protocol.

## Source findings

| Framework | Edition | Provider source | Result | Remaining gap |
|---|---|---|---|---|
| WURI | 2026 | https://www.wuri.world/ and the private `S3034_WURI2026_Evaluation (1).xlsx` workbook | The workbook inventories 24 categories. The supplied research claim that cases are evaluated on innovativeness, implementability, and impact is retained as a provisional dimension description. | No official numerical dimension weights or complete scoring/normalization rules were verified. The private workbook is a candidate-source inventory, not an institutional evidence corpus. |
| THE World University Rankings | 2026 | https://www.timeshighereducation.com/world-university-rankings/methodology-world-university-rankings-2026 | The five published pillar weights and the 18-metric structure are recorded in the machine-readable catalog. | Exact provider normalization and all data-access conditions are not reproduced by this repository. Source document hash was not captured. |
| QS World University Rankings | 2026 | https://www.topuniversities.com/world-university-rankings/methodology | The published category and indicator weights are recorded, including International Student Diversity at 0%. | Provider normalization, survey construction, and complete source-document hash were not captured. |
| UI GreenMetric | 2025 | https://uigreenmetric.com/resources/university/guidelines | The six published category weights are recorded as unverified reference values only. | The complete 2025 guideline, every indicator, point allocation, threshold, and scoring rule were not available for source verification. No catalog is marked verified. |

## WURI 2026 categories

The category names below are preserved from the private workbook audit. They
are not a claim that the workbook itself is the authoritative WURI
methodology document.

`A1` Student Support and Engagement; `A2` Student Mobility and Openness;
`A3` Industrial Application; `A4` Entrepreneurial Culture & Eco System;
`A5` Crisis Management; `A6` Ethics and Integrity; `A7` Future-Oriented
Responses to Global Uncertainty and Geopolitical Risk; `A8` SDG- and
ESG-Based Responses to Past and Present Global Challenges; `B1` Visionary
Leadership; `B2` Empowerment-Based Management; `B3` Digital and AI
Transformation in Strategy and Management; `B4` Culture/Value; `B5` Funding
for Sustainability; `B6` Infrastructure/Technologies; `B7` Cost-Benefit
Management; `B8` University Brand and Reputation; `C1` Representative Research
Project; `C2` Interdisciplinary, Convergent, and Integrated Research; `C3`
Curricular Innovation for Future-Readiness; `C4` AI-based Teaching and
Learning Transformation; `C5` Social Impact through Knowledge Transfer; `C6`
Inclusive Social Innovation for the Underserved; `C7` University-Based
Entrepreneurial Projects; `C8` Financial Impact-Driven Tech Transfer.

## Interpretation boundary

THE and QS entries in the catalog are official published methodology inputs,
not a reproduction of the providers' final ranking algorithms. WURI entries
describe case-level program categories, not institution-level scores. UI
GreenMetric remains incomplete until the 2025 guideline is obtained and
checked indicator by indicator. Operational mappings from passages to
criterion values require a separate approved research decision.

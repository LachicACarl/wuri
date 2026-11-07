# Framework criteria provenance register

The current indicator descriptions are a retrieval catalog inherited from the prototype. They are not asserted to be official ranking criteria or official weights.

| Framework | Criteria status | Weight status | Methodology version | Source | Checked |
|---|---|---|---|---|---|
| WURI | 2026 category inventory; dimensions unverified | Unverified | 2026 | [WURI source register](./framework-source-research.md) | Partial |
| THE | 2026 metric catalog proposed | Published weights recorded; provider normalization unavailable | 2026 | [THE methodology](https://www.timeshighereducation.com/world-university-rankings/methodology-world-university-rankings-2026) | Weights checked |
| QS | 2026 indicator catalog proposed | Published weights recorded; provider normalization unavailable | 2026 | [QS methodology](https://www.topuniversities.com/world-university-rankings/methodology) | Weights checked |
| UI GreenMetric | Category reference only | Unverified | 2025 | [UI GreenMetric guidelines](https://uigreenmetric.com/resources/university/guidelines) | Incomplete |

Final scoring is blocked until each framework has an applicable methodology version, authoritative source reference, verified criteria mapping, and provenance for every weight. Missing weights are not treated as zero and are not replaced automatically with equal weights. The detailed proposed catalog is [`framework-criteria-catalog.json`](./framework-criteria-catalog.json); it is not approved for scoring.

The machine-readable representation is in [`backend/app/frameworks.py`](../backend/app/frameworks.py). Updating a framework requires updating both the provenance fields and the associated tests before it can be marked verified.

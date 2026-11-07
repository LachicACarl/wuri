# Methodology decisions and scoring gates

## Criterion-level aggregation is unresolved

**Relevant source:** The locally available `UniversityRanking_V3.1.docx`, Chapter 3, Sections 3.5.8–3.5.9 and 3.7.6. The source defines normalized criterion value `x_fj` and its use in readiness scoring, but does not provide a rule for reducing multiple evidence passages to that value.

### Explicitly stated

- Readiness uses a normalized criterion value `x_fj`.
- Fixed-reference TOPSIS uses a full-readiness ideal and a zero-readiness anti-ideal.
- Evidence quality uses five equally weighted dimensions for the primary experiment.
- Evidence acceptance requires validation-set threshold calibration.
- ARRS uses equal framework weights.
- Best-Fit uses the highest RRS, with a close alternative when the margin is less than five percentage points.

### Unspecified in Chapter 3

- How multiple accepted passages supporting one indicator are combined.
- How independent documents are combined.
- How contradictory evidence is resolved.
- Whether duplicate passages are deduplicated before aggregation.
- How freshness/reporting periods affect a criterion.
- Whether required evidence elements map one-to-one to criteria.
- How missing evidence is represented in `x_fj`.

### Plausible alternatives and implications

| Alternative | Implication |
|---|---|
| Maximum accepted AES | Rewards the strongest passage but can ignore coverage and conflicting evidence. |
| Mean accepted AES | Reflects average evidence quality but can dilute a strong, specific document with weak passages. |
| Weighted aggregation by required evidence elements | Represents completeness directly but requires approved checklists and duplicate/conflict rules. |
| Recency- or source-weighted aggregation | May reflect current institutional readiness but requires a documented time and reliability policy. |

No alternative is selected in production. Choosing one without approval would change the research method.

## Protocol-level statistical and evaluation decisions remain unresolved

**Relevant source:** Chapter 3 Sections 3.7.4–3.7.11 and 3.10.

The dissertation states a 0.05 criterion for the comparative hypothesis test,
requires model/retrieval and readiness comparisons, and describes ICC,
Spearman agreement, score error, Best-Fit agreement, sensitivity/robustness,
XAI, and ISO/IEC 25010 evaluation. It does not provide a complete
machine-readable analysis plan for:

- the exact paired statistical tests and estimands;
- effect sizes and confidence intervals;
- multiplicity control;
- missing and incomplete cases;
- minimum sample sizes or power justification;
- the operational XAI instrument and evaluator scoring;
- the ISO/IEC 25010 questionnaire, recruitment, consent, and response analysis.

These choices require researcher/adviser approval. No p-value, confidence
interval, effect, software-quality result, or explanation-quality result may
be reported from the current repository.

## Institution coverage decision

The working research design is mixed: the platform may support a broad
Philippine HEI population, while the empirical A0–A4 study will use a
selected sample of eligible institutions that provide authorized, usable
evidence. This separates product/platform coverage from the dissertation's
empirical sample.

The decision does not select a sampling frame, unit, method, sample size,
eligibility rule, non-response policy, replacement rule, or power/precision
rationale. Those items remain subject to researcher/adviser approval and are
recorded in [`institution-sampling-plan.md`](./institution-sampling-plan.md).

## A0–A4 implementation boundary

The dissertation's Table 3.9 definitions are recorded in
[`experiment-matrix.md`](./experiment-matrix.md). The current local A0
executor is retrieval-only and is not the complete pretrained
Sentence-BERT + conventional AHP-TOPSIS baseline described in Table 3.9.
A1–A4 have no approved, reproducible research artifacts or completed
evaluation. Existing AHP, TOPSIS, EQAM, and explanation utilities are
components, not evidence that an ablation was executed.

## Framework-to-evidence mappings remain unresolved

The proposed versioned catalog in
[`framework-criteria-catalog.json`](./framework-criteria-catalog.json) records
published THE 2026 and QS 2026 weights, preserves their zero-weight
indicators, and keeps WURI 2026 and UI GreenMetric 2025 separate. It does not
define an operational mapping from retrieved passages to provider metrics.
THE and QS require provider-specific normalization and data sources that are
not reproduced by this application. WURI is case-level and UI GreenMetric
requires the complete 2025 guideline.

The researcher/adviser must approve, for each framework, which authorized
institutional evidence can support each criterion, how unavailable survey,
bibliometric, campus-measurement, or submitted-provider data are represented,
and whether a readiness proxy is permitted. No official ranking score may be
claimed from the proposed catalog alone.

### Required approval

An adviser-approved aggregation policy must define the input evidence set, duplicate handling, contradictory evidence handling, missing evidence behavior, freshness rules, and the exact transformation to `x_fj`. The assessment state remains blocked until a versioned policy identifier is supplied.

### Required tests after approval

- Multiple passages for one criterion.
- Multiple documents for one criterion.
- Duplicate and near-duplicate passages.
- Conflicting evidence.
- Missing required evidence.
- Fresh and stale reporting periods.
- Reproducibility under identical inputs and policy versions.

## Equation confirmation

The DOCX contains native Word math objects. Sections 3.5.8–3.5.11 include equations for weighted criterion values, fixed ideal/anti-ideal distances, closeness coefficient, 0–100 RRS, equal-weight ARRS, and Best-Fit selection. Their mathematical direction is reflected by the fixed-reference TOPSIS and framework-aggregation helpers. This confirms that the equations are present in the source; it does not resolve the missing evidence-to-`x_fj` aggregation rule or establish full workflow compliance. No claim is made that the current implementation has reproduced every equation or the dissertation's full A0 pipeline.

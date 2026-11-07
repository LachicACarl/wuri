# Phase 17A — Research protocol readiness

## Decision

The research protocol is **not ready for approval or experimentation**. The
repository contains substantial software infrastructure and synthetic
validation, but it does not contain the approved data, locked framework
catalogs, model artifacts, expert judgments, or operational decisions needed
to claim an A0–A4 evaluation.

The primary methodological source is the local
`backend/private/research-input/UniversityRanking_V3.1.docx`. Chapter 3 was
read directly. The reviewed copy has no embedded comments or tracked changes;
separate adviser comments were not supplied.

## Dissertation-supported requirements

Chapter 3 establishes the following:

- The study scope uses WURI 2026, THE World University Rankings 2026, QS World
  University Rankings 2026, and UI GreenMetric 2025 (Section 3.2.3 and
  Table 3.1).
- Evidence is to come from official institutional documents, with
  authorization/data-use controls and source traceability (Sections 3.2.1,
  3.2.2, and 3.9).
- Five domain experts independently label/rate cases before consensus;
  categorical agreement uses Fleiss' kappa and continuous or quasi-continuous
  agreement uses ICC (Sections 3.3.1 and 3.3.4; Tables 3.2–3.3).
- The corpus uses common preprocessing and fixed 70:15:15
  train/validation/test partitions, stratified by framework and major
  indicator group where sample size permits (Sections 3.5.4 and 3.7.4).
- Retrieval reports Precision@K and Recall@K at K=1, 3, and 5 (Sections 3.5.4
  and 3.7.3).
- EQAM has five normalized dimensions: semantic relevance, model confidence,
  evidence completeness, source reliability, and evidence strength (Sections
  3.5.5–3.5.6 and Table 3.4).
- Validation data select evidence-acceptance thresholds before test evaluation
  (Sections 3.5.6 and 3.7.7).
- Fixed-reference TOPSIS, RRS, ARRS, Best-Fit, close-margin review, ablation,
  sensitivity/robustness, XAI, and software-quality evaluation are described
  in Sections 3.5.7–3.5.11 and 3.7.4–3.7.11.
- The dissertation states a 0.05 significance criterion for the comparative
  hypothesis test (Section 3.7.4), but does not by itself resolve every
  statistical test, multiplicity policy, effect-size convention, or missing
  data rule.

These statements do not establish that the repository has completed the
corresponding research work.

## Current implementation versus research evidence

| Area | Implemented software | Research evidence available | Status |
|---|---|---|---|
| Institution/document security | Institution-scoped storage, permissions, audit events, quarantine boundary, and synthetic isolation tests | No participating HEI corpus or external authorization | Software validated; research input missing |
| Framework registry | Fixed edition names and provisional catalog | Complete authoritative criteria, eligibility rules, weights, and locked source digests | Blocked |
| Evidence provenance | Source document/passage IDs, metadata, permission states, review states, scan states | Human-confirmed source rights, DUA, ethics/privacy decisions, and approved institutional evidence | Blocked |
| Expert validation | Five-reviewer persistence, blinded queues, Fleiss' kappa integration, consensus records | Five qualified experts, approved rubric, real independent judgments and approved adjudication | Blocked |
| Data splitting | Versioned grouped stratified splitter | Approved dataset and frozen manifest | Blocked |
| Retrieval | Local-only A0 retrieval evaluator and metric utilities | Approved model artifact, labels, partitions, and protocol | Blocked |
| Full readiness scoring | AHP/TOPSIS utilities exist | Approved criterion aggregation, framework weights, mappings, and end-to-end A0 | Not established |
| A1–A4 | Component utilities and readiness descriptors only | Domain-adapted model, EQAM calibration, XAI evaluation, and results | Not implemented/evaluated |
| Validation results | 85 software tests and synthetic acceptance results | No model accuracy, ranking quality, agreement, or hypothesis result | No empirical result |

The 120-record WURI abstract pilot remains candidate program data. It is not
authorized institutional evidence, not a Philippine HEI sample, and not an
approved evaluation dataset.

## Blocking prerequisites

1. Researcher approval of the decisions in
   [researcher-approval-checklist.md](./researcher-approval-checklist.md).
2. A dated, deduplicated Philippine HEI sampling frame and approved sampling
   unit, eligibility, selected-sample size, recruitment, non-response, and
   replacement rules for the chosen mixed design. The leading stratified
   purposive method and current nested-unit structure are proposals only.
3. Verified edition-specific framework criteria, eligibility requirements,
   weights, provider data requirements, and source/catalog digests.
4. Human-authorized institutional evidence with provenance, retention,
   privacy, ethics, and data-use determinations.
5. Approved expert eligibility, rubric, independent-review, consensus, and
   missing-rating procedures, followed by real five-expert judgments.
6. An approved criterion aggregation policy that maps accepted evidence to
   `x_fj`.
7. A selected and approved baseline Sentence-BERT identity/revision, local
   artifact, checksum, license/provenance, and model configuration.
8. A versioned enhanced-model training/calibration plan and artifact for A1.
9. Locked leakage-controlled partitions and validation-only threshold
   selection.
10. Approved AHP/TOPSIS configuration, weight provenance, score interpretation,
    A4 explanation instrument, and statistical analysis plan.

Until these are satisfied, the A0 protocol must remain
`pending_researcher_approval`, deployment intake must remain blocked, and no
A0–A4, RRS, ARRS, Best-Fit, ranking prediction, or empirical claim may be
generated.

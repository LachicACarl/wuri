# Researcher approval checklist

This checklist is intentionally unanswered. A checked software test is not
researcher approval. Each decision needs a dated decision record, responsible
approver, version identifier, and supporting source or rationale.

## Population and participating institutions

- [x] Working coverage design selected: broad platform population plus a
      selected empirical sample of eligible institutions with authorized data.
- [ ] Review leading proposal: stratified purposive sampling of Philippine
      HEIs, with public/private and possible regional representation, subject
      to the reconciled frame and separate framework eligibility.
- [ ] Approve the proposed nested structure: institution primary unit, campus
      nested where applicable, institution-framework assessment, and WURI
      program/case nested within an institution.
- [ ] What dated CHED/HEI sampling frame is authoritative?
- [ ] Is the unit an institution, campus, parent institution, or another unit?
- [ ] What inclusion/exclusion and framework-eligibility rules apply?
- [ ] What sampling method, sample size, power/precision rationale, regional
      strata, non-response rule, and replacement rule will be used?
- [ ] What institutional participation, authorization, DUA, privacy, ethics,
      retention, and withdrawal procedures apply?

Chapter 3 requires a defined population, respondents, and sampling procedure
(Sections 3.2.1 and 3.3.1–3.3.3), but the available source does not freeze a
CHED manifest or answer these operational choices.

## Frameworks and evidence

- [ ] Approve the locked source and digest for each of WURI 2026, THE 2026,
      QS 2026, and UI GreenMetric 2025.
- [ ] Verify official criteria, provider eligibility, required data,
      normalization, and weights for each edition.
- [ ] Decide whether the study assesses operational readiness proxies or can
      reproduce provider metrics; do not call a proxy an official ranking.
- [ ] Approve which document types and evidence elements map to each
      criterion.
- [ ] Decide how multiple passages/documents, duplicates, contradictions,
      stale evidence, missing evidence, and unavailable provider indicators
      become one normalized `x_fj`.

Chapter 3 specifies the editions and fixed-reference scoring concepts
(Sections 3.2.3 and 3.5.7–3.5.11), but it does not specify the complete
evidence-to-criterion aggregation rule.

## Expert validation

- [ ] Approve domain-expert eligibility and credential verification.
- [ ] Approve the relevance, indicator-mapping, and EQAM rubric anchors and
      rater instructions.
- [ ] Confirm five independent judgments occur before consensus.
- [ ] Select the ICC model, missing-rating policy, minimum complete cases,
      and agreement interpretation.
- [ ] Approve the disagreement and consensus/adjudication procedure.
- [ ] Confirm that consensus labels do not replace independent ratings in
      agreement calculations.

The independent-before-consensus requirement and Fleiss' kappa/ICC choices
are dissertation-supported (Section 3.3.4); the operational details above
remain unresolved.

## Model, retrieval, and splits

- [ ] Select the exact pretrained Sentence-BERT model, revision, license,
      local artifact, checksum, maximum sequence length, and embedding settings.
- [ ] Approve the domain-adaptation objective, training data, negative/hard
      negative construction, and A1 artifact provenance.
- [ ] Approve query unit, candidate pool, eligible-query rule, metric
      aggregation, undefined-metric policy, and deterministic tie-breaking.
- [ ] Approve the additional document/text leakage grouping and similarity
      rules beyond dissertation stratification.
- [ ] Freeze the 70:15:15 manifest before test evaluation.
- [ ] Confirm that no test labels or test-derived thresholds enter training or
      validation decisions.

Chapter 3 specifies the 70:15:15 common partitions and P@K/R@K at K=1,3,5
(Sections 3.5.4 and 3.7.3–3.7.4), but not the remaining implementation
choices.

## Scoring and explainability

- [ ] Approve EQAM calibration data, dimension rubrics, combination rule, and
      acceptance threshold/tie-break.
- [ ] Approve AHP criteria weights, consistency-ratio policy, and provenance.
- [ ] Approve fixed ideal/anti-ideal references and score interpretation bands.
- [ ] Confirm equal framework weights for ARRS and the Best-Fit rule.
- [ ] Review or adjust the proposed five-point close-margin rule through the
      expert panel before final evaluation.
- [ ] Define the A4 explanation evaluation instrument, fidelity/completeness
      criteria, and independent evaluators.

Chapter 3 supplies the conceptual components and the five-point close-margin
review (Sections 3.5.5–3.5.11 and 3.7.6–3.7.10), but does not fully specify
all operational thresholds or instruments.

## Statistics, ethics, and release

- [ ] Approve the comparison estimands, paired analysis, significance
      criterion, effect-size reporting, confidence intervals, multiplicity
      handling, and missing-data policy.
- [ ] Approve ISO/IEC 25010 evaluator recruitment and questionnaire procedure;
      Chapter 3 Section 3.7.11 describes at least 30 purposive evaluators.
- [ ] Confirm ethics review or formal determination, privacy review, DUA,
      source-rights, retention, deletion, and incident procedures.
- [ ] Confirm the deployment readiness preflight is successful with a real
      verified scanner and operational controls.
- [ ] Approve the protocol version and record approver, date, and reference.

No checklist item is currently approved by this repository.

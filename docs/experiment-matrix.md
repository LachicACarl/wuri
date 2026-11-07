# A0–A4 experiment matrix

The matrix separates the dissertation design from the current software state.
An implementation component is not evidence that the corresponding
experiment has been executed.

| Variant | Dissertation definition | Required inputs/artifacts | Evaluation | Current status | Evidence required to claim evaluation |
|---|---|---|---|---|---|
| A0 | Pretrained Sentence-BERT with conventional AHP-TOPSIS (Table 3.9; Sections 3.5.1 and 3.7.4) | Authorized institutional corpus; five-expert labels; locked 70:15:15 partitions; approved framework catalog/weights; criterion aggregation to `x_fj`; approved pretrained model artifact and checksum; conventional AHP/TOPSIS config | Classification/retrieval metrics, P@K/R@K at K=1,3,5; score error/agreement and Best-Fit measures where applicable | Retrieval-only local evaluator exists. Full readiness A0 is not implemented or executed. | Approved protocol, dataset manifest, model digest, frozen config, run provenance, predictions, metrics, and no test-label leakage |
| A1 | Domain-adapted Sentence-BERT with conventional AHP-TOPSIS (Table 3.9; Sections 3.5.3–3.5.4 and 3.7.5) | A0 inputs plus approved training pairs, adaptation code/config, training artifact/checksum, validation procedure | Compare adapted retrieval/classification against A0 using common partitions and metrics | Domain-adapted model/training artifact absent | Training manifest, artifact digest, independent test run, error analysis, and comparison record |
| A2 | Enhanced Sentence-BERT + EQAM + conventional AHP-TOPSIS (Table 3.9) | A1 artifacts plus five EQAM dimensions, expert rubric, calibration data, validation threshold and locked acceptance rule | Retrieval/classification plus EQAM dimension agreement/association, acceptance precision/recall/F1, score validation | EQAM utilities/descriptors exist; calibrated research inputs and end-to-end variant absent | Rubric approval, calibration trace, threshold lock before test, dimension ratings, predictions, and metrics |
| A3 | A2 plus framework-constrained AHP and fixed-reference TOPSIS (Table 3.9; Sections 3.5.7–3.5.9) | A2 inputs plus verified framework weights/mappings, AHP consistency policy, fixed ideal/anti-ideal, criterion aggregation and score interpretation | RRS error/agreement, ICC/Spearman where appropriate, Best-Fit exact/categorical agreement, sensitivity/robustness | AHP/TOPSIS utilities exist; approved catalogs, aggregation and complete A3 pipeline absent | Locked scoring config, criterion-level trace, RRS/ARRS/Best-Fit outputs, expert references, and reproducible run |
| A4 | A3 plus XAI; numerical improvement is evaluated at A3 and explanations separately (Table 3.9; Section 3.7.10) | A3 inputs plus explanation generator, explanation rubric/instrument, evaluator sample, fidelity/completeness criteria | Explanation effectiveness/fidelity and decision-support evaluation, separate from numerical score improvement | XAI utilities/checks exist, but explanation instrument, evaluators, and A4 run absent | Approved XAI protocol, evaluator records, explanation outputs, fidelity results, and separate A3 numerical results |

## Common controls

- Baseline and proposed variants must use the same approved corpus,
  preprocessing, labels, partitions, criteria, and computational environment
  (Sections 3.3.4, 3.5.1, and 3.7.4).
- Test labels must remain unavailable to training, threshold calibration, and
  model selection.
- The 70:15:15 split is dissertation-supported, but source-document grouping,
  near-duplicate rules, and seed require approval.
- P@K/R@K cutoffs K=1,3,5 are dissertation-supported; query and aggregation
  definitions remain unresolved.
- The current A0 retrieval executor is not the dissertation's complete
  Sentence-BERT + AHP-TOPSIS readiness baseline.
- No variant may run until the protocol JSON changes from
  `pending_researcher_approval` through an actual researcher approval process,
  and all dataset/model/framework gates pass.

## Variables and claims

The dissertation describes the baseline/proposed configuration differences and
outcomes, but does not provide a complete machine-readable causal variable
schema. The researcher must approve the independent-variable configuration,
dependent measures, statistical comparisons, effect-size reporting, and
missing-data policy before execution. Software test counts must not be used as
model-performance evidence.


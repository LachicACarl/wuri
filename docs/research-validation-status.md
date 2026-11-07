# Research validation status

## Audit scope and evidence

This status records a source-tree and local SQLite audit performed before adding research-validation infrastructure. It distinguishes application tests and controlled fixtures from empirical research.

| Prerequisite | Audit result | Consequence |
|---|---|---|
| Genuine expert-labeled institutional evidence | Not found. The local database had no assessments, documents, passages, or indicator matches. | No empirical evaluation can run. |
| Positive and negative evidence-indicator labels | Not found. | Classification and retrieval metrics have no research ground truth. |
| Five qualified expert judgments per case | None are present in the local research database. Phase 15 adds five-reviewer persistence/API infrastructure, but no actual reviewer qualifications or judgments have been entered. | Dataset approval and A0 remain blocked until expert eligibility, genuine judgments, and an approved consensus procedure exist. |
| Fixed train/validation/test partitions | Not found. | The new split utility must be run only after an approved dataset is imported. |
| Conventional pretrained Sentence-BERT baseline | A local-only held-out retrieval evaluator is implemented, but no approved model artifact/protocol or held-out empirical run is configured. | A0 retrieval is executable only after the explicit model/data/protocol gates pass; it is not yet an empirical result. |
| Enhanced/domain-adapted model or training pipeline | Not found. | A1-A4 remain blocked. |
| Expert readiness references or EQAM ratings | Not found. | Agreement, score error, acceptance thresholds, and EQAM validation remain blocked. |
| Verified ranking-framework criteria and weights | Not found. Existing framework entries are explicitly provisional/unverified. | Final RRS/ARRS/Best-Fit comparisons remain blocked. |
| Approved criterion aggregation rule | Not found; see [methodology-decisions.md](./methodology-decisions.md). | No RRS result may be derived from extracted passages. |
| Expert XAI evaluation instrument and ratings | Not found. | A4 explainability results remain blocked. |
| Empirical results | None found. Unit tests are software checks, not research experiments. | No gains, significance, or conclusions are reported. |
| Dissertation Chapter 3 source | `UniversityRanking_V3.1.docx` is now available in the ignored private research-input folder and was directly reviewed for Phase 14. It specifies the four framework editions, authorized institutional evidence, five domain experts, a stratified 70:15:15 split, P@K/R@K at K=1,3,5, EQAM, fixed-reference scoring, and A0-A4. No embedded comments/tracked changes were found; separate adviser comments were not supplied. | The A0 protocol draft remains pending. See [research-methodology-traceability.md](./research-methodology-traceability.md) for verified requirements, implementation gaps, and unresolved decisions. |

## Implemented infrastructure

The research-validation code provides:

- Immutable versioned evidence-label records and deterministic grouped 70:15:15 splitting.
- Grouping by source document and highly similar normalized text to reduce leakage.
- Fixed-`k` precision/recall for semantic retrieval, classification summaries, threshold locking from validation labels, agreement/error statistics, and paired-test utilities.
- EQAM descriptive/agreement summaries, complete-case EQAM/RRS association and regression diagnostics (only when an a-priori sample-size requirement is supplied), Best-Fit/close-margin agreement, robustness scenario summaries, and explanation evidence/numerical-fidelity checks.
- Explicit A0-A4 component descriptions and prerequisite-based readiness states.
- Persistent dataset, expert-reference, experiment, and prediction tables. Research endpoints are institution-membership protected.
- Authenticated all-or-nothing CSV/JSONL import with private original-file retention, SHA-256, durable line-level reports, strict schema/source validation, and institution-scoped report retrieval.
- Five-distinct-reviewer panel ratings with institutionally recorded qualification status, independent categorical and optional continuous ratings, rubric version, timestamp, and rationale. The review queue withholds imported labels, model predictions, and peer judgments. Fleiss' kappa is calculated from complete five-rater cases; ICC(2,1) is returned only as a diagnostic candidate, pending researcher decision. The legacy two-review workflow cannot authorize dataset approval.
- Per-case consensus/adjudication records linked to a referenced procedure version. Dataset approval requires five currently qualified ratings per case, recorded outcomes for every case, and source-use/institutional-approval references. The application records these attestations but cannot independently validate external credentials, DUA/licensing, or adviser approval.
- Preflight checks for approved datasets, annotation state, deterministic partition manifests, local model artifacts, protocol approval, scoring gates, expert references, and XAI inputs.
- Authenticated experiment preflight, run-request, and run-detail endpoints. Execution records preserve preflight state, start/completion timestamps, dataset and split versions, seed, model version, warnings, sample counts, evaluation configuration, and safe failure diagnostics.
- A real A0 pretrained Sentence-BERT retrieval evaluator that loads only a locally configured artifact, ranks held-out evidence against the approved indicator catalog, and calculates P@K/R@K from consensus test labels after inference. The A0 retrieval adapter receives only test evidence and no labels; A1-A4 remain unimplemented.
- A runner contract that validates complete held-out prediction coverage and stores predictions/results atomically. Retrieval and full readiness are distinct evaluation scopes.
- A research dashboard that shows per-configuration prerequisites and run states. It displays metrics only for completed execution records and does not display illustrative values as results.

## Experiment runner status

The service has a production A0 retrieval-only execution path plus preflight, result validation/persistence, and API/UI orchestration. The runner hashes the configured local model artifact and requires the approved protocol to record that digest/version/configuration, the exact indicator-catalog digest, binary relevance mapping, P@K/R@K cutoffs, and embedding settings. SentenceTransformer loads with `local_files_only=True`; there is no network download or fallback. The baseline executor receives only held-out test evidence and indicator descriptions. Expert consensus labels are read only after inference to calculate retrieval metrics. Synthetic adapter tests run only against temporary databases and do not create research results. Chapter 3 Table 3.9 defines A0 as pretrained Sentence-BERT plus conventional AHP-TOPSIS; the current retrieval-only executor is not that complete A0 baseline.

This retrieval component is not full A0 readiness scoring. Conventional AHP–TOPSIS, criterion aggregation and verified weights remain separately gated, so readiness-scope A0 does not run and no AES/RRS/ARRS result is produced. A1-A4 remain unimplemented. The repository still lacks the authorized HEI institutional corpus, five-expert reference judgments, verified framework criteria/weights, approved scoring rubrics, and a selected/approved local artifact/protocol; therefore no empirical run/result has been established. The 120-record WURI workbook abstract pilot is a private content-review candidate set only, not the institutional evidence corpus or an evaluation dataset.

The split algorithm is now versioned as `grouped-stratified-70-15-15-v3-approved-leakage-groups`, grouping source documents, explicitly provided leakage groups, and exact/highly similar text before deterministic assignment. The persisted manifest is reproducible independent of row ordering. Older split manifests are not accepted as reproducible by the new preflight.

The split algorithm records actual partition counts and warnings because indivisible document/leakage/near-duplicate groups can prevent exact 70:15:15 record counts. It does not change the requested proportions. Dataset versions are immutable; corrections require a new version. Uploaded labels remain provisional until two distinct reviewers independently confirm/correct them; disagreements require a third reviewer. Dataset approval requires completed consensus on every record. Test labels are not exposed to the A0 retrieval executor or used for threshold selection.

Classification reports use zero for a class metric with a zero denominator and report every observed or predicted class; empty samples return null aggregate metrics. Retrieval precision@k divides by the requested k, while recall@k divides by the query's expert-labeled relevant-set size; queries with no relevant items are counted but excluded from averaged metric denominators. Agreement metrics and statistical tests report sample counts and limitations; successful function execution is not interpreted as a substantive or statistically significant finding.

## Experimental definitions and limits

The A0 evaluator uses the configured pretrained baseline only for retrieval metrics; it does not train or fine-tune a model and is not evidence of an enhanced model. A0 readiness scoring still requires an approved conventional AHP/TOPSIS configuration and resolved criterion aggregation. A1 requires a versioned enhanced model artifact and reproducible training provenance. A2/A3 additionally require expert validation, a locked validation threshold, approved aggregation, and verified framework knowledge/weights. A4 additionally requires an explicit XAI instrument and expert/user ratings.

Undefined methodology details (including precise conventional baseline weights, the authoritative significance criterion, and the dissertation's exact statistical/ablation protocol) are not guessed. Confirm them against Chapter 3 before presenting protocol-compliant results. The regression helper uses a caller-supplied preregistered minimum sample size, complete-case handling, standardized coefficients, VIF, residual normality and Breusch-Pagan diagnostics, and Holm adjustment for five Spearman tests. Its associations remain descriptively coupled to AES and are not causal estimates.

## Safe interpretation

Controlled test fixtures are marked as synthetic in tests and are never included in the research database or UI summaries. The dashboard separates retrieval metrics from readiness results: a retrieval-only run cannot set the readiness-results flag or be presented as an A0 readiness score. Passing tests validates implementation behavior only; it does not demonstrate algorithm superiority or answer the dissertation's research questions.

## Phase 8 execution-readiness audit (2026-10-14)

The current local SQLite database was queried in read-only mode: it contains zero research datasets, zero examples, zero approved datasets, and zero completed A0 retrieval runs. The working tree has no `UniversityRanking_V3.1.docx`, backend `.env`, or `backend/models` directory, and the baseline model path/version and approved protocol path are not configured. The backend virtual environment has `sentence-transformers` 5.6.1, `transformers` 5.14.1, `torch` 2.13.0, and `numpy` 2.5.1 installed; this verifies dependency availability only, not model loading or inference.

The A0 runner was tightened to:

- Pass the inference executor only test example IDs, framework/indicator IDs, evidence text, and partition name. It does not pass labels, annotation/review fields, original model predictions, or the label-derived preflight summary.
- Require the approved retrieval protocol to confirm the exact implemented query grouping, eligible-query rule, K denominators, per-framework/overall aggregation, undefined-metric behavior, and tie-breaking. These are implementation semantics awaiting authoritative approval, not declared dissertation methodology.
- Require an approved positive integer `max_seq_length` and apply it to the loaded local SentenceTransformer; unsupported model settings cannot silently go unused.
- Fingerprint the approved protocol, verify the local artifact before inference and after predictions, and persist the protocol fingerprint, partition/query counts, and installed runtime dependency versions.

The previously recorded A0 preflight remains `blocked_missing_data`; no experiment was run in Phase 15. The five-expert workflow is implemented, but no real expert qualifications, reviews, consensus records, approved procedure, source-use clearance, or institutional approval were created. Outstanding prerequisites also include the authorized institutional evidence corpus, approved consensus/eligibility/ICC/missing-rating/rubric decisions, verified official criteria and weights, the approved Chapter 3 protocol, and an approved local baseline artifact. The A0 executor is retrieval-only, not the complete Sentence-BERT plus conventional AHP-TOPSIS baseline. No model inference or readiness scoring occurred.

## Phase 15 — five-expert review infrastructure

Migration 005 is additive and preserves prior review rows. Existing datasets approved through the legacy two-review workflow are reclassified as submitted legacy datasets and receive an audit event; they cannot pass the new runner preflight. New datasets use the five-expert design. Reviewer qualification and consensus-procedure references are stored per institution, and individual panel ratings are unique by dataset, case, and reviewer. Panel ratings are immutable; corrections require a new dataset version.

Fleiss' kappa uses complete categorical five-rater cases. This missing-rating handling is an operational candidate, not a Chapter 3 requirement. ICC(2,1) is calculated only as a diagnostic candidate and marked `requires_researcher_decision`; Chapter 3 does not specify the ICC model. Undefined values are returned as null with an explicit status, not numeric zero. No agreement values from real research judgments exist.

Consensus is recorded explicitly under a referenced procedure version; no majority, unanimity, or disagreement rule is inferred. Expert-eligibility criteria, consensus/adjudication policy, ICC model, missing-rating policy, minimum case requirements, and interpretation thresholds remain unapproved. Approval references are recorded as administrator attestations and are not independently verified by the application.

## Phase 9 methodology traceability

The earlier Phase 9 audit could not locate the dissertation and made no Chapter 3 alignment claims. That finding is superseded: `UniversityRanking_V3.1.docx` has since been placed in the ignored private research-input folder and directly reviewed for Phase 14. See [research-methodology-traceability.md](./research-methodology-traceability.md) for the source-based matrix and [a0-retrieval-protocol-draft.json](./a0-retrieval-protocol-draft.json) for the unapproved draft. Its `approval_status` remains `pending_researcher_approval`; it must not be configured as the active protocol.

The traceability work also exposed and fixed an implementation defect: `label_is_relevant` returned `None` for unsupported values rather than raising its intended validation error. A regression test now covers rejection of an unrecognized label. The test suite and other build commands verify software behavior only; the draft does not constitute a methodology decision or research approval.

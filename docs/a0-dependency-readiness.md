# Phase 16A — WURI research readiness and A0 dependency audit

## Audit boundary and evidence inspected

This is a source and configuration audit only. No model was loaded, no A0–A4 executor was called, and no RRS/ARRS score or empirical result was produced.

The audit inspected the private `UniversityRanking_V3.1.docx` in `backend/private/research-input/`, the local application modules and protocol draft, and the configured local backend database. Chapter 3 references below use Sections 3.2–3.5, 3.7, 3.9–3.10 and Tables 3.1–3.5, 3.8–3.9 as applicable. The reviewed dissertation copy contains no embedded adviser comments; no separate comments were available.

At audit time:

- The draft protocol at [`a0-retrieval-protocol-draft.json`](./a0-retrieval-protocol-draft.json) is still `pending_researcher_approval`.
- The backend `.env` file is absent. `WURI_BASELINE_MODEL_PATH`, `WURI_BASELINE_MODEL_VERSION`, and `WURI_RESEARCH_PROTOCOL_PATH` are not configured in the current process. The expected baseline model directory is not present at the checked project model locations. No model artifact SHA-256 can therefore be established.
- The project's default local SQLite database has migrations 001–005 applied, but contains zero assessments, source documents, evidence passages, research datasets/examples, expert panel reviews/consensus records, and research predictions. No expert qualifications or consensus procedures are recorded.
- The dissertation, 120-record WURI abstract pilot, and private review workbook exist in the ignored research-input folder. The pilot is not an authorized institutional evidence corpus and is not present in the research database.
- Framework catalog data currently consists of four provisional retrieval descriptions per framework. Their methodology versions, source URLs, official criteria provenance, and weights are not verified.

## Dependency readiness matrix

| Requirement | Chapter 3 requirement | Current implementation | Available input / local verification | Status | Next action |
|---|---|---|---|---|---|
| Official framework criteria and weights locked to edition | Table 3.1 names WURI 2026, THE World University Rankings 2026, QS World University Rankings 2026, and UI GreenMetric 2025. Sections 3.2.3 and 3.5.7 require the adopted criteria/weights to be held constant; published weights stay fixed where directly usable. | [`frameworks.py`](../backend/app/frameworks.py) marks all four definitions `provisional_retrieval_catalog` / `unverified`, with no source, version, or checked date. [`indicators.py`](../backend/app/indicators.py) has four prototype descriptions each. `verified_frameworks()` returns none. | Version names are known from the dissertation; official full criteria, weight documents, and digests are not in the repository. [`framework-criteria.md`](./framework-criteria.md) also records them as unverified. | **Missing research input** | Supply authoritative edition-specific catalogs and weight sources. Map each criterion and subcriterion, preserve source citations, compute source/catalog digests, and approve a version lock. Do not substitute equal weights or prototypes. |
| Authorized institutional documents and evidence provenance | Sections 3.2.1–3.2.2 and 3.9 require official HEI-provided evidence, authorization/DUA, screening, and source/date/page-or-section/unit traceability. | Import and passage storage can retain text and source-document/passage IDs. Approval requires each case to resolve to a document registered to the institution and validates any passage-to-document association. The system still cannot establish source authenticity, authorization, licensing, privacy clearance, or adequacy of provenance by itself. | Private WURI program abstracts and their links support only pilot content review; no authorized HEI evidence or DUA was found in the database. | **Missing research input** | Obtain institution-authorized records, source metadata, clearance and data-use terms; verify source identity, traceability, privacy and retention requirements before import. |
| Five-expert review and consensus procedure | Sections 3.3.1 and 3.3.4 and Tables 3.2–3.3 specify five domain experts, independent judgments before consensus, and retained ratings. | Migration 005 and the panel API store distinct reviewer judgments, qualifications, rubric version, optional ratings, and a separate procedure-linked consensus record. Approval requires five qualified reviewers per case, one shared panel/rubric and one procedure. It does not choose a majority or other consensus rule. | No expert qualifications, panel reviews, consensus procedures, or consensus records exist in the default database. | **Infrastructure present; research input/decision missing** | Researcher/adviser must define eligibility and consensus/adjudication policies; institution must verify real qualifications and record actual independent reviews. No approval may be inferred from test fixtures. |
| Approved retrieval relevance rubric and labeled cases | Sections 3.5.4 and 3.7.3 evaluate retrieval against expert relevance judgments. | Binary label import/validation and five-person judgment persistence exist. A0 retrieval calculates metrics only after inference and label isolation. No approved operational relevance rubric or genuine labels are present. | 120 private WURI abstracts are unannotated operational candidates, not indicator-level institutional evidence and not evaluation cases. Local research database has zero examples. | **Missing research input** | Supply an approved relevance rubric and eligibility instructions, then obtain authorized, independent labels for the proper evidence corpus. |
| Sentence-BERT baseline artifact, identity, checksum and configuration | Sections 3.5.1 and 3.7.4 specify an off-the-shelf pretrained Sentence-BERT baseline; exact model identity/revision and deployment settings are not prescribed. | A local-only SentenceTransformer A0 retrieval executor exists. Preflight requires model path, version, actual artifact SHA-256 and approved `max_seq_length`; inference has no remote fallback. The executor only performs retrieval, not scoring. | No baseline path/version environment settings or expected model artifact directory were found. No checksum, revision, or model configuration can be verified. | **Missing research input** | Researcher selects and approves exact model ID/revision, provenance/license, local artifact, checksum and configuration. Do not download or choose a model in this phase. |
| Criterion-level evidence aggregation rule | Sections 3.5.8–3.5.9 and 3.7.6 define normalized criterion value `x_fj` and its scoring role; they do not say how multiple accepted passages/documents reduce to one criterion value. | No production aggregation exists. The runner requires an approved, versioned `criterion_aggregation_policy` before conventional scoring. | `methodology-decisions.md` lists unresolved duplicates, conflicts, missing evidence and freshness behavior; no policy is selected. | **Researcher/adviser decision** | Approve evidence-set membership, duplicate treatment, conflicting evidence, missingness, freshness, and exact transformation to `x_fj`; implement and test that versioned rule. Block RRS until then. |
| Conventional AHP–TOPSIS integration | Table 3.9 defines A0 as pretrained Sentence-BERT plus conventional AHP–TOPSIS. Sections 3.5.7–3.5.9 describe weights, AHP consistency and fixed-reference TOPSIS. | `ahp.py` calculates AHP weights/CR and `topsis.py` calculates fixed-reference TOPSIS from caller-provided vectors. No end-to-end pipeline maps approved evidence to `x_fj`, loads official framework weights, and produces per-framework RRS. Runner explicitly registers only retrieval A0; readiness scope has no executor. | No approved catalog, aggregation policy, scoring configuration, or real corpus is available. | **Implementation gap plus missing inputs** | Implement the full readiness A0 pipeline only after the criterion model, catalog/weights, aggregation and protocol are approved. Keep retrieval evaluation separate. |
| Grouped 70:15:15 split manifest | Section 3.5.4 requires 70:15:15 stratification by framework and major indicator group where sample size permits; Section 3.7.4 requires shared partitions for compared methods. | Deterministic grouped stratified splitting and manifest reproduction checks are implemented. Additional exact/near-duplicate/leakage grouping choices exceed the stated details and remain unapproved. | No dataset/examples or manifest are present in the default database. | **Infrastructure present; data/decision missing** | Approve the extra grouping and seed choices; create a manifest only after genuine data and labels are ready. Do not partition the 120-record pilot for evaluation. |
| Retrieval metrics and query definitions | Sections 3.5.4 and 3.7.3 specify cosine similarity, Precision@K and Recall@K at K=1,3,5 against expert judgments. Query grouping, pool, eligibility and aggregation are not specified. | Metric helpers and a Sentence-BERT retrieval executor exist. Code assumes framework/indicator-pair queries, same-pair test candidates, excludes queries with no relevant candidate from macro metrics, and uses example-ID tie-breaks. Preflight requires exact definitions to be explicitly approved. | Draft contains the current candidate definitions but marks them unapproved. No labeled query set exists. | **Researcher/adviser decision** | Approve query unit and candidate eligibility/pool, zero-relevant handling, across-query/framework aggregation, undefined-metric rule and tie-breaking. Chapter 3’s K values need no reinterpretation. |
| EQAM expert-validated rubrics and model-confidence calibration | Sections 3.5.5–3.5.6 and Table 3.4 name five dimensions, [0,1] normalization and initial equal AES weights 0.20; operational anchors and calibration details are not complete. | `eqam.py` implements weighted arithmetic and a generic completeness checklist, marked provisional. There is no approved source-reliability/evidence-strength rubric, indicator checklist or confidence calibration pipeline. | No expert ratings or calibration dataset exists. | **Missing decisions and research input** | Approve detailed anchors, raters’ instructions, checklist sources, missing/unassessable rules and model-confidence calibration method; validate on appropriate data before EQAM scoring. |
| Validation-set acceptance threshold | Section 3.5.6 requires threshold selection on validation AES against acceptable/insufficient expert labels, prioritizing macro-F1 and balanced precision-recall behavior, then locking before test use. | `calibrate_threshold` implements validation-style candidate selection and locks a result; the helper uses macro-F1, then balanced accuracy, then favors the higher threshold. | No validation partition, expert labels, or approved precise tie-break definition is present. | **Researcher/adviser decision + data missing** | Approve the operational meaning/tie-break for “balanced precision-recall”; then run calibration only after approved validation data exist and lock before test evaluation. |
| ICC model and missing-rating policy | Sections 3.3.4 and 3.10 require ICC for continuous/quasi-continuous ratings but do not specify the ICC form or missingness policy. | Agreement endpoint computes Fleiss’ kappa for complete categorical five-rater cases and returns an ICC(2,1) candidate from complete continuous cases, explicitly marked as decision-pending. | No actual ratings exist. | **Researcher/adviser decision** | Select and justify ICC model (including single/average measure and consistency/absolute agreement), missingness policy, eligible-case minimum and interpretation. Do not report the diagnostic candidate as the approved statistic. |
| Source-use, privacy and institutional approvals | Sections 3.2.1–3.2.2 and 3.9 require authorization and traceable institutional data. | Dataset approval requires clearance and institutional-approval references and logs reviewer actions. References are attestations, not independently verified evidence. | No reference is in the database; the private pilot remains ignored by Git. | **Missing research input/approval** | Provide applicable DUA/source permissions, ethics/privacy review, institutional approval and retention/access requirements; have an authorized administrator verify and record them. |
| Protocol and experiment approval | Chapter 3 methods must be operationalized and approved before evaluation. | Protocol loader uses `WURI_RESEARCH_PROTOCOL_PATH`; it fails closed if no valid approved manifest. It is configured to remain pending here. | Draft exists at `docs/a0-retrieval-protocol-draft.json`; protocol path is unset and the draft is not an approved active protocol. | **Pending decision/approval** | Resolve the decisions above, version and approve the completed protocol, then configure its path. Do not change the pending status to enable execution. |

## Methodological decisions that must remain open

| Decision | What Chapter 3 says | What software currently assumes or implements | Not specified by Chapter 3 | Decision required and blocked component |
|---|---|---|---|---|
| Criterion-level evidence aggregation | A normalized criterion value `x_fj` enters fixed-reference scoring. | Runner accepts a versioned policy only when marked approved; no aggregation algorithm is implemented. | Passage/document aggregation, contradictory evidence, duplicate handling, missing criteria, freshness, and `x_fj` transformation. | Researcher/adviser selects a policy; **block all criterion values, RRS, ARRS and readiness A0**. |
| Retrieval query eligibility and aggregation | Cosine similarity and P@K/R@K for K=1,3,5. | Current candidate implementation groups by framework/indicator, evaluates matching test candidates, counts only queries with at least one relevant candidate, macro-averages and tie-breaks by example ID. | Query unit, candidates, all-negative queries, macro/micro aggregation and ties. | Approve every convention; **block empirical A0 retrieval metrics**. |
| ICC model and missing ratings | ICC is named for continuous/quasi-continuous agreement. | Complete five-rater cases only; computes ICC(2,1) candidate. | Model type, fixed/random raters, single/average measure, consistency/absolute agreement, missingness and thresholds. | Approve model and policy; **block reporting ICC as study result**. |
| Consensus policy | Independent expert judgments precede consensus. | No automated rule; administrator records an explicit outcome under a procedure version. | Majority/unanimity, disagreement resolution, adjudicator role and acceptable disagreement. | Approve a versioned method; **block final consensus and dataset approval**. |
| Expert qualification criteria | Five domain experts validate. | Administrator records a verification status and reference for each expert identity. | Required credentials, disciplines, experience, independence and conflict-of-interest handling. | Approve eligibility and verify actual people; **block counting reviewers as qualified**. |
| Framework weight provenance | Published weights fixed where available; AHP may address uncovered subcriteria/mappings; CR ≤0.10. | AHP utility accepts pairwise matrices; framework catalogs have no official weights and are all unverified. | Exact adopted source edition, hierarchy/mapping where official weights cannot be used, and provenance of each weight. | Obtain authoritative catalogs and decide documented mappings; **block scoring weights and framework RRS**. |
| AES threshold tie-break | Validation-only threshold against expert labels, prioritize macro-F1 and balanced precision-recall. | Macro-F1 then balanced accuracy then higher threshold. | Exact definition of balanced behavior and tie resolution. | Approve tie-break before validation calibration; **block locked threshold/test evaluation**. |
| EQAM operationalization | Five dimensions, normalized [0,1], initial equal weights. | Arithmetic aggregation exists but dimension inputs are not validated against full rubrics. | Full anchors, model confidence calibration, checklists, source assessment and missing values. | Approve rubrics/calibration; **block AES and EQAM ablations**. |
| Criteria/version lock and catalog digest | Four editions are specified; criteria held constant. | Digest currently fingerprints provisional code descriptions. | Exact official catalog package, source versions, corrections and update policy. | Obtain and lock official source/version/digest; **block approved indicator use and scoring**. |
| Data authorization | Formal authorized institutional evidence with traceability. | Import validates data shape and institutional access, not permission or truth of provenance. | Exact DUA, privacy, licensing, ethics, retention and cross-institution policy. | Obtain relevant approvals; **block dataset research approval and experiments**. |

## A0 baseline architecture and boundary

```text
Authorized HEI source documents
  [DUA / source-use / privacy / institutional approval]
        |
        v
Document extraction and traceable evidence passages
  [document ID, checksum, date, page/section/unit provenance]
        |
        v
Sentence-BERT retrieval
  [approved local artifact + identity/revision + SHA-256 + max sequence length]
  [approved, version-locked framework criteria/catalog descriptions]
        |
        +---- Retrieval evaluation (separate outcome)
        |       [five-expert relevance labels, approved query/pool rules]
        |       [P@K / R@K for K=1,3,5; no readiness score]
        |
        v
Approved accepted-evidence set per criterion
  [approved EQAM rubrics / validation-locked threshold where applicable]
        |
        v
Criterion-level aggregation to x_fj
  [explicit approved duplicate/conflict/missing/freshness policy]
        |
        v
Conventional AHP–TOPSIS per framework
  [official published weights fixed where usable]
  [approved AHP mappings only where required; accepted CR <= 0.10]
  [fixed ideal = final criterion weights; anti-ideal = 0]
        |
        v
Framework-specific RRS (0–100)
```

The current code implements only parts of this flow. `document_processing.py` extracts text and the application can preserve passage/document metadata; panel dataset approval now checks registered source documents and passage/document consistency, but source authorization and full study provenance still require review. The retrieval module and registered A0 executor rank passages against provisional descriptions; that is not proof of ranking readiness. `ahp.py` and `topsis.py` are mathematical helpers with caller-supplied inputs; there is no full readiness executor joining approved evidence, official criteria/weights, aggregation, AHP and TOPSIS. Accordingly, no A0 readiness RRS/ARRS is available or permitted.

ARRS is a subsequent equal-framework aggregation of valid framework RRS values, and Best-Fit selects the highest RRS subject to its close-margin expert-review rule. Neither should run until all underlying framework scores and approvals exist.

## Safe implementation assessment

No additional code change was necessary to complete this dependency audit. Existing runtime gates already distinguish retrieval-only from readiness execution, require local model identity and a protocol, and block conventional scoring without versioned aggregation/scoring configuration. The A0 protocol remains pending. The current local DB and environment checks were read-only. No remote model, synthetic research input, or experimental score was created.

## Researcher inputs needed next

1. Official criteria and published-weight documents for all four Chapter 3 editions, with provenance and authorization to use them.
2. Authorized institutional source documents, source metadata, DUA/data-use basis, and applicable ethics/privacy/institutional approvals.
3. Approved expert eligibility criteria, reviewer conflict rules, relevance rubric, consensus/adjudication procedure, and five actual qualified independent reviewers.
4. Decisions on criterion aggregation, retrieval query/pool/eligibility/aggregation, ICC model/missingness, EQAM anchors/confidence calibration, and threshold tie-break.
5. Exact Sentence-BERT baseline model ID/revision, provenance/license, local artifact, checksum and settings.
6. Once the above is complete, an approved protocol version and a genuine reviewed corpus. Only then should the team consider dataset partitioning and a separate A0 preflight; this phase did not execute it.

7. A dated CHED HEI population manifest, approved unit of sampling, inclusion/exclusion rules, and framework-specific eligibility decisions. No nationwide population freeze or participating-institution corpus exists yet.

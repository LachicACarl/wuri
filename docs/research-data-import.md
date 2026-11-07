# Research data import and review

## Institutional evidence-document intake

The protected `POST /api/upload` endpoint accepts PDF, DOCX, and UTF-8 TXT
documents for an authenticated administrator or evaluator belonging to the
selected institution. The selected framework edition and criterion are
validated against the registered dissertation editions and current catalog;
the mapping is stored separately from the shared framework definitions.

Uploaded files are stored under the private storage root with a generated
storage key and SHA-256 checksum. The server validates the extension and
basic content signature (PDF, DOCX archive, or UTF-8 text), extracts text,
and records passages under the institution and assessment. Uploading sets
authorization and research-use permission to `unknown`; browser-supplied
permission flags cannot verify source rights. Only an institution
administrator can change permission fields or mark a document verified.

Document metadata tracks title, source reference, collection date, reporting
period, provenance, limitations, processing/review state, and framework
criterion mapping. Authenticated downloads are membership-checked and
audited; deletion is administrator-only and removes the database record and
private storage object. Failed extraction does not create verified evidence.
The application does not provide antivirus scanning or independent validation
of DUAs, copyright, ethics approval, or institutional authorization. Those
checks remain human/institutional responsibilities and unknown states remain
unverified.

The protected `POST /api/research/datasets/import` endpoint accepts UTF-8 CSV or JSONL multipart uploads. It is restricted to an administrator or evaluator with access to the selected institution. Dataset metadata is supplied as multipart fields: `dataset_version`, `annotation_version`, `provenance`, and `random_seed`.

## Required record fields

Each row/object must provide:

| Field | Meaning |
|---|---|
| `example_id` | Unique stable ID within the dataset version. |
| `framework` | Exact framework key from the current indicator catalog (`WURI`, `THE`, `QS`, or `UI GreenMetric`). |
| `indicator` | Exact indicator key listed under the selected framework in `app/indicators.py`. |
| `label` | Binary relevance: `true`/`false`, `1`/`0`, `yes`/`no`, `positive`/`negative`, or `relevant`/`not_relevant`. Source spelling/value is retained. |
| `source_document_id` | Stable document identifier used for traceability and leakage grouping. |
| `institution_group_id` | Identifier of the originating institution/dataset group. |
| `text` or `source_passage_id` | Evidence text or a passage ID already accessible to the importing institution. If both a local document and passage are supplied, their relationship must match. |

Optional fields are `major_indicator_group`, `leakage_group_id`, `annotation_version`, `annotation_provenance`, and `model_prediction`. Predictions are stored separately from expert labels. A supplied leakage-group identifier ties its records together during partitioning; source-document IDs and exact/near-duplicate text are grouped as well. Grouping identifiers are metadata, not authorization credentials.

Example CSV:

```csv
example_id,framework,indicator,label,source_document_id,institution_group_id,text,model_prediction
ex-001,WURI,Industrial Application,relevant,doc-001,source-university-1,"Evidence passage text","{""score"":0.82}"
ex-002,WURI,Industrial Application,not_relevant,doc-002,source-university-1,"Another evidence passage","{""score"":0.13}"
```

Example JSONL:

```jsonl
{"example_id":"ex-001","framework":"WURI","indicator":"Industrial Application","label":"relevant","source_document_id":"doc-001","institution_group_id":"source-university-1","text":"Evidence passage text","model_prediction":{"score":0.82}}
{"example_id":"ex-002","framework":"WURI","indicator":"Industrial Application","label":"not_relevant","source_document_id":"doc-002","institution_group_id":"source-university-1","text":"Another evidence passage","model_prediction":{"score":0.13}}
```

Imports are all-or-nothing. The maximum upload is 25 MB, the maximum dataset is 2,000 rows, and evidence text is limited to 10 MB total. Invalid encodings, malformed rows, duplicate IDs/annotation pairs, unknown framework-indicator combinations, invalid labels, missing provenance/grouping/source fields, inaccessible passages, and inconsistent local document references reject the import; no rows are silently skipped or partially inserted. Each rejection report includes a source line where available. The exact uploaded bytes and report remain private and institution-scoped; the report endpoint does not expose the stored file.

## Independent review and consensus

New datasets use the five-expert panel workflow. The same five distinct, institutionally verified expert accounts must independently submit a categorical relevance judgment for every case under one rubric version; optional continuous/quasi-continuous rubric dimensions are stored with that judgment. The database prevents repeat ratings by the same reviewer and the review queue does not disclose the imported label, predictions, or other reviewers' identities/judgments. Reviewer qualification is recorded by an institutional administrator with a qualification reference and rationale; this records the institution's verification and does not establish that the dissertation's expert-eligibility criteria have been approved.

The old two-review/third-person workflow remains only for backward compatibility with legacy records. It cannot satisfy five-panel approval. Migration 005 marks prior two-review datasets as legacy and invalidates their prior approval state without deleting their records.

Fleiss' kappa is computed from complete five-rater categorical panels; cases with missing panel ratings are excluded and counted. Undefined kappa is returned as null with a status, not reported as zero. Continuous dimension statistics use complete five-rater cases and return an ICC(2,1) diagnostic candidate. Chapter 3 says ICC but does not specify its model; the candidate is not an approved study result until the researcher/adviser selects the model, missing-rating policy, minimum case requirements, and interpretation rules.

The application does not infer consensus from a majority or automatically adjudicate disagreements. An administrator records an explicit per-case outcome and rationale against a consensus procedure version with an approval reference. Dataset approval is blocked unless every case has five currently qualified reviewers using one rubric version and a procedure-linked consensus/adjudication record, and source-use clearance and institutional-approval references are recorded. The application stores those references as institutional attestations; it cannot independently validate an external DUA, source-use permission, expert credential, or adviser approval. Do not treat these software gates as approval of the dissertation protocol. Panel judgments are immutable; corrections require a new dataset version.

## Genuine A0 intake checklist

Complete and verify this checklist before asking an independent administrator to approve a dataset. Upload validation checks data shape and institutional access; it cannot establish that evidence, labels, provenance claims, or reviewer qualifications are genuine.

### Required for every evidence record

- [ ] A stable, unique `example_id` within an immutable `dataset_version`.
- [ ] Actual institutional evidence text, or an existing institution-accessible `source_passage_id`; retain a verifiable source document and its provenance.
- [ ] A `source_document_id` that identifies the source document and is consistent with any referenced passage.
- [ ] An exact supported `framework` and `indicator` identifier from the currently installed catalog; catalog authority remains a separate approval.
- [ ] An expert binary relevance label and documented `annotation_version` and `annotation_provenance`. The imported value is provisional, not consensus.
- [ ] The originating `institution_group_id`; supply `leakage_group_id` where the approved grouping protocol requires it.
- [ ] Evidence that data use and access are authorized, and that source identity, confidential information, and personal data are handled under the applicable institutional privacy controls.

### Required before A0 preflight can pass

- [ ] Five distinct, actually qualified domain experts independently judge every record under the approved rubric version. The application checks distinct identities and recorded qualification status; the researcher/institution must verify qualifications and eligibility criteria.
- [ ] Obtain researcher/adviser approval for the consensus/adjudication procedure and record the exact procedure version. The application does not choose a majority rule.
- [ ] An independent administrator records the consensus/adjudication outcome and approves the completed dataset only after all five judgments and external clearance references are verified.
- [ ] Use the stored deterministic grouped 70:15:15 manifest. Inspect document, explicit leakage-group, exact-text, and near-duplicate grouping; the implementation groups using five-token shingles and a 0.90 Jaccard threshold. This policy is not dissertation-verified and needs researcher approval.
- [ ] Check the actual partition counts. Group indivisibility can make record counts depart from exactly 70:15:15.
- [ ] Confirm the held-out test set contains at least one framework/indicator test query with at least one consensus-relevant candidate. Record eligible and ineligible query counts; do not alter labels to make a query eligible.
- [ ] Keep the original upload, source documents, provenance evidence, annotation history, dataset version, split seed, and access/audit records available to authorized reviewers.

### Missing versus invalid inputs

**Missing inputs** include no genuine evidence corpus; absent source provenance; no approved annotation/relevance protocol; no completed independent reviews or adjudications; no independent dataset approval; no approved split/grouping policy; no eligible relevant test query; no approved indicator source; no approved model artifact; or no approved A0 protocol. Missing inputs block research execution. Do not fill them with examples, labels, approvals, or model predictions created for software tests.

**Invalid inputs** include duplicate or blank IDs; unsupported framework/indicator or label values; malformed CSV/JSONL; absent required metadata; unresolvable or inaccessible passages; mismatched passage/document references; unauthorized or unverifiable source records; failed reviewer independence/adjudication; irreproducible split assignments; invalid artifact digest/configuration; or a protocol whose approval fields or definitions do not match the executed implementation. Reject or correct these through an auditable new import/version; do not bypass validation.

## A0 retrieval evaluation boundary

The runner reproduces the persisted grouped 70:15:15 split from the original imported labels. The A0 retrieval evaluator is a pretrained Sentence-BERT baseline, not a fine-tuned model. It loads only a local model artifact with `local_files_only=True`, ranks held-out test evidence against the approved framework-indicator descriptions using cosine similarity, and computes P@K/R@K for K=1,3,5 from consensus labels only after inference. Test labels, train records, and validation records are not passed to this baseline executor.

Preflight requires an approved protocol to record the exact local artifact SHA-256 and model version/configuration, the indicator-catalog digest/version, binary relevance-label mapping, retrieval cutoffs, and encoding parameters. The currently supported baseline model configuration is the approved positive integer `max_seq_length`; the evaluator applies it to the loaded local model, and preflight rejects settings it would otherwise ignore. A retrieval-only A0 result is not a full readiness result. AHP–TOPSIS, criterion aggregation, verified framework criteria/weights, and RRS/ARRS remain separately gated; A1-A4 are not implemented by this import/retrieval workflow.

The retrieval protocol must also explicitly approve the evaluator's query and metric definitions: a query is one framework/indicator pair; candidates come only from the matching held-out test records; a query is eligible when it contains at least one consensus-relevant candidate; precision divides by K; recall divides by the number of relevant candidates; per-framework and overall results are macro means over eligible queries; undefined metrics are `null`; and tied similarities are ordered by example ID. These values describe the current implementation, not an authoritative methodological decision. Chapter 3 or a separately approved protocol must confirm them before preflight permits A0. The inference executor receives only held-out example IDs, framework/indicator IDs, evidence text, and partition name; it does not receive labels, annotation status, source model predictions, or label-derived preflight summaries. Preflight fingerprints the approved protocol, and execution rejects protocol changes after preflight or local artifact changes before or after inference. Completed runs persist per-framework and aggregate query counts plus the installed SentenceTransformers, Transformers, PyTorch, and NumPy versions. The configured local artifact path is not returned in user-facing reports.

## Baseline artifact readiness

Supply the baseline as a complete local Sentence-Transformers model directory accepted by the loader (`modules.json` plus the model configuration files). Record its canonical model identity, immutable upstream revision or provenance, locally configured version string, complete artifact SHA-256, and every inference-affecting configuration value. The current evaluator specifically requires a researcher-approved positive integer `max_seq_length`; it applies this value after local model loading. Do not set `local_files_only=False`, fetch weights at run time, or substitute a different model when an artifact is missing.

The backend dependency manifest names SentenceTransformers, Transformers via its dependency tree, PyTorch via the model package, and NumPy; its current broad version constraints are not an exact environment lock. At the Phase 9 audit the configured backend venv reported `sentence-transformers 5.6.1`, `transformers 5.14.1`, `torch 2.13.0`, and `numpy 2.5.1`. These are installed-package observations, not a protocol pin or evidence of successful inference. Record approved/pinned runtime versions and platform details with the protocol/run before claiming reproducibility. Keep model paths and credentials in local protected configuration; user-facing reports may expose version and checksum, but not private paths or raw evidence.

The current source and artifact check is insufficient to establish authorship, licensing, trustworthiness, or equivalence to a named upstream model by itself. Researcher approval of identity and provenance is required in addition to a matching checksum.

## WURI 2026 workbook source-access sample

On 2026-10-16, an unauthenticated, bounded source-download check was run against the 12 Abstract and Template links for six records in categories A1, A8, B3, B8, C3, and C8. The original Drive links were tested through Google's standard public download endpoint. Requests used no credentials, cookies, session tokens, or configured proxy; HTTPS redirects were restricted to Google document-delivery hosts. Each response was limited to 8 MiB with a 20-second timeout, and source bytes were processed in memory and not saved.

All 12 requests returned HTTP 200 with `application/octet-stream` content from Google's Drive download host. The response bodies were verified as PDF bytes, rather than HTML viewer pages, and the existing PDF extractor returned non-empty text for every file (834 to 43,705 extracted characters). No login or permission requirement was encountered in this sample. The private sample audit records the workbook row/cell references, response metadata, extraction counts, and outcomes; this public document intentionally omits source URLs and document IDs.

This result establishes only that the sampled links were anonymously downloadable and text-extractable at the time of the check. It does not establish access for all 26,422 workbook links, validate document quality or provenance, establish permissions for research use, or make the contents relevant evidence. It does not supply independent annotations or dataset approval. Do not start bulk retrieval or A0 based on this sample alone; any later import must retain authorized source provenance and follow institutional privacy, licensing, and review requirements.

## WURI 2026 stratified abstract pilot

A bounded operational pilot selected five distinct records from each of the workbook's 24 categories (120 program records total). Selection was outcome-blind and reproducible: within each category, records were ranked by the SHA-256 digest of the workbook SHA-256, a NUL separator, the category code, another NUL separator, and the stable WURI record ID; the five lowest digests were selected. No titles, document contents, relevance judgments, or labels influenced selection. This pilot is for access and data-quality assessment only and is not a statistically representative evaluation sample.

Only each selected record's Abstract link was requested; Template links were excluded from the candidate evidence corpus and were not part of this 120-document batch. Requests were unauthenticated, had proxy use disabled, followed HTTPS redirects only to allowlisted Google document-delivery hosts, used a 20-second timeout and an 8 MiB per-response cap, and ran with at most four concurrent requests. PDF, DOCX, or plain-text source bytes were verified before extraction with the existing document processor. Source files were processed in memory and not retained.

All 120 Abstract requests returned PDF source bytes and yielded non-empty extracted text. Extracted lengths ranged from 489 to 3,212 characters (median 1,659). There were no inaccessible, malformed, unsupported, empty, or size-limited items, and no duplicate source-byte or extracted-text hashes in this sample. The operational short/long-text flags were set below 200 characters and above 100,000 characters; none were triggered. A clean extraction is not a quality or relevance determination.

The per-record outcomes and the 120-record candidate JSONL, including extracted text, hashes, source URLs, and workbook row/cell provenance, are retained only in the ignored private research-input folder. Every record remains unannotated and unapproved; all 120 require researcher review for source identity, content suitability, privacy, and relevance before use as study evidence. The pilot did not create labels, partitions, model predictions, or evaluation results.

The private `wuri2026-human-content-review.xlsx` workbook provides a source/content review worksheet with the extracted abstracts, source links and row/cell provenance, extraction hashes, and pending review fields. Reviewer decisions and comments are blank; source identity, text quality, research-use, licensing, privacy, adjudication, and final inclusion states are pending. One PDF-extracted NUL control character is represented as U+FFFD in the Excel display for XML compatibility; the worksheet records this substitution, and the extracted-text hash remains that of the original unsanitized text. The authoritative `UniversityRanking_V3.1.docx` was not found in the workspace or searched Documents folder, so no relevance rubric or annotation guidance has been inferred.

Before broader retention or research use, the researcher must confirm applicable source-use authorization, licensing/terms, privacy and personal-data handling, institutional requirements, and the appropriateness of the documents for the study. Abstracts and Templates must remain distinct; inspect Template content separately before considering any of it as evidence. The sample does not authorize bulk retrieval, establish accessibility or suitability for untested records, or satisfy independent relevance review, dataset approval, protocol approval, or baseline prerequisites. No A0-A4 experiment or readiness scoring was run.

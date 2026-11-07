# WURI backend

## Local setup

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set `WURI_ADMIN_USERNAME` and `WURI_ADMIN_PASSWORD` in the process environment before starting the server. Do not commit `.env` or real institutional documents.

The local backend uses SQLite and private storage directories configured by `WURI_DATABASE_PATH` and `WURI_STORAGE_PATH`. Authentication uses a signed, HTTP-only session cookie and `hashlib.scrypt` password hashes. Generate a long random `WURI_SESSION_SECRET`; do not use the example value outside local setup.

The upload endpoint validates and extracts PDF, DOCX, and TXT files, segments the extracted content, and attempts passage-level indicator retrieval using the configured pretrained Sentence-BERT model. Retrieval similarity is not model confidence or readiness. It intentionally does not return EQAM, AHP, TOPSIS, RRS, or ARRS scores.

## Permission matrix

| Role | View institution data | Upload/process documents | Manage users/frameworks |
|---|---:|---:|---:|
| Administrator | Yes | Yes | Yes, when implemented by a protected endpoint |
| Evaluator | Yes | Yes | No |
| Viewer | Yes | No | No |

Membership is checked on the backend. Client-supplied institution IDs, roles, and user IDs are never treated as authorization proof.

## Phase 3 scoring modules

The reusable modules under `app/` now provide independently tested:

- `eqam.py`: equal-weight AES calculation, checklist completeness, and validation-set threshold calibration. Confidence, reliability, and strength inputs must be supplied by an approved assessment workflow; unavailable dimensions are rejected.
- `ahp.py`: reciprocal pairwise-matrix validation, geometric-mean weights, CI, CR, and review status.
- `topsis.py`: fixed ideal/anti-ideal reference TOPSIS for an explicitly supplied criterion vector.
- `readiness.py`: complete-framework ARRS, Best-Fit, close-alternative, and proposed readiness categories.

These modules are not yet connected to the upload endpoint. Criterion-level aggregation from multiple passages, official framework-weight provenance, and the dissertation's blank/ambiguous equation blocks require confirmation before an end-to-end readiness assessment can be enabled.

The upload response also includes an explicit guarded assessment state. Extracted passages and retrieval matches do not enable final scoring: calibrated model confidence, threshold calibration, criterion aggregation policy, verified framework weights, accepted AHP/fixed-weight configuration, complete criterion vectors, and a scoring-method version are required.

## Research validation

The `/api/research/validation/status` endpoint and the frontend Research Validation view report the evidence, model, expert-reference, and methodology prerequisites for the A0-A4 study. Dataset files can be imported as CSV or JSONL through the authenticated multipart endpoint `POST /api/research/datasets/import`; the endpoint validates the entire file, retains the exact source bytes in private storage, records a SHA-256 and line-level validation report, and only creates a dataset when every row and source reference is valid. Retrieve the stored, institution-scoped report using `GET /api/research/imports/{import_id}`; the private raw file is never exposed by that route. The legacy JSON dataset endpoint remains available.

The import schema and example files are documented in [research-data-import.md](../docs/research-data-import.md). Imports begin with `submitted` annotations: `GET /api/research/datasets/{dataset_id}/annotations` returns the authorized review queue, and `POST /api/research/datasets/{dataset_id}/annotation-reviews` records independent confirmations/corrections or a third-person adjudication. A dataset cannot be approved until every example has two distinct independent reviewers and every disagreement is adjudicated. Imported labels and model predictions remain preserved separately from adjudicated consensus labels. Dataset versions are immutable.

The grouped split v3 keeps records from the same source document and explicitly supplied leakage group together; exact and highly similar text is also grouped before assignment. Actual group-constrained counts may differ from 70:15:15, and assignments/counts/proportions are persisted. Expert ratings also require independent review before they count as expert references. Threshold locking only reads predictions assigned to the validation partition and requires predictions for every validation example.

The authenticated experiment preflight/run/detail endpoints expose and persist the scope, protocol, model version/configuration and artifact digest, split manifest, metrics, predictions, and safe failures. A0 has a local-only Sentence-BERT held-out retrieval evaluator. Configure `WURI_BASELINE_MODEL_PATH`, `WURI_BASELINE_MODEL_VERSION`, and `WURI_RESEARCH_PROTOCOL_PATH` only after preparing the versioned local model artifact and obtaining an approved protocol manifest; no model is downloaded or substituted. Protocol preflight requires the model SHA-256 and `max_seq_length`, catalog digest, label mapping, K values, encoding parameters, and explicit approval of the implemented query/metric definitions. The inference executor receives only test example IDs, framework/indicator IDs, evidence text, and partition name—not labels, review fields, prior predictions, or label-derived preflight data—and compares its predictions against consensus labels only after inference. Protocol and artifact fingerprints are rechecked around execution; successful run metadata includes dependency versions and eligible query counts. A completed A0 retrieval run is explicitly a retrieval component evaluation, not a completed A0 readiness baseline. The full readiness run remains blocked until the approved AHP–TOPSIS/criterion-aggregation methodology is available. A1-A4 remain unimplemented, and no readiness, RRS, or ARRS output is generated. See [research-validation-status.md](../docs/research-validation-status.md) and verify the authoritative dissertation Chapter 3 before treating any result as a research finding.

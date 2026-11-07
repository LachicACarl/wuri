# WURI Assessment API Contract (Proposed — Not Implemented)

**Status:** DESIGN ONLY — NOT AN AUTHORIZATION TO IMPLEMENT OR RUN  
**Proposed future backend target:** `POST /api/upload` (not used by the current frontend)  
**Current repository finding:** No backend/API source directory is present in the clean-root branch tree. The previous frontend upload integration was removed. This document is a proposed future API contract only; it does not describe a current frontend expectation or prove an API exists.

## Request

- Method: `POST`
- Path: `/api/upload`
- Content type: `multipart/form-data`
- Required fields:
  - `file`: institutional document; supported types must be enforced server-side.
  - `document_type`: document classification selected by the user.

The server must enforce authentication, authorization, file-size limits, content-type/signature checks, malware scanning where approved, storage policy, and audit logging. Do not trust client-supplied filenames, MIME types, institution names, metadata, or scores.

## Success response

A future approved frontend/backend integration may adopt a structured assessment response with fields such as these:

```json
{
  "filename": "source-document.pdf",
  "school_name": "Institution name established from verified source metadata",
  "best_fit": "Framework result supported by approved scoring output",
  "arrs": 0,
  "scores": {
    "WURI": 0,
    "THE": 0,
    "QS": 0,
    "UI GreenMetric": 0
  },
  "strengths": ["Evidence-supported strength"],
  "weaknesses": ["Evidence-supported gap"],
  "evidence": [
    {
      "id": "EVIDENCE-ID",
      "passage": "Verbatim extracted passage from the source document",
      "framework": "WURI",
      "indicator": "Mapped indicator",
      "source": "source-document.pdf",
      "date": "YYYY-MM-DD",
      "page": 1,
      "section": "Source section heading",
      "split": "validation",
      "aes": 0,
      "accepted": false,
      "dimensions": {
        "Semantic Relevance": 0,
        "Model Confidence": 0,
        "Evidence Completeness": 0,
        "Source Reliability": 0,
        "Evidence Strength": 0
      }
    }
  ],
  "metadata": {
    "source": "source-document.pdf",
    "sourceType": "Strategic plan",
    "date": "YYYY-MM-DD",
    "extractionStatus": "Actual extraction state",
    "verificationStatus": "Actual verification state",
    "provenance": "Stable source record or provenance reference"
  }
}
```

The numeric zeroes above are schema placeholders, not sample institutional scores, defaults, or acceptable fallback output. A backend must never return placeholder values as an assessment.

## Contract gaps to resolve before implementation

The example above is intentionally illustrative and is not yet a complete production response schema. Before implementation, the API owner and research reviewer must decide and version at least:

- Stable `request_id` and `assessment_id` fields and their lifecycle/idempotency behavior.
- Explicit `status` and timestamps, including whether an accepted upload returns `202 Accepted` with a processing resource or waits for completion.
- `methodology_version`, `model_version`, `extractor_version`, and contract/schema version in the response envelope.
- A stable provenance reference for every evidence item, including source-document identifier and content hash; do not expose private storage object keys.
- A typed, machine-readable error envelope with a correlation/request identifier and documented retryability.
- Whether framework-specific scores may be absent independently, or whether the entire assessment must fail closed when any required framework is incomplete.

The numeric placeholders in the example must not be interpreted as required defaults. Replace them with an approved typed schema before implementation; never serialize fabricated zero scores as completed results.

## Required semantics

1. All scores must be produced by the approved and validated assessment pipeline. The API must not synthesize values from filenames, file sizes, timestamps, hardcoded passages, or deterministic placeholder functions.
2. Evidence passages must originate from the uploaded document. Each item must retain accurate page/section and source provenance.
3. EQAM dimensions and AES must follow the approved methodology version. Do not invent confidence or source-reliability values.
4. Framework scores and ARRS must follow approved criteria, weights, anchors, and data partitions. The API must identify the methodology/model version in the eventual production contract.
5. If extraction, provenance, mapping, or scoring is incomplete, return an explicit non-success response and no completed score object. If the approved workflow is asynchronous, return only a processing resource with no scores until the assessment reaches a valid completed state.
6. Client-side validation is a display safeguard only. The server is authoritative and must validate data, permissions, research gate, and provenance.

## Error behavior

Use appropriate non-success HTTP responses for authentication failure, authorization failure, unsupported/invalid files, extraction failure, unprocessable evidence, missing approvals, and internal errors. Do not include secrets, stack traces, private file contents, or credential values in error bodies.

## Security and research gates

This contract does not authorize implementation, dependency installation, backend startup, API calls, Supabase access, synthetic-data testing, institutional-data processing, research scoring, or deployment.

Before implementation, obtain:
- written security clearance for an exact reviewed repository commit;
- confirmation from the authorized Supabase owner regarding revocation of the exposed credential, where applicable;
- separate written implementation and isolated-test authorization;
- researcher approval of methodology, corpus, and validation prerequisites before research scoring.

## Change control

Any schema change must be reviewed against:
- the dissertation methodology and approved data dictionary;
- an approved future frontend response validator (none exists in the current security-hold UI);
- authentication and authorization design;
- evidence provenance and audit requirements;
- versioning and backward-compatibility rules.

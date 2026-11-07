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

## Illustrative asynchronous acceptance response (proposed)

The preferred draft lifecycle is asynchronous because extraction and assessment may take longer than a normal request. This is an example only; the exact status code, resource path, and fields require owner approval before implementation. An accepted request has **not** completed an assessment and must not contain scores or evidence claims:

```json
{
  "request_id": "opaque-request-id",
  "assessment_id": "opaque-assessment-id",
  "status": "queued",
  "status_url": "/api/assessments/opaque-assessment-id",
  "created_at": "RFC-3339 timestamp",
  "contract_version": "approved-contract-version"
}
```

The acceptance example intentionally contains no scores, evidence passages, or institution claims. A completed-result schema, if approved, must be specified separately and may only be returned after a valid assessment reaches its approved terminal success state.

## Contract gaps to resolve before implementation

The example above is intentionally illustrative and is not yet a complete production response schema. Before implementation, the API owner and research reviewer must decide and version at least:

- Stable `request_id` and `assessment_id` fields, their lifecycle, and an idempotency-key policy. Define whether IDs are created before or after durable queue acceptance.
- Explicit processing statuses and timestamps. The current proposal prefers `202 Accepted` with a processing resource, but the final state names, polling/notification mechanism, retention, and timeout behavior remain approval decisions.
- `methodology_version`, `model_version`, `extractor_version`, and contract/schema version in the response envelope.
- A stable provenance reference for every evidence item, including source-document identifier and content hash; do not expose private storage object keys. Distinguish a public opaque evidence ID from a private storage object key.
- A typed, machine-readable error envelope with a correlation/request identifier and documented retryability.
- Whether framework-specific scores may be absent independently, or whether the entire assessment must fail closed when any required framework is incomplete.
- A separate completed-result schema, including score units/ranges, missing-value representation, explanation references, and partial-framework policy.

The numeric placeholders in the example must not be interpreted as required defaults. Replace them with an approved typed schema before implementation; never serialize fabricated zero scores as completed results.

## Proposed lifecycle (to be finalized)

The draft asynchronous flow is: validate and authorize the request; durably accept it with an opaque request/assessment ID; return a processing resource without scores; transition through approved processing states; publish a completed result only after all required evidence/provenance/methodology checks pass; otherwise move to a terminal failure state with a safe error code. Polling, callbacks, cancellation, retry, and state naming remain unresolved until the API and operations owners approve them.

HTTP behavior must be finalized with the API owner. A possible pattern is `202 Accepted` for durable queue acceptance, `200 OK` for retrieval of an existing processing/completed resource, `401/403` for identity/access failures, `409 Conflict` for idempotency-key reuse with a different request fingerprint, `413` for oversized input, `415` for unsupported media, `422` for semantically invalid content, and safe `5xx` errors for service failures. These are proposals, not implemented behavior or final commitments.

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

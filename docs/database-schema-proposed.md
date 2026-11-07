# WURI DSS Database Design (Proposed — Not Implemented)

**Status:** DESIGN ONLY — SECURITY HOLD / NO-GO  
**Target:** PostgreSQL-compatible relational store  
**Purpose:** Reviewable logical data model for future backend planning. This is not a migration, SQL execution script, or authorization to connect to Supabase.

## 1. Design principles

- The server is the only trusted writer for users, documents, evidence, assessments, scores, and audit events.
- Browser clients never receive database service-role credentials or direct write privileges.
- Every institutional record is tenant-scoped by an institution identifier. Every protected query must enforce the authenticated user's institution and role on the server.
- Uploaded binaries belong in private object storage, not in ordinary relational rows. The database stores opaque object keys and integrity metadata only.
- Preserve immutable provenance: source document hash, extraction version, methodology version, model version, and assessment run identity.
- Do not store a score unless the complete approved pipeline produced it. Failed or partial runs have status and error codes, not fabricated zero scores.
- Retention, deletion, legal hold, and research consent rules must be approved before implementation.

## 2. Logical entities

| Entity | Purpose | Important fields / constraints |
|---|---|---|
| institutions | Tenant boundary | id, display_name, status, created_at |
| users | Server-managed identity profile | id from approved identity provider, email, status, created_at |
| institution_memberships | User-to-institution role | user_id, institution_id, role; unique(user_id, institution_id); role in administrator/evaluator/viewer |
| documents | Uploaded document metadata | id, institution_id, uploader_id, document_type, original_filename, storage_key, sha256, byte_size, detected_media_type, status, created_at |
| extraction_runs | Extraction attempt and provenance | id, document_id, tool_name, tool_version, status, started_at, completed_at, failure_code |
| evidence_items | Source-grounded extracted passage | id, extraction_run_id, institution_id, passage_text, page_number, section_label, character_start, character_end, source_hash |
| evidence_mappings | Evidence-to-framework indicator mapping | id, evidence_id, framework_code, indicator_code, mapping_model_version, relevance_value, review_status, reviewer_id |
| assessment_runs | One versioned assessment execution | id, institution_id, document_id, requested_by, status, methodology_version, model_version, started_at, completed_at, failure_code |
| evidence_quality | EQAM values for a specific run/evidence pair | assessment_run_id, evidence_id, semantic_relevance, model_confidence, completeness, source_reliability, evidence_strength, aes, accepted |
| framework_scores | Per-framework output | assessment_run_id, framework_code, rrs, calculation_version; unique(assessment_run_id, framework_code) |
| aggregate_scores | Aggregate and best-fit output | assessment_run_id, arrs, best_fit_code, aggregation_version |
| assessment_explanations | Evidence-supported strengths, gaps, and explanation references | id, assessment_run_id, category, explanation_text, evidence references |
| audit_events | Security and governance trail | id, actor_id, institution_id, action, target_type, target_id, request_id, occurred_at, redacted_metadata |

This is a logical model. Column types, indexes, foreign-key delete behavior, encryption, partitioning, and row-level security policies require review before a physical schema is approved.

## 3. Relationship outline

- One institution has many memberships, documents, and assessment runs.
- One user has memberships in one or more institutions, each with one role per institution.
- One document has many extraction runs; one extraction run has many evidence items.
- Evidence items may have multiple indicator mappings.
- One assessment run references one institution and one source document, and has many evidence-quality rows and framework scores.
- One completed assessment run has one aggregate result and zero or more explanation records.
- Audit events reference actors and affected resources where available; audit retention is separately governed.

## 4. Required integrity rules

1. Foreign keys must prevent evidence or assessment records from silently becoming detached from their source document and institution.
2. Unique constraints must prevent duplicate membership roles and duplicate framework score rows for the same assessment run.
3. Scores must be constrained to approved numeric ranges; a database range check does not prove methodological validity.
4. Evidence page numbers must be positive when known. Unknown page/section values must be represented explicitly, never guessed.
5. Assessment status transitions must be controlled by the backend. A completed state requires all required calculation artifacts and provenance.
6. The API must not expose storage keys, private passage text, or assessment data unless the caller is authorized for that institution and resource.
7. Audit metadata must be redacted; do not record passwords, session tokens, API keys, or raw secrets.

## 5. Access-control matrix (server enforced)

| Resource/action | Administrator | Evaluator | Viewer |
|---|---:|---:|---:|
| Manage institution memberships | Yes, within assigned institution | No | No |
| Upload documents | Yes | Yes | No |
| View documents/evidence | Yes | Yes | Approved read-only scope |
| Verify evidence mappings | Yes | Yes | No |
| Run approved assessments | Yes | Yes, if research authorization permits | No |
| View approved assessment reports | Yes | Yes | Yes |
| Change methodology/model configuration | Restricted governance approval | No | No |
| Read audit trail | Authorized scope only | No | No |

A UI role check is not authorization. Every API action must independently check the authenticated principal, membership, role, institution scope, and applicable research/operational approval.

## 6. Data lifecycle and storage

1. Receive upload only after authentication and authorization.
2. Validate size, extension, MIME, and file signature; generate an opaque object key.
3. Quarantine/scan according to the approved security policy before extraction.
4. Store the object privately; record hash, size, detected media type, uploader, institution, and timestamps.
5. Create extraction and assessment records with explicit status transitions.
6. Preserve source-to-passage traceability and calculation versions.
7. Apply approved retention, export, deletion, backup, and restore procedures.

No public bucket, client-side service-role key, user-controlled storage path, or unrestricted signed URL is acceptable.

## 7. Unresolved decisions before physical schema

- Authoritative identity provider and user identifier format.
- Tenant model and whether a user may belong to multiple institutions.
- Institution verification and ownership of uploaded records.
- Approved object-storage provider, encryption, malware scanning, and retention.
- Research consent, privacy classification, data residency, and deletion requirements.
- Final methodology/data dictionary for framework indicators and EQAM dimensions.
- Audit retention, backup/restore objectives, and operational ownership.
- Whether database row-level security is required in addition to server-side authorization, and how policies will be independently reviewed.

## 8. Approval gates

Before turning this design into migrations or code, require:
- independent security clearance for the exact repository revision;
- confirmation that exposed credentials have been contained by the authorized provider owner;
- written implementation authorization naming the isolated branch and allowed scope;
- separate authorization for dependency installation and isolated tests;
- data-owner/researcher approval for the data model and processing purpose;
- database-owner approval for project, schema, backup, and access changes.

**No database has been created or modified by this document. No Supabase connection, SQL execution, migration, or data access is authorized.**

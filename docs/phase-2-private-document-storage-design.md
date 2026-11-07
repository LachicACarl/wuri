# Phase 2 — Private Document Storage Design

Status: design only; no files were uploaded, read from application storage, or migrated. Security status remains **NO-GO** for runtime work.

## Existing implementation

- [storage.py](/C:/Users/lance/Documents/wuri/backend/app/storage.py:7) implements `PrivateStorage` with a local root from `WURI_STORAGE_PATH` or `backend/private`. It writes bytes to a UUID-based filename plus extension, returns a SHA-256 digest, reads files by key, and rejects resolved paths whose parent is not the storage root.
- [main.py](/C:/Users/lance/Documents/wuri/backend/app/main.py:422) authenticates the caller, selects an authorized institution, accepts PDF/DOCX/TXT within a 25 MB limit, checks content, saves locally, malware-scans, extracts/segments, then persists metadata and evidence rows.
- Document metadata includes institution, assessment, filename/type/size/checksum, storage key, extraction and malware-scan state, provenance/authorization fields, and optional framework mapping. The migration-defined `documents.storage_key` is unique.
- Download at [main.py](/C:/Users/lance/Documents/wuri/backend/app/main.py:574) checks active membership for the document's institution, reads the local file, and records a download audit event. It returns the bytes through FastAPI; it does not expose a public URL.
- Delete at [main.py](/C:/Users/lance/Documents/wuri/backend/app/main.py:649) uses `Database.delete_document` to authorize an administrator, remove evidence references, delete the document row, and write an audit event; after that DB transaction commits, the route deletes the file. If file deletion fails, the API reports failure but the metadata row has already been deleted, leaving an orphaned file that requires reconciliation.
- Research import files are also stored locally at [main.py](/C:/Users/lance/Documents/wuri/backend/app/main.py:904). Metadata stores the object key, SHA-256, byte count, filename and processing status. No research-import file download/delete route was found in the inspected route inventory; confirm intended retention and disposal rules before migrating that class of object.

## Target adapter design

Keep storage separate from database migration. Preserve a narrow storage interface (`save`, `read` or streaming `open`, `delete`) behind a configurable provider. The application should continue authorizing through its authenticated user and institution membership before every operation. The object store must not be the source of authorization decisions.

Recommended initial behavior:

1. Use a private bucket/container with public access disabled. Do not put object-store credentials or privileged API keys in React or `VITE_*` variables.
2. Generate opaque object keys server-side; do not use supplied filenames as keys. Include an institution namespace only if access checks do not depend on trusting that key. Keep the original sanitized filename only as database metadata.
3. Keep the current type, size, content validation and malware scan gates. Store checksum, size, content type, object key, scan status/time/tool, and provenance in the relational metadata. Verify the checksum after upload and during any migration copy.
4. Initially proxy downloads through FastAPI so existing `current_user`, membership, approval/provenance rules and download audit event remain in force. A later short-lived signed URL design would require authorization before issuing it, a strict expiry, no public bucket, and audit semantics that record URL issuance and/or actual download as appropriate.
5. Treat upload as a recoverable two-system operation. Persist a pending object/metadata state or durable operation record, upload to a temporary/quarantine key, verify it, scan it, then mark the DB record ready. On DB failure, enqueue or attempt idempotent object cleanup; on object failure, keep the record non-ready and retry safely. Do not assume a DB transaction spans PostgreSQL and object storage.
6. Make deletes idempotent and auditable. Prefer a tombstone/pending-delete state, object delete with retry, then finalize metadata removal (or retain a tombstone under retention policy). Add a reconciliation job for objects without rows and rows without objects. The current route deletes the row before the file, which can orphan an object if storage deletion fails.
7. Separate buckets/prefixes or retention classes for institutional evidence and research-import artifacts. Set explicit retention, backup, versioning and deletion policies with the data owner. Database backups alone do not back up object bytes.

## Tenant isolation and RLS boundary

Current code checks active user/institution membership in FastAPI before document access; document deletion additionally requires administrator role and blocks deletion when approved research examples reference the source. Preserve those checks and test them with multiple synthetic institutions.

If using a managed object store, determine its policy model and credential scope before implementation. A privileged service-role credential must not be exposed to browsers; do not assume database row policies replace FastAPI authorization for object access. Prefer a backend-only identity with the narrowest available scope, verify application authorization before each object operation, and use a private bucket/container. The exact Supabase Storage policy and key behavior remains to be confirmed against approved project configuration before implementation.

Do not introduce a browser-side Supabase client for private institutional objects unless a separate identity and policy design is approved. WURI's custom HMAC session cookie is not automatically a Supabase Auth JWT and does not automatically satisfy Supabase policies.

## Migration procedure (future, after clearance)

- Inventory local storage keys from an authorized metadata export without printing document names or contents into logs.
- Freeze writes and create an approved source backup. Copy to a private development bucket first, using an explicit mapping from old storage key to new key.
- Stream files, verify size and SHA-256, scan under the approved scanner process, and record success/failure per object. Never use public URLs or browser upload credentials for the migration.
- Keep source files unchanged until object/database reconciliation and owner sign-off. Reconcile metadata count, missing objects, extra objects, checksums, object size, permissions, provenance, and audit records.
- On partial failure, retain source and retry idempotently. Do not delete source objects until a separate retention/deletion approval and restore test.

## Required post-clearance checks

Using synthetic/authorized non-sensitive files only: authorized upload and download, rejected type/size, cross-institution denial, non-admin delete denial, approved-research-reference delete denial, scanner unavailable/infected cases, checksum mismatch, object-store outage, database outage during upload, object deletion retry, orphan reconciliation, and backup/restore. These checks are not authorized now.

No object-storage adapter, bucket, policy, migration or test has been created or run for this design.

ALTER TABLE documents ADD COLUMN title TEXT;
ALTER TABLE documents ADD COLUMN source_reference TEXT;
ALTER TABLE documents ADD COLUMN collection_date TEXT;
ALTER TABLE documents ADD COLUMN reporting_period TEXT;
ALTER TABLE documents ADD COLUMN provenance TEXT;
ALTER TABLE documents ADD COLUMN authorization_status TEXT NOT NULL DEFAULT 'unknown'
    CHECK (authorization_status IN ('verified', 'pending', 'unavailable', 'unknown'));
ALTER TABLE documents ADD COLUMN research_permission_status TEXT NOT NULL DEFAULT 'unknown'
    CHECK (research_permission_status IN ('verified', 'pending', 'unavailable', 'unknown'));
ALTER TABLE documents ADD COLUMN review_status TEXT NOT NULL DEFAULT 'uploaded'
    CHECK (review_status IN ('uploaded', 'processing_failed', 'pending_review', 'verified', 'rejected'));
ALTER TABLE documents ADD COLUMN limitations TEXT;

CREATE TABLE IF NOT EXISTS document_framework_mappings (
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    framework_id TEXT NOT NULL,
    framework_edition TEXT NOT NULL,
    criterion_id TEXT NOT NULL,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, framework_id, framework_edition, criterion_id)
);

CREATE INDEX IF NOT EXISTS ix_document_framework_mappings_institution
    ON document_framework_mappings(institution_id, framework_id, framework_edition, criterion_id);

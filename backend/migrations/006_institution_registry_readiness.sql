ALTER TABLE institutions ADD COLUMN display_name TEXT;
ALTER TABLE institutions ADD COLUMN country TEXT NOT NULL DEFAULT 'Philippines';
ALTER TABLE institutions ADD COLUMN region TEXT;
ALTER TABLE institutions ADD COLUMN institution_type TEXT;
ALTER TABLE institutions ADD COLUMN campus_name TEXT;
ALTER TABLE institutions ADD COLUMN parent_institution_id TEXT REFERENCES institutions(id);
ALTER TABLE institutions ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'inactive'));
ALTER TABLE institutions ADD COLUMN provenance TEXT;

CREATE TABLE IF NOT EXISTS evidence_readiness (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    framework_id TEXT NOT NULL,
    framework_edition TEXT NOT NULL,
    criterion_id TEXT NOT NULL,
    eligibility_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (eligibility_status IN ('verified', 'not_eligible', 'unknown')),
    authorization_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (authorization_status IN ('verified', 'not_authorized', 'unknown')),
    provenance_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (provenance_status IN ('verified', 'incomplete', 'unknown')),
    evidence_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (evidence_status IN ('available', 'missing', 'incomplete', 'unknown')),
    privacy_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (privacy_status IN ('reviewed', 'issues_found', 'unknown')),
    expert_review_status TEXT NOT NULL DEFAULT 'not_required'
        CHECK (expert_review_status IN ('not_required', 'pending', 'complete', 'unknown')),
    evidence_title TEXT,
    evidence_type TEXT,
    source_reference TEXT,
    source_date TEXT,
    collection_date TEXT,
    description TEXT,
    limitations TEXT,
    reviewer_id TEXT REFERENCES users(id),
    reviewed_at TEXT,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (institution_id, framework_id, framework_edition, criterion_id)
);

CREATE INDEX IF NOT EXISTS ix_evidence_readiness_institution_framework
    ON evidence_readiness(institution_id, framework_id, framework_edition);

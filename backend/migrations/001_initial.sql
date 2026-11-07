CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS institution_memberships (
    user_id TEXT NOT NULL REFERENCES users(id),
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    role TEXT NOT NULL CHECK (role IN ('administrator', 'evaluator', 'viewer')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, institution_id)
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    created_by TEXT NOT NULL REFERENCES users(id),
    status TEXT NOT NULL,
    failure_reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    assessment_id TEXT NOT NULL REFERENCES assessments(id),
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    extraction_status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_passages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    assessment_id TEXT NOT NULL REFERENCES assessments(id),
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    passage_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    start_offset INTEGER,
    end_offset INTEGER,
    extraction_method TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (document_id, passage_index)
);

CREATE TABLE IF NOT EXISTS indicator_matches (
    id TEXT PRIMARY KEY,
    passage_id TEXT NOT NULL REFERENCES evidence_passages(id),
    framework TEXT NOT NULL,
    indicator TEXT NOT NULL,
    similarity REAL NOT NULL,
    retrieval_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    assessment_id TEXT REFERENCES assessments(id),
    user_id TEXT REFERENCES users(id),
    event_type TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

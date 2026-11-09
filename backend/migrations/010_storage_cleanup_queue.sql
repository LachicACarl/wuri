CREATE TABLE IF NOT EXISTS storage_cleanup_queue (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    document_id TEXT NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    claimed_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS ix_storage_cleanup_queue_pending
    ON storage_cleanup_queue(status, created_at);

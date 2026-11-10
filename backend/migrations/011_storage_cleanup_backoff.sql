-- Rebuild the cleanup queue to add a terminal failed status while retaining
-- every existing item, lease and audit-relevant value. SQLite cannot alter a
-- CHECK constraint in place.
CREATE TABLE storage_cleanup_queue_v2 (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    document_id TEXT NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    claimed_at TEXT,
    completed_at TEXT,
    next_attempt_at TEXT,
    last_error_at TEXT,
    failed_at TEXT
);

INSERT INTO storage_cleanup_queue_v2 (
    id, institution_id, document_id, storage_key, reason, status, attempts,
    created_at, updated_at, claimed_at, completed_at,
    next_attempt_at, last_error_at, failed_at
)
SELECT
    id, institution_id, document_id, storage_key, reason, status, attempts,
    created_at, updated_at, claimed_at, completed_at,
    next_attempt_at, last_error_at, failed_at
FROM storage_cleanup_queue;

DROP TABLE storage_cleanup_queue;
ALTER TABLE storage_cleanup_queue_v2 RENAME TO storage_cleanup_queue;

CREATE INDEX IF NOT EXISTS ix_storage_cleanup_queue_pending
    ON storage_cleanup_queue(status, created_at);
CREATE INDEX IF NOT EXISTS ix_storage_cleanup_queue_due
    ON storage_cleanup_queue(status, next_attempt_at, created_at);

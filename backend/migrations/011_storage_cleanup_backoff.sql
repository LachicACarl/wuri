-- Add bounded retry scheduling and terminal failure state without rebuilding
-- the queue table. Existing pending/processing/completed rows remain valid.
ALTER TABLE storage_cleanup_queue
    ADD COLUMN next_attempt_at TEXT;

ALTER TABLE storage_cleanup_queue
    ADD COLUMN last_error_at TEXT;

ALTER TABLE storage_cleanup_queue
    ADD COLUMN failed_at TEXT;

CREATE INDEX IF NOT EXISTS ix_storage_cleanup_queue_due
    ON storage_cleanup_queue(status, next_attempt_at, created_at);

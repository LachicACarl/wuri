-- Fence stale workers after a cleanup claim expires and is reassigned.
ALTER TABLE storage_cleanup_queue ADD COLUMN claim_token TEXT;

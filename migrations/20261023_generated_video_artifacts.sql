-- Apply explicitly to the configured PostgreSQL database before enabling /generate.
-- Safe to rerun. Legacy metadata-only rows are deliberately not backfilled as verified assets.
BEGIN;

CREATE TABLE IF NOT EXISTS generated_video_artifacts (
    artifact_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    story_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    artifact_url TEXT NOT NULL,
    duration_sec INTEGER,
    evidence_status TEXT NOT NULL,
    storage_provider TEXT NOT NULL,
    storage_public_id TEXT NOT NULL,
    storage_asset_id TEXT NOT NULL,
    storage_bytes BIGINT NOT NULL CHECK (storage_bytes > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Upgrade an existing metadata-only table without pretending legacy rows have storage proof.
ALTER TABLE generated_video_artifacts
    ADD COLUMN IF NOT EXISTS storage_provider TEXT;
ALTER TABLE generated_video_artifacts
    ADD COLUMN IF NOT EXISTS storage_public_id TEXT;
ALTER TABLE generated_video_artifacts
    ADD COLUMN IF NOT EXISTS storage_asset_id TEXT;
ALTER TABLE generated_video_artifacts
    ADD COLUMN IF NOT EXISTS storage_bytes BIGINT;

COMMIT;

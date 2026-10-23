"""Durable metadata storage for copied provider-generated video artifacts."""
import os
import uuid
from typing import Optional

import psycopg
from psycopg.rows import dict_row


def persist_generated_artifact(
    *,
    video_id: str,
    story_id: str,
    provider: str,
    artifact_url: str,
    duration_sec: Optional[int],
    evidence_status: str,
    storage_provider: str,
    storage_public_id: str,
    storage_asset_id: str,
    storage_bytes: int,
) -> dict:
    """Insert storage evidence and verify the committed row can be read back."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for durable generated-artifact storage")
    if evidence_status != "OBSERVED":
        raise RuntimeError("Only observed provider artifacts may be persisted as generated")
    if storage_provider != "cloudinary" or not storage_public_id or not storage_asset_id or storage_bytes <= 0:
        raise RuntimeError("A verified durable Cloudinary video asset is required")

    artifact_id = f"artifact_{uuid.uuid4().hex}"
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS generated_video_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    story_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    artifact_url TEXT NOT NULL,
                    duration_sec INTEGER,
                    evidence_status TEXT NOT NULL,
                    storage_provider TEXT NOT NULL DEFAULT 'cloudinary',
                    storage_public_id TEXT NOT NULL,
                    storage_asset_id TEXT NOT NULL,
                    storage_bytes BIGINT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Safe additive migration for deployments where PR #20's metadata-only
            # table may already exist from a previous generation request.
            cur.execute("ALTER TABLE generated_video_artifacts ADD COLUMN IF NOT EXISTS storage_provider TEXT NOT NULL DEFAULT 'cloudinary'")
            cur.execute("ALTER TABLE generated_video_artifacts ADD COLUMN IF NOT EXISTS storage_public_id TEXT")
            cur.execute("ALTER TABLE generated_video_artifacts ADD COLUMN IF NOT EXISTS storage_asset_id TEXT")
            cur.execute("ALTER TABLE generated_video_artifacts ADD COLUMN IF NOT EXISTS storage_bytes BIGINT")
            cur.execute(
                """
                INSERT INTO generated_video_artifacts
                    (artifact_id, video_id, story_id, provider, artifact_url, duration_sec,
                     evidence_status, storage_provider, storage_public_id, storage_asset_id, storage_bytes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (artifact_id, video_id, story_id, provider, artifact_url, duration_sec,
                 evidence_status, storage_provider, storage_public_id, storage_asset_id, storage_bytes),
            )
            cur.execute(
                """
                SELECT artifact_id, video_id, story_id, provider, artifact_url, duration_sec,
                       evidence_status, storage_provider, storage_public_id, storage_asset_id, storage_bytes
                FROM generated_video_artifacts WHERE artifact_id = %s
                """,
                (artifact_id,),
            )
            row = cur.fetchone()
            if not row or (
                row["artifact_url"] != artifact_url
                or row["video_id"] != video_id
                or row["storage_asset_id"] != storage_asset_id
                or row["storage_bytes"] != storage_bytes
                or row["evidence_status"] != evidence_status
            ):
                raise RuntimeError("Generated artifact persistence readback did not match")
    return {"artifact_id": artifact_id, "readback_verified": True, "artifact": dict(row)}

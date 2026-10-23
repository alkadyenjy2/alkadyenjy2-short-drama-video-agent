"""Durable metadata storage for provider-generated video artifacts."""
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
) -> dict:
    """Insert provider evidence and verify the committed row can be read back."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for durable generated-artifact storage")
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
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                INSERT INTO generated_video_artifacts
                    (artifact_id, video_id, story_id, provider, artifact_url, duration_sec, evidence_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (artifact_id, video_id, story_id, provider, artifact_url, duration_sec, evidence_status),
            )
            cur.execute(
                """
                SELECT artifact_id, video_id, story_id, provider, artifact_url, duration_sec, evidence_status
                FROM generated_video_artifacts WHERE artifact_id = %s
                """,
                (artifact_id,),
            )
            row = cur.fetchone()
            if not row or row["artifact_url"] != artifact_url or row["video_id"] != video_id:
                raise RuntimeError("Generated artifact persistence readback did not match")
    return {"artifact_id": artifact_id, "readback_verified": True, "artifact": dict(row)}

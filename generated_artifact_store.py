"""Durable metadata storage for copied provider-generated video artifacts.

Schema changes are managed by explicit SQL migrations, never by request handlers.
"""
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
    """Insert artifact evidence and verify the committed row can be read back."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for durable generated-artifact storage")
    if evidence_status != "OBSERVED":
        raise RuntimeError("Only observed provider artifacts may be persisted as generated")
    if (
        storage_provider != "cloudinary"
        or not storage_public_id
        or not storage_asset_id
        or isinstance(storage_bytes, bool)
        or not isinstance(storage_bytes, int)
        or storage_bytes <= 0
    ):
        raise RuntimeError("A verified durable Cloudinary video asset is required")
    if not video_id or not story_id or not provider or not artifact_url:
        raise RuntimeError("Video, story, provider, and artifact identifiers are required")

    artifact_id = f"artifact_{uuid.uuid4().hex}"
    # Intentionally no CREATE/ALTER here: deploy migrations separately before
    # enabling generation. Missing/outdated schema must fail closed.
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO generated_video_artifacts
                    (artifact_id, video_id, story_id, provider, artifact_url, duration_sec,
                     evidence_status, storage_provider, storage_public_id, storage_asset_id, storage_bytes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    artifact_id, video_id, story_id, provider, artifact_url, duration_sec,
                    evidence_status, storage_provider, storage_public_id, storage_asset_id, storage_bytes,
                ),
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
                or row["story_id"] != story_id
                or row["storage_provider"] != storage_provider
                or row["storage_public_id"] != storage_public_id
                or row["storage_asset_id"] != storage_asset_id
                or row["storage_bytes"] != storage_bytes
                or row["evidence_status"] != evidence_status
            ):
                raise RuntimeError("Generated artifact persistence readback did not match")
    return {"artifact_id": artifact_id, "readback_verified": True, "artifact": dict(row)}


def get_generated_artifact(artifact_id: str) -> Optional[dict]:
    """Read one durable artifact record without initializing or mutating schema."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to read generated-artifact metadata")
    if not isinstance(artifact_id, str) or not artifact_id.startswith("artifact_") or len(artifact_id) > 128:
        raise ValueError("A valid artifact ID is required")

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT artifact_id, video_id, story_id, provider, artifact_url,
                       duration_sec, evidence_status, storage_provider,
                       storage_public_id, storage_asset_id, storage_bytes, created_at
                FROM generated_video_artifacts
                WHERE artifact_id = %s
                """,
                (artifact_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None

"""Approval-gated YouTube release orchestration for the existing Short Drama pipeline.

This module is intentionally orchestration-only. It reuses publisher.YouTubePublisher and
never treats code presence, HTTP 200, or a workflow run as publication evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from publisher import PublicationState, YouTubePublisher

MAX_EPISODES = 10
STAGES = ("SCRIPT", "ASSETS", "RENDER", "MP4_EVIDENCE", "METADATA", "APPROVAL", "PUBLISH_EVIDENCE")


def episode_id(n: int) -> str:
    if not 1 <= n <= MAX_EPISODES:
        raise ValueError(f"episode number must be 1..{MAX_EPISODES}")
    return f"EP{n:02d}"


def verify_mp4(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file() or p.stat().st_size <= 0:
        return {"status": "NOT_VERIFIED", "reason": "real MP4 file missing or empty"}
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"status": "GENERATED", "bytes": p.stat().st_size, "sha256": digest, "path": str(p)}


def build_release_record(n: int, script: dict, assets: dict, render: dict, metadata: dict) -> dict[str, Any]:
    eid = episode_id(n)
    mp4 = verify_mp4(str(render.get("mp4_path", "")))
    stages = {
        "SCRIPT": "READY" if script.get("ready") else "BLOCKED",
        "ASSETS": "READY" if assets.get("ready") else "BLOCKED",
        "RENDER": "GENERATED" if render.get("mp4_path") else "BLOCKED",
        "MP4_EVIDENCE": mp4["status"],
        "METADATA": "READY" if metadata.get("ready") else "BLOCKED",
        "APPROVAL": "BLOCKED",
        "PUBLISH_EVIDENCE": "BLOCKED",
    }
    return {
        "episode": eid,
        "stages": stages,
        "publish_allowed": False,
        "reason": "Explicit approval record is required before any publish call.",
        "mp4_evidence": mp4,
    }


def load_approval(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {"approved": False, "reason": "approval record missing"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"approved": False, "reason": "approval record invalid JSON"}
    if data.get("approved") is not True or not data.get("approved_by") or not data.get("approved_at"):
        return {"approved": False, "reason": "approval must contain approved=true, approved_by, approved_at"}
    return data


def publish_if_approved(n: int, video_path: str, title: str, description: str, tags: list[str], approval_path: str) -> dict[str, Any]:
    approval = load_approval(approval_path)
    if not approval.get("approved"):
        return {"status": "BLOCKED", "stage": "APPROVAL", "reason": approval.get("reason")}

    if n > MAX_EPISODES:
        return {"status": "BLOCKED", "stage": "APPROVAL", "reason": "10-episode release cap exceeded"}

    if not os.getenv("YOUTUBE_CLIENT_ID") or not os.getenv("YOUTUBE_CLIENT_SECRET"):
        return {"status": "BLOCKED", "stage": "PUBLISH_EVIDENCE", "reason": "real YouTube OAuth client credentials unavailable"}

    if not os.getenv("YOUTUBE_REFRESH_TOKEN") and not os.getenv("YOUTUBE_ACCESS_TOKEN"):
        return {"status": "BLOCKED", "stage": "PUBLISH_EVIDENCE", "reason": "real YouTube OAuth token unavailable"}

    result = YouTubePublisher().publish(
        video_path, title, description, tags, f"youtube_{episode_id(n)}",
        privacy_status=os.getenv("YOUTUBE_PRIVACY_STATUS", "private"),
    )
    if result.get("state") != PublicationState.PUBLISHED or not result.get("receipt"):
        return {"status": "BLOCKED", "stage": "PUBLISH_EVIDENCE", "publisher_result": result}
    return {
        "status": "PUBLISHED",
        "stage": "PUBLISH_EVIDENCE",
        "receipt": result["receipt"],
        "evidence_record": result.get("evidence_record"),
    }

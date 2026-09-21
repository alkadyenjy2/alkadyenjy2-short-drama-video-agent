"""Normalized inbox for user-supplied URLs and ideas.
It stores provenance metadata only; fetching/transcription is performed by a connected source adapter.
"""
import hashlib
from datetime import datetime, timezone
from typing import Dict
from rights_engine import validate_source_url

def create_idea_item(kind: str, content: str, user_id: str = "system", source_url: str = "") -> Dict:
    kind = (kind or "idea").lower().strip()
    if kind == "url" and not validate_source_url(content):
        raise ValueError("invalid source URL")
    now = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256((kind + "|" + content).encode()).hexdigest()[:16]
    return {"idea_id": "idea_" + digest, "kind": kind, "content": content, "source_url": source_url or (content if kind == "url" else ""),
            "user_id": str(user_id), "created_at": now, "status": "RECEIVED", "provenance_status": "PENDING_ANALYSIS"}

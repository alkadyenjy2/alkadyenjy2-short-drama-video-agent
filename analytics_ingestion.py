"""Persist normalized analytics events with deterministic event IDs."""
import hashlib
import json
from typing import Dict, Iterable

from persistence.repository import PersistenceRepository


def persist_events(repo: PersistenceRepository, events: Iterable[Dict], publication_id: str = "") -> int:
    count = 0
    for event in events:
        payload = json.dumps({
            "platform": event["platform"],
            "video_id": event["video_id"],
            "observed_at": event["observed_at"],
            "metrics": event.get("metrics", {}),
        }, sort_keys=True, separators=(",", ":"))
        event = dict(event)
        event["event_id"] = "evt_" + hashlib.sha256(payload.encode()).hexdigest()[:20]
        if publication_id:
            event["publication_id"] = publication_id
        repo.create_analytics_event(event)
        count += 1
    return count

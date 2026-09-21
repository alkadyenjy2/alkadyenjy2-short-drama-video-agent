"""Platform-neutral analytics event schema.
Metrics are only populated from platform evidence; absent values remain None/UNKNOWN.
"""
from typing import Any, Dict, Optional

def normalize_metric_event(platform: str, video_id: str, observed_at: str, metrics: Dict[str, Any], source_url: str = "") -> Dict:
    allowed = ("views", "likes", "comments", "shares", "saves", "downloads", "watch_time_sec", "followers_gained", "ad_spend", "revenue")
    clean: Dict[str, Optional[Any]] = {k: metrics.get(k) for k in allowed}
    for k,v in clean.items():
        if isinstance(v, (int,float)) and v < 0: raise ValueError(f"negative metric: {k}")
    return {"platform": platform, "video_id": video_id, "observed_at": observed_at, "source_url": source_url,
            "metrics": clean, "evidence_status": "OBSERVED" if metrics else "UNKNOWN",
            "currency": metrics.get("currency"), "attribution_window": metrics.get("attribution_window")}

"""Meta/Instagram/Facebook analytics boundary.

Uses Graph API Insights for authorized assets. Missing credentials/permissions fail closed.
No metric is synthesized.
"""
import os
from datetime import datetime, timezone
from typing import Dict, Optional
import requests

from analytics_schema import normalize_metric_event


class MetaAnalyticsAccessError(RuntimeError):
    pass


class MetaInsightsAdapter:
    def __init__(self, access_token: Optional[str] = None, graph_version: Optional[str] = None, timeout: int = 30):
        self.access_token = access_token or os.getenv("META_PAGE_ACCESS_TOKEN")
        self.graph_version = graph_version or os.getenv("META_GRAPH_VERSION", "v23.0")
        self.timeout = timeout

    def _get(self, object_id: str, params: Dict) -> Dict:
        if not self.access_token:
            raise MetaAnalyticsAccessError("META_PAGE_ACCESS_TOKEN is required")
        params = dict(params)
        params["access_token"] = self.access_token
        url = f"https://graph.facebook.com/{self.graph_version}/{object_id}/insights"
        response = requests.get(url, params=params, timeout=self.timeout)
        if response.status_code != 200:
            raise MetaAnalyticsAccessError(f"Meta insights failed: HTTP {response.status_code}")
        payload = response.json()
        if payload.get("error"):
            raise MetaAnalyticsAccessError("Meta insights returned an API error")
        return payload

    def facebook_video_insights(self, video_id: str, metrics: str = "total_video_views") -> Dict:
        payload = self._get(video_id, {"metric": metrics})
        values = {}
        for row in payload.get("data", []):
            name = row.get("name")
            value = row.get("values", [{}])[-1].get("value")
            values[name] = value
        return normalize_metric_event(
            "facebook", video_id, datetime.now(timezone.utc).isoformat(),
            {"views": values.get("total_video_views"), "likes": None, "comments": None,
             "shares": None, "watch_time_sec": None, "followers_gained": None,
             "downloads": None, "ad_spend": None, "revenue": None},
            f"https://www.facebook.com/{video_id}",
        )

    def instagram_media_insights(self, media_id: str, metrics: str = "views,likes,comments,shares,saved,total_interactions") -> Dict:
        payload = self._get(media_id, {"metric": metrics})
        values = {}
        for row in payload.get("data", []):
            name = row.get("name")
            values[name] = row.get("values", [{}])[-1].get("value")
        return normalize_metric_event(
            "instagram", media_id, datetime.now(timezone.utc).isoformat(),
            {"views": values.get("views"), "likes": values.get("likes"),
             "comments": values.get("comments"), "shares": values.get("shares"),
             "saves": values.get("saved"), "watch_time_sec": None,
             "followers_gained": None, "downloads": None,
             "ad_spend": None, "revenue": None},
            f"https://www.instagram.com/",
        )

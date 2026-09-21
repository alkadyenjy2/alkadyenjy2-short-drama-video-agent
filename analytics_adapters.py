"""Live analytics adapters for owned/authorized content.

No metrics are fabricated. Missing credentials/scopes are explicit ACCESS_REQUIRED.
"""
from datetime import datetime, timezone
import os
from typing import Dict, Optional, List
import requests

from analytics_schema import normalize_metric_event


class AnalyticsAccessError(RuntimeError):
    pass


class YouTubeAnalyticsAdapter:
    def __init__(self, access_token: Optional[str] = None, timeout: int = 30):
        self.access_token = access_token or os.getenv("YOUTUBE_ACCESS_TOKEN")
        self.timeout = timeout

    def fetch_video_metrics(self, video_id: str, start_date: str, end_date: str,
                            include_revenue: bool = False) -> Dict:
        if not self.access_token:
            raise AnalyticsAccessError("YOUTUBE_ACCESS_TOKEN is required")
        if not video_id:
            raise ValueError("video_id is required")
        metrics = ["views", "likes", "comments", "shares", "estimatedMinutesWatched", "subscribersGained"]
        if include_revenue:
            metrics += ["estimatedRevenue", "estimatedAdRevenue"]
        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": ",".join(metrics),
            "filters": f"video=={video_id}",
            "access_token": self.access_token,
        }
        response = requests.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            params=params,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise AnalyticsAccessError(f"youtube analytics failed: HTTP {response.status_code}")
        payload = response.json()
        headers = payload.get("columnHeaders", [])
        rows = payload.get("rows", [])
        if not rows:
            return normalize_metric_event(
                "youtube", video_id, datetime.now(timezone.utc).isoformat(), {},
                f"https://www.youtube.com/watch?v={video_id}",
            )
        values = dict(zip([h.get("name") for h in headers], rows[0]))
        clean = {
            "views": values.get("views"),
            "likes": values.get("likes"),
            "comments": values.get("comments"),
            "shares": values.get("shares"),
            "watch_time_sec": (float(values["estimatedMinutesWatched"]) * 60) if values.get("estimatedMinutesWatched") is not None else None,
            "followers_gained": values.get("subscribersGained"),
            "revenue": values.get("estimatedRevenue"),
            "ad_spend": None,
            "currency": "USD" if include_revenue else None,
            "attribution_window": f"{start_date}:{end_date}",
        }
        return normalize_metric_event(
            "youtube", video_id, datetime.now(timezone.utc).isoformat(), clean,
            f"https://www.youtube.com/watch?v={video_id}",
        )


class TikTokOwnedAnalyticsAdapter:
    def __init__(self, access_token: Optional[str] = None, timeout: int = 30):
        self.access_token = access_token or os.getenv("TIKTOK_ACCESS_TOKEN")
        self.timeout = timeout

    def fetch_recent_videos(self, max_count: int = 20) -> List[Dict]:
        if not self.access_token:
            raise AnalyticsAccessError("TIKTOK_ACCESS_TOKEN is required")
        max_count = max(1, min(int(max_count), 20))
        response = requests.post(
            "https://open.tiktokapis.com/v2/video/list/?fields=id,title,video_description,duration,like_count,comment_count,share_count,view_count,create_time,share_url",
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json={"max_count": max_count},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise AnalyticsAccessError(f"tiktok video.list failed: HTTP {response.status_code}")
        payload = response.json()
        error = payload.get("error", {})
        if error and error.get("code") not in (None, "ok"):
            raise AnalyticsAccessError("tiktok video.list returned an API error")
        events = []
        for video in payload.get("data", {}).get("videos", []):
            events.append(normalize_metric_event(
                "tiktok",
                str(video.get("id")),
                datetime.now(timezone.utc).isoformat(),
                {
                    "views": video.get("view_count"),
                    "likes": video.get("like_count"),
                    "comments": video.get("comment_count"),
                    "shares": video.get("share_count"),
                    "watch_time_sec": None,
                    "followers_gained": None,
                    "revenue": None,
                    "ad_spend": None,
                    "currency": None,
                    "attribution_window": "current_api_snapshot",
                },
                video.get("share_url", ""),
            ))
        return events

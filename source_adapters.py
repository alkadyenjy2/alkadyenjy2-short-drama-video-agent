"""Live discovery adapters -> fetch -> normalize -> TrendObservation.

Adapters are fail-closed: missing credentials/access never becomes fake trend data.
"""
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import requests

from trend_intelligence import TrendObservation


class AdapterAccessError(RuntimeError):
    pass


class SourceAdapter:
    source = "unknown"

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def normalize(self, records: List[Dict[str, Any]], observed_at: Optional[str] = None) -> List[TrendObservation]:
        raise NotImplementedError

    def discover(self, **kwargs) -> List[TrendObservation]:
        observed_at = datetime.now(timezone.utc).isoformat()
        return self.normalize(self.fetch(**kwargs), observed_at=observed_at)


class YouTubeDiscoveryAdapter(SourceAdapter):
    source = "youtube"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 20):
        self.api_key = api_key or os.getenv("YOUTUBE_DATA_API_KEY")
        self.timeout = timeout

    def fetch(self, query: str, published_after: Optional[str] = None,
              region_code: str = "US", max_results: int = 25) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise AdapterAccessError("YOUTUBE_DATA_API_KEY is required")
        if not query.strip():
            raise ValueError("query is required")
        max_results = max(1, min(int(max_results), 50))
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount",
            "maxResults": max_results,
            "regionCode": region_code,
            "key": self.api_key,
        }
        if published_after:
            params["publishedAfter"] = published_after
        search = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params=params,
            timeout=self.timeout,
        )
        if search.status_code != 200:
            raise AdapterAccessError(f"youtube search failed: HTTP {search.status_code}")
        items = search.json().get("items", [])
        ids = [x.get("id", {}).get("videoId") for x in items if x.get("id", {}).get("videoId")]
        if not ids:
            return []

        stats = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(ids),
                "key": self.api_key,
            },
            timeout=self.timeout,
        )
        if stats.status_code != 200:
            raise AdapterAccessError(f"youtube videos.list failed: HTTP {stats.status_code}")
        return stats.json().get("items", [])

    def normalize(self, records: List[Dict[str, Any]], observed_at: Optional[str] = None) -> List[TrendObservation]:
        observed_at = observed_at or datetime.now(timezone.utc).isoformat()
        out = []
        now = datetime.now(timezone.utc)
        for item in records:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content = item.get("contentDetails", {})
            published = snippet.get("publishedAt")
            try:
                age_hours = max((now - datetime.fromisoformat(published.replace("Z", "+00:00"))).total_seconds() / 3600, 0.1)
            except Exception:
                age_hours = 24.0
            out.append(TrendObservation(
                source=self.source,
                source_url=f"https://www.youtube.com/watch?v={item.get('id')}",
                observed_at=observed_at,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                views=int(statistics.get("viewCount", 0) or 0),
                likes=int(statistics.get("likeCount", 0) or 0),
                comments=int(statistics.get("commentCount", 0) or 0),
                shares=0,
                duration_sec=_iso_duration_seconds(content.get("duration", "")),
                age_hours=age_hours,
                genre="unknown",
            ))
        return out


class TikTokResearchAdapter(SourceAdapter):
    source = "tiktok_research"

    def __init__(self, access_token: Optional[str] = None, timeout: int = 20):
        self.access_token = access_token or os.getenv("TIKTOK_RESEARCH_ACCESS_TOKEN")
        self.timeout = timeout

    def fetch(self, keyword: str, start_date: str, end_date: str,
              region_codes: Optional[List[str]] = None, max_count: int = 20) -> List[Dict[str, Any]]:
        if not self.access_token:
            raise AdapterAccessError("TIKTOK_RESEARCH_ACCESS_TOKEN is required")
        if not keyword.strip():
            raise ValueError("keyword is required")
        regions = region_codes or ["US"]
        max_count = max(1, min(int(max_count), 100))
        body = {
            "query": {"and": [
                {"operation": "IN", "field_name": "region_code", "field_values": regions},
                {"operation": "EQ", "field_name": "keyword", "field_values": [keyword]},
            ]},
            "max_count": max_count,
            "cursor": 0,
            "start_date": start_date,
            "end_date": end_date,
            "is_random": False,
        }
        response = requests.post(
            "https://open.tiktokapis.com/v2/research/video/query/?fields=id,video_description,create_time,region_code,view_count,like_count,comment_count,share_count,video_duration,username,hashtag_names",
            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            json=body,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise AdapterAccessError(f"tiktok research query failed: HTTP {response.status_code}")
        payload = response.json()
        error = payload.get("error", {})
        if error and error.get("code") not in (None, "ok"):
            raise AdapterAccessError("tiktok research query returned an API error")
        return payload.get("data", {}).get("videos", [])

    def normalize(self, records: List[Dict[str, Any]], observed_at: Optional[str] = None) -> List[TrendObservation]:
        observed_at = observed_at or datetime.now(timezone.utc).isoformat()
        now = datetime.now(timezone.utc)
        out = []
        for item in records:
            created = item.get("create_time")
            try:
                age_hours = max((now - datetime.fromtimestamp(int(created), tz=timezone.utc)).total_seconds() / 3600, 0.1)
            except Exception:
                age_hours = 24.0
            vid = str(item.get("id", ""))
            out.append(TrendObservation(
                source=self.source,
                source_url=f"https://www.tiktok.com/@{item.get('username','')}/video/{vid}",
                observed_at=observed_at,
                title=item.get("video_description", "")[:500],
                description=item.get("video_description", ""),
                views=int(item.get("view_count", 0) or 0),
                likes=int(item.get("like_count", 0) or 0),
                comments=int(item.get("comment_count", 0) or 0),
                shares=int(item.get("share_count", 0) or 0),
                duration_sec=int(item.get("video_duration", 0) or 0),
                age_hours=age_hours,
                genre="unknown",
            ))
        return out


def _iso_duration_seconds(value: str) -> int:
    if not value or not value.startswith("PT"):
        return 0
    import re
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return 0
    hours, minutes, seconds = (int(x or 0) for x in match.groups())
    return hours * 3600 + minutes * 60 + seconds

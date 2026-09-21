import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_adapters import TikTokOwnedAnalyticsAdapter, YouTubeAnalyticsAdapter


def test_youtube_access_is_required():
    try:
        YouTubeAnalyticsAdapter(access_token="").fetch_video_metrics("vid", "2026-09-01", "2026-09-02")
    except Exception as exc:
        assert "YOUTUBE_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("missing YouTube analytics token must fail closed")


def test_tiktok_access_is_required():
    try:
        TikTokOwnedAnalyticsAdapter(access_token="").fetch_recent_videos()
    except Exception as exc:
        assert "TIKTOK_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("missing TikTok token must fail closed")


if __name__ == "__main__":
    test_youtube_access_is_required()
    test_tiktok_access_is_required()
    print("ANALYTICS ADAPTER AUDIT: 2 PASS")

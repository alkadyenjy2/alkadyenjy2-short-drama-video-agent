import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from discovery_pipeline import run_discovery
from platform_recommender import recommend_platforms
from source_adapters import SourceAdapter, TikTokResearchAdapter, YouTubeDiscoveryAdapter


class FakeAdapter(SourceAdapter):
    source = "fake"

    def fetch(self, **kwargs):
        return [{"id": "1"}]

    def normalize(self, records, observed_at=None):
        from trend_intelligence import TrendObservation
        return [TrendObservation(
            source="fake", source_url="https://example.com/1",
            observed_at=observed_at or "2026-01-01T00:00:00+00:00",
            title="Test winner", views=100000, likes=12000, comments=1000,
            shares=3000, duration_sec=42, age_hours=4
        )]


def test_youtube_missing_key_is_access_required():
    adapter = YouTubeDiscoveryAdapter(api_key="")
    try:
        adapter.fetch(query="romance")
    except Exception as exc:
        assert "YOUTUBE_DATA_API_KEY" in str(exc)
    else:
        raise AssertionError("missing YouTube key must fail closed")


def test_tiktok_missing_key_is_access_required():
    adapter = TikTokResearchAdapter(access_token="")
    try:
        adapter.fetch(keyword="romance", start_date="20260901", end_date="20260902")
    except Exception as exc:
        assert "TIKTOK_RESEARCH_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("missing TikTok token must fail closed")


def test_pipeline_normalizes_and_ranks_and_gates():
    result = run_discovery([FakeAdapter()], {"fake": {}})
    assert result["status"] == "OBSERVED"
    assert result["evidence_status"] == "OBSERVED"
    item = result["results"][0]
    assert item["trend"]["trend_score"] > 0
    assert item["rights_gate"]["status"] == "DO_NOT_PUBLISH_UNTIL_REVIEW"
    assert {x["platform"] for x in item["platform_fit"]} == {"youtube", "tiktok", "instagram", "facebook"}


def test_platform_access_constraints():
    result = recommend_platforms({"duration_sec": 45, "evidence_status": "OBSERVED"},
                                 {"youtube": False, "tiktok": True, "instagram": False, "facebook": False})
    assert [x["platform"] for x in result] == ["tiktok"]


if __name__ == "__main__":
    for fn in [test_youtube_missing_key_is_access_required, test_tiktok_missing_key_is_access_required,
               test_pipeline_normalizes_and_ranks_and_gates, test_platform_access_constraints]:
        fn()
    print("DISCOVERY PIPELINE AUDIT: 4 PASS")

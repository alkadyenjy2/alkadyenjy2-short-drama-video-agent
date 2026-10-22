import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meta_ads_analytics import MetaAdsInsightsAdapter
from http_video_generation import HTTPVideoGenerationAdapter


def test_meta_ads_credentials_fail_closed():
    try:
        MetaAdsInsightsAdapter(access_token="", account_id="").fetch_account_insights("2026-09-01", "2026-09-02")
    except Exception as exc:
        assert "META_ADS_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("Meta Ads missing token must fail closed")


def test_http_generation_credentials_fail_closed():
    try:
        HTTPVideoGenerationAdapter(endpoint="", api_key="").generate("script", {})
    except Exception as exc:
        assert "VIDEO_GENERATION_API_URL" in str(exc)
    else:
        raise AssertionError("generic video provider must fail closed")


if __name__ == "__main__":
    test_meta_ads_credentials_fail_closed()
    test_http_generation_credentials_fail_closed()
    print("META ADS + HTTP GENERATION AUDIT: 2 PASS")

def test_http_generation_rejects_empty_script_before_network():
    adapter = HTTPVideoGenerationAdapter(endpoint="https://provider.invalid/generate", api_key="test-key")
    try:
        adapter.generate("   ", {})
    except ValueError as exc:
        assert "script is required" in str(exc)
    else:
        raise AssertionError("empty scripts must fail before a provider request")


def test_http_generation_rejects_unrecognized_provider_response():
    from unittest.mock import Mock, patch

    adapter = HTTPVideoGenerationAdapter(endpoint="https://provider.invalid/generate", api_key="test-key")
    response = Mock(status_code=202)
    response.json.return_value = {"status": "queued"}
    with patch("http_video_generation.requests.post", return_value=response):
        try:
            adapter.generate("A phone rings in a dark room.", {"beats": []})
        except Exception as exc:
            assert "artifact_url" in str(exc) or "job_id" in str(exc)
        else:
            raise AssertionError("a response without an artifact or pollable job must not pass")

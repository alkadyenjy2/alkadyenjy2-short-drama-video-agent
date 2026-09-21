import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ad_revenue_schema import observed_financial_event
from meta_analytics import MetaInsightsAdapter
from transcription_adapter import ProviderUnavailableTranscriptionAdapter
from video_generation_adapter import ProviderUnavailableVideoGenerationAdapter


def test_meta_access_is_required():
    try:
        MetaInsightsAdapter(access_token="").facebook_video_insights("vid")
    except Exception as exc:
        assert "META_PAGE_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("missing Meta token must fail closed")


def test_financial_event_is_observed_only_when_declared():
    event = observed_financial_event("youtube", "vid", 2.0, 5.0, "USD")
    assert event["evidence_status"] == "OBSERVED"
    assert event["ad_spend"] == 2.0


def test_transcription_boundary_fails_closed():
    try:
        ProviderUnavailableTranscriptionAdapter().transcribe("https://example.com/a.mp4")
    except Exception as exc:
        assert "No transcription provider" in str(exc)
    else:
        raise AssertionError("unconfigured transcription must fail closed")


def test_generation_boundary_fails_closed():
    try:
        ProviderUnavailableVideoGenerationAdapter().generate("script", {})
    except Exception as exc:
        assert "No video-generation provider" in str(exc)
    else:
        raise AssertionError("unconfigured generation must fail closed")


if __name__ == "__main__":
    test_meta_access_is_required()
    test_financial_event_is_observed_only_when_declared()
    test_transcription_boundary_fails_closed()
    test_generation_boundary_fails_closed()
    print("META/FINANCE/MEDIA BOUNDARY AUDIT: 4 PASS")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from idea_fetcher import attach_transcript
from rights_policy_evidence import evaluate_platform_rights, get_policy_evidence


def test_transcript_never_fabricated():
    doc = {"status": "FETCHED", "transcript_status": "NOT_AVAILABLE"}
    out = attach_transcript(doc, "hello transcript", "user_supplied")
    assert out["transcript_status"] == "OBSERVED"
    assert out["transcript_provider"] == "user_supplied"


def test_policy_evidence_exists_for_supported_platforms():
    for platform in ("youtube", "tiktok", "instagram", "facebook"):
        assert get_policy_evidence(platform)


def test_youtube_permission_does_not_bypass_monetization_review():
    source_gate = {"status": "ADAPT_WITH_PERMISSION", "reasons": []}
    out = evaluate_platform_rights("youtube", source_gate, original_value=False)
    assert out["status"] == "REVIEW_MONETIZATION_ELIGIBILITY"
    assert out["legal_review_required"] is False


if __name__ == "__main__":
    test_transcript_never_fabricated()
    test_policy_evidence_exists_for_supported_platforms()
    test_youtube_permission_does_not_bypass_monetization_review()
    print("IDEA/RIGHTS POLICY AUDIT: 3 PASS")

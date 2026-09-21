"""Platform-specific rights/monetization policy evidence.

URLs are official policy sources. This module is an operational gate, not legal advice.
"""
from typing import Dict, List

POLICY_SOURCES = {
    "youtube": [
        {
            "topic": "copyright",
            "url": "https://support.google.com/youtube/answer/2797466",
            "rule": "Copyright owners control use of original creative works; permission, a valid exception, public domain, or applicable license may be relevant.",
        },
        {
            "topic": "monetization_reused_content",
            "url": "https://support.google.com/youtube/answer/1311392",
            "rule": "Reused content needs meaningful original value; permission alone does not guarantee monetization eligibility.",
        },
    ],
    "tiktok": [
        {
            "topic": "copyright",
            "url": "https://t.tiktok.com/legal/page/global/copyright-policy/en",
            "rule": "TikTok prohibits copyright infringement; unauthorized use may violate policy, subject to applicable legal exceptions.",
        },
        {
            "topic": "research_access",
            "url": "https://developers.tiktok.com/docs/en/research-api-get-started",
            "rule": "Public research data access requires an approved Research project and client credentials.",
        },
    ],
    "instagram": [
        {
            "topic": "meta_publisher",
            "url": "https://developers.facebook.com/docs/instagram-api/guides/content-publishing/",
            "rule": "Publishing depends on the applicable Instagram account/API permissions and product requirements.",
        },
    ],
    "facebook": [
        {
            "topic": "meta_publisher",
            "url": "https://developers.facebook.com/docs/video-api/guides/publishing/",
            "rule": "Video publishing depends on Page/account permissions and Meta API requirements.",
        },
    ],
}


def get_policy_evidence(platform: str) -> List[Dict]:
    return POLICY_SOURCES.get(platform.lower(), [])


def evaluate_platform_rights(platform: str, source_gate: Dict, original_value: bool = False) -> Dict:
    evidence = get_policy_evidence(platform)
    reasons = list(source_gate.get("reasons", []))
    status = source_gate.get("status", "DO_NOT_PUBLISH_UNTIL_REVIEW")

    if platform.lower() == "youtube" and not original_value:
        reasons.append("YouTube monetization policy requires meaningful original value for reused content.")
        if status == "ADAPT_WITH_PERMISSION":
            status = "REVIEW_MONETIZATION_ELIGIBILITY"

    return {
        "platform": platform,
        "status": status,
        "policy_evidence": evidence,
        "reasons": reasons,
        "legal_review_required": status == "DO_NOT_PUBLISH_UNTIL_REVIEW",
    }

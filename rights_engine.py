"""Rights/similarity gate for source material.
This module deliberately does not declare legal ownership. It classifies operational risk
and requires provenance/evidence before adaptation or publishing.
"""
from typing import Dict
from urllib.parse import urlparse

PROTECTED = {"copyrighted", "licensed_to_third_party", "unknown"}

def classify_source(source_type: str, has_permission: bool = False, user_owned: bool = False) -> str:
    s = (source_type or "unknown").lower().strip()
    if user_owned or has_permission: return "PERMISSION_CONFIRMED"
    if s in {"public_domain", "original", "user_idea", "public_fact"}: return "LOW_RISK_SOURCE"
    if s in PROTECTED: return "REQUIRES_REVIEW"
    return "REQUIRES_REVIEW"


def assess_adaptation(source_type: str, has_permission: bool = False, user_owned: bool = False,
                      uses_original_footage: bool = False, copies_dialogue: bool = False,
                      copies_characters: bool = False, similarity_score: float = 0.0) -> Dict:
    classification = classify_source(source_type, has_permission, user_owned)
    reasons = []
    if uses_original_footage: reasons.append("original source footage would be reused")
    if copies_dialogue: reasons.append("source dialogue would be copied")
    if copies_characters: reasons.append("source-specific characters would be copied")
    if similarity_score >= 0.80: reasons.append("high structural/content similarity requires review")
    if classification == "REQUIRES_REVIEW": reasons.append("source rights/provenance not confirmed")
    if reasons:
        status = "DO_NOT_PUBLISH_UNTIL_REVIEW"
    elif classification == "PERMISSION_CONFIRMED":
        status = "ADAPT_WITH_PERMISSION"
    else:
        status = "ORIGINAL_ADAPTATION"
    return {"status": status, "source_classification": classification, "similarity_score": similarity_score,
            "reasons": reasons, "provenance_required": True,
            "disclaimer": "Operational screening only; not a legal opinion."}


def validate_source_url(url: str) -> bool:
    p = urlparse(url or "")
    return p.scheme in {"http", "https"} and bool(p.netloc)

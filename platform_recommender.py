"""Evidence-based platform fit recommendations.

This is a rule engine, not a performance guarantee. It only uses supplied evidence
and explicit account/access constraints.
"""
from typing import Any, Dict, List


def recommend_platforms(trend: Dict[str, Any], account_access: Dict[str, bool] | None = None) -> List[Dict[str, Any]]:
    access = account_access or {}
    duration = int(trend.get("duration_sec") or 0)
    recommendations = []

    def add(platform: str, reasons: List[str], requirements: List[str]):
        recommendations.append({
            "platform": platform,
            "fit_reasons": reasons,
            "requirements": requirements,
            "evidence_status": "OBSERVED" if trend.get("evidence_status") == "OBSERVED" else "UNKNOWN",
        })

    if access.get("youtube", True):
        reasons = ["source metrics are compatible with YouTube discovery/analytics"]
        if duration <= 60:
            reasons.append("short duration is compatible with short-form packaging")
        add("youtube", reasons, ["YouTube channel/API access"])

    if access.get("tiktok", True):
        reasons = ["source metrics are compatible with short-form distribution"]
        if duration <= 180:
            reasons.append("duration is within common short-form production range")
        add("tiktok", reasons, ["TikTok account/app access", "publishing permissions where applicable"])

    if access.get("instagram", True):
        reasons = ["short-form video can be packaged for Reels"]
        add("instagram", reasons, ["Instagram professional account", "Meta permissions"])

    if access.get("facebook", True):
        add("facebook", ["short-form video can be packaged for Facebook video/Reels"],
            ["Facebook Page", "Meta permissions"])

    return recommendations

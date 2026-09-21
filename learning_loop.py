"""Deterministic feedback loop from observed analytics into future story selection.

This module produces signals/features, not promises. It never invents missing metrics.
"""
from typing import Any, Dict, Iterable, List


def build_learning_signal(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    events = list(events)
    if not events:
        return {"status": "NO_DATA", "evidence_status": "UNKNOWN", "signals": {}}

    views = [e["metrics"].get("views") for e in events if e.get("metrics", {}).get("views") is not None]
    likes = [e["metrics"].get("likes") for e in events if e.get("metrics", {}).get("likes") is not None]
    comments = [e["metrics"].get("comments") for e in events if e.get("metrics", {}).get("comments") is not None]
    shares = [e["metrics"].get("shares") for e in events if e.get("metrics", {}).get("shares") is not None]
    watch = [e["metrics"].get("watch_time_sec") for e in events if e.get("metrics", {}).get("watch_time_sec") is not None]
    followers = [e["metrics"].get("followers_gained") for e in events if e.get("metrics", {}).get("followers_gained") is not None]
    revenue = [e["metrics"].get("revenue") for e in events if e.get("metrics", {}).get("revenue") is not None]

    total_views = sum(views) if views else None
    total_likes = sum(likes) if likes else None
    total_comments = sum(comments) if comments else None
    total_shares = sum(shares) if shares else None

    signals: Dict[str, Any] = {
        "observed_events": len(events),
        "views": total_views,
        "likes": total_likes,
        "comments": total_comments,
        "shares": total_shares,
        "watch_time_sec": sum(watch) if watch else None,
        "followers_gained": sum(followers) if followers else None,
        "revenue": sum(revenue) if revenue else None,
        "engagement_rate": ((total_likes or 0) + (total_comments or 0) + (total_shares or 0)) / total_views if total_views else None,
        "watch_time_per_view_sec": (sum(watch) / total_views) if watch and total_views else None,
    }

    feedback = []
    if signals["engagement_rate"] is not None:
        feedback.append("engagement_observed")
    if signals["watch_time_per_view_sec"] is not None:
        feedback.append("watch_time_observed")
    if signals["followers_gained"] is not None:
        feedback.append("follower_conversion_observed")
    if signals["revenue"] is not None:
        feedback.append("revenue_observed")
    return {
        "status": "OBSERVED",
        "evidence_status": "OBSERVED",
        "signals": signals,
        "feedback_features": feedback,
    }


def compare_story_variants(variant_events: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    result = []
    for variant, events in variant_events.items():
        signal = build_learning_signal(events)
        result.append({"variant": variant, **signal})
    return result

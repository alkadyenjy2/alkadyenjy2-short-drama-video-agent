"""P1 trend intelligence: evidence-first scoring over normalized source observations.
No fabricated live data; adapters must provide observed_at/source_url and metrics.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

@dataclass(frozen=True)
class TrendObservation:
    source: str
    source_url: str
    observed_at: str
    title: str
    description: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    duration_sec: int = 0
    age_hours: float = 24.0
    genre: str = "unknown"

    def validate(self) -> None:
        if not self.source or not self.source_url or not self.observed_at or not self.title:
            raise ValueError("trend observation requires source, source_url, observed_at, title")
        if min(self.views, self.likes, self.comments, self.shares, self.duration_sec) < 0:
            raise ValueError("trend metrics cannot be negative")


def score_observation(o: TrendObservation) -> Dict:
    o.validate()
    views = max(o.views, 1)
    engagement = (o.likes + o.comments + o.shares) / views
    velocity = views / max(o.age_hours, 1.0)
    share_rate = o.shares / views
    # Transparent bounded score; it is a ranking heuristic, not a promise of future performance.
    score = min(100.0, 35.0 * min(velocity / 10000.0, 1.0) + 45.0 * min(engagement / 0.15, 1.0) + 20.0 * min(share_rate / 0.03, 1.0))
    return {
        "source": o.source, "source_url": o.source_url, "observed_at": o.observed_at,
        "title": o.title, "genre": o.genre, "views": o.views, "likes": o.likes,
        "comments": o.comments, "shares": o.shares, "duration_sec": o.duration_sec,
        "engagement_rate": round(engagement, 6), "views_per_hour": round(velocity, 2),
        "share_rate": round(share_rate, 6), "trend_score": round(score, 2),
        "score_method": "bounded_velocity_engagement_share_v1", "evidence_status": "OBSERVED"
    }


def rank_trends(observations: List[TrendObservation], limit: int = 20) -> List[Dict]:
    ranked = [score_observation(o) for o in observations]
    return sorted(ranked, key=lambda x: x["trend_score"], reverse=True)[:limit]


def recommended_episode_count(trend: Dict) -> int:
    # Content planning heuristic; never presented as platform fact.
    d = int(trend.get("duration_sec") or 0)
    if d <= 30: return 4
    if d <= 60: return 6
    return 8

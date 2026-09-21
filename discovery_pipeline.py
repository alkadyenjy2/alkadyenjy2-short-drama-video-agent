"""Discovery orchestration: Source Adapter -> Fetch -> Normalize -> Trend Rank -> Rights Gate -> Platform Fit."""
from typing import Any, Dict, Iterable, List

from platform_recommender import recommend_platforms
from rights_engine import assess_adaptation
from trend_intelligence import rank_trends


def run_discovery(adapters: Iterable[Any], adapter_kwargs: Dict[str, Dict[str, Any]],
                  source_type: str = "unknown", account_access: Dict[str, bool] | None = None) -> Dict[str, Any]:
    observations = []
    access = []
    for adapter in adapters:
        try:
            observations.extend(adapter.discover(**adapter_kwargs.get(adapter.source, {})))
        except Exception as exc:
            access.append({"source": adapter.source, "status": "ACCESS_REQUIRED", "reason": str(exc)})

    ranked = rank_trends(observations)
    results = []
    for trend in ranked:
        rights = assess_adaptation(source_type=source_type)
        results.append({
            "trend": trend,
            "rights_gate": rights,
            "platform_fit": recommend_platforms(trend, account_access),
        })
    return {
        "status": "OBSERVED" if observations else ("ACCESS_REQUIRED" if access else "NO_RESULTS"),
        "results": results,
        "access": access,
        "evidence_status": "OBSERVED" if observations else "UNKNOWN",
    }

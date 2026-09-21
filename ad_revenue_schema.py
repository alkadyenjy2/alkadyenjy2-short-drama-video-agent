"""Normalized ad spend/revenue event schema.

Provider adapters may populate these fields only from verified API responses or
provider transaction records. Estimates remain explicitly labeled.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import hashlib
import json


def normalize_financial_event(platform: str, object_id: str, observed_at: str,
                              spend: Optional[float] = None,
                              revenue: Optional[float] = None,
                              currency: Optional[str] = None,
                              source_url: str = "",
                              attribution_window: Optional[str] = None,
                              evidence_status: str = "UNKNOWN") -> Dict[str, Any]:
    if spend is not None and spend < 0:
        raise ValueError("spend cannot be negative")
    if revenue is not None and revenue < 0:
        raise ValueError("revenue cannot be negative")
    if evidence_status not in {"OBSERVED", "ESTIMATED", "UNKNOWN"}:
        raise ValueError("invalid evidence_status")
    event = {
        "platform": platform,
        "object_id": object_id,
        "observed_at": observed_at,
        "ad_spend": spend,
        "revenue": revenue,
        "currency": currency,
        "source_url": source_url,
        "attribution_window": attribution_window,
        "evidence_status": evidence_status,
    }
    event["event_id"] = "fin_" + hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
    return event


def observed_financial_event(platform: str, object_id: str, spend: Optional[float],
                             revenue: Optional[float], currency: Optional[str],
                             source_url: str = "", attribution_window: Optional[str] = None) -> Dict[str, Any]:
    return normalize_financial_event(
        platform, object_id, datetime.now(timezone.utc).isoformat(),
        spend, revenue, currency, source_url, attribution_window, "OBSERVED"
    )

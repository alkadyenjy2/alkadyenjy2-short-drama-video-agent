"""Meta Marketing API Insights adapter for authorized ad accounts.

Returns observed spend/conversion metrics only. It never treats estimates as revenue.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional
import requests

from ad_revenue_schema import normalize_financial_event


class MetaAdsAccessError(RuntimeError):
    pass


class MetaAdsInsightsAdapter:
    def __init__(self, access_token: Optional[str] = None, account_id: Optional[str] = None,
                 graph_version: Optional[str] = None, timeout: int = 30):
        self.access_token = access_token or os.getenv("META_ADS_ACCESS_TOKEN") or os.getenv("META_PAGE_ACCESS_TOKEN")
        self.account_id = account_id or os.getenv("META_AD_ACCOUNT_ID")
        self.graph_version = graph_version or os.getenv("META_GRAPH_VERSION", "v23.0")
        self.timeout = timeout

    def fetch_account_insights(self, since: str, until: str, level: str = "ad") -> Dict:
        if not self.access_token:
            raise MetaAdsAccessError("META_ADS_ACCESS_TOKEN is required")
        if not self.account_id:
            raise MetaAdsAccessError("META_AD_ACCOUNT_ID is required")
        if level not in {"account", "campaign", "adset", "ad"}:
            raise ValueError("invalid insights level")
        fields = ",".join([
            "date_start","date_stop","account_id","ad_id","ad_name",
            "adset_id","adset_name","campaign_id","campaign_name",
            "impressions","clicks","reach","spend","account_currency",
            "actions","action_values","conversions","conversion_values"
        ])
        response = requests.get(
            f"https://graph.facebook.com/{self.graph_version}/act_{self.account_id}/insights",
            params={
                "fields": fields,
                "level": level,
                "time_range": json.dumps({"since": since, "until": until}, separators=(",", ":")),
                "access_token": self.access_token,
            },
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise MetaAdsAccessError(f"Meta Ads Insights failed: HTTP {response.status_code}")
        payload = response.json()
        if payload.get("error"):
            raise MetaAdsAccessError("Meta Ads Insights returned an API error")
        return payload

    def normalize_financial_events(self, since: str, until: str, level: str = "ad"):
        payload = self.fetch_account_insights(since, until, level)
        events = []
        for row in payload.get("data", []):
            object_id = row.get("ad_id") or row.get("campaign_id") or row.get("adset_id") or row.get("account_id")
            spend = float(row["spend"]) if row.get("spend") is not None else None
            # Meta action_values/conversion_values are attribution values, not automatically business revenue.
            events.append(normalize_financial_event(
                "meta_ads", str(object_id), datetime.now(timezone.utc).isoformat(),
                spend=spend, revenue=None,
                currency=row.get("account_currency"),
                source_url=f"https://www.facebook.com/adsmanager/",
                attribution_window=f"{row.get('date_start')}:{row.get('date_stop')}",
                evidence_status="OBSERVED",
            ))
        return events

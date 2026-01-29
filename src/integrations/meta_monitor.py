"""Meta Ads monitoring helpers.

Goal: pull performance + status from Meta Ads, and translate into agent-friendly artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from .meta_ads import MetaAdsAPI


DEFAULT_FIELDS = [
    "impressions",
    "clicks",
    "spend",
    "ctr",
    "cpc",
    "actions",
    "cost_per_action_type",
]


AD_LEVEL_FIELDS = DEFAULT_FIELDS + [
    'ad_id',
    'ad_name',
]


@dataclass
class MonitorResult:
    campaign_id: str
    date_start: str
    date_end: str
    insights: Dict[str, Any]
    status: Optional[Dict[str, Any]] = None


def fetch_campaign_metrics(
    api: MetaAdsAPI,
    campaign_id: str,
    date_start: str,
    date_end: str,
    fields: Optional[List[str]] = None,
    level: Optional[str] = None,
    include_advantage_state: bool = True,
) -> MonitorResult:
    insights = api.get_campaign_insights(
        campaign_id=campaign_id,
        date_start=date_start,
        date_end=date_end,
        fields=fields or DEFAULT_FIELDS,
        level=level,
    )

    status = None
    if include_advantage_state:
        try:
            status = api.get_advantage_state(campaign_id)
        except Exception:
            status = None

    return MonitorResult(
        campaign_id=campaign_id,
        date_start=date_start,
        date_end=date_end,
        insights=insights,
        status=status,
    )

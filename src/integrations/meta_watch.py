"""Cron-friendly Meta monitoring + guardrail evaluation.

This module is used by `cli.py watch-meta`.

It intentionally avoids any side-effects besides returning structured data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _insights_rows(insights: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Meta insights responses typically look like {"data": [ ... ]}."""
    if not isinstance(insights, dict):
        return []
    data = insights.get("data")
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    # Some mocks might return a single dict.
    if isinstance(data, dict):
        return [data]
    return []


def extract_actions_value(rows: List[Dict[str, Any]], preferred_types: List[str]) -> float:
    """Sum actions values across rows for preferred action types.

    If preferred types aren't found, returns 0.
    """
    total = 0.0
    for r in rows:
        actions = r.get("actions") or []
        if not isinstance(actions, list):
            continue
        for a in actions:
            if not isinstance(a, dict):
                continue
            at = a.get("action_type")
            if at in preferred_types:
                v = _to_float(a.get("value"))
                if v is not None:
                    total += v
    return total


def summarize_insights(insights: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a simple aggregate metric dict from Meta insights."""
    rows = _insights_rows(insights)
    if not rows:
        return {
            "spend": 0.0,
            "impressions": 0.0,
            "clicks": 0.0,
            "ctr": None,
            "conversions": 0.0,
            "cpa": None,
        }

    spend = 0.0
    impressions = 0.0
    clicks = 0.0
    ctr_weighted_numer = 0.0
    ctr_weight_denom = 0.0

    for r in rows:
        s = _to_float(r.get("spend"))
        if s is not None:
            spend += s
        imp = _to_float(r.get("impressions"))
        if imp is not None:
            impressions += imp
        clk = _to_float(r.get("clicks"))
        if clk is not None:
            clicks += clk

        # Prefer computing CTR from clicks/impressions when possible.
        if imp and imp > 0 and clk is not None:
            ctr_weighted_numer += clk
            ctr_weight_denom += imp
        else:
            ctr = _to_float(r.get("ctr"))
            if ctr is not None and imp and imp > 0:
                # ctr in insights is typically percent; but can be fraction.
                # We treat values >1 as percent.
                ctr_val = ctr / 100.0 if ctr > 1 else ctr
                ctr_weighted_numer += ctr_val * imp
                ctr_weight_denom += imp

    ctr_final = None
    if ctr_weight_denom > 0:
        ctr_final = ctr_weighted_numer / ctr_weight_denom

    # Conversions: best-effort. For demo guardrails we treat purchases/leads as conversions.
    conversions = extract_actions_value(
        rows,
        preferred_types=[
            "purchase",
            "offsite_conversion.purchase",
            "lead",
            "offsite_conversion.lead",
        ],
    )

    cpa = None
    if conversions and conversions > 0:
        cpa = spend / conversions

    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr_final,
        "conversions": conversions,
        "cpa": cpa,
    }


@dataclass
class GuardrailAlert:
    code: str
    severity: str  # info|warning|critical
    message: str
    suggested_action: str


def evaluate_guardrails(
    *,
    campaign_id: str,
    today: Dict[str, Any],
    trailing_7d: Dict[str, Any],
    daily_cap: Optional[float],
    target_cpa: Optional[float],
) -> List[GuardrailAlert]:
    alerts: List[GuardrailAlert] = []

    # 1) Spend cap
    if daily_cap is not None and today.get("spend") is not None:
        if float(today["spend"]) > float(daily_cap):
            alerts.append(
                GuardrailAlert(
                    code="SPEND_CAP",
                    severity="critical",
                    message=f"Spend today ${today['spend']:.2f} exceeds daily cap ${daily_cap:.2f}",
                    suggested_action="Cut budget or pause ad set(s) until spend stabilizes.",
                )
            )

    # 2) CTR drop vs trailing 7d avg
    t_ctr = today.get("ctr")
    avg_ctr = trailing_7d.get("ctr")
    if t_ctr is not None and avg_ctr is not None and avg_ctr > 0:
        if t_ctr < 0.8 * avg_ctr:
            drop_pct = (1 - (t_ctr / avg_ctr)) * 100
            alerts.append(
                GuardrailAlert(
                    code="CTR_DROP",
                    severity="warning",
                    message=f"CTR drop: today {t_ctr*100:.2f}% vs 7d avg {avg_ctr*100:.2f}% (-{drop_pct:.1f}%)",
                    suggested_action="Pause lowest-CTR ads, refresh creative, or narrow targeting.",
                )
            )

    # 3) CPA increase vs target
    t_cpa = today.get("cpa")
    if target_cpa is not None and t_cpa is not None and target_cpa > 0:
        if t_cpa > 1.2 * target_cpa:
            up_pct = ((t_cpa / target_cpa) - 1) * 100
            alerts.append(
                GuardrailAlert(
                    code="CPA_HIGH",
                    severity="critical",
                    message=f"CPA high: today ${t_cpa:.2f} vs target ${target_cpa:.2f} (+{up_pct:.1f}%)",
                    suggested_action="Pause worst-performing ads/ad sets; reduce bid cap or tighten audience.",
                )
            )

    # Helpful info when no alerts
    if not alerts:
        alerts.append(
            GuardrailAlert(
                code="OK",
                severity="info",
                message=f"No guardrail breaches for campaign {campaign_id}.",
                suggested_action="Continue monitoring.",
            )
        )

    return alerts

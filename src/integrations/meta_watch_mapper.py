from __future__ import annotations

from typing import Any, Dict, List, Optional


def to_experiment_result(
    *,
    project_id: str,
    timestamp: str,
    campaign_id: str,
    guardrails: Dict[str, Any],
    today_metrics: Dict[str, Any],
    trailing_metrics: Dict[str, Any],
    alerts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Deterministic mapper: Meta watch metrics -> internal experiment_results shape.

    Keep schema stable; reflection/planning can depend on these keys.
    """
    return {
        "source": "meta_watch",
        "project_id": project_id,
        "timestamp": timestamp,
        "campaign_id": campaign_id,
        "guardrails": guardrails,
        "windows": {
            "today": today_metrics,
            "trailing_7d": trailing_metrics,
        },
        "alerts": alerts,
    }

"""Planning helpers for plan/execute/verify mode."""

from __future__ import annotations

from typing import Any, Dict, List


def default_plan_template(decision: str) -> Dict[str, Any]:
    """Deterministic fallback plan if LLM planning fails."""
    if decision in ("reflect",):
        steps = [
            {"id": "s_reflect", "action": "reflection", "success": "verification.threshold_status set"},
            {"id": "s_adjust", "action": "adjustment", "success": "config_history appended"},
            {"id": "s_save", "action": "save", "success": "state saved"},
        ]
    else:
        # initialize/enrich/continue
        steps = [
            {"id": "s_discovery", "action": "discovery", "success": "knowledge_facts has product_description and target_budget"},
            {"id": "s_collect", "action": "data_collection", "success": "historical_data.metadata exists"},
            {"id": "s_insight", "action": "insight", "success": "current_strategy.insights exists"},
            {"id": "s_creatives", "action": "creative_generation", "success": "artifacts.creatives exists"},
            {"id": "s_campaign", "action": "campaign_setup", "success": "current_config exists"},
            {"id": "s_save", "action": "save", "success": "state saved"},
        ]

    return {
        "objective": "Run marketing agent workflow",
        "version": 1,
        "decision": decision,
        "steps": steps,
    }

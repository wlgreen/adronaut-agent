"""Planning helpers for plan/execute/verify mode.

The "planner" produces a TODO checklist (a JSON array of steps). We wrap it into
an internal plan object that the graph can execute.
"""

from __future__ import annotations

from typing import Any, Dict, List


ALLOWED_ACTIONS = {
    "discovery",
    "data_collection",
    "insight",
    "creative_generation",
    "campaign_setup",
    "reflection",
    "adjustment",
    "save",
}


def default_todo(decision: str) -> List[Dict[str, Any]]:
    """Deterministic fallback TODO list if LLM planning fails."""
    if decision in ("reflect",):
        return [
            {
                "id": "s_reflect",
                "action": "reflection",
                "rationale": "Assess performance vs thresholds and diagnose causes.",
                "success": "verification.threshold_status set",
                "requires_approval": False,
            },
            {
                "id": "s_adjust",
                "action": "adjustment",
                "rationale": "Generate a safe patch config (no live changes).",
                "success": "config_history appended",
                "requires_approval": True,
            },
            {
                "id": "s_save",
                "action": "save",
                "rationale": "Persist state for resumability.",
                "success": "state saved",
                "requires_approval": False,
            },
        ]

    # initialize/enrich/continue
    return [
        {
            "id": "s_discovery",
            "action": "discovery",
            "rationale": "Infer product + goals and fill missing context.",
            "success": "knowledge_facts has product_description and target_budget",
            "requires_approval": False,
        },
        {
            "id": "s_collect",
            "action": "data_collection",
            "rationale": "Load historical/experiment data into normalized tables.",
            "success": "historical_data.metadata exists",
            "requires_approval": False,
        },
        {
            "id": "s_insight",
            "action": "insight",
            "rationale": "Create insights → strategy mapping.",
            "success": "current_strategy.insights exists",
            "requires_approval": False,
        },
        {
            "id": "s_creatives",
            "action": "creative_generation",
            "rationale": "Generate demo-quality creative prompts for key combos.",
            "success": "artifacts.creatives exists",
            "requires_approval": False,
        },
        {
            "id": "s_campaign",
            "action": "campaign_setup",
            "rationale": "Generate platform configs; no live deployment.",
            "success": "current_config exists",
            "requires_approval": True,
        },
        {
            "id": "s_save",
            "action": "save",
            "rationale": "Persist state for resumability.",
            "success": "state saved",
            "requires_approval": False,
        },
    ]


def default_plan_template(decision: str) -> Dict[str, Any]:
    """Wrap the default TODO list into an internal plan object."""
    return {
        "objective": "Run marketing agent workflow",
        "version": 1,
        "decision": decision,
        "steps": default_todo(decision),
    }


def normalize_todo_list(todo: Any) -> List[Dict[str, Any]]:
    """Validate and normalize a planner-produced TODO list.

    Returns a list of step dicts with required keys.
    Raises ValueError with an actionable message on invalid input.
    """
    if not isinstance(todo, list):
        raise ValueError("Planner output must be a JSON array of steps")

    out: List[Dict[str, Any]] = []
    for i, step in enumerate(todo):
        if not isinstance(step, dict):
            raise ValueError(f"Step {i} must be an object")

        step_id = step.get("id") or f"s_{i+1}"
        action = step.get("action")
        if action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"Step {step_id}: invalid action '{action}'. Allowed: {sorted(ALLOWED_ACTIONS)}"
            )

        rationale = step.get("rationale")
        success = step.get("success")
        if not rationale or not isinstance(rationale, str):
            raise ValueError(f"Step {step_id}: missing 'rationale' string")
        if not success or not isinstance(success, str):
            raise ValueError(f"Step {step_id}: missing 'success' string")

        requires_approval = bool(step.get("requires_approval", False))

        out.append(
            {
                "id": step_id,
                "action": action,
                "rationale": rationale,
                "success": success,
                "requires_approval": requires_approval,
            }
        )

    if not out:
        raise ValueError("Planner produced an empty TODO list")

    return out

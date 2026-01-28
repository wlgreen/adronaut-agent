"""Plan/Execute/Verify nodes (agentic mode)."""

from __future__ import annotations

import json
from typing import Any, Dict

from .state import AgentState
from .planning import default_plan_template, normalize_todo_list
from ..modules.creative_generator import generate_creative_prompts
from ..modules.creative_rater import rate_creative_prompt
from ..llm.gemini import get_gemini


PLANNER_SYSTEM = """You are a planning agent for an ads/marketing automation product.

Create a TODO checklist (a JSON array of steps) to go from inputs → artifacts → an actionable campaign config.

Rules:
- Output STRICT JSON.
- Output MUST be a JSON ARRAY (not an object).
- Steps must be small and executable.
- Use only these actions:
  discovery, data_collection, insight, creative_generation, campaign_setup, reflection, adjustment, save
- Each step must include: id, action, rationale, success, requires_approval.
- Set requires_approval=true for any step that could spend money or push changes to Meta.
"""


def _plan_prompt(state: AgentState) -> str:
    file_types = [fa.get('type') for fa in state.get('file_analyses', [])]
    return json.dumps({
        "project_loaded": state.get("project_loaded"),
        "decision": state.get("decision"),
        "current_phase": state.get("current_phase"),
        "iteration": state.get("iteration"),
        "file_types": file_types,
        "known_facts": list((state.get("knowledge_facts") or {}).keys())[:30],
        "has_config": bool(state.get("current_config")),
        "has_strategy": bool(state.get("current_strategy")),
        "goal": "Demo an agentic workflow: analyze data -> generate creatives -> produce an ad plan/config; then iterate based on results.",
    }, indent=2)


def planning_node(state: AgentState) -> AgentState:
    """Create or refresh a plan.

    Planner output is a TODO list (JSON array). Internally we wrap it into
    state["plan"] = {"steps": [...], ...}.

    If state already has a valid plan with steps (e.g., pre-seeded), we reuse it.
    """
    decision = state.get("decision") or "initialize"

    existing = state.get("plan")
    if isinstance(existing, dict) and isinstance(existing.get("steps"), list) and existing["steps"]:
        state["plan_step_index"] = 0
        state["approval_status"] = None
        state["requires_approval"] = False
        state.setdefault("artifacts", {})
        state.setdefault("verification", {})
        state["messages"].append("Plan reused")
        return state

    gemini = get_gemini()

    try:
        todo = gemini.generate_json(
            prompt=_plan_prompt(state),
            system_instruction=PLANNER_SYSTEM,
            temperature=0.2,
            task_name="Planning",
        )
        steps = normalize_todo_list(todo)
        state["plan"] = {
            "objective": "Run marketing agent workflow",
            "version": 1,
            "decision": decision,
            "steps": steps,
        }
    except Exception:
        state["plan"] = default_plan_template(decision)

    state["plan_step_index"] = 0
    state["approval_status"] = None
    state["requires_approval"] = False
    state.setdefault("artifacts", {})
    state.setdefault("verification", {})
    state["todo_printed"] = False
    state["messages"].append("Plan created")
    return state


def execute_step_node(state: AgentState) -> AgentState:
    """Execute the current plan step by dispatching to existing nodes/modules."""
    plan = state.get("plan") or {}
    steps = plan.get("steps") or []
    idx = int(state.get("plan_step_index", 0))

    # Print the TODO list exactly once, before the first step executes.
    if steps and idx == 0 and not state.get("todo_printed", False):
        print("\n" + "=" * 60)
        print("  TODO CHECKLIST (PLAN)")
        print("=" * 60)
        todo_out = [
            {
                "id": s.get("id"),
                "action": s.get("action"),
                "requires_approval": bool(s.get("requires_approval")),
                "success": s.get("success"),
            }
            for s in steps
        ]
        print(json.dumps(todo_out, indent=2))
        print()
        state["todo_printed"] = True

    if idx >= len(steps):
        state["messages"].append("Plan complete")
        return state

    step = steps[idx]
    step_id = step.get("id", f"step_{idx}")
    action = step.get("action")

    state["current_step_id"] = step_id
    state.setdefault("artifacts", {})

    # Certain actions should require approval in a real product (spend money)
    if action in ("campaign_setup", "adjustment"):
        # For MVP: generate configs without pushing live changes.
        state["requires_approval"] = True

    # Dispatch to existing nodes via imports to avoid rewriting logic.
    from .nodes import (
        discovery_node,
        data_collection_node,
        insight_node,
        campaign_setup_node,
        reflection_node,
        adjustment_node,
        save_state_node,
    )

    if action == "discovery":
        state = discovery_node(state)
    elif action == "data_collection":
        state = data_collection_node(state)
    elif action == "insight":
        state = insight_node(state)
    elif action == "campaign_setup":
        state = campaign_setup_node(state)
    elif action == "reflection":
        state = reflection_node(state)
    elif action == "adjustment":
        state = adjustment_node(state)
    elif action == "creative_generation":
        # Minimal creative generation: generate prompts for a single test combo.
        user_inputs = state.get("user_inputs", {})
        product_desc = user_inputs.get("product_description") or state.get("knowledge_facts", {}).get("product_description", {}).get("value")
        if not product_desc:
            state["errors"].append("creative_generation: missing product_description")
        else:
            combo = {
                "combo_id": "demo_combo_1",
                "platform": "Meta",
                "audience": user_inputs.get("target_audience", "General"),
                "creative_style": "Professional",
            }
            gen = generate_creative_prompts(test_combination=combo, strategy=state.get("current_strategy", {}), user_inputs={"product_description": product_desc})
            rating = rate_creative_prompt(
                original_prompt=gen.get("visual_prompt", ""),
                reviewed_prompt=gen.get("visual_prompt", ""),
                product_description=product_desc,
                required_keywords=None,
                brand_name=None,
                original_requirements={"platform": "Meta"},
            )
            state["artifacts"][step_id] = {"creative": gen, "rating": rating}
            state["messages"].append("Creative prompts generated")
    elif action == "save":
        state = save_state_node(state)
    else:
        state["errors"].append(f"Unknown plan action: {action}")

    return state


def verify_step_node(state: AgentState) -> AgentState:
    """Verify step outputs; decide continue vs replan."""
    plan = state.get("plan") or {}
    steps = plan.get("steps") or []
    idx = int(state.get("plan_step_index", 0))

    if idx >= len(steps):
        state["verification"] = {"status": "done"}
        return state

    step = steps[idx]
    action = step.get("action")

    ok = True
    notes = []

    # Light-weight checks (MVP)
    if action == "discovery":
        kf = state.get("knowledge_facts", {})
        ok = bool(kf.get("product_description") and kf.get("target_budget"))
        if not ok:
            notes.append("Missing product_description/target_budget")
    if action == "insight":
        ok = bool(state.get("current_strategy"))
        if not ok:
            notes.append("Strategy missing")
    if action == "campaign_setup":
        ok = bool(state.get("current_config"))
        if not ok:
            notes.append("Config missing")

    state["verification"] = {
        "step": step.get("id"),
        "action": action,
        "ok": ok,
        "notes": notes,
    }

    if ok:
        state["plan_step_index"] = idx + 1
        state["messages"].append(f"✓ Verified {action}")
    else:
        # MVP behavior: replan once by resetting plan
        state["messages"].append(f"✗ Verification failed for {action}: {notes}")
        state["plan_step_index"] = 0
        state["plan"] = None

    return state

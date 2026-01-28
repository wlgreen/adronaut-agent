"""Combined Planning node (routing + plan generation).

Single LLM call that:
1. Analyzes state and decides the approach (initialize/reflect/enrich/continue)
2. Produces a TODO checklist of steps to execute
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .state import AgentState
from .planning import default_plan_template, normalize_todo_list
from ..modules.creative_generator import generate_creative_prompts
from ..modules.creative_rater import rate_creative_prompt
from ..llm import gemini as gemini_mod


PLANNER_SYSTEM = """You are a planning agent for an ads/marketing automation product.

Your job is to:
1. Analyze the current project state and decide what approach to take
2. Create a TODO checklist (JSON array of steps) to execute

Decision types:
- "initialize": New project - start data collection, strategy building, campaign setup
- "reflect": Project exists + experiment results uploaded - analyze and optimize
- "enrich": Project exists + additional context uploaded - incorporate into strategy
- "continue": Project exists but incomplete - continue from current phase

Rules for the plan:
- Output STRICT JSON with both "decision" and "steps" fields
- Steps must be small and executable
- Use only these actions: discovery, data_collection, insight, creative_generation, campaign_setup, reflection, adjustment, save
- Each step must include: id, action, rationale, success, requires_approval
- Set requires_approval=true for any step that could spend money or push changes externally
"""


PLANNER_PROMPT_TEMPLATE = """
Analyze this context and create an execution plan:

PROJECT STATE:
- Project loaded: {project_loaded}
- Current phase: {current_phase}
- Iteration: {iteration}
- Has strategy: {has_strategy}
- Has config: {has_config}
- Previous experiments: {num_experiments}

UPLOADED FILES:
{file_analyses}

KNOWN FACTS:
{known_facts}

Respond with JSON in this exact format:
{{
  "decision": "initialize" | "reflect" | "enrich" | "continue",
  "reasoning": "Why you chose this approach",
  "steps": [
    {{"id": "s1", "action": "discovery", "rationale": "...", "success": "...", "requires_approval": false}},
    {{"id": "s2", "action": "data_collection", "rationale": "...", "success": "...", "requires_approval": false}},
    ...
  ]
}}
"""


def _build_planner_prompt(state: AgentState) -> str:
    """Build the prompt for the combined router+planner."""
    file_analyses = state.get("file_analyses", [])
    file_analyses_str = "\n".join([
        f"- {fa.get('file_name', 'unknown')}: {fa.get('type', 'unknown')}, {fa.get('row_count', 0)} rows"
        for fa in file_analyses
    ]) or "No files uploaded"

    known_facts = state.get("knowledge_facts", {})
    facts_str = "\n".join([
        f"- {k}: {v.get('value', '')[:50]}... (confidence: {v.get('confidence', 0):.0%})"
        for k, v in list(known_facts.items())[:10]
    ]) or "None yet"

    return PLANNER_PROMPT_TEMPLATE.format(
        project_loaded=state.get("project_loaded", False),
        current_phase=state.get("current_phase", "initialized"),
        iteration=state.get("iteration", 0),
        has_strategy=bool(state.get("current_strategy")),
        has_config=bool(state.get("current_config")),
        num_experiments=len(state.get("experiment_results", [])),
        file_analyses=file_analyses_str,
        known_facts=facts_str,
    )


def planning_node(state: AgentState) -> AgentState:
    """Combined routing + planning node.

    Single LLM call that decides the approach and produces a TODO list.
    If state already has a valid plan, reuses it (for resumption).
    """
    # Check for existing valid plan (resumption case)
    existing = state.get("plan")
    if isinstance(existing, dict) and isinstance(existing.get("steps"), list) and existing["steps"]:
        # Reuse existing plan
        state["plan_step_index"] = state.get("plan_step_index", 0)
        state["approval_status"] = None
        state["requires_approval"] = False
        state.setdefault("artifacts", {})
        state.setdefault("verification", {})
        state["messages"].append("Plan reused (resuming)")
        return state

    # Make combined routing + planning LLM call
    gemini = gemini_mod.get_gemini()

    try:
        result = gemini.generate_json(
            prompt=_build_planner_prompt(state),
            system_instruction=PLANNER_SYSTEM,
            temperature=0.2,
            task_name="Planning",
        )

        # Extract decision (routing)
        decision = result.get("decision", "initialize")
        reasoning = result.get("reasoning", "")

        # Extract and normalize steps
        steps = normalize_todo_list(result.get("steps", []))

        state["decision"] = decision
        state["decision_reasoning"] = reasoning
        state["plan"] = {
            "objective": "Run marketing agent workflow",
            "version": 1,
            "decision": decision,
            "reasoning": reasoning,
            "steps": steps,
        }

        state["messages"].append(f"Decision: {decision}")
        state["messages"].append(f"Reasoning: {reasoning}")

    except Exception as e:
        # Fallback to default plan
        state["decision"] = "initialize"
        state["decision_reasoning"] = f"Fallback due to error: {e}"
        state["plan"] = default_plan_template("initialize")
        state["messages"].append(f"Planning fallback: {e}")

    state["plan_step_index"] = 0
    state["approval_status"] = None
    state["requires_approval"] = False
    state.setdefault("artifacts", {})
    state.setdefault("verification", {})
    state["todo_printed"] = False
    state["messages"].append("Plan created")

    state["cycle_num"] += 1
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
        print(f"  Decision: {plan.get('decision', 'N/A')}")
        print(f"  Reasoning: {plan.get('reasoning', 'N/A')[:80]}...")
        print()
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

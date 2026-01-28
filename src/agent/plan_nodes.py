"""Combined Planning node (routing + plan generation).

Single LLM call that:
1. Analyzes state and decides the approach (initialize/reflect/enrich/continue)
2. Produces a TODO checklist of steps to execute

Option A refactor: actions are dispatched via a registry of pluggable skills.
"""

from __future__ import annotations

import json
from typing import Dict

from .actions import build_action_registry, list_available_actions
from .state import AgentState
from .planning import default_plan_template, normalize_todo_list
from ..llm import gemini as gemini_mod
from ..storage.analysis_store import summarize_cached_insights_for_planner


PLANNER_SYSTEM_TEMPLATE = """You are a planning agent for an ads/marketing automation product.

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
- Use ONLY the available actions listed below
- Each step must include: id, action, rationale, success, requires_approval
- Set requires_approval=true for any step that could spend money or push changes externally

AVAILABLE ACTIONS:
{available_actions}
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

CACHED INSIGHTS (JSON, from previous runs if available):
{cached_insights}

LATEST REFLECTION (JSON, if available):
{latest_reflection}

REPO SEARCH SUMMARY (JSON, if available):
{repo_search}

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


_ACTION_REGISTRY: Dict[str, object] | None = None


def _get_action_registry() -> Dict[str, object]:
    global _ACTION_REGISTRY
    if _ACTION_REGISTRY is None:
        _ACTION_REGISTRY = build_action_registry()
    return _ACTION_REGISTRY


def _build_planner_prompt(state: AgentState) -> str:
    """Build the prompt for the combined router+planner."""
    file_analyses = state.get("file_analyses", [])
    file_analyses_str = "\n".join(
        [
            f"- {fa.get('file_name', 'unknown')}: {fa.get('type', 'unknown')}, {fa.get('row_count', 0)} rows"
            for fa in file_analyses
        ]
    ) or "No files uploaded"

    known_facts = state.get("knowledge_facts", {})
    facts_str = "\n".join(
        [
            f"- {k}: {str(v.get('value', ''))[:50]}... (confidence: {v.get('confidence', 0):.0%})"
            for k, v in list(known_facts.items())[:10]
        ]
    ) or "None yet"

    cached_insights = "[]"
    try:
        cached_insights = summarize_cached_insights_for_planner(state.get("project_id", ""))
    except Exception:
        cached_insights = "[]"

    latest_reflection = "null"
    try:
        lr = (state.get("knowledge_facts", {}) or {}).get("latest_reflection", {}).get("value")
        latest_reflection = json.dumps(lr, indent=2) if lr is not None else "null"
    except Exception:
        latest_reflection = "null"

    repo_search = "null"
    try:
        rs = (state.get("knowledge_facts", {}) or {}).get("repo_search", {}).get("value")
        repo_search = json.dumps(rs, indent=2) if rs is not None else "null"
    except Exception:
        repo_search = "null"

    return PLANNER_PROMPT_TEMPLATE.format(
        project_loaded=state.get("project_loaded", False),
        current_phase=state.get("current_phase", "initialized"),
        iteration=state.get("iteration", 0),
        has_strategy=bool(state.get("current_strategy")),
        has_config=bool(state.get("current_config")),
        num_experiments=len(state.get("experiment_results", [])),
        file_analyses=file_analyses_str,
        known_facts=facts_str,
        cached_insights=cached_insights,
        latest_reflection=latest_reflection,
        repo_search=repo_search,
    )


def planning_node(state: AgentState) -> AgentState:
    """Combined routing + planning node.

    Single LLM call that decides the approach and produces a TODO list.
    If state already has a valid plan, reuses it (for resumption).
    """
    # Check for existing valid plan (resumption case)
    existing = state.get("plan")
    if isinstance(existing, dict) and isinstance(existing.get("steps"), list) and existing["steps"]:
        state["plan_step_index"] = state.get("plan_step_index", 0)
        state["approval_status"] = None
        state["requires_approval"] = False
        state.setdefault("artifacts", {})
        state.setdefault("verification", {})
        state["messages"].append("Plan reused (resuming)")
        return state

    registry = _get_action_registry()
    available_actions = "\n".join(list_available_actions(registry))
    planner_system = PLANNER_SYSTEM_TEMPLATE.format(available_actions=available_actions)

    gemini = gemini_mod.get_gemini()

    try:
        result = gemini.generate_json(
            prompt=_build_planner_prompt(state),
            system_instruction=planner_system,
            temperature=0.2,
            task_name="Planning",
        )

        decision = result.get("decision", "initialize")
        reasoning = result.get("reasoning", "")
        steps = normalize_todo_list(result.get("steps", []))

        # If previous run requested forced repo_search (e.g., config quality gate failure), prepend it.
        frs = state.pop("force_repo_search", None)
        if isinstance(frs, dict):
            queries = frs.get("queries") or []
            if steps and steps[0].get("action") != "repo_search":
                steps = [
                    {
                        "id": "auto_repo_search",
                        "action": "repo_search",
                        "rationale": frs.get("reason") or "Investigate codebase/schema to fix verification failure",
                        "success": "Find relevant code references and schema expectations",
                        "requires_approval": False,
                        "search": queries,
                    }
                ] + steps
            elif not steps:
                steps = [
                    {
                        "id": "auto_repo_search",
                        "action": "repo_search",
                        "rationale": frs.get("reason") or "Investigate codebase/schema to fix verification failure",
                        "success": "Find relevant code references and schema expectations",
                        "requires_approval": False,
                        "search": queries,
                    }
                ]

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
    """Execute the current plan step by dispatching to action skills."""
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

    registry = _get_action_registry()
    skill = registry.get(action)

    if skill is None:
        state.setdefault("errors", []).append(f"Unknown plan action: {action}")
        return state

    # Approval flag: allow planner to request it, and allow the skill to enforce it.
    requires_approval = bool(step.get("requires_approval"))
    try:
        requires_approval = requires_approval or bool(skill.requires_approval(state))
    except Exception:
        # Be robust; approval should never crash execution.
        pass

    if requires_approval:
        state["requires_approval"] = True

    # Hard approval gate: do not execute until approved.
    if state.get("requires_approval") and state.get("approval_status") != "approved":
        state["approval_status"] = "pending"
        state.setdefault("messages", []).append(
            f"Approval required for action '{action}'. Re-run with ADRONAUT_APPROVE=1 to approve and continue."
        )
        return state

    state = skill.run(state)
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

    registry = _get_action_registry()
    skill = registry.get(action)

    # If approval is pending, don't verify/advance; just persist and stop.
    if state.get("approval_status") == "pending":
        state["verification"] = {
            "step": step.get("id"),
            "action": action,
            "ok": False,
            "notes": ["Pending approval"],
        }
        return state

    # Unknown action => fail and replan
    if skill is None:
        ok = False
        notes = [f"Unknown plan action: {action}"]
    else:
        try:
            ok, notes = skill.verify(state)
        except Exception as e:
            ok = False
            notes = [f"Verification error: {e}"]

    state["verification"] = {
        "step": step.get("id"),
        "action": action,
        "ok": bool(ok),
        "notes": notes,
    }

    if ok:
        state["plan_step_index"] = idx + 1
        state["messages"].append(f"✓ Verified {action}")
    else:
        # If config validation failed, hint planner to run repo_search next.
        if action in ("campaign_setup", "adjustment"):
            state["force_repo_search"] = {
                "queries": ["generate_campaign_config", "current_config", "summary", "daily_budget", "schema"],
                "reason": f"{action} produced invalid config: {notes}",
            }
        state["messages"].append(f"✗ Verification failed for {action}: {notes}")
        state["plan_step_index"] = 0
        state["plan"] = None

    return state

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .skills import BaseSkill
from ..state import AgentState


def _summarize_reflection_for_planner(state: AgentState) -> Dict[str, Any]:
    """Best-effort extraction of reflection outcomes into a compact planner-friendly summary.

    We keep this intentionally schema-light because underlying module outputs may evolve.
    """
    summary: Dict[str, Any] = {}

    # Common places where reflection outputs might land
    if state.get("threshold_status") is not None:
        summary["threshold_status"] = state.get("threshold_status")

    if state.get("best_performers"):
        summary["best_performers"] = state.get("best_performers")

    # Recent experiment results (cap)
    exp_results = state.get("experiment_results") or []
    if isinstance(exp_results, list) and exp_results:
        summary["recent_experiment_results_count"] = len(exp_results)
        summary["recent_experiment_results_tail"] = exp_results[-3:]

    # Metrics timeline tail (cap)
    mt = state.get("metrics_timeline") or []
    if isinstance(mt, list) and mt:
        summary["recent_metrics_tail"] = mt[-3:]

    # Patch history tail (cap)
    ph = state.get("patch_history") or []
    if isinstance(ph, list) and ph:
        summary["recent_patches_tail"] = ph[-3:]

    # Heuristic recommended next actions
    recommended: List[str] = []
    if exp_results:
        recommended.append("adjustment")
    if state.get("threshold_status") == "not_met":
        recommended.append("creative_generation")
    summary["recommended_next_actions"] = list(dict.fromkeys(recommended))

    return summary


@dataclass
class ReflectionSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="reflection",
            description=(
                "Analyze experiment_results and summarize performance; write latest_reflection fact for the planner "
                "and force a replan so next steps adapt to results."
            ),
        )

    def run(self, state: AgentState) -> AgentState:
        from .. import nodes as agent_nodes

        state = agent_nodes.reflection_node(state)

        # Summarize into knowledge_facts so the planner can reason over a compact view.
        summary = _summarize_reflection_for_planner(state)
        state.setdefault("knowledge_facts", {})
        state["knowledge_facts"]["latest_reflection"] = {
            "value": summary,
            "confidence": 0.7,
            "source": "reflection",
        }

        state.setdefault("messages", []).append("Reflection summarized into knowledge_facts.latest_reflection")

        # Force replan so planning_node incorporates the new reflection summary.
        state["plan"] = None
        state["plan_step_index"] = 0
        state.setdefault("messages", []).append("Reflection complete; forcing replan")

        return state

    def verify(self, state: AgentState) -> Tuple[bool, List[str]]:
        # Best-effort: reflection may succeed even without strong signals.
        lf = state.get("knowledge_facts", {}).get("latest_reflection", {}).get("value")
        if lf is None:
            return False, ["reflection: missing latest_reflection summary"]
        return True, []

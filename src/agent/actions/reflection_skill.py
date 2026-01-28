from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .skills import BaseSkill
from ..state import AgentState


def _summarize_reflection_for_planner(state: AgentState) -> Dict[str, Any]:
    """Extract reflection outcomes into a compact, stable schema for planning.

    Goal: make post-results replanning high quality and low ambiguity.
    """
    summary: Dict[str, Any] = {
        "iteration": state.get("iteration", 0),
        "current_phase": state.get("current_phase"),
        "threshold_status": state.get("threshold_status"),
    }

    # Prefer the structured analysis produced by reflection_node
    analysis = (state.get("node_outputs") or {}).get("reflection_analysis")
    if isinstance(analysis, dict) and analysis:
        summary["threshold_met"] = analysis.get("threshold_met")
        summary["threshold_gap"] = analysis.get("threshold_gap")
        summary["performance_summary"] = analysis.get("performance_summary")
        summary["winners"] = analysis.get("winners")
        summary["losers"] = analysis.get("losers")

        var = analysis.get("variation_analysis")
        if isinstance(var, list) and var:
            summary["top_variations"] = var[:3]

        insights = analysis.get("insights")
        if isinstance(insights, list) and insights:
            summary["insights"] = insights[:5]

        recs = analysis.get("recommendations")
        if isinstance(recs, list) and recs:
            summary["recommendations"] = recs[:5]

    # Add easy-to-use summary fields
    if state.get("best_performers"):
        summary["best_performers"] = state.get("best_performers")

    exp_results = state.get("experiment_results") or []
    if isinstance(exp_results, list) and exp_results:
        summary["recent_experiment_results_count"] = len(exp_results)

    # Recommended next actions (planner still decides)
    recommended: List[str] = []
    if exp_results:
        recommended.append("adjustment")
    # If threshold not met, often need creative refresh or targeting tweaks
    if (analysis or {}).get("threshold_met") is False or state.get("threshold_status") == "not_met":
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

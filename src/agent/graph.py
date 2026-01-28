"""
LangGraph workflow assembly with resumption support

Uses an agentic Plan → Execute → Verify loop.
Router + Planning are merged into a single planning_node.
"""

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    load_context_node,
    analyze_files_node,
    save_state_node,
)
from .plan_nodes import planning_node, execute_step_node, verify_step_node


def should_skip_to_resume_point(state: AgentState) -> str:
    """Determine if we should skip directly to resume point."""
    is_resuming = state.get("is_resuming", False)
    last_completed = state.get("last_completed_node")
    completed_nodes = state.get("completed_nodes", [])

    if not is_resuming or not last_completed:
        return "normal"
    if last_completed == "load_context":
        return "normal"
    # If we've already done analyze_files and planning, resume into planning
    if "analyze_files" in completed_nodes and "planning" in completed_nodes:
        return "resume"
    return "normal"


def _continue_or_execute(state: AgentState) -> str:
    """After planning/verify, decide next node."""
    plan = state.get("plan") or {}
    steps = plan.get("steps") or []
    idx = int(state.get("plan_step_index", 0))

    # If planning cleared plan due to failure, replan
    if not steps:
        return "planning"

    if idx >= len(steps):
        return "save"

    return "execute_step"


def create_campaign_agent_graph():
    """Create and compile the campaign setup agent graph."""
    workflow = StateGraph(AgentState)

    # Base nodes
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("analyze_files", analyze_files_node)

    # Save node
    workflow.add_node("save", save_state_node)

    # Agentic loop nodes (planning now includes routing)
    workflow.add_node("planning", planning_node)
    workflow.add_node("execute_step", execute_step_node)
    workflow.add_node("verify_step", verify_step_node)

    # Entry point
    workflow.set_entry_point("load_context")

    # Flow: load_context → analyze_files (or resume to planning)
    workflow.add_conditional_edges(
        "load_context",
        should_skip_to_resume_point,
        {"normal": "analyze_files", "resume": "planning"},
    )

    # analyze_files → planning (merged router + planner)
    workflow.add_edge("analyze_files", "planning")

    # Planning → Execute → Verify loop
    workflow.add_conditional_edges(
        "planning",
        _continue_or_execute,
        {"planning": "planning", "execute_step": "execute_step", "save": "save"},
    )
    workflow.add_edge("execute_step", "verify_step")
    workflow.add_conditional_edges(
        "verify_step",
        _continue_or_execute,
        {"planning": "planning", "execute_step": "execute_step", "save": "save"},
    )

    workflow.add_edge("save", END)

    return workflow.compile()


_graph = None


def get_campaign_agent():
    global _graph
    if _graph is None:
        _graph = create_campaign_agent_graph()
    return _graph

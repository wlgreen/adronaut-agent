"""
LangGraph workflow assembly with resumption support

Now supports an agentic Plan → Execute → Verify loop.
"""

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    load_context_node,
    analyze_files_node,
    user_input_node,
    discovery_node,
    data_collection_node,
    insight_node,
    campaign_setup_node,
    reflection_node,
    adjustment_node,
    save_state_node,
)
from .router import router_node, get_next_node, get_resume_node
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
    if "analyze_files" in completed_nodes and "router" in completed_nodes:
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
    workflow.add_node("router", router_node)

    # Existing nodes (kept as reusable tools + backward compatibility)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("data_collection", data_collection_node)
    workflow.add_node("insight", insight_node)
    workflow.add_node("campaign_setup", campaign_setup_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("adjustment", adjustment_node)
    workflow.add_node("save", save_state_node)

    # Agentic loop nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("execute_step", execute_step_node)
    workflow.add_node("verify_step", verify_step_node)

    workflow.set_entry_point("load_context")

    workflow.add_conditional_edges(
        "load_context",
        should_skip_to_resume_point,
        {"normal": "analyze_files", "resume": "router"},
    )

    workflow.add_edge("analyze_files", "router")

    # Router now defaults into planning
    workflow.add_conditional_edges(
        "router",
        get_next_node,
        {
            "discovery": "planning",
            "user_input": "planning",
            "data_collection": "planning",
            "insight": "planning",
            "campaign_setup": "planning",
            "reflection": "planning",
            "adjustment": "planning",
            "save": "save",
        },
    )

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

"""
LangGraph workflow assembly with resumption support
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


def should_skip_to_resume_point(state: AgentState) -> str:
    """
    Determine if we should skip directly to resume point.
    This optimizes resumption by skipping already-completed nodes.

    Returns:
        "resume" to skip to resume point, "normal" for normal flow
    """
    is_resuming = state.get("is_resuming", False)
    last_completed = state.get("last_completed_node")
    completed_nodes = state.get("completed_nodes", [])

    # If not resuming, follow normal flow
    if not is_resuming or not last_completed:
        return "normal"

    # If load_context is the last completed, continue normally
    if last_completed == "load_context":
        return "normal"

    # If we've already completed analyze_files and router, skip to resume point
    if "analyze_files" in completed_nodes and "router" in completed_nodes:
        return "resume"

    return "normal"


def create_campaign_agent_graph():
    """
    Create and compile the campaign setup agent graph

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize graph with state schema
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("analyze_files", analyze_files_node)
    workflow.add_node("router", router_node)
    workflow.add_node("discovery", discovery_node)  # New intelligent discovery node
    workflow.add_node("user_input", user_input_node)  # Kept for backward compatibility
    workflow.add_node("data_collection", data_collection_node)
    workflow.add_node("insight", insight_node)
    workflow.add_node("campaign_setup", campaign_setup_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("adjustment", adjustment_node)
    workflow.add_node("save", save_state_node)

    # Set entry point
    workflow.set_entry_point("load_context")

    # Conditional edge from load_context: skip to resume point or continue normally
    workflow.add_conditional_edges(
        "load_context",
        should_skip_to_resume_point,
        {
            "normal": "analyze_files",
            "resume": "router",  # Skip to router when resuming
        },
    )

    # Fixed edges for initial flow
    workflow.add_edge("analyze_files", "router")

    # Conditional routing from router based on decision
    workflow.add_conditional_edges(
        "router",
        get_next_node,
        {
            "discovery": "discovery",  # New intelligent discovery route
            "user_input": "user_input",  # Backward compatibility
            "data_collection": "data_collection",
            "insight": "insight",
            "campaign_setup": "campaign_setup",
            "reflection": "reflection",
            "adjustment": "adjustment",
            "save": "save",
        },
    )

    # Discovery flows to data collection
    workflow.add_edge("discovery", "data_collection")

    # User input flows to data collection (backward compatibility)
    workflow.add_edge("user_input", "data_collection")

    # Initialize flow edges
    workflow.add_edge("data_collection", "insight")
    workflow.add_edge("insight", "campaign_setup")
    workflow.add_edge("campaign_setup", "save")

    # Reflect flow edges
    workflow.add_edge("reflection", "adjustment")
    workflow.add_edge("adjustment", "save")

    # End after save
    workflow.add_edge("save", END)

    # Compile the graph
    return workflow.compile()


# Create singleton instance
_graph = None


def get_campaign_agent():
    """
    Get or create the campaign agent graph

    Returns:
        Compiled LangGraph workflow
    """
    global _graph
    if _graph is None:
        _graph = create_campaign_agent_graph()
    return _graph

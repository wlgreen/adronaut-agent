"""
LLM-based router for intelligent decision making
"""

from typing import Dict, Any
from functools import wraps
from ..llm.gemini import get_gemini
from .state import AgentState
from ..utils.progress import get_progress_tracker


def track_node(func):
    """Decorator to track node execution progress"""
    @wraps(func)
    def wrapper(state: AgentState) -> AgentState:
        tracker = get_progress_tracker()
        node_name = func.__name__.replace('_node', '')

        # Start tracking
        tracker.node_start(node_name)

        # Execute node
        result = func(state)

        # End tracking
        tracker.node_end(node_name, result)

        return result

    return wrapper


ROUTER_SYSTEM_INSTRUCTION = """You are an intelligent router for a campaign optimization agent.

Your job is to analyze the current project state and uploaded files to decide what action to take next.

Decision types:
- "initialize": No project exists yet. Start data collection, strategy building, and campaign setup.
- "reflect": Project exists and user uploaded experiment results. Analyze performance and optimize.
- "enrich": Project exists and user uploaded additional context data. Incorporate into strategy.
- "continue": Project exists but needs more work on current phase. Continue from where we left off.

Consider:
1. Does a project already exist? (project_loaded field)
2. What type of files were uploaded? (file_analyses)
3. What phase is the project in? (current_phase)
4. What's the iteration count? (iteration)

Be decisive and provide clear reasoning.
"""


ROUTER_PROMPT_TEMPLATE = """
Analyze the following context and decide the next action:

PROJECT STATE:
- Project loaded: {project_loaded}
- Current phase: {current_phase}
- Iteration: {iteration}
- Has strategy: {has_strategy}
- Has config: {has_config}
- Previous experiments: {num_experiments}

UPLOADED FILES:
{file_analyses}

Based on this context, what should we do next?

Respond with JSON in this exact format:
{{
  "decision": "initialize" | "reflect" | "enrich" | "continue",
  "reasoning": "Explain why you made this decision",
  "next_action": "Brief description of what to do next",
  "confidence": 0.0 to 1.0
}}
"""


@track_node
def router_node(state: AgentState) -> AgentState:
    """
    LLM-based router node that decides next action

    Args:
        state: Current agent state

    Returns:
        Updated state with routing decision
    """
    gemini = get_gemini()

    # Prepare context for LLM
    file_analyses_str = "\n".join([
        f"- File: {fa.get('file_name', 'unknown')}\n"
        f"  Type: {fa.get('type', 'unknown')}\n"
        f"  Rows: {fa.get('row_count', 0)}\n"
        f"  Columns: {fa.get('columns', [])}\n"
        f"  Metrics: {fa.get('metrics', {})}"
        for fa in state.get("file_analyses", [])
    ])

    # Build prompt
    prompt = ROUTER_PROMPT_TEMPLATE.format(
        project_loaded=state.get("project_loaded", False),
        current_phase=state.get("current_phase", "unknown"),
        iteration=state.get("iteration", 0),
        has_strategy=bool(state.get("current_strategy")),
        has_config=bool(state.get("current_config")),
        num_experiments=len(state.get("experiment_results", [])),
        file_analyses=file_analyses_str if file_analyses_str else "No files analyzed yet"
    )

    # Get decision from LLM
    try:
        response = gemini.generate_json(
            prompt=prompt,
            system_instruction=ROUTER_SYSTEM_INSTRUCTION,
            temperature=0.3,  # Lower temperature for more consistent decisions
            task_name="Router Decision",
        )

        # Update state with decision
        state["decision"] = response.get("decision")
        state["decision_reasoning"] = response.get("reasoning")
        state["next_action"] = response.get("next_action")

        # Add to messages
        state["messages"].append(f"Router decision: {response.get('decision')}")
        state["messages"].append(f"Reasoning: {response.get('reasoning')}")

    except Exception as e:
        state["errors"].append(f"Router error: {str(e)}")
        # Fallback to initialize if we can't make a decision
        state["decision"] = "initialize"
        state["decision_reasoning"] = "Fallback decision due to error"

    # Increment cycle counter
    state["cycle_num"] += 1

    return state


def get_next_node(state: AgentState) -> str:
    """
    Determine next node based on router decision

    Args:
        state: Current agent state with decision

    Returns:
        Next node name
    """
    decision = state.get("decision")

    if decision == "initialize":
        # Go through discovery to collect context with intelligent strategies
        return "discovery"
    elif decision == "reflect":
        # Go directly to reflection for performance analysis
        return "reflection"
    elif decision == "enrich":
        # Go through discovery to collect additional context using parallel search
        return "discovery"
    elif decision == "continue":
        # Continue based on current phase
        phase = state.get("current_phase")
        if phase == "initialized":
            return "insight"
        elif phase == "strategy_built":
            return "campaign_setup"
        elif phase == "awaiting_results":
            # Should actually be in reflect mode, but fallback
            return "save"
        elif phase == "optimizing":
            return "adjustment"
        else:
            return "discovery"
    else:
        # Default to discovery for safety
        return "discovery"

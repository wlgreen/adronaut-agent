"""
Agent state definitions for LangGraph
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class AgentState(TypedDict):
    """
    Complete state for the campaign setup agent.
    This state flows through all nodes in the LangGraph.
    """

    # ===== Session Metadata =====
    project_id: str
    session_id: str
    session_num: int
    cycle_num: int

    # ===== Uploaded Files (Current Session) =====
    uploaded_files: List[Dict[str, Any]]  # List of file paths
    file_analyses: List[Dict[str, Any]]  # Analyzed file data

    # ===== Router Decision =====
    decision: Optional[str]  # 'initialize', 'reflect', 'enrich', 'continue'
    decision_reasoning: Optional[str]
    next_action: Optional[str]  # Next node to execute

    # ===== Flow Tracking (for resumption) =====
    last_completed_node: Optional[str]  # Last successfully completed node
    completed_nodes: List[str]  # Ordered history of all completed nodes
    flow_status: str  # 'not_started', 'in_progress', 'completed', 'failed'
    current_executing_node: Optional[str]  # Currently executing node
    is_resuming: bool  # Whether this is a resumed flow
    force_restart: bool  # CLI flag to force restart even if resumption possible

    # ===== Project State (Loaded from DB) =====
    project_loaded: bool  # Whether project was loaded from DB
    current_phase: str  # 'initialized', 'strategy_built', 'awaiting_results', 'optimizing', 'completed'
    iteration: int

    # ===== Accumulated Data =====
    historical_data: Dict[str, Any]
    market_data: Dict[str, Any]
    user_inputs: Dict[str, Any]
    knowledge_facts: Dict[str, Dict[str, Any]]  # fact_key → {value, confidence, source}

    # ===== Strategy & Experiments =====
    current_strategy: Dict[str, Any]
    experiment_plan: Dict[str, Any]
    experiment_results: List[Dict[str, Any]]  # Grows with each iteration

    # ===== Campaign Configurations =====
    current_config: Dict[str, Any]
    config_history: List[Dict[str, Any]]  # All versions

    # ===== Decision History =====
    patch_history: List[Dict[str, Any]]  # All patches applied
    metrics_timeline: List[Dict[str, Any]]  # Performance over time

    # ===== Performance Tracking =====
    best_performers: Dict[str, Any]
    threshold_status: Optional[str]  # 'not_met', 'met', 'exceeded'

    # ===== Node Outputs (Intermediate) =====
    # Used to pass data between nodes
    node_outputs: Dict[str, Any]

    # ===== Errors & Messages =====
    errors: List[str]
    messages: List[str]


def create_initial_state(
    project_id: str,
    uploaded_files: List[Dict[str, Any]],
    session_num: int = 1
) -> AgentState:
    """
    Create initial agent state for a new session

    Args:
        project_id: UUID of the project
        uploaded_files: List of uploaded file info
        session_num: Session number

    Returns:
        Initialized AgentState
    """
    return AgentState(
        # Session metadata
        project_id=project_id,
        session_id="",  # Will be set after session creation
        session_num=session_num,
        cycle_num=0,

        # Uploaded files
        uploaded_files=uploaded_files,
        file_analyses=[],

        # Router decision
        decision=None,
        decision_reasoning=None,
        next_action=None,

        # Flow tracking
        last_completed_node=None,
        completed_nodes=[],
        flow_status="not_started",
        current_executing_node=None,
        is_resuming=False,
        force_restart=False,

        # Project state
        project_loaded=False,
        current_phase="initialized",
        iteration=0,

        # Accumulated data
        historical_data={},
        market_data={},
        user_inputs={},
        knowledge_facts={},

        # Strategy & experiments
        current_strategy={},
        experiment_plan={},
        experiment_results=[],

        # Campaign configurations
        current_config={},
        config_history=[],

        # Decision history
        patch_history=[],
        metrics_timeline=[],

        # Performance tracking
        best_performers={},
        threshold_status=None,

        # Node outputs
        node_outputs={},

        # Errors & messages
        errors=[],
        messages=[],
    )


def load_project_into_state(
    state: AgentState,
    project_data: Dict[str, Any]
) -> AgentState:
    """
    Load project data from database into state

    Args:
        state: Current agent state
        project_data: Project data from database

    Returns:
        Updated state with loaded project data
    """
    state["project_loaded"] = True
    state["current_phase"] = project_data.get("current_phase", "initialized")
    state["iteration"] = project_data.get("iteration", 0)

    # Load flow tracking
    state["last_completed_node"] = project_data.get("last_completed_node")
    state["completed_nodes"] = project_data.get("completed_nodes", [])
    state["flow_status"] = project_data.get("flow_status", "not_started")
    state["current_executing_node"] = project_data.get("current_executing_node")

    # Load accumulated data
    state["historical_data"] = project_data.get("historical_data", {})
    state["market_data"] = project_data.get("market_data", {})
    state["user_inputs"] = project_data.get("user_inputs", {})
    state["knowledge_facts"] = project_data.get("knowledge_facts", {})

    # Load strategy & experiments
    state["current_strategy"] = project_data.get("current_strategy", {})
    state["experiment_plan"] = project_data.get("experiment_plan", {})
    state["experiment_results"] = project_data.get("experiment_results", [])

    # Load campaign configurations
    state["current_config"] = project_data.get("current_config", {})
    state["config_history"] = project_data.get("config_history", [])

    # Load decision history
    state["patch_history"] = project_data.get("patch_history", [])
    state["metrics_timeline"] = project_data.get("metrics_timeline", [])

    # Load performance tracking
    state["best_performers"] = project_data.get("best_performers", {})
    state["threshold_status"] = project_data.get("threshold_status")

    return state


def state_to_project_dict(state: AgentState, include_knowledge_facts: bool = True) -> Dict[str, Any]:
    """
    Convert state to project dictionary for database storage

    Args:
        state: Current agent state
        include_knowledge_facts: Whether to include knowledge_facts (set False if DB not updated yet)

    Returns:
        Dictionary ready for database storage
    """
    project_dict = {
        "project_id": state["project_id"],
        "current_phase": state["current_phase"],
        "iteration": state["iteration"],

        # Flow tracking
        "last_completed_node": state.get("last_completed_node"),
        "completed_nodes": state.get("completed_nodes", []),
        "flow_status": state.get("flow_status", "not_started"),
        "current_executing_node": state.get("current_executing_node"),

        "historical_data": state["historical_data"],
        "market_data": state["market_data"],
        "user_inputs": state["user_inputs"],

        "current_strategy": state["current_strategy"],
        "experiment_plan": state["experiment_plan"],
        "experiment_results": state["experiment_results"],

        "current_config": state["current_config"],
        "config_history": state["config_history"],

        "patch_history": state["patch_history"],
        "metrics_timeline": state["metrics_timeline"],

        "best_performers": state["best_performers"],
        "threshold_status": state["threshold_status"],
    }

    # Only include knowledge_facts if requested (handles schema migration)
    if include_knowledge_facts:
        project_dict["knowledge_facts"] = state["knowledge_facts"]

    return project_dict

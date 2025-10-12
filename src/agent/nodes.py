"""
Core agent nodes for the LangGraph workflow
"""

import os
from typing import Dict, Any
from functools import wraps
from tavily import TavilyClient
from ..database.persistence import ProjectPersistence, SessionPersistence, CyclePersistence
from ..modules.data_loader import DataLoader
from ..modules.insight import generate_insights_and_strategy
from ..modules.campaign import generate_campaign_config
from ..modules.reflection import analyze_experiment_results, generate_patch_strategy
from .state import AgentState, load_project_into_state, state_to_project_dict
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


@track_node
def load_context_node(state: AgentState) -> AgentState:
    """
    Load project context from database if it exists

    Args:
        state: Current agent state

    Returns:
        Updated state with loaded project data
    """
    project_id = state["project_id"]

    # Try to load project from database
    project_data = ProjectPersistence.load_project(project_id)

    if project_data:
        # Project exists, load it into state
        state = load_project_into_state(state, project_data)
        state["messages"].append(f"Loaded existing project: {project_id}")
        state["session_num"] = len(project_data.get("config_history", [])) + 1
    else:
        # New project
        state["messages"].append(f"New project: {project_id}")
        state["session_num"] = 1

    state["cycle_num"] += 1

    return state


@track_node
def analyze_files_node(state: AgentState) -> AgentState:
    """
    Analyze uploaded files - check cache first, download from storage if needed

    Args:
        state: Current agent state (uploaded_files contains storage_path + original_filename)

    Returns:
        Updated state with file analyses
    """
    from ..database.file_persistence import FilePersistence
    from ..storage.file_manager import download_file

    project_id = state["project_id"]
    analyses = []

    try:
        for file_info in state["uploaded_files"]:
            storage_path = file_info["storage_path"]
            original_filename = file_info["original_filename"]

            # Check if file analysis is cached in database
            cached_record = FilePersistence.get_file_record(project_id, storage_path)

            if cached_record and cached_record.get("file_metadata") and cached_record.get("file_type"):
                # Cache hit - use cached analysis
                analysis = {
                    "file_path": storage_path,
                    "file_name": original_filename,
                    "type": cached_record["file_type"],
                    "row_count": cached_record["file_metadata"].get("row_count", 0),
                    "columns": cached_record["file_metadata"].get("columns", []),
                    "metrics": cached_record["file_metadata"].get("metrics", {}),
                    "data": [],  # Don't load full data from cache
                    "cached": True,
                    "insights_cache": cached_record.get("insights_cache")
                }

                state["messages"].append(f"✓ Using cached analysis for {original_filename}")

            else:
                # Cache miss - download and analyze
                state["messages"].append(f"Downloading and analyzing {original_filename}...")

                # Download file from storage to /tmp
                local_path = download_file(storage_path)

                # Analyze file
                analysis = DataLoader.analyze_file(local_path)
                analysis["cached"] = False

                # Save metadata and file_type to database
                FilePersistence.upsert_file_record(
                    project_id=project_id,
                    storage_path=storage_path,
                    original_filename=original_filename,
                    file_type=analysis.get("type"),
                    file_metadata={
                        "row_count": analysis.get("row_count"),
                        "columns": analysis.get("columns", []),
                        "metrics": analysis.get("metrics", {}),
                    }
                )

                state["messages"].append(
                    f"✓ Analyzed {original_filename}: "
                    f"{analysis['type']}, {analysis['row_count']} rows"
                )

            analyses.append(analysis)

        state["file_analyses"] = analyses

    except Exception as e:
        state["errors"].append(f"File analysis error: {str(e)}")

    state["cycle_num"] += 1

    return state


@track_node
def user_input_node(state: AgentState) -> AgentState:
    """
    Collect additional user inputs and perform targeted web search

    Args:
        state: Current agent state

    Returns:
        Updated state with user inputs and search results
    """
    # Check if we're in CLI mode (interactive) or programmatic mode
    # For now, we'll make interactive prompts optional
    interactive_mode = os.getenv("INTERACTIVE_MODE", "true").lower() == "true"

    # Collect missing critical fields
    user_inputs = state.get("user_inputs", {})

    if interactive_mode:
        print("\n--- Additional Context (optional) ---")

        # Product description
        if not user_inputs.get("product_description"):
            response = input("Product description (press Enter to skip): ").strip()
            if response:
                user_inputs["product_description"] = response

        # Target budget
        if not user_inputs.get("target_budget"):
            response = input("Target daily budget in USD (press Enter to skip): ").strip()
            if response:
                try:
                    user_inputs["target_budget"] = float(response)
                except ValueError:
                    state["messages"].append("Invalid budget format, using default")

        # Target CPA
        if not user_inputs.get("target_cpa"):
            response = input("Target CPA in USD (press Enter to skip): ").strip()
            if response:
                try:
                    user_inputs["target_cpa"] = float(response)
                except ValueError:
                    state["messages"].append("Invalid CPA format")

        # Target ROAS
        if not user_inputs.get("target_roas"):
            response = input("Target ROAS (press Enter to skip): ").strip()
            if response:
                try:
                    user_inputs["target_roas"] = float(response)
                except ValueError:
                    state["messages"].append("Invalid ROAS format")

        print()

    # Update state with collected inputs
    state["user_inputs"] = user_inputs

    # Conditional web search based on decision type
    decision = state.get("decision", "")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key:
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=tavily_key)

            # For 'enrich' decision: Search for competitive intelligence
            if decision == "enrich":
                product_desc = user_inputs.get("product_description", "")
                if product_desc:
                    search_query = f"{product_desc} competitor advertising strategies best practices"
                    results = tavily.search(query=search_query, max_results=3)
                    if "competitive_intel" not in state["market_data"]:
                        state["market_data"]["competitive_intel"] = []
                    state["market_data"]["competitive_intel"].append({
                        "query": search_query,
                        "results": results.get("results", [])
                    })
                    state["messages"].append("Collected competitive intelligence via web search")

            # For 'reflect' decision: Search for optimization tactics
            elif decision == "reflect":
                # Get underperforming platforms from previous analysis
                best_performers = state.get("best_performers", {})
                if best_performers:
                    # Search for platform-specific optimization tactics
                    search_query = f"advertising optimization tactics improve CPA ROAS {best_performers.get('best_platform', 'digital')}"
                    results = tavily.search(query=search_query, max_results=3)
                    if "optimization_intel" not in state["market_data"]:
                        state["market_data"]["optimization_intel"] = []
                    state["market_data"]["optimization_intel"].append({
                        "query": search_query,
                        "results": results.get("results", [])
                    })
                    state["messages"].append("Collected optimization tactics via web search")

        except Exception as e:
            state["messages"].append(f"Web search skipped: {str(e)}")

    state["cycle_num"] += 1

    return state


@track_node
def data_collection_node(state: AgentState) -> AgentState:
    """
    Collect additional data via web search and user prompts

    NOTE: This node stores only METADATA, not raw data.
    Raw data is used temporarily during insight generation but not persisted.

    Args:
        state: Current agent state

    Returns:
        Updated state with collected data metadata
    """
    # Store only metadata from uploaded files (not raw data to avoid NaN issues)
    for analysis in state.get("file_analyses", []):
        if analysis.get("type") == "historical":
            # Store only metadata about historical data
            if "metadata" not in state["historical_data"]:
                state["historical_data"]["metadata"] = {
                    "file_count": 0,
                    "total_rows": 0,
                    "files": []
                }
            state["historical_data"]["metadata"]["file_count"] += 1
            state["historical_data"]["metadata"]["total_rows"] += analysis.get("row_count", 0)
            state["historical_data"]["metadata"]["files"].append({
                "name": analysis.get("file_name"),
                "rows": analysis.get("row_count"),
                "columns": analysis.get("columns", [])
            })
            # Store the actual data temporarily in node_outputs for insight generation
            if "temp_historical_data" not in state["node_outputs"]:
                state["node_outputs"]["temp_historical_data"] = []
            state["node_outputs"]["temp_historical_data"].extend(analysis.get("data", []))

        elif analysis.get("type") == "experiment_results":
            # Add to experiment results (keep for performance tracking)
            state["experiment_results"].append({
                "iteration": state["iteration"] + 1,
                "data": analysis.get("data", []),
                "metrics": analysis.get("metrics", {}),
            })

        elif analysis.get("type") == "enrichment":
            # Store enrichment metadata only
            if "enrichment_metadata" not in state["market_data"]:
                state["market_data"]["enrichment_metadata"] = []
            state["market_data"]["enrichment_metadata"].append({
                "file_name": analysis.get("file_name"),
                "row_count": analysis.get("row_count"),
                "columns": analysis.get("columns", [])
            })
            # Store temporarily for strategy enhancement
            if "temp_enrichment_data" not in state["node_outputs"]:
                state["node_outputs"]["temp_enrichment_data"] = []
            state["node_outputs"]["temp_enrichment_data"].extend(analysis.get("data", []))

    # Web search for market benchmarks (simplified)
    try:
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key and not state.get("market_data", {}).get("benchmarks"):
            tavily = TavilyClient(api_key=tavily_key)

            # Search for market benchmarks based on product
            product_desc = state.get("user_inputs", {}).get("product_description", "")
            if product_desc:
                search_query = f"{product_desc} advertising benchmarks CPA CTR ROAS"
                results = tavily.search(query=search_query, max_results=3)

                state["market_data"]["benchmarks"] = {
                    "search_query": search_query,
                    "results": results.get("results", []),
                }
                state["messages"].append("Collected market benchmarks via web search")

    except Exception as e:
        state["messages"].append(f"Web search skipped: {str(e)}")

    # Interactive prompts for missing data (simplified for MVP)
    # In a real implementation, this would use input() for CLI
    # For now, we'll just mark what's missing
    if not state.get("user_inputs", {}).get("product_description"):
        state["messages"].append("Note: Product description not provided")

    if not state.get("user_inputs", {}).get("target_budget"):
        state["messages"].append("Note: Target budget not provided")

    state["current_phase"] = "data_collected"
    state["cycle_num"] += 1

    return state


def merge_cached_insights(cached_files: list) -> Dict[str, Any]:
    """
    Merge multiple cached insights into a single strategy

    Args:
        cached_files: List of file analyses with insights_cache

    Returns:
        Merged strategy dict
    """
    if not cached_files:
        return {}

    # For now, use the most recent cached insights
    # In future: could intelligently merge multiple insights
    most_recent = cached_files[0]
    cached_strategy = most_recent.get("insights_cache", {}).get("strategy", {})

    return cached_strategy


def extract_cached_context(cached_files: list) -> str:
    """
    Extract key learnings from cached insights for LLM context

    Args:
        cached_files: List of file analyses with insights_cache

    Returns:
        Formatted string of previous insights
    """
    if not cached_files:
        return "No previous insights available"

    context_parts = []

    for file_analysis in cached_files:
        insights_cache = file_analysis.get("insights_cache", {})
        strategy = insights_cache.get("strategy", {})

        if strategy:
            # Extract key points from cached strategy
            insights = strategy.get("insights", {})
            if insights:
                context_parts.append(f"Previous insights from {file_analysis.get('file_name', 'file')}:")
                context_parts.append(f"- Patterns: {insights.get('patterns', [])}")
                context_parts.append(f"- Strengths: {insights.get('strengths', [])}")
                context_parts.append(f"- Weaknesses: {insights.get('weaknesses', [])}")

    return "\n".join(context_parts) if context_parts else "No previous insights available"


@track_node
def insight_node(state: AgentState) -> AgentState:
    """
    Generate insights and strategy from collected data
    Uses hybrid caching: reuse cached insights or combine with new data

    Args:
        state: Current agent state

    Returns:
        Updated state with strategy
    """
    from ..database.file_persistence import FilePersistence

    try:
        # Categorize files: cached vs new
        cached_files = []
        new_files = []

        for analysis in state.get("file_analyses", []):
            if analysis.get("cached") and analysis.get("insights_cache"):
                cached_files.append(analysis)
            else:
                new_files.append(analysis)

        # Decision: Use cached or generate new
        if not new_files and cached_files:
            # Scenario 1: All files cached - skip LLM call
            strategy = merge_cached_insights(cached_files)
            state["current_strategy"] = strategy
            state["current_phase"] = "strategy_built"
            state["messages"].append("✓ Using cached insights (no LLM call)")

            # Extract experiment plan from cached strategy
            state["experiment_plan"] = strategy.get("experiment_plan", {})

        else:
            # Scenario 2: New files present - generate with context
            cached_context = extract_cached_context(cached_files) if cached_files else None

            # Generate strategy using the insight module
            strategy = generate_insights_and_strategy(state, cached_insights=cached_context)

            state["current_strategy"] = strategy
            state["current_phase"] = "strategy_built"

            if cached_context and cached_context != "No previous insights available":
                state["messages"].append("🤖 Generated new insights building on cached learnings")
            else:
                state["messages"].append("🤖 Generated fresh insights from new data")

            # Extract experiment plan
            state["experiment_plan"] = strategy.get("experiment_plan", {})

        # Cache insights back to uploaded_files for future sessions
        # This allows reuse of insights without re-analyzing same files
        project_id = state["project_id"]
        for file_info in state["uploaded_files"]:
            storage_path = file_info["storage_path"]

            # Cache the full strategy as insights for this file
            # In a more sophisticated implementation, could extract file-specific insights
            insights_to_cache = {
                "strategy": strategy,
                "experiment_plan": state["experiment_plan"],
                "generated_at": None,  # Will be set by database
            }

            FilePersistence.cache_file_insights(
                project_id=project_id,
                storage_path=storage_path,
                insights=insights_to_cache
            )

        state["messages"].append("Cached insights for future sessions")

        # Clear temporary data from node_outputs to avoid persisting it
        state["node_outputs"].pop("temp_historical_data", None)
        state["node_outputs"].pop("temp_enrichment_data", None)

    except Exception as e:
        state["errors"].append(f"Insight generation error: {str(e)}")

    state["cycle_num"] += 1

    return state


@track_node
def campaign_setup_node(state: AgentState) -> AgentState:
    """
    Generate campaign configuration

    Args:
        state: Current agent state

    Returns:
        Updated state with campaign config
    """
    try:
        # Generate campaign config
        config = generate_campaign_config(state)

        state["current_config"] = config
        state["config_history"].append({
            "iteration": state["iteration"],
            "config": config,
            "timestamp": None,  # Will be set by database
        })

        state["current_phase"] = "awaiting_results"
        state["messages"].append("Campaign configuration generated")

    except Exception as e:
        state["errors"].append(f"Campaign setup error: {str(e)}")

    state["cycle_num"] += 1

    return state


@track_node
def reflection_node(state: AgentState) -> AgentState:
    """
    Analyze experiment results and generate insights

    Args:
        state: Current agent state

    Returns:
        Updated state with performance analysis
    """
    try:
        # Analyze the latest experiment results
        if state["experiment_results"]:
            latest_results = state["experiment_results"][-1]

            analysis = analyze_experiment_results(
                experiment_data=latest_results,
                strategy=state["current_strategy"],
                historical_context=state["historical_data"]
            )

            # Update metrics timeline
            state["metrics_timeline"].append({
                "iteration": state["iteration"] + 1,
                "analysis": analysis,
            })

            # Update best performers
            if "winners" in analysis:
                state["best_performers"] = analysis["winners"]

            # Check threshold
            if analysis.get("threshold_met"):
                state["threshold_status"] = "met"
                state["current_phase"] = "completed"
                state["messages"].append("Performance threshold met!")
            else:
                state["threshold_status"] = "not_met"
                state["current_phase"] = "optimizing"
                state["messages"].append("Performance below threshold, optimizing...")

            # Store analysis for adjustment node
            state["node_outputs"]["reflection_analysis"] = analysis

    except Exception as e:
        state["errors"].append(f"Reflection error: {str(e)}")

    state["cycle_num"] += 1

    return state


@track_node
def adjustment_node(state: AgentState) -> AgentState:
    """
    Generate patches and adjust campaign configuration

    Args:
        state: Current agent state

    Returns:
        Updated state with adjusted config
    """
    try:
        # Get reflection analysis
        analysis = state["node_outputs"].get("reflection_analysis", {})

        # Generate patch strategy
        patch = generate_patch_strategy(
            analysis=analysis,
            current_config=state["current_config"],
            current_strategy=state["current_strategy"],
            all_historical_context=state
        )

        # Apply patch to create new config
        # For MVP, we'll just store the patch and generate new config
        new_config = generate_campaign_config(state, patch=patch)

        # Update state
        state["patch_history"].append({
            "iteration": state["iteration"] + 1,
            "patch": patch,
            "reasoning": patch.get("reasoning", ""),
        })

        state["current_config"] = new_config
        state["config_history"].append({
            "iteration": state["iteration"] + 1,
            "config": new_config,
        })

        state["iteration"] += 1
        state["current_phase"] = "awaiting_results"
        state["messages"].append(f"Configuration updated to v{state['iteration']}")

    except Exception as e:
        state["errors"].append(f"Adjustment error: {str(e)}")

    state["cycle_num"] += 1

    return state


@track_node
def save_state_node(state: AgentState) -> AgentState:
    """
    Save current state to database

    Args:
        state: Current agent state

    Returns:
        Updated state
    """
    try:
        # Convert state to project dict
        project_data = state_to_project_dict(state)

        # Save to database
        ProjectPersistence.save_project(project_data)

        # Complete session
        if state.get("session_id"):
            SessionPersistence.complete_session(
                session_id=state["session_id"],
                status="completed"
            )

        state["messages"].append("State saved to database")

    except Exception as e:
        state["errors"].append(f"Save error: {str(e)}")

    state["cycle_num"] += 1

    return state

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
    """
    Decorator to track node execution progress and auto-save state after each node.
    This enables incremental state saving and flow resumption.
    """
    @wraps(func)
    def wrapper(state: AgentState) -> AgentState:
        tracker = get_progress_tracker()
        node_name = func.__name__.replace('_node', '')

        # Mark node as currently executing
        state["current_executing_node"] = node_name
        state["flow_status"] = "in_progress"

        # Start tracking
        tracker.node_start(node_name)

        try:
            # Execute node
            result = func(state)

            # Node completed successfully
            result["last_completed_node"] = node_name

            # Append to completed nodes history (avoid duplicates)
            if node_name not in result.get("completed_nodes", []):
                result["completed_nodes"].append(node_name)

            result["current_executing_node"] = None

            # Special case: if this is the save_state_node, mark flow as completed
            if node_name == "save_state":
                result["flow_status"] = "completed"

            # End tracking
            tracker.node_end(node_name, result)

            # Auto-save state after each node (except save_state_node to avoid double-save)
            if node_name != "save_state" and result.get("project_id"):
                try:
                    project_data = state_to_project_dict(result, include_knowledge_facts=True)
                    ProjectPersistence.save_project(project_data)
                    tracker.log_message(f"✓ Auto-saved state after {node_name}", "info")
                except Exception as save_error:
                    # Try without knowledge_facts if schema not updated
                    if "knowledge_facts" in str(save_error):
                        try:
                            project_data = state_to_project_dict(result, include_knowledge_facts=False)
                            ProjectPersistence.save_project(project_data)
                            tracker.log_message(f"✓ Auto-saved state after {node_name} (without knowledge_facts)", "info")
                        except Exception as retry_error:
                            tracker.log_message(f"⚠ Auto-save failed: {str(retry_error)}", "warning")
                    else:
                        tracker.log_message(f"⚠ Auto-save failed: {str(save_error)}", "warning")

            return result

        except Exception as e:
            # Node failed - mark as failed but keep last_completed_node
            state["flow_status"] = "failed"
            state["current_executing_node"] = None
            state["errors"].append(f"{node_name} failed: {str(e)}")

            # Try to save failed state
            try:
                project_data = state_to_project_dict(state, include_knowledge_facts=False)
                ProjectPersistence.save_project(project_data)
                tracker.log_message(f"✓ Saved failed state after {node_name}", "info")
            except Exception as save_error:
                tracker.log_message(f"⚠ Failed to save error state: {str(save_error)}", "warning")

            # Re-raise the original error
            raise e

    return wrapper


@track_node
def load_context_node(state: AgentState) -> AgentState:
    """
    Load project context from database if it exists.
    Detects if flow should be resumed from last checkpoint.

    Args:
        state: Current agent state

    Returns:
        Updated state with loaded project data and resumption flags
    """
    project_id = state["project_id"]

    # Try to load project from database
    project_data = ProjectPersistence.load_project(project_id)

    if project_data:
        # Project exists, load it into state
        state = load_project_into_state(state, project_data)
        state["messages"].append(f"Loaded existing project: {project_id}")
        state["session_num"] = len(project_data.get("config_history", [])) + 1

        # Check if we should resume from a previous incomplete flow
        flow_status = state.get("flow_status", "not_started")
        last_completed = state.get("last_completed_node")
        force_restart = state.get("force_restart", False)  # Can be set by CLI

        if flow_status == "in_progress" and last_completed and not force_restart:
            # Resume from last checkpoint
            state["is_resuming"] = True
            state["messages"].append("=" * 60)
            state["messages"].append("RESUMING FROM CHECKPOINT")
            state["messages"].append("=" * 60)
            state["messages"].append(f"Last completed node: {last_completed}")
            state["messages"].append(f"Completed nodes: {state.get('completed_nodes', [])}")
            state["messages"].append(f"Resuming workflow from node: {last_completed}")
            state["messages"].append("=" * 60)
        elif flow_status == "failed" and last_completed and not force_restart:
            # Previous flow failed - allow resume or restart
            state["is_resuming"] = True
            state["messages"].append("=" * 60)
            state["messages"].append("PREVIOUS FLOW FAILED - RESUMING")
            state["messages"].append("=" * 60)
            state["messages"].append(f"Last completed node before failure: {last_completed}")
            state["messages"].append(f"Retrying from next node after: {last_completed}")
            state["messages"].append("=" * 60)
        elif force_restart:
            # User requested force restart - clear flow state
            state["is_resuming"] = False
            state["flow_status"] = "not_started"
            state["last_completed_node"] = None
            state["completed_nodes"] = []
            state["current_executing_node"] = None
            state["messages"].append("Force restart requested - starting fresh flow")
        else:
            # Normal new session on existing project
            state["is_resuming"] = False
            if flow_status == "completed":
                state["messages"].append("Previous flow completed - starting new session")

    else:
        # New project
        state["messages"].append(f"New project: {project_id}")
        state["session_num"] = 1
        state["is_resuming"] = False

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


def infer_facts_from_data(state: AgentState) -> Dict[str, Dict[str, Any]]:
    """
    Use LLM to infer facts from historical campaign data in file_analyses

    Args:
        state: Current agent state with file_analyses

    Returns:
        Dictionary of inferred facts with confidence scores
    """
    from ..llm.gemini import get_gemini
    import json

    facts = {}

    # Get data from file_analyses (populated by analyze_files_node)
    file_analyses = state.get("file_analyses", [])

    # Collect all historical campaign data
    all_data = []
    for analysis in file_analyses:
        if analysis.get("type") == "historical" and analysis.get("data"):
            all_data.extend(analysis["data"])

    if not all_data or len(all_data) == 0:
        state.get("messages", []).append("⚠ No historical data available for LLM inference")
        return facts

    state.get("messages", []).append(f"🔍 Analyzing {len(all_data)} campaign records for inference...")

    try:
        gemini = get_gemini()

        # Sample first 5 campaigns for inference
        sample = all_data[:5]

        inference_prompt = f"""
Analyze these campaign data samples and infer:
1. Product type/category
2. Target audience hints
3. Likely business goals

Data: {json.dumps(sample, indent=2)}

Respond with JSON:
{{
  "product_type": "description",
  "audience_hint": "description",
  "business_goals": "description"
}}
"""

        result = gemini.generate_json(
            prompt=inference_prompt,
            temperature=0.3,
            task_name="Data Inference"
        )

        if result.get("product_type"):
            facts["product_category"] = {
                "value": result["product_type"],
                "confidence": 0.7,
                "source": "llm_inference"
            }

        if result.get("audience_hint"):
            facts["audience_hint"] = {
                "value": result["audience_hint"],
                "confidence": 0.6,
                "source": "llm_inference"
            }

        if result.get("business_goals"):
            facts["business_goals"] = {
                "value": result["business_goals"],
                "confidence": 0.5,
                "source": "llm_inference"
            }

    except Exception as e:
        state.get("messages", []).append(f"⚠ LLM inference error: {str(e)}")

    return facts


def parallel_web_search(state: AgentState) -> Dict[str, Dict[str, Any]]:
    """
    Execute multiple Tavily searches concurrently

    Args:
        state: Current agent state

    Returns:
        Dictionary of web search results with confidence scores
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    facts = {}
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        return facts

    # Get product description from knowledge_facts or user_inputs
    product = state.get("knowledge_facts", {}).get("product_description", {}).get("value")
    if not product:
        product = state.get("user_inputs", {}).get("product_description", "")

    if not product:
        return facts

    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=tavily_key)

        # Define search queries
        searches = {
            "competitors": f"{product} competitors advertising strategies",
            "benchmarks": f"{product} advertising CPA ROAS benchmarks industry standards"
        }

        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_key = {
                executor.submit(tavily.search, query, max_results=3): key
                for key, query in searches.items()
            }

            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    result = future.result()
                    facts[f"market_{key}"] = {
                        "value": result.get("results", []),
                        "confidence": 0.8,
                        "source": "web_search"
                    }
                except Exception as e:
                    state.get("messages", []).append(f"Web search for {key} failed: {str(e)}")

    except Exception as e:
        state.get("messages", []).append(f"Parallel web search skipped: {str(e)}")

    return facts


def ask_user_batch(missing_keys: list, state: AgentState) -> Dict[str, Dict[str, Any]]:
    """
    Ask user multiple questions at once in batch

    Args:
        missing_keys: List of fact keys that need user input
        state: Current agent state

    Returns:
        Dictionary of user-provided facts with confidence 1.0
    """
    # Friendly question mappings
    QUESTION_MAP = {
        "product_description": "Product/service description: ",
        "target_cpa": "Target CPA (cost per acquisition) in USD: ",
        "target_roas": "Target ROAS (return on ad spend): ",
        "target_budget": "Daily budget in USD: ",
        "target_audience": "Target audience description: ",
    }

    facts = {}

    if not missing_keys:
        return facts

    print("\n" + "="*60)
    print("  Required Information")
    print("="*60)
    print("(Press Enter to skip any question)\n")

    for key in missing_keys:
        prompt = QUESTION_MAP.get(key, f"{key.replace('_', ' ').title()}: ")
        response = input(prompt).strip()

        if response:
            # Try to convert numeric values
            value = response
            try:
                if "cpa" in key.lower() or "roas" in key.lower() or "budget" in key.lower():
                    value = float(response)
            except ValueError:
                pass

            facts[key] = {
                "value": value,
                "confidence": 1.0,
                "source": "user"
            }

    print()
    return facts


@track_node
def discovery_node(state: AgentState) -> AgentState:
    """
    Intelligent discovery using parallel strategies with detailed progress logging

    Minimizes user questions by inferring from data and searching web first.
    Only asks user for critical unknowns with low confidence.

    Args:
        state: Current agent state

    Returns:
        Updated state with knowledge_facts populated
    """
    interactive_mode = os.getenv("INTERACTIVE_MODE", "true").lower() == "true"
    knowledge = state.get("knowledge_facts", {}).copy()

    # Header
    state["messages"].append("="*60)
    state["messages"].append("DISCOVERY PROCESS")
    state["messages"].append("="*60)

    # Strategy 1: LLM Inference from historical data
    state["messages"].append("\n[Strategy 1/3] LLM Inference from Historical Data")
    inferred = infer_facts_from_data(state)

    if inferred:
        knowledge.update(inferred)
        avg_conf = sum(f['confidence'] for f in inferred.values())/len(inferred)
        state["messages"].append(f"  ✓ Inferred {len(inferred)} facts (avg confidence: {avg_conf:.2f})")
        for key, fact in inferred.items():
            value_preview = str(fact['value'])[:50] + "..." if len(str(fact['value'])) > 50 else str(fact['value'])
            state["messages"].append(f"    - {key}: {value_preview} (conf: {fact['confidence']:.2f})")
    else:
        state["messages"].append("  ⊘ No facts inferred")

    # Strategy 2: Parallel Web Search
    state["messages"].append("\n[Strategy 2/3] Parallel Web Search")
    web_facts = parallel_web_search(state)

    if web_facts:
        knowledge.update(web_facts)
        state["messages"].append(f"  ✓ Found {len(web_facts)} facts from web")
        for key in web_facts.keys():
            state["messages"].append(f"    - {key}")
    else:
        # Check why web search didn't run
        product = knowledge.get("product_description", {}).get("value") or state.get("user_inputs", {}).get("product_description")
        if not product:
            state["messages"].append("  ⊘ Web search skipped (no product description yet)")
        else:
            state["messages"].append("  ⊘ Web search skipped (no Tavily API key)")

    # Strategy 3: User Questions (only for critical missing facts)
    state["messages"].append("\n[Strategy 3/3] User Input for Critical Facts")
    critical_facts = ["product_description", "target_budget"]

    missing = []
    for key in critical_facts:
        existing_conf = knowledge.get(key, {}).get("confidence", 0)
        if key not in knowledge or existing_conf < 0.6:
            missing.append(key)
            state["messages"].append(f"  ? {key} needed (current confidence: {existing_conf:.2f}, threshold: 0.60)")

    if not missing:
        state["messages"].append("  ✓ All critical facts already known")
    elif not interactive_mode:
        state["messages"].append("  ⊘ Interactive mode disabled, skipping user questions")
    else:
        user_facts = ask_user_batch(missing, state)
        knowledge.update(user_facts)
        if user_facts:
            state["messages"].append(f"  ✓ User provided {len(user_facts)} facts")
            for key in user_facts.keys():
                state["messages"].append(f"    - {key}")
        else:
            state["messages"].append("  ⊘ User skipped all questions")

    # Final Summary
    state["messages"].append("\n" + "="*60)
    state["messages"].append("DISCOVERY SUMMARY")
    state["messages"].append("="*60)

    if knowledge:
        sources = {}
        for fact in knowledge.values():
            source = fact["source"]
            sources[source] = sources.get(source, 0) + 1

        state["messages"].append(f"Total facts discovered: {len(knowledge)}")
        state["messages"].append(f"By source: {dict(sources)}")

        state["messages"].append("\nKnowledge Graph:")
        for key, fact in knowledge.items():
            value_str = str(fact['value'])[:40] + "..." if len(str(fact['value'])) > 40 else str(fact['value'])
            state["messages"].append(
                f"  {key:25} {value_str:42} "
                f"[conf: {fact['confidence']:.2f}, src: {fact['source']}]"
            )
    else:
        state["messages"].append("⚠ WARNING: No facts discovered!")
        state["messages"].append("  Possible reasons:")
        state["messages"].append("  - No historical data in uploaded files")
        state["messages"].append("  - User skipped all questions")
        state["messages"].append("  - Web search disabled (no Tavily API key)")

    state["messages"].append("="*60)

    # Update state
    state["knowledge_facts"] = knowledge

    # Extract values for backward compatibility with existing code
    user_inputs = {}
    for key, fact in knowledge.items():
        if key in ["product_description", "target_cpa", "target_roas", "target_budget", "target_audience"]:
            user_inputs[key] = fact["value"]

    state["user_inputs"] = user_inputs

    state["cycle_num"] += 1
    return state


@track_node
def user_input_node(state: AgentState) -> AgentState:
    """
    DEPRECATED: Use discovery_node instead
    This node is kept for backward compatibility but redirects to discovery_node

    Collect additional user inputs and perform targeted web search

    Args:
        state: Current agent state

    Returns:
        Updated state with user inputs and search results
    """
    # Redirect to discovery_node
    return discovery_node(state)

    # Old implementation below (never reached)
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

            # Extract execution timeline from cached strategy
            state["experiment_plan"] = strategy.get("execution_timeline", {})

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

            # Extract execution timeline from strategy
            state["experiment_plan"] = strategy.get("execution_timeline", {})

        # Cache insights back to uploaded_files for future sessions
        # This allows reuse of insights without re-analyzing same files
        project_id = state["project_id"]
        for file_info in state["uploaded_files"]:
            storage_path = file_info["storage_path"]

            # Cache the full strategy as insights for this file
            # In a more sophisticated implementation, could extract file-specific insights
            insights_to_cache = {
                "strategy": strategy,
                "execution_timeline": state["experiment_plan"],
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
    Save current state to database with fallback for schema migration

    Args:
        state: Current agent state

    Returns:
        Updated state
    """
    try:
        # Try to save with knowledge_facts
        project_data = state_to_project_dict(state, include_knowledge_facts=True)
        ProjectPersistence.save_project(project_data)

        # Complete session
        if state.get("session_id"):
            SessionPersistence.complete_session(
                session_id=state["session_id"],
                status="completed"
            )

        state["messages"].append("State saved to database")

    except Exception as e:
        error_str = str(e)

        # Check if it's the schema cache error for knowledge_facts
        if "knowledge_facts" in error_str and ("PGRST204" in error_str or "schema cache" in error_str):
            # Retry without knowledge_facts
            state["messages"].append("⚠ Database schema not updated yet - saving without knowledge_facts")
            state["messages"].append("💡 Run migration: migrations/add_knowledge_facts_column.sql")

            try:
                project_data = state_to_project_dict(state, include_knowledge_facts=False)
                ProjectPersistence.save_project(project_data)

                # Complete session
                if state.get("session_id"):
                    SessionPersistence.complete_session(
                        session_id=state["session_id"],
                        status="completed"
                    )

                state["messages"].append("State saved (without knowledge_facts)")
            except Exception as retry_error:
                state["errors"].append(f"Save error (retry failed): {str(retry_error)}")
        else:
            # Different error, report it
            state["errors"].append(f"Save error: {error_str}")

    state["cycle_num"] += 1

    return state

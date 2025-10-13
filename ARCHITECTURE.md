# Adronaut Agent - Technical Architecture

**Version:** 1.0
**Last Updated:** 2025-10-13
**Purpose:** Comprehensive technical documentation for developers and collaborators

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Design Principles](#design-principles)
3. [LangGraph Agent Architecture](#langgraph-agent-architecture)
4. [State Management](#state-management)
5. [Node Descriptions](#node-descriptions)
6. [Router Logic](#router-logic)
7. [Module Breakdown](#module-breakdown)
8. [LLM Integration](#llm-integration)
9. [Database Schema](#database-schema)
10. [File Storage](#file-storage)
11. [Development Patterns](#development-patterns)

---

## System Overview

Adronaut is an **AI-powered campaign optimization agent** built on **LangGraph** (stateful multi-step workflows) with **Gemini 2.0 Flash** for LLM reasoning. The system follows a **router-based architecture** where an LLM examines project state and uploaded files to determine the optimal execution path.

### Core Capabilities

1. **Multi-Session Continuity**: Projects persist across sessions with full state restoration
2. **Intelligent Routing**: LLM-powered decision making based on project state and file types
3. **Flexible Execution Timelines**: Adaptive 7-30 day test plans based on campaign complexity
4. **Data-Driven Insights**: Extracts patterns from historical performance data
5. **Automated Optimization**: Generates patches and new configs based on experiment results

### Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│                      CLI Interface                           │
│                        (cli.py)                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                             │
│         LangGraph Workflow (src/agent/graph.py)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Router  │→ │Discovery │→ │ Insight  │→ │ Campaign │   │
│  │   Node   │  │   Node   │  │   Node   │  │   Setup  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                │
│  │Reflection│→ │Adjustment│→ Save                          │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  insight.py  │  │ campaign.py  │  │reflection.py │     │
│  │  Strategy    │  │Config        │  │Performance   │     │
│  │  Generation  │  │Generation    │  │Analysis      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │data_loader.py│  │execution_    │                        │
│  │File Analysis │  │planner.py    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Integration Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  gemini.py   │  │persistence.py│  │file_manager.py│    │
│  │LLM Wrapper   │  │Database I/O  │  │Storage I/O   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Infrastructure                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Gemini API  │  │   Supabase   │  │    Tavily    │     │
│  │  (Google)    │  │  (Database + │  │ (Web Search) │     │
│  │              │  │   Storage)   │  │  (Optional)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. State-First Architecture

All agent logic operates on a single **AgentState** dictionary that flows through the graph. This enables:
- **Transparency**: Full state visibility at any point
- **Resumability**: Exact state restoration across sessions
- **Debugging**: Complete audit trail via state snapshots

### 2. Router-Based Workflow

Instead of hardcoded branching, an **LLM-powered router** examines state to decide the next node:
```python
# Router examines:
- project_loaded: bool
- current_phase: 'initialized' | 'strategy_built' | 'awaiting_results' | 'optimizing'
- uploaded_file_types: ['historical' | 'experiment_results' | 'enrichment']

# Router decides:
- initialize: New project with historical data → full setup flow
- reflect: Experiment results uploaded → performance analysis + optimization
- enrich: Additional data uploaded → update strategy
- continue: Resume incomplete flow
```

### 3. Separation of Concerns

**Nodes** (in `nodes.py`) handle orchestration and state updates:
```python
def insight_node(state: AgentState) -> AgentState:
    # 1. Extract data from state
    # 2. Call business logic module
    # 3. Update state with results
    # 4. Add message for user
    return state
```

**Modules** (in `modules/`) contain pure business logic:
```python
def generate_insights_and_strategy(data, state) -> dict:
    # Pure function: data in, insights out
    # No state mutations, no side effects
    return {"insights": {...}, "target_audience": {...}}
```

### 4. LLM as Reasoning Engine

LLM calls are centralized in `src/llm/gemini.py` with:
- **Descriptive task names** for progress tracking
- **Temperature tuning** per task (0.3 for analysis, 0.7 for creativity)
- **Structured output** via JSON mode
- **Error handling** with retries

### 5. Multi-Session Persistence

Projects are stored in Supabase with full state:
```python
# Session 1: Upload historical data
state = load_project_into_state(state, db_project)  # Hydrate from DB
# ... agent runs ...
save_project(state_to_project_dict(state))  # Persist to DB

# Session 2: Upload experiment results
state = load_project_into_state(state, db_project)  # Restore full context
# ... agent optimizes ...
```

---

## LangGraph Agent Architecture

### Graph Structure

The agent is defined in `src/agent/graph.py` using LangGraph's `StateGraph`:

```python
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("load_context", load_context_node)
workflow.add_node("analyze_files", analyze_files_node)
workflow.add_node("router", router_node)
workflow.add_node("discovery", discovery_node)
workflow.add_node("data_collection", data_collection_node)
workflow.add_node("insight", insight_node)
workflow.add_node("campaign_setup", campaign_setup_node)
workflow.add_node("reflection", reflection_node)
workflow.add_node("adjustment", adjustment_node)
workflow.add_node("save", save_state_node)

# Set entry point
workflow.set_entry_point("load_context")
```

### Execution Paths

**Initialize Path** (new project with historical data):
```
load_context → analyze_files → router → discovery → data_collection →
insight → campaign_setup → save → END
```

**Reflect Path** (existing project with experiment results):
```
load_context → analyze_files → router → reflection → adjustment →
save → END
```

**Enrich Path** (additional data):
```
load_context → analyze_files → router → discovery → data_collection →
insight → campaign_setup → save → END
```

### Conditional Routing

The router uses `add_conditional_edges` to dynamically route:

```python
workflow.add_conditional_edges(
    "router",
    get_next_node,  # Function that returns next node name
    {
        "discovery": "discovery",
        "data_collection": "data_collection",
        "insight": "insight",
        "campaign_setup": "campaign_setup",
        "reflection": "reflection",
        "adjustment": "adjustment",
        "save": "save",
    },
)
```

---

## State Management

### AgentState Schema

Defined in `src/agent/state.py`:

```python
class AgentState(TypedDict):
    # Session metadata
    project_id: str                  # UUID
    session_id: Optional[str]        # Current session UUID
    session_num: int                 # Sequential session counter
    cycle_num: int                   # Node execution counter

    # Router decision
    decision: str                    # 'initialize' | 'reflect' | 'enrich' | 'continue'
    decision_reasoning: str          # LLM explanation

    # Project state
    project_loaded: bool             # Whether project exists in DB
    current_phase: str               # State machine: initialized | strategy_built | awaiting_results | optimizing
    iteration: int                   # Optimization cycle counter (0 = baseline)

    # Uploaded files
    uploaded_files: List[Dict]       # [{storage_path, original_filename}, ...]
    file_analysis: Dict[str, Any]    # {file_name: {file_type, row_count, columns, ...}}

    # Accumulated data
    historical_data: Dict[str, Any]  # {metadata: {...}, summary: {...}}
    market_data: Dict[str, Any]      # {competitive_intel: [...], benchmarks: [...]}
    experiment_results: List[Dict]   # [{iteration: 1, data: [...], analysis: {...}}, ...]

    # Strategy & config
    current_strategy: Dict[str, Any] # {insights, target_audience, creative_strategy, platform_strategy}
    experiment_plan: Dict[str, Any]  # {timeline: {...}, statistical_requirements: {...}}
    current_config: Dict[str, Any]   # {tiktok: {...}, meta: {...}, summary: {...}}
    config_history: List[Dict]       # All config versions

    # Performance tracking
    best_performers: Dict[str, Any]  # Top combinations from experiments
    threshold_status: str            # 'not_met' | 'met' | 'exceeded'
    metrics_timeline: List[Dict]     # Performance over iterations
    patch_history: List[Dict]        # All optimization patches

    # Knowledge graph
    knowledge_facts: Dict[str, Dict] # {fact_name: {value, confidence, source, last_updated}}
    user_inputs: Dict[str, Any]      # Collected via discovery

    # Node communication
    node_outputs: Dict[str, Any]     # Temporary data between nodes (not persisted)
    messages: List[str]              # User-facing messages
    errors: List[str]                # Error messages
```

### State Persistence Pattern

**Load on entry** (`load_context_node` in `src/agent/nodes.py:37-68`):
```python
def load_context_node(state: AgentState) -> AgentState:
    project_id = state["project_id"]
    project_data = ProjectPersistence.load_project(project_id)

    if project_data:
        state = load_project_into_state(state, project_data)
        state["project_loaded"] = True
        state["messages"].append(f"Loaded existing project: {project_id}")
    else:
        state["project_loaded"] = False
        state["messages"].append(f"New project: {project_id}")

    return state
```

**Save on exit** (`save_state_node` in `src/agent/nodes.py:448-479`):
```python
def save_state_node(state: AgentState) -> AgentState:
    # Convert state to DB format
    project_data = state_to_project_dict(state)

    # Persist to Supabase
    ProjectPersistence.save_project(project_data)

    state["messages"].append("State saved to database")
    return state
```

### Temporary vs Persistent State

**Persistent fields** (saved to DB):
- `historical_data`, `market_data`, `experiment_results`
- `current_strategy`, `experiment_plan`, `current_config`
- `knowledge_facts`, `best_performers`, `metrics_timeline`

**Temporary fields** (session-only):
- `node_outputs` - Inter-node communication within a session
- `uploaded_files` - Replaced with storage paths in DB
- `messages`, `errors` - UI feedback only

---

## Node Descriptions

### load_context_node
**File:** `src/agent/nodes.py:37-68`
**Purpose:** Load existing project state from database or initialize new project
**Input:** Project ID in state
**Output:** Hydrated state with project data or empty state
**Key Logic:**
```python
if project_exists:
    state = load_project_into_state(state, db_data)
    state["project_loaded"] = True
else:
    state["project_loaded"] = False
```

### analyze_files_node
**File:** `src/agent/nodes.py:71-109`
**Purpose:** Analyze uploaded files to detect type (historical/experiments/enrichment)
**Input:** `uploaded_files` list with storage paths
**Output:** `file_analysis` dict with file types and metadata
**Key Logic:**
```python
for file in uploaded_files:
    data = download_and_parse(file)
    file_type = DataLoader.detect_file_type(data)  # historical | experiment_results | enrichment
    analysis[filename] = {
        "file_type": file_type,
        "row_count": len(data),
        "columns": data.columns.tolist()
    }
```

### router_node
**File:** `src/agent/router.py:22-119`
**Purpose:** LLM-powered decision on next workflow step
**Input:** `project_loaded`, `current_phase`, `file_analysis`
**Output:** `decision` and `decision_reasoning`
**Key Logic:**
```python
prompt = f"""
Analyze project state:
- Project exists: {state['project_loaded']}
- Current phase: {state['current_phase']}
- Uploaded files: {file_types}

Decide next action: initialize | reflect | enrich | continue
"""
decision = gemini.generate_structured(prompt, temp=0.3)
state["decision"] = decision["action"]
state["decision_reasoning"] = decision["reasoning"]
```

### discovery_node
**File:** `src/agent/nodes.py:112-190`
**Purpose:** Intelligent data discovery using parallel strategies (LLM inference + web search + user prompts)
**Input:** Project state and uploaded files
**Output:** Discovered facts in `knowledge_facts`
**Key Strategies:**
1. **LLM Inference**: Analyze uploaded data to infer product, budget, CPA
2. **Web Search**: Tavily search for market benchmarks (if TAVILY_API_KEY set)
3. **User Prompts**: Ask for missing critical fields (if INTERACTIVE_MODE=true)

**Key Logic:**
```python
# Strategy 1: LLM inference from uploaded data
facts = llm_infer_facts(uploaded_data)  # Infer product, target_cpa, etc.

# Strategy 2: Web search
if TAVILY_API_KEY and product_description:
    search_results = tavily_search(f"{product} market benchmarks CPA ROAS")
    facts["market_benchmarks"] = extract_benchmarks(search_results)

# Strategy 3: User prompts (minimal friction)
if INTERACTIVE_MODE and missing_critical_fields:
    user_input = prompt_user(missing_fields)
    facts.update(user_input)

# Store all facts in knowledge graph
state["knowledge_facts"].update(facts)
```

### data_collection_node
**File:** `src/agent/nodes.py:193-243`
**Purpose:** Merge uploaded files into accumulated state
**Input:** `uploaded_files`, `file_analysis`
**Output:** Updated `historical_data`, `experiment_results`, or `market_data`
**Key Logic:**
```python
for file, analysis in file_analysis.items():
    file_type = analysis["file_type"]
    data = download_and_parse(file["storage_path"])

    if file_type == "historical":
        # Get detailed analysis (performance summary, top/bottom performers)
        detailed_analysis = DataLoader.get_detailed_analysis(data)
        state["historical_data"]["metadata"] = {...}
        state["historical_data"]["summary"] = detailed_analysis

    elif file_type == "experiment_results":
        state["experiment_results"].append({
            "iteration": state["iteration"],
            "data": data.to_dict(),
            "uploaded_at": datetime.now()
        })

    elif file_type == "enrichment":
        state["market_data"]["enrichment"] = data.to_dict()
```

### insight_node
**File:** `src/agent/nodes.py:246-287`
**Purpose:** Generate campaign strategy and execution timeline
**Input:** `historical_data`, `market_data`, `knowledge_facts`
**Output:** `current_strategy`, `experiment_plan`
**Key Logic:**
```python
# Generate strategy (LLM call with temp=0.7 for creativity)
strategy = generate_insights_and_strategy(
    historical_data=state["historical_data"],
    market_data=state["market_data"],
    knowledge_facts=state["knowledge_facts"]
)
state["current_strategy"] = strategy

# Generate flexible execution timeline (LLM call with temp=0.6)
timeline = generate_execution_timeline(
    state=state,
    strategy=strategy
)
state["experiment_plan"] = timeline

# Validate timeline structure
is_valid, errors = validate_execution_timeline(timeline)
if not is_valid:
    state["errors"].extend(errors)
```

### campaign_setup_node
**File:** `src/agent/nodes.py:290-335`
**Purpose:** Generate platform-specific campaign configurations (TikTok, Meta)
**Input:** `current_strategy`, `experiment_plan`, `knowledge_facts`
**Output:** `current_config`
**Key Logic:**
```python
config = generate_campaign_config(
    strategy=state["current_strategy"],
    execution_plan=state["experiment_plan"],
    target_budget=state["knowledge_facts"]["target_budget"]["value"],
    target_cpa=state["knowledge_facts"]["target_cpa"]["value"]
)

state["current_config"] = config
state["config_history"].append({
    "version": state["iteration"],
    "config": config,
    "created_at": datetime.now()
})
state["current_phase"] = "awaiting_results"
```

### reflection_node
**File:** `src/agent/nodes.py:338-387`
**Purpose:** Analyze experiment results and compare vs thresholds
**Input:** `experiment_results`, `current_config`, `knowledge_facts`
**Output:** `best_performers`, `threshold_status`, `metrics_timeline`
**Key Logic:**
```python
# Get latest experiment results
latest_results = state["experiment_results"][-1]["data"]

# Analyze performance (LLM call with temp=0.3 for precision)
analysis = analyze_experiment_results(
    experiment_data=latest_results,
    current_config=state["current_config"],
    target_cpa=state["knowledge_facts"]["target_cpa"]["value"],
    target_roas=state["knowledge_facts"]["target_roas"]["value"]
)

state["best_performers"] = analysis["top_performers"]
state["threshold_status"] = analysis["threshold_status"]  # 'met' | 'not_met' | 'exceeded'
state["metrics_timeline"].append({
    "iteration": state["iteration"],
    "avg_cpa": analysis["avg_cpa"],
    "avg_roas": analysis["avg_roas"],
    "total_conversions": analysis["total_conversions"]
})

# Store analysis in node_outputs for adjustment_node
state["node_outputs"]["reflection_analysis"] = analysis
```

### adjustment_node
**File:** `src/agent/nodes.py:390-445`
**Purpose:** Generate optimization patches and new campaign config
**Input:** `reflection_analysis` (from node_outputs), `current_strategy`
**Output:** Updated `current_config`, `patch_history`, incremented `iteration`
**Key Logic:**
```python
# Get reflection analysis from previous node
analysis = state["node_outputs"]["reflection_analysis"]

# Generate optimization patch (LLM call with temp=0.6)
patch = generate_patch_strategy(
    performance_analysis=analysis,
    current_config=state["current_config"],
    historical_winners=state["best_performers"]
)

state["patch_history"].append({
    "iteration": state["iteration"] + 1,
    "patch": patch,
    "analysis_summary": analysis["summary"]
})

# Generate new config incorporating patch
new_config = generate_campaign_config(
    strategy=state["current_strategy"],
    execution_plan=state["experiment_plan"],
    optimization_patch=patch,
    ...
)

# Update state
state["iteration"] += 1
state["current_config"] = new_config
state["config_history"].append(new_config)
state["current_phase"] = "optimizing"
```

### save_state_node
**File:** `src/agent/nodes.py:448-479`
**Purpose:** Persist agent state to database
**Input:** Full state
**Output:** State (unchanged) with success message
**Key Logic:**
```python
project_data = state_to_project_dict(state)
ProjectPersistence.save_project(project_data)
state["messages"].append("State saved to database")
```

---

## Router Logic

### Decision Tree

**File:** `src/agent/router.py:143-180`

```
┌─────────────────────────────────────────────────────────────┐
│                        ROUTER                                │
│              (LLM-powered decision making)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    [project_loaded?]    [file_types?]      [current_phase?]
          │                   │                   │
          └───────────────────┴───────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      DECISION LOGIC                          │
│                                                              │
│  IF project_loaded == False AND file_types == ['historical']│
│    → Decision: INITIALIZE                                    │
│    → Route to: discovery → data_collection → insight →      │
│                campaign_setup → save                         │
│                                                              │
│  IF project_loaded == True AND file_types == ['experiments']│
│    → Decision: REFLECT                                       │
│    → Route to: reflection → adjustment → save               │
│                                                              │
│  IF project_loaded == True AND file_types == ['enrichment'] │
│    → Decision: ENRICH                                        │
│    → Route to: discovery → data_collection → insight →      │
│                campaign_setup → save                         │
│                                                              │
│  IF current_phase == 'initialized' AND no new files         │
│    → Decision: CONTINUE                                      │
│    → Route to: insight (resume incomplete flow)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Router Prompt Template

**File:** `src/agent/router.py:24-80`

```python
ROUTER_PROMPT = """
Analyze the following project state and decide the next workflow action:

PROJECT STATE:
- Project loaded from database: {project_loaded}
- Current phase: {current_phase}
- Current iteration: {iteration}

UPLOADED FILES ANALYSIS:
{file_analysis}

WORKFLOW CONTEXT:
- If this is a NEW PROJECT with HISTORICAL DATA → initialize
- If EXPERIMENT RESULTS were uploaded → reflect
- If ADDITIONAL DATA was uploaded to existing project → enrich
- If project is incomplete (e.g., phase='initialized' but no config) → continue

DECISION OPTIONS:
1. initialize: Start full campaign setup flow (discovery → strategy → config)
2. reflect: Analyze experiment performance and generate optimization patch
3. enrich: Add new data to existing strategy and regenerate config
4. continue: Resume incomplete workflow from last checkpoint

Respond with JSON:
{{
  "action": "initialize" | "reflect" | "enrich" | "continue",
  "reasoning": "Explain why this action was chosen based on state"
}}
"""
```

### Router Node to Next Node Mapping

**File:** `src/agent/router.py:143-180`

```python
def get_next_node(state: AgentState) -> str:
    """
    Map router decision to next node name

    Returns:
        Node name to route to
    """
    decision = state.get("decision", "")
    current_phase = state.get("current_phase", "")

    if decision == "initialize":
        return "discovery"  # Start discovery → data_collection → insight → campaign_setup

    elif decision == "reflect":
        return "reflection"  # Analyze results → adjustment → save

    elif decision == "enrich":
        return "discovery"  # Re-run discovery with new data → data_collection → insight

    elif decision == "continue":
        # Resume from last checkpoint
        if current_phase == "initialized":
            return "insight"  # Resume strategy generation
        elif current_phase == "strategy_built":
            return "campaign_setup"  # Resume config generation
        else:
            return "save"  # Already complete, just save

    else:
        # Fallback
        return "save"
```

---

## Module Breakdown

### insight.py

**File:** `src/modules/insight.py`
**Purpose:** Strategy generation and LLM-powered insights extraction

**Key Function: `generate_insights_and_strategy()`** (lines 131-273)

```python
def generate_insights_and_strategy(
    historical_data: Dict[str, Any],
    market_data: Dict[str, Any],
    knowledge_facts: Dict[str, Dict]
) -> Dict[str, Any]:
    """
    Generate campaign strategy from historical performance data

    Returns:
        {
          "insights": {
            "patterns": [...],
            "strengths": [...],
            "weaknesses": [...],
            "benchmark_comparison": "..."
          },
          "target_audience": {
            "primary_segments": [...],
            "demographics": {...},
            "interests": [...]
          },
          "creative_strategy": {
            "messaging_angles": [...],
            "value_props": [...]
          },
          "platform_strategy": {
            "priorities": ['TikTok', 'Meta'],
            "budget_split": {'TikTok': 0.6, 'Meta': 0.4},
            "rationale": "..."
          }
        }
    """
    gemini = get_gemini()

    # Extract historical performance summary
    hist_summary = historical_data.get("summary", {})

    # Build prompt with ACTUAL data citations
    prompt = STRATEGY_PROMPT_TEMPLATE.format(
        historical_summary=hist_summary,
        market_benchmarks=market_data.get("benchmarks", "N/A"),
        product=knowledge_facts.get("product_description", {}).get("value", "Product")
    )

    # Generate with temperature=0.7 for creativity
    strategy = gemini.generate_json(
        prompt=prompt,
        system_instruction=STRATEGY_SYSTEM_INSTRUCTION,
        temperature=0.7,
        task_name="Strategy & Insights Generation"
    )

    return strategy
```

**Critical Prompt Instruction** (lines 35-55):
```python
CRITICAL INSTRUCTIONS:
1. Reference ACTUAL data from historical performance:
   - Cite specific CPA values (e.g., "TikTok had $18 CPA vs Meta $23 CPA")
   - Quote campaign names from top/bottom performers
   - Use exact metrics from summary (not generic statements)

2. Base insights on DATA GAPS and OPPORTUNITIES:
   - If only 1 platform tested → Recommend testing alternatives
   - If audience is broad → Recommend segment testing
   - If creative format is stale → Recommend new angles

3. Generate TESTABLE hypotheses:
   - Each insight should lead to an experiment
   - Prioritize high-impact, quick-win tests
```

### execution_planner.py

**File:** `src/modules/execution_planner.py`
**Purpose:** LLM-powered flexible execution timeline generation (7-30 days)

**Key Function: `generate_execution_timeline()`** (lines 163-230)

```python
def generate_execution_timeline(
    state: Dict[str, Any],
    strategy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate flexible execution timeline using LLM

    Returns:
        {
          "timeline": {
            "total_duration_days": 14,
            "reasoning": "Why this timeline length",
            "phases": [
              {
                "name": "Short-term Discovery",
                "duration_days": 5,
                "budget_allocation_percent": 35,
                "objectives": [...],
                "test_combinations": [
                  {
                    "platform": "TikTok",
                    "audience": "Interest targeting",
                    "creative": "UGC video",
                    "budget_percent": 15,
                    "rationale": "..."
                  }
                ],
                "success_criteria": [...],
                "decision_triggers": {
                  "proceed_if": "CPA < $30",
                  "pause_if": "CPA > $50",
                  "scale_if": "ROAS > 3.5"
                }
              }
            ],
            "checkpoints": [
              {
                "day": 3,
                "purpose": "Early signal check",
                "review_focus": [...],
                "action_required": false
              }
            ]
          },
          "statistical_requirements": {
            "min_conversions_per_combo": 15,
            "confidence_level": 0.90
          }
        }
    """
    gemini = get_gemini()

    # Extract constraints from knowledge facts
    daily_budget = state.get("knowledge_facts", {}).get("target_budget", {}).get("value", 1000)
    target_cpa = state.get("knowledge_facts", {}).get("target_cpa", {}).get("value", 25.0)

    # Generate timeline with temperature=0.6 (balance structure + creativity)
    timeline = gemini.generate_json(
        prompt=EXECUTION_PLANNER_PROMPT_TEMPLATE.format(...),
        system_instruction=EXECUTION_PLANNER_SYSTEM_INSTRUCTION,
        temperature=0.6,
        task_name="Execution Timeline Planning"
    )

    # Validate structure
    is_valid, errors = validate_execution_timeline(timeline)
    if not is_valid:
        # Log errors but return timeline (graceful degradation)
        print(f"Timeline validation errors: {errors}")

    return timeline
```

**Validation Function** (lines 233-296):
```python
def validate_execution_timeline(timeline: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate execution timeline structure and constraints

    Checks:
    - Total duration: 7-30 days
    - At least 2 phases
    - Budget allocations sum to 100%
    - Phase dates within range
    - Test combination budgets sum to phase budget
    - At least one checkpoint

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check total duration
    total_days = timeline.get("timeline", {}).get("total_duration_days", 0)
    if not total_days or total_days < 7 or total_days > 30:
        errors.append(f"Invalid total_duration_days: {total_days}")

    # Validate budget allocation
    phases = timeline.get("timeline", {}).get("phases", [])
    total_budget = sum(phase.get("budget_allocation_percent", 0) for phase in phases)
    if abs(total_budget - 100) > 2:  # 2% tolerance
        errors.append(f"Phase budgets sum to {total_budget}%")

    # ... more validation checks

    return len(errors) == 0, errors
```

### campaign.py

**File:** `src/modules/campaign.py`
**Purpose:** Platform-specific campaign configuration generation

**Key Function: `generate_campaign_config()`** (lines 89-234)

```python
def generate_campaign_config(
    strategy: Dict[str, Any],
    execution_plan: Dict[str, Any],
    target_budget: float,
    target_cpa: float,
    optimization_patch: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate ready-to-execute campaign configs for TikTok and Meta

    Returns:
        {
          "tiktok": {
            "campaign_name": "...",
            "objective": "CONVERSIONS",
            "daily_budget": 350.0,
            "targeting": {
              "age_range": "25-34",
              "gender": "FEMALE",
              "locations": ["United States"],
              "interests": [...]
            },
            "placements": ["TikTok Feeds"],
            "bidding": {
              "strategy": "LOWEST_COST_WITH_BID_CAP",
              "target_cpa": 25.0
            },
            "creative_specs": {
              "format": "Video",
              "messaging": [...]
            }
          },
          "meta": {...},
          "summary": {
            "total_daily_budget": 500.0,
            "experiment": "Week 1: Platform Test"
          }
        }
    """
    gemini = get_gemini()

    # If optimization patch provided, merge with strategy
    if optimization_patch:
        strategy = apply_patch_to_strategy(strategy, optimization_patch)

    # Build prompt
    prompt = CAMPAIGN_CONFIG_PROMPT_TEMPLATE.format(
        strategy=json.dumps(strategy, indent=2),
        execution_plan=json.dumps(execution_plan, indent=2),
        target_budget=target_budget,
        target_cpa=target_cpa,
        optimization_patch=json.dumps(optimization_patch or {})
    )

    # Generate with temperature=0.5 (balanced precision)
    config = gemini.generate_json(
        prompt=prompt,
        system_instruction=CAMPAIGN_CONFIG_SYSTEM_INSTRUCTION,
        temperature=0.5,
        task_name="Campaign Configuration"
    )

    return config
```

### reflection.py

**File:** `src/modules/reflection.py`
**Purpose:** Experiment result analysis and optimization patch generation

**Key Function: `analyze_experiment_results()`** (lines 67-189)

```python
def analyze_experiment_results(
    experiment_data: List[Dict],
    current_config: Dict[str, Any],
    target_cpa: float,
    target_roas: float
) -> Dict[str, Any]:
    """
    Analyze experiment performance and identify winners/losers

    Returns:
        {
          "summary": "...",
          "avg_cpa": 23.45,
          "avg_roas": 3.2,
          "total_conversions": 847,
          "threshold_status": "met" | "not_met" | "exceeded",
          "top_performers": [
            {
              "combination": "TikTok + Interest + UGC",
              "cpa": 22.10,
              "roas": 4.1,
              "conversions": 412
            }
          ],
          "underperformers": [...],
          "recommendations": [...]
        }
    """
    gemini = get_gemini()

    # Calculate aggregate metrics
    df = pd.DataFrame(experiment_data)
    avg_cpa = df['cpa'].mean()
    avg_roas = df['roas'].mean()
    total_conversions = df['conversions'].sum()

    # Determine threshold status
    if avg_cpa <= target_cpa * 0.9 and avg_roas >= target_roas * 1.1:
        threshold_status = "exceeded"
    elif avg_cpa <= target_cpa and avg_roas >= target_roas:
        threshold_status = "met"
    else:
        threshold_status = "not_met"

    # LLM analysis
    prompt = REFLECTION_PROMPT_TEMPLATE.format(
        experiment_data=df.to_dict(),
        current_config=json.dumps(current_config),
        target_cpa=target_cpa,
        target_roas=target_roas,
        avg_cpa=avg_cpa,
        avg_roas=avg_roas
    )

    analysis = gemini.generate_json(
        prompt=prompt,
        system_instruction=REFLECTION_SYSTEM_INSTRUCTION,
        temperature=0.3,  # Low temp for precision
        task_name="Performance Analysis"
    )

    # Add calculated metrics
    analysis["avg_cpa"] = avg_cpa
    analysis["avg_roas"] = avg_roas
    analysis["total_conversions"] = total_conversions
    analysis["threshold_status"] = threshold_status

    return analysis
```

**Key Function: `generate_patch_strategy()`** (lines 192-297)

```python
def generate_patch_strategy(
    performance_analysis: Dict[str, Any],
    current_config: Dict[str, Any],
    historical_winners: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate optimization patch based on performance analysis

    Returns:
        {
          "patch_type": "scaling_winners" | "budget_reallocation" | "targeting_refinement",
          "changes": {
            "budget_adjustments": {
              "tiktok": "+20%",
              "meta": "-20%"
            },
            "targeting_changes": {
              "platform": "tiktok",
              "field": "gender",
              "from": "ALL",
              "to": "FEMALE"
            },
            "creative_updates": [...]
          },
          "rationale": "TikTok outperformed Meta by 23% on CPA...",
          "expected_improvement": "Expect 15-20% CPA reduction"
        }
    """
    gemini = get_gemini()

    prompt = PATCH_GENERATION_PROMPT_TEMPLATE.format(
        performance_analysis=json.dumps(performance_analysis, indent=2),
        current_config=json.dumps(current_config, indent=2),
        historical_winners=json.dumps(historical_winners, indent=2)
    )

    patch = gemini.generate_json(
        prompt=prompt,
        system_instruction=PATCH_GENERATION_SYSTEM_INSTRUCTION,
        temperature=0.6,  # Balance creativity + precision
        task_name="Optimization Patch Generation"
    )

    return patch
```

### data_loader.py

**File:** `src/modules/data_loader.py`
**Purpose:** File parsing, type detection, and detailed analysis

**Key Class: `DataLoader`**

```python
class DataLoader:
    """Handles file parsing and type detection"""

    @staticmethod
    def detect_file_type(data: pd.DataFrame) -> str:
        """
        Auto-detect file type based on columns

        Returns: 'historical' | 'experiment_results' | 'enrichment'
        """
        columns = set(data.columns.str.lower())

        # Historical data indicators (≥3 required)
        historical_indicators = [
            'campaign_name', 'spend', 'conversions', 'cpa',
            'roas', 'ctr', 'impressions', 'clicks'
        ]
        hist_count = sum(1 for ind in historical_indicators if ind in columns)

        # Experiment result indicators
        experiment_indicators = [
            'experiment_id', 'variant', 'test_group',
            'combination_id', 'iteration'
        ]
        exp_count = sum(1 for ind in experiment_indicators if ind in columns)

        # Enrichment data indicators
        enrichment_indicators = [
            'competitor', 'market', 'benchmark',
            'industry', 'intel'
        ]
        enrich_count = sum(1 for ind in enrichment_indicators if ind in columns)

        # Decision logic
        if hist_count >= 3:
            return "historical"
        elif exp_count >= 1:
            return "experiment_results"
        elif enrich_count >= 1:
            return "enrichment"
        else:
            return "historical"  # Default fallback

    @staticmethod
    def get_detailed_analysis(data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive analysis for LLM consumption

        Returns:
            {
              "performance_summary": {
                "mean_cpa": 28.45,
                "median_cpa": 26.30,
                "min_cpa": 18.20,
                "max_cpa": 45.60,
                "mean_roas": 2.8,
                ...
              },
              "platform_breakdown": {
                "TikTok": {
                  "campaign_count": 12,
                  "avg_cpa": 23.10,
                  "avg_roas": 3.2
                },
                "Meta": {
                  "campaign_count": 8,
                  "avg_cpa": 30.45,
                  "avg_roas": 2.4
                }
              },
              "top_performers": [
                {
                  "campaign_name": "Summer Launch TikTok",
                  "cpa": 18.20,
                  "roas": 4.5,
                  "conversions": 234
                }
              ],
              "bottom_performers": [...],
              "sample_campaigns": [...]  # For context
            }
        """
        analysis = {}

        # Performance summary (all numeric columns)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        analysis["performance_summary"] = {}
        for col in numeric_cols:
            analysis["performance_summary"][col] = {
                "mean": data[col].mean(),
                "median": data[col].median(),
                "min": data[col].min(),
                "max": data[col].max()
            }

        # Platform breakdown (if platform column exists)
        if 'platform' in data.columns:
            analysis["platform_breakdown"] = {}
            for platform in data['platform'].unique():
                platform_data = data[data['platform'] == platform]
                analysis["platform_breakdown"][platform] = {
                    "campaign_count": len(platform_data),
                    "avg_cpa": platform_data['cpa'].mean() if 'cpa' in platform_data else None,
                    "avg_roas": platform_data['roas'].mean() if 'roas' in platform_data else None
                }

        # Top/bottom performers (sorted by CPA or conversions)
        sort_col = 'cpa' if 'cpa' in data.columns else 'conversions'
        ascending = True if sort_col == 'cpa' else False
        sorted_data = data.sort_values(by=sort_col, ascending=ascending)

        analysis["top_performers"] = sorted_data.head(5).to_dict('records')
        analysis["bottom_performers"] = sorted_data.tail(5).to_dict('records')

        # Sample campaigns for context
        analysis["sample_campaigns"] = data.head(10).to_dict('records')

        return analysis
```

---

## LLM Integration

### Gemini Wrapper

**File:** `src/llm/gemini.py`

**Key Class: `GeminiClient`**

```python
class GeminiClient:
    """Wrapper for Google Gemini API"""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_json(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        task_name: str = "LLM Generation"
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response

        Args:
            prompt: Main prompt
            system_instruction: System-level instructions
            temperature: 0.0-1.0 (0.3 for analysis, 0.7 for creativity)
            task_name: For progress tracking

        Returns:
            Parsed JSON dict
        """
        # Log to progress tracker
        tracker = get_progress_tracker()
        tracker.log_llm_call(
            task_name=task_name,
            prompt_preview=prompt[:200],
            temperature=temperature
        )

        # Configure generation
        generation_config = {
            "temperature": temperature,
            "response_mime_type": "application/json"  # Force JSON output
        }

        # Create model with system instruction
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=system_instruction
        )

        # Generate
        response = model.generate_content(prompt)

        # Parse JSON
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback: extract JSON from markdown code block
            result = extract_json_from_markdown(response.text)

        # Log response preview
        tracker.log_llm_call(
            task_name=f"{task_name} (response)",
            prompt_preview=json.dumps(result)[:200],
            temperature=temperature
        )

        return result
```

### Temperature Guidelines

| Task | Temperature | Module | Rationale |
|------|-------------|--------|-----------|
| Router Decision | 0.3 | `router.py` | Needs precise, deterministic routing |
| Performance Analysis | 0.3 | `reflection.py` | Data-driven analysis, no creativity needed |
| Strategy Generation | 0.7 | `insight.py` | Benefits from creative hypotheses |
| Execution Timeline | 0.6 | `execution_planner.py` | Balance structure + flexibility |
| Campaign Config | 0.5 | `campaign.py` | Needs accuracy + some variation |
| Optimization Patches | 0.6 | `reflection.py` | Creative solutions within constraints |

---

## Database Schema

### Tables

**File:** `src/database/schema.sql`

#### projects
```sql
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    product_description TEXT,
    target_budget NUMERIC DEFAULT 1000,

    -- State machine
    current_phase TEXT DEFAULT 'initialized',  -- initialized | strategy_built | awaiting_results | optimizing | completed
    iteration INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Accumulated data (JSONB for flexibility)
    historical_data JSONB DEFAULT '{}',
    market_data JSONB DEFAULT '{}',
    experiment_results JSONB DEFAULT '[]',
    knowledge_facts JSONB DEFAULT '{}',
    user_inputs JSONB DEFAULT '{}',

    -- Strategy & experiments
    current_strategy JSONB DEFAULT '{}',
    experiment_plan JSONB DEFAULT '{}',

    -- Configurations
    current_config JSONB DEFAULT '{}',
    config_history JSONB DEFAULT '[]',

    -- Performance tracking
    best_performers JSONB DEFAULT '{}',
    threshold_status TEXT DEFAULT 'not_met',
    metrics_timeline JSONB DEFAULT '[]',
    patch_history JSONB DEFAULT '[]'
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_updated_at ON projects(updated_at DESC);
```

#### sessions
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    session_num INTEGER NOT NULL,

    -- Files uploaded in this session
    uploaded_files JSONB DEFAULT '[]',  -- [{storage_path, original_filename, uploaded_at}]
    file_analysis JSONB DEFAULT '{}',   -- {file_name: {file_type, row_count, ...}}

    -- Router decision
    decision TEXT,                       -- initialize | reflect | enrich | continue
    decision_reasoning TEXT,

    -- Execution tracking
    nodes_executed TEXT[] DEFAULT '{}',
    execution_status TEXT DEFAULT 'running',  -- running | completed | failed
    error_message TEXT,

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_project_id ON sessions(project_id);
CREATE INDEX idx_sessions_started_at ON sessions(started_at DESC);
```

#### react_cycles
```sql
CREATE TABLE react_cycles (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    cycle_num INTEGER NOT NULL,
    node_name TEXT NOT NULL,

    -- ReAct pattern
    thought TEXT,                        -- Optional: LLM reasoning
    action JSONB NOT NULL,               -- {node: '...', inputs: {...}}
    observation JSONB NOT NULL,          -- {outputs: {...}, messages: [...]}

    -- Performance metrics
    execution_time_ms INTEGER,
    llm_tokens_used INTEGER,

    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_react_cycles_session_id ON react_cycles(session_id);
CREATE INDEX idx_react_cycles_project_id ON react_cycles(project_id);
CREATE INDEX idx_react_cycles_timestamp ON react_cycles(timestamp DESC);
```

### Persistence Pattern

**File:** `src/database/persistence.py`

```python
class ProjectPersistence:
    """Database operations for projects"""

    @staticmethod
    def create_project(
        user_id: str,
        project_name: str,
        product_description: str,
        target_budget: float
    ) -> str:
        """Create new project, returns project_id"""
        supabase = get_supabase_client()

        data = {
            "user_id": user_id,
            "project_name": project_name,
            "product_description": product_description,
            "target_budget": target_budget,
            "current_phase": "initialized",
            "iteration": 0
        }

        response = supabase.table("projects").insert(data).execute()
        return response.data[0]["project_id"]

    @staticmethod
    def load_project(project_id: str) -> Optional[Dict[str, Any]]:
        """Load project from database"""
        supabase = get_supabase_client()

        response = supabase.table("projects") \
            .select("*") \
            .eq("project_id", project_id) \
            .execute()

        if response.data:
            return response.data[0]
        return None

    @staticmethod
    def save_project(project_data: Dict[str, Any]):
        """Save/update project"""
        supabase = get_supabase_client()

        project_id = project_data["project_id"]
        project_data["updated_at"] = datetime.now().isoformat()

        supabase.table("projects") \
            .update(project_data) \
            .eq("project_id", project_id) \
            .execute()
```

---

## File Storage

### Supabase Storage Integration

**File:** `src/storage/file_manager.py`

```python
def upload_file(local_path: str, project_id: str) -> str:
    """
    Upload file to Supabase Storage

    Args:
        local_path: Path to local file
        project_id: Project UUID for organization

    Returns:
        storage_path: Supabase storage path
    """
    supabase = get_supabase_client()

    filename = Path(local_path).name
    storage_path = f"{project_id}/{filename}"

    # Upload to 'campaign-files' bucket
    with open(local_path, 'rb') as f:
        supabase.storage.from_("campaign-files") \
            .upload(storage_path, f, file_options={"upsert": "true"})

    return storage_path

def download_file(storage_path: str) -> bytes:
    """Download file from Supabase Storage"""
    supabase = get_supabase_client()

    response = supabase.storage.from_("campaign-files") \
        .download(storage_path)

    return response

def delete_file(storage_path: str):
    """Delete file from Supabase Storage"""
    supabase = get_supabase_client()

    supabase.storage.from_("campaign-files") \
        .remove([storage_path])
```

### Storage Organization

```
campaign-files/
├── {project_id_1}/
│   ├── historical_campaigns.csv
│   ├── experiment_results_week1.csv
│   └── experiment_results_week2.csv
├── {project_id_2}/
│   ├── performance_data.csv
│   └── market_benchmarks.json
...
```

---

## Development Patterns

### Adding a New Node

1. **Define node function** in `src/agent/nodes.py`:
```python
@track_node
def my_new_node(state: AgentState) -> AgentState:
    """
    Description of what this node does
    """
    # Extract inputs from state
    input_data = state.get("some_field")

    # Call business logic module
    from src.modules.my_module import my_function
    result = my_function(input_data)

    # Update state
    state["output_field"] = result
    state["messages"].append("My new node completed")

    return state
```

2. **Add node to graph** in `src/agent/graph.py`:
```python
workflow.add_node("my_new_node", my_new_node)
```

3. **Add routing logic** if needed:
```python
# Fixed edge
workflow.add_edge("previous_node", "my_new_node")
workflow.add_edge("my_new_node", "next_node")

# OR conditional edge
workflow.add_conditional_edges(
    "router",
    get_next_node,
    {
        ...
        "my_new_route": "my_new_node"
    }
)
```

### Adding a New LLM Task

1. **Define prompt template** in module file:
```python
MY_TASK_PROMPT_TEMPLATE = """
Your instructions here...

Data:
{data}

Respond with JSON:
{{
  "field1": "value",
  "field2": [...]
}}
"""

MY_TASK_SYSTEM_INSTRUCTION = """
You are an expert in...

Key principles:
- Principle 1
- Principle 2
"""
```

2. **Call LLM with appropriate temperature**:
```python
def my_llm_task(data: Dict) -> Dict:
    gemini = get_gemini()

    prompt = MY_TASK_PROMPT_TEMPLATE.format(data=json.dumps(data))

    result = gemini.generate_json(
        prompt=prompt,
        system_instruction=MY_TASK_SYSTEM_INSTRUCTION,
        temperature=0.5,  # Choose based on task
        task_name="My Task Name"
    )

    return result
```

### Error Handling Pattern

```python
def my_node(state: AgentState) -> AgentState:
    try:
        # Main logic
        result = risky_operation()
        state["output"] = result
        state["messages"].append("Success")

    except Exception as e:
        # Log error, don't crash
        error_msg = f"Error in my_node: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(f"⚠ {error_msg}")

        # Optionally set fallback values
        state["output"] = {}

    return state
```

### Testing a Node

```python
# Create mock state
test_state = create_initial_state(
    project_id="test-project",
    uploaded_files=[]
)
test_state["some_input"] = mock_data

# Run node
result_state = my_new_node(test_state)

# Assert outputs
assert "output_field" in result_state
assert len(result_state["messages"]) > 0
```

---

## Performance Optimizations

### 1. State Compression

Only essential data is stored in DB. Raw data is discarded after processing:

```python
# ✅ Good: Store metadata only
state["historical_data"] = {
    "metadata": {"file_count": 3, "total_rows": 1234},
    "summary": {...}  # Aggregated analysis
}

# ❌ Bad: Store raw data
state["historical_data"] = {
    "raw_data": df.to_dict()  # 10MB+ of data
}
```

### 2. Temporary Node Outputs

Use `node_outputs` for inter-node communication (not persisted):

```python
# In reflection_node
state["node_outputs"]["reflection_analysis"] = analysis

# In adjustment_node
analysis = state["node_outputs"].get("reflection_analysis")
```

### 3. LLM Call Caching

Identical prompts reuse previous responses (Gemini built-in caching).

### 4. Batch File Uploads

Upload multiple files in one session to minimize round-trips.

---

## Security Considerations

### API Keys

- Never commit `.env` to git
- Use environment variables for all secrets
- Rotate keys regularly

### File Uploads

- Validate file types before upload
- Limit file sizes (max 10MB per file)
- Scan for malicious content (CSV/JSON only)

### Database Access

- Use Row Level Security (RLS) in Supabase
- Filter by user_id in all queries
- Never expose project_ids publicly

---

## Troubleshooting

### Common Issues

**Issue: "NaN values are not JSON compliant"**
- **Cause:** Raw DataFrame with NaN stored in state
- **Fix:** Use `state_to_project_dict()` which sanitizes NaN → null

**Issue: "Router stuck in loop"**
- **Cause:** `current_phase` not updated after node execution
- **Fix:** Ensure nodes update `current_phase` appropriately

**Issue: "LLM returns invalid JSON"**
- **Cause:** Gemini occasionally returns markdown-wrapped JSON
- **Fix:** Use `extract_json_from_markdown()` fallback in `gemini.py`

**Issue: "File not found in storage"**
- **Cause:** Storage path mismatch
- **Fix:** Use `{project_id}/{filename}` pattern consistently

---

## Next Steps for Contributors

1. **Read this document** thoroughly
2. **Review CLAUDE.md** for implementation details
3. **Explore examples/** directory for sample data
4. **Run CLI with sample data** to see full flow
5. **Check CONTRIBUTING.md** for PR guidelines
6. **Join discussion** on GitHub Issues

---

**Document Version:** 1.0
**Last Updated:** 2025-10-13
**Maintainer:** Adronaut Team

For questions, open an issue on GitHub or contact the maintainers.

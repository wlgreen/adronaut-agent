# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with: GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY, TAVILY_API_KEY (optional)
```

### Database Setup
Run `src/database/schema.sql` in your Supabase SQL Editor to create:
- `projects` - Main persistent state across sessions
- `sessions` - Logs each interaction
- `react_cycles` - Audit trail of node executions

### Running the Agent

```bash
# New project (by name)
python cli.py run --project-id my-campaign-001

# Existing project (by UUID)
python cli.py run --project-id 8f7a2b1c-4e3d-9a5f-1b2c-3d4e5f6a7b8c
```

The CLI will prompt for comma-separated file paths. The agent automatically detects file types.

## Core Architecture

### LangGraph Workflow

The agent is built on **LangGraph** (stateful multi-step workflows) with **Gemini 2.0 Flash** for LLM reasoning. The workflow follows a **router-based architecture** where an LLM decides which path to take based on project state and uploaded files.

#### State Management (`src/agent/state.py`)

**AgentState** is a TypedDict that flows through all nodes. Key state fields:
- **Session metadata**: `project_id`, `session_num`, `cycle_num`
- **Router decision**: `decision` (initialize/reflect/enrich/continue), `decision_reasoning`
- **Project state**: `current_phase`, `iteration`, `project_loaded`
- **Accumulated data**: `historical_data`, `market_data`, `experiment_results`
- **Strategy & config**: `current_strategy`, `current_config`, `config_history`
- **Performance tracking**: `best_performers`, `threshold_status`, `metrics_timeline`, `patch_history`

#### Workflow Execution Flow (`src/agent/graph.py`)

```
load_context → analyze_files → router → [conditional routing]
```

**Router decisions** (`src/agent/router.py`):
- `initialize`: New project → `data_collection` → `insight` → `campaign_setup` → `save`
- `reflect`: Experiment results uploaded → `reflection` → `adjustment` → `save`
- `enrich`: Additional data uploaded → `data_collection` → (resume flow)
- `continue`: Resume incomplete flow based on `current_phase`

The router is **LLM-powered** (temperature: 0.3) and examines:
1. Whether project exists (`project_loaded`)
2. File types from analysis (historical/experiments/enrichment)
3. Current phase (initialized/strategy_built/awaiting_results/optimizing)

#### Two Main Execution Paths

**Initialize Path** (new project with historical data):
1. `data_collection_node`: Merges uploaded files into state, optionally searches web for benchmarks via Tavily
2. `insight_node`: Calls `generate_insights_and_strategy()` with historical data → generates strategy + flexible execution timeline (7-30 days)
3. `campaign_setup_node`: Calls `generate_campaign_config()` → produces TikTok/Meta configs
4. `save_state_node`: Persists state to Supabase via `ProjectPersistence.save_project()`

**Reflect Path** (existing project with experiment results):
1. `reflection_node`: Calls `analyze_experiment_results()` → compares performance vs thresholds
2. `adjustment_node`: Calls `generate_patch_strategy()` → creates optimization patches, generates new config
3. `save_state_node`: Saves updated state with new iteration

### State Persistence Pattern

**Load on entry** (`load_context_node`):
```python
project_data = ProjectPersistence.load_project(project_id)
if project_data:
    state = load_project_into_state(state, project_data)  # Hydrates AgentState from DB
```

**Save on exit** (`save_state_node`):
```python
project_data = state_to_project_dict(state)  # Converts AgentState to DB format
ProjectPersistence.save_project(project_data)
```

This enables **multi-session continuity**: Upload historical data in session 1, upload experiment results in session 2, etc. All accumulated data persists.

## Data Processing

### File Type Detection (`src/modules/data_loader.py`)

**DataLoader** automatically classifies CSV/JSON files:
- **historical**: Has campaign_name, spend, conversions, CPA, ROAS, etc. (≥3 campaign indicators)
- **experiment_results**: Has experiment_id, variant, test_group, etc.
- **enrichment**: Has competitor, market, benchmark, industry, etc.

**Key method**: `get_detailed_analysis()` generates comprehensive analysis for LLM consumption:
- Performance summaries (mean/median/min/max for all numeric columns)
- Platform breakdowns (if platform column exists)
- Top/bottom performers sorted by CPA or conversions
- Sample campaigns for context

This detailed analysis is passed to `generate_insights_and_strategy()` to ensure **data-driven insights** (not generic recommendations).

### LLM Integration (`src/llm/gemini.py`)

All LLM calls use descriptive `task_name` for progress tracking:

| Task | Temperature | Module | Purpose |
|------|-------------|--------|---------|
| Router Decision | 0.3 | `router.py` | Decides next workflow step |
| Strategy & Insights Generation | 0.7 | `insight.py` | Creates campaign strategy |
| Execution Timeline Planning | 0.6 | `execution_planner.py` | Designs flexible test timeline |
| Campaign Configuration | 0.5 | `campaign.py` | Generates platform configs |
| Performance Analysis | 0.3 | `reflection.py` | Analyzes experiment results |
| Optimization Patch Generation | 0.6 | `reflection.py` | Creates optimization patches |

**Critical detail**: `insight.py` prompt template instructs LLM to:
- Reference actual data (e.g., "TikTok had 23% lower CPA")
- Cite top/bottom performers from historical data
- Base experiment plans on data gaps and opportunities

## Important Implementation Details

### Progress Tracking

All nodes are decorated with `@track_node` which logs execution time and output messages. The `ProgressTracker` (`src/utils/progress.py`) displays:
- Colored terminal output for each node
- LLM call prompts and responses (first 200 chars)
- Execution timing for debugging

### Node Outputs for Inter-Node Communication

The `node_outputs` dict in state is used for passing data between nodes within a single flow:
```python
# In reflection_node
state["node_outputs"]["reflection_analysis"] = analysis

# In adjustment_node
analysis = state["node_outputs"].get("reflection_analysis", {})
```

### Config History and Iteration Tracking

Each optimization cycle increments `iteration` and appends to:
- `config_history`: All campaign config versions
- `patch_history`: All optimization patches with reasoning
- `metrics_timeline`: Performance analysis for each iteration

Output files are versioned: `campaign_{project_id}_v{iteration}.json`

### Tavily Web Search (Optional)

If `TAVILY_API_KEY` is set, `data_collection_node` searches for market benchmarks based on product description. If not set, agent proceeds without web data.

## Flexible Execution Timeline (NEW)

The agent now supports **LLM-powered flexible execution planning** with adaptive timelines from 7-30 days based on campaign complexity and budget.

**How it works:**
- LLM analyzes historical data, budget constraints, and strategic hypotheses
- Designs 2-3 phases (short/medium/long-term) with optimal budget allocation
- Sets checkpoints at statistically meaningful intervals
- Adapts timeline length based on:
  - Number of critical hypotheses to test
  - Available budget for testing
  - Expected conversion volume
  - Complexity of campaign variables

**Key files:**
- `src/modules/execution_planner.py`: LLM-powered timeline generator with validation
- `src/modules/insight.py`: Calls execution planner after generating strategy
- `cli.py`: New display function for execution timeline (line 200-324)

**Generated plan structure:**
```json
{
  "timeline": {
    "total_duration_days": 14,
    "reasoning": "Why this timeline length was chosen",
    "phases": [
      {
        "name": "Short-term Discovery",
        "duration_days": 5,
        "start_day": 1,
        "end_day": 5,
        "budget_allocation_percent": 35,
        "objectives": ["Objective 1", "Objective 2"],
        "test_combinations": [/* Platform + Audience + Creative combos */],
        "success_criteria": ["Criteria 1"],
        "decision_triggers": {
          "proceed_if": "CPA < $30 in at least 2 combinations",
          "pause_if": "CPA > $50 across all combinations"
        }
      }
      /* Additional phases... */
    ],
    "checkpoints": [
      {
        "day": 3,
        "purpose": "Early signal check",
        "review_focus": ["Check for obvious losers"],
        "action_required": false
      }
    ]
  },
  "statistical_requirements": {
    "min_conversions_per_combo": 15,
    "confidence_level": 0.90
  }
}
```

**Key benefits:**
- Adapts timeline to campaign needs (not rigid 7 or 21 days)
- Strategic budget allocation across phases
- Clear checkpoint schedule with review frequencies
- Risk mitigation with early warning signals
- Data-driven phase design based on historical performance

## Data Collection & Enhancement

The agent has multiple mechanisms for gathering context:

1. **Web search**: `data_collection_node` uses Tavily to search for market benchmarks (line 138-152 in `nodes.py`)
2. **User data collection**: Accepts multiple file uploads per session, merges into accumulated state
3. **Discovery node**: Parallel strategies (LLM inference + web search + user prompts) with minimal friction

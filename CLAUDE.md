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

**Optional**: Supabase Storage bucket for file uploads (see `SUPABASE_STORAGE_SETUP.md`)

### Running the Agent

```bash
# New project (by name) - creates UUID automatically
python cli.py run --project-id my-campaign-001

# Existing project (by UUID)
python cli.py run --project-id 8f7a2b1c-4e3d-9a5f-1b2c-3d4e5f6a7b8c

# Resume interrupted workflow with --resume flag
python cli.py run --project-id my-campaign-001 --resume

# Force restart even if resumption possible
python cli.py run --project-id my-campaign-001 --force-restart
```

The CLI will prompt for comma-separated file paths. The agent automatically detects file types (historical/experiment_results/enrichment).

### Test Creative Workflow

The `test-creative` command runs a **local-only** standalone creative generation workflow for testing and experimentation. This workflow requires **no database setup** - it runs entirely locally and outputs JSON files.

**Workflow Steps:**
1. **Generate**: LLM creates initial creative prompt from product description
2. **Review**: Automated review and upgrade of prompt quality (10-point checklist)
3. **Creative**: Final output ready for image generation with validation
4. **Rate**: LLM-based scoring with keyword analysis, brand presence, prompt adherence

**Usage Examples:**

```bash
# Basic usage
python cli.py test-creative \
  --product-description "Premium wireless headphones with active noise cancellation" \
  --platform Meta

# With product image and quality checks
python cli.py test-creative \
  --product-description "Premium wireless headphones with active noise cancellation" \
  --product-image /path/to/headphones.jpg \
  --platform Meta \
  --keywords "noise cancellation,wireless,premium" \
  --brand-name "AudioTech" \
  --creative-style "Aspirational lifestyle"

# Specify audience and output file
python cli.py test-creative \
  --product-description "Premium wireless headphones" \
  --platform TikTok \
  --audience "Tech enthusiasts 25-40" \
  --output my_test_results.json

# Test for Google Ads
python cli.py test-creative \
  --product-description "Product description here" \
  --platform Google \
  --audience "Small business owners"
```

**Available Platforms:**
- `Meta` (default) - Feed (1:1), Stories (9:16), Mobile Feed (4:5)
- `TikTok` - Primary (9:16), Secondary (1:1)
- `Google` - Responsive (1.91:1), Square (1:1)

**Rating Criteria:**
The LLM evaluates prompts on 8 categories (0-10 each):
- Keyword Presence - Required keywords present
- Brand/Logo Visibility - Brand name and logo clearly described
- Prompt Adherence - Follows platform/audience/style requirements
- Visual Clarity - Clear, specific visual description
- Product Fidelity - Product accurately represented
- Professional Quality - Cinema-quality language
- Completeness - All required elements present
- Authenticity - Platform-appropriate voice

**Output:**
- **JSON file**: `output/test_creatives/test_creative_<timestamp>.json` (local file only, no database)
- **Terminal**: Pretty-printed results with scores, strengths, weaknesses, suggestions

**Code Structure:**
- `src/modules/creative_rater.py` - LLM-based rating with detailed criteria
- `src/workflows/test_creative_workflow.py` - Orchestrates 4-step workflow (local-only)
- `cli.py` - `test_creative_command()` and `display_test_creative_results()`

**Shared Implementation:**
The test workflow reuses existing production components:
- `src/modules/creative_generator.py` - `generate_creative_prompts()` for step 1
- `src/modules/creative_generator.py` - `review_and_upgrade_visual_prompt()` for step 2
- Platform specs and validation from `creative_generator.py`

This ensures the test workflow uses the same generation logic as the main campaign agent, making test results directly applicable to production campaigns.

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
| Creative Prompt Generation | 0.7 | `creative_generator.py` | Generates visual prompts & ad copy |
| Creative Rating | 0.4 | `creative_rater.py` | Rates creative quality (0-100) |
| Image Generation | N/A | `gemini.py` | Imagen model for image generation |

**Critical detail**: `insight.py` prompt template instructs LLM to:
- Reference actual data (e.g., "TikTok had 23% lower CPA")
- Cite top/bottom performers from historical data
- Base experiment plans on data gaps and opportunities

**Gemini Model**: Default is `gemini-2.0-flash-exp` (set via `GEMINI_MODEL` env var)

## Important Implementation Details

### Progress Tracking

All nodes are decorated with `@track_node` which logs execution time and output messages. The `ProgressTracker` (`src/utils/progress.py`) displays:
- Colored terminal output for each node
- LLM call prompts and responses (first 200 chars)
- Execution timing for debugging

Use `get_progress_tracker()` to get the singleton tracker instance.

### Node Outputs for Inter-Node Communication

The `node_outputs` dict in state is used for passing data between nodes within a single flow:
```python
# In reflection_node
state["node_outputs"]["reflection_analysis"] = analysis

# In adjustment_node
analysis = state["node_outputs"].get("reflection_analysis", {})
```

**Important**: `node_outputs` is ephemeral and NOT persisted to database. Use it only for passing data between nodes in a single session.

### Config History and Iteration Tracking

Each optimization cycle increments `iteration` and appends to:
- `config_history`: All campaign config versions
- `patch_history`: All optimization patches with reasoning
- `metrics_timeline`: Performance analysis for each iteration

Output files are versioned: `campaign_{project_id}_v{iteration}.json`

### Tavily Web Search (Optional)

If `TAVILY_API_KEY` is set, `data_collection_node` searches for market benchmarks based on product description. If not set, agent proceeds without web data.

### Flow Resumption

The agent supports resuming interrupted workflows:

**How it works**:
1. Each node marks itself as `current_executing_node` before execution
2. On completion, updates `last_completed_node` and appends to `completed_nodes`
3. If execution fails/stops, state contains exact resumption point
4. Use `--resume` flag to continue from last checkpoint
5. Use `--force-restart` to start fresh even if resumable

**Key fields** (`src/agent/state.py`):
- `last_completed_node`: Last successfully completed node
- `completed_nodes`: List of all completed nodes in order
- `flow_status`: `not_started` | `in_progress` | `completed` | `failed`
- `current_executing_node`: Currently running node (for crash recovery)
- `is_resuming`: Boolean flag indicating resumption mode

**Router logic** (`src/agent/router.py`):
- `get_resume_node()`: Determines next node based on last completed
- Skips already-completed nodes when resuming

See `RESUMPTION_GUIDE.md` for detailed documentation.

## Creative Generation Workflow

The system includes a complete creative generation pipeline:

**Components**:
1. **`src/modules/creative_generator.py`**: Generates visual prompts, ad copy, hooks
   - `generate_creative_prompts()`: Creates platform-specific creative assets
   - `review_and_upgrade_visual_prompt()`: LLM-powered quality review (10-point checklist)
   - `validate_creative_prompt()`: Platform compliance validation

2. **`src/modules/creative_rater.py`**: LLM-based quality rating system
   - `rate_creative_prompt()`: Rates prompts 0-100 across 8 categories
   - `rate_generated_image()`: Reviews generated images for prompt adherence
   - Categories: Keyword Presence, Brand Visibility, Visual Clarity, Product Fidelity, etc.

3. **`src/workflows/test_creative_workflow.py`**: 6-step standalone workflow
   - Step 1: Generate initial creative prompt
   - Step 2: Review and upgrade prompt
   - Step 3: Validate final creative
   - Step 4: Rate creative quality
   - Step 5: Generate image from prompt (Imagen)
   - Step 6: Review/rate generated image

**Platform Specifications**:
- **Meta**: Feed (1:1), Stories (9:16), Mobile Feed (4:5) | 125 char primary text, 40 char headline
- **TikTok**: Primary (9:16), Secondary (1:1) | 100 char text limit
- **Google**: Responsive (1.91:1), Square (1:1) | 30 char headline, 90 char description

**Usage in main workflow**:
Creative prompts are automatically generated for each test combination in the execution timeline during the `campaign_setup_node`. The system generates platform-specific visual prompts and ad copy based on strategy, audience segments, and creative styles.

## Flexible Execution Timeline

The agent supports **LLM-powered flexible execution planning** with adaptive timelines from 7-30 days based on campaign complexity and budget.

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

1. **Web search**: `data_collection_node` uses Tavily to search for market benchmarks (optional, requires API key)
2. **User data collection**: Accepts multiple file uploads per session, merges into accumulated state
3. **Discovery node**: Parallel strategies (LLM inference + web search + user prompts) with minimal friction

## Testing

```bash
# Run specific test file
python -m pytest tests/test_creative_generation.py -v

# Run all tests
python -m pytest tests/ -v

# Run Meta Ads API tests (requires credentials)
python -m pytest tests/test_meta_ads_api.py -v

# Run integration tests
python -m pytest tests/integration/ -v
```

## Meta Ads API Integration

The system includes full Meta Marketing API integration for automated campaign deployment:

**Configuration** (`.env`):
- `META_ACCESS_TOKEN` - Meta Marketing API access token
- `META_AD_ACCOUNT_ID` - Ad account ID (format: `act_XXXXXXXXX`)
- `META_PAGE_ID` - Facebook Page ID for creative publishing
- `META_INSTAGRAM_ACTOR_ID` - Instagram actor ID (optional)
- `META_API_VERSION` - API version (default: `v24.0`)
- `META_DRY_RUN` - Set `true` to log API calls without executing
- `META_SANDBOX_MODE` - Set `true` to use Meta's sandbox environment

**Key Files**:
- `src/integrations/meta_ads.py` - Full Meta API implementation (campaigns, ad sets, creatives)
- `docs/META_ADS_API_V24_UPDATES.md` - Latest API changes and Advantage+ features
- `docs/META_ADS_TESTING_GUIDE.md` - Testing strategies and sandbox setup
- `docs/MANUAL_META_ADS_SETUP.md` - Step-by-step manual deployment guide

**Features**:
- Advantage+ campaign structure (v23.0+)
- Automated audience targeting with `advantage_audience`
- Creative upload to Facebook/Instagram
- Budget optimization and placement flexibility
- Rate limiting and error handling

## Image Generation

The creative workflow includes AI image generation using Gemini's Imagen model:

**Usage**:
```python
from src.llm.gemini import get_gemini
gemini = get_gemini()

result = gemini.generate_image(
    prompt="Visual prompt here",
    aspect_ratio="1:1",  # or "9:16", "16:9", "4:5"
    task_name="Creative Generation"
)
# Returns: {"success": bool, "image_path": str, "model": str}
```

Images are saved to `output/generated_images/` with timestamped filenames.

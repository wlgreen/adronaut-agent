# Campaign Setup Agent

An intelligent autonomous agent that transforms campaign data into optimized advertising strategies with continuous learning and experimentation.

## Features

- **Intelligent Routing**: LLM-based decision making determines whether to initialize, reflect, or enrich based on uploaded data
- **Meta Deployment (Real)**: Can create **campaign + ad set + creatives + ads** in Meta Ads (safe default: **PAUSED**)
- **Auto-Discovery**: Minimal input required - agent infers product context, competitors, and benchmarks
- **Sequential Experiments**: Designs and documents 3-week experiment plans (platform, audience, creative tests)
- **Multi-Session Support**: Full context persistence across sessions for long-running optimization cycles
- **Complete Configs**: Generates ready-to-execute campaign configurations for TikTok and Meta platforms
- **Iterative Optimization**: Analyzes experiment results and automatically generates patch strategies

## Architecture

Built on:
- **LangGraph**: Orchestrates a Plan → Execute → Verify loop
- **Gemini 2.0 Flash**: Powers planning, strategy generation, and analysis
- **Local-first persistence** (recommended for demos): checkpoints + artifacts under `ADRONAUT_HOME`
- **Supabase** (optional): can be disabled via `ADRONAUT_DISABLE_DB=1`
- **Tavily** (optional): web search for benchmarks/competitive intelligence

## Setup

### 1. Prerequisites

- Python 3.10+
- Supabase account
- Gemini API key
- Tavily API key (optional, for web search)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

#### Core
```
GEMINI_API_KEY=your_gemini_api_key
```

#### Local-first demo mode (recommended)
```
ADRONAUT_HOME=~/adronaut
ADRONAUT_DISABLE_DB=1
```

#### Optional: Supabase persistence (disable with ADRONAUT_DISABLE_DB=1)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

#### Optional
```
TAVILY_API_KEY=your_tavily_key
```

### 4. Setup Database (optional)

If you want Supabase persistence, set `SUPABASE_URL` + `SUPABASE_KEY` and:

1. Go to your Supabase project SQL Editor
2. Run the schema from `src/database/schema.sql`
3. Verify tables created: `projects`, `sessions`, `react_cycles`

## Usage

### Basic Workflow

```bash
# Session 1: Initial setup with historical data
python cli.py run --project-id eco-bottle-001 --inputs ./data/historical_campaigns.csv

# Session 2: Upload experiment results (after running campaigns)
python cli.py run --project-id eco-bottle-001 --inputs ./data/week1_results.csv

# Session 3: Continue optimization
python cli.py run --project-id eco-bottle-001 --inputs ./data/week2_results.csv
```

### Approval-gated steps (campaign_setup / adjustment)

Some steps intentionally pause before executing (to prevent unintended changes).

Resume a pending step with:
```bash
python cli.py run --project-id eco-bottle-001 --approve
```


### Deploy to Meta (creates real objects, default PAUSED)

⚠️ Approval gate: you must type **YES** before any Meta API writes occur.

```bash
# Create campaign + ad set + (optionally) creatives + ads
python cli.py deploy-to-meta --config-path campaign_eco-bottle-001_v0.json

# Test mode (logs API calls, creates nothing)
python cli.py deploy-to-meta --config-path campaign_eco-bottle-001_v0.json --dry-run
```

**To create actual creatives/ads**, set:
- `META_ACCESS_TOKEN`
- `META_AD_ACCOUNT_ID` (act_...)
- `META_PAGE_ID`

And include an image via `meta.creative_specs.image_url` or `image_path`.

By default, if you don’t provide `creative_assets`, the deploy step will synthesize **3 image creatives** for a quick demo.

### Monitor Meta

```bash
python cli.py monitor-meta --campaign-id <campaign_id> --since 2026-01-01 --until 2026-01-07
# or
python cli.py monitor-meta --deployment-result campaign_eco-bottle-001_v0_deployment_result.json --since 2026-01-01 --until 2026-01-07
```

### Watch Meta (Guardrails + Snapshots)

Cron-friendly monitoring that pulls **today** + **trailing 7d** insights and checks guardrails:
- Spend > daily cap
- CTR drop > 20% vs trailing 7d avg
- CPA up > 20% vs target

```bash
python cli.py watch-meta --deployment-result \
  $ADRONAUT_HOME/projects/eco-bottle-001/artifacts/deployments/campaign_eco-bottle-001_v0_deployment_result.json
```

Creates a snapshot in:
`$ADRONAUT_HOME/projects/<project_id>/artifacts/snapshots/<timestamp>.json`

### Auto Watch (prepare mode)

Automatically pulls metrics from the Meta API and, if guardrails breach, triggers the agent up to the approval gate.

```bash
python cli.py auto-watch --project-id eco-bottle-001 --mode prepare
```

It persists the fetched payload for debugging under:
`$ADRONAUT_HOME/projects/<project_id>/analysis/derived/meta_watch/<timestamp>.json`

### Setup Cron

Print a crontab entry for hourly monitoring from 9am-9pm:

```bash
python cli.py setup-cron --deployment-result campaign_eco-bottle-001_v0_deployment_result.json
```


### File Formats

The agent automatically detects file types based on columns:

**Historical Campaign Data** (CSV/JSON):
```csv
campaign_name,spend,conversions,cpa,ctr,roas,impressions,clicks
Summer Campaign,1500,75,20.0,2.5,3.5,50000,1250
```

**Experiment Results** (CSV/JSON):
```csv
experiment_id,variant,date,spend,conversions,cpa,ctr,roas
exp_001,TikTok,2024-01-15,300,18,16.67,3.2,4.1
exp_001,Meta,2024-01-15,200,10,20.00,2.1,3.0
```

**Enrichment Data** (CSV/JSON):
```csv
competitor,market,benchmark_cpa,benchmark_ctr
Competitor A,Water Bottles,22.5,2.8
```

### How It Works

The system supports an **agentic Plan → Execute → Verify** loop (built on LangGraph), while still using routing signals (initialize/reflect/enrich) to choose the right high-level objective.

1. **Upload Files**: Analyze file type (historical, experiment results, enrichment)
2. **Route (high-level intent)**: decide the objective:
   - **Initialize**: new project → build strategy + first config
   - **Reflect**: results uploaded → analyze + propose patch
   - **Enrich**: new context → refresh strategy/config
3. **Plan**: planning agent produces a structured plan (steps + success criteria)
4. **Execute**: executor runs one step at a time (reusing existing modules: discovery/data_collection/insight/creative/campaign/reflection/adjustment)
5. **Verify**: verifier checks outputs vs criteria; on failure it triggers re-plan (MVP: simple retry/replan)
6. **Save**: state + artifacts persisted for resumption

Output includes campaign configuration + optional artifacts (e.g., creative prompts) saved as JSON.

### Example Output

```
============================================================
  Session Results
============================================================

Project ID: eco-bottle-001
Session: 2
Decision: reflect
Phase: optimizing
Iteration: 1

--- Messages ---
  • Loaded existing project: eco-bottle-001
  • Analyzed week1_results.csv: experiment_results, 10 rows
  • Router decision: reflect
  • Performance below threshold, optimizing...
  • Configuration updated to v1

--- Campaign Configuration ---
  Total Daily Budget: $500
  Experiment: Platform allocation optimization

  TikTok:
    Budget: $350
    Objective: CONVERSIONS

  Meta:
    Budget: $150
    Objective: CONVERSIONS

✓ Configuration saved to: campaign_eco-bottle-001_v1.json

--- Key Insights ---
  • TikTok outperformed Meta by 20% on CPA
  • Eco-conscious messaging resonates best
  • Target audience: 25-34 year olds

============================================================
```

## Project Structure

```
adronaut-agent/
├── src/
│   ├── agent/          # LangGraph agent logic
│   │   ├── graph.py    # Workflow assembly
│   │   ├── nodes.py    # Core agent nodes
│   │   ├── router.py   # Intelligent routing
│   │   └── state.py    # State definitions
│   ├── modules/        # Business logic
│   │   ├── campaign.py         # Config generation
│   │   ├── data_loader.py      # File parsing
│   │   ├── insight.py          # Strategy builder
│   │   ├── reflection.py       # Performance analysis
│   │   └── execution_planner.py # Timeline generation
│   ├── database/       # Persistence layer
│   │   ├── client.py           # Supabase client
│   │   ├── persistence.py      # CRUD operations
│   │   └── schema.sql          # Database schema
│   ├── storage/        # File management
│   │   └── file_manager.py     # Supabase storage I/O
│   ├── llm/            # LLM integration
│   │   └── gemini.py           # Gemini wrapper
│   └── utils/          # Utilities
│       └── progress.py         # Progress tracking
├── examples/           # Sample data & outputs
│   ├── sample_historical_data.csv
│   ├── sample_experiment_results.csv
│   └── sample_outputs/
├── cli.py              # CLI interface
├── requirements.txt
├── ARCHITECTURE.md     # Technical documentation
├── CONTRIBUTING.md     # Contribution guidelines
└── .env
```

## Example Outputs

### Session Output

When you run the agent, you'll see detailed progress and results:

```
============================================================
  Session Results
============================================================

Project ID: eco-bottle-campaign-001
Session: 1
Decision: initialize
Phase: awaiting_results
Iteration: 0

--- Messages ---
  • New project: eco-bottle-campaign-001
  • Analyzed historical_q3.csv: historical, 45 rows
  • Router decision: initialize
  • Discovered 5 facts via LLM inference
  • Generated strategy with 8 insights
  • Created execution timeline: 14 days
  • Configuration generated successfully

--- Knowledge Graph ---
Total facts: 5

  product_description         Eco-friendly water bottles...  [████████  ] 0.85 (llm_inference)
  target_budget               1000.0                         [██████████] 0.95 (user_input)
  target_cpa                  25.0                           [████████  ] 0.80 (llm_inference)
  target_roas                 3.0                            [██████    ] 0.70 (llm_inference)
  market_segment              Health & Wellness              [█████████ ] 0.90 (llm_inference)

--- Campaign Configuration ---
  Total Daily Budget: $1000
  Experiment: Short-term Discovery (Days 1-5)

  TikTok:
    Budget: $600
    Objective: CONVERSIONS

  Meta:
    Budget: $400
    Objective: CONVERSIONS

✓ Configuration saved to: campaign_eco-bottle-campaign-001_v0.json
```

### Strategy Output

```json
{
  "insights": {
    "patterns": [
      "TikTok campaigns achieved 23% lower CPA ($18 vs $23) compared to Meta",
      "Female audience (25-34) showed 40% higher engagement rate",
      "UGC video content drove 3.2x ROAS vs static images (2.1x)"
    ],
    "strengths": [
      "Strong brand awareness in wellness community",
      "Proven conversion funnel with 8.5% checkout rate"
    ],
    "weaknesses": [
      "Meta platform underperforming on CPA targets",
      "Limited creative variety tested (only 3 formats)"
    ]
  },
  "target_audience": {
    "primary_segments": ["Health-conscious millennials", "Eco-warriors", "Fitness enthusiasts"],
    "demographics": {
      "age": "25-34",
      "gender": "Female-primary, All-secondary",
      "location": "United States (Urban areas)"
    },
    "interests": ["Sustainability", "Fitness", "Wellness", "Yoga", "Nutrition"]
  },
  "platform_strategy": {
    "priorities": ["TikTok", "Meta"],
    "budget_split": {"TikTok": 0.6, "Meta": 0.4},
    "rationale": "TikTok demonstrated 23% lower CPA and higher engagement with target demo"
  }
}
```

### Execution Timeline Output

```
============================================================
  EXECUTION TIMELINE (14 DAYS)
============================================================

💡 Timeline Design:
  14-day timeline chosen to allow 2 optimization cycles with
  sufficient statistical power. Budget supports 20+ conversions
  per combination for 90% confidence.

📅 TESTING PHASES (3 phases):
────────────────────────────────────────────────────────────

[1] SHORT-TERM DISCOVERY
    Days 1-5 (5 days) | Budget: 35%
    Objectives:
      • Identify winning platform
      • Test 3 audience segments
      • Validate UGC vs static creative
    Test Combinations (3):
      [15%] TikTok + Interest + UGC Video
           → Historical winner, testing scalability
      [12%] Meta + Lookalike + Static Image
           → Hedge bet for audience discovery
      [8%] TikTok + Lookalike + UGC Video
           → Testing interaction effect
    Success Criteria:
      ✓ CPA < $30 in at least 1 combination
      ✓ ROAS > 2.5x overall
    Decision Triggers:
      → Proceed if: CPA < $30 in 2+ combos
      ⚠ Pause if: CPA > $50 across all

[2] MEDIUM-TERM VALIDATION
    Days 6-11 (6 days) | Budget: 40%
    ...

📍 CHECKPOINT SCHEDULE (3 checkpoints):
────────────────────────────────────────────────────────────

  🟡 Day 3: Early Signal Check
     Focus:
       • Check for obvious losers
       • Validate tracking setup
       • Confirm conversion volume

  🔴 Day 7: Phase 1 Decision Point
     Focus:
       • Identify winning combinations
       • Calculate statistical significance
       • Decide on phase 2 allocation

────────────────────────────────────────────────────────────
  ⏱️  Total Duration: 14 days (max 30 days)
  📈 Adaptive approach based on historical performance
```

For more example outputs, see the [`examples/`](examples/) directory.

---

## Key Concepts

### Agent Flow - Detailed

**Initialize Path** (New project with historical data):
```
┌─────────────┐
│Load Context │  Check if project exists in DB
└──────┬──────┘
       ↓
┌─────────────┐
│Analyze Files│  Detect file type: historical/experiments/enrichment
└──────┬──────┘
       ↓
┌─────────────┐
│   Router    │  LLM decides: "initialize" (new project + historical data)
└──────┬──────┘
       ↓
┌─────────────┐
│  Discovery  │  Intelligent discovery: LLM inference + web search + user prompts
└──────┬──────┘
       ↓
┌─────────────┐
│Data Collect │  Merge files → historical_data, get detailed analysis
└──────┬──────┘
       ↓
┌─────────────┐
│   Insight   │  Generate strategy (insights, audience, creative, platform)
└──────┬──────┘  + execution timeline (7-30 days, adaptive)
       ↓
┌─────────────┐
│Campaign     │  Generate TikTok + Meta configs with targeting & creative
│Setup        │
└──────┬──────┘
       ↓
┌─────────────┐
│ Save State  │  Persist to Supabase (projects table)
└──────┬──────┘
       ↓
      END
```

**Reflect Path** (Existing project with experiment results):
```
┌─────────────┐
│Load Context │  Restore project state from DB
└──────┬──────┘
       ↓
┌─────────────┐
│Analyze Files│  Detect file type: experiment_results
└──────┬──────┘
       ↓
┌─────────────┐
│   Router    │  LLM decides: "reflect" (experiment results uploaded)
└──────┬──────┘
       ↓
┌─────────────┐
│ Reflection  │  Analyze performance vs thresholds
└──────┬──────┘  Identify top performers & underperformers
       ↓
┌─────────────┐
│ Adjustment  │  Generate optimization patch
└──────┬──────┘  Create new config (v1, v2, v3, ...)
       ↓
┌─────────────┐
│ Save State  │  Persist updated state + new config
└──────┬──────┘
       ↓
      END
```

### State Persistence

All agent state is saved to Supabase after each session:
- Historical data and market benchmarks
- Strategy and experiment plans
- Campaign configurations (all versions)
- Patch history and performance metrics
- Decision reasoning and insights

### LLM Router Logic

The router examines:
1. Project exists? (project_loaded)
2. File types? (historical/experiments/enrichment)
3. Current phase? (initialized/strategy_built/awaiting_results/optimizing)

Decision outcomes:
- **initialize**: No project → full setup flow
- **reflect**: Experiment results → performance analysis + patches
- **enrich**: Additional data → update strategy
- **continue**: Resume incomplete flow

## Development

### Adding New Nodes

1. Implement node function in `src/agent/nodes.py`
2. Add node to graph in `src/agent/graph.py`
3. Update router logic if needed in `src/agent/router.py`

### Testing

```bash
# Run with sample data
python cli.py run --project-id test-001
> Files: examples/sample_historical.csv
```

### Debugging

Check `react_cycles` table for complete execution trace:
```sql
SELECT * FROM react_cycles
WHERE project_id = 'your-project-id'
ORDER BY timestamp DESC;
```

## Roadmap

### Phase 2 (Future)
- Real-time performance monitoring
- API integration with TikTok/Meta Ads Manager
- Auto-execution of campaign updates
- Human-in-the-loop approval workflows

### Phase 3 (Advanced)
- Predictive performance modeling
- Cross-campaign pattern detection
- Portfolio-level optimization
- Advanced semantic memory with embeddings

## Troubleshooting

**Import errors**: Ensure virtual environment is activated and dependencies installed

**Database connection errors**: Verify Supabase credentials in `.env`

**LLM errors**: Check Gemini API key and quota

**File parsing errors**: Ensure CSV/JSON files have required columns (see File Formats section)

---

## For Collaborators

### Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Comprehensive technical documentation covering:
  - System design principles
  - LangGraph agent architecture (detailed node descriptions)
  - State management patterns
  - Router decision logic
  - Module breakdown (insight.py, campaign.py, reflection.py, etc.)
  - LLM integration guidelines
  - Database schema
  - Development patterns & best practices

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Collaboration guidelines:
  - Development setup
  - Code organization
  - Adding new nodes
  - Testing guidelines
  - Pull request process

- **[examples/](examples/)** - Sample data and outputs:
  - Sample CSV files (historical data, experiment results)
  - Sample JSON outputs (strategy, timeline, configs)
  - Annotated examples with explanations

### Quick Start for Developers

1. **Clone and setup**:
```bash
git clone <repo-url>
cd adronaut-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

2. **Read the docs**:
- Start with this README for overview
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical deep dive
- Check [examples/](examples/) for sample data

3. **Run with sample data**:
```bash
python cli.py run --project-id test-campaign
# Upload: examples/sample_historical_data.csv
```

4. **Explore the codebase**:
- `src/agent/graph.py` - Workflow definition
- `src/agent/nodes.py` - Node implementations
- `src/modules/` - Business logic modules
- `cli.py` - Entry point and output formatting

### Key Features for Contributors

- **Flexible execution timelines**: See `src/modules/execution_planner.py` - LLM-powered adaptive 7-30 day test plans
- **Intelligent discovery**: See `src/agent/nodes.py:discovery_node` - Parallel strategies (LLM + web search + user prompts)
- **Knowledge graph**: See `src/agent/state.py:knowledge_facts` - Confidence-scored facts with provenance
- **Multi-session state**: See `src/database/persistence.py` - Full state restoration across sessions
- **Progress tracking**: See `src/utils/progress.py` - Real-time node execution logging

### Architecture Highlights

```
Router-Based Workflow:
- LLM examines project state → decides next action
- Supports: initialize | reflect | enrich | continue

State-First Design:
- Single AgentState dict flows through graph
- Full visibility, resumability, debugging

Separation of Concerns:
- Nodes: Orchestration & state updates
- Modules: Pure business logic functions
- LLM: Centralized reasoning engine
```

## License

MIT

## Contributing

We welcome contributions! To get started:

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
2. Check [GitHub Issues](https://github.com/your-repo/issues) for open tasks
3. Fork the repo and create a feature branch
4. Make your changes and add tests
5. Submit a pull request with clear description

For questions or discussions, open an issue or reach out to the maintainers.

# Campaign Setup Agent

An intelligent autonomous agent that transforms campaign data into optimized advertising strategies with continuous learning and experimentation.

## Features

- **Intelligent Routing**: LLM-based decision making determines whether to initialize, reflect, or enrich based on uploaded data
- **Auto-Discovery**: Minimal input required - agent infers product context, competitors, and benchmarks
- **Sequential Experiments**: Designs and documents 3-week experiment plans (platform, audience, creative tests)
- **Multi-Session Support**: Full context persistence across sessions for long-running optimization cycles
- **Complete Configs**: Generates ready-to-execute campaign configurations for TikTok and Meta platforms
- **Iterative Optimization**: Analyzes experiment results and automatically generates patch strategies

## Architecture

Built on:
- **LangGraph**: Orchestrates multi-step agent workflow with intelligent routing
- **Gemini 2.0 Flash**: Powers reasoning, strategy generation, and decision-making
- **Supabase**: PostgreSQL database for persistent state and session management
- **Tavily**: Web search for market benchmarks and competitive intelligence

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

Required environment variables:
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
TAVILY_API_KEY=your_tavily_key  # Optional
```

### 4. Setup Database

1. Go to your Supabase project SQL Editor
2. Run the schema from `src/database/schema.sql`
3. Verify tables created: `projects`, `sessions`, `react_cycles`

## Usage

### Basic Workflow

```bash
# Session 1: Initial setup with historical data
python cli.py run --project-id eco-bottle-001
> Files: data/historical_campaigns.csv

# Session 2: Upload experiment results (after running campaigns)
python cli.py run --project-id eco-bottle-001
> Files: data/week1_results.csv

# Session 3: Continue optimization
python cli.py run --project-id eco-bottle-001
> Files: data/week2_results.csv
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

1. **Upload Files**: Agent analyzes file type (historical, experiment results, enrichment)
2. **Intelligent Routing**: LLM decides next action:
   - **Initialize**: New project → data collection → strategy → campaign setup
   - **Reflect**: Experiment results → performance analysis → optimization patches
   - **Enrich**: Additional data → strategy update → config adjustment
3. **Execute Flow**: Runs appropriate node sequence
4. **Save State**: Persists everything to database
5. **Output**: Complete campaign configuration saved as JSON

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
│   │   ├── campaign.py    # Config generation
│   │   ├── data_loader.py # File parsing
│   │   ├── insight.py     # Strategy builder
│   │   └── reflection.py  # Performance analysis
│   ├── database/       # Persistence layer
│   │   ├── client.py      # Supabase client
│   │   ├── persistence.py # CRUD operations
│   │   └── schema.sql     # Database schema
│   └── llm/            # LLM integration
│       └── gemini.py      # Gemini wrapper
├── cli.py              # CLI interface
├── requirements.txt
└── .env
```

## Key Concepts

### Agent Flow

```
┌─────────────┐
│ Load Context│ (Check if project exists)
└──────┬──────┘
       ↓
┌─────────────┐
│Analyze Files│ (Detect file types)
└──────┬──────┘
       ↓
┌─────────────┐
│   Router    │ (LLM decides next action)
└──────┬──────┘
       ↓
   ┌───┴───┐
   │       │
Initialize Reflect
   │       │
   └───┬───┘
       ↓
┌─────────────┐
│ Save State  │
└─────────────┘
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

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.

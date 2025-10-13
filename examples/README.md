# Examples Directory

This directory contains sample data files and outputs to help you understand how the Adronaut agent works.

## Sample Input Files

### sample_historical_data.csv

Historical campaign performance data used to initialize a new project.

**Use case:** Session 1 - Initialize path
**Command:**
```bash
python cli.py run --project-id eco-bottle-test
# Files: examples/sample_historical_data.csv
```

**Columns:**
- `campaign_name`: Campaign identifier
- `platform`: TikTok or Meta
- `spend`: Total spend ($)
- `impressions`: Total impressions
- `clicks`: Total clicks
- `conversions`: Total conversions
- `cpa`: Cost per acquisition ($)
- `roas`: Return on ad spend
- `ctr`: Click-through rate (%)
- `date`: Campaign date

**Key Insights** from this dataset:
- 45 campaigns across 6 months
- TikTok showed 23% lower CPA than Meta ($18 vs $23)
- Female 25-34 audience had highest engagement
- UGC video content drove 3.2x ROAS vs static images

### sample_experiment_results.csv

Experiment results from running Phase 1 campaigns.

**Use case:** Session 2 - Reflect path
**Command:**
```bash
python cli.py run --project-id eco-bottle-test
# Files: examples/sample_experiment_results.csv
```

**Columns:**
- `experiment_id`: Experiment identifier
- `combination_id`: Test combination ID
- `platform`: TikTok or Meta
- `audience`: Targeting type (Interest, Lookalike, Broad)
- `creative_format`: Video, Static, Carousel
- `spend`: Total spend ($)
- `conversions`: Total conversions
- `cpa`: Cost per acquisition ($)
- `roas`: Return on ad spend
- `date`: Experiment date

**Key Results** from this dataset:
- TikTok + Interest + UGC Video: $22 CPA, 4.1x ROAS (winner)
- Meta + Lookalike + Static: $38 CPA, 2.1x ROAS (underperformer)
- Overall performance: Met target CPA of $25

## Sample Output Files

### sample_outputs/strategy_v0.json

Generated strategy from `sample_historical_data.csv`.

**Contains:**
- Insights (patterns, strengths, weaknesses)
- Target audience (segments, demographics, interests)
- Creative strategy (messaging angles, value propositions)
- Platform strategy (priorities, budget split, rationale)

**Highlights:**
- Data-driven insights citing specific metrics
- Testable hypotheses for experiments
- Clear audience segmentation

### sample_outputs/timeline_v0.json

Execution timeline for the campaign (14 days, 3 phases).

**Contains:**
- Timeline reasoning
- Phases with objectives, test combinations, success criteria
- Checkpoints with review schedule
- Statistical requirements (90% confidence, 15+ conversions/combo)

**Highlights:**
- Adaptive timeline based on budget and complexity
- Budget allocation: 35% short-term, 40% medium-term, 25% long-term
- Clear decision triggers (proceed_if, pause_if, scale_if)

### sample_outputs/config_v0.json

Campaign configuration for TikTok and Meta platforms.

**Contains:**
- TikTok config (targeting, bidding, creative specs)
- Meta config (targeting, bidding, creative specs)
- Summary (total budget, experiment description)

**Highlights:**
- Ready-to-execute configs with all parameters
- Budget split: TikTok $600/day (60%), Meta $400/day (40%)
- Targeting based on strategy insights

### sample_outputs/patch_v1.json

Optimization patch generated after analyzing `sample_experiment_results.csv`.

**Contains:**
- Patch type (scaling_winners, budget_reallocation, targeting_refinement)
- Changes (budget adjustments, targeting changes, creative updates)
- Rationale with data citations
- Expected improvement

**Highlights:**
- Increases TikTok budget by 20% (winner)
- Decreases Meta budget by 20% (underperformer)
- Narrows targeting to female 25-34 (best performer)
- Expected CPA reduction: 15-20%

## How to Use These Examples

### 1. Test the Initialize Path

```bash
# Create new project with historical data
python cli.py run --project-id my-test-project

# When prompted for files:
Files: examples/sample_historical_data.csv

# Agent will:
# - Detect file type: historical
# - Router decision: initialize
# - Generate strategy, timeline, and config
# - Save output to: campaign_my-test-project_v0.json
```

Compare your output with `examples/sample_outputs/strategy_v0.json` and `examples/sample_outputs/config_v0.json`.

### 2. Test the Reflect Path

```bash
# Use same project, upload experiment results
python cli.py run --project-id my-test-project

# When prompted for files:
Files: examples/sample_experiment_results.csv

# Agent will:
# - Detect file type: experiment_results
# - Router decision: reflect
# - Analyze performance vs thresholds
# - Generate optimization patch
# - Create new config (v1)
# - Save output to: campaign_my-test-project_v1.json
```

Compare your output with `examples/sample_outputs/patch_v1.json`.

### 3. Inspect the Database

After running, check Supabase:

```sql
-- View project state
SELECT project_id, current_phase, iteration, updated_at
FROM projects
WHERE project_id = 'your-project-id';

-- View session history
SELECT session_num, decision, execution_status, started_at
FROM sessions
WHERE project_id = 'your-project-id'
ORDER BY started_at DESC;

-- View node execution audit trail
SELECT node_name, execution_time_ms, timestamp
FROM react_cycles
WHERE project_id = 'your-project-id'
ORDER BY timestamp DESC;
```

## Understanding the Agent Flow

### Initialize Flow (Session 1)
```
Load Context → Analyze Files → Router (initialize) →
Discovery → Data Collection → Insight → Campaign Setup → Save
```

**Key Nodes:**
- **Discovery**: Infers facts (product, budget, CPA) via LLM + web search
- **Data Collection**: Merges CSV data, generates detailed analysis
- **Insight**: Generates strategy + execution timeline
- **Campaign Setup**: Creates TikTok + Meta configs

### Reflect Flow (Session 2)
```
Load Context → Analyze Files → Router (reflect) →
Reflection → Adjustment → Save
```

**Key Nodes:**
- **Reflection**: Analyzes performance vs thresholds, identifies winners/losers
- **Adjustment**: Generates optimization patch, creates new config (v1)

## Tips for Creating Your Own Data

### Historical Data CSV Requirements

Must have **at least 3** of these columns:
- `campaign_name`, `spend`, `conversions`, `cpa`, `roas`, `ctr`, `impressions`, `clicks`

Optional but recommended:
- `platform` (TikTok, Meta, Google, etc.) - Enables platform breakdown
- `date` - Enables trend analysis
- `audience`, `creative_format` - Enables segmentation

### Experiment Results CSV Requirements

Must have **at least 1** of these columns:
- `experiment_id`, `variant`, `test_group`, `combination_id`, `iteration`

Recommended performance metrics:
- `spend`, `conversions`, `cpa`, `roas`, `ctr`

Optional:
- `platform`, `audience`, `creative_format` - For combination analysis

### Data Quality Tips

1. **Use realistic metrics**: CPA, ROAS, CTR should be industry-appropriate
2. **Include variance**: Not all campaigns should perform identically
3. **Add platform diversity**: Test multiple platforms for better insights
4. **Use date ranges**: Cover at least 30 days for temporal patterns
5. **Avoid NaN values**: Replace with 0 or remove rows

## Troubleshooting

**Issue**: Agent doesn't detect file type correctly
- **Fix**: Ensure CSV has required column names (see above)

**Issue**: Strategy is too generic
- **Fix**: Add more diverse historical data with clear patterns

**Issue**: Timeline is always 7 days
- **Fix**: Increase budget or add more hypotheses to test

**Issue**: Config missing platform
- **Fix**: Include platform column in historical data

---

For more details, see:
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical documentation
- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

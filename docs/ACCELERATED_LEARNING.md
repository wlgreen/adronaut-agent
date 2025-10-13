# Accelerated Learning Feature

## Overview

The accelerated learning feature reduces campaign optimization time from **21 days to 7 days** by testing platform, audience, and creative variations **in parallel** instead of sequentially.

## Key Differences

### Traditional Sequential Testing (21 days)
```
Week 1: Test Platform (TikTok vs Meta) → Choose winner
Week 2: Test Audience (Interest vs Broad vs Lookalike) → Choose winner
Week 3: Test Creative (UGC vs Demo vs Testimonial) → Choose winner
─────────────────────────────────────────────────────────
Total: 21 days to optimal configuration
```

### Accelerated Parallel Testing (7 days)
```
Day 1-7: Test 4-6 combinations simultaneously:
  - TikTok + Interest + UGC (30% budget)
  - TikTok + Lookalike + UGC (25% budget)
  - Meta + Interest + Testimonial (20% budget)
  - TikTok + Broad + Demo (15% budget)
  - Meta + Lookalike + UGC (10% budget)
─────────────────────────────────────────────────────────
Total: 7 days to optimal configuration
```

## How It Works

### 1. Intelligent Combination Selection
The LLM analyzes historical data to create 4-6 smart combinations:
- **Best bet (30%)**: Highest confidence based on historical winners
- **Strong hedge (25%)**: Alternative with proven performance
- **Test variations (20-25%)**: New hypotheses worth testing
- **Control/backup (10-15%)**: Safe fallback options

### 2. Memory-Based Skipping
Historical data informs what NOT to test:
```json
"memory_based_optimizations": {
  "skipped_tests": [
    "Google Ads: Historical data shows 40% higher CPA, not worth testing"
  ],
  "confident_decisions": [
    "TikTok primary platform: 80% confidence from 12 campaigns"
  ]
}
```

### 3. Statistical Confidence
Each combination needs 15-20 conversions for 90% confidence:
- Formula: `budget_per_combo / expected_cpa >= 15`
- If insufficient budget, agent recommends increasing budget or reducing combinations
- Helper function `calculate_statistical_requirements()` validates power analysis

### 4. Evaluation Schedule
- **Day 3**: Optional checkpoint to flag issues (e.g., combo with <5 conversions)
- **Day 7**: Final evaluation and winner selection

## Usage

The accelerated mode is **enabled by default** in the updated system. The LLM automatically generates parallel experiment plans.

### Generated Plan Structure

```python
{
  "mode": "accelerated",
  "total_duration_days": 7,
  "approach": "parallel_testing",
  "day_1_to_7": {
    "name": "Parallel Multi-Variable Test",
    "test_matrix": {
      "combinations": [
        {
          "id": "combo_1",
          "label": "TikTok + Fitness Interests + UGC Video",
          "platform": "TikTok",
          "audience": "Interest: fitness+wellness",
          "creative": "UGC video",
          "budget_allocation": "30%",
          "rationale": "Best historical platform + proven interest"
        }
        // ... 3-5 more combinations
      ]
    },
    "decision_criteria": {
      "min_conversions_per_combo": 15,
      "confidence_level": 0.90,
      "primary_metric": "CPA"
    },
    "evaluation_schedule": {
      "day_3": "Check preliminary results",
      "day_7": "Final evaluation"
    },
    "hypotheses": {
      "platform": "TikTok will deliver 20% lower CPA (historical: $18 vs $23)",
      "audience": "Interest targeting will beat broad by 10-15%",
      "creative": "UGC video will drive 20% higher ROAS",
      "interaction": "Best combo will emerge from synergy effects"
    }
  }
}
```

## Benefits

1. **3x Faster Learning**: 7 days instead of 21
2. **Interaction Effects**: Discover synergies (e.g., TikTok+UGC performs better than sum of parts)
3. **Reduced Opportunity Cost**: Start scaling winners 14 days earlier
4. **Historical Memory**: Skip obvious losers, focus budget on viable options
5. **Statistical Rigor**: Same confidence level (90%) with proper sample sizes

## Implementation Details

### Files Modified
1. **`src/modules/insight.py`**: Updated prompt template for parallel experiment generation
2. **`cli.py`**: Added `print_accelerated_experiment_plan()` for display
3. **`src/modules/accelerated_learning.py`**: Helper functions for validation and statistics

### Backward Compatibility
- Old sequential plans (with `week_1`, `week_2`, `week_3`) still work
- Display function auto-detects format based on `mode` field
- No breaking changes to existing workflows

## Example Output

When running the agent with historical data, you'll see:

```
============================================================
  EXPERIMENT PLAN (7 DAYS - PARALLEL TESTING)
============================================================
  ⚡ ACCELERATED MODE: Test everything simultaneously
============================================================

📋 Test platform, audience, and creative simultaneously

🔬 HYPOTHESES:
  Platform: TikTok will deliver 20% lower CPA (historical: $18 vs $23)
  Audience: Interest targeting will beat broad by 10-15%
  Creative: UGC video will drive 20% higher ROAS
  Interaction: Best combo will emerge from synergy effects

📊 TEST MATRIX (5 combinations running in parallel):
────────────────────────────────────────────────────────────

  [1] TikTok + Fitness Interests + UGC Video (30%)
      Platform:  TikTok
      Audience:  Interest: fitness+wellness
      Creative:  UGC video
      Why:       Best historical platform + proven interest + trending...

  [2] TikTok + Lookalike + UGC Video (25%)
      Platform:  TikTok
      Audience:  Lookalike 1%
      Creative:  UGC video
      Why:       Best platform + new audience test + trending creative

  ... (3 more combinations)

📏 DECISION CRITERIA:
  Min conversions per combo: 15
  Confidence level: 0.9
  Primary metric: CPA
  Secondary metrics: ROAS, CTR

📅 EVALUATION SCHEDULE:
  Day 3: Check preliminary results
  Day 7: Final evaluation and winner selection

🧠 MEMORY-BASED OPTIMIZATIONS:
  Skipped (based on historical data):
    ✗ Google Ads: Historical data shows 40% higher CPA
  Confident decisions:
    ✓ TikTok primary platform: 80% confidence from 12 campaigns

────────────────────────────────────────────────────────────
  → Upload results on Day 3 for checkpoint, Day 7 for final
  ⚡ TIME SAVED: 14 days vs traditional sequential testing
```

## Future Enhancements

Potential additions for later versions:
1. **Mid-cycle adaptation**: Reallocate budgets on Day 3 based on early signals
2. **Early stopping**: Kill losing combinations before Day 7
3. **Bayesian optimization**: Dynamic budget allocation using Thompson Sampling
4. **User preference**: CLI flag to choose sequential vs parallel mode

## Technical Notes

### Statistical Power Calculation
```python
def calculate_statistical_requirements(
    combinations: int,
    expected_cpa: float,
    daily_budget: float,
    test_days: int = 7
):
    budget_per_combo = (daily_budget * test_days) / combinations
    conversions_per_combo = budget_per_combo / expected_cpa

    # Need 15-20 conversions for 90% confidence
    has_power = conversions_per_combo >= 15
    return has_power
```

### Combination Selection Logic
The LLM uses historical data to create a smart portfolio:
- **60-70%** of budget to high-confidence options
- **20-30%** to exploration/new tests
- **10%** to safe fallback/control

This balances exploitation (use what we know works) with exploration (discover new winners).

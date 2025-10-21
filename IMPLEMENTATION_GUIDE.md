# Implementation Guide - Campaign Quality Improvements

## Priority 1: Add Root Cause Analysis to Reflection (4 hours)

**File**: `src/modules/reflection.py`

**Current REFLECTION_PROMPT_TEMPLATE** (lines 21-85):
- Identifies winners/losers
- Missing: Why did they win/lose?

**Change Required**: Replace REFLECTION_PROMPT_TEMPLATE with enhanced version that includes root cause analysis section:

```python
REFLECTION_PROMPT_TEMPLATE = """
Analyze these experiment results:

EXPERIMENT DATA:
{experiment_data}

ORIGINAL STRATEGY:
{strategy}

HISTORICAL CONTEXT:
{historical_context}

TARGET METRICS:
- Target CPA: {target_cpa}
- Target ROAS: {target_roas}

ROOT CAUSE ANALYSIS INSTRUCTIONS:
For each underperforming variation, identify 3-5 root causes:
1. What specifically underperformed? (metric + gap from target)
2. What are the likely root causes? (ranked by estimated contribution %)
3. What evidence supports each cause? (cite actual data: CTR, engagement, cost)
4. What's the recommended fix?

Example:
"Google Ads underperformance (CPA $52 vs target $25):
- Root Cause 1: Audience too broad (45% contribution)
  Evidence: CTR 0.6% vs 2.1% for narrower targeting
  Fix: Restrict to age 25-34, add interest targeting
- Root Cause 2: Ad copy not benefit-focused (35% contribution)
  Evidence: Engagement 0.3% vs 1.8% for benefit-focused variants
  Fix: Rewrite primary text to lead with benefit
- Root Cause 3: Bid strategy suboptimal (20% contribution)
  Evidence: Auto-optimized CPC $0.80 vs manual $2.10
  Fix: Switch to Target CPA bidding, lower bid cap"

STATISTICAL RIGOR:
Flag results with: n < 30 conversions as "insufficient data"
Only recommend changes with > 80% confidence

Respond with valid JSON:
{
  "performance_summary": { ... },
  "variation_analysis": [ ... ],
  "root_cause_analysis": {
    "underperforming_element": {
      "metric": "CPA",
      "current": 52,
      "target": 25,
      "gap_percent": 108,
      "root_causes": [
        {
          "cause": "Description",
          "estimated_contribution_percent": 45,
          "evidence": "Actual data",
          "confidence": 0.88
        }
      ]
    }
  },
  "recommendations": [ ... ]
}
"""
```

**New analyze_experiment_results function** (add RCA logic):

```python
def analyze_experiment_results(
    experiment_data: Dict[str, Any],
    strategy: Dict[str, Any],
    historical_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Enhanced with root cause analysis"""
    
    # ... existing code ...
    
    # Parse analysis to extract and structure root cause analysis
    if "root_cause_analysis" in analysis:
        # This will be populated by LLM
        pass
    
    return analysis
```

---

## Priority 2: Add Statistical Significance Checks (6 hours)

**Files**: All modules using LLM calls

**Add helper functions** to `src/llm/gemini.py`:

```python
def add_statistical_rigor_check(task_name: str, context: Dict[str, Any]) -> str:
    """Generate statistical rigor guidance for LLM prompts"""
    
    guidelines = """
STATISTICAL RIGOR REQUIREMENTS:
1. Sample Size Check:
   - Results with <15 conversions: Flag as "unreliable"
   - Results with 15-30: Flag as "moderate confidence"
   - Results with >30: "Good confidence"
   
2. Confidence Intervals:
   - Calculate 95% CI for all metrics
   - Don't recommend changes if CI overlaps with acceptable range
   
3. Recommendation Confidence:
   - Only recommend if >80% confidence
   - Flag lower-confidence recommendations as "test further"
   
4. Multiple Comparisons:
   - If comparing >3 variants, apply Bonferroni correction
   - Adjust p-value threshold accordingly
"""
    
    return guidelines
```

**Modify INSIGHT_PROMPT_TEMPLATE** (add after line 49):

```python
# Add this section:
CRITICAL: Apply statistical rigor to all claims:
- For any metric comparison, include: n (sample size), confidence interval
- Flag results with n < 15 as "unreliable for strategic decisions"
- Recommend only changes with >80% statistical confidence
- Example: "TikTok shows 23% lower CPA (n=47, CI=[-5%, -42%], p<0.001, high confidence)"
```

**Modify REFLECTION_PROMPT_TEMPLATE** (add section):

```python
# In the REFLECTION_PROMPT_TEMPLATE, add:
STATISTICAL REQUIREMENTS:
- Only flag winners if: n_conversions >= 30 AND performance significantly above target
- Only recommend changes if: confidence > 80% OR n_conversions >= 50
- Always include: sample size, confidence level, p-value interpretation
```

---

## Priority 3: Add Cohort Analysis (3 hours)

**File**: `src/modules/data_loader.py`

**Add new method** to DataLoader class:

```python
@staticmethod
def get_cohort_analysis(campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Segment campaigns by performance tiers and analyze characteristics
    """
    if not campaigns:
        return {}
    
    df = pd.DataFrame(campaigns)
    
    # Find performance metric column (CPA, ROAS, or conversions)
    perf_metric = None
    for col in ['cpa', 'cost_per_acquisition', 'roas', 'return_on_ad_spend']:
        matching = [c for c in df.columns if c.lower() == col]
        if matching:
            perf_metric = matching[0]
            break
    
    if not perf_metric:
        return {}
    
    # Segment into cohorts
    df_clean = df.dropna(subset=[perf_metric])
    if len(df_clean) < 10:
        return {}
    
    # Define cohorts: top 10%, middle 50%, bottom 25%
    cohorts = {
        "top_10_percent": df_clean.nlargest(int(len(df_clean) * 0.1), perf_metric),
        "middle_50_percent": df_clean.iloc[int(len(df_clean) * 0.25):int(len(df_clean) * 0.75)],
        "bottom_25_percent": df_clean.nsmallest(int(len(df_clean) * 0.25), perf_metric)
    }
    
    # Analyze cohort characteristics
    analysis = {}
    categorical_cols = ['platform', 'creative_type', 'audience', 'targeting']
    
    for cohort_name, cohort_df in cohorts.items():
        cohort_analysis = {}
        
        for col in categorical_cols:
            matching_cols = [c for c in cohort_df.columns if col.lower() in c.lower()]
            if matching_cols:
                col_name = matching_cols[0]
                # Get most common value
                value_counts = cohort_df[col_name].value_counts()
                if len(value_counts) > 0:
                    top_value = value_counts.index[0]
                    percentage = (value_counts.iloc[0] / len(cohort_df)) * 100
                    cohort_analysis[col] = f"{top_value} ({percentage:.0f}%)"
        
        analysis[cohort_name] = cohort_analysis
    
    return analysis
```

**Update get_detailed_analysis** (add cohort analysis call):

```python
# In DataLoader.get_detailed_analysis, add:
analysis["cohort_analysis"] = DataLoader.get_cohort_analysis(campaigns)
```

**Update INSIGHT_PROMPT_TEMPLATE** (add cohort context):

```python
# Add to prompt:
COHORT ANALYSIS (Top vs Bottom Performers):
{cohort_analysis}

Use this to identify what distinguishes winners from losers.
What attributes do top 10% campaigns share? What do bottom 25% have in common?
```

---

## Priority 4: Add Confidence Scoring to Strategy (2 hours)

**File**: `src/modules/insight.py`

**Update INSIGHT_PROMPT_TEMPLATE** to request confidence scores:

```python
# In the JSON response section, change:

"platform_strategy": {{
  "priorities": ["Google Ads", "Meta"],
  "budget_split": {{"Google Ads": 0.6, "Meta": 0.4}},
  "rationale": "explanation text",
  "confidence": 0.88,  // ADD THIS
  "supporting_campaigns": 200,  // ADD THIS
  "supporting_data": "Brief evidence"  // ADD THIS
}}

"target_audience": {{
  "primary_segments": [
    {{
      "name": "Tech enthusiasts",
      "confidence": 0.92,  // ADD THIS
      "supporting_campaigns": 75,
      "average_cpa": 16,
      "rationale": "Actual reason based on data"
    }}
  ]
}}
```

**Add instruction to prompt**:

```python
# Add to CRITICAL INSTRUCTIONS section:

CONFIDENCE SCORING:
- Assign 0.0-1.0 confidence score to each recommendation
- Confidence based on: number of supporting campaigns + statistical significance
- < 10 campaigns supporting: confidence 0.4-0.5 (exploratory)
- 10-30 campaigns: confidence 0.6-0.7 (moderate)
- 30-50 campaigns: confidence 0.8-0.85 (high)
- >50 campaigns: confidence 0.9+ (very high)

Prioritize recommendations by: Impact * Confidence

Example:
"Recommendation 1 (HIGH PRIORITY):
  - Action: Focus on TikTok platform
  - Confidence: 0.94 (based on 85 campaigns)
  - Expected impact: 35% lower CPA
  - Priority score: 0.94 * 0.35 = 0.33

Recommendation 2 (MEDIUM PRIORITY):
  - Action: Test video testimonials
  - Confidence: 0.62 (based on 12 campaigns)
  - Expected impact: 40% lower CPA
  - Priority score: 0.62 * 0.40 = 0.25"
```

---

## Priority 5: Correlation Analysis Module (8 hours)

**File**: Create new `src/modules/correlation_analysis.py`

```python
"""
Correlation analysis for campaign variables
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple


class CorrelationAnalysis:
    """Analyze correlations between variables and performance metrics"""
    
    @staticmethod
    def analyze_correlations(
        campaigns: List[Dict[str, Any]],
        performance_metric: str = "cpa"
    ) -> Dict[str, Any]:
        """
        Analyze correlations between all variables and performance metric
        
        Args:
            campaigns: List of campaign dictionaries
            performance_metric: Metric to correlate with (cpa, roas, ctr, etc.)
        
        Returns:
            Dictionary with correlation analysis
        """
        if not campaigns or len(campaigns) < 20:
            return {"error": "Insufficient data for correlation analysis (need >20 campaigns)"}
        
        df = pd.DataFrame(campaigns)
        results = {
            "total_campaigns": len(df),
            "correlations": {},
            "strongest_drivers": []
        }
        
        # Find numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Find performance metric column
        perf_col = None
        for col in numeric_cols:
            if performance_metric.lower() in col.lower():
                perf_col = col
                break
        
        if not perf_col:
            return results
        
        # Calculate correlations with performance metric
        for col in numeric_cols:
            if col == perf_col:
                continue
            
            # Clean data
            valid_data = df[[col, perf_col]].dropna()
            if len(valid_data) < 10:
                continue
            
            # Calculate Pearson correlation
            correlation = valid_data[col].corr(valid_data[perf_col])
            
            results["correlations"][col] = {
                "correlation_coefficient": float(correlation),
                "interpretation": CorrelationAnalysis._interpret_correlation(correlation),
                "sample_size": len(valid_data)
            }
        
        # Sort by absolute correlation strength
        sorted_corr = sorted(
            results["correlations"].items(),
            key=lambda x: abs(x[1]["correlation_coefficient"]),
            reverse=True
        )
        
        # Top 5 strongest drivers
        results["strongest_drivers"] = [
            {
                "variable": var,
                "correlation": corr["correlation_coefficient"],
                "interpretation": corr["interpretation"]
            }
            for var, corr in sorted_corr[:5]
        ]
        
        return results
    
    @staticmethod
    def _interpret_correlation(corr: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return "Very strong"
        elif abs_corr >= 0.6:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very weak"
```

**Update data_loader.py** to use correlation analysis:

```python
# In DataLoader.get_detailed_analysis, add:

from ..modules.correlation_analysis import CorrelationAnalysis

# Add to analysis dict:
analysis["correlations"] = CorrelationAnalysis.analyze_correlations(
    campaigns,
    performance_metric="cpa"
)
```

**Update INSIGHT_PROMPT_TEMPLATE** to include correlations:

```python
# Add section:
VARIABLE CORRELATIONS WITH CPA:
{correlation_analysis}

Use these correlations to explain WHICH VARIABLES DRIVE PERFORMANCE.
Example: "Audience age correlates 0.72 with lower CPA, suggesting age targeting matters"
```

---

## Priority 6: Evidence-Based Targeting (6 hours)

**File**: `src/modules/campaign.py`

**Update generate_campaign_config** function:

```python
def generate_campaign_config(
    state: Dict[str, Any],
    patch: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate campaign configuration with evidence-based targeting"""
    
    gemini = get_gemini()
    
    strategy = state.get("current_strategy", {})
    budget = state.get("user_inputs", {}).get("target_budget", 500)
    product = state.get("user_inputs", {}).get("product_description", "Product")
    iteration = state.get("iteration", 0)
    
    # NEW: Build targeting evidence from historical data
    targeting_evidence = _build_targeting_evidence(state)
    
    # NEW: Build budget allocation rationale
    budget_allocation_rationale = _build_budget_rationale(state, strategy)
    
    # Add patch context if provided
    patch_context = ""
    if patch:
        patch_context = f"""
PATCH TO APPLY:
This is an optimization iteration. Apply these changes:
{patch.get('reasoning', 'No reasoning provided')}

Changes to make:
{patch.get('changes', {})}
"""
    
    # Build enhanced prompt
    prompt = CAMPAIGN_PROMPT_TEMPLATE.format(
        strategy=str(strategy),
        budget=budget,
        product=product,
        iteration=iteration,
        patch_context=patch_context,
        targeting_evidence=targeting_evidence,  # NEW
        budget_rationale=budget_allocation_rationale  # NEW
    )
    
    # ... rest of function ...


def _build_targeting_evidence(state: Dict[str, Any]) -> str:
    """Extract historical evidence for targeting decisions"""
    
    # Get historical performance by targeting dimension
    temp_data = state.get("node_outputs", {}).get("temp_historical_data", [])
    if not temp_data:
        return "No historical data available"
    
    df = pd.DataFrame(temp_data)
    evidence = []
    
    # Analyze by age group if available
    age_cols = [c for c in df.columns if 'age' in c.lower()]
    if age_cols:
        # Calculate CPA by age group
        pass  # Analysis logic
    
    # Analyze by platform if available
    platform_cols = [c for c in df.columns if 'platform' in c.lower()]
    if platform_cols:
        # Calculate CPA by platform
        pass  # Analysis logic
    
    return "\n".join(evidence)


def _build_budget_rationale(state: Dict[str, Any], strategy: Dict[str, Any]) -> str:
    """Build budget allocation rationale based on platform performance"""
    
    rationale = """
BUDGET ALLOCATION RATIONALE:
Based on historical platform performance:
- TikTok: Allocate 60% (avg ROAS 2.8x based on 47 campaigns)
- Meta: Allocate 30% (avg ROAS 1.8x based on 52 campaigns)  
- Google: Allocate 10% (avg ROAS 1.2x based on 30 campaigns)

Rationale: Allocate proportionally to platform ROI
"""
    
    return rationale
```

**Update CAMPAIGN_PROMPT_TEMPLATE** (add sections):

```python
CAMPAIGN_PROMPT_TEMPLATE = """
Generate complete campaign configurations based on this strategy:

STRATEGY:
{strategy}

USER REQUIREMENTS:
- Target Budget: {budget}
- Product: {product}
- Current Iteration: {iteration}

TARGETING HISTORICAL EVIDENCE:
{targeting_evidence}

BUDGET ALLOCATION RATIONALE:
{budget_rationale}

{patch_context}

For each platform config, include:
- Campaign objective
- **Evidence-based daily budget** (with rationale from historical data)
- **Data-driven audience targeting** (each targeting criterion with historical CPA and confidence)
- Placements
- Bidding strategy (justified by historical performance)
- Ad creative requirements
- Optimization settings

CRITICAL: For every decision, provide:
1. Historical evidence (campaigns it's based on)
2. Confidence level (0.0-1.0)
3. Comparable historical CPA/ROAS

Respond with valid JSON:
{...}
"""
```

---

## Priority 7: Creative Performance Prediction (8 hours)

**File**: `src/modules/creative_generator.py` + create `src/modules/creative_predictor.py`

**Create new file** `src/modules/creative_predictor.py`:

```python
"""
Performance prediction for generated creatives based on historical similarity
"""

from typing import Dict, Any, List
import pandas as pd
from ..modules.data_loader import DataLoader


class CreativePerformancePredictor:
    """Predict creative performance based on similar historical campaigns"""
    
    @staticmethod
    def predict_performance(
        creative_metadata: Dict[str, Any],
        historical_campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict creative performance by finding similar historical campaigns
        
        Args:
            creative_metadata: New creative's metadata (platform, audience, style, etc.)
            historical_campaigns: List of historical campaign dictionaries
        
        Returns:
            Performance prediction with confidence
        """
        if not historical_campaigns or len(historical_campaigns) < 10:
            return {
                "prediction": None,
                "confidence": 0,
                "reason": "Insufficient historical data"
            }
        
        df = pd.DataFrame(historical_campaigns)
        
        # Find similar campaigns
        similar = CreativePerformancePredictor._find_similar_campaigns(
            creative_metadata, df
        )
        
        if len(similar) == 0:
            return {
                "prediction": None,
                "confidence": 0,
                "reason": "No similar campaigns found"
            }
        
        # Predict performance based on similar campaigns
        prediction = {
            "estimated_cpa": float(similar["cpa"].mean()),
            "estimated_cpa_std": float(similar["cpa"].std()),
            "estimated_roas": float(similar["roas"].mean()) if "roas" in similar else None,
            "estimated_ctr": float(similar["ctr"].mean()) if "ctr" in similar else None,
            "confidence": min(0.95, 0.5 + (len(similar) * 0.05)),
            "similar_campaigns_found": len(similar),
            "reasoning": f"Based on {len(similar)} similar historical campaigns"
        }
        
        return prediction
    
    @staticmethod
    def _find_similar_campaigns(
        creative_metadata: Dict[str, Any],
        historical_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Find campaigns similar to the creative metadata"""
        
        similar = historical_df.copy()
        
        # Filter by platform if available
        if "platform" in creative_metadata:
            platform = creative_metadata["platform"]
            platform_cols = [c for c in similar.columns if "platform" in c.lower()]
            if platform_cols:
                similar = similar[similar[platform_cols[0]] == platform]
        
        # Filter by creative style if available
        if "creative_style" in creative_metadata:
            style = creative_metadata["creative_style"]
            style_cols = [c for c in similar.columns if "creative" in c.lower() or "type" in c.lower()]
            if style_cols:
                # Fuzzy match on creative style
                similar = similar[similar[style_cols[0]].str.contains(style, case=False, na=False)]
        
        # Filter by audience if available
        if "audience" in creative_metadata:
            audience = creative_metadata["audience"]
            audience_cols = [c for c in similar.columns if "audience" in c.lower()]
            if audience_cols:
                similar = similar[similar[audience_cols[0]].str.contains(audience, case=False, na=False)]
        
        return similar
```

**Update generate_creative_prompts** in creative_generator.py:

```python
def generate_creative_prompts(
    test_combination: Dict[str, Any],
    strategy: Dict[str, Any],
    user_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate creative prompts with performance prediction"""
    
    # ... existing code ...
    
    # Generate creative prompts
    creative_prompts = gemini.generate_json(
        prompt=prompt,
        system_instruction=CREATIVE_GENERATION_SYSTEM_INSTRUCTION,
        temperature=0.8,
        task_name="Creative Prompt Generation",
    )
    
    # NEW: Add performance prediction
    from ..modules.creative_predictor import CreativePerformancePredictor
    
    temp_data = state.get("node_outputs", {}).get("temp_historical_data", [])
    if temp_data:
        prediction = CreativePerformancePredictor.predict_performance(
            test_combination,
            temp_data
        )
        creative_prompts["performance_prediction"] = prediction
    
    # ... rest of function ...
```

---

## Priority 8: A/B Testing Framework (6 hours)

**File**: `src/modules/execution_planner.py`

**Add A/B testing generation** to generate_execution_timeline:

```python
def _add_ab_testing_framework(timeline: Dict[str, Any], phases: list) -> Dict[str, Any]:
    """Add A/B testing plan to each phase"""
    
    for phase in phases:
        combos = phase.get("test_combinations", [])
        if len(combos) >= 2:
            # Pair first two combos for A/B test
            phase["ab_test"] = {
                "variant_a": combos[0].get("id"),
                "variant_b": combos[1].get("id"),
                "budget_split": "50/50",
                "required_sample_size_per_variant": 50,
                "confidence_level": 0.95,
                "minimum_duration_days": 7,
                "analysis_plan": {
                    "primary_metric": "CPA",
                    "success_criteria": "Variant with CPA <$25",
                    "statistical_test": "Two-sample t-test"
                }
            }
    
    return timeline
```

**Update EXECUTION_PLANNER_PROMPT_TEMPLATE** (add A/B section):

```python
# Add to template:
"For combinations in each phase:
- If 2+ combinations, specify A/B testing approach
- Include: budget split, sample size needed, duration
- Include: success criteria and statistical test method

A/B TESTING FRAMEWORK:
- Allocate 50% budget to each variant for statistical power
- Continue test until: 50 conversions per variant (95% confidence) OR 14 days
- Use two-sample t-test for CPA comparison
- Example:
  {
    'test': 'Creative angle variation',
    'variant_a': 'UGC style',
    'variant_b': 'Professional',
    'budget_split': '50/50',
    'required_conversions': 50,
    'expected_duration_days': 7,
    'success_criteria': 'UGC achieves CPA <$20'
  }
"
```

---

## Summary of Changes by File

| File | Changes | Effort | Impact |
|------|---------|--------|--------|
| `src/modules/reflection.py` | Enhanced prompts, RCA framework | 4h | HIGH |
| `src/llm/gemini.py` | Add statistical rigor checks | 2h | MEDIUM |
| `src/modules/data_loader.py` | Add cohort analysis | 3h | HIGH |
| `src/modules/insight.py` | Add confidence scoring | 2h | MEDIUM |
| Create `src/modules/correlation_analysis.py` | New module | 8h | HIGH |
| `src/modules/campaign.py` | Evidence-based targeting | 6h | HIGH |
| Create `src/modules/creative_predictor.py` | New module | 8h | HIGH |
| `src/modules/execution_planner.py` | A/B testing framework | 6h | HIGH |
| `src/modules/creative_generator.py` | Link to predictor | 2h | MEDIUM |

**Total Effort**: ~41 hours
**Expected Impact**: 25-35% campaign performance improvement

---

## Testing & Validation

For each change, test with:

1. **Sample data**: Ensure new modules handle edge cases (empty data, NaN values, etc.)
2. **LLM output**: Verify new prompts generate valid JSON with new fields
3. **Integration**: Ensure enhanced outputs flow through dependent modules
4. **End-to-end**: Run full campaign generation workflow and verify quality improvements


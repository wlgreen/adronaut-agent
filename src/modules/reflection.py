"""
Reflection and performance analysis module
"""

from typing import Dict, Any
from ..llm.gemini import get_gemini


REFLECTION_SYSTEM_INSTRUCTION = """You are an expert campaign performance analyst.

Your job is to:
1. Analyze experiment results against targets and benchmarks
2. Identify winners and losers
3. Determine if performance threshold is met
4. Provide actionable insights for optimization

Be data-driven and specific in your recommendations.
"""


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

Analyze the results and determine:
1. Which variations performed best?
2. Did we meet the performance threshold?
3. What insights can we extract?
4. What should we optimize next?

Respond with valid JSON:
{{
  "performance_summary": {{
    "total_spend": 0.0,
    "total_conversions": 0,
    "overall_cpa": 0.0,
    "overall_roas": 0.0
  }},
  "variation_analysis": [
    {{
      "variation_name": "",
      "metrics": {{"cpa": 0.0, "roas": 0.0, "ctr": 0.0}},
      "vs_target": "above/below/at target",
      "performance_rating": "excellent/good/poor"
    }}
  ],
  "winners": {{
    "best_platform": "",
    "best_audience": "",
    "best_creative": ""
  }},
  "losers": {{
    "worst_platform": "",
    "worst_audience": "",
    "worst_creative": ""
  }},
  "threshold_met": true/false,
  "threshold_gap": {{
    "cpa_gap": 0.0,
    "roas_gap": 0.0
  }},
  "insights": [
    "Key insight 1",
    "Key insight 2",
    "Key insight 3"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2",
    "Recommendation 3"
  ]
}}
"""


PATCH_SYSTEM_INSTRUCTION = """You are an expert at generating optimization patches for advertising campaigns.

Given performance analysis, generate specific, actionable changes to improve results.

Be precise about:
- What to change
- By how much
- Why this change will help
"""


PATCH_PROMPT_TEMPLATE = """
Generate an optimization patch based on this analysis:

PERFORMANCE ANALYSIS:
{analysis}

CURRENT CONFIG:
{current_config}

CURRENT STRATEGY:
{current_strategy}

ALL HISTORICAL CONTEXT:
{historical_context}

Create a patch that:
1. Addresses underperforming elements
2. Doubles down on what's working
3. Tests new hypotheses based on learnings

Respond with valid JSON:
{{
  "reasoning": "Explain the overall optimization strategy",
  "changes": {{
    "budget_adjustments": {{
      "platform_name": {{
        "change": "+20% or -15%",
        "reason": "explanation"
      }}
    }},
    "targeting_adjustments": {{
      "add_interests": [],
      "remove_interests": [],
      "reason": "explanation"
    }},
    "creative_adjustments": {{
      "new_angles": [],
      "deprecate_angles": [],
      "reason": "explanation"
    }},
    "bidding_adjustments": {{
      "target_cpa": 0.0,
      "reason": "explanation"
    }}
  }},
  "expected_impact": {{
    "cpa_improvement": "estimated %",
    "roas_improvement": "estimated %"
  }},
  "risks": ["potential risk 1", "potential risk 2"]
}}
"""


def analyze_experiment_results(
    experiment_data: Dict[str, Any],
    strategy: Dict[str, Any],
    historical_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze experiment results and determine performance

    Args:
        experiment_data: Latest experiment results
        strategy: Current strategy
        historical_context: All historical data

    Returns:
        Analysis dictionary
    """
    gemini = get_gemini()

    # Extract target metrics
    target_cpa = historical_context.get("target_cpa", 25.0)
    target_roas = historical_context.get("target_roas", 3.0)

    # Build prompt
    prompt = REFLECTION_PROMPT_TEMPLATE.format(
        experiment_data=str(experiment_data),
        strategy=str(strategy),
        historical_context=str(historical_context),
        target_cpa=target_cpa,
        target_roas=target_roas
    )

    # Generate analysis
    analysis = gemini.generate_json(
        prompt=prompt,
        system_instruction=REFLECTION_SYSTEM_INSTRUCTION,
        temperature=0.3,  # Lower temperature for analytical tasks
        task_name="Performance Analysis",
    )

    return analysis


def generate_patch_strategy(
    analysis: Dict[str, Any],
    current_config: Dict[str, Any],
    current_strategy: Dict[str, Any],
    all_historical_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate patch strategy based on performance analysis

    Args:
        analysis: Performance analysis from reflection
        current_config: Current campaign config
        current_strategy: Current strategy
        all_historical_context: Complete state with all history

    Returns:
        Patch dictionary
    """
    gemini = get_gemini()

    # Build prompt
    prompt = PATCH_PROMPT_TEMPLATE.format(
        analysis=str(analysis),
        current_config=str(current_config),
        current_strategy=str(current_strategy),
        historical_context=str(all_historical_context)
    )

    # Generate patch
    patch = gemini.generate_json(
        prompt=prompt,
        system_instruction=PATCH_SYSTEM_INSTRUCTION,
        temperature=0.6,  # Moderate creativity for optimization ideas
        task_name="Optimization Patch Generation",
    )

    return patch

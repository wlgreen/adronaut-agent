"""
Insight and strategy generation module
"""

import json
from typing import Dict, Any
from ..llm.gemini import get_gemini
from ..modules.data_loader import DataLoader


INSIGHT_SYSTEM_INSTRUCTION = """You are an expert campaign strategist specializing in digital advertising optimization.

Your job is to analyze historical campaign data, market benchmarks, and product information to generate:
1. Strategic insights about what works and what doesn't
2. A comprehensive experiment plan for testing key hypotheses
3. Clear targeting and creative recommendations

Focus on data-driven decision making and clear, testable hypotheses.
"""


INSIGHT_PROMPT_TEMPLATE = """
Analyze the following data and generate a comprehensive, data-driven campaign strategy:

PRODUCT INFORMATION:
{product_info}

PREVIOUS INSIGHTS (from earlier sessions):
{previous_insights}

HISTORICAL CAMPAIGN DATA:
{historical_data}

MARKET BENCHMARKS:
{market_data}

USER INPUTS:
{user_inputs}

CRITICAL INSTRUCTIONS:
- Base ALL insights on the actual historical campaign data provided above
- Identify SPECIFIC patterns (e.g., "TikTok campaigns had 23% lower CPA than Meta")
- Reference actual top/bottom performers from the data
- DO NOT make generic recommendations - be specific and data-driven
- If no data is available for a category, explicitly state that
- If PREVIOUS INSIGHTS are provided: Build upon them, identify confirmations or contradictions with new data
- If PREVIOUS INSIGHTS show patterns, validate them with new data or explain divergences

Based on this data, create a strategy that includes:

1. KEY INSIGHTS (MUST BE SPECIFIC AND DATA-DRIVEN):
   - What SPECIFIC patterns do you see? (cite actual metrics, platforms, creatives)
   - Which platforms/creatives/audiences performed best? (provide actual numbers)
   - What are the concrete strengths and weaknesses based on the data?
   - How does our actual performance compare to benchmarks?
   - What is our best CPA? Worst CPA? What caused the difference?

2. TARGET AUDIENCE (BASED ON HISTORICAL DATA):
   - Which audience segments showed best performance in historical data?
   - What interests/demographics worked well before?
   - What should we test that we haven't tried yet?

3. CREATIVE STRATEGY (BASED ON WHAT WORKED):
   - Which creative types/formats had best performance?
   - What messaging angles should we double down on?
   - What new angles should we test based on gaps in historical data?

4. PLATFORM STRATEGY (DATA-DRIVEN):
   - Compare actual platform performance from historical data
   - Recommend budget allocation based on historical ROI
   - Provide specific rationale with numbers

5. EXPERIMENT PLAN (ACCELERATED 7-DAY PARALLEL TESTING):
   Design parallel experiments to test platform, audience, and creative simultaneously in 7 days:

   CRITICAL INSTRUCTIONS FOR PARALLEL TESTING:
   - Test 4-6 smart COMBINATIONS of platform+audience+creative together (not sequentially)
   - Use historical data to skip obvious losers and focus budget on viable options
   - Allocate budgets across combinations (e.g., 30% to best bet, 25% to hedge, etc.)
   - Each combination needs 15-20 conversions minimum for statistical confidence
   - Include interaction effects (some platform+creative combos work better together)

   For the experiment plan, specify:
   - Test matrix: 4-6 combinations with platform/audience/creative for each
   - Budget allocation per combination (must sum to 100%)
   - Rationale for each combination based on historical data
   - Memory-based optimizations: What obvious losers are you skipping? Why?
   - Decision criteria: Min conversions, confidence level, primary metric
   - Evaluation schedule: Day 3 check (flag issues), Day 7 final decision
   - Hypotheses for platform, audience, creative, and interaction effects

CRITICAL: Respond with valid JSON in this EXACT format. All fields marked with [] MUST be arrays/lists, all fields marked with {{}} MUST be objects/dicts:
{{
  "insights": {{
    "patterns": ["pattern 1", "pattern 2"],  // MUST be array of strings
    "strengths": ["strength 1", "strength 2"],  // MUST be array of strings
    "weaknesses": ["weakness 1", "weakness 2"],  // MUST be array of strings
    "benchmark_comparison": "comparison text"  // string
  }},
  "target_audience": {{
    "primary_segments": ["segment 1", "segment 2"],  // MUST be array
    "interests": ["interest 1", "interest 2"],  // MUST be array
    "demographics": {{"age": "18-35", "gender": "all", "location": "US"}}  // MUST be object
  }},
  "creative_strategy": {{
    "messaging_angles": ["angle 1", "angle 2"],  // MUST be array
    "themes": ["theme 1", "theme 2"],  // MUST be array
    "value_props": ["prop 1", "prop 2"]  // MUST be array
  }},
  "platform_strategy": {{
    "priorities": ["Google Ads", "Meta"],  // MUST be array of platform names
    "budget_split": {{"Google Ads": 0.6, "Meta": 0.4}},  // MUST be object with numeric values (0-1)
    "rationale": "explanation text"  // string
  }},
  "experiment_plan": {{
    "mode": "accelerated",  // string
    "total_duration_days": 7,  // number
    "approach": "parallel_testing",  // string
    "day_1_to_7": {{
      "name": "Parallel Multi-Variable Test",  // string
      "description": "Test platform, audience, and creative simultaneously",  // string
      "test_matrix": {{
        "combinations": [  // MUST be array of combination objects
          {{
            "id": "combo_1",  // string
            "label": "Platform + Audience + Creative",  // string
            "platform": "TikTok",  // string
            "audience": "Interest targeting",  // string
            "creative": "UGC video",  // string
            "budget_allocation": "30%",  // string percentage
            "rationale": "Why this combination makes sense"  // string
          }}
          // Include 4-6 combinations total
        ]
      }},
      "decision_criteria": {{
        "min_conversions_per_combo": 15,  // number
        "confidence_level": 0.90,  // number (0-1)
        "primary_metric": "CPA",  // string
        "secondary_metrics": ["ROAS", "CTR"]  // MUST be array
      }},
      "evaluation_schedule": {{
        "day_3": "Check preliminary results",  // string
        "day_7": "Final evaluation and decision"  // string
      }},
      "hypotheses": {{
        "platform": "Platform hypothesis with data",  // string
        "audience": "Audience hypothesis with data",  // string
        "creative": "Creative hypothesis with data",  // string
        "interaction": "Interaction effect hypothesis"  // string
      }},
      "expected_outcome": "What we expect to learn in 7 days",  // string
      "statistical_power": "Confidence calculation explanation"  // string
    }},
    "memory_based_optimizations": {{
      "skipped_tests": ["What we're NOT testing and why"],  // MUST be array
      "confident_decisions": ["What we know from historical data"],  // MUST be array
      "hedge_tests": ["What we're testing as backup options"]  // MUST be array
    }}
  }}
}}

DO NOT return any field as a plain string if it should be an array or object!
"""


def generate_insights_and_strategy(
    state: Dict[str, Any],
    cached_insights: str = None
) -> Dict[str, Any]:
    """
    Generate insights and strategy from collected data

    NOTE: Uses temporary data from node_outputs (not persisted state)

    Args:
        state: Agent state with collected data
        cached_insights: Optional previous insights to build upon

    Returns:
        Strategy dictionary
    """
    gemini = get_gemini()

    # Prepare data summaries
    product_info = state.get("user_inputs", {}).get("product_description", "Not provided")

    # Format knowledge facts with confidence scores
    knowledge_facts = state.get("knowledge_facts", {})
    if knowledge_facts:
        knowledge_summary = "DISCOVERED FACTS (with confidence scores):\n"
        for key, fact in knowledge_facts.items():
            value = fact.get("value", "N/A")
            confidence = fact.get("confidence", 0.0)
            source = fact.get("source", "unknown")
            knowledge_summary += f"- {key}: {value} (confidence: {confidence:.1f}, source: {source})\n"
    else:
        knowledge_summary = "No knowledge facts discovered yet"

    # Get detailed historical data analysis from TEMPORARY data
    # This data is NOT stored in state, only used for insight generation
    temp_historical_data = state.get("node_outputs", {}).get("temp_historical_data", [])
    if temp_historical_data:
        # Generate comprehensive analysis from campaign data
        detailed_analysis = DataLoader.get_detailed_analysis(
            temp_historical_data,
            max_sample=50  # Include top 50 sample campaigns for context
        )
        hist_summary = json.dumps(detailed_analysis, indent=2)
    else:
        # Fallback to metadata if available
        metadata = state.get("historical_data", {}).get("metadata", {})
        if metadata:
            hist_summary = f"Historical data metadata: {json.dumps(metadata, indent=2)}"
        else:
            hist_summary = "No historical campaign data available"

    market_data = state.get("market_data", {})
    if market_data.get("benchmarks"):
        market_summary = json.dumps(market_data["benchmarks"], indent=2)
    else:
        market_summary = "No market benchmarks available"

    user_inputs = state.get("user_inputs", {})
    user_inputs_summary = "\n".join([f"- {k}: {v}" for k, v in user_inputs.items()])

    # Include cached insights if available
    previous_insights = cached_insights if cached_insights else "No previous insights available"

    # Build prompt with knowledge facts
    prompt = INSIGHT_PROMPT_TEMPLATE.format(
        product_info=product_info,
        historical_data=hist_summary,
        market_data=market_summary,
        user_inputs=user_inputs_summary if user_inputs_summary else "None provided",
        previous_insights=previous_insights
    )

    # Prepend knowledge summary to prompt
    prompt = knowledge_summary + "\n" + prompt

    # Generate strategy
    strategy = gemini.generate_json(
        prompt=prompt,
        system_instruction=INSIGHT_SYSTEM_INSTRUCTION,
        temperature=0.7,
        task_name="Strategy & Insights Generation",
    )

    return strategy

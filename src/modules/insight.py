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

5. EXPERIMENT PLAN:
   Design 3 sequential experiments informed by historical data gaps and opportunities:
   - Week 1: Platform test (based on historical platform comparison)
   - Week 2: Audience test (test best historical audiences vs new segments)
   - Week 3: Creative test (test winning formats vs new variations)

   For each experiment, specify:
   - Hypothesis (grounded in historical data)
   - Variations to test
   - Control vs test setup
   - Success metrics
   - Expected improvement based on historical benchmarks

Respond with valid JSON in this format:
{{
  "insights": {{
    "patterns": ["list of key patterns"],
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"],
    "benchmark_comparison": "How we compare to market"
  }},
  "target_audience": {{
    "primary_segments": ["list of segments"],
    "interests": ["list of interests"],
    "demographics": {{"age": "", "gender": "", "location": ""}}
  }},
  "creative_strategy": {{
    "messaging_angles": ["list of angles"],
    "themes": ["list of themes"],
    "value_props": ["list of value propositions"]
  }},
  "platform_strategy": {{
    "priorities": ["platform 1", "platform 2"],
    "budget_split": {{"platform 1": 0.6, "platform 2": 0.4}},
    "rationale": "Explanation"
  }},
  "experiment_plan": {{
    "week_1": {{
      "name": "Platform Test",
      "hypothesis": "",
      "variations": ["TikTok", "Meta"],
      "control": {{}},
      "metrics": ["CPA", "CTR", "ROAS"]
    }},
    "week_2": {{
      "name": "Audience Test",
      "hypothesis": "",
      "variations": ["segment 1", "segment 2"],
      "control": {{}},
      "metrics": ["CPA", "CTR", "ROAS"]
    }},
    "week_3": {{
      "name": "Creative Test",
      "hypothesis": "",
      "variations": ["angle 1", "angle 2"],
      "control": {{}},
      "metrics": ["CPA", "CTR", "ROAS"]
    }}
  }}
}}
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

    # Build prompt
    prompt = INSIGHT_PROMPT_TEMPLATE.format(
        product_info=product_info,
        historical_data=hist_summary,
        market_data=market_summary,
        user_inputs=user_inputs_summary if user_inputs_summary else "None provided",
        previous_insights=previous_insights
    )

    # Generate strategy
    strategy = gemini.generate_json(
        prompt=prompt,
        system_instruction=INSIGHT_SYSTEM_INSTRUCTION,
        temperature=0.7,
        task_name="Strategy & Insights Generation",
    )

    return strategy

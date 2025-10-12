"""
Campaign configuration generation module
"""

from typing import Dict, Any, Optional
from ..llm.gemini import get_gemini


CAMPAIGN_SYSTEM_INSTRUCTION = """You are an expert in digital advertising campaign configuration.

Your job is to convert strategic recommendations into complete, executable campaign configurations
for TikTok and Meta (Facebook/Instagram) platforms.

Include specific:
- Targeting parameters (interests, behaviors, demographics)
- Budget allocation and bidding strategies
- Placement specifications
- Optimization goals
- Ad creative guidelines

Be precise and actionable.
"""


CAMPAIGN_PROMPT_TEMPLATE = """
Generate complete campaign configurations based on this strategy:

STRATEGY:
{strategy}

USER REQUIREMENTS:
- Target Budget: {budget}
- Product: {product}
- Current Iteration: {iteration}

{patch_context}

Create detailed configs for:
1. TikTok Ads
2. Meta Ads (Facebook/Instagram)

For each platform, include:
- Campaign objective
- Daily budget
- Audience targeting (specific interests, behaviors, demographics)
- Placements
- Bidding strategy (CPA target, bid amount)
- Ad creative requirements
- Optimization settings

Respond with valid JSON:
{{
  "tiktok": {{
    "campaign_name": "",
    "objective": "CONVERSIONS",
    "daily_budget": 0.0,
    "targeting": {{
      "age_range": "",
      "gender": "",
      "locations": [],
      "interests": [],
      "behaviors": []
    }},
    "placements": [],
    "bidding": {{
      "strategy": "LOWEST_COST_WITH_BID_CAP",
      "bid_amount": 0.0,
      "target_cpa": 0.0
    }},
    "creative_specs": {{
      "format": "",
      "duration": "",
      "messaging": []
    }},
    "optimization": {{
      "optimization_goal": "CONVERSIONS",
      "attribution_window": "7_DAY_CLICK"
    }}
  }},
  "meta": {{
    "campaign_name": "",
    "objective": "CONVERSIONS",
    "daily_budget": 0.0,
    "targeting": {{
      "age_range": "",
      "gender": "",
      "locations": [],
      "detailed_targeting": {{
        "interests": [],
        "behaviors": []
      }}
    }},
    "placements": [],
    "bidding": {{
      "strategy": "LOWEST_COST_WITH_BID_CAP",
      "bid_amount": 0.0,
      "target_cpa": 0.0
    }},
    "creative_specs": {{
      "formats": [],
      "messaging": []
    }},
    "optimization": {{
      "optimization_goal": "CONVERSIONS",
      "conversion_window": "7_DAY_CLICK"
    }}
  }},
  "summary": {{
    "total_daily_budget": 0.0,
    "budget_allocation": {{"tiktok": 0.0, "meta": 0.0}},
    "experiment": "Description of what we're testing"
  }}
}}
"""


def generate_campaign_config(
    state: Dict[str, Any],
    patch: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate campaign configuration from strategy

    Args:
        state: Agent state with strategy
        patch: Optional patch to apply (for adjustments)

    Returns:
        Campaign configuration dictionary
    """
    gemini = get_gemini()

    strategy = state.get("current_strategy", {})
    budget = state.get("user_inputs", {}).get("target_budget", 500)
    product = state.get("user_inputs", {}).get("product_description", "Product")
    iteration = state.get("iteration", 0)

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

    # Build prompt
    prompt = CAMPAIGN_PROMPT_TEMPLATE.format(
        strategy=str(strategy),
        budget=budget,
        product=product,
        iteration=iteration,
        patch_context=patch_context
    )

    # Generate config
    task_name = "Campaign Configuration" if not patch else "Adjusted Campaign Configuration"
    config = gemini.generate_json(
        prompt=prompt,
        system_instruction=CAMPAIGN_SYSTEM_INSTRUCTION,
        temperature=0.5,  # Moderate creativity
        task_name=task_name,
    )

    return config

"""
Flexible execution timeline planner - LLM-powered adaptive testing schedules
"""

from typing import Dict, Any, List
from ..llm.gemini import get_gemini


EXECUTION_PLANNER_SYSTEM_INSTRUCTION = """You are an expert campaign testing strategist.

Your job is to design flexible execution timelines that maximize learning velocity while maintaining statistical rigor.

Key principles:
- Adapt timeline length to campaign complexity (7-30 days max)
- Allocate budget strategically across short/medium/long-term phases
- Set checkpoints at statistically meaningful intervals
- Balance risk and learning speed
- Design tests that answer critical questions as quickly as possible
"""


EXECUTION_PLANNER_PROMPT_TEMPLATE = """
Design an optimal execution timeline for this campaign based on the following context:

STRATEGY & INSIGHTS:
{strategy_summary}

HISTORICAL PERFORMANCE DATA:
{historical_data}

BUDGET & CONSTRAINTS:
- Daily budget: ${daily_budget}
- Target CPA: ${target_cpa}
- Target ROAS: {target_roas}
- Maximum timeline: 30 days

KEY HYPOTHESES TO TEST:
{hypotheses}

CRITICAL INSTRUCTIONS:
1. Design a timeline with 2-3 phases (short-term, medium-term, optional long-term)
2. Each phase should have:
   - Clear test objectives based on historical data gaps
   - Specific test combinations (platform + audience + creative)
   - Budget allocation that balances risk/reward
   - Checkpoint dates for progress reviews
3. Set checkpoint frequency based on expected conversion volume:
   - High volume (>50 conversions/week): Check every 3-4 days
   - Medium volume (20-50 conversions/week): Check every 5-7 days
   - Low volume (<20 conversions/week): Check every 7-10 days
4. Total timeline should be 7-30 days depending on:
   - Number of critical hypotheses to test
   - Budget available for testing
   - Complexity of campaign (more variables = longer timeline)
5. Budget allocation philosophy:
   - Short-term (30-40%): High-confidence tests, quick wins
   - Medium-term (35-45%): Validation and scaling
   - Long-term (20-30%): Optimization and refinement (only if timeline >14 days)

CRITICAL: Respond with valid JSON in this EXACT format:
{{
  "timeline": {{
    "total_duration_days": 14,  // 7-30 days based on complexity
    "reasoning": "Explain why this timeline length was chosen",
    "phases": [
      {{
        "name": "Short-term Discovery",
        "duration_days": 5,
        "start_day": 1,
        "end_day": 5,
        "budget_allocation_percent": 35,
        "objectives": [
          "Objective 1",
          "Objective 2"
        ],
        "test_combinations": [
          {{
            "id": "combo_1",
            "label": "Platform + Audience + Creative",
            "platform": "TikTok",
            "audience": "Interest targeting",
            "creative": "UGC video",
            "budget_percent": 15,
            "rationale": "Why this combination"
          }}
        ],
        "success_criteria": [
          "Criteria 1",
          "Criteria 2"
        ],
        "decision_triggers": {{
          "proceed_if": "CPA < $30 in at least 2 combinations",
          "pause_if": "CPA > $50 across all combinations",
          "scale_if": "ROAS > 3.5 in any combination"
        }}
      }},
      {{
        "name": "Medium-term Validation",
        "duration_days": 6,
        "start_day": 6,
        "end_day": 11,
        "budget_allocation_percent": 40,
        "objectives": ["Objective 1"],
        "test_combinations": [],
        "success_criteria": [],
        "decision_triggers": {{
          "proceed_if": "",
          "pause_if": "",
          "scale_if": ""
        }}
      }}
      // Add long-term phase only if total_duration_days > 14
    ],
    "checkpoints": [
      {{
        "day": 3,
        "purpose": "Early signal check",
        "review_focus": [
          "Check for obvious losers",
          "Validate tracking setup",
          "Confirm conversion volume"
        ],
        "action_required": false
      }},
      {{
        "day": 7,
        "purpose": "Phase 1 decision point",
        "review_focus": [
          "Identify winning combinations",
          "Calculate statistical significance",
          "Decide on phase 2 allocation"
        ],
        "action_required": true
      }}
    ]
  }},
  "statistical_requirements": {{
    "min_conversions_per_combo": 15,
    "confidence_level": 0.90,
    "expected_weekly_conversions": 45,
    "power_analysis": "Explanation of statistical validity"
  }},
  "risk_mitigation": {{
    "early_warning_signals": [
      "Signal 1",
      "Signal 2"
    ],
    "contingency_plans": [
      "Plan 1 if tests fail",
      "Plan 2 if budget exhausted early"
    ]
  }}
}}

IMPORTANT:
- Budget allocations across all phases must sum to 100%
- Budget allocations within each phase's test_combinations should sum to that phase's budget_allocation_percent
- All day numbers must be within 1 to total_duration_days range
- Checkpoint days must align with phase boundaries or fall within phases
"""


def generate_execution_timeline(
    state: Dict[str, Any],
    strategy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate flexible execution timeline using LLM

    Args:
        state: Agent state with historical data and constraints
        strategy: Generated strategy with insights and hypotheses

    Returns:
        Execution timeline dictionary
    """
    gemini = get_gemini()

    # Extract key information
    daily_budget = state.get("knowledge_facts", {}).get("target_budget", {}).get("value", 1000)
    target_cpa = state.get("knowledge_facts", {}).get("target_cpa", {}).get("value", 25.0)
    target_roas = state.get("knowledge_facts", {}).get("target_roas", {}).get("value", 3.0)

    # Prepare strategy summary
    insights = strategy.get("insights", {})
    strategy_summary = f"""
Key Patterns: {insights.get('patterns', [])}
Strengths: {insights.get('strengths', [])}
Weaknesses: {insights.get('weaknesses', [])}
Platform Priorities: {strategy.get('platform_strategy', {}).get('priorities', [])}
Target Audience: {strategy.get('target_audience', {}).get('primary_segments', [])}
"""

    # Extract historical data summary
    hist_metadata = state.get("historical_data", {}).get("metadata", {})
    historical_summary = f"""
Total campaigns analyzed: {hist_metadata.get('total_rows', 'N/A')}
Files: {len(hist_metadata.get('files', []))}
"""

    # Extract hypotheses from strategy
    hypotheses_list = []
    if strategy.get("platform_strategy", {}).get("rationale"):
        hypotheses_list.append(f"Platform: {strategy['platform_strategy']['rationale']}")
    if strategy.get("target_audience", {}).get("primary_segments"):
        hypotheses_list.append(f"Audience: Test segments {strategy['target_audience']['primary_segments']}")
    if strategy.get("creative_strategy", {}).get("messaging_angles"):
        hypotheses_list.append(f"Creative: Test angles {strategy['creative_strategy']['messaging_angles'][:2]}")

    hypotheses = "\n".join([f"- {h}" for h in hypotheses_list])

    # Build prompt
    prompt = EXECUTION_PLANNER_PROMPT_TEMPLATE.format(
        strategy_summary=strategy_summary,
        historical_data=historical_summary,
        daily_budget=daily_budget,
        target_cpa=target_cpa,
        target_roas=target_roas,
        hypotheses=hypotheses if hypotheses else "- Validate platform effectiveness\n- Test audience segments\n- Optimize creative messaging"
    )

    # Generate timeline
    timeline = gemini.generate_json(
        prompt=prompt,
        system_instruction=EXECUTION_PLANNER_SYSTEM_INSTRUCTION,
        temperature=0.6,  # Balance creativity with structure
        task_name="Execution Timeline Planning",
    )

    return timeline


def validate_execution_timeline(timeline: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate execution timeline structure and constraints

    Args:
        timeline: Timeline dictionary from LLM

    Returns:
        (is_valid, error_messages)
    """
    errors = []
    timeline_data = timeline.get("timeline", {})

    # Check total duration
    total_days = timeline_data.get("total_duration_days", 0)
    if not total_days or total_days < 7 or total_days > 30:
        errors.append(f"Invalid total_duration_days: {total_days} (must be 7-30)")

    # Check phases exist
    phases = timeline_data.get("phases", [])
    if not phases or len(phases) < 2:
        errors.append("Must have at least 2 phases")

    # Validate budget allocation
    total_budget = sum(phase.get("budget_allocation_percent", 0) for phase in phases)
    if abs(total_budget - 100) > 2:  # Allow 2% tolerance
        errors.append(f"Phase budgets sum to {total_budget}%, must be 100%")

    # Validate each phase
    for i, phase in enumerate(phases):
        phase_name = phase.get("name", f"Phase {i+1}")

        if not phase.get("objectives"):
            errors.append(f"{phase_name}: Missing objectives")

        if phase.get("start_day", 0) < 1:
            errors.append(f"{phase_name}: start_day must be >= 1")

        if phase.get("end_day", 0) > total_days:
            errors.append(f"{phase_name}: end_day exceeds total_duration_days")

        # Validate test combinations budget
        combos = phase.get("test_combinations", [])
        if combos:
            combo_budget_sum = sum(c.get("budget_percent", 0) for c in combos)
            phase_budget = phase.get("budget_allocation_percent", 0)
            if abs(combo_budget_sum - phase_budget) > 2:
                errors.append(
                    f"{phase_name}: test combinations budget ({combo_budget_sum}%) "
                    f"doesn't match phase budget ({phase_budget}%)"
                )

    # Validate checkpoints
    checkpoints = timeline_data.get("checkpoints", [])
    if not checkpoints:
        errors.append("Must have at least one checkpoint")

    for checkpoint in checkpoints:
        day = checkpoint.get("day", 0)
        if day < 1 or day > total_days:
            errors.append(f"Checkpoint day {day} outside valid range (1-{total_days})")

    is_valid = len(errors) == 0
    return is_valid, errors


def get_timeline_summary(timeline: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of execution timeline

    Args:
        timeline: Timeline dictionary

    Returns:
        Formatted summary string
    """
    timeline_data = timeline.get("timeline", {})
    total_days = timeline_data.get("total_duration_days", 0)
    phases = timeline_data.get("phases", [])
    checkpoints = timeline_data.get("checkpoints", [])

    summary = f"""
Execution Timeline: {total_days} days
Phases: {len(phases)}
Checkpoints: {len(checkpoints)}
Reasoning: {timeline_data.get('reasoning', 'N/A')}
"""

    return summary.strip()

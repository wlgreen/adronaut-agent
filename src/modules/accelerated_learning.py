"""
Accelerated learning helper functions for parallel experiment design
"""

from typing import Dict, Any, List
import math


def validate_parallel_experiment_plan(experiment_plan: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate that parallel experiment plan has required structure

    Args:
        experiment_plan: Experiment plan dictionary from LLM

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check mode
    if experiment_plan.get("mode") != "accelerated":
        errors.append("Missing or incorrect mode (should be 'accelerated')")

    # Check day_1_to_7 structure
    day_plan = experiment_plan.get("day_1_to_7", {})
    if not day_plan:
        errors.append("Missing 'day_1_to_7' plan structure")
        return False, errors

    # Check test matrix
    test_matrix = day_plan.get("test_matrix", {})
    combinations = test_matrix.get("combinations", [])

    if not combinations or len(combinations) < 3:
        errors.append("Need at least 3 combinations in test matrix")

    if len(combinations) > 8:
        errors.append("Too many combinations (max 8 for statistical power)")

    # Validate each combination
    for i, combo in enumerate(combinations):
        if not combo.get("platform"):
            errors.append(f"Combination {i+1}: Missing platform")
        if not combo.get("audience"):
            errors.append(f"Combination {i+1}: Missing audience")
        if not combo.get("creative"):
            errors.append(f"Combination {i+1}: Missing creative")
        if not combo.get("budget_allocation"):
            errors.append(f"Combination {i+1}: Missing budget_allocation")
        if not combo.get("rationale"):
            errors.append(f"Combination {i+1}: Missing rationale")

    # Check budget allocations sum to ~100%
    budget_sum = 0
    for combo in combinations:
        allocation = combo.get("budget_allocation", "0%")
        try:
            # Parse percentage string (e.g., "30%" -> 30)
            pct = float(allocation.strip("%"))
            budget_sum += pct
        except (ValueError, AttributeError):
            errors.append(f"Invalid budget allocation format: {allocation}")

    if abs(budget_sum - 100) > 5:  # Allow 5% tolerance
        errors.append(f"Budget allocations sum to {budget_sum}%, should be 100%")

    # Check decision criteria
    criteria = day_plan.get("decision_criteria", {})
    if not criteria.get("min_conversions_per_combo"):
        errors.append("Missing min_conversions_per_combo in decision_criteria")

    is_valid = len(errors) == 0
    return is_valid, errors


def calculate_statistical_requirements(
    combinations: int,
    expected_cpa: float,
    daily_budget: float,
    test_days: int = 7
) -> Dict[str, Any]:
    """
    Calculate statistical requirements for parallel testing

    Args:
        combinations: Number of combinations to test
        expected_cpa: Expected cost per acquisition
        daily_budget: Total daily budget
        test_days: Duration of test in days

    Returns:
        Dictionary with statistical calculations
    """
    total_budget = daily_budget * test_days
    budget_per_combo = total_budget / combinations

    # Estimate conversions per combination
    estimated_conversions = budget_per_combo / expected_cpa

    # Calculate minimum detectable effect (MDE)
    # Rule of thumb: need ~15-20 conversions per variant for 80% power
    has_sufficient_power = estimated_conversions >= 15

    # Calculate confidence level achievable
    # Simplified calculation - in production would use proper power analysis
    if estimated_conversions >= 20:
        confidence = 0.95
    elif estimated_conversions >= 15:
        confidence = 0.90
    elif estimated_conversions >= 10:
        confidence = 0.80
    else:
        confidence = 0.70

    return {
        "combinations": combinations,
        "test_duration_days": test_days,
        "total_budget": total_budget,
        "budget_per_combo": budget_per_combo,
        "estimated_conversions_per_combo": estimated_conversions,
        "has_sufficient_power": has_sufficient_power,
        "achievable_confidence": confidence,
        "recommendation": (
            "Sufficient sample size for reliable results"
            if has_sufficient_power
            else f"Consider increasing budget or reducing combinations. "
            f"Need ${expected_cpa * 15 * combinations:.2f} total for 15 conversions per combo"
        )
    }


def format_combination_label(platform: str, audience: str, creative: str) -> str:
    """
    Create concise label for a test combination

    Args:
        platform: Platform name
        audience: Audience type
        creative: Creative type

    Returns:
        Formatted label
    """
    # Shorten common terms
    audience_short = audience.replace("Interest targeting: ", "").replace("Lookalike ", "LAL ")
    creative_short = creative.replace(" video", "").replace(" ad", "")

    return f"{platform} + {audience_short[:20]} + {creative_short[:15]}"


def extract_combination_summary(experiment_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract key info from combinations for display

    Args:
        experiment_plan: Experiment plan dictionary

    Returns:
        List of simplified combination summaries
    """
    summaries = []

    day_plan = experiment_plan.get("day_1_to_7", {})
    combinations = day_plan.get("test_matrix", {}).get("combinations", [])

    for combo in combinations:
        summaries.append({
            "id": combo.get("id", "unknown"),
            "label": combo.get("label", format_combination_label(
                combo.get("platform", "?"),
                combo.get("audience", "?"),
                combo.get("creative", "?")
            )),
            "platform": combo.get("platform"),
            "audience": combo.get("audience"),
            "creative": combo.get("creative"),
            "budget": combo.get("budget_allocation"),
            "rationale": combo.get("rationale", "")[:80] + "..."  # Truncate for display
        })

    return summaries


def compare_sequential_vs_parallel(sequential_days: int = 21, parallel_days: int = 7) -> Dict[str, Any]:
    """
    Calculate time savings from parallel testing

    Args:
        sequential_days: Days for sequential testing (default 21)
        parallel_days: Days for parallel testing (default 7)

    Returns:
        Comparison metrics
    """
    time_saved = sequential_days - parallel_days
    percent_reduction = (time_saved / sequential_days) * 100

    return {
        "sequential_duration": sequential_days,
        "parallel_duration": parallel_days,
        "time_saved_days": time_saved,
        "time_reduction_percent": percent_reduction,
        "learning_speed_multiplier": sequential_days / parallel_days
    }

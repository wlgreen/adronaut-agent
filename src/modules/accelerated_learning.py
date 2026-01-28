"""Accelerated learning helpers.

This module supports the 7-day parallel testing workflow described in
`docs/ACCELERATED_LEARNING.md`.

The functions are intentionally dependency-free so they can be unit-tested
without requiring the full agent stack.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


REQUIRED_COMBINATION_FIELDS = {
    "id",
    "platform",
    "audience",
    "creative",
    "budget_allocation",
}


def validate_parallel_experiment_plan(plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a parallel (accelerated) experiment plan.

    Returns (is_valid, errors).

    The validator is permissive by design: it checks the presence of key
    structural fields and the required fields on each combination.
    """

    errors: List[str] = []

    if not isinstance(plan, dict):
        return False, ["Plan must be a dict"]

    if plan.get("mode") != "accelerated":
        errors.append("Plan mode must be 'accelerated'")

    if "total_duration_days" not in plan:
        errors.append("Missing total_duration_days")

    day_block = plan.get("day_1_to_7")
    if not isinstance(day_block, dict):
        errors.append("Missing day_1_to_7 block")
        return False, errors

    test_matrix = day_block.get("test_matrix")
    if not isinstance(test_matrix, dict):
        errors.append("Missing test_matrix")
        return False, errors

    combinations = test_matrix.get("combinations")
    if not isinstance(combinations, list) or not combinations:
        errors.append("test_matrix.combinations must be a non-empty list")
        return False, errors

    for i, combo in enumerate(combinations, start=1):
        if not isinstance(combo, dict):
            errors.append(f"Combination #{i} must be an object")
            continue
        missing = sorted(REQUIRED_COMBINATION_FIELDS - set(combo.keys()))
        if missing:
            errors.append(f"Combination #{i} missing fields: {', '.join(missing)}")

    # decision criteria is recommended, but validate if present
    decision_criteria = day_block.get("decision_criteria")
    if decision_criteria is not None and not isinstance(decision_criteria, dict):
        errors.append("decision_criteria must be an object")

    return (len(errors) == 0), errors


def calculate_statistical_requirements(
    *,
    combinations: int,
    expected_cpa: float,
    daily_budget: float,
    test_days: int = 7,
    min_conversions_per_combo: int = 15,
) -> Dict[str, Any]:
    """Compute simple power/sample-size guidance for parallel tests.

    This uses a pragmatic heuristic (15+ conversions per combo) rather than a
    full statistical power model.
    """

    if combinations <= 0:
        raise ValueError("combinations must be > 0")
    if expected_cpa <= 0:
        raise ValueError("expected_cpa must be > 0")
    if daily_budget < 0:
        raise ValueError("daily_budget must be >= 0")
    if test_days <= 0:
        raise ValueError("test_days must be > 0")

    total_budget = daily_budget * test_days
    budget_per_combo = total_budget / combinations
    estimated_conversions = budget_per_combo / expected_cpa

    # Keep both: a rounded human-friendly number and the float value.
    estimated_conversions_rounded = int(round(estimated_conversions))
    has_sufficient_power = estimated_conversions >= float(min_conversions_per_combo)

    # Very rough mapping from conversions to achievable confidence.
    # (Enough for display + unit tests; not used for strict decisions.)
    if estimated_conversions >= 25:
        achievable_confidence = 0.90
    elif estimated_conversions >= 20:
        achievable_confidence = 0.85
    elif estimated_conversions >= 15:
        achievable_confidence = 0.80
    else:
        achievable_confidence = 0.70

    if has_sufficient_power:
        recommendation = (
            f"Sufficient budget for ~{estimated_conversions_rounded} conversions per combo. "
            "Proceed with parallel test."
        )
    else:
        needed_total_budget = combinations * expected_cpa * min_conversions_per_combo
        needed_daily_budget = needed_total_budget / test_days
        recommendation = (
            "Insufficient budget for reliable results. Consider increasing budget "
            f"to ~${needed_daily_budget:.0f}/day, reducing combinations, or extending the test."
        )

    return {
        "total_budget": int(round(total_budget)),
        "budget_per_combo": int(round(budget_per_combo)),
        "estimated_conversions_per_combo": estimated_conversions_rounded,
        "estimated_conversions_per_combo_float": float(estimated_conversions),
        "min_conversions_per_combo": int(min_conversions_per_combo),
        "has_sufficient_power": bool(has_sufficient_power),
        "achievable_confidence": float(achievable_confidence),
        "recommendation": recommendation,
    }


def format_combination_label(*, platform: str, audience: str, creative: str, max_len: int = 60) -> str:
    """Create a readable short label for a combination.

    Heuristic: preserve platform + *some* audience + *some* creative, prioritizing
    keeping the creative token(s) visible (tests expect e.g. "UGC" to survive).
    """

    platform = " ".join((platform or "").split())
    audience = " ".join((audience or "").split())
    creative = " ".join((creative or "").split())

    # Start with full label
    parts = [p for p in (platform, audience, creative) if p]
    label = " + ".join(parts)
    if len(label) <= max_len:
        return label

    # If too long, shrink audience first, but keep creative visible.
    base_parts = [p for p in (platform, creative) if p]
    base = " + ".join(base_parts)
    if not audience:
        return (base[: max_len - 3].rstrip() + "...") if len(base) > max_len else base

    # How much room remains for audience (including separators)?
    # target: "{platform} + {audience_trunc} + {creative}"
    sep = " + "
    fixed_len = len(platform) + len(sep) + len(sep) + len(creative)
    remaining_for_audience = max_len - fixed_len

    if remaining_for_audience <= 0:
        # No room for audience; ensure we still show creative.
        minimal = sep.join([p for p in (platform, creative) if p])
        return (minimal[: max_len - 3].rstrip() + "...") if len(minimal) > max_len else minimal

    aud = audience
    if len(aud) > remaining_for_audience:
        aud = aud[: max(0, remaining_for_audience - 3)].rstrip() + "..."

    label = f"{platform}{sep}{aud}{sep}{creative}" if platform else f"{aud}{sep}{creative}"
    return label[:max_len]  # defensive


def extract_combination_summary(plan: Dict[str, Any], *, rationale_max_len: int = 80) -> List[Dict[str, str]]:
    """Extract a compact summary list for display/CLI output."""

    day_block = (plan or {}).get("day_1_to_7") or {}
    combos = ((day_block.get("test_matrix") or {}).get("combinations")) or []

    summaries: List[Dict[str, str]] = []
    for combo in combos:
        if not isinstance(combo, dict):
            continue

        rationale = str(combo.get("rationale", ""))
        rationale = " ".join(rationale.split())
        if len(rationale) > rationale_max_len:
            rationale = rationale[: rationale_max_len].rstrip() + "..."

        summaries.append(
            {
                "id": str(combo.get("id", "")),
                "label": str(combo.get("label") or format_combination_label(
                    platform=str(combo.get("platform", "")),
                    audience=str(combo.get("audience", "")),
                    creative=str(combo.get("creative", "")),
                )),
                "budget": str(combo.get("budget_allocation", "")),
                "rationale": rationale,
            }
        )

    return summaries


def compare_sequential_vs_parallel(sequential_days: int = 21, parallel_days: int = 7) -> Dict[str, Any]:
    """Compare durations between sequential and accelerated parallel testing."""

    if sequential_days <= 0 or parallel_days <= 0:
        raise ValueError("Durations must be > 0")

    time_saved = sequential_days - parallel_days
    time_reduction_percent = round((time_saved / sequential_days) * 100.0, 2)
    learning_speed_multiplier = round(sequential_days / parallel_days, 2)

    return {
        "sequential_duration": int(sequential_days),
        "parallel_duration": int(parallel_days),
        "time_saved_days": int(time_saved),
        "time_reduction_percent": float(time_reduction_percent),
        "learning_speed_multiplier": float(learning_speed_multiplier),
    }

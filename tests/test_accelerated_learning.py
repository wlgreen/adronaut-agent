"""
Unit tests for accelerated learning module
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.accelerated_learning import (
    validate_parallel_experiment_plan,
    calculate_statistical_requirements,
    format_combination_label,
    extract_combination_summary,
    compare_sequential_vs_parallel
)


def test_validate_parallel_experiment_plan():
    """Test validation of parallel experiment plans"""
    print("\n=== Test: validate_parallel_experiment_plan ===")

    # Valid plan
    valid_plan = {
        "mode": "accelerated",
        "total_duration_days": 7,
        "day_1_to_7": {
            "test_matrix": {
                "combinations": [
                    {
                        "id": "combo_1",
                        "label": "TikTok + Interest + UGC",
                        "platform": "TikTok",
                        "audience": "Interest: fitness",
                        "creative": "UGC video",
                        "budget_allocation": "30%",
                        "rationale": "Best historical performer"
                    },
                    {
                        "id": "combo_2",
                        "label": "Meta + Lookalike + Testimonial",
                        "platform": "Meta",
                        "audience": "Lookalike 1%",
                        "creative": "Testimonial",
                        "budget_allocation": "35%",
                        "rationale": "Strong hedge option"
                    },
                    {
                        "id": "combo_3",
                        "label": "TikTok + Broad + Demo",
                        "platform": "TikTok",
                        "audience": "Broad",
                        "creative": "Product demo",
                        "budget_allocation": "35%",
                        "rationale": "Control group"
                    }
                ]
            },
            "decision_criteria": {
                "min_conversions_per_combo": 15,
                "confidence_level": 0.90,
                "primary_metric": "CPA"
            }
        }
    }

    is_valid, errors = validate_parallel_experiment_plan(valid_plan)
    print(f"Valid plan: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    assert is_valid, f"Valid plan should pass validation. Errors: {errors}"

    # Invalid plan - missing fields
    invalid_plan = {
        "mode": "accelerated",
        "day_1_to_7": {
            "test_matrix": {
                "combinations": [
                    {
                        "id": "combo_1",
                        "platform": "TikTok"
                        # Missing audience, creative, budget_allocation
                    }
                ]
            }
        }
    }

    is_valid, errors = validate_parallel_experiment_plan(invalid_plan)
    print(f"Invalid plan: {is_valid}")
    print(f"Expected errors: {errors}")
    assert not is_valid, "Invalid plan should fail validation"
    assert len(errors) > 0, "Should have error messages"

    print("✓ Validation tests passed\n")


def test_calculate_statistical_requirements():
    """Test statistical power calculations"""
    print("\n=== Test: calculate_statistical_requirements ===")

    # Scenario: 5 combos, $25 CPA, $500/day budget, 7 days
    result = calculate_statistical_requirements(
        combinations=5,
        expected_cpa=25.0,
        daily_budget=500.0,
        test_days=7
    )

    print(f"Total budget: ${result['total_budget']}")
    print(f"Budget per combo: ${result['budget_per_combo']}")
    print(f"Est conversions per combo: {result['estimated_conversions_per_combo']:.1f}")
    print(f"Has sufficient power: {result['has_sufficient_power']}")
    print(f"Achievable confidence: {result['achievable_confidence']}")
    print(f"Recommendation: {result['recommendation']}")

    assert result["total_budget"] == 3500, "Total budget should be $3500"
    assert result["budget_per_combo"] == 700, "Budget per combo should be $700"
    assert result["estimated_conversions_per_combo"] == 28, "Should estimate 28 conversions"
    assert result["has_sufficient_power"], "Should have sufficient power with 28 conversions"

    # Scenario: Insufficient budget
    result_low = calculate_statistical_requirements(
        combinations=6,
        expected_cpa=50.0,
        daily_budget=200.0,
        test_days=7
    )

    print(f"\nLow budget scenario:")
    print(f"Est conversions per combo: {result_low['estimated_conversions_per_combo']:.1f}")
    print(f"Has sufficient power: {result_low['has_sufficient_power']}")
    print(f"Recommendation: {result_low['recommendation']}")

    assert not result_low["has_sufficient_power"], "Should not have sufficient power"
    assert "increasing budget" in result_low["recommendation"].lower() or "increase budget" in result_low["recommendation"].lower(), "Should recommend budget increase"

    print("✓ Statistical calculation tests passed\n")


def test_format_combination_label():
    """Test combination label formatting"""
    print("\n=== Test: format_combination_label ===")

    label = format_combination_label(
        platform="TikTok",
        audience="Interest targeting: fitness, wellness, health",
        creative="UGC video testimonial"
    )

    print(f"Formatted label: {label}")
    assert "TikTok" in label
    assert "fitness" in label or "Interest" in label
    assert "UGC" in label

    print("✓ Label formatting tests passed\n")


def test_extract_combination_summary():
    """Test combination summary extraction"""
    print("\n=== Test: extract_combination_summary ===")

    plan = {
        "day_1_to_7": {
            "test_matrix": {
                "combinations": [
                    {
                        "id": "combo_1",
                        "label": "TikTok + Interest + UGC",
                        "platform": "TikTok",
                        "audience": "Interest: fitness",
                        "creative": "UGC video",
                        "budget_allocation": "40%",
                        "rationale": "This is a very long rationale that should be truncated when displayed to users because it contains too much detail"
                    }
                ]
            }
        }
    }

    summaries = extract_combination_summary(plan)

    print(f"Extracted {len(summaries)} summary(ies)")
    for s in summaries:
        print(f"  - {s['label']} ({s['budget']})")
        print(f"    Rationale: {s['rationale']}")

    assert len(summaries) == 1
    assert summaries[0]["id"] == "combo_1"
    assert summaries[0]["budget"] == "40%"
    assert len(summaries[0]["rationale"]) <= 83, "Rationale should be truncated"

    print("✓ Summary extraction tests passed\n")


def test_compare_sequential_vs_parallel():
    """Test comparison calculation"""
    print("\n=== Test: compare_sequential_vs_parallel ===")

    comparison = compare_sequential_vs_parallel(21, 7)

    print(f"Sequential: {comparison['sequential_duration']} days")
    print(f"Parallel: {comparison['parallel_duration']} days")
    print(f"Time saved: {comparison['time_saved_days']} days")
    print(f"Reduction: {comparison['time_reduction_percent']:.1f}%")
    print(f"Speed multiplier: {comparison['learning_speed_multiplier']:.1f}x")

    assert comparison["time_saved_days"] == 14
    assert comparison["time_reduction_percent"] == 66.67 or abs(comparison["time_reduction_percent"] - 66.67) < 0.1
    assert comparison["learning_speed_multiplier"] == 3.0

    print("✓ Comparison tests passed\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Accelerated Learning Module Tests")
    print("="*60)

    try:
        test_validate_parallel_experiment_plan()
        test_calculate_statistical_requirements()
        test_format_combination_label()
        test_extract_combination_summary()
        test_compare_sequential_vs_parallel()

        print("\n" + "="*60)
        print("  ✓ ALL TESTS PASSED")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

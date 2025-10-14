"""
Unit tests for creative generation module
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.creative_generator import (
    PLATFORM_SPECS,
    validate_creative_prompt,
    get_platform_specs_summary
)


def test_platform_specs_structure():
    """Test that platform specs are properly defined"""
    print("\n=== Test: platform_specs_structure ===")

    required_platforms = ["Meta", "TikTok", "Google Ads"]

    for platform in required_platforms:
        print(f"Checking {platform}...")
        assert platform in PLATFORM_SPECS, f"Missing platform: {platform}"

        specs = PLATFORM_SPECS[platform]
        assert "copy_limits" in specs, f"{platform} missing copy_limits"
        assert "file_format" in specs, f"{platform} missing file_format"
        assert "file_size_max" in specs, f"{platform} missing file_size_max"

        print(f"  ✓ {platform} has required fields")

    # Check Meta-specific placements
    meta_specs = PLATFORM_SPECS["Meta"]
    assert "feed" in meta_specs, "Meta missing feed placement"
    assert "stories" in meta_specs, "Meta missing stories placement"
    assert meta_specs["feed"]["aspect_ratio"] == "1:1"
    assert meta_specs["stories"]["aspect_ratio"] == "9:16"
    print("  ✓ Meta placements configured correctly")

    # Check TikTok-specific placements
    tiktok_specs = PLATFORM_SPECS["TikTok"]
    assert "primary" in tiktok_specs, "TikTok missing primary placement"
    assert tiktok_specs["primary"]["aspect_ratio"] == "9:16"
    print("  ✓ TikTok placements configured correctly")

    print("✓ Platform specs structure tests passed\n")


def test_validate_creative_prompt_valid():
    """Test validation of valid creative prompts"""
    print("\n=== Test: validate_creative_prompt_valid ===")

    valid_prompt = {
        "visual_prompt": "High-quality lifestyle photograph, modern setting, natural lighting",
        "copy_primary_text": "Transform your mornings with our 30-day wellness program. Join 10,000+ happy customers today!",
        "copy_headline": "Start Your Wellness Journey",
        "copy_cta": "SHOP_NOW",
        "hooks": [
            "What if mornings could be amazing?",
            "The wellness secret nobody talks about",
            "30 days to a better you"
        ],
        "technical_specs": {
            "aspect_ratio": "1:1",
            "dimensions": "1080x1080",
            "file_format": "PNG"
        }
    }

    is_valid, errors = validate_creative_prompt(valid_prompt, "Meta")
    print(f"Valid prompt: {is_valid}")
    if errors:
        print(f"Unexpected errors: {errors}")

    assert is_valid, f"Valid prompt should pass validation. Errors: {errors}"
    assert len(errors) == 0, "Valid prompt should have no errors"

    print("✓ Valid prompt validation passed\n")


def test_validate_creative_prompt_missing_fields():
    """Test validation catches missing required fields"""
    print("\n=== Test: validate_creative_prompt_missing_fields ===")

    incomplete_prompt = {
        "visual_prompt": "Some prompt",
        "copy_primary_text": "Some text"
        # Missing: copy_headline, copy_cta, hooks, technical_specs
    }

    is_valid, errors = validate_creative_prompt(incomplete_prompt, "Meta")
    print(f"Incomplete prompt valid: {is_valid}")
    print(f"Errors found: {len(errors)}")
    for error in errors:
        print(f"  - {error}")

    assert not is_valid, "Incomplete prompt should fail validation"
    assert len(errors) > 0, "Should have error messages"
    assert any("copy_headline" in error for error in errors), "Should flag missing headline"
    assert any("copy_cta" in error for error in errors), "Should flag missing CTA"
    assert any("hooks" in error for error in errors), "Should flag missing hooks"

    print("✓ Missing fields validation passed\n")


def test_validate_creative_prompt_copy_limits():
    """Test validation enforces platform copy limits"""
    print("\n=== Test: validate_creative_prompt_copy_limits ===")

    # Meta has 125 char limit for primary text
    too_long_prompt = {
        "visual_prompt": "Some prompt",
        "copy_primary_text": "a" * 150,  # 150 chars - exceeds Meta's 125 limit
        "copy_headline": "b" * 50,  # 50 chars - exceeds Meta's 40 limit
        "copy_cta": "SHOP_NOW",
        "hooks": ["Hook 1", "Hook 2", "Hook 3"],
        "technical_specs": {
            "aspect_ratio": "1:1",
            "dimensions": "1080x1080",
            "file_format": "PNG"
        }
    }

    is_valid, errors = validate_creative_prompt(too_long_prompt, "Meta")
    print(f"Over-limit prompt valid: {is_valid}")
    print(f"Errors found: {len(errors)}")
    for error in errors:
        print(f"  - {error}")

    assert not is_valid, "Over-limit prompt should fail validation"
    assert any("Primary text exceeds" in error for error in errors), "Should flag primary text length"
    assert any("Headline exceeds" in error for error in errors), "Should flag headline length"

    print("✓ Copy limits validation passed\n")


def test_validate_creative_prompt_hooks_count():
    """Test validation enforces minimum hook count"""
    print("\n=== Test: validate_creative_prompt_hooks_count ===")

    insufficient_hooks = {
        "visual_prompt": "Some prompt",
        "copy_primary_text": "Short copy",
        "copy_headline": "Headline",
        "copy_cta": "SHOP_NOW",
        "hooks": ["Only one hook"],  # Need at least 3
        "technical_specs": {
            "aspect_ratio": "1:1",
            "dimensions": "1080x1080",
            "file_format": "PNG"
        }
    }

    is_valid, errors = validate_creative_prompt(insufficient_hooks, "Meta")
    print(f"Insufficient hooks valid: {is_valid}")
    print(f"Errors found: {len(errors)}")
    for error in errors:
        print(f"  - {error}")

    assert not is_valid, "Should require at least 3 hooks"
    assert any("at least 3 hook" in error for error in errors), "Should flag insufficient hooks"

    print("✓ Hooks count validation passed\n")


def test_platform_specs_summary():
    """Test platform specs summary generation"""
    print("\n=== Test: platform_specs_summary ===")

    # Test Meta summary
    meta_summary = get_platform_specs_summary("Meta")
    print("Meta Summary:")
    print(meta_summary)

    assert "Meta" in meta_summary
    assert "1:1" in meta_summary  # Feed aspect ratio
    assert "9:16" in meta_summary  # Stories aspect ratio
    assert "125" in meta_summary or "primary_text" in meta_summary  # Copy limits

    # Test TikTok summary
    tiktok_summary = get_platform_specs_summary("TikTok")
    print("\nTikTok Summary:")
    print(tiktok_summary)

    assert "TikTok" in tiktok_summary
    assert "9:16" in tiktok_summary  # Primary aspect ratio

    # Test unknown platform
    unknown_summary = get_platform_specs_summary("UnknownPlatform")
    print("\nUnknown Platform Summary:")
    print(unknown_summary)

    assert "not found" in unknown_summary.lower()

    print("✓ Platform specs summary tests passed\n")


def test_creative_prompt_structure():
    """Test that creative prompt has expected structure"""
    print("\n=== Test: creative_prompt_structure ===")

    expected_fields = [
        "visual_prompt",
        "copy_primary_text",
        "copy_headline",
        "copy_cta",
        "hooks",
        "technical_specs"
    ]

    expected_tech_fields = [
        "aspect_ratio",
        "dimensions",
        "file_format"
    ]

    # Simulate what would be returned from LLM
    sample_creative = {
        "visual_prompt": "Modern lifestyle photo...",
        "copy_primary_text": "Join us today!",
        "copy_headline": "Transform Your Life",
        "copy_cta": "LEARN_MORE",
        "hooks": ["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
        "technical_specs": {
            "aspect_ratio": "1:1",
            "dimensions": "1080x1080",
            "file_format": "PNG",
            "file_size_max": "30MB",
            "brand_assets": ["logo_placement: bottom-right"],
            "color_scheme": "#FF5733"
        }
    }

    # Check all expected fields present
    for field in expected_fields:
        assert field in sample_creative, f"Missing field: {field}"
        print(f"  ✓ Has field: {field}")

    # Check technical specs structure
    tech_specs = sample_creative["technical_specs"]
    for field in expected_tech_fields:
        assert field in tech_specs, f"Missing technical spec: {field}"
        print(f"  ✓ Has tech spec: {field}")

    # Validate it passes validation
    is_valid, errors = validate_creative_prompt(sample_creative, "Meta")
    assert is_valid, f"Sample creative should be valid. Errors: {errors}"

    print("✓ Creative prompt structure tests passed\n")


def test_platform_copy_limits():
    """Test platform-specific copy limits are enforced correctly"""
    print("\n=== Test: platform_copy_limits ===")

    # Test Meta limits
    meta_limits = PLATFORM_SPECS["Meta"]["copy_limits"]
    print(f"Meta limits: {meta_limits}")
    assert meta_limits["primary_text"] == 125
    assert meta_limits["headline"] == 40

    # Create prompt at exact limits (should pass)
    exact_limit_prompt = {
        "visual_prompt": "Prompt",
        "copy_primary_text": "a" * 125,  # Exactly 125 chars
        "copy_headline": "b" * 40,  # Exactly 40 chars
        "copy_cta": "SHOP_NOW",
        "hooks": ["Hook 1", "Hook 2", "Hook 3"],
        "technical_specs": {
            "aspect_ratio": "1:1",
            "dimensions": "1080x1080",
            "file_format": "PNG"
        }
    }

    is_valid, errors = validate_creative_prompt(exact_limit_prompt, "Meta")
    print(f"Exact limit prompt valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    assert is_valid, "Prompt at exact limits should be valid"

    # Test TikTok limits
    tiktok_limits = PLATFORM_SPECS["TikTok"]["copy_limits"]
    print(f"TikTok limits: {tiktok_limits}")
    assert tiktok_limits["text"] == 100

    print("✓ Platform copy limits tests passed\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Creative Generation Module Tests")
    print("="*60)

    try:
        test_platform_specs_structure()
        test_validate_creative_prompt_valid()
        test_validate_creative_prompt_missing_fields()
        test_validate_creative_prompt_copy_limits()
        test_validate_creative_prompt_hooks_count()
        test_platform_specs_summary()
        test_creative_prompt_structure()
        test_platform_copy_limits()

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

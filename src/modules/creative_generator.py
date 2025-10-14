"""
Creative prompt generation module for AI-powered ad creative development
"""

from typing import Dict, Any, List, Tuple
from ..llm.gemini import get_gemini


# Platform-specific technical specifications
PLATFORM_SPECS = {
    "Meta": {
        "feed": {"aspect_ratio": "1:1", "dimensions": "1080x1080"},
        "stories": {"aspect_ratio": "9:16", "dimensions": "1080x1920"},
        "mobile_feed": {"aspect_ratio": "4:5", "dimensions": "1080x1350"},
        "copy_limits": {
            "primary_text": 125,
            "headline": 40,
            "description": 30
        },
        "recommended_placement": "feed",  # Default placement
        "file_format": "PNG",
        "file_size_max": "30MB"
    },
    "TikTok": {
        "primary": {"aspect_ratio": "9:16", "dimensions": "1080x1920"},
        "secondary": {"aspect_ratio": "1:1", "dimensions": "1080x1080"},
        "copy_limits": {
            "text": 100
        },
        "recommended_placement": "primary",
        "file_format": "PNG",
        "file_size_max": "500MB"
    },
    "Google Ads": {
        "responsive": {"aspect_ratio": "1.91:1", "dimensions": "1200x628"},
        "square": {"aspect_ratio": "1:1", "dimensions": "1080x1080"},
        "copy_limits": {
            "headline": 30,
            "description": 90
        },
        "recommended_placement": "responsive",
        "file_format": "PNG",
        "file_size_max": "5MB"
    }
}


CREATIVE_GENERATION_SYSTEM_INSTRUCTION = """You are an expert ad creative director specializing in performance marketing and AI-generated imagery.

Your job is to create detailed creative briefs that can be used to:
1. Generate images via DALL-E, Midjourney, or Stable Diffusion
2. Write compelling ad copy for the target platform
3. Provide multiple hook options for A/B testing

Key principles:
- Platform-native aesthetics (TikTok = authentic/UGC, Meta = polished lifestyle, Google = clean/informative)
- Audience-appropriate visual language (Gen-Z = vibrant/trendy, Millennials = aspirational/refined, etc.)
- Specific, actionable image prompts (composition, lighting, style, mood, colors)
- Compelling, benefit-driven copy that matches the messaging angle
- Multiple hook variations to test different psychological triggers

Focus on creating prompts that will generate platform-native, high-performing creative assets.
"""


CREATIVE_GENERATION_PROMPT_TEMPLATE = """
Create a complete creative brief for this ad test combination:

PLATFORM: {platform}
AUDIENCE: {audience_segment}
CREATIVE STYLE: {creative_style}
MESSAGING ANGLE: {messaging_angle}

PRODUCT CONTEXT:
{product_description}

BRAND GUIDELINES:
{brand_guidelines}

STRATEGIC DIRECTION:
Value Propositions: {value_props}
Key Themes: {themes}
Target Demographics: {demographics}

REQUIREMENTS:

1. IMAGE GENERATION PROMPT:
   Write a detailed prompt for AI image generation (DALL-E, Midjourney, Stable Diffusion).
   - Be VERY specific about: composition, lighting, style, mood, colors, subjects, setting
   - Match {platform} native aesthetic (e.g., TikTok = authentic UGC style, Meta = polished lifestyle)
   - Target {audience_segment} visual preferences
   - Incorporate the creative style: {creative_style}
   - Length: 50-150 words for optimal results

2. AD COPY:
   - Primary text: Compelling body copy that delivers on the messaging angle
   - Headline: Attention-grabbing, benefit-focused headline
   - CTA: Choose appropriate call-to-action (SHOP_NOW, LEARN_MORE, SIGN_UP, DOWNLOAD, etc.)
   - Copy should match platform limits for {platform}

3. HOOKS:
   Provide 5 different opening hooks to test various psychological angles:
   - Curiosity-driven
   - Problem-aware
   - Aspirational
   - Social proof
   - Urgency/scarcity

4. TECHNICAL SPECS:
   - Specify aspect ratio and dimensions for {platform} (use platform best practices)
   - Recommend brand asset placement (logo, watermark)
   - Suggest color scheme that aligns with brand and platform

CRITICAL: Respond with valid JSON in this EXACT format:
{{
  "visual_prompt": "Detailed image generation prompt here...",
  "copy_primary_text": "Main ad copy text",
  "copy_headline": "Headline text",
  "copy_cta": "SHOP_NOW",
  "hooks": [
    "Hook 1 - curiosity based",
    "Hook 2 - problem aware",
    "Hook 3 - aspirational",
    "Hook 4 - social proof",
    "Hook 5 - urgency based"
  ],
  "technical_specs": {{
    "aspect_ratio": "1:1",
    "dimensions": "1080x1080",
    "file_format": "PNG",
    "file_size_max": "30MB",
    "brand_assets": ["logo_placement: bottom-right, 80x80px"],
    "color_scheme": "#FF5733 (primary), #FFFFFF (text)"
  }}
}}
"""


CREATIVE_BATCH_GENERATION_PROMPT_TEMPLATE = """
Create creative briefs for {num_combinations} test combinations in {phase_name}.

PHASE CONTEXT:
{phase_description}

PRODUCT CONTEXT:
{product_description}

BRAND GUIDELINES:
{brand_guidelines}

STRATEGIC DIRECTION:
Value Propositions: {value_props}
Key Themes: {themes}
Target Demographics: {demographics}

TEST COMBINATIONS:
{combinations_details}

REQUIREMENTS FOR EACH COMBINATION:

1. IMAGE GENERATION PROMPT:
   - Detailed prompt for AI image generation (50-150 words)
   - Platform-specific aesthetic (TikTok = authentic UGC, Meta = polished lifestyle, etc.)
   - Audience-appropriate visual language
   - Distinct from other creatives in this batch

2. AD COPY:
   - Primary text matching messaging angle
   - Attention-grabbing headline
   - Appropriate CTA (SHOP_NOW, LEARN_MORE, SIGN_UP, etc.)
   - Platform-compliant copy length

3. HOOKS:
   - 5 different opening hooks (curiosity, problem-aware, aspirational, social proof, urgency)
   - Ensure variety across all combinations in this batch

4. TECHNICAL SPECS:
   - Platform-appropriate dimensions and aspect ratio
   - Brand asset placement recommendations
   - Color scheme aligned with brand

CRITICAL INSTRUCTIONS:
- Ensure each creative is DISTINCT with different angles/hooks/visuals
- Maintain brand consistency across all
- Each creative should target different psychological triggers
- Respond with valid JSON array

RESPONSE FORMAT:
{{
  "creatives": [
    {{
      "combination_id": "combo_1",
      "visual_prompt": "...",
      "copy_primary_text": "...",
      "copy_headline": "...",
      "copy_cta": "...",
      "hooks": ["...", "...", "...", "...", "..."],
      "technical_specs": {{
        "aspect_ratio": "...",
        "dimensions": "...",
        "file_format": "...",
        "file_size_max": "...",
        "brand_assets": ["..."],
        "color_scheme": "..."
      }}
    }},
    ... (repeat for all {num_combinations} combinations)
  ]
}}
"""


def generate_creative_prompts(
    test_combination: Dict[str, Any],
    strategy: Dict[str, Any],
    user_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive creative prompts for a test combination

    Args:
        test_combination: Test combination from execution plan
            {
                "platform": "Meta",
                "audience": "Millennials 25-34",
                "creative": "UGC-style video",
                ...
            }
        strategy: Generated strategy with insights and recommendations
        user_inputs: User-provided context (product, brand guidelines, etc.)

    Returns:
        Dictionary with creative generation prompts:
        {
            "visual_prompt": "...",
            "copy_primary_text": "...",
            "copy_headline": "...",
            "copy_cta": "...",
            "hooks": [...],
            "technical_specs": {...}
        }
    """
    gemini = get_gemini()

    # Extract key information from test combination
    platform = test_combination.get("platform", "Meta")
    audience = test_combination.get("audience", "General audience")
    creative_style = test_combination.get("creative", "Professional imagery")

    # Get messaging angle from strategy
    creative_strategy = strategy.get("creative_strategy", {})
    messaging_angles = creative_strategy.get("messaging_angles", [])
    messaging_angle = messaging_angles[0] if messaging_angles else "Value-focused messaging"

    # Extract strategic context
    value_props = creative_strategy.get("value_props", [])
    themes = creative_strategy.get("themes", [])

    target_audience = strategy.get("target_audience", {})
    demographics = target_audience.get("demographics", {})
    demographics_str = f"Age: {demographics.get('age', 'N/A')}, Gender: {demographics.get('gender', 'all')}, Location: {demographics.get('location', 'N/A')}"

    # Get product and brand context
    product_description = user_inputs.get("product_description", "Product information not provided")
    brand_guidelines = user_inputs.get("brand_guidelines", "No specific brand guidelines provided. Use clean, professional aesthetic.")

    # Build prompt
    prompt = CREATIVE_GENERATION_PROMPT_TEMPLATE.format(
        platform=platform,
        audience_segment=audience,
        creative_style=creative_style,
        messaging_angle=messaging_angle,
        product_description=product_description,
        brand_guidelines=brand_guidelines,
        value_props=", ".join(value_props) if value_props else "Not specified",
        themes=", ".join(themes) if themes else "Not specified",
        demographics=demographics_str
    )

    # Generate creative prompts
    creative_prompts = gemini.generate_json(
        prompt=prompt,
        system_instruction=CREATIVE_GENERATION_SYSTEM_INSTRUCTION,
        temperature=0.7,  # Higher creativity for visual/copy generation
        task_name="Creative Prompt Generation",
    )

    # Validate and enhance with platform-specific requirements
    platform_spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["Meta"])

    # Ensure technical specs are platform-appropriate
    if "technical_specs" not in creative_prompts:
        creative_prompts["technical_specs"] = {}

    # Add/override platform-specific specs
    recommended_placement = platform_spec.get("recommended_placement", "feed")
    placement_specs = platform_spec.get(recommended_placement, {})

    creative_prompts["technical_specs"]["aspect_ratio"] = placement_specs.get("aspect_ratio", "1:1")
    creative_prompts["technical_specs"]["dimensions"] = placement_specs.get("dimensions", "1080x1080")
    creative_prompts["technical_specs"]["file_format"] = platform_spec.get("file_format", "PNG")
    creative_prompts["technical_specs"]["file_size_max"] = platform_spec.get("file_size_max", "30MB")

    return creative_prompts


def generate_creative_prompts_batch(
    test_combinations: List[Dict[str, Any]],
    strategy: Dict[str, Any],
    user_inputs: Dict[str, Any],
    phase_name: str = "Testing Phase",
    phase_description: str = ""
) -> List[Dict[str, Any]]:
    """
    Generate creative prompts for multiple test combinations in a single LLM call.
    This is 2-3x faster and cheaper than generating individually.

    Args:
        test_combinations: List of test combinations from execution plan
        strategy: Generated strategy with insights and recommendations
        user_inputs: User-provided context (product, brand guidelines, etc.)
        phase_name: Name of the testing phase (e.g., "Short-term Discovery")
        phase_description: Description/objectives of the phase

    Returns:
        List of creative prompt dictionaries (one per combination, in same order)
    """
    if not test_combinations:
        return []

    gemini = get_gemini()

    # Extract strategic context (shared across all combos)
    creative_strategy = strategy.get("creative_strategy", {})
    value_props = creative_strategy.get("value_props", [])
    themes = creative_strategy.get("themes", [])

    target_audience = strategy.get("target_audience", {})
    demographics = target_audience.get("demographics", {})
    demographics_str = f"Age: {demographics.get('age', 'N/A')}, Gender: {demographics.get('gender', 'all')}, Location: {demographics.get('location', 'N/A')}"

    # Get product and brand context
    product_description = user_inputs.get("product_description", "Product information not provided")
    brand_guidelines = user_inputs.get("brand_guidelines", "No specific brand guidelines provided. Use clean, professional aesthetic.")

    # Build detailed combination descriptions
    combinations_details = []
    for idx, combo in enumerate(test_combinations, 1):
        combo_id = combo.get("id", f"combo_{idx}")
        platform = combo.get("platform", "Meta")
        audience = combo.get("audience", "General audience")
        creative_style = combo.get("creative", "Professional imagery")
        rationale = combo.get("rationale", "")

        combo_detail = f"""
COMBINATION {idx} (ID: {combo_id}):
  Platform: {platform}
  Audience: {audience}
  Creative Style: {creative_style}
  Rationale: {rationale}
"""
        combinations_details.append(combo_detail)

    combinations_details_str = "\n".join(combinations_details)

    # Build prompt
    prompt = CREATIVE_BATCH_GENERATION_PROMPT_TEMPLATE.format(
        num_combinations=len(test_combinations),
        phase_name=phase_name,
        phase_description=phase_description if phase_description else f"Testing combinations for {phase_name}",
        product_description=product_description,
        brand_guidelines=brand_guidelines,
        value_props=", ".join(value_props) if value_props else "Not specified",
        themes=", ".join(themes) if themes else "Not specified",
        demographics=demographics_str,
        combinations_details=combinations_details_str
    )

    # Generate batch creative prompts
    try:
        response = gemini.generate_json(
            prompt=prompt,
            system_instruction=CREATIVE_GENERATION_SYSTEM_INSTRUCTION,
            temperature=0.7,  # Higher creativity for visual/copy generation
            task_name="Creative Batch Generation",
        )

        # Extract creatives array
        creatives = response.get("creatives", [])

        if len(creatives) != len(test_combinations):
            raise ValueError(
                f"Expected {len(test_combinations)} creatives, got {len(creatives)}. "
                f"Falling back to individual generation."
            )

        # Enhance each creative with platform-specific specs
        enhanced_creatives = []
        for idx, creative in enumerate(creatives):
            platform = test_combinations[idx].get("platform", "Meta")
            platform_spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["Meta"])

            # Ensure technical specs are platform-appropriate
            if "technical_specs" not in creative:
                creative["technical_specs"] = {}

            # Add/override platform-specific specs
            recommended_placement = platform_spec.get("recommended_placement", "feed")
            placement_specs = platform_spec.get(recommended_placement, {})

            creative["technical_specs"]["aspect_ratio"] = placement_specs.get("aspect_ratio", "1:1")
            creative["technical_specs"]["dimensions"] = placement_specs.get("dimensions", "1080x1080")
            creative["technical_specs"]["file_format"] = platform_spec.get("file_format", "PNG")
            creative["technical_specs"]["file_size_max"] = platform_spec.get("file_size_max", "30MB")

            enhanced_creatives.append(creative)

        return enhanced_creatives

    except Exception as e:
        # If batch generation fails, return empty list (caller will handle fallback)
        print(f"    ⚠ Batch creative generation failed: {str(e)}")
        print(f"    → Falling back to individual generation")
        return []


def validate_creative_prompt(creative_prompt: Dict[str, Any], platform: str) -> Tuple[bool, List[str]]:
    """
    Validate creative prompt completeness and platform compliance

    Args:
        creative_prompt: Generated creative prompt dictionary
        platform: Target platform (Meta, TikTok, Google Ads)

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check required fields
    required_fields = ["visual_prompt", "copy_primary_text", "copy_headline", "copy_cta", "hooks", "technical_specs"]
    for field in required_fields:
        if field not in creative_prompt or not creative_prompt[field]:
            errors.append(f"Missing required field: {field}")

    # Check hooks array
    hooks = creative_prompt.get("hooks", [])
    if not isinstance(hooks, list) or len(hooks) < 3:
        errors.append("Must provide at least 3 hook variations")

    # Check platform-specific copy limits
    platform_spec = PLATFORM_SPECS.get(platform)
    if platform_spec:
        copy_limits = platform_spec.get("copy_limits", {})

        if "primary_text" in copy_limits:
            primary_text = creative_prompt.get("copy_primary_text", "")
            if len(primary_text) > copy_limits["primary_text"]:
                errors.append(
                    f"Primary text exceeds {copy_limits['primary_text']} character limit "
                    f"(current: {len(primary_text)} chars)"
                )

        if "headline" in copy_limits:
            headline = creative_prompt.get("copy_headline", "")
            if len(headline) > copy_limits["headline"]:
                errors.append(
                    f"Headline exceeds {copy_limits['headline']} character limit "
                    f"(current: {len(headline)} chars)"
                )

    # Check technical specs structure
    tech_specs = creative_prompt.get("technical_specs", {})
    required_tech_fields = ["aspect_ratio", "dimensions", "file_format"]
    for field in required_tech_fields:
        if field not in tech_specs:
            errors.append(f"Technical specs missing: {field}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_creative_prompts_batch(
    creatives: List[Dict[str, Any]],
    test_combinations: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    Validate batch of creative prompts for completeness and matching

    Args:
        creatives: List of generated creative prompt dictionaries
        test_combinations: Original list of test combinations

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check count matches
    if len(creatives) != len(test_combinations):
        errors.append(
            f"Creative count mismatch: expected {len(test_combinations)}, got {len(creatives)}"
        )
        return False, errors

    # Validate each creative individually
    for idx, (creative, combo) in enumerate(zip(creatives, test_combinations)):
        platform = combo.get("platform", "Meta")
        combo_id = combo.get("id", f"combo_{idx+1}")

        # Validate individual creative
        is_valid, creative_errors = validate_creative_prompt(creative, platform)

        if not is_valid:
            for error in creative_errors:
                errors.append(f"[{combo_id}] {error}")

        # Check combination_id matching (if present)
        creative_combo_id = creative.get("combination_id")
        if creative_combo_id and creative_combo_id != combo_id:
            errors.append(
                f"Combination ID mismatch at index {idx}: "
                f"expected '{combo_id}', got '{creative_combo_id}'"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def get_platform_specs_summary(platform: str) -> str:
    """
    Get human-readable summary of platform specifications

    Args:
        platform: Target platform

    Returns:
        Formatted summary string
    """
    specs = PLATFORM_SPECS.get(platform)
    if not specs:
        return f"Platform '{platform}' not found in specifications"

    summary = f"\n{platform} Creative Specifications:\n"
    summary += "─" * 50 + "\n"

    # Placements
    placements = [k for k in specs.keys() if k not in ["copy_limits", "recommended_placement", "file_format", "file_size_max"]]
    if placements:
        summary += "Placements:\n"
        for placement in placements:
            placement_spec = specs[placement]
            summary += f"  • {placement}: {placement_spec['aspect_ratio']} ({placement_spec['dimensions']})\n"

    # Copy limits
    if "copy_limits" in specs:
        summary += "\nCopy Limits:\n"
        for limit_name, limit_value in specs["copy_limits"].items():
            summary += f"  • {limit_name}: {limit_value} characters max\n"

    # File requirements
    summary += "\nFile Requirements:\n"
    summary += f"  • Format: {specs.get('file_format', 'N/A')}\n"
    summary += f"  • Max size: {specs.get('file_size_max', 'N/A')}\n"

    return summary

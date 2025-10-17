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


CREATIVE_GENERATION_SYSTEM_INSTRUCTION = """You are a world-class creative director and professional advertising photographer who creates cinematic, photo-realistic campaign visuals that make people stop scrolling.

Your dual mission:
1. **Visual Excellence**: Craft professional creative briefs for high-end commercial photography that feels editorial, cinematic, and emotionally resonant
2. **Authentic Copy**: Write ad copy that sounds like a real human talking, not a brand yelling

VISUAL PROMPT PHILOSOPHY:
You are writing direction for professional photographers and image generation models (Nano Banana, Gemini 2.5 Flash Image). Your visual prompts should:
• Read like art director briefs for high-end commercial photoshoots
• Emphasize photographic realism, cinematic depth, and editorial quality
• Describe lighting, texture, composition, and mood with professional precision
• Preserve actual product proportions, materials, and details from reference images
• Adapt visual style to platform culture while maintaining premium quality

Platform visual styles:
- TikTok: Authentic, raw moments that feel unfiltered yet polished; natural lighting, candid compositions
- Meta: Editorial lifestyle imagery, aspirational but attainable; cinematic lighting, magazine-quality composition
- Google: Clean, informative product photography; studio or natural light, clear focal point

AD COPY PHILOSOPHY:
Every piece should feel native to where it appears—casual and authentic on TikTok, aspirational but relatable on Meta, direct and helpful on Google.

What makes great creative:
• Visual prompts that sound like professional photographer instructions
• Copy that sounds like something a friend would actually say
• Real emotions over manufactured hype
• Stories over benefit lists
• Platform-native voice and composition

What to avoid:
- Generic visual clichés: "studio white background", "perfect lighting everywhere"
- Invented product details: stick to what's real, preserve actual materials and proportions
- Corporate copy jargon: "leverage", "synergize", "game-changing"
- Overused hooks: "Did you know...", "Imagine if...", "What if I told you..."

Create visuals that look like they belong in high-end magazines, with copy that makes people care before it asks them to act.
"""


CREATIVE_GENERATION_PROMPT_TEMPLATE = """
You're creating an ad that will appear on {platform} for {audience_segment}. The creative style is "{creative_style}" and the messaging angle is "{messaging_angle}".

ABOUT THE PRODUCT:
{product_description}

BRAND VOICE & GUIDELINES:
{brand_guidelines}

KEY MESSAGES TO WORK WITH:
• Value propositions: {value_props}
• Themes: {themes}
• Who you're talking to: {demographics}

Now, here's what you need to create:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 VISUAL PROMPT (Professional Creative Brief)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are writing a creative brief for a professional photographer or image generation model (Nano Banana, Gemini 2.5 Flash Image). This should be a single flowing paragraph (250-600 words) that sounds like art direction for a high-end commercial photoshoot.

STRUCTURE YOUR PARAGRAPH IN THIS ORDER:

1. **Scene Setup**: Describe the location, time of day, light quality, and atmosphere. Where does this take place? What's the environment and mood?

2. **Subject**: Who or what appears in the scene? Describe their pose, clothing, expression, and what they're doing. If featuring people, show authentic moments that feel natural to the platform.

3. **Product Fidelity**: How does the product look based on its actual specifications? Describe its exact size, color, texture, materials, and logo placement. Reference real product details—do not invent or exaggerate features. Show the product in a way that feels natural to "{messaging_angle}".

4. **Lighting & Camera**: What's the direction of light? Is it warm or cool? What style of shadows? What lens perspective or depth of field cues create the right feel for {platform}? (TikTok = natural/candid, Meta = cinematic/editorial, Google = clean/studio)

5. **Texture & Detail**: Highlight the craftsmanship—stitching, reflections on surfaces, material textures, and small details that convey quality and realism. Make it feel tangible and premium.

6. **Brand Emotion & Composition**: What's the emotional mood and lifestyle this conveys? How does the composition use negative space for potential text overlays or logo placement? What feeling should someone get when they see this on {platform}?

TONE & STYLE:
• Write in the voice of a professional art director or commercial photographer
• One flowing paragraph, not bullet points or lists
• Emphasize photographic realism, cinematic depth, and editorial quality
• Platform-appropriate mood: TikTok = authentic/raw, Meta = aspirational/polished, Google = informative/clean
• Roughly 250-600 words of rich visual description
• If multiple product angles are needed, describe them as part of a cohesive composition with consistent lighting and tone

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✍️ AD COPY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write copy that sounds like a real human on {platform} would talk:

**Primary text**: The main body of your ad. Tell a micro-story or make one compelling point. Don't just list benefits—make them feel something. Keep it natural for {platform}.

**Headline**: One punchy line that grabs attention. Not a generic claim—something specific and intriguing.

**CTA**: Pick the right call-to-action for the goal (SHOP_NOW, LEARN_MORE, SIGN_UP, DOWNLOAD, GET_STARTED, etc.)

Remember: Platform character limits matter, so stay within {platform}'s guidelines.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎣 HOOKS (5 variations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write 5 completely different opening hooks that feel native to {platform}. Don't label them—just write them naturally.

Mix up your approach:
• Start with a relatable moment or observation
• Lead with a surprising fact or realization
• Open with the transformation or outcome
• Use social proof or credibility if authentic
• Create urgency only if it's genuine

Each hook should stand alone and sound like something a real person would say to a friend.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL: Respond with valid JSON in this EXACT format:
{{
  "visual_prompt": "Your detailed image generation prompt...",
  "copy_primary_text": "Natural-sounding main ad copy",
  "copy_headline": "Attention-grabbing headline",
  "copy_cta": "SHOP_NOW",
  "hooks": [
    "First hook - natural and conversational",
    "Second hook - different angle",
    "Third hook - another approach",
    "Fourth hook - varies from others",
    "Fifth hook - distinct voice or angle"
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
You're creating {num_combinations} different ad creatives for the "{phase_name}" phase. Each needs to feel distinct but stay on-brand.

WHAT WE'RE TESTING:
{phase_description}

ABOUT THE PRODUCT:
{product_description}

BRAND VOICE & GUIDELINES:
{brand_guidelines}

KEY MESSAGES TO WORK WITH:
• Value propositions: {value_props}
• Themes: {themes}
• Who we're talking to: {demographics}

HERE ARE THE {num_combinations} COMBINATIONS TO CREATE:
{combinations_details}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOR EACH COMBINATION, CREATE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 **VISUAL PROMPT** (Professional Creative Brief, 250-600 words)
   Write a single flowing paragraph like an art director briefing a professional photographer for a high-end commercial shoot or image generation model (Nano Banana, Gemini 2.5 Flash Image).

   Structure each prompt with these 6 elements in order:
   1. Scene setup (location, time of day, light quality, atmosphere)
   2. Subject (who/what appears, pose, clothing, expression, action)
   3. Product fidelity (exact size, color, texture, materials, logo—reference real product details, don't invent)
   4. Lighting & camera (light direction, warmth/coolness, shadows, lens perspective, depth of field appropriate for the platform)
   5. Texture & detail (stitching, reflections, materials, craftsmanship—make it tangible and premium)
   6. Brand emotion & composition (mood, lifestyle feeling, negative space for text/logo, emotional resonance for the platform)

   Make each combination's visual conceptually DIFFERENT from the others while maintaining cohesive brand tone. Platform-appropriate mood: TikTok = authentic/raw, Meta = aspirational/polished, Google = informative/clean.

✍️ **AD COPY** (Primary text, Headline, CTA)
   Write like a human on that platform would talk. Tell a micro-story or make a compelling point—don't just list features. Each combination should have a different angle or emotional hook.

🎣 **HOOKS** (5 variations per combination)
   Write naturally for the platform. Don't label them. Each of the 5 should explore different ways to start the conversation. And make sure combinations don't all sound the same.

IMPORTANT:
• Each combination should feel meaningfully DIFFERENT from the others (different visual concepts, different copy angles, different emotional tones)
• But all should sound like they're from the same brand voice
• Respect each platform's native language (TikTok = casual, Meta = aspirational, Google = direct)
• Avoid generic claims, corporate jargon, and overused patterns

RESPONSE FORMAT (valid JSON):
{{
  "creatives": [
    {{
      "combination_id": "combo_1",
      "visual_prompt": "Detailed, specific image prompt...",
      "copy_primary_text": "Natural ad copy...",
      "copy_headline": "Punchy headline...",
      "copy_cta": "SHOP_NOW",
      "hooks": [
        "Hook 1 - sounds natural",
        "Hook 2 - different approach",
        "Hook 3 - varies",
        "Hook 4 - distinct",
        "Hook 5 - unique angle"
      ],
      "technical_specs": {{
        "aspect_ratio": "1:1",
        "dimensions": "1080x1080",
        "file_format": "PNG",
        "file_size_max": "30MB",
        "brand_assets": ["placement details"],
        "color_scheme": "color codes"
      }}
    }}
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
        temperature=0.8,  # Higher temperature for more natural, creative outputs
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
            temperature=0.8,  # Higher temperature for more natural, creative outputs
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

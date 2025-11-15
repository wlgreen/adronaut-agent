"""
Creative prompt generation module for AI-powered ad creative development
"""

from typing import Dict, Any, List, Tuple
import re
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


# Product feature to visual marker mapping
FEATURE_VISUAL_MARKERS = {
    # Audio/Headphone features
    "noise cancellation": [
        "CLEARLY VISIBLE small external microphone holes or grilles on the ear cups for active noise detection (flush-mounted circular or oval openings)",
        "thick, plush memory foam ear cushions that create a VISIBLE SEAL around the ears, showing cushion depth and softness",
        "closed-back ear cup design with solid outer shells",
        "small LED indicator light CLEARLY VISIBLE on the headphone body (white or green for ANC active status)"
    ],
    "active noise cancellation": [
        "CLEARLY VISIBLE small external microphone holes or grilles on the ear cups for active noise detection (flush-mounted circular or oval openings)",
        "thick, plush memory foam ear cushions that create a VISIBLE SEAL around the ears, showing cushion depth and softness",
        "closed-back ear cup design with solid outer shells",
        "small LED indicator light CLEARLY VISIBLE on the headphone body (white or green for ANC active status)"
    ],
    "anc": [
        "CLEARLY VISIBLE small external microphone holes or grilles on the ear cups for noise detection",
        "thick, plush memory foam ear cushions creating a visible seal around the ears",
        "closed-back ear cup design"
    ],
    "wireless": [
        "clean design with ABSOLUTELY NO VISIBLE CABLES or wires connecting to the headphones",
        "small LED indicator light showing wireless connectivity status (blue pulse or solid blue for Bluetooth pairing)",
        "sleek wireless aesthetic with smooth, uninterrupted surfaces"
    ],
    "bluetooth": [
        "ABSOLUTELY NO CABLES attached to the headphones anywhere",
        "small LED light CLEARLY VISIBLE showing Bluetooth status (blue color for pairing/connection)",
        "wireless connectivity evident in clean, cable-free design"
    ],

    # Premium/Quality features
    "premium": [
        "high-quality materials with VISIBLE TEXTURE clearly shown (brushed metal surfaces, genuine leather grain, premium fabric weave)",
        "precision craftsmanship evident in seams, joints, and assembly with visible clean lines",
        "refined color palette with premium finishing touches",
        "brand logo or emblem CLEARLY VISIBLE and well-lit (debossed, engraved, or embossed on ear cups or headband)"
    ],
    "luxury": [
        "premium materials like brushed aluminum, soft leather, or high-end fabrics with VISIBLE material quality",
        "meticulous attention to detail in stitching and construction - every seam should be visible and perfect",
        "sophisticated color schemes and metallic accents that catch the light",
        "prominent brand marking or logo CLEARLY VISIBLE (embossed, debossed, or laser-engraved)"
    ],

    # Technology features
    "touch controls": [
        "visible touch-sensitive panel on ear cup",
        "smooth, glossy surface indicating touch interface",
        "subtle touch gesture icons or indicators"
    ],
    "long battery": [
        "USB-C charging port visible",
        "battery indicator LED",
        "robust build suggesting extended use capability"
    ],

    # Comfort features
    "comfortable": [
        "soft, padded ear cushions with visible plushness",
        "adjustable headband with cushioning",
        "ergonomic shape conforming to head/ear contours"
    ],
    "lightweight": [
        "slim profile and streamlined design",
        "minimal bulk while maintaining structure",
        "refined proportions suggesting reduced weight"
    ]
}


def extract_product_features(product_description: str) -> List[str]:
    """
    Extract key product features from description and map them to specific visual markers

    Args:
        product_description: Raw product description text

    Returns:
        List of specific visual markers that should appear in generated images
    """
    if not product_description:
        return []

    # Convert to lowercase for matching
    desc_lower = product_description.lower()

    visual_markers = []
    matched_features = []

    # Find all matching features
    for feature_key, markers in FEATURE_VISUAL_MARKERS.items():
        if feature_key in desc_lower:
            matched_features.append(feature_key)
            visual_markers.extend(markers)

    # Remove duplicates while preserving order
    unique_markers = []
    seen = set()
    for marker in visual_markers:
        if marker not in seen:
            unique_markers.append(marker)
            seen.add(marker)

    return unique_markers


def enhance_visual_prompt_with_features(
    visual_prompt_template: str,
    product_description: str
) -> str:
    """
    Enhance the visual prompt template with explicit product feature requirements

    Args:
        visual_prompt_template: Base visual prompt template
        product_description: Product description to extract features from

    Returns:
        Enhanced template with feature-specific instructions
    """
    visual_markers = extract_product_features(product_description)

    if not visual_markers:
        return visual_prompt_template

    # Create feature emphasis section
    feature_emphasis = "\n\nCRITICAL PRODUCT FEATURES THAT MUST BE VISIBLE:\n"
    feature_emphasis += "The product MUST clearly show these specific visual elements:\n"
    for marker in visual_markers:
        feature_emphasis += f"• {marker}\n"
    feature_emphasis += "\nThese features are ESSENTIAL to the product's identity and must be prominently depicted.\n"

    # Insert feature emphasis after product fidelity section
    if "3. **Product fidelity**:" in visual_prompt_template:
        enhanced = visual_prompt_template.replace(
            "3. **Product fidelity**: Describe the product precisely (shape, color, materials, proportions, logo placement) based on the uploaded reference.",
            f"3. **Product fidelity**: Describe the product precisely (shape, color, materials, proportions, logo placement) based on the uploaded reference.{feature_emphasis}"
        )
        return enhanced

    # Fallback: Add to beginning of template
    return feature_emphasis + "\n" + visual_prompt_template


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

{feature_requirements}

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

You are a professional creative prompt author for high-end advertising photography.
Your task is to write one refined, production-ready image prompt for an image-generation model (such as Nano Banana or Gemini 2.5 Flash Image).

The output must sound like a creative brief for a commercial photographer — realistic, cinematic, emotionally resonant, and brand-consistent.

STRUCTURE (in this order):

1. **Scene setup**: Describe the location, time of day, light quality, and mood.

2. **Subject**: Describe who or what is in the image, their action, attire, and demeanor.

3. **Product fidelity**: Describe the product precisely (shape, color, materials, proportions, logo placement) based on the uploaded reference. {feature_emphasis}

4. **Lighting and camera**: Describe light direction, color temperature, exposure, lens perspective, and depth of field.

5. **Texture and detail**: Mention stitching, fabric texture, reflections, and tactile realism.

6. **Brand emotion and composition**: Convey the mood (premium, minimalist, adventurous, elegant, etc.) and note clean negative space for possible text overlay.

PRODUCT VISIBILITY AND FIDELITY REQUIREMENTS:

• The product must be clearly visible and prominent — occupying roughly one-third of the frame.
• It must be unobstructed, positioned naturally (e.g., at the model's waist if wearable).
• Maintain exact proportions and materials from the reference image — do not stylize, resize, or alter the design.
• Lighting must illuminate all key details (logo, stitching, zippers, texture).
• If there is any conflict, always prioritize product accuracy and visibility over background or subject.

TONE AND QUALITY:

• Use photographic realism — emulate professional editorial lighting and camera optics.
• Keep the language clear, descriptive, and cinematic, not technical or imperative.
• Avoid lists, directives, or "generate" verbs — write as one flowing paragraph.
• Maintain premium brand tone similar to Arc'teryx, Peak Design, or Patagonia campaigns.
• End with a sense of professional polish ("editorial, print-ready advertising photography").
• Roughly 250-600 words of rich visual description

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

CRITICAL: Respond with valid JSON in this EXACT format (no comments, no extra text):
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

Note: All fields are required. Provide exactly 5 hooks in the array.
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
   You are a professional creative prompt author for high-end advertising photography.
   Write one refined, production-ready image prompt for an image-generation model (such as Nano Banana or Gemini 2.5 Flash Image).
   The output must sound like a creative brief for a commercial photographer — realistic, cinematic, emotionally resonant, and brand-consistent.

   STRUCTURE (in this order):
   1. Scene setup: Describe the location, time of day, light quality, and mood.
   2. Subject: Describe who or what is in the image, their action, attire, and demeanor.
   3. Product fidelity: Describe the product precisely (shape, color, materials, proportions, logo placement) based on the uploaded reference.
   4. Lighting and camera: Describe light direction, color temperature, exposure, lens perspective, and depth of field.
   5. Texture and detail: Mention stitching, fabric texture, reflections, and tactile realism.
   6. Brand emotion and composition: Convey the mood (premium, minimalist, adventurous, elegant, etc.) and note clean negative space for possible text overlay.

   PRODUCT VISIBILITY AND FIDELITY REQUIREMENTS:
   • The product must be clearly visible and prominent — occupying roughly one-third of the frame.
   • It must be unobstructed, positioned naturally (e.g., at the model's waist if wearable).
   • Maintain exact proportions and materials from the reference image — do not stylize, resize, or alter the design.
   • Lighting must illuminate all key details (logo, stitching, zippers, texture).
   • If there is any conflict, always prioritize product accuracy and visibility over background or subject.

   TONE AND QUALITY:
   • Use photographic realism — emulate professional editorial lighting and camera optics.
   • Keep the language clear, descriptive, and cinematic, not technical or imperative.
   • Avoid lists, directives, or "generate" verbs — write as one flowing paragraph.
   • Maintain premium brand tone similar to Arc'teryx, Peak Design, or Patagonia campaigns.
   • End with a sense of professional polish ("editorial, print-ready advertising photography").

   Make each combination's visual conceptually DIFFERENT from the others while maintaining cohesive brand tone.

✍️ **AD COPY** (Primary text, Headline, CTA)
   Write like a human on that platform would talk. Tell a micro-story or make a compelling point—don't just list features. Each combination should have a different angle or emotional hook.

🎣 **HOOKS** (5 variations per combination)
   Write naturally for the platform. Don't label them. Each of the 5 should explore different ways to start the conversation. And make sure combinations don't all sound the same.

IMPORTANT:
• Each combination should feel meaningfully DIFFERENT from the others (different visual concepts, different copy angles, different emotional tones)
• But all should sound like they're from the same brand voice
• Respect each platform's native language (TikTok = casual, Meta = aspirational, Google = direct)
• Avoid generic claims, corporate jargon, and overused patterns

RESPONSE FORMAT (valid JSON - no comments, no extra text):
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
  ]
}}

IMPORTANT: Include exactly {num_combinations} creative objects in the "creatives" array.
"""


VISUAL_PROMPT_REVIEW_SYSTEM_INSTRUCTION = """You are a creative-director reviewer who evaluates and improves visual-generation prompts for realism, product fidelity, and storytelling strength.

Your expertise:
- Professional advertising photography direction (Arc'teryx, Peak Design, Patagonia level)
- Cinematic lighting and camera techniques
- Product fidelity and brand consistency
- Editorial composition and mood creation

Your approach:
- Evaluate prompts against professional standards
- Identify missing details that impact quality
- Rewrite when needed while preserving the original concept
- Maintain brand tone and platform appropriateness
"""


VISUAL_PROMPT_REVIEW_TEMPLATE = """
You are reviewing a visual prompt that was generated for an image-generation model.

ORIGINAL VISUAL PROMPT:
{visual_prompt}

CONTEXT:
- Platform: {platform}
- Product: {product_description}
- Brand Guidelines: {brand_guidelines}

EVALUATION CHECKLIST:

Assess the prompt against these criteria:

1. **Scene clarity** – clear setting, time of day, atmosphere, and tone
2. **Subject realism** – natural posture, attire, and believable human behavior
3. **Product fidelity** –
   - Product matches reference in shape, size, color, materials, logo placement
   - Product is prominent (about one-third of frame) and unobstructed
   - No invented details or redesigns
4. **Lighting and camera realism** – coherent light direction, natural contrast, real-world optics (focal length, depth of field)
5. **Texture and craftsmanship** – stitching, materials, reflections, shadows where appropriate
6. **Brand tone** – mood and style consistent with brand guidelines (premium, minimalist, adventurous, etc.)
7. **Composition and layout** – balanced framing, negative space for text if required
8. **Logo treatment** – described as physical embossed or printed mark (not text); visible and correctly lit
9. **Language quality** – one flowing paragraph, descriptive not imperative, cinematic but concise (200-600 words)
10. **Professional feel** – sounds like creative brief for commercial photographer

YOUR TASK:

1. Read the prompt carefully and assess it against ALL checklist items above
2. If all criteria are met → return it unchanged with note "Prompt passes quality review"
3. If any item is missing or weak → rewrite the paragraph to fix issues while keeping the same concept, scene, and tone

CRITICAL: Respond with valid JSON in this EXACT format (no comments, no extra text):
{{
  "reviewed_prompt": "The final visual prompt (original or improved)",
  "changed": true,
  "notes": "Brief summary of what was changed or why it was already strong (2-3 sentences max)"
}}

Note: The "changed" field should be true if you made improvements, or false if the prompt was already excellent.

If you make changes:
- Keep the same scene concept and overall mood
- Preserve platform appropriateness ({platform})
- Maintain brand voice from guidelines
- Write as ONE flowing paragraph (no lists, no bullet points)
- Target 250-600 words of rich visual description
"""


VISUAL_PROMPT_REVIEW_BATCH_TEMPLATE = """
You are reviewing {num_prompts} visual prompts that were generated for image-generation models.

CONTEXT (applies to all prompts):
- Platform: {platform}
- Product: {product_description}
- Brand Guidelines: {brand_guidelines}

EVALUATION CHECKLIST (same for all):
1. Scene clarity – setting, time, atmosphere, tone
2. Subject realism – natural posture, attire, behavior
3. Product fidelity – accurate shape/size/color/materials, prominent (~1/3 frame), unobstructed
4. Lighting/camera – coherent direction, natural contrast, realistic optics
5. Texture/craftsmanship – stitching, materials, reflections, shadows
6. Brand tone – consistent with guidelines
7. Composition – balanced framing, negative space
8. Logo treatment – physical mark (not text), visible, well-lit
9. Language quality – flowing paragraph, descriptive, 200-600 words
10. Professional feel – commercial photographer brief quality

PROMPTS TO REVIEW:

{prompts_list}

YOUR TASK:

For EACH prompt:
1. Assess against checklist
2. If all criteria met → keep unchanged with note "Passes quality review"
3. If issues found → rewrite to fix while keeping same concept/scene/tone

CRITICAL: Respond with valid JSON in this EXACT format (no comments, no extra text):
{{
  "reviews": [
    {{
      "prompt_id": "combo_1",
      "reviewed_prompt": "The final visual prompt (original or improved)",
      "changed": true,
      "notes": "Brief summary (2-3 sentences)"
    }},
    {{
      "prompt_id": "combo_2",
      "reviewed_prompt": "The final visual prompt (original or improved)",
      "changed": false,
      "notes": "Brief summary (2-3 sentences)"
    }}
  ]
}}

Note: Include one review object per prompt. The "changed" field should be true or false (boolean).

Requirements for rewrites:
- ONE flowing paragraph per prompt (no lists)
- Preserve scene concept and mood
- Maintain platform appropriateness and brand voice
- 250-600 words of rich visual description
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

    # Extract product features and create requirements section
    visual_markers = extract_product_features(product_description)
    if visual_markers:
        feature_requirements = "CRITICAL PRODUCT FEATURES THAT MUST BE VISIBLE:\n"
        for marker in visual_markers:
            feature_requirements += f"• {marker}\n"
        feature_requirements += "\nThese features are ESSENTIAL to the product's identity and must be prominently depicted in the visual prompt."
        feature_emphasis = "Ensure ALL the critical product features listed above are explicitly described in the product description."
    else:
        feature_requirements = ""
        feature_emphasis = ""

    # Build prompt
    prompt = CREATIVE_GENERATION_PROMPT_TEMPLATE.format(
        platform=platform,
        audience_segment=audience,
        creative_style=creative_style,
        messaging_angle=messaging_angle,
        product_description=product_description,
        feature_requirements=feature_requirements,
        brand_guidelines=brand_guidelines,
        value_props=", ".join(value_props) if value_props else "Not specified",
        themes=", ".join(themes) if themes else "Not specified",
        demographics=demographics_str,
        feature_emphasis=feature_emphasis
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

    # REVIEW STEP: Evaluate and potentially upgrade the visual prompt
    try:
        visual_prompt = creative_prompts.get("visual_prompt", "")
        if visual_prompt:
            review_result = review_and_upgrade_visual_prompt(
                visual_prompt=visual_prompt,
                product_description=product_description,
                brand_guidelines=brand_guidelines,
                platform=platform
            )

            # Replace visual prompt with reviewed version
            creative_prompts["visual_prompt"] = review_result.get("reviewed_prompt", visual_prompt)

            # Store review metadata
            creative_prompts["visual_prompt_review"] = {
                "changed": review_result.get("changed", False),
                "notes": review_result.get("notes", "")
            }

    except Exception as e:
        # If review fails, keep original prompt and log warning
        print(f"    ⚠ Visual prompt review failed: {str(e)}")
        creative_prompts["visual_prompt_review"] = {
            "changed": False,
            "notes": f"Review failed: {str(e)}"
        }

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

    # Extract product features for all combinations
    visual_markers = extract_product_features(product_description)
    if visual_markers:
        feature_requirements = "\n\nCRITICAL PRODUCT FEATURES THAT MUST BE VISIBLE IN ALL CREATIVES:\n"
        for marker in visual_markers:
            feature_requirements += f"• {marker}\n"
        feature_requirements += "\nThese features are ESSENTIAL to the product's identity and must be prominently depicted in EVERY visual prompt.\n"
        product_description_enhanced = product_description + feature_requirements
    else:
        product_description_enhanced = product_description

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

    # Build prompt with enhanced product description
    prompt = CREATIVE_BATCH_GENERATION_PROMPT_TEMPLATE.format(
        num_combinations=len(test_combinations),
        phase_name=phase_name,
        phase_description=phase_description if phase_description else f"Testing combinations for {phase_name}",
        product_description=product_description_enhanced,
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

        # BATCH REVIEW STEP: Evaluate and potentially upgrade all visual prompts
        try:
            # Prepare visual prompts for batch review
            visual_prompts_for_review = []
            for idx, creative in enumerate(enhanced_creatives):
                combo_id = test_combinations[idx].get("id", f"combo_{idx+1}")
                visual_prompt = creative.get("visual_prompt", "")
                if visual_prompt:
                    visual_prompts_for_review.append((combo_id, visual_prompt))

            # Perform batch review (assumes all combos share same platform for efficiency)
            # If multiple platforms, we group by platform
            if visual_prompts_for_review:
                # Get platform (use first combo's platform; if mixed, batch review handles it)
                primary_platform = test_combinations[0].get("platform", "Meta")

                review_results = review_visual_prompts_batch(
                    visual_prompts=visual_prompts_for_review,
                    product_description=product_description,
                    brand_guidelines=brand_guidelines,
                    platform=primary_platform
                )

                # Apply reviewed prompts back to creatives
                for idx, creative in enumerate(enhanced_creatives):
                    combo_id = test_combinations[idx].get("id", f"combo_{idx+1}")

                    if combo_id in review_results:
                        review_result = review_results[combo_id]
                        creative["visual_prompt"] = review_result.get("reviewed_prompt", creative.get("visual_prompt", ""))
                        creative["visual_prompt_review"] = {
                            "changed": review_result.get("changed", False),
                            "notes": review_result.get("notes", "")
                        }
                    else:
                        # Review not found for this combo
                        creative["visual_prompt_review"] = {
                            "changed": False,
                            "notes": "Review not performed"
                        }

        except Exception as e:
            # If batch review fails, keep original prompts and log warning
            print(f"    ⚠ Batch visual prompt review failed: {str(e)}")
            for creative in enhanced_creatives:
                if "visual_prompt_review" not in creative:
                    creative["visual_prompt_review"] = {
                        "changed": False,
                        "notes": f"Batch review failed: {str(e)}"
                    }

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


def review_and_upgrade_visual_prompt(
    visual_prompt: str,
    product_description: str,
    brand_guidelines: str,
    platform: str
) -> Dict[str, Any]:
    """
    Review and potentially upgrade a visual prompt for quality and completeness

    This function acts as a creative director review, evaluating the visual prompt
    against professional standards and rewriting it if needed to improve:
    - Product fidelity and visibility
    - Lighting and camera realism
    - Brand consistency
    - Professional cinematic quality

    Args:
        visual_prompt: The original generated visual prompt
        product_description: Product information for context
        brand_guidelines: Brand voice and visual style guidelines
        platform: Target platform (Meta, TikTok, etc.)

    Returns:
        Dictionary with:
        {
            "reviewed_prompt": "The final prompt (original or improved)",
            "changed": bool,  # True if changes were made
            "notes": "Summary of changes or confirmation"
        }
    """
    gemini = get_gemini()

    # Build review prompt
    prompt = VISUAL_PROMPT_REVIEW_TEMPLATE.format(
        visual_prompt=visual_prompt,
        platform=platform,
        product_description=product_description if product_description else "Product information not provided",
        brand_guidelines=brand_guidelines if brand_guidelines else "No specific brand guidelines provided"
    )

    # Execute review with lower temperature for critical evaluation
    review_result = gemini.generate_json(
        prompt=prompt,
        system_instruction=VISUAL_PROMPT_REVIEW_SYSTEM_INSTRUCTION,
        temperature=0.3,  # Lower temperature for critical, analytical review
        task_name="Visual Prompt Review",
    )

    return review_result


def review_visual_prompts_batch(
    visual_prompts: List[Tuple[str, str]],  # List of (prompt_id, visual_prompt)
    product_description: str,
    brand_guidelines: str,
    platform: str
) -> Dict[str, Dict[str, Any]]:
    """
    Review multiple visual prompts in a single LLM call for efficiency

    Args:
        visual_prompts: List of tuples (prompt_id, visual_prompt_text)
        product_description: Product information for context
        brand_guidelines: Brand voice and visual style guidelines
        platform: Target platform (Meta, TikTok, etc.)

    Returns:
        Dictionary mapping prompt_id to review result:
        {
            "combo_1": {
                "reviewed_prompt": "...",
                "changed": bool,
                "notes": "..."
            },
            ...
        }
    """
    if not visual_prompts:
        return {}

    gemini = get_gemini()

    # Build prompts list for template
    prompts_list = []
    for prompt_id, prompt_text in visual_prompts:
        prompts_list.append(f"""
[PROMPT {prompt_id}]
{prompt_text}
""")

    prompts_list_str = "\n".join(prompts_list)

    # Build batch review prompt
    prompt = VISUAL_PROMPT_REVIEW_BATCH_TEMPLATE.format(
        num_prompts=len(visual_prompts),
        platform=platform,
        product_description=product_description if product_description else "Product information not provided",
        brand_guidelines=brand_guidelines if brand_guidelines else "No specific brand guidelines provided",
        prompts_list=prompts_list_str
    )

    # Execute batch review
    try:
        review_results = gemini.generate_json(
            prompt=prompt,
            system_instruction=VISUAL_PROMPT_REVIEW_SYSTEM_INSTRUCTION,
            temperature=0.3,  # Lower temperature for critical evaluation
            task_name="Visual Prompt Batch Review",
        )

        # Validate response structure
        if not isinstance(review_results, dict):
            raise ValueError(f"Expected dict response, got {type(review_results)}")

        if "reviews" not in review_results:
            raise ValueError(f"Response missing 'reviews' key. Keys found: {list(review_results.keys())}")

        reviews_list = review_results.get("reviews", [])
        if not isinstance(reviews_list, list):
            raise ValueError(f"Expected 'reviews' to be a list, got {type(reviews_list)}")

        # Convert list of reviews to dictionary keyed by prompt_id
        reviews_dict = {}
        for idx, review in enumerate(reviews_list):
            if not isinstance(review, dict):
                print(f"    ⚠ Review {idx} is not a dict, skipping")
                continue

            prompt_id = review.get("prompt_id")
            if prompt_id:
                reviews_dict[prompt_id] = {
                    "reviewed_prompt": review.get("reviewed_prompt", ""),
                    "changed": review.get("changed", False),
                    "notes": review.get("notes", "")
                }
            else:
                print(f"    ⚠ Review {idx} missing prompt_id, skipping")

        return reviews_dict

    except ValueError as e:
        # JSON parsing or validation error
        error_msg = str(e)
        print(f"    ⚠ Batch visual prompt review failed (JSON error): {error_msg[:200]}")
        return {}
    except Exception as e:
        # Other errors
        print(f"    ⚠ Batch visual prompt review failed (unexpected error): {str(e)[:200]}")
        return {}

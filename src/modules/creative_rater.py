"""
Creative Prompt Rating Module

LLM-based scoring of generated creative prompts against specific criteria.
"""

from typing import Dict, Any, List, Optional
from src.llm.gemini import call_gemini


def rate_creative_prompt(
    original_prompt: str,
    reviewed_prompt: str,
    product_description: str,
    required_keywords: Optional[List[str]] = None,
    brand_name: Optional[str] = None,
    original_requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Rate a creative prompt using LLM-based evaluation.

    Args:
        original_prompt: Initial generated visual prompt
        reviewed_prompt: Final reviewed/upgraded visual prompt
        product_description: Original product description for context
        required_keywords: List of keywords that should be present
        brand_name: Brand/logo name that should be mentioned
        original_requirements: Dict with platform, audience, creative_style, etc.

    Returns:
        Dict with:
        - overall_score: 0-100
        - category_scores: Dict of individual criterion scores
        - strengths: List of identified strengths
        - weaknesses: List of identified weaknesses
        - suggestions: List of improvement suggestions
        - keyword_analysis: Detailed keyword presence check
        - brand_presence: Analysis of brand/logo mention
        - prompt_adherence: How well it follows original requirements
    """

    # Build criteria checklist
    criteria = [
        "Keyword Presence - Required product/feature keywords are present",
        "Brand/Logo Visibility - Brand name and logo placement clearly described",
        "Prompt Adherence - Follows original requirements (platform, audience, style)",
        "Visual Clarity - Clear, specific visual description with concrete details",
        "Product Fidelity - Product accurately represented without stylization",
        "Professional Quality - Cinema-quality language and technical specifications",
        "Completeness - All required elements present (scene, subject, lighting, composition)",
        "Authenticity - Platform-appropriate voice and style"
    ]

    # Build rating prompt
    rating_prompt = f"""You are an expert creative director evaluating a visual prompt for advertising image generation.

PRODUCT DESCRIPTION:
{product_description}

ORIGINAL GENERATED PROMPT:
{original_prompt}

FINAL REVIEWED PROMPT:
{reviewed_prompt}

ORIGINAL REQUIREMENTS:
{_format_requirements(original_requirements) if original_requirements else "Not specified"}

REQUIRED KEYWORDS (if specified):
{', '.join(required_keywords) if required_keywords else "None specified"}

BRAND NAME (if specified):
{brand_name if brand_name else "None specified"}

EVALUATION CRITERIA:
{chr(10).join(f'{i+1}. {c}' for i, c in enumerate(criteria))}

YOUR TASK:
Evaluate the FINAL REVIEWED PROMPT against each criterion. Provide:

1. OVERALL SCORE (0-100): Holistic quality assessment
2. CATEGORY SCORES: Score each of the {len(criteria)} criteria (0-10)
3. KEYWORD ANALYSIS:
   - List each required keyword and whether it appears (explicitly or conceptually)
   - Note any missing critical keywords
4. BRAND PRESENCE:
   - Is the brand name mentioned?
   - Is logo placement/visibility described?
   - How prominent is the brand presence?
5. PROMPT ADHERENCE:
   - Does it match the platform requirements?
   - Does it target the specified audience?
   - Does it align with the creative style?
6. STRENGTHS: List 2-3 key strengths
7. WEAKNESSES: List 2-3 areas for improvement
8. SUGGESTIONS: Provide 2-3 specific actionable suggestions

Return your evaluation as a JSON object with this structure:
{{
    "overall_score": 85,
    "category_scores": {{
        "keyword_presence": 9,
        "brand_logo_visibility": 8,
        "prompt_adherence": 10,
        "visual_clarity": 9,
        "product_fidelity": 8,
        "professional_quality": 9,
        "completeness": 10,
        "authenticity": 9
    }},
    "keyword_analysis": {{
        "required_keywords_found": ["keyword1", "keyword2"],
        "required_keywords_missing": ["keyword3"],
        "conceptual_matches": {{"keyword4": "appears as 'alternative phrase'"}}
    }},
    "brand_presence": {{
        "brand_mentioned": true,
        "logo_described": true,
        "prominence_level": "high/medium/low",
        "details": "Specific notes about brand visibility"
    }},
    "prompt_adherence": {{
        "platform_match": true,
        "audience_match": true,
        "style_match": true,
        "details": "How well it matches requirements"
    }},
    "strengths": [
        "Strength 1",
        "Strength 2"
    ],
    "weaknesses": [
        "Weakness 1",
        "Weakness 2"
    ],
    "suggestions": [
        "Suggestion 1",
        "Suggestion 2"
    ]
}}

Be specific and reference actual content from the prompt in your analysis."""

    # Call LLM for rating
    response = call_gemini(
        rating_prompt,
        task_name="Creative Prompt Rating",
        temperature=0.3,  # Analytical evaluation
        json_response=True
    )

    # Parse and validate response
    try:
        import json
        rating_result = json.loads(response) if isinstance(response, str) else response

        # Ensure all required fields are present
        required_fields = [
            "overall_score", "category_scores", "keyword_analysis",
            "brand_presence", "prompt_adherence", "strengths",
            "weaknesses", "suggestions"
        ]

        for field in required_fields:
            if field not in rating_result:
                rating_result[field] = _get_default_field_value(field)

        # Add metadata
        rating_result["metadata"] = {
            "original_prompt_length": len(original_prompt),
            "reviewed_prompt_length": len(reviewed_prompt),
            "prompt_changed": original_prompt != reviewed_prompt,
            "product_description": product_description[:200] + "..." if len(product_description) > 200 else product_description
        }

        return rating_result

    except (json.JSONDecodeError, TypeError) as e:
        # Fallback if JSON parsing fails
        return {
            "overall_score": 0,
            "category_scores": {},
            "keyword_analysis": {"error": f"Failed to parse rating: {str(e)}"},
            "brand_presence": {},
            "prompt_adherence": {},
            "strengths": [],
            "weaknesses": ["Rating failed to generate properly"],
            "suggestions": ["Re-run rating with adjusted parameters"],
            "metadata": {
                "error": str(e),
                "raw_response": str(response)[:500]
            }
        }


def rate_creative_prompts_batch(
    creative_results: List[Dict[str, Any]],
    product_description: str,
    required_keywords: Optional[List[str]] = None,
    brand_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rate multiple creative prompts in batch.

    Args:
        creative_results: List of dicts with original_prompt, reviewed_prompt, requirements
        product_description: Original product description
        required_keywords: List of required keywords
        brand_name: Brand name to check for

    Returns:
        Dict with:
        - individual_ratings: List of rating dicts for each creative
        - aggregate_stats: Overall statistics across all creatives
        - best_performer: Highest-scoring creative
        - worst_performer: Lowest-scoring creative
    """

    individual_ratings = []

    for i, creative in enumerate(creative_results):
        rating = rate_creative_prompt(
            original_prompt=creative.get("original_prompt", ""),
            reviewed_prompt=creative.get("reviewed_prompt", ""),
            product_description=product_description,
            required_keywords=required_keywords,
            brand_name=brand_name,
            original_requirements=creative.get("requirements", {})
        )

        # Add creative ID for reference
        rating["creative_id"] = creative.get("combo_id", f"creative_{i+1}")
        rating["platform"] = creative.get("requirements", {}).get("platform", "unknown")

        individual_ratings.append(rating)

    # Calculate aggregate statistics
    if individual_ratings:
        overall_scores = [r["overall_score"] for r in individual_ratings]

        aggregate_stats = {
            "total_creatives": len(individual_ratings),
            "average_score": sum(overall_scores) / len(overall_scores),
            "median_score": sorted(overall_scores)[len(overall_scores) // 2],
            "min_score": min(overall_scores),
            "max_score": max(overall_scores),
            "score_distribution": {
                "excellent (90-100)": sum(1 for s in overall_scores if s >= 90),
                "good (70-89)": sum(1 for s in overall_scores if 70 <= s < 90),
                "fair (50-69)": sum(1 for s in overall_scores if 50 <= s < 70),
                "poor (<50)": sum(1 for s in overall_scores if s < 50)
            }
        }

        # Find best and worst performers
        best_idx = overall_scores.index(max(overall_scores))
        worst_idx = overall_scores.index(min(overall_scores))

        best_performer = {
            "creative_id": individual_ratings[best_idx]["creative_id"],
            "platform": individual_ratings[best_idx]["platform"],
            "score": individual_ratings[best_idx]["overall_score"],
            "strengths": individual_ratings[best_idx]["strengths"]
        }

        worst_performer = {
            "creative_id": individual_ratings[worst_idx]["creative_id"],
            "platform": individual_ratings[worst_idx]["platform"],
            "score": individual_ratings[worst_idx]["overall_score"],
            "weaknesses": individual_ratings[worst_idx]["weaknesses"]
        }
    else:
        aggregate_stats = {}
        best_performer = None
        worst_performer = None

    return {
        "individual_ratings": individual_ratings,
        "aggregate_stats": aggregate_stats,
        "best_performer": best_performer,
        "worst_performer": worst_performer
    }


def _format_requirements(requirements: Dict[str, Any]) -> str:
    """Format requirements dict as readable string."""
    if not requirements:
        return "None specified"

    parts = []
    if "platform" in requirements:
        parts.append(f"Platform: {requirements['platform']}")
    if "audience" in requirements:
        parts.append(f"Audience: {requirements['audience']}")
    if "creative_style" in requirements:
        parts.append(f"Style: {requirements['creative_style']}")
    if "aspect_ratio" in requirements:
        parts.append(f"Aspect Ratio: {requirements['aspect_ratio']}")

    return ", ".join(parts) if parts else "General requirements"


def _get_default_field_value(field_name: str) -> Any:
    """Get default value for missing field."""
    defaults = {
        "overall_score": 0,
        "category_scores": {},
        "keyword_analysis": {"error": "Not generated"},
        "brand_presence": {"error": "Not generated"},
        "prompt_adherence": {"error": "Not generated"},
        "strengths": [],
        "weaknesses": ["Rating incomplete"],
        "suggestions": []
    }
    return defaults.get(field_name, {})

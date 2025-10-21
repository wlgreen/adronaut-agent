"""
Test Creative Workflow

Standalone workflow for testing creative generation with the following steps:
1. Generate initial creative prompt from LLM
2. Review and upgrade the prompt
3. Output final creative (visual prompt)
4. Rate the creative against criteria
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import base64

from src.modules.creative_generator import (
    generate_creative_prompts,
    review_and_upgrade_visual_prompt,
    validate_creative_prompt
)
from src.modules.creative_rater import rate_creative_prompt
from src.utils.progress import ProgressTracker


def run_test_creative_workflow(
    product_description: str,
    product_image_path: Optional[str] = None,
    platform: str = "Meta",
    audience: Optional[str] = None,
    creative_style: Optional[str] = None,
    required_keywords: Optional[List[str]] = None,
    brand_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete test creative workflow.

    Args:
        product_description: Description of the product/service
        product_image_path: Path to product image (optional, for visual context)
        platform: Target platform (Meta/TikTok/Google)
        audience: Target audience description
        creative_style: Creative style preference
        required_keywords: Keywords that must be present in prompt
        brand_name: Brand name to check for presence

    Returns:
        Dict with complete workflow results:
        - step1_generation: Initial prompt generation results
        - step2_review: Prompt review and upgrade results
        - step3_creative: Final creative output
        - step4_rating: Prompt rating results
        - metadata: Workflow metadata
    """

    tracker = ProgressTracker()

    # Prepare workflow metadata
    metadata = {
        "product_description": product_description,
        "product_image": product_image_path,
        "platform": platform,
        "audience": audience,
        "creative_style": creative_style
    }

    # Set defaults for audience and style if not provided
    if not audience:
        audience = "General audience"
    if not creative_style:
        creative_style = "Professional"

    # Prepare user inputs
    user_inputs = {
        "product_description": product_description
    }

    # Handle product image if provided
    if product_image_path:
        image_path = Path(product_image_path)
        if image_path.exists():
            tracker.log_message(f"Product image loaded: {image_path.name}")
            # Read image and encode as base64 for potential LLM vision analysis
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                user_inputs["product_image_base64"] = image_data
                user_inputs["product_image_path"] = str(image_path)
        else:
            tracker.log_message(f"Warning: Product image not found at {product_image_path}", level="warning")

    # ============================================
    # STEP 1: Generate Initial Creative Prompt
    # ============================================
    tracker.log_message("STEP 1: Generating initial creative prompt...", level="info")

    # Build test combination structure expected by generate_creative_prompts
    test_combination = {
        "combo_id": "test_combo_1",
        "platform": platform,
        "audience": audience,
        "creative_style": creative_style
    }

    try:
        # Generate creative prompts (returns dict with visual_prompt, copy, hooks, etc.)
        # Note: We pass empty strategy dict since this is standalone testing
        generation_result = generate_creative_prompts(
            test_combination=test_combination,
            strategy={},
            user_inputs=user_inputs
        )

        step1_result = {
            "success": True,
            "original_prompt": generation_result.get("visual_prompt", ""),
            "copy_primary_text": generation_result.get("copy_primary_text", ""),
            "copy_headline": generation_result.get("copy_headline", ""),
            "copy_cta": generation_result.get("copy_cta", ""),
            "hooks": generation_result.get("hooks", []),
            "technical_specs": generation_result.get("technical_specs", {}),
            "full_generation": generation_result
        }

        tracker.log_message(f"✓ Initial prompt generated ({len(step1_result['original_prompt'])} chars)")

    except Exception as e:
        tracker.log_message(f"✗ Failed to generate prompt: {str(e)}", level="error")
        return {
            "success": False,
            "error": f"Step 1 failed: {str(e)}",
            "metadata": metadata
        }

    # ============================================
    # STEP 2: Review and Upgrade Prompt
    # ============================================
    tracker.log_message("STEP 2: Reviewing and upgrading prompt...", level="info")

    try:
        # Review the visual prompt
        review_result = review_and_upgrade_visual_prompt(
            visual_prompt=step1_result["original_prompt"],
            product_description=product_description,
            brand_guidelines="",  # Empty for test workflow - can be added via CLI if needed
            platform=platform
        )

        step2_result = {
            "success": True,
            "reviewed_prompt": review_result.get("reviewed_prompt", step1_result["original_prompt"]),
            "changed": review_result.get("changed", False),
            "review_notes": review_result.get("notes", ""),
            "full_review": review_result
        }

        if step2_result["changed"]:
            tracker.log_message(f"✓ Prompt upgraded ({len(step2_result['reviewed_prompt'])} chars, review notes: {step2_result['review_notes'][:100]}...)")
        else:
            tracker.log_message("✓ Prompt passed review (no changes needed)")

    except Exception as e:
        tracker.log_message(f"✗ Review failed: {str(e)}, using original prompt", level="warning")
        step2_result = {
            "success": False,
            "reviewed_prompt": step1_result["original_prompt"],
            "changed": False,
            "review_notes": f"Review failed: {str(e)}",
            "error": str(e)
        }

    # ============================================
    # STEP 3: Final Creative Output
    # ============================================
    tracker.log_message("STEP 3: Preparing final creative output...", level="info")

    # The reviewed prompt IS the creative for image generation
    step3_result = {
        "success": True,
        "final_visual_prompt": step2_result["reviewed_prompt"],
        "copy_primary_text": step1_result["copy_primary_text"],
        "copy_headline": step1_result["copy_headline"],
        "copy_cta": step1_result["copy_cta"],
        "hooks": step1_result["hooks"],
        "technical_specs": step1_result["technical_specs"],
        "ready_for_image_generation": True
    }

    # Validate the final creative
    is_valid, validation_errors = validate_creative_prompt(step3_result, platform)
    step3_result["validation"] = {
        "is_valid": is_valid,
        "errors": validation_errors
    }

    if is_valid:
        tracker.log_message("✓ Final creative validated and ready for image generation")
    else:
        tracker.log_message(f"⚠ Validation warnings: {', '.join(validation_errors)}", level="warning")

    # ============================================
    # STEP 4: Rate the Creative Prompt
    # ============================================
    tracker.log_message("STEP 4: Rating creative prompt quality...", level="info")

    try:
        # Build requirements dict for rating context
        requirements = {
            "platform": platform,
            "audience": audience,
            "creative_style": creative_style,
            "aspect_ratio": step1_result["technical_specs"].get("aspect_ratio")
        }

        rating_result = rate_creative_prompt(
            original_prompt=step1_result["original_prompt"],
            reviewed_prompt=step2_result["reviewed_prompt"],
            product_description=product_description,
            required_keywords=required_keywords,
            brand_name=brand_name,
            original_requirements=requirements
        )

        step4_result = {
            "success": True,
            "overall_score": rating_result.get("overall_score", 0),
            "category_scores": rating_result.get("category_scores", {}),
            "keyword_analysis": rating_result.get("keyword_analysis", {}),
            "brand_presence": rating_result.get("brand_presence", {}),
            "prompt_adherence": rating_result.get("prompt_adherence", {}),
            "strengths": rating_result.get("strengths", []),
            "weaknesses": rating_result.get("weaknesses", []),
            "suggestions": rating_result.get("suggestions", []),
            "full_rating": rating_result
        }

        tracker.log_message(f"✓ Rating complete: {step4_result['overall_score']}/100")

    except Exception as e:
        tracker.log_message(f"✗ Rating failed: {str(e)}", level="error")
        step4_result = {
            "success": False,
            "error": str(e),
            "overall_score": 0
        }

    # ============================================
    # STEP 5: Generate Image from Prompt
    # ============================================
    tracker.log_message("STEP 5: Generating image from visual prompt...", level="info")

    try:
        from src.llm.gemini import get_gemini
        gemini = get_gemini()

        # Get aspect ratio from technical specs
        aspect_ratio = step3_result["technical_specs"].get("aspect_ratio", "1:1")

        image_result = gemini.generate_image(
            prompt=step3_result["final_visual_prompt"],
            aspect_ratio=aspect_ratio,
            task_name="Creative Image Generation"
        )

        step5_result = {
            "success": image_result["success"],
            "image_path": image_result.get("image_path"),
            "model": image_result.get("model"),
            "aspect_ratio": aspect_ratio,
            "error": image_result.get("error")
        }

        if step5_result["success"]:
            tracker.log_message(f"✓ Image generated: {step5_result['image_path']}")
        else:
            tracker.log_message(f"✗ Image generation failed: {step5_result['error']}", level="error")

    except Exception as e:
        tracker.log_message(f"✗ Image generation failed: {str(e)}", level="error")
        step5_result = {
            "success": False,
            "image_path": None,
            "error": str(e)
        }

    # ============================================
    # STEP 6: Review/Rate Generated Image
    # ============================================
    tracker.log_message("STEP 6: Reviewing and rating generated image...", level="info")

    step6_result = {}

    if step5_result["success"] and step5_result["image_path"]:
        try:
            from src.modules.creative_rater import rate_generated_image

            image_rating = rate_generated_image(
                image_path=step5_result["image_path"],
                original_prompt=step3_result["final_visual_prompt"],
                product_description=product_description,
                platform=platform,
                required_keywords=required_keywords,
                brand_name=brand_name
            )

            step6_result = {
                "success": True,
                "overall_score": image_rating.get("overall_score", 0),
                "category_scores": image_rating.get("category_scores", {}),
                "prompt_match_details": image_rating.get("prompt_match_details", {}),
                "strengths": image_rating.get("strengths", []),
                "weaknesses": image_rating.get("weaknesses", []),
                "suggestions": image_rating.get("suggestions", []),
                "full_rating": image_rating
            }

            tracker.log_message(f"✓ Image rating complete: {step6_result['overall_score']}/100")

        except Exception as e:
            tracker.log_message(f"✗ Image rating failed: {str(e)}", level="error")
            step6_result = {
                "success": False,
                "error": str(e),
                "overall_score": 0
            }
    else:
        tracker.log_message("⚠ Skipping image review (no image generated)", level="warning")
        step6_result = {
            "success": False,
            "skipped": True,
            "reason": "No image generated"
        }

    # ============================================
    # Compile Final Results
    # ============================================
    tracker.log_message("Workflow complete!", level="success")

    final_result = {
        "success": True,
        "workflow_steps": {
            "step1_generation": step1_result,
            "step2_review": step2_result,
            "step3_creative": step3_result,
            "step4_rating": step4_result,
            "step5_image_generation": step5_result,
            "step6_image_rating": step6_result
        },
        "summary": {
            "platform": platform,
            "audience": audience,
            "creative_style": creative_style,
            "prompt_changed_in_review": step2_result["changed"],
            "final_score": step4_result.get("overall_score", 0),
            "validation_passed": step3_result["validation"]["is_valid"],
            "image_generated": step5_result.get("success", False),
            "image_path": step5_result.get("image_path"),
            "image_score": step6_result.get("overall_score", 0)
        },
        "metadata": metadata
    }

    return final_result


def save_test_creative_results(
    results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save test creative results to JSON file.

    Args:
        results: Workflow results from run_test_creative_workflow
        output_path: Custom output path (optional)

    Returns:
        Path to saved file
    """

    # Determine output path
    if not output_path:
        output_dir = Path("output/test_creatives")
        output_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_creative_{timestamp}.json"

        output_path = output_dir / filename

    # Save to file
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    return str(output_path)

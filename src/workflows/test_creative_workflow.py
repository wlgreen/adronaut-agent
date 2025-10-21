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
    context: Optional[Dict[str, Any]] = None,
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
        context: Additional context (strategy, insights, market data from main workflow)
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
        "creative_style": creative_style,
        "has_context": context is not None and len(context) > 0
    }

    # Extract context components
    strategy = context.get("strategy", {}) if context else {}
    user_inputs = context.get("user_inputs", {}) if context else {}

    # If no audience/style specified, try to extract from context
    if not audience and strategy:
        audience = strategy.get("target_audience", "General audience")
    if not creative_style and strategy:
        creative_style = strategy.get("messaging_angles", ["Professional"])[0] if strategy.get("messaging_angles") else "Professional"

    # Add product description to user inputs
    if not user_inputs:
        user_inputs = {}
    user_inputs["product_description"] = product_description

    # Handle product image if provided
    if product_image_path:
        image_path = Path(product_image_path)
        if image_path.exists():
            tracker.log_progress(f"Product image loaded: {image_path.name}")
            # Read image and encode as base64 for potential LLM vision analysis
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                user_inputs["product_image_base64"] = image_data
                user_inputs["product_image_path"] = str(image_path)
        else:
            tracker.log_progress(f"Warning: Product image not found at {product_image_path}", level="warning")

    # ============================================
    # STEP 1: Generate Initial Creative Prompt
    # ============================================
    tracker.log_progress("STEP 1: Generating initial creative prompt...", level="info")

    # Build test combination structure expected by generate_creative_prompts
    test_combination = {
        "combo_id": "test_combo_1",
        "platform": platform,
        "audience": audience or "General audience",
        "creative_style": creative_style or "Professional"
    }

    try:
        # Generate creative prompts (returns dict with visual_prompt, copy, hooks, etc.)
        generation_result = generate_creative_prompts(
            test_combination=test_combination,
            strategy=strategy,
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

        tracker.log_progress(f"✓ Initial prompt generated ({len(step1_result['original_prompt'])} chars)")

    except Exception as e:
        tracker.log_progress(f"✗ Failed to generate prompt: {str(e)}", level="error")
        return {
            "success": False,
            "error": f"Step 1 failed: {str(e)}",
            "metadata": metadata
        }

    # ============================================
    # STEP 2: Review and Upgrade Prompt
    # ============================================
    tracker.log_progress("STEP 2: Reviewing and upgrading prompt...", level="info")

    try:
        # Review the visual prompt
        review_result = review_and_upgrade_visual_prompt(
            visual_prompt=step1_result["original_prompt"],
            combo_id="test_combo_1",
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
            tracker.log_progress(f"✓ Prompt upgraded ({len(step2_result['reviewed_prompt'])} chars, review notes: {step2_result['review_notes'][:100]}...)")
        else:
            tracker.log_progress("✓ Prompt passed review (no changes needed)")

    except Exception as e:
        tracker.log_progress(f"✗ Review failed: {str(e)}, using original prompt", level="warning")
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
    tracker.log_progress("STEP 3: Preparing final creative output...", level="info")

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
        tracker.log_progress("✓ Final creative validated and ready for image generation")
    else:
        tracker.log_progress(f"⚠ Validation warnings: {', '.join(validation_errors)}", level="warning")

    # ============================================
    # STEP 4: Rate the Creative Prompt
    # ============================================
    tracker.log_progress("STEP 4: Rating creative prompt quality...", level="info")

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

        tracker.log_progress(f"✓ Rating complete: {step4_result['overall_score']}/100")

    except Exception as e:
        tracker.log_progress(f"✗ Rating failed: {str(e)}", level="error")
        step4_result = {
            "success": False,
            "error": str(e),
            "overall_score": 0
        }

    # ============================================
    # Compile Final Results
    # ============================================
    tracker.log_progress("Workflow complete!", level="success")

    final_result = {
        "success": True,
        "workflow_steps": {
            "step1_generation": step1_result,
            "step2_review": step2_result,
            "step3_creative": step3_result,
            "step4_rating": step4_result
        },
        "summary": {
            "platform": platform,
            "audience": audience,
            "creative_style": creative_style,
            "prompt_changed_in_review": step2_result["changed"],
            "final_score": step4_result.get("overall_score", 0),
            "validation_passed": step3_result["validation"]["is_valid"]
        },
        "metadata": metadata
    }

    return final_result


def save_test_creative_results(
    results: Dict[str, Any],
    product_description: str,
    output_path: Optional[str] = None,
    project_id: Optional[str] = None,
    product_image_path: Optional[str] = None,
    required_keywords: Optional[List[str]] = None,
    brand_name: Optional[str] = None,
    save_to_db: bool = True
) -> Dict[str, str]:
    """
    Save test creative results to JSON file and optionally to database.

    Args:
        results: Workflow results from run_test_creative_workflow
        product_description: Product description used
        output_path: Custom output path (optional)
        project_id: Project ID for naming (optional)
        product_image_path: Path to product image (optional)
        required_keywords: Keywords that were checked for
        brand_name: Brand name that was checked for
        save_to_db: Whether to save to database (default: True)

    Returns:
        Dict with file_path and test_id (if saved to DB)
    """

    # Determine output path
    if not output_path:
        output_dir = Path("output/test_creatives")
        output_dir.mkdir(parents=True, exist_ok=True)

        if project_id:
            filename = f"test_creative_{project_id}.json"
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_creative_{timestamp}.json"

        output_path = output_dir / filename

    # Save to file
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    result = {"file_path": str(output_path)}

    # Save to database if requested
    if save_to_db:
        try:
            from src.database.persistence import TestCreativePersistence

            test_id = TestCreativePersistence.save_test_creative(
                workflow_result=results,
                product_description=product_description,
                product_image_path=product_image_path,
                project_id=project_id,
                required_keywords=required_keywords,
                brand_name=brand_name
            )

            result["test_id"] = test_id

        except Exception as e:
            print(f"Warning: Failed to save to database: {str(e)}")
            result["db_error"] = str(e)

    return result


def load_context_from_project(project_id: str) -> Dict[str, Any]:
    """
    Load context from an existing project for use in test workflow.

    Args:
        project_id: Project ID to load

    Returns:
        Dict with strategy, insights, market_data, etc.
    """

    from src.database.persistence import ProjectPersistence

    try:
        project_data = ProjectPersistence.load_project(project_id)

        if not project_data:
            return {}

        # Extract relevant context
        context = {
            "strategy": project_data.get("current_strategy", {}),
            "insights": project_data.get("insights", {}),
            "market_data": project_data.get("market_data", {}),
            "historical_data": project_data.get("historical_data", {}),
            "user_inputs": project_data.get("user_inputs", {}),
            "current_phase": project_data.get("current_phase", ""),
            "iteration": project_data.get("iteration", 0)
        }

        return context

    except Exception as e:
        print(f"Warning: Failed to load context from project {project_id}: {str(e)}")
        return {}

"""
Gemini API wrapper for LLM interactions
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import progress tracker (avoid circular import by lazy importing)
def _get_progress_tracker():
    """Lazy import to avoid circular dependency"""
    try:
        from ..utils.progress import get_progress_tracker
        return get_progress_tracker()
    except ImportError:
        return None


class GeminiClient:
    """Wrapper for Gemini API with structured output support"""

    def __init__(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing Gemini API key. "
                "Please set GEMINI_API_KEY in .env file"
            )

        genai.configure(api_key=api_key)

        # Use Gemini 2.0 Flash by default, can be overridden
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.model = genai.GenerativeModel(self.model_name)

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        task_name: str = "JSON Generation",
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response

        Args:
            prompt: User prompt
            system_instruction: System instruction for context
            temperature: Sampling temperature (0-1)
            task_name: Name of the task for logging

        Returns:
            Parsed JSON response
        """
        # Get progress tracker
        tracker = _get_progress_tracker()

        # Construct full prompt with JSON instruction
        full_prompt = f"{prompt}\n\nRespond with valid JSON only. Do not include any markdown formatting or code blocks."

        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{full_prompt}"

        # Log LLM call start
        if tracker:
            prompt_preview = full_prompt.replace('\n', ' ')[:200]
            tracker.llm_call_start(task_name, prompt_preview)

        # Track timing
        start_time = time.time()

        # Generate response
        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                candidate_count=1,
            ),
        )

        # Calculate duration
        duration = time.time() - start_time

        # Parse JSON from response
        text = response.text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        if text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove trailing ```

        text = text.strip()

        # Log LLM call end
        if tracker:
            response_preview = text.replace('\n', ' ')[:200]
            tracker.llm_call_end(task_name, duration, response_preview)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            if tracker:
                tracker.log_message(f"JSON parse error: {str(e)}", "error")
                # Show more context: first 500 chars and position of error
                error_pos = getattr(e, 'pos', 0)
                context_start = max(0, error_pos - 100)
                context_end = min(len(text), error_pos + 100)
                context = text[context_start:context_end]
                tracker.log_message(f"Error context: ...{context}...", "error")
            raise ValueError(f"Failed to parse JSON response: {e}\n\nResponse preview: {text[:500]}...")

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        task_name: str = "Text Generation",
    ) -> str:
        """
        Generate text response

        Args:
            prompt: User prompt
            system_instruction: System instruction for context
            temperature: Sampling temperature (0-1)
            task_name: Name of the task for logging

        Returns:
            Generated text
        """
        # Get progress tracker
        tracker = _get_progress_tracker()

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{full_prompt}"

        # Log LLM call start
        if tracker:
            prompt_preview = full_prompt.replace('\n', ' ')[:200]
            tracker.llm_call_start(task_name, prompt_preview)

        # Track timing
        start_time = time.time()

        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                candidate_count=1,
            ),
        )

        # Calculate duration
        duration = time.time() - start_time
        text = response.text.strip()

        # Log LLM call end
        if tracker:
            response_preview = text.replace('\n', ' ')[:200]
            tracker.llm_call_end(task_name, duration, response_preview)

        return text

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """
        Chat with conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
                     roles: 'user' or 'model'
            temperature: Sampling temperature (0-1)

        Returns:
            Generated response text
        """
        chat = self.model.start_chat(history=[])

        # Add history
        for msg in messages[:-1]:
            if msg["role"] == "user":
                chat.send_message(msg["content"])

        # Send final message and get response
        final_message = messages[-1]["content"]
        response = chat.send_message(
            final_message,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                candidate_count=1,
            ),
        )

        return response.text.strip()

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        task_name: str = "Image Generation"
    ) -> Dict[str, Any]:
        """
        Generate image using Gemini 2.5 Flash Image

        Args:
            prompt: Visual prompt for image generation
            aspect_ratio: "1:1", "16:9", "9:16", "4:5"
            task_name: Task name for logging

        Returns:
            {
                "success": True,
                "image_data": base64_string,
                "image_path": "output/test_creatives/images/test_creative_<timestamp>.png",
                "model": "gemini-2.5-flash-image",
                "error": None
            }
        """
        from pathlib import Path
        from datetime import datetime
        import base64

        tracker = _get_progress_tracker()

        # Map aspect ratios to dimensions
        dimensions_map = {
            "1:1": "1024x1024",
            "16:9": "1792x1024",
            "9:16": "1024x1792",
            "4:5": "1024x1280"
        }

        try:
            if tracker:
                tracker.log_message(f"🎨 Generating image with {aspect_ratio} aspect ratio...", "info")

            # Use gemini-2.5-flash-image model
            image_model = genai.GenerativeModel("gemini-2.5-flash-image")

            # Generate image
            response = image_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    candidate_count=1,
                )
            )

            # Extract image data (response will contain image bytes)
            image_data = response.candidates[0].content.parts[0].inline_data.data

            # Save to file
            output_dir = Path("output/test_creatives/images")
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = output_dir / f"test_creative_{timestamp}.png"

            # Decode and save
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))

            if tracker:
                tracker.log_message(f"✓ Image saved: {image_path}", "success")

            return {
                "success": True,
                "image_data": image_data,
                "image_path": str(image_path),
                "model": "gemini-2.5-flash-image",
                "error": None
            }

        except Exception as e:
            if tracker:
                tracker.log_message(f"✗ Image generation failed: {str(e)}", "error")

            return {
                "success": False,
                "image_data": None,
                "image_path": None,
                "model": "gemini-2.5-flash-image",
                "error": str(e)
            }

    def review_image(
        self,
        image_path: str,
        original_prompt: str,
        criteria: Dict[str, Any],
        task_name: str = "Image Review"
    ) -> Dict[str, Any]:
        """
        Review generated image using Gemini Vision

        Args:
            image_path: Path to generated image
            original_prompt: Original text prompt used for generation
            criteria: Review criteria dict with platform, product_description, etc.
            task_name: Task name for logging

        Returns:
            {
                "overall_score": 85,
                "category_scores": {
                    "visual_quality": 9,
                    "prompt_adherence": 8,
                    "product_visibility": 9,
                    "brand_presence": 7,
                    "platform_fit": 8,
                    "technical_quality": 9
                },
                "strengths": [...],
                "weaknesses": [...],
                "suggestions": [...]
            }
        """
        import PIL.Image

        tracker = _get_progress_tracker()

        if tracker:
            tracker.log_message(f"🔍 Reviewing generated image...", "info")

        try:
            # Read image
            image = PIL.Image.open(image_path)

            # Build review prompt
            review_prompt = f"""You are an expert creative director reviewing an AI-generated advertising image.

ORIGINAL TEXT PROMPT:
{original_prompt}

EVALUATION CRITERIA (rate each 0-10):
1. Visual Quality - Composition, lighting, color, professionalism
2. Prompt Adherence - How well does image match the text prompt?
3. Product Visibility - Is product clearly shown (~1/3 of frame)?
4. Brand Presence - Logo/brand visible and prominent as described?
5. Platform Fit - Appropriate for {criteria.get('platform', 'social media')} ads?
6. Technical Quality - Resolution, clarity, no artifacts or distortions

YOUR TASK:
Analyze the image and provide:
1. OVERALL SCORE (0-100): Holistic quality for advertising use
2. CATEGORY SCORES: Rate each of 6 criteria (0-10)
3. STRENGTHS: List 2-3 key strengths
4. WEAKNESSES: List 2-3 areas for improvement
5. SUGGESTIONS: Provide 2-3 specific suggestions to improve

Return as JSON:
{{
    "overall_score": 85,
    "category_scores": {{
        "visual_quality": 9,
        "prompt_adherence": 8,
        "product_visibility": 9,
        "brand_presence": 7,
        "platform_fit": 8,
        "technical_quality": 9
    }},
    "prompt_match_details": {{
        "matched_elements": ["element1", "element2"],
        "missing_elements": ["element3"],
        "extra_elements": ["unexpected1"]
    }},
    "strengths": ["Strength 1", "Strength 2"],
    "weaknesses": ["Weakness 1", "Weakness 2"],
    "suggestions": ["Suggestion 1", "Suggestion 2"]
}}"""

            # Use vision model (current Gemini model for vision)
            vision_model = genai.GenerativeModel("gemini-2.0-flash-exp")

            response = vision_model.generate_content(
                [review_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    candidate_count=1,
                )
            )

            # Parse JSON response
            result_text = response.text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()
            result = json.loads(result_text)

            if tracker:
                tracker.log_message(f"✓ Image review complete: {result.get('overall_score', 0)}/100", "success")

            return result

        except Exception as e:
            if tracker:
                tracker.log_message(f"✗ Image review failed: {str(e)}", "error")

            return {
                "overall_score": 0,
                "category_scores": {},
                "prompt_match_details": {},
                "strengths": [],
                "weaknesses": [f"Review failed: {str(e)}"],
                "suggestions": [],
                "error": str(e)
            }


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini() -> GeminiClient:
    """
    Get or create Gemini client singleton

    Returns:
        GeminiClient instance
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client

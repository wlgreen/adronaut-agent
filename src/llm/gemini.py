"""
Gemini API wrapper for LLM interactions
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from dotenv import load_dotenv
from ..utils.retry import retry, is_retryable_error

# Load environment variables
load_dotenv()


class LLMError(Exception):
    """Raised when LLM API call fails"""
    pass


class LLMTimeoutError(Exception):
    """Raised when LLM API call times out"""
    pass

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

    @retry(max_attempts=3, exceptions=(Exception,), base_delay=2.0)
    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        task_name: str = "JSON Generation",
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response with retry logic and timeout

        Args:
            prompt: User prompt
            system_instruction: System instruction for context
            temperature: Sampling temperature (0-1)
            task_name: Name of the task for logging
            timeout: Request timeout in seconds (default: 120s)

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If LLM API call fails after retries
            LLMTimeoutError: If request times out
        """
        # Get progress tracker
        tracker = _get_progress_tracker()

        try:
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

            # Generate response with timeout
            try:
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        candidate_count=1,
                    ),
                    request_options={'timeout': timeout}
                )
            except TimeoutError as e:
                raise LLMTimeoutError(f"LLM request timed out after {timeout}s") from e

            # Calculate duration
            duration = time.time() - start_time

            # Check if request exceeded timeout
            if duration > timeout:
                raise LLMTimeoutError(f"LLM request took {duration:.1f}s, exceeding timeout of {timeout}s")

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
                raise LLMError(f"Failed to parse JSON response: {e}\n\nResponse preview: {text[:500]}...") from e

        except (LLMTimeoutError, LLMError) as e:
            # Don't retry timeout or parse errors
            raise
        except Exception as e:
            # Check if error is retryable
            if is_retryable_error(e):
                if tracker:
                    tracker.log_message(f"Retryable LLM error: {str(e)}", "warning")
                raise  # Will be retried by decorator
            else:
                raise LLMError(f"LLM API call failed: {str(e)}") from e

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

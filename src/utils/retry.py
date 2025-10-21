"""
Retry utility with exponential backoff for handling transient failures
"""

import time
import functools
from typing import Callable, Type, Tuple, Optional
from ..utils.progress import get_progress_tracker


class RetryError(Exception):
    """Raised when all retry attempts have been exhausted"""
    pass


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0) -> float:
    """
    Calculate exponential backoff delay

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    return delay


def retry(
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_attempts: Maximum number of attempts (including first try)
        exceptions: Tuple of exception types to catch and retry
        base_delay: Initial delay in seconds between retries
        max_delay: Maximum delay in seconds
        on_retry: Optional callback function called on each retry

    Example:
        @retry(max_attempts=3, exceptions=(NetworkError, TimeoutError))
        def fetch_data():
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracker = get_progress_tracker()
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # If this was the last attempt, raise
                    if attempt == max_attempts - 1:
                        if tracker:
                            tracker.log_message(
                                f"❌ {func.__name__} failed after {max_attempts} attempts: {str(e)}",
                                "error"
                            )
                        raise RetryError(
                            f"{func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {str(e)}"
                        ) from e

                    # Calculate delay and wait
                    delay = exponential_backoff(attempt, base_delay, max_delay)

                    if tracker:
                        tracker.log_message(
                            f"⚠ {func.__name__} attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {delay:.1f}s...",
                            "warning"
                        )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)

                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is likely transient and retryable

    Args:
        error: Exception to check

    Returns:
        True if error is likely transient
    """
    error_str = str(error).lower()

    # Network/connection errors
    transient_indicators = [
        "timeout",
        "connection",
        "network",
        "temporary",
        "503",  # Service unavailable
        "502",  # Bad gateway
        "504",  # Gateway timeout
        "429",  # Rate limit (should retry with backoff)
        "socket",
        "dns",
        "ssl",
        "certificate",
    ]

    return any(indicator in error_str for indicator in transient_indicators)

"""
Utility functions for error handling, logging, and retry logic.
"""

import time
import random
import logging
import json
from typing import Callable, Any, Optional
from functools import wraps


def fetch_with_backoff(
    request_fn: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: tuple = (ConnectionError, TimeoutError)
) -> Any:
    """
    Execute a request function with exponential backoff and jitter.

    Args:
        request_fn: Function to execute (should raise exception on transient failures)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter: Whether to add random jitter to delays
        exceptions: Tuple of exception types to retry on

    Returns:
        Result from request_fn

    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return request_fn()

        except exceptions as e:
            last_exception = e

            if attempt == max_retries - 1:
                # Last attempt, re-raise
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)

            # Add jitter (random factor between 0.5 and 1.5)
            if jitter:
                delay *= (0.5 + random.random())

            print(f"[Retry] Attempt {attempt + 1}/{max_retries} failed: {e}")
            print(f"[Retry] Waiting {delay:.2f}s before retry...")
            time.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function on failure with exponential backoff.

    Usage:
        @retry_on_failure(max_retries=3, base_delay=2.0)
        def my_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return fetch_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                exceptions=exceptions
            )
        return wrapper
    return decorator


class StructuredLogger:
    """Structured JSON logger for consistent logging across the application."""

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__)
            level: Logging level (default INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Create console handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setLevel(level)

        # Set formatter (will be JSON in production)
        if logging.root.level == logging.DEBUG:
            # Human-readable format for development
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            # JSON format for production
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "logger": "%(name)s", '
                '"level": "%(levelname)s", "message": "%(message)s"}'
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message: str, **kwargs):
        """Log info message with optional extra fields."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.info(message)

    def error(self, message: str, **kwargs):
        """Log error message with optional extra fields."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.error(message)

    def warning(self, message: str, **kwargs):
        """Log warning message with optional extra fields."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.warning(message)

    def debug(self, message: str, **kwargs):
        """Log debug message with optional extra fields."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.debug(message)


def log_api_request(
    logger: StructuredLogger,
    provider: str,
    endpoint: str,
    params: dict,
    response_code: int,
    duration_ms: float,
    error: Optional[str] = None
):
    """
    Log API request details in structured format.

    Args:
        logger: StructuredLogger instance
        provider: API provider name (e.g., 'theoddsapi')
        endpoint: API endpoint path
        params: Request parameters
        response_code: HTTP response code
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
    """
    log_data = {
        'provider': provider,
        'endpoint': endpoint,
        'params': params,
        'response_code': response_code,
        'duration_ms': round(duration_ms, 2)
    }

    if error:
        log_data['error'] = error
        logger.error(f"API request failed: {endpoint}", **log_data)
    else:
        logger.info(f"API request successful: {endpoint}", **log_data)


def measure_duration(func: Callable) -> Callable:
    """
    Decorator to measure and log function execution duration.

    Usage:
        @measure_duration
        def my_slow_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start_time) * 1000  # Convert to ms

        print(f"[Duration] {func.__name__} took {duration:.2f}ms")
        return result

    return wrapper


# Global logger instance (can be imported directly)
logger = StructuredLogger(__name__)

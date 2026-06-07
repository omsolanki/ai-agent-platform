"""Retry and failure recovery utilities for agent execution."""

import asyncio
from typing import Any, Callable, TypeVar

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()

T = TypeVar("T")


def with_retry(max_attempts: int = 3, min_wait: float = 1.0, max_wait: float = 10.0):
    """Decorator for async functions with exponential backoff retry."""

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
            reraise=True,
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def execute_with_fallback(
    primary: Callable[..., Any],
    fallback: Callable[..., Any],
    *args,
    **kwargs,
) -> Any:
    """Execute primary function; fall back on failure."""
    try:
        return await primary(*args, **kwargs)
    except Exception as exc:
        logger.warning("fallback_triggered", error=str(exc))
        return await fallback(*args, **kwargs)


class CircuitBreaker:
    """Simple circuit breaker for external service calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "closed"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        import time

        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise ConnectionError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error("circuit_breaker_open", failures=self.failure_count)
            raise

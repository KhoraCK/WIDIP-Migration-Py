"""
Utilitaires pour les retries avec backoff exponentiel.
"""

import asyncio
import functools
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T")

# Exceptions par défaut à retry
DEFAULT_RETRY_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Décorateur pour ajouter des retries avec backoff exponentiel.

    Args:
        max_attempts: Nombre maximum de tentatives
        min_wait: Temps d'attente minimum entre les tentatives (secondes)
        max_wait: Temps d'attente maximum entre les tentatives (secondes)
        retry_exceptions: Types d'exceptions à retry (défaut: ConnectionError, TimeoutError)

    Usage:
        @with_retry(max_attempts=3)
        async def fetch_data():
            ...
    """
    exceptions = retry_exceptions or DEFAULT_RETRY_EXCEPTIONS

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                attempt = 0
                async for attempt_ctx in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=min_wait, max=max_wait),
                    retry=retry_if_exception_type(exceptions),
                    reraise=True,
                ):
                    with attempt_ctx:
                        attempt += 1
                        if attempt > 1:
                            logger.warning(
                                "retry_attempt",
                                function=func.__name__,
                                attempt=attempt,
                                max_attempts=max_attempts,
                            )
                        return await func(*args, **kwargs)
                # Should not reach here, but satisfy type checker
                raise RuntimeError("Retry loop exited unexpectedly")

            return async_wrapper  # type: ignore
        else:
            # Version synchrone
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                last_exception: Optional[Exception] = None
                wait_time = min_wait

                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts:
                            logger.warning(
                                "retry_attempt",
                                function=func.__name__,
                                attempt=attempt,
                                max_attempts=max_attempts,
                                error=str(e),
                            )
                            import time

                            time.sleep(wait_time)
                            wait_time = min(wait_time * 2, max_wait)
                        else:
                            raise

                # Should not reach here
                if last_exception:
                    raise last_exception
                raise RuntimeError("Retry loop exited unexpectedly")

            return sync_wrapper  # type: ignore

    return decorator


class RetryableError(Exception):
    """Exception marquée comme retryable."""

    pass


class NonRetryableError(Exception):
    """Exception qui ne doit pas être retry."""

    pass

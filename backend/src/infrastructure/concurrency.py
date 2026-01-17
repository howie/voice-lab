"""Concurrency utilities for TTS synthesis.

T070: Handle concurrent request processing
"""

import asyncio
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrency limits."""

    # Maximum concurrent synthesis requests per provider
    max_concurrent_per_provider: int = 10

    # Maximum total concurrent synthesis requests
    max_concurrent_total: int = 50

    # Maximum queue size before rejecting requests
    max_queue_size: int = 100

    # Request timeout in seconds
    request_timeout: float = 60.0

    # Provider-specific limits (override defaults)
    provider_limits: dict[str, int] | None = None

    def get_provider_limit(self, provider: str) -> int:
        """Get concurrency limit for a specific provider."""
        if self.provider_limits and provider in self.provider_limits:
            return self.provider_limits[provider]
        return self.max_concurrent_per_provider


class ConcurrencyManager:
    """Manager for controlling concurrent TTS synthesis requests.

    Uses semaphores to limit concurrent requests both globally
    and per-provider to prevent overwhelming TTS services.
    """

    def __init__(self, config: ConcurrencyConfig | None = None) -> None:
        self.config = config or ConcurrencyConfig()

        # Global semaphore for total concurrent requests
        self._global_semaphore = asyncio.Semaphore(
            self.config.max_concurrent_total
        )

        # Per-provider semaphores
        self._provider_semaphores: dict[str, asyncio.Semaphore] = {}

        # Queue size tracking
        self._queue_size = 0
        self._queue_lock = asyncio.Lock()

        # Stats
        self._stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "rejected_requests": 0,
            "timeout_requests": 0,
        }

    def _get_provider_semaphore(self, provider: str) -> asyncio.Semaphore:
        """Get or create semaphore for a provider."""
        if provider not in self._provider_semaphores:
            limit = self.config.get_provider_limit(provider)
            self._provider_semaphores[provider] = asyncio.Semaphore(limit)
        return self._provider_semaphores[provider]

    async def _increment_queue(self) -> bool:
        """Try to add to queue, return False if full."""
        async with self._queue_lock:
            if self._queue_size >= self.config.max_queue_size:
                self._stats["rejected_requests"] += 1
                return False
            self._queue_size += 1
            self._stats["total_requests"] += 1
            return True

    async def _decrement_queue(self) -> None:
        """Remove from queue."""
        async with self._queue_lock:
            self._queue_size = max(0, self._queue_size - 1)

    @asynccontextmanager
    async def acquire(self, provider: str):
        """Acquire concurrency slots for a synthesis request.

        Args:
            provider: The TTS provider name

        Raises:
            asyncio.QueueFull: If the queue is full
            asyncio.TimeoutError: If acquisition times out

        Usage:
            async with manager.acquire("azure"):
                result = await synthesize(...)
        """
        # Check queue capacity
        if not await self._increment_queue():
            raise asyncio.QueueFull("Request queue is full")

        try:
            provider_sem = self._get_provider_semaphore(provider)

            # Acquire both semaphores with timeout
            try:
                async with asyncio.timeout(self.config.request_timeout):
                    await self._global_semaphore.acquire()
                    try:
                        await provider_sem.acquire()
                        try:
                            yield
                            self._stats["completed_requests"] += 1
                        finally:
                            provider_sem.release()
                    finally:
                        self._global_semaphore.release()
            except TimeoutError:
                self._stats["timeout_requests"] += 1
                raise

        finally:
            await self._decrement_queue()

    async def execute_with_limit(
        self,
        provider: str,
        coro: Callable[[], Any],
    ) -> Any:
        """Execute a coroutine with concurrency limits.

        Args:
            provider: The TTS provider name
            coro: Coroutine function to execute

        Returns:
            Result of the coroutine
        """
        async with self.acquire(provider):
            return await coro()

    async def execute_batch(
        self,
        tasks: list[tuple[str, Callable[[], Any]]],
        return_exceptions: bool = True,
    ) -> list[Any]:
        """Execute multiple tasks with concurrency limits.

        Args:
            tasks: List of (provider, coroutine) tuples
            return_exceptions: Whether to return exceptions or raise

        Returns:
            List of results (or exceptions if return_exceptions=True)
        """
        async def wrapped_task(provider: str, coro: Callable[[], Any]):
            async with self.acquire(provider):
                return await coro()

        coros = [wrapped_task(p, c) for p, c in tasks]
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)

    def get_stats(self) -> dict[str, Any]:
        """Get concurrency statistics."""
        return {
            **self._stats,
            "current_queue_size": self._queue_size,
            "global_available": self._global_semaphore._value,
            "provider_available": {
                p: s._value for p, s in self._provider_semaphores.items()
            },
        }

    def get_availability(self, provider: str) -> dict[str, int]:
        """Get availability info for a provider."""
        provider_sem = self._get_provider_semaphore(provider)
        return {
            "global_available": self._global_semaphore._value,
            "provider_available": provider_sem._value,
            "queue_available": max(
                0, self.config.max_queue_size - self._queue_size
            ),
        }


# Default manager instance
default_concurrency_manager = ConcurrencyManager()


class ProviderCircuitBreaker:
    """Circuit breaker for handling provider failures.

    Prevents overwhelming a failing provider by temporarily
    blocking requests after consecutive failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_requests: int = 1,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying again
            half_open_requests: Requests allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self._failures: dict[str, int] = {}
        self._last_failure: dict[str, float] = {}
        self._state: dict[str, str] = {}  # "closed", "open", "half_open"
        self._half_open_count: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def is_available(self, provider: str) -> bool:
        """Check if provider is available."""
        async with self._lock:
            state = self._state.get(provider, "closed")

            if state == "closed":
                return True

            if state == "open":
                # Check if recovery timeout passed
                import time
                last = self._last_failure.get(provider, 0)
                if time.time() - last >= self.recovery_timeout:
                    # Move to half-open
                    self._state[provider] = "half_open"
                    self._half_open_count[provider] = 0
                    return True
                return False

            if state == "half_open":
                # Allow limited requests
                count = self._half_open_count.get(provider, 0)
                if count < self.half_open_requests:
                    self._half_open_count[provider] = count + 1
                    return True
                return False

            return False

    async def record_success(self, provider: str) -> None:
        """Record a successful request."""
        async with self._lock:
            state = self._state.get(provider, "closed")

            if state == "half_open":
                # Success in half-open: close circuit
                self._state[provider] = "closed"
                self._failures[provider] = 0

    async def record_failure(self, provider: str) -> None:
        """Record a failed request."""
        import time

        async with self._lock:
            failures = self._failures.get(provider, 0) + 1
            self._failures[provider] = failures
            self._last_failure[provider] = time.time()

            state = self._state.get(provider, "closed")

            if state == "half_open":
                # Failure in half-open: reopen circuit
                self._state[provider] = "open"
            elif failures >= self.failure_threshold:
                # Too many failures: open circuit
                self._state[provider] = "open"

    def get_status(self, provider: str) -> dict[str, Any]:
        """Get circuit breaker status for a provider."""
        import time

        state = self._state.get(provider, "closed")
        failures = self._failures.get(provider, 0)
        last_failure = self._last_failure.get(provider)

        status = {
            "provider": provider,
            "state": state,
            "failures": failures,
            "failure_threshold": self.failure_threshold,
        }

        if last_failure:
            elapsed = time.time() - last_failure
            status["seconds_since_failure"] = round(elapsed, 1)
            if state == "open":
                remaining = max(0, self.recovery_timeout - elapsed)
                status["recovery_in_seconds"] = round(remaining, 1)

        return status


# Default circuit breaker instance
default_circuit_breaker = ProviderCircuitBreaker()

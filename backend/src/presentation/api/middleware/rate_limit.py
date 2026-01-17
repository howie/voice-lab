"""Rate limiting middleware.

T067: Implement rate limiting middleware
"""

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.domain.errors import RateLimitError


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Requests per window
    requests_per_minute: int = 60
    requests_per_hour: int = 1000

    # TTS-specific limits (more restrictive)
    tts_requests_per_minute: int = 20
    tts_requests_per_hour: int = 200

    # Burst allowance
    burst_size: int = 10

    # Paths that are rate limited more strictly
    strict_paths: list[str] = field(
        default_factory=lambda: [
            "/api/v1/tts/synthesize",
            "/api/v1/tts/stream",
        ]
    )

    # Paths excluded from rate limiting
    excluded_paths: list[str] = field(
        default_factory=lambda: [
            "/health",
            "/api/v1/providers",
            "/docs",
            "/openapi.json",
        ]
    )


@dataclass
class RateLimitState:
    """State for tracking rate limits."""

    minute_requests: int = 0
    hour_requests: int = 0
    minute_start: float = field(default_factory=time.time)
    hour_start: float = field(default_factory=time.time)
    tokens: float = 0.0
    last_update: float = field(default_factory=time.time)


class RateLimiter:
    """Token bucket rate limiter with sliding window."""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self.config = config or RateLimitConfig()
        self._states: dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._lock = asyncio.Lock()

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Try to get user ID from auth
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client = request.client
        if client:
            return f"ip:{client.host}"

        return "unknown"

    def _is_strict_path(self, path: str) -> bool:
        """Check if path requires strict rate limiting."""
        return any(path.startswith(p) for p in self.config.strict_paths)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        return any(path.startswith(p) for p in self.config.excluded_paths)

    def _get_limits(self, path: str) -> tuple[int, int]:
        """Get rate limits for a path (per minute, per hour)."""
        if self._is_strict_path(path):
            return (
                self.config.tts_requests_per_minute,
                self.config.tts_requests_per_hour,
            )
        return (
            self.config.requests_per_minute,
            self.config.requests_per_hour,
        )

    async def check_rate_limit(self, request: Request) -> int | None:
        """Check if request is within rate limits.

        Returns:
            None if allowed, or seconds until retry if rate limited.
        """
        path = request.url.path

        # Skip excluded paths
        if self._is_excluded_path(path):
            return None

        client_id = self._get_client_id(request)
        per_minute, per_hour = self._get_limits(path)

        async with self._lock:
            state = self._states[client_id]
            now = time.time()

            # Reset minute window if needed
            if now - state.minute_start >= 60:
                state.minute_requests = 0
                state.minute_start = now

            # Reset hour window if needed
            if now - state.hour_start >= 3600:
                state.hour_requests = 0
                state.hour_start = now

            # Check minute limit
            if state.minute_requests >= per_minute:
                retry_after = int(60 - (now - state.minute_start))
                return max(1, retry_after)

            # Check hour limit
            if state.hour_requests >= per_hour:
                retry_after = int(3600 - (now - state.hour_start))
                return max(1, retry_after)

            # Allow request and increment counters
            state.minute_requests += 1
            state.hour_requests += 1

            return None

    def get_remaining(self, request: Request) -> dict[str, int]:
        """Get remaining requests for a client."""
        client_id = self._get_client_id(request)
        path = request.url.path
        per_minute, per_hour = self._get_limits(path)

        state = self._states.get(client_id)
        if not state:
            return {
                "minute_remaining": per_minute,
                "hour_remaining": per_hour,
            }

        now = time.time()
        minute_remaining = per_minute - state.minute_requests
        hour_remaining = per_hour - state.hour_requests

        # Reset if window expired
        if now - state.minute_start >= 60:
            minute_remaining = per_minute
        if now - state.hour_start >= 3600:
            hour_remaining = per_hour

        return {
            "minute_remaining": max(0, minute_remaining),
            "hour_remaining": max(0, hour_remaining),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, config: RateLimitConfig | None = None) -> None:
        super().__init__(app)
        self.limiter = RateLimiter(config)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        retry_after = await self.limiter.check_rate_limit(request)

        if retry_after is not None:
            raise RateLimitError(retry_after=retry_after)

        # Add rate limit headers to response
        response = await call_next(request)

        remaining = self.limiter.get_remaining(request)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining["minute_remaining"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining["hour_remaining"])

        return response


# Default rate limiter instance
default_rate_limiter = RateLimiter()

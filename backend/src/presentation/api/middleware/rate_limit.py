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
            "/api/v1/credentials/providers",
            "/docs",
            "/openapi.json",
        ]
    )


@dataclass
class RateLimitState:
    """State for tracking rate limits.

    Maintains separate counters for general and strict (TTS) paths so that
    general API traffic does not inflate the strict-path remaining count.
    """

    # General counters (all requests)
    minute_requests: int = 0
    hour_requests: int = 0
    minute_start: float = field(default_factory=time.time)
    hour_start: float = field(default_factory=time.time)
    # Strict-path counters (TTS/STT synthesis only)
    strict_minute_requests: int = 0
    strict_hour_requests: int = 0
    strict_minute_start: float = field(default_factory=time.time)
    strict_hour_start: float = field(default_factory=time.time)


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

    async def check_rate_limit(self, request: Request) -> int | None:
        """Check if request is within rate limits.

        Returns:
            None if allowed, or seconds until retry if rate limited.

        For strict paths (TTS synthesis), the request must pass **both**
        general and strict limits.  General counters are always incremented;
        strict counters are only incremented for strict-path requests.
        """
        path = request.url.path

        # Skip excluded paths
        if self._is_excluded_path(path):
            return None

        client_id = self._get_client_id(request)
        is_strict = self._is_strict_path(path)

        async with self._lock:
            state = self._states[client_id]
            now = time.time()

            # --- Reset general windows ---
            if now - state.minute_start >= 60:
                state.minute_requests = 0
                state.minute_start = now
            if now - state.hour_start >= 3600:
                state.hour_requests = 0
                state.hour_start = now

            # --- Check general limits ---
            gen_per_minute = self.config.requests_per_minute
            gen_per_hour = self.config.requests_per_hour

            if state.minute_requests >= gen_per_minute:
                retry_after = int(60 - (now - state.minute_start))
                return max(1, retry_after)
            if state.hour_requests >= gen_per_hour:
                retry_after = int(3600 - (now - state.hour_start))
                return max(1, retry_after)

            # --- For strict paths, also check strict limits ---
            if is_strict:
                if now - state.strict_minute_start >= 60:
                    state.strict_minute_requests = 0
                    state.strict_minute_start = now
                if now - state.strict_hour_start >= 3600:
                    state.strict_hour_requests = 0
                    state.strict_hour_start = now

                if state.strict_minute_requests >= self.config.tts_requests_per_minute:
                    retry_after = int(60 - (now - state.strict_minute_start))
                    return max(1, retry_after)
                if state.strict_hour_requests >= self.config.tts_requests_per_hour:
                    retry_after = int(3600 - (now - state.strict_hour_start))
                    return max(1, retry_after)

            # Allow request — increment general counters always
            state.minute_requests += 1
            state.hour_requests += 1

            # Increment strict counters only for strict paths
            if is_strict:
                state.strict_minute_requests += 1
                state.strict_hour_requests += 1

            return None

    def get_remaining(self, request: Request) -> dict[str, int]:
        """Get remaining *general* requests for a client."""
        client_id = self._get_client_id(request)
        per_minute = self.config.requests_per_minute
        per_hour = self.config.requests_per_hour

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

    def get_remaining_for_path(
        self,
        request: Request,
        path_override: str,
    ) -> dict[str, int]:
        """Get remaining requests for a specific path type.

        For strict paths, uses the **strict** counters so that general API
        traffic does not deflate the TTS remaining count.
        For general paths, delegates to ``get_remaining()``.
        """
        if not self._is_strict_path(path_override):
            return self.get_remaining(request)

        client_id = self._get_client_id(request)
        per_minute = self.config.tts_requests_per_minute
        per_hour = self.config.tts_requests_per_hour

        state = self._states.get(client_id)
        if not state:
            return {
                "minute_remaining": per_minute,
                "hour_remaining": per_hour,
            }

        now = time.time()
        minute_used = state.strict_minute_requests if (now - state.strict_minute_start) < 60 else 0
        hour_used = state.strict_hour_requests if (now - state.strict_hour_start) < 3600 else 0

        return {
            "minute_remaining": max(0, per_minute - minute_used),
            "hour_remaining": max(0, per_hour - hour_used),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(
        self,
        app,
        config: RateLimitConfig | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter or RateLimiter(config)

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

"""Unit and integration tests for the rate limiting middleware.

Tests cover:
- RateLimiter: general and strict-path limits, window resets, per-client isolation
- RateLimitMiddleware: response headers, 429 rejection
- BUG-1 regression: general traffic must NOT inflate strict counters
"""

import time
from unittest.mock import MagicMock

import pytest

from src.domain.errors import RateLimitError
from src.presentation.api.middleware.rate_limit import (
    RateLimitConfig,
    RateLimiter,
    RateLimitMiddleware,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(path: str = "/api/v1/test", client_host: str = "127.0.0.1") -> MagicMock:
    """Create a minimal mock Request for testing."""
    request = MagicMock()
    request.url.path = path
    request.state = MagicMock(spec=[])  # no user_id attribute
    request.headers = {}
    request.client = MagicMock()
    request.client.host = client_host
    return request


def _config(**overrides) -> RateLimitConfig:
    return RateLimitConfig(**overrides)


# ---------------------------------------------------------------------------
# RateLimiter unit tests
# ---------------------------------------------------------------------------


class TestRateLimiterGeneral:
    """General (non-strict) rate limiting behaviour."""

    @pytest.mark.asyncio
    async def test_allows_requests_within_minute_limit(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=5, requests_per_hour=100))
        req = _make_request()

        for _ in range(5):
            assert await limiter.check_rate_limit(req) is None

    @pytest.mark.asyncio
    async def test_rejects_when_minute_limit_exceeded(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=3, requests_per_hour=100))
        req = _make_request()

        for _ in range(3):
            await limiter.check_rate_limit(req)

        retry_after = await limiter.check_rate_limit(req)
        assert retry_after is not None
        assert retry_after >= 1

    @pytest.mark.asyncio
    async def test_rejects_when_hour_limit_exceeded(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=100, requests_per_hour=5))
        req = _make_request()

        for _ in range(5):
            await limiter.check_rate_limit(req)

        retry_after = await limiter.check_rate_limit(req)
        assert retry_after is not None
        assert retry_after >= 1

    @pytest.mark.asyncio
    async def test_minute_window_resets_after_60s(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=2, requests_per_hour=100))
        req = _make_request()

        for _ in range(2):
            await limiter.check_rate_limit(req)

        # Simulate 61 seconds passing
        client_id = limiter._get_client_id(req)
        state = limiter._states[client_id]
        state.minute_start = time.time() - 61

        assert await limiter.check_rate_limit(req) is None

    @pytest.mark.asyncio
    async def test_excluded_path_not_limited(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=1, requests_per_hour=1))
        req = _make_request(path="/health")

        for _ in range(10):
            assert await limiter.check_rate_limit(req) is None

    @pytest.mark.asyncio
    async def test_different_clients_tracked_independently(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=2, requests_per_hour=100))
        req_a = _make_request(client_host="10.0.0.1")
        req_b = _make_request(client_host="10.0.0.2")

        for _ in range(2):
            await limiter.check_rate_limit(req_a)

        # Client A is exhausted
        assert await limiter.check_rate_limit(req_a) is not None
        # Client B should still be fine
        assert await limiter.check_rate_limit(req_b) is None


class TestRateLimiterStrict:
    """Strict-path (TTS) rate limiting behaviour."""

    @pytest.mark.asyncio
    async def test_strict_path_uses_tts_limits(self) -> None:
        limiter = RateLimiter(
            _config(
                requests_per_minute=100,
                requests_per_hour=1000,
                tts_requests_per_minute=3,
                tts_requests_per_hour=30,
            )
        )
        req = _make_request(path="/api/v1/tts/synthesize")

        for _ in range(3):
            assert await limiter.check_rate_limit(req) is None

        retry_after = await limiter.check_rate_limit(req)
        assert retry_after is not None

    @pytest.mark.asyncio
    async def test_general_traffic_does_not_affect_strict_counter(self) -> None:
        """BUG-1 regression: general requests must not inflate the strict counter."""
        limiter = RateLimiter(
            _config(
                requests_per_minute=100,
                requests_per_hour=1000,
                tts_requests_per_minute=20,
                tts_requests_per_hour=200,
            )
        )
        general_req = _make_request(path="/api/v1/some-api")
        tts_req = _make_request(path="/api/v1/tts/synthesize")

        # Send 15 general requests
        for _ in range(15):
            await limiter.check_rate_limit(general_req)

        # TTS should still have full 20 remaining
        remaining = limiter.get_remaining_for_path(tts_req, "/api/v1/tts/synthesize")
        assert remaining["minute_remaining"] == 20

        # TTS request should pass
        assert await limiter.check_rate_limit(tts_req) is None

    @pytest.mark.asyncio
    async def test_strict_request_increments_both_counters(self) -> None:
        """Strict-path requests must increment both general and strict counters."""
        limiter = RateLimiter(
            _config(
                requests_per_minute=100,
                requests_per_hour=1000,
                tts_requests_per_minute=20,
                tts_requests_per_hour=200,
            )
        )
        tts_req = _make_request(path="/api/v1/tts/synthesize")

        # Send 5 TTS requests
        for _ in range(5):
            await limiter.check_rate_limit(tts_req)

        # General remaining should be 100 - 5 = 95
        general_remaining = limiter.get_remaining(tts_req)
        assert general_remaining["minute_remaining"] == 95

        # Strict remaining should be 20 - 5 = 15
        tts_remaining = limiter.get_remaining_for_path(tts_req, "/api/v1/tts/synthesize")
        assert tts_remaining["minute_remaining"] == 15

    @pytest.mark.asyncio
    async def test_strict_path_also_checked_against_general_limit(self) -> None:
        """Even strict-path requests must not exceed general limits."""
        limiter = RateLimiter(
            _config(
                requests_per_minute=5,  # General limit lower than strict
                requests_per_hour=1000,
                tts_requests_per_minute=20,
                tts_requests_per_hour=200,
            )
        )
        tts_req = _make_request(path="/api/v1/tts/synthesize")

        for _ in range(5):
            await limiter.check_rate_limit(tts_req)

        # Should hit general limit even though strict limit (20) not reached
        retry_after = await limiter.check_rate_limit(tts_req)
        assert retry_after is not None


class TestGetRemaining:
    """Tests for get_remaining and get_remaining_for_path."""

    def test_get_remaining_no_state(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=60, requests_per_hour=1000))
        req = _make_request()

        remaining = limiter.get_remaining(req)
        assert remaining["minute_remaining"] == 60
        assert remaining["hour_remaining"] == 1000

    @pytest.mark.asyncio
    async def test_get_remaining_after_requests(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=60, requests_per_hour=1000))
        req = _make_request()

        for _ in range(10):
            await limiter.check_rate_limit(req)

        remaining = limiter.get_remaining(req)
        assert remaining["minute_remaining"] == 50
        assert remaining["hour_remaining"] == 990

    def test_get_remaining_for_path_strict_no_state(self) -> None:
        limiter = RateLimiter(_config(tts_requests_per_minute=20, tts_requests_per_hour=200))
        req = _make_request()

        remaining = limiter.get_remaining_for_path(req, "/api/v1/tts/synthesize")
        assert remaining["minute_remaining"] == 20
        assert remaining["hour_remaining"] == 200

    @pytest.mark.asyncio
    async def test_get_remaining_for_path_uses_strict_counters(self) -> None:
        """get_remaining_for_path must use strict counters, not general ones."""
        limiter = RateLimiter(
            _config(
                requests_per_minute=100,
                requests_per_hour=1000,
                tts_requests_per_minute=20,
                tts_requests_per_hour=200,
            )
        )
        general_req = _make_request(path="/api/v1/other")
        tts_req = _make_request(path="/api/v1/tts/synthesize")

        # 30 general + 3 TTS
        for _ in range(30):
            await limiter.check_rate_limit(general_req)
        for _ in range(3):
            await limiter.check_rate_limit(tts_req)

        remaining = limiter.get_remaining_for_path(tts_req, "/api/v1/tts/synthesize")
        assert remaining["minute_remaining"] == 17  # 20 - 3 (not 20 - 33)

    def test_get_remaining_for_general_path_delegates(self) -> None:
        """Non-strict path_override should delegate to get_remaining."""
        limiter = RateLimiter(_config(requests_per_minute=60, requests_per_hour=1000))
        req = _make_request()

        remaining = limiter.get_remaining_for_path(req, "/api/v1/some-api")
        assert remaining["minute_remaining"] == 60
        assert remaining["hour_remaining"] == 1000


# ---------------------------------------------------------------------------
# RateLimitMiddleware integration tests
# ---------------------------------------------------------------------------


class TestRateLimitMiddleware:
    """Integration tests for the middleware."""

    @pytest.mark.asyncio
    async def test_adds_rate_limit_headers(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=60, requests_per_hour=1000))
        middleware = RateLimitMiddleware(MagicMock(), limiter=limiter)

        req = _make_request()

        async def call_next(_request):
            resp = MagicMock()
            resp.headers = {}
            return resp

        response = await middleware.dispatch(req, call_next)
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers

    @pytest.mark.asyncio
    async def test_returns_429_when_rate_limited(self) -> None:
        limiter = RateLimiter(_config(requests_per_minute=1, requests_per_hour=100))
        middleware = RateLimitMiddleware(MagicMock(), limiter=limiter)

        req = _make_request()

        async def call_next(_request):
            resp = MagicMock()
            resp.headers = {}
            return resp

        # First request passes
        await middleware.dispatch(req, call_next)

        # Second should raise RateLimitError
        with pytest.raises(RateLimitError):
            await middleware.dispatch(req, call_next)

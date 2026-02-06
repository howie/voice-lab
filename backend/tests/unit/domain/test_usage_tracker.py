"""Tests for provider usage tracker — rate limit header parsing and storage."""

import time

from src.domain.services.usage_tracker import (
    ProviderUsageTracker,
    RateLimitHeaders,
    parse_rate_limit_headers,
)


class TestParseRateLimitHeaders:
    """Tests for parse_rate_limit_headers()."""

    def test_standard_x_ratelimit_headers(self):
        headers = {
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Remaining": "8",
            "X-RateLimit-Reset": "1700000000",
        }
        result = parse_rate_limit_headers(headers, "gemini")
        assert result is not None
        assert result.limit == 10
        assert result.remaining == 8
        assert result.reset_at == 1700000000.0

    def test_ratelimit_headers_without_x_prefix(self):
        headers = {
            "RateLimit-Limit": "100",
            "RateLimit-Remaining": "42",
        }
        result = parse_rate_limit_headers(headers)
        assert result is not None
        assert result.limit == 100
        assert result.remaining == 42
        assert result.reset_at is None

    def test_elevenlabs_xi_ratelimit_headers(self):
        headers = {
            "xi-ratelimit-limit": "50",
            "xi-ratelimit-remaining": "49",
        }
        result = parse_rate_limit_headers(headers, "elevenlabs")
        assert result is not None
        assert result.limit == 50
        assert result.remaining == 49

    def test_case_insensitive(self):
        headers = {
            "x-ratelimit-limit": "20",
            "X-RATELIMIT-REMAINING": "15",
        }
        result = parse_rate_limit_headers(headers)
        assert result is not None
        assert result.limit == 20
        assert result.remaining == 15

    def test_no_rate_limit_headers_returns_none(self):
        headers = {
            "Content-Type": "application/json",
            "X-Request-Id": "abc123",
        }
        result = parse_rate_limit_headers(headers)
        assert result is None

    def test_empty_headers_returns_none(self):
        result = parse_rate_limit_headers({})
        assert result is None

    def test_only_remaining_is_parsed(self):
        headers = {"X-RateLimit-Remaining": "3"}
        result = parse_rate_limit_headers(headers)
        assert result is not None
        assert result.limit is None
        assert result.remaining == 3
        assert result.reset_at is None

    def test_invalid_values_are_ignored(self):
        headers = {
            "X-RateLimit-Limit": "not-a-number",
            "X-RateLimit-Remaining": "5",
        }
        result = parse_rate_limit_headers(headers)
        assert result is not None
        assert result.limit is None
        assert result.remaining == 5

    def test_captured_at_is_set(self):
        headers = {"X-RateLimit-Limit": "10"}
        before = time.time()
        result = parse_rate_limit_headers(headers)
        after = time.time()
        assert result is not None
        assert before <= result.captured_at <= after


class TestProviderUsageTrackerRateLimits:
    """Tests for rate limit header storage in ProviderUsageTracker."""

    def test_record_and_get_rate_limit_headers(self):
        tracker = ProviderUsageTracker()
        rl = RateLimitHeaders(limit=10, remaining=8, reset_at=1700000000.0)

        tracker.record_rate_limit_headers("user1", "gemini", rl)
        result = tracker.get_rate_limit_headers("user1", "gemini")

        assert result is not None
        assert result.limit == 10
        assert result.remaining == 8
        assert result.reset_at == 1700000000.0

    def test_get_nonexistent_returns_none(self):
        tracker = ProviderUsageTracker()
        assert tracker.get_rate_limit_headers("user1", "gemini") is None

    def test_latest_headers_overwrite_previous(self):
        tracker = ProviderUsageTracker()
        rl1 = RateLimitHeaders(limit=10, remaining=8)
        rl2 = RateLimitHeaders(limit=10, remaining=5)

        tracker.record_rate_limit_headers("user1", "gemini", rl1)
        tracker.record_rate_limit_headers("user1", "gemini", rl2)

        result = tracker.get_rate_limit_headers("user1", "gemini")
        assert result is not None
        assert result.remaining == 5

    def test_different_providers_are_isolated(self):
        tracker = ProviderUsageTracker()
        rl_gemini = RateLimitHeaders(limit=10, remaining=8)
        rl_eleven = RateLimitHeaders(limit=50, remaining=49)

        tracker.record_rate_limit_headers("user1", "gemini", rl_gemini)
        tracker.record_rate_limit_headers("user1", "elevenlabs", rl_eleven)

        g = tracker.get_rate_limit_headers("user1", "gemini")
        e = tracker.get_rate_limit_headers("user1", "elevenlabs")
        assert g is not None and g.limit == 10
        assert e is not None and e.limit == 50

    def test_get_usage_includes_rate_limit_data(self):
        tracker = ProviderUsageTracker()
        rl = RateLimitHeaders(
            limit=10,
            remaining=7,
            reset_at=1700000000.0,
            captured_at=time.time() - 5.0,
        )
        tracker.record_rate_limit_headers("user1", "gemini", rl)
        tracker.record_request("user1", "gemini")

        snapshot = tracker.get_usage("user1", "gemini")
        assert snapshot.provider_rpm_limit == 10
        assert snapshot.provider_rpm_remaining == 7
        assert snapshot.provider_rpm_reset_at == 1700000000.0
        assert snapshot.rate_limit_data_age_seconds is not None
        assert snapshot.rate_limit_data_age_seconds >= 4.0

    def test_get_usage_without_rate_limit_data(self):
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")

        snapshot = tracker.get_usage("user1", "gemini")
        assert snapshot.provider_rpm_limit is None
        assert snapshot.provider_rpm_remaining is None
        assert snapshot.provider_rpm_reset_at is None
        assert snapshot.rate_limit_data_age_seconds is None

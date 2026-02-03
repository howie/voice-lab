"""Unit tests for ProviderUsageTracker.

Tests the in-memory usage tracking logic: window counters, resets,
RPM estimation, and warning generation.
"""

import time
from unittest.mock import patch

from src.domain.services.usage_tracker import (
    ProviderUsageSnapshot,
    ProviderUsageTracker,
    UsageWindow,
    _estimate_rpm_limit,
    _generate_warning,
)


class TestUsageWindow:
    """Tests for UsageWindow dataclass defaults."""

    def test_default_values(self) -> None:
        w = UsageWindow()
        assert w.request_count == 0
        assert w.error_count == 0
        assert w.quota_error_count == 0
        assert w.last_request_at == 0.0
        assert w.last_quota_error_at == 0.0
        assert w.last_retry_after is None


class TestProviderUsageTracker:
    """Tests for the ProviderUsageTracker core logic."""

    def test_record_request_increments_all_windows(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")

        usage = tracker.get_usage("user1", "gemini")
        assert usage.minute_requests == 1
        assert usage.hour_requests == 1
        assert usage.day_requests == 1
        assert usage.minute_errors == 0

    def test_multiple_requests_accumulate(self) -> None:
        tracker = ProviderUsageTracker()
        for _ in range(5):
            tracker.record_request("user1", "gemini")

        usage = tracker.get_usage("user1", "gemini")
        assert usage.minute_requests == 5
        assert usage.hour_requests == 5
        assert usage.day_requests == 5

    def test_separate_users_tracked_independently(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")
        tracker.record_request("user1", "gemini")
        tracker.record_request("user2", "gemini")

        u1 = tracker.get_usage("user1", "gemini")
        u2 = tracker.get_usage("user2", "gemini")
        assert u1.minute_requests == 2
        assert u2.minute_requests == 1

    def test_separate_providers_tracked_independently(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")
        tracker.record_request("user1", "gemini")
        tracker.record_request("user1", "azure")

        gemini = tracker.get_usage("user1", "gemini")
        azure = tracker.get_usage("user1", "azure")
        assert gemini.minute_requests == 2
        assert azure.minute_requests == 1

    def test_record_error_increments_error_counters(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")
        tracker.record_error("user1", "gemini")

        usage = tracker.get_usage("user1", "gemini")
        assert usage.minute_requests == 1
        assert usage.minute_errors == 1
        assert usage.quota_hits_today == 0

    def test_record_quota_error_increments_quota_counters(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")
        tracker.record_error("user1", "gemini", is_quota_error=True, retry_after=3600)

        usage = tracker.get_usage("user1", "gemini")
        assert usage.minute_errors == 1
        assert usage.quota_hits_today == 1
        assert usage.last_retry_after == 3600

    def test_multiple_quota_errors_accumulate(self) -> None:
        tracker = ProviderUsageTracker()
        for _ in range(3):
            tracker.record_request("user1", "gemini")
            tracker.record_error("user1", "gemini", is_quota_error=True)

        usage = tracker.get_usage("user1", "gemini")
        assert usage.quota_hits_today == 3
        assert usage.day_errors == 3

    def test_get_usage_for_unused_provider_returns_zeros(self) -> None:
        tracker = ProviderUsageTracker()
        usage = tracker.get_usage("user1", "nonexistent")
        assert usage.minute_requests == 0
        assert usage.hour_requests == 0
        assert usage.day_requests == 0
        assert usage.quota_hits_today == 0
        assert usage.last_request_at is None

    def test_get_all_usage_returns_all_used_providers(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")
        tracker.record_request("user1", "azure")

        all_usage = tracker.get_all_usage("user1")
        assert set(all_usage.keys()) == {"gemini", "azure"}
        assert all_usage["gemini"].minute_requests == 1
        assert all_usage["azure"].minute_requests == 1

    def test_get_all_usage_empty_for_unused_user(self) -> None:
        tracker = ProviderUsageTracker()
        all_usage = tracker.get_all_usage("nobody")
        assert all_usage == {}

    def test_window_resets_after_expiration(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")

        # Simulate time passing beyond the minute window
        with patch("src.domain.services.usage_tracker.time") as mock_time:
            # First call during record was at real time; now jump ahead
            mock_time.time.return_value = time.time() + 61
            usage = tracker.get_usage("user1", "gemini")

        # Minute window should have reset, but hour and day remain
        assert usage.minute_requests == 0
        assert usage.hour_requests == 1
        assert usage.day_requests == 1

    def test_snapshot_has_correct_provider(self) -> None:
        tracker = ProviderUsageTracker()
        tracker.record_request("user1", "gemini")
        usage = tracker.get_usage("user1", "gemini")
        assert isinstance(usage, ProviderUsageSnapshot)
        assert usage.provider == "gemini"


class TestEstimateRpmLimit:
    """Tests for _estimate_rpm_limit function."""

    def test_returns_known_limit_when_no_errors(self) -> None:
        minute = UsageWindow(request_count=3, quota_error_count=0)
        result = _estimate_rpm_limit("gemini", minute)
        assert result == 10  # Known free tier for Gemini

    def test_returns_none_for_unknown_provider(self) -> None:
        minute = UsageWindow(request_count=3, quota_error_count=0)
        result = _estimate_rpm_limit("some_unknown_provider", minute)
        assert result is None

    def test_estimates_from_error_count_when_hit(self) -> None:
        minute = UsageWindow(request_count=8, error_count=2, quota_error_count=1)
        result = _estimate_rpm_limit("gemini", minute)
        # Hit at request_count + error_count = 10
        assert result == 10

    def test_prefers_observed_over_known_when_quota_hit(self) -> None:
        minute = UsageWindow(request_count=45, error_count=5, quota_error_count=2)
        result = _estimate_rpm_limit("gemini", minute)
        # Observed: 45 + 5 = 50 (overrides known 10)
        assert result == 50


class TestGenerateWarning:
    """Tests for _generate_warning function."""

    def test_no_warning_when_no_issues(self) -> None:
        minute = UsageWindow(request_count=2)
        hour = UsageWindow()
        day = UsageWindow()
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=10)
        assert result is None

    def test_warning_when_quota_hit_today(self) -> None:
        minute = UsageWindow()
        hour = UsageWindow()
        day = UsageWindow(quota_error_count=3)
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=10)
        assert result is not None
        assert "3 次" in result

    def test_warning_with_active_rate_limit(self) -> None:
        minute = UsageWindow(quota_error_count=1, last_retry_after=60)
        hour = UsageWindow()
        day = UsageWindow(quota_error_count=1)
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=10)
        assert result is not None
        assert "60 秒" in result

    def test_warning_with_active_rate_limit_no_retry_after(self) -> None:
        minute = UsageWindow(quota_error_count=1, last_retry_after=None)
        hour = UsageWindow()
        day = UsageWindow(quota_error_count=1)
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=10)
        assert result is not None
        assert "切換 Provider" in result

    def test_warning_when_approaching_rpm_limit(self) -> None:
        minute = UsageWindow(request_count=9)
        hour = UsageWindow()
        day = UsageWindow()
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=10)
        assert result is not None
        assert "RPM" in result
        assert "1" in result  # ~1 remaining

    def test_no_warning_when_well_below_limit(self) -> None:
        minute = UsageWindow(request_count=2)
        hour = UsageWindow()
        day = UsageWindow()
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=10)
        assert result is None

    def test_no_warning_without_estimated_rpm(self) -> None:
        minute = UsageWindow(request_count=100)
        hour = UsageWindow()
        day = UsageWindow()
        result = _generate_warning("gemini", minute, hour, day, estimated_rpm=None)
        assert result is None

"""Unit tests for STT route quota tracking helpers.

Tests the _track_success and _track_quota_error helper functions in
the STT routes, ensuring that usage is recorded correctly and
QuotaExceededError details are enriched with usage context.

Mirrors the structure of test_tts_route_quota_tracking.py.
"""

import uuid
from unittest.mock import patch

import pytest

from src.domain.errors import QuotaExceededError
from src.domain.services.usage_tracker import ProviderUsageTracker
from src.presentation.api.routes.stt import _track_quota_error, _track_success


@pytest.fixture()
def fresh_tracker() -> ProviderUsageTracker:
    """A fresh tracker instance for isolation between tests."""
    return ProviderUsageTracker()


@pytest.fixture()
def user_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


class TestTrackSuccess:
    """Tests for _track_success helper."""

    def test_records_request_for_authenticated_user(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """Authenticated user requests are tracked with their UUID string."""
        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_success(user_id, "whisper")

        usage = fresh_tracker.get_usage(str(user_id), "whisper")
        assert usage.minute_requests == 1
        assert usage.hour_requests == 1
        assert usage.day_requests == 1

    def test_records_request_for_anonymous_user(self, fresh_tracker: ProviderUsageTracker) -> None:
        """None user_id should be tracked as 'anonymous'."""
        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_success(None, "whisper")

        usage = fresh_tracker.get_usage("anonymous", "whisper")
        assert usage.minute_requests == 1

    def test_multiple_calls_accumulate(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """Multiple track_success calls accumulate in the tracker."""
        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            for _ in range(5):
                _track_success(user_id, "whisper")

        usage = fresh_tracker.get_usage(str(user_id), "whisper")
        assert usage.minute_requests == 5

    def test_different_providers_tracked_separately(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """Different providers are tracked independently."""
        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_success(user_id, "whisper")
            _track_success(user_id, "whisper")
            _track_success(user_id, "deepgram")

        whisper = fresh_tracker.get_usage(str(user_id), "whisper")
        deepgram = fresh_tracker.get_usage(str(user_id), "deepgram")
        assert whisper.minute_requests == 2
        assert deepgram.minute_requests == 1


class TestTrackQuotaError:
    """Tests for _track_quota_error helper."""

    def test_records_quota_error_in_tracker(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """Quota error is recorded with is_quota_error=True."""
        exc = QuotaExceededError(
            provider="whisper",
            retry_after=3600,
            original_error="quota exceeded",
        )

        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_quota_error(user_id, "whisper", exc)

        usage = fresh_tracker.get_usage(str(user_id), "whisper")
        assert usage.quota_hits_today == 1
        assert usage.last_retry_after == 3600

    def test_enriches_exception_details_with_usage_context(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """Exception details should contain usage_context after tracking."""
        exc = QuotaExceededError(
            provider="whisper",
            retry_after=3600,
            original_error="quota exceeded",
        )

        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            # Record some prior requests before the quota error
            fresh_tracker.record_request(str(user_id), "whisper")
            fresh_tracker.record_request(str(user_id), "whisper")
            fresh_tracker.record_request(str(user_id), "whisper")

            _track_quota_error(user_id, "whisper", exc)

        ctx = exc.details["usage_context"]
        assert ctx["minute_requests"] == 3
        assert ctx["hour_requests"] == 3
        assert ctx["day_requests"] == 3
        assert ctx["quota_hits_today"] == 1
        assert "estimated_rpm_limit" in ctx
        assert "usage_warning" in ctx

    def test_enriches_with_anonymous_user(self, fresh_tracker: ProviderUsageTracker) -> None:
        """Anonymous user quota errors are also enriched."""
        exc = QuotaExceededError(
            provider="whisper",
            original_error="quota exceeded",
        )

        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_quota_error(None, "whisper", exc)

        assert "usage_context" in exc.details
        ctx = exc.details["usage_context"]
        assert ctx["quota_hits_today"] == 1

    def test_retry_after_from_exception_is_recorded(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """retry_after from QuotaExceededError is passed to the tracker."""
        exc = QuotaExceededError(
            provider="whisper",
            retry_after=7200,
            original_error="rate limited",
        )

        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_quota_error(user_id, "whisper", exc)

        usage = fresh_tracker.get_usage(str(user_id), "whisper")
        assert usage.last_retry_after == 7200

    def test_no_retry_after_when_missing(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """When exception has no retry_after, tracker gets None."""
        exc = QuotaExceededError(
            provider="whisper",
            retry_after=None,
            original_error="quota exceeded",
        )
        # Override default_retry_after by removing it from details
        exc.details.pop("retry_after", None)

        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            _track_quota_error(user_id, "whisper", exc)

        usage = fresh_tracker.get_usage(str(user_id), "whisper")
        assert usage.last_retry_after is None

    def test_usage_context_includes_warning_after_multiple_hits(
        self, user_id: uuid.UUID, fresh_tracker: ProviderUsageTracker
    ) -> None:
        """After multiple quota hits, usage_context should include a warning."""
        with patch(
            "src.presentation.api.routes.stt.provider_usage_tracker",
            fresh_tracker,
        ):
            for _ in range(3):
                exc = QuotaExceededError(
                    provider="whisper",
                    retry_after=60,
                    original_error="quota exceeded",
                )
                fresh_tracker.record_request(str(user_id), "whisper")
                _track_quota_error(user_id, "whisper", exc)

        # The last exception should have enriched usage_context
        ctx = exc.details["usage_context"]
        assert ctx["quota_hits_today"] == 3
        # Warning should exist since we have quota hits today
        assert ctx["usage_warning"] is not None

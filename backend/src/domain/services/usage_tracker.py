"""Provider API usage tracker.

Tracks per-provider API request counts in memory to give users
visibility into their usage patterns even when providers don't
expose quota query APIs (e.g., Gemini).
"""

import contextlib
import logging
import time
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitHeaders:
    """Rate limit info captured from provider HTTP response headers."""

    limit: int | None = None
    remaining: int | None = None
    reset_at: float | None = None
    captured_at: float = field(default_factory=time.time)


def parse_rate_limit_headers(
    headers: Mapping[str, str],
    provider: str = "",
) -> RateLimitHeaders | None:
    """Parse rate limit headers from HTTP response.

    Handles standard patterns:
    - x-ratelimit-limit / ratelimit-limit
    - x-ratelimit-remaining / ratelimit-remaining
    - x-ratelimit-reset / ratelimit-reset

    Also handles ElevenLabs-specific headers (xi-ratelimit-*).

    Returns None if no rate limit headers are found.
    """
    # Normalize header keys to lowercase for case-insensitive matching
    try:
        lower_headers = {k.lower(): v for k, v in headers.items()}
    except (TypeError, AttributeError):
        return None

    limit: int | None = None
    remaining: int | None = None
    reset_at: float | None = None

    # Try standard patterns (most common first)
    for prefix in ("x-ratelimit-", "ratelimit-", "xi-ratelimit-"):
        if limit is None:
            raw = lower_headers.get(f"{prefix}limit")
            if raw is not None:
                with contextlib.suppress(ValueError, TypeError):
                    limit = int(raw)

        if remaining is None:
            raw = lower_headers.get(f"{prefix}remaining")
            if raw is not None:
                with contextlib.suppress(ValueError, TypeError):
                    remaining = int(raw)

        if reset_at is None:
            raw = lower_headers.get(f"{prefix}reset")
            if raw is not None:
                with contextlib.suppress(ValueError, TypeError):
                    reset_at = float(raw)

    # Nothing found
    if limit is None and remaining is None and reset_at is None:
        return None

    result = RateLimitHeaders(
        limit=limit,
        remaining=remaining,
        reset_at=reset_at,
    )
    logger.debug(
        "Parsed rate limit headers for %s: limit=%s, remaining=%s, reset_at=%s",
        provider or "unknown",
        limit,
        remaining,
        reset_at,
    )
    return result


@dataclass
class UsageWindow:
    """Usage counters for a time window."""

    request_count: int = 0
    error_count: int = 0
    quota_error_count: int = 0
    last_request_at: float = 0.0
    last_quota_error_at: float = 0.0
    last_retry_after: int | None = None
    window_start: float = field(default_factory=time.time)


@dataclass
class ProviderUsageSnapshot:
    """Snapshot of current usage for a provider."""

    provider: str
    minute_requests: int
    minute_errors: int
    hour_requests: int
    hour_errors: int
    day_requests: int
    day_errors: int
    quota_hits_today: int
    last_request_at: float | None
    last_quota_error_at: float | None
    last_retry_after: int | None
    estimated_rpm_limit: int | None
    usage_warning: str | None
    # Rate limit data from provider response headers
    provider_rpm_limit: int | None = None
    provider_rpm_remaining: int | None = None
    provider_rpm_reset_at: float | None = None
    rate_limit_data_age_seconds: float | None = None


class ProviderUsageTracker:
    """In-memory tracker for per-provider API usage.

    Tracks request counts per minute/hour/day to help estimate
    remaining quota for providers that don't expose usage APIs.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        # {user_id: {provider: {window_key: UsageWindow}}}
        self._usage: dict[str, dict[str, dict[str, UsageWindow]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        # {user_id: {provider: RateLimitHeaders}}
        self._rate_limits: dict[str, dict[str, RateLimitHeaders]] = defaultdict(dict)

    def _get_or_reset_window(
        self,
        windows: dict[str, UsageWindow],
        key: str,
        duration_seconds: float,
    ) -> UsageWindow:
        """Get a window, resetting it if expired."""
        now = time.time()
        window = windows.get(key)
        if window is None or (now - window.window_start) >= duration_seconds:
            windows[key] = UsageWindow(window_start=now)
        return windows[key]

    def record_request(self, user_id: str, provider: str) -> None:
        """Record a successful API request."""
        with self._lock:
            windows = self._usage[user_id][provider]
            now = time.time()

            for key, duration in [("minute", 60), ("hour", 3600), ("day", 86400)]:
                w = self._get_or_reset_window(windows, key, duration)
                w.request_count += 1
                w.last_request_at = now

    def record_rate_limit_headers(
        self,
        user_id: str,
        provider: str,
        headers: RateLimitHeaders,
    ) -> None:
        """Store the latest rate limit headers from a provider response."""
        with self._lock:
            self._rate_limits[user_id][provider] = headers

    def get_rate_limit_headers(
        self,
        user_id: str,
        provider: str,
    ) -> RateLimitHeaders | None:
        """Get the most recent rate limit headers for a provider."""
        with self._lock:
            return self._rate_limits.get(user_id, {}).get(provider)

    def record_error(
        self,
        user_id: str,
        provider: str,
        *,
        is_quota_error: bool = False,
        retry_after: int | None = None,
    ) -> None:
        """Record an API error."""
        with self._lock:
            windows = self._usage[user_id][provider]
            now = time.time()

            for key, duration in [("minute", 60), ("hour", 3600), ("day", 86400)]:
                w = self._get_or_reset_window(windows, key, duration)
                w.error_count += 1
                if is_quota_error:
                    w.quota_error_count += 1
                    w.last_quota_error_at = now
                    w.last_retry_after = retry_after

    def get_usage(self, user_id: str, provider: str) -> ProviderUsageSnapshot:
        """Get current usage snapshot for a provider."""
        with self._lock:
            windows = self._usage.get(user_id, {}).get(provider, {})
            now = time.time()

            def _get_valid(key: str, duration: float) -> UsageWindow:
                w = windows.get(key)
                if w and (now - w.window_start) < duration:
                    return w
                return UsageWindow()

            minute = _get_valid("minute", 60)
            hour = _get_valid("hour", 3600)
            day = _get_valid("day", 86400)

            # Estimate RPM limit based on when quota was hit
            estimated_rpm = _estimate_rpm_limit(provider, minute)

            # Generate warning
            warning = _generate_warning(provider, minute, hour, day, estimated_rpm)

            # Merge rate limit header data if available
            rl = self._rate_limits.get(user_id, {}).get(provider)
            rl_limit: int | None = None
            rl_remaining: int | None = None
            rl_reset_at: float | None = None
            rl_age: float | None = None
            if rl is not None:
                rl_limit = rl.limit
                rl_remaining = rl.remaining
                rl_reset_at = rl.reset_at
                rl_age = round(now - rl.captured_at, 1)

            return ProviderUsageSnapshot(
                provider=provider,
                minute_requests=minute.request_count,
                minute_errors=minute.error_count,
                hour_requests=hour.request_count,
                hour_errors=hour.error_count,
                day_requests=day.request_count,
                day_errors=day.error_count,
                quota_hits_today=day.quota_error_count,
                last_request_at=day.last_request_at or None,
                last_quota_error_at=day.last_quota_error_at or None,
                last_retry_after=day.last_retry_after,
                estimated_rpm_limit=estimated_rpm,
                usage_warning=warning,
                provider_rpm_limit=rl_limit,
                provider_rpm_remaining=rl_remaining,
                provider_rpm_reset_at=rl_reset_at,
                rate_limit_data_age_seconds=rl_age,
            )

    def get_all_usage(self, user_id: str) -> dict[str, ProviderUsageSnapshot]:
        """Get usage snapshots for all providers a user has used."""
        with self._lock:
            providers = list(self._usage.get(user_id, {}).keys())

        return {p: self.get_usage(user_id, p) for p in providers}


# Known free-tier RPM limits for estimation
_KNOWN_FREE_RPM: dict[str, int] = {
    "gemini": 10,  # Flash ~10, Pro ~5
    "openai": 3,
    "azure": 20,
    "anthropic": 5,
}


def _estimate_rpm_limit(provider: str, minute: UsageWindow) -> int | None:
    """Estimate RPM limit based on known tiers and observed behavior."""
    known = _KNOWN_FREE_RPM.get(provider)
    if minute.quota_error_count > 0 and minute.request_count > 0:
        # Hit the limit at this count — the limit is approximately this
        return minute.request_count + minute.error_count
    return known


def _generate_warning(
    _provider: str,
    minute: UsageWindow,
    _hour: UsageWindow,
    day: UsageWindow,
    estimated_rpm: int | None,
) -> str | None:
    """Generate a usage warning message if approaching limits."""
    if day.quota_error_count > 0:
        if minute.quota_error_count > 0:
            retry = minute.last_retry_after
            if retry:
                return f"目前已被限流，建議等待 {retry} 秒後再試"
            return "目前已被限流，請稍後再試或切換 Provider"

        return f"今日已觸發 {day.quota_error_count} 次配額限制，請注意用量"

    if estimated_rpm and minute.request_count >= estimated_rpm * 0.8:
        remaining = max(0, estimated_rpm - minute.request_count)
        return f"接近 RPM 限制，本分鐘剩餘約 {remaining} 次請求"

    return None


# Singleton instance
provider_usage_tracker = ProviderUsageTracker()

"""Provider API usage tracker.

Tracks per-provider API request counts in memory to give users
visibility into their usage patterns even when providers don't
expose quota query APIs (e.g., Gemini).
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


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

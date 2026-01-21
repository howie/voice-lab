"""Structured logging for interaction module.

T103: Implement structured logging with session_id, event_type, provider_name.
T104: API call counter metrics per provider.
T105: Error rate tracking and detailed error context.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from uuid import UUID

import structlog

# Configure structlog for JSON output
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


@dataclass
class ProviderMetrics:
    """Metrics for a single provider."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency_ms: float = 0.0
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.successful_calls == 0:
            return 0.0
        return self.total_latency_ms / self.successful_calls


class InteractionMetrics:
    """T104: API call counter metrics per provider.
    T105: Error rate tracking.
    """

    _instance: "InteractionMetrics | None" = None
    _lock = Lock()

    def __new__(cls) -> "InteractionMetrics":
        """Singleton pattern for metrics collection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize metrics storage."""
        self._providers: dict[str, ProviderMetrics] = defaultdict(ProviderMetrics)
        self._sessions: dict[UUID, dict[str, Any]] = {}
        self._lock = Lock()

    def record_call(
        self,
        provider: str,
        success: bool,
        latency_ms: float,
        error_context: dict[str, Any] | None = None,
    ) -> None:
        """Record an API call to a provider."""
        with self._lock:
            metrics = self._providers[provider]
            metrics.total_calls += 1
            if success:
                metrics.successful_calls += 1
                metrics.total_latency_ms += latency_ms
            else:
                metrics.failed_calls += 1
                if error_context:
                    metrics.errors.append(
                        {
                            "timestamp": time.time(),
                            "latency_ms": latency_ms,
                            **error_context,
                        }
                    )
                    # Keep only last 100 errors
                    if len(metrics.errors) > 100:
                        metrics.errors = metrics.errors[-100:]

    def start_session(self, session_id: UUID, mode: str) -> None:
        """Record session start."""
        with self._lock:
            self._sessions[session_id] = {
                "start_time": time.time(),
                "mode": mode,
                "turns": 0,
                "errors": 0,
            }

    def end_session(self, session_id: UUID) -> None:
        """Record session end."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["end_time"] = time.time()

    def record_turn(self, session_id: UUID) -> None:
        """Record a conversation turn."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["turns"] += 1

    def record_session_error(self, session_id: UUID) -> None:
        """Record an error in a session."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["errors"] += 1

    def get_provider_metrics(self, provider: str) -> dict[str, Any]:
        """Get metrics for a provider."""
        with self._lock:
            m = self._providers.get(provider)
            if not m:
                return {}
            return {
                "provider": provider,
                "total_calls": m.total_calls,
                "successful_calls": m.successful_calls,
                "failed_calls": m.failed_calls,
                "error_rate_pct": round(m.error_rate, 2),
                "avg_latency_ms": round(m.avg_latency_ms, 2),
                "recent_errors": m.errors[-10:],
            }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get metrics for all providers."""
        with self._lock:
            return {
                "providers": {
                    name: {
                        "total_calls": m.total_calls,
                        "successful_calls": m.successful_calls,
                        "failed_calls": m.failed_calls,
                        "error_rate_pct": round(m.error_rate, 2),
                        "avg_latency_ms": round(m.avg_latency_ms, 2),
                    }
                    for name, m in self._providers.items()
                },
                "active_sessions": len([s for s in self._sessions.values() if "end_time" not in s]),
                "total_sessions": len(self._sessions),
            }


class InteractionLogger:
    """T103: Structured logger for interaction events.

    Provides consistent logging with session context.
    """

    def __init__(self, session_id: UUID | None = None, mode: str | None = None) -> None:
        """Initialize logger with session context."""
        self._logger = structlog.get_logger("interaction")
        self._session_id = session_id
        self._mode = mode
        self._metrics = InteractionMetrics()

    def bind(self, **kwargs: Any) -> "InteractionLogger":
        """Create a new logger with additional context."""
        new_logger = InteractionLogger(self._session_id, self._mode)
        new_logger._logger = self._logger.bind(**kwargs)
        return new_logger

    def _log_context(self) -> dict[str, Any]:
        """Get base logging context."""
        ctx: dict[str, Any] = {}
        if self._session_id:
            ctx["session_id"] = str(self._session_id)
        if self._mode:
            ctx["mode"] = self._mode
        return ctx

    def session_started(self, session_id: UUID, mode: str, provider_config: dict[str, Any]) -> None:
        """Log session start event."""
        self._session_id = session_id
        self._mode = mode
        self._metrics.start_session(session_id, mode)
        self._logger.info(
            "session_started",
            event_type="session_started",
            session_id=str(session_id),
            mode=mode,
            provider_config=provider_config,
        )

    def session_ended(self, session_id: UUID, reason: str = "completed") -> None:
        """Log session end event."""
        self._metrics.end_session(session_id)
        self._logger.info(
            "session_ended",
            event_type="session_ended",
            session_id=str(session_id),
            reason=reason,
            **self._log_context(),
        )

    def turn_started(self, turn_number: int) -> None:
        """Log turn start event."""
        if self._session_id:
            self._metrics.record_turn(self._session_id)
        self._logger.info(
            "turn_started",
            event_type="turn_started",
            turn_number=turn_number,
            **self._log_context(),
        )

    def turn_completed(self, turn_number: int, latency_ms: int) -> None:
        """Log turn completion event."""
        self._logger.info(
            "turn_completed",
            event_type="turn_completed",
            turn_number=turn_number,
            latency_ms=latency_ms,
            **self._log_context(),
        )

    def turn_interrupted(self, turn_number: int, interrupt_latency_ms: int) -> None:
        """Log turn interruption event."""
        self._logger.info(
            "turn_interrupted",
            event_type="turn_interrupted",
            turn_number=turn_number,
            interrupt_latency_ms=interrupt_latency_ms,
            **self._log_context(),
        )

    def provider_call_started(self, provider: str, provider_type: str) -> float:
        """Log provider API call start. Returns start time."""
        self._logger.debug(
            "provider_call_started",
            event_type="provider_call_started",
            provider_name=provider,
            provider_type=provider_type,
            **self._log_context(),
        )
        return time.perf_counter()

    def provider_call_completed(
        self,
        provider: str,
        provider_type: str,
        start_time: float,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Log provider API call completion."""
        latency_ms = (time.perf_counter() - start_time) * 1000
        error_context = None

        if not success:
            error_context = {
                "provider": provider,
                "provider_type": provider_type,
                "error": error,
            }
            if self._session_id:
                self._metrics.record_session_error(self._session_id)

        self._metrics.record_call(
            provider=provider,
            success=success,
            latency_ms=latency_ms,
            error_context=error_context,
        )

        if success:
            self._logger.info(
                "provider_call_completed",
                event_type="provider_call_completed",
                provider_name=provider,
                provider_type=provider_type,
                latency_ms=round(latency_ms, 2),
                success=True,
                **self._log_context(),
            )
        else:
            self._logger.error(
                "provider_call_failed",
                event_type="provider_call_failed",
                provider_name=provider,
                provider_type=provider_type,
                latency_ms=round(latency_ms, 2),
                success=False,
                error=error,
                **self._log_context(),
            )

    def error(
        self,
        message: str,
        error_type: str | None = None,
        error_detail: str | None = None,
        **extra: Any,
    ) -> None:
        """Log an error with context."""
        if self._session_id:
            self._metrics.record_session_error(self._session_id)
        self._logger.error(
            message,
            event_type="error",
            error_type=error_type,
            error_detail=error_detail,
            **extra,
            **self._log_context(),
        )

    def warning(self, message: str, **extra: Any) -> None:
        """Log a warning with context."""
        self._logger.warning(message, event_type="warning", **extra, **self._log_context())

    def info(self, message: str, **extra: Any) -> None:
        """Log info with context."""
        self._logger.info(message, **extra, **self._log_context())

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug with context."""
        self._logger.debug(message, **extra, **self._log_context())


# Convenience function to get a logger
def get_interaction_logger(
    session_id: UUID | None = None, mode: str | None = None
) -> InteractionLogger:
    """Get an interaction logger with optional session context."""
    return InteractionLogger(session_id, mode)


# Convenience function to get metrics
def get_interaction_metrics() -> InteractionMetrics:
    """Get the metrics singleton."""
    return InteractionMetrics()

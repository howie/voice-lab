"""LatencyMetrics entity.

T010: Represents latency measurements for a conversation turn.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class LatencyMetrics:
    """Latency measurements for a conversation turn."""

    turn_id: UUID
    total_latency_ms: int
    id: UUID = field(default_factory=uuid4)
    stt_latency_ms: int | None = None  # Cascade mode only
    llm_ttft_ms: int | None = None  # Cascade mode: LLM time to first token
    tts_ttfb_ms: int | None = None  # Cascade mode: TTS time to first byte
    realtime_latency_ms: int | None = None  # Realtime mode only
    # T088: Track how long AI was speaking before being interrupted
    interrupt_latency_ms: int | None = None  # Time from response start to interrupt
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def for_realtime(cls, turn_id: UUID, total_ms: int, realtime_ms: int) -> "LatencyMetrics":
        """Create metrics for Realtime API mode."""
        return cls(
            turn_id=turn_id,
            total_latency_ms=total_ms,
            realtime_latency_ms=realtime_ms,
        )

    @classmethod
    def for_cascade(
        cls,
        turn_id: UUID,
        total_ms: int,
        stt_ms: int,
        llm_ttft_ms: int,
        tts_ttfb_ms: int,
    ) -> "LatencyMetrics":
        """Create metrics for Cascade mode."""
        return cls(
            turn_id=turn_id,
            total_latency_ms=total_ms,
            stt_latency_ms=stt_ms,
            llm_ttft_ms=llm_ttft_ms,
            tts_ttfb_ms=tts_ttfb_ms,
        )

    def is_cascade_mode(self) -> bool:
        """Check if metrics are for cascade mode."""
        return self.stt_latency_ms is not None

    def is_realtime_mode(self) -> bool:
        """Check if metrics are for realtime mode."""
        return self.realtime_latency_ms is not None

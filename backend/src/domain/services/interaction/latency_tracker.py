"""Latency tracking service.

T014: Tracks timing measurements for voice interaction turns.
"""

import time
from dataclasses import dataclass
from uuid import UUID

from src.domain.entities import LatencyMetrics


@dataclass
class LatencyMeasurement:
    """Tracks timing points for a single turn."""

    turn_id: UUID
    speech_started_at: float | None = None
    speech_ended_at: float | None = None
    stt_completed_at: float | None = None
    llm_first_token_at: float | None = None
    tts_first_byte_at: float | None = None
    response_started_at: float | None = None
    response_ended_at: float | None = None
    interrupted_at: float | None = None


class LatencyTracker:
    """Tracks and calculates latency metrics for voice interactions.

    Supports both Realtime API and Cascade modes with different
    measurement granularities.
    """

    def __init__(self) -> None:
        self._measurements: dict[UUID, LatencyMeasurement] = {}

    def start_turn(self, turn_id: UUID) -> None:
        """Start tracking a new turn."""
        self._measurements[turn_id] = LatencyMeasurement(turn_id=turn_id)

    def mark_speech_started(self, turn_id: UUID) -> None:
        """Mark when user speech was detected."""
        if turn_id in self._measurements:
            self._measurements[turn_id].speech_started_at = time.perf_counter()

    def mark_speech_ended(self, turn_id: UUID) -> None:
        """Mark when user speech ended."""
        if turn_id in self._measurements:
            self._measurements[turn_id].speech_ended_at = time.perf_counter()

    def mark_stt_completed(self, turn_id: UUID) -> None:
        """Mark when STT transcription completed (cascade mode)."""
        if turn_id in self._measurements:
            self._measurements[turn_id].stt_completed_at = time.perf_counter()

    def mark_llm_first_token(self, turn_id: UUID) -> None:
        """Mark when first LLM token received (cascade mode)."""
        if turn_id in self._measurements:
            self._measurements[turn_id].llm_first_token_at = time.perf_counter()

    def mark_tts_first_byte(self, turn_id: UUID) -> None:
        """Mark when first TTS audio byte received (cascade mode)."""
        if turn_id in self._measurements:
            self._measurements[turn_id].tts_first_byte_at = time.perf_counter()

    def mark_response_started(self, turn_id: UUID) -> None:
        """Mark when AI response playback started."""
        if turn_id in self._measurements:
            self._measurements[turn_id].response_started_at = time.perf_counter()

    def mark_response_ended(self, turn_id: UUID) -> None:
        """Mark when AI response completed."""
        if turn_id in self._measurements:
            self._measurements[turn_id].response_ended_at = time.perf_counter()

    def mark_interrupted(self, turn_id: UUID) -> None:
        """Mark when response was interrupted."""
        if turn_id in self._measurements:
            self._measurements[turn_id].interrupted_at = time.perf_counter()

    def get_metrics_realtime(self, turn_id: UUID) -> LatencyMetrics | None:
        """Calculate metrics for Realtime API mode.

        Total latency = time from speech_ended to response_started
        """
        m = self._measurements.get(turn_id)
        if m is None or m.speech_ended_at is None or m.response_started_at is None:
            return None

        total_ms = int((m.response_started_at - m.speech_ended_at) * 1000)
        realtime_ms = total_ms  # In realtime mode, this is the same

        # T088: Calculate interrupt latency if turn was interrupted
        interrupt_ms = None
        if m.interrupted_at and m.response_started_at:
            interrupt_ms = int((m.interrupted_at - m.response_started_at) * 1000)

        metrics = LatencyMetrics.for_realtime(
            turn_id=turn_id,
            total_ms=total_ms,
            realtime_ms=realtime_ms,
        )
        metrics.interrupt_latency_ms = interrupt_ms
        return metrics

    def get_metrics_cascade(self, turn_id: UUID) -> LatencyMetrics | None:
        """Calculate metrics for Cascade mode.

        Returns segment latencies: STT, LLM TTFT, TTS TTFB
        """
        m = self._measurements.get(turn_id)
        if m is None or m.speech_ended_at is None:
            return None

        # Calculate segment latencies
        stt_ms = None
        if m.stt_completed_at and m.speech_ended_at:
            stt_ms = int((m.stt_completed_at - m.speech_ended_at) * 1000)

        llm_ttft_ms = None
        if m.llm_first_token_at and m.stt_completed_at:
            llm_ttft_ms = int((m.llm_first_token_at - m.stt_completed_at) * 1000)

        tts_ttfb_ms = None
        if m.tts_first_byte_at and m.llm_first_token_at:
            tts_ttfb_ms = int((m.tts_first_byte_at - m.llm_first_token_at) * 1000)

        # Total latency
        total_ms = 0
        if m.response_started_at and m.speech_ended_at:
            total_ms = int((m.response_started_at - m.speech_ended_at) * 1000)

        # T088: Calculate interrupt latency if turn was interrupted
        interrupt_ms = None
        if m.interrupted_at and m.response_started_at:
            interrupt_ms = int((m.interrupted_at - m.response_started_at) * 1000)

        metrics = LatencyMetrics.for_cascade(
            turn_id=turn_id,
            total_ms=total_ms,
            stt_ms=stt_ms or 0,
            llm_ttft_ms=llm_ttft_ms or 0,
            tts_ttfb_ms=tts_ttfb_ms or 0,
        )
        metrics.interrupt_latency_ms = interrupt_ms
        return metrics

    def clear_turn(self, turn_id: UUID) -> None:
        """Remove measurement data for a turn."""
        self._measurements.pop(turn_id, None)

    def clear_all(self) -> None:
        """Clear all measurements."""
        self._measurements.clear()

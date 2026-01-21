"""Unit tests for LatencyTracker.

T112: Unit tests to ensure 80% coverage on domain/services.
"""

from unittest.mock import patch
from uuid import uuid4

from src.domain.services.interaction.latency_tracker import (
    LatencyMeasurement,
    LatencyTracker,
)


class TestLatencyMeasurement:
    """Test LatencyMeasurement dataclass."""

    def test_default_values(self) -> None:
        """All optional fields default to None."""
        turn_id = uuid4()
        m = LatencyMeasurement(turn_id=turn_id)

        assert m.turn_id == turn_id
        assert m.speech_started_at is None
        assert m.speech_ended_at is None
        assert m.stt_completed_at is None
        assert m.llm_first_token_at is None
        assert m.tts_first_byte_at is None
        assert m.response_started_at is None
        assert m.response_ended_at is None
        assert m.interrupted_at is None

    def test_with_values(self) -> None:
        """Can set all values."""
        turn_id = uuid4()
        m = LatencyMeasurement(
            turn_id=turn_id,
            speech_started_at=1.0,
            speech_ended_at=2.0,
            stt_completed_at=2.5,
            llm_first_token_at=3.0,
            tts_first_byte_at=3.5,
            response_started_at=4.0,
            response_ended_at=5.0,
            interrupted_at=4.5,
        )

        assert m.speech_started_at == 1.0
        assert m.speech_ended_at == 2.0
        assert m.stt_completed_at == 2.5
        assert m.llm_first_token_at == 3.0
        assert m.tts_first_byte_at == 3.5
        assert m.response_started_at == 4.0
        assert m.response_ended_at == 5.0
        assert m.interrupted_at == 4.5


class TestLatencyTrackerStartTurn:
    """Test LatencyTracker.start_turn."""

    def test_start_turn_creates_measurement(self) -> None:
        """start_turn creates a new measurement."""
        tracker = LatencyTracker()
        turn_id = uuid4()

        tracker.start_turn(turn_id)

        assert turn_id in tracker._measurements
        assert tracker._measurements[turn_id].turn_id == turn_id

    def test_start_turn_multiple_turns(self) -> None:
        """Can track multiple turns simultaneously."""
        tracker = LatencyTracker()
        turn1 = uuid4()
        turn2 = uuid4()

        tracker.start_turn(turn1)
        tracker.start_turn(turn2)

        assert turn1 in tracker._measurements
        assert turn2 in tracker._measurements


class TestLatencyTrackerMarkPoints:
    """Test marking timing points."""

    def test_mark_speech_started(self) -> None:
        """mark_speech_started sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=10.0):
            tracker.mark_speech_started(turn_id)

        assert tracker._measurements[turn_id].speech_started_at == 10.0

    def test_mark_speech_started_unknown_turn_ignored(self) -> None:
        """mark_speech_started with unknown turn does nothing."""
        tracker = LatencyTracker()
        unknown_turn = uuid4()

        tracker.mark_speech_started(unknown_turn)  # Should not raise

        assert unknown_turn not in tracker._measurements

    def test_mark_speech_ended(self) -> None:
        """mark_speech_ended sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=12.0):
            tracker.mark_speech_ended(turn_id)

        assert tracker._measurements[turn_id].speech_ended_at == 12.0

    def test_mark_speech_ended_unknown_turn_ignored(self) -> None:
        """mark_speech_ended with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_speech_ended(uuid4())  # Should not raise

    def test_mark_stt_completed(self) -> None:
        """mark_stt_completed sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=13.0):
            tracker.mark_stt_completed(turn_id)

        assert tracker._measurements[turn_id].stt_completed_at == 13.0

    def test_mark_stt_completed_unknown_turn_ignored(self) -> None:
        """mark_stt_completed with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_stt_completed(uuid4())  # Should not raise

    def test_mark_llm_first_token(self) -> None:
        """mark_llm_first_token sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=14.0):
            tracker.mark_llm_first_token(turn_id)

        assert tracker._measurements[turn_id].llm_first_token_at == 14.0

    def test_mark_llm_first_token_unknown_turn_ignored(self) -> None:
        """mark_llm_first_token with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_llm_first_token(uuid4())  # Should not raise

    def test_mark_tts_first_byte(self) -> None:
        """mark_tts_first_byte sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=15.0):
            tracker.mark_tts_first_byte(turn_id)

        assert tracker._measurements[turn_id].tts_first_byte_at == 15.0

    def test_mark_tts_first_byte_unknown_turn_ignored(self) -> None:
        """mark_tts_first_byte with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_tts_first_byte(uuid4())  # Should not raise

    def test_mark_response_started(self) -> None:
        """mark_response_started sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=16.0):
            tracker.mark_response_started(turn_id)

        assert tracker._measurements[turn_id].response_started_at == 16.0

    def test_mark_response_started_unknown_turn_ignored(self) -> None:
        """mark_response_started with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_response_started(uuid4())  # Should not raise

    def test_mark_response_ended(self) -> None:
        """mark_response_ended sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=20.0):
            tracker.mark_response_ended(turn_id)

        assert tracker._measurements[turn_id].response_ended_at == 20.0

    def test_mark_response_ended_unknown_turn_ignored(self) -> None:
        """mark_response_ended with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_response_ended(uuid4())  # Should not raise

    def test_mark_interrupted(self) -> None:
        """mark_interrupted sets timestamp."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        with patch("time.perf_counter", return_value=17.0):
            tracker.mark_interrupted(turn_id)

        assert tracker._measurements[turn_id].interrupted_at == 17.0

    def test_mark_interrupted_unknown_turn_ignored(self) -> None:
        """mark_interrupted with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.mark_interrupted(uuid4())  # Should not raise


class TestLatencyTrackerGetMetricsRealtime:
    """Test get_metrics_realtime."""

    def test_returns_none_for_unknown_turn(self) -> None:
        """Returns None for unknown turn."""
        tracker = LatencyTracker()
        assert tracker.get_metrics_realtime(uuid4()) is None

    def test_returns_none_without_speech_ended(self) -> None:
        """Returns None if speech_ended is not set."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].response_started_at = 10.0

        assert tracker.get_metrics_realtime(turn_id) is None

    def test_returns_none_without_response_started(self) -> None:
        """Returns None if response_started is not set."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 5.0

        assert tracker.get_metrics_realtime(turn_id) is None

    def test_calculates_total_latency(self) -> None:
        """Calculates total latency correctly."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.5

        metrics = tracker.get_metrics_realtime(turn_id)

        assert metrics is not None
        assert metrics.total_latency_ms == 500  # 0.5 seconds = 500ms
        assert metrics.realtime_latency_ms == 500

    def test_calculates_interrupt_latency(self) -> None:
        """T088: Calculates interrupt latency when interrupted."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.5
        tracker._measurements[turn_id].interrupted_at = 2.0

        metrics = tracker.get_metrics_realtime(turn_id)

        assert metrics is not None
        assert metrics.interrupt_latency_ms == 500  # 2.0 - 1.5 = 0.5s = 500ms

    def test_no_interrupt_latency_when_not_interrupted(self) -> None:
        """No interrupt latency when not interrupted."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.5

        metrics = tracker.get_metrics_realtime(turn_id)

        assert metrics is not None
        assert metrics.interrupt_latency_ms is None


class TestLatencyTrackerGetMetricsCascade:
    """Test get_metrics_cascade."""

    def test_returns_none_for_unknown_turn(self) -> None:
        """Returns None for unknown turn."""
        tracker = LatencyTracker()
        assert tracker.get_metrics_cascade(uuid4()) is None

    def test_returns_none_without_speech_ended(self) -> None:
        """Returns None if speech_ended is not set."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)

        assert tracker.get_metrics_cascade(turn_id) is None

    def test_calculates_stt_latency(self) -> None:
        """Calculates STT latency correctly."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        # Use values that don't cause floating point precision issues
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].stt_completed_at = 1.25
        tracker._measurements[turn_id].response_started_at = 2.0

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.stt_latency_ms == 250  # 0.25s = 250ms

    def test_calculates_llm_ttft(self) -> None:
        """Calculates LLM TTFT correctly."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].stt_completed_at = 1.2
        tracker._measurements[turn_id].llm_first_token_at = 1.5
        tracker._measurements[turn_id].response_started_at = 2.0

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.llm_ttft_ms == 300  # 1.5 - 1.2 = 0.3s = 300ms

    def test_calculates_tts_ttfb(self) -> None:
        """Calculates TTS TTFB correctly."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].stt_completed_at = 1.2
        tracker._measurements[turn_id].llm_first_token_at = 1.5
        tracker._measurements[turn_id].tts_first_byte_at = 1.8
        tracker._measurements[turn_id].response_started_at = 2.0

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.tts_ttfb_ms == 300  # 1.8 - 1.5 = 0.3s = 300ms

    def test_calculates_total_latency(self) -> None:
        """Calculates total latency correctly."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 2.5

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.total_latency_ms == 1500  # 1.5s = 1500ms

    def test_total_latency_zero_without_response_started(self) -> None:
        """Total latency is 0 if response not started."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.total_latency_ms == 0

    def test_missing_segments_default_to_zero(self) -> None:
        """Missing segment latencies default to 0."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 2.0

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.stt_latency_ms == 0
        assert metrics.llm_ttft_ms == 0
        assert metrics.tts_ttfb_ms == 0

    def test_calculates_interrupt_latency(self) -> None:
        """T088: Calculates interrupt latency when interrupted."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.5
        tracker._measurements[turn_id].interrupted_at = 2.0

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.interrupt_latency_ms == 500

    def test_no_interrupt_latency_when_not_interrupted(self) -> None:
        """No interrupt latency when not interrupted."""
        tracker = LatencyTracker()
        turn_id = uuid4()
        tracker.start_turn(turn_id)
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.5

        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.interrupt_latency_ms is None


class TestLatencyTrackerClear:
    """Test clearing measurements."""

    def test_clear_turn(self) -> None:
        """clear_turn removes specific measurement."""
        tracker = LatencyTracker()
        turn1 = uuid4()
        turn2 = uuid4()
        tracker.start_turn(turn1)
        tracker.start_turn(turn2)

        tracker.clear_turn(turn1)

        assert turn1 not in tracker._measurements
        assert turn2 in tracker._measurements

    def test_clear_turn_unknown_turn_ignored(self) -> None:
        """clear_turn with unknown turn does nothing."""
        tracker = LatencyTracker()
        tracker.clear_turn(uuid4())  # Should not raise

    def test_clear_all(self) -> None:
        """clear_all removes all measurements."""
        tracker = LatencyTracker()
        tracker.start_turn(uuid4())
        tracker.start_turn(uuid4())
        tracker.start_turn(uuid4())

        tracker.clear_all()

        assert len(tracker._measurements) == 0


class TestLatencyTrackerIntegration:
    """Integration tests for full workflow."""

    def test_realtime_mode_workflow(self) -> None:
        """Test full realtime mode workflow."""
        tracker = LatencyTracker()
        turn_id = uuid4()

        # Start turn
        tracker.start_turn(turn_id)

        # Simulate timing events
        tracker._measurements[turn_id].speech_started_at = 0.0
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.3
        tracker._measurements[turn_id].response_ended_at = 3.0

        # Get metrics
        metrics = tracker.get_metrics_realtime(turn_id)

        assert metrics is not None
        assert metrics.total_latency_ms == 300
        assert metrics.turn_id == turn_id

    def test_cascade_mode_workflow(self) -> None:
        """Test full cascade mode workflow."""
        tracker = LatencyTracker()
        turn_id = uuid4()

        # Start turn
        tracker.start_turn(turn_id)

        # Simulate timing events using integer-convertible values
        tracker._measurements[turn_id].speech_started_at = 0.0
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].stt_completed_at = 1.25
        tracker._measurements[turn_id].llm_first_token_at = 1.5
        tracker._measurements[turn_id].tts_first_byte_at = 1.75
        tracker._measurements[turn_id].response_started_at = 2.0
        tracker._measurements[turn_id].response_ended_at = 5.0

        # Get metrics
        metrics = tracker.get_metrics_cascade(turn_id)

        assert metrics is not None
        assert metrics.total_latency_ms == 1000
        assert metrics.stt_latency_ms == 250  # 1.25 - 1.0 = 0.25s
        assert metrics.llm_ttft_ms == 250  # 1.5 - 1.25 = 0.25s
        assert metrics.tts_ttfb_ms == 250  # 1.75 - 1.5 = 0.25s
        assert metrics.turn_id == turn_id

    def test_interrupted_turn_workflow(self) -> None:
        """Test workflow with interruption."""
        tracker = LatencyTracker()
        turn_id = uuid4()

        # Start turn
        tracker.start_turn(turn_id)

        # Simulate timing events with interruption
        tracker._measurements[turn_id].speech_ended_at = 1.0
        tracker._measurements[turn_id].response_started_at = 1.5
        tracker._measurements[turn_id].interrupted_at = 2.0

        # Get metrics
        metrics = tracker.get_metrics_realtime(turn_id)

        assert metrics is not None
        assert metrics.total_latency_ms == 500
        assert metrics.interrupt_latency_ms == 500

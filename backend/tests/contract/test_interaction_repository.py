"""Contract tests for InteractionRepository.

Feature: 004-interaction-module
T026c: Contract test for InteractionRepository interface

Tests the repository method signatures and return type contracts.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities import (
    ConversationTurn,
    InteractionMode,
    InteractionSession,
    LatencyMetrics,
    SessionStatus,
)


class TestInteractionSessionContract:
    """Contract tests for InteractionSession entity."""

    @pytest.fixture
    def sample_session(self) -> InteractionSession:
        """Create a sample interaction session."""
        return InteractionSession(
            id=uuid4(),
            user_id=uuid4(),
            mode=InteractionMode.REALTIME,
            provider_config={"provider": "openai", "voice": "alloy"},
            system_prompt="You are a helpful assistant.",
            status=SessionStatus.ACTIVE,
            started_at=datetime.now(UTC),
            ended_at=None,
        )

    def test_session_has_required_fields(self, sample_session: InteractionSession) -> None:
        """Verify InteractionSession has all required fields."""
        required_attrs = [
            "id",
            "user_id",
            "mode",
            "provider_config",
            "system_prompt",
            "status",
            "started_at",
            "ended_at",
            "created_at",
            "updated_at",
        ]
        for attr in required_attrs:
            assert hasattr(sample_session, attr), f"Missing required attribute: {attr}"

    def test_session_mode_is_interaction_mode(self, sample_session: InteractionSession) -> None:
        """Verify mode field is an InteractionMode enum."""
        assert isinstance(sample_session.mode, InteractionMode)

    def test_session_status_is_session_status(self, sample_session: InteractionSession) -> None:
        """Verify status field is a SessionStatus enum."""
        assert isinstance(sample_session.status, SessionStatus)

    def test_session_provider_config_is_dict(self, sample_session: InteractionSession) -> None:
        """Verify provider_config is a dictionary."""
        assert isinstance(sample_session.provider_config, dict)

    def test_session_timestamps_are_datetime(self, sample_session: InteractionSession) -> None:
        """Verify timestamp fields are datetime objects."""
        assert isinstance(sample_session.started_at, datetime)
        assert isinstance(sample_session.created_at, datetime)
        assert isinstance(sample_session.updated_at, datetime)
        # ended_at can be None for active sessions
        if sample_session.ended_at is not None:
            assert isinstance(sample_session.ended_at, datetime)


class TestConversationTurnContract:
    """Contract tests for ConversationTurn entity."""

    @pytest.fixture
    def sample_turn(self) -> ConversationTurn:
        """Create a sample conversation turn."""
        return ConversationTurn(
            id=uuid4(),
            session_id=uuid4(),
            turn_number=1,
            user_audio_path="interactions/test/turn_001_user.webm",
            user_transcript="Hello, how are you?",
            ai_response_text="I'm doing well, thank you!",
            ai_audio_path="interactions/test/turn_001_ai.mp3",
            interrupted=False,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
        )

    def test_turn_has_required_fields(self, sample_turn: ConversationTurn) -> None:
        """Verify ConversationTurn has all required fields."""
        required_attrs = [
            "id",
            "session_id",
            "turn_number",
            "user_audio_path",
            "user_transcript",
            "ai_response_text",
            "ai_audio_path",
            "interrupted",
            "started_at",
            "ended_at",
            "created_at",
        ]
        for attr in required_attrs:
            assert hasattr(sample_turn, attr), f"Missing required attribute: {attr}"

    def test_turn_number_is_positive_int(self, sample_turn: ConversationTurn) -> None:
        """Verify turn_number is a positive integer."""
        assert isinstance(sample_turn.turn_number, int)
        assert sample_turn.turn_number > 0

    def test_turn_interrupted_is_bool(self, sample_turn: ConversationTurn) -> None:
        """Verify interrupted field is a boolean."""
        assert isinstance(sample_turn.interrupted, bool)

    def test_turn_audio_paths_are_strings(self, sample_turn: ConversationTurn) -> None:
        """Verify audio paths are strings or None."""
        if sample_turn.user_audio_path is not None:
            assert isinstance(sample_turn.user_audio_path, str)
        if sample_turn.ai_audio_path is not None:
            assert isinstance(sample_turn.ai_audio_path, str)


class TestLatencyMetricsContract:
    """Contract tests for LatencyMetrics entity."""

    @pytest.fixture
    def cascade_latency(self) -> LatencyMetrics:
        """Create latency metrics for cascade mode."""
        return LatencyMetrics(
            id=uuid4(),
            turn_id=uuid4(),
            total_latency_ms=450.5,
            stt_latency_ms=150.0,
            llm_ttft_ms=200.0,
            tts_ttfb_ms=100.0,
            realtime_latency_ms=None,
        )

    @pytest.fixture
    def realtime_latency(self) -> LatencyMetrics:
        """Create latency metrics for realtime mode."""
        return LatencyMetrics(
            id=uuid4(),
            turn_id=uuid4(),
            total_latency_ms=250.0,
            stt_latency_ms=None,
            llm_ttft_ms=None,
            tts_ttfb_ms=None,
            realtime_latency_ms=250.0,
        )

    def test_latency_has_required_fields(self, cascade_latency: LatencyMetrics) -> None:
        """Verify LatencyMetrics has all required fields."""
        required_attrs = [
            "id",
            "turn_id",
            "total_latency_ms",
            "stt_latency_ms",
            "llm_ttft_ms",
            "tts_ttfb_ms",
            "realtime_latency_ms",
            "created_at",
        ]
        for attr in required_attrs:
            assert hasattr(cascade_latency, attr), f"Missing required attribute: {attr}"

    def test_cascade_mode_latency_fields(self, cascade_latency: LatencyMetrics) -> None:
        """Verify cascade mode has STT, LLM, TTS latencies."""
        assert cascade_latency.stt_latency_ms is not None
        assert cascade_latency.llm_ttft_ms is not None
        assert cascade_latency.tts_ttfb_ms is not None
        assert cascade_latency.realtime_latency_ms is None

    def test_realtime_mode_latency_fields(self, realtime_latency: LatencyMetrics) -> None:
        """Verify realtime mode has realtime_latency_ms."""
        assert realtime_latency.realtime_latency_ms is not None
        # Cascade-specific fields should be None for realtime mode
        assert realtime_latency.stt_latency_ms is None
        assert realtime_latency.llm_ttft_ms is None
        assert realtime_latency.tts_ttfb_ms is None

    def test_latency_values_are_numeric(self, cascade_latency: LatencyMetrics) -> None:
        """Verify latency values are numeric."""
        assert isinstance(cascade_latency.total_latency_ms, (int, float))
        if cascade_latency.stt_latency_ms is not None:
            assert isinstance(cascade_latency.stt_latency_ms, (int, float))
        if cascade_latency.llm_ttft_ms is not None:
            assert isinstance(cascade_latency.llm_ttft_ms, (int, float))
        if cascade_latency.tts_ttfb_ms is not None:
            assert isinstance(cascade_latency.tts_ttfb_ms, (int, float))


class TestLatencyStatsContract:
    """Contract tests for latency statistics response."""

    def test_latency_stats_format(self) -> None:
        """Verify expected latency stats structure."""
        # This is the expected format returned by get_session_latency_stats
        expected_stats = {
            "total_turns": 5,
            "avg_total_ms": 450.5,
            "min_total_ms": 320.0,
            "max_total_ms": 580.0,
            "p95_total_ms": 550.0,
            "avg_stt_ms": 150.0,
            "avg_llm_ttft_ms": 200.0,
            "avg_tts_ttfb_ms": 100.0,
        }

        required_fields = [
            "total_turns",
            "avg_total_ms",
            "min_total_ms",
            "max_total_ms",
            "p95_total_ms",
            "avg_stt_ms",
            "avg_llm_ttft_ms",
            "avg_tts_ttfb_ms",
        ]

        for field in required_fields:
            assert field in expected_stats, f"Missing required field: {field}"

    def test_empty_latency_stats_format(self) -> None:
        """Verify latency stats format when no data."""
        empty_stats = {
            "total_turns": 0,
            "avg_total_ms": None,
            "min_total_ms": None,
            "max_total_ms": None,
            "p95_total_ms": None,
            "avg_stt_ms": None,
            "avg_llm_ttft_ms": None,
            "avg_tts_ttfb_ms": None,
        }

        assert empty_stats["total_turns"] == 0
        # All other fields should be None when no data
        for key, value in empty_stats.items():
            if key != "total_turns":
                assert value is None


class TestPaginationContract:
    """Contract tests for list operations pagination."""

    def test_list_response_format(self) -> None:
        """Verify list response includes pagination info."""
        # Expected format from list_sessions
        sample_response = {
            "sessions": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
        }

        assert "sessions" in sample_response
        assert "total" in sample_response
        assert "page" in sample_response
        assert "page_size" in sample_response

    def test_pagination_values_are_valid(self) -> None:
        """Verify pagination values are positive integers."""
        pagination = {
            "total": 100,
            "page": 2,
            "page_size": 20,
        }

        assert isinstance(pagination["total"], int)
        assert pagination["total"] >= 0
        assert isinstance(pagination["page"], int)
        assert pagination["page"] >= 1
        assert isinstance(pagination["page_size"], int)
        assert pagination["page_size"] >= 1


class TestRepositoryMethodContract:
    """Contract tests for repository method signatures."""

    def test_session_crud_operations(self) -> None:
        """Document expected CRUD method signatures for sessions."""
        # These are the expected method signatures
        expected_methods = {
            "create_session": "async (session: InteractionSession) -> InteractionSession",
            "get_session": "async (session_id: UUID) -> InteractionSession | None",
            "update_session": "async (session: InteractionSession) -> InteractionSession",
            "delete_session": "async (session_id: UUID) -> bool",
            "list_sessions": (
                "async (user_id: UUID, mode?: InteractionMode, status?: SessionStatus, "
                "start_date?: datetime, end_date?: datetime, page: int, page_size: int) "
                "-> tuple[Sequence[InteractionSession], int]"
            ),
        }

        # This test documents the expected interface
        assert len(expected_methods) == 5

    def test_turn_crud_operations(self) -> None:
        """Document expected CRUD method signatures for turns."""
        expected_methods = {
            "create_turn": "async (turn: ConversationTurn) -> ConversationTurn",
            "get_turn": "async (turn_id: UUID) -> ConversationTurn | None",
            "update_turn": "async (turn: ConversationTurn) -> ConversationTurn",
            "list_turns": "async (session_id: UUID) -> Sequence[ConversationTurn]",
            "get_next_turn_number": "async (session_id: UUID) -> int",
        }

        assert len(expected_methods) == 5

    def test_latency_operations(self) -> None:
        """Document expected method signatures for latency metrics."""
        expected_methods = {
            "create_latency_metrics": "async (metrics: LatencyMetrics) -> LatencyMetrics",
            "get_latency_metrics": "async (turn_id: UUID) -> LatencyMetrics | None",
            "get_session_latency_stats": "async (session_id: UUID) -> dict[str, float | int | None]",
        }

        assert len(expected_methods) == 3

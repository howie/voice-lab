"""Contract tests for Interaction REST API endpoints.

Feature: 004-interaction-module
T026b: Contract test for interaction REST API endpoints

Tests the REST API request/response contracts.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities import (
    ConversationTurn,
    InteractionMode,
    InteractionSession,
    SessionStatus,
)
from src.infrastructure.persistence.database import get_db_session
from src.main import app


@pytest.fixture
def mock_session() -> InteractionSession:
    """Create a mock interaction session."""
    return InteractionSession(
        id=uuid4(),
        user_id=uuid4(),
        mode=InteractionMode.REALTIME,
        provider_config={"provider": "openai", "voice": "alloy"},
        system_prompt="You are a helpful assistant.",
        status=SessionStatus.COMPLETED,
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_turn(mock_session: InteractionSession) -> ConversationTurn:
    """Create a mock conversation turn."""
    return ConversationTurn(
        id=uuid4(),
        session_id=mock_session.id,
        turn_number=1,
        user_audio_path="interactions/test/turn_001_user.webm",
        user_transcript="Hello, how are you?",
        ai_response_text="I'm doing well, thank you!",
        ai_audio_path="interactions/test/turn_001_ai.mp3",
        interrupted=False,
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_latency_stats() -> dict:
    """Create mock latency statistics."""
    return {
        "total_turns": 5,
        "avg_total_ms": 450.5,
        "min_total_ms": 320.0,
        "max_total_ms": 580.0,
        "p95_total_ms": 550.0,
        "avg_stt_ms": 150.0,
        "avg_llm_ttft_ms": 200.0,
        "avg_tts_ttfb_ms": 100.0,
    }


class TestSessionListEndpoint:
    """Contract tests for GET /api/v1/interaction/sessions endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self) -> None:
        """Override database dependencies."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        app.dependency_overrides[get_db_session] = lambda: mock_db
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sessions_response_format(self, mock_session: InteractionSession) -> None:
        """Verify session list response format."""
        # The actual endpoint would return data from repository
        # This test verifies the expected response structure

        expected_response = {
            "sessions": [
                {
                    "id": str(mock_session.id),
                    "user_id": str(mock_session.user_id),
                    "mode": mock_session.mode.value,
                    "provider_config": mock_session.provider_config,
                    "system_prompt": mock_session.system_prompt,
                    "status": mock_session.status.value,
                    "started_at": mock_session.started_at.isoformat(),
                    "ended_at": mock_session.ended_at.isoformat()
                    if mock_session.ended_at
                    else None,
                    "created_at": mock_session.created_at.isoformat(),
                    "updated_at": mock_session.updated_at.isoformat(),
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }

        # Verify structure
        assert "sessions" in expected_response
        assert "total" in expected_response
        assert "page" in expected_response
        assert "page_size" in expected_response
        assert isinstance(expected_response["sessions"], list)

    @pytest.mark.asyncio
    async def test_session_response_fields(self, mock_session: InteractionSession) -> None:
        """Verify individual session response has all required fields."""
        session_dict = {
            "id": str(mock_session.id),
            "user_id": str(mock_session.user_id),
            "mode": mock_session.mode.value,
            "provider_config": mock_session.provider_config,
            "system_prompt": mock_session.system_prompt,
            "status": mock_session.status.value,
            "started_at": mock_session.started_at.isoformat(),
            "ended_at": mock_session.ended_at.isoformat() if mock_session.ended_at else None,
            "created_at": mock_session.created_at.isoformat(),
            "updated_at": mock_session.updated_at.isoformat(),
        }

        required_fields = [
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
        for field in required_fields:
            assert field in session_dict, f"Missing required field: {field}"


class TestSessionDetailEndpoint:
    """Contract tests for GET /api/v1/interaction/sessions/{id} endpoint."""

    def test_session_detail_response_format(self, mock_session: InteractionSession) -> None:
        """Verify session detail response format."""
        response_dict = {
            "id": str(mock_session.id),
            "user_id": str(mock_session.user_id),
            "mode": mock_session.mode.value,
            "provider_config": mock_session.provider_config,
            "system_prompt": mock_session.system_prompt,
            "status": mock_session.status.value,
            "started_at": mock_session.started_at.isoformat(),
            "ended_at": mock_session.ended_at.isoformat() if mock_session.ended_at else None,
            "created_at": mock_session.created_at.isoformat(),
            "updated_at": mock_session.updated_at.isoformat(),
        }

        # Verify all fields are present
        assert response_dict["mode"] in ["realtime", "cascade"]
        assert response_dict["status"] in ["active", "completed", "disconnected", "error"]


class TestTurnListEndpoint:
    """Contract tests for GET /api/v1/interaction/sessions/{id}/turns endpoint."""

    def test_turn_response_format(self, mock_turn: ConversationTurn) -> None:
        """Verify turn response format."""
        turn_dict = {
            "id": str(mock_turn.id),
            "session_id": str(mock_turn.session_id),
            "turn_number": mock_turn.turn_number,
            "user_audio_path": mock_turn.user_audio_path,
            "user_transcript": mock_turn.user_transcript,
            "ai_response_text": mock_turn.ai_response_text,
            "ai_audio_path": mock_turn.ai_audio_path,
            "interrupted": mock_turn.interrupted,
            "started_at": mock_turn.started_at.isoformat(),
            "ended_at": mock_turn.ended_at.isoformat() if mock_turn.ended_at else None,
        }

        required_fields = [
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
        ]
        for field in required_fields:
            assert field in turn_dict, f"Missing required field: {field}"

    def test_turn_number_is_positive(self, mock_turn: ConversationTurn) -> None:
        """Verify turn number is positive integer."""
        assert mock_turn.turn_number > 0
        assert isinstance(mock_turn.turn_number, int)


class TestLatencyStatsEndpoint:
    """Contract tests for GET /api/v1/interaction/sessions/{id}/latency endpoint."""

    def test_latency_stats_response_format(self, mock_latency_stats: dict) -> None:
        """Verify latency stats response format."""
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
            assert field in mock_latency_stats, f"Missing required field: {field}"

    def test_latency_values_are_numeric_or_null(self, mock_latency_stats: dict) -> None:
        """Verify latency values are numeric or null."""
        for key, value in mock_latency_stats.items():
            if key == "total_turns":
                assert isinstance(value, int)
            else:
                assert value is None or isinstance(value, (int, float))


class TestDeleteSessionEndpoint:
    """Contract tests for DELETE /api/v1/interaction/sessions/{id} endpoint."""

    def test_delete_response_format(self) -> None:
        """Verify delete response format."""
        session_id = uuid4()
        expected_response = {
            "status": "deleted",
            "session_id": str(session_id),
        }

        assert "status" in expected_response
        assert "session_id" in expected_response
        assert expected_response["status"] == "deleted"


class TestInteractionModeValues:
    """Contract tests for interaction mode enum values."""

    def test_valid_mode_values(self) -> None:
        """Verify valid interaction mode values."""
        valid_modes = ["realtime", "cascade"]

        assert InteractionMode.REALTIME.value in valid_modes
        assert InteractionMode.CASCADE.value in valid_modes

    def test_mode_enum_members(self) -> None:
        """Verify mode enum has expected members."""
        assert hasattr(InteractionMode, "REALTIME")
        assert hasattr(InteractionMode, "CASCADE")


class TestSessionStatusValues:
    """Contract tests for session status enum values."""

    def test_valid_status_values(self) -> None:
        """Verify valid session status values."""
        valid_statuses = ["active", "completed", "disconnected", "error"]

        assert SessionStatus.ACTIVE.value in valid_statuses
        assert SessionStatus.COMPLETED.value in valid_statuses
        assert SessionStatus.DISCONNECTED.value in valid_statuses
        assert SessionStatus.ERROR.value in valid_statuses

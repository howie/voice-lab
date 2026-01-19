"""Contract tests for WebSocket protocol.

Feature: 004-interaction-module
T026a: Contract test for WebSocket interaction protocol

Tests the WebSocket message format and protocol compliance.
"""

from uuid import uuid4

from src.infrastructure.websocket.base_handler import (
    MessageType,
    WebSocketMessage,
)


class TestMessageType:
    """Tests for WebSocket message type enum."""

    def test_client_message_types(self) -> None:
        """Verify client -> server message types are defined."""
        assert MessageType.AUDIO_CHUNK == "audio_chunk"
        assert MessageType.END_TURN == "end_turn"
        assert MessageType.INTERRUPT == "interrupt"
        assert MessageType.CONFIG == "config"
        assert MessageType.PING == "ping"

    def test_server_message_types(self) -> None:
        """Verify server -> client message types are defined."""
        assert MessageType.SPEECH_STARTED == "speech_started"
        assert MessageType.SPEECH_ENDED == "speech_ended"
        assert MessageType.TRANSCRIPT == "transcript"
        assert MessageType.AUDIO == "audio"
        assert MessageType.TEXT_DELTA == "text_delta"
        assert MessageType.RESPONSE_STARTED == "response_started"
        assert MessageType.RESPONSE_ENDED == "response_ended"
        assert MessageType.INTERRUPTED == "interrupted"
        assert MessageType.ERROR == "error"
        assert MessageType.PONG == "pong"
        assert MessageType.CONNECTED == "connected"
        assert MessageType.DISCONNECTED == "disconnected"


class TestWebSocketMessage:
    """Tests for WebSocketMessage dataclass."""

    def test_message_with_all_fields(self) -> None:
        """Test message creation with all fields."""
        session_id = uuid4()
        turn_id = uuid4()
        message = WebSocketMessage(
            type=MessageType.AUDIO,
            data={"audio": "base64data", "format": "pcm16"},
            session_id=session_id,
            turn_id=turn_id,
        )

        assert message.type == MessageType.AUDIO
        assert message.data == {"audio": "base64data", "format": "pcm16"}
        assert message.session_id == session_id
        assert message.turn_id == turn_id

    def test_message_minimal(self) -> None:
        """Test message creation with minimal fields."""
        message = WebSocketMessage(type=MessageType.PING)

        assert message.type == MessageType.PING
        assert message.data == {}
        assert message.session_id is None
        assert message.turn_id is None

    def test_message_with_empty_data(self) -> None:
        """Test message with explicitly empty data."""
        message = WebSocketMessage(type=MessageType.PONG, data={})
        assert message.data == {}


class TestConfigMessageContract:
    """Tests for CONFIG message contract."""

    def test_realtime_config_format(self) -> None:
        """Verify realtime mode config message format."""
        config_data = {
            "config": {
                "provider": "openai",
                "model": "gpt-4o-realtime",
                "voice": "alloy",
            },
            "system_prompt": "You are a helpful assistant.",
        }

        message = WebSocketMessage(type=MessageType.CONFIG, data=config_data)

        assert message.type == MessageType.CONFIG
        assert "config" in message.data
        assert "system_prompt" in message.data
        assert message.data["config"]["provider"] == "openai"

    def test_cascade_config_format(self) -> None:
        """Verify cascade mode config message format."""
        config_data = {
            "config": {
                "stt_provider": "azure",
                "llm_provider": "openai",
                "tts_provider": "azure",
                "language": "zh-TW",
            },
            "system_prompt": "",
        }

        message = WebSocketMessage(type=MessageType.CONFIG, data=config_data)

        assert message.type == MessageType.CONFIG
        assert message.data["config"]["stt_provider"] == "azure"


class TestAudioChunkMessageContract:
    """Tests for AUDIO_CHUNK message contract."""

    def test_audio_chunk_format(self) -> None:
        """Verify audio chunk message format."""
        audio_data = {
            "audio": "SGVsbG8gV29ybGQ=",  # base64 encoded
            "format": "pcm16",
            "sample_rate": 16000,
            "is_final": False,
        }

        message = WebSocketMessage(type=MessageType.AUDIO_CHUNK, data=audio_data)

        assert message.type == MessageType.AUDIO_CHUNK
        assert "audio" in message.data
        assert message.data["format"] == "pcm16"
        assert message.data["sample_rate"] == 16000

    def test_audio_chunk_final_flag(self) -> None:
        """Verify is_final flag in audio chunk."""
        audio_data = {
            "audio": "base64data",
            "format": "webm",
            "sample_rate": 16000,
            "is_final": True,
        }

        message = WebSocketMessage(type=MessageType.AUDIO_CHUNK, data=audio_data)
        assert message.data["is_final"] is True


class TestTranscriptMessageContract:
    """Tests for TRANSCRIPT message contract."""

    def test_transcript_format(self) -> None:
        """Verify transcript message format."""
        transcript_data = {
            "text": "Hello, how are you?",
            "is_final": True,
            "confidence": 0.95,
        }

        message = WebSocketMessage(type=MessageType.TRANSCRIPT, data=transcript_data)

        assert message.type == MessageType.TRANSCRIPT
        assert message.data["text"] == "Hello, how are you?"
        assert message.data["is_final"] is True
        assert message.data["confidence"] == 0.95

    def test_partial_transcript(self) -> None:
        """Verify partial (interim) transcript format."""
        transcript_data = {
            "text": "Hello",
            "is_final": False,
        }

        message = WebSocketMessage(type=MessageType.TRANSCRIPT, data=transcript_data)
        assert message.data["is_final"] is False


class TestAudioResponseMessageContract:
    """Tests for AUDIO response message contract."""

    def test_audio_response_format(self) -> None:
        """Verify audio response message format."""
        audio_data = {
            "audio": "base64audiocontent",
            "format": "pcm16",
            "is_first": True,
            "is_final": False,
        }

        message = WebSocketMessage(type=MessageType.AUDIO, data=audio_data)

        assert message.type == MessageType.AUDIO
        assert "audio" in message.data
        assert message.data["is_first"] is True


class TestErrorMessageContract:
    """Tests for ERROR message contract."""

    def test_error_format(self) -> None:
        """Verify error message format."""
        error_data = {
            "error_code": "INVALID_CONFIG",
            "message": "Provider not supported",
            "details": {"provider": "unknown"},
        }

        message = WebSocketMessage(type=MessageType.ERROR, data=error_data)

        assert message.type == MessageType.ERROR
        assert "error_code" in message.data
        assert "message" in message.data
        assert message.data["error_code"] == "INVALID_CONFIG"

    def test_error_minimal(self) -> None:
        """Verify error message with minimal fields."""
        error_data = {
            "error_code": "INTERNAL_ERROR",
            "message": "An error occurred",
            "details": {},
        }

        message = WebSocketMessage(type=MessageType.ERROR, data=error_data)
        assert message.data["details"] == {}


class TestConnectedMessageContract:
    """Tests for CONNECTED message contract."""

    def test_connected_initial(self) -> None:
        """Verify initial connected message format."""
        connected_data = {
            "user_id": str(uuid4()),
            "mode": "realtime",
        }

        message = WebSocketMessage(type=MessageType.CONNECTED, data=connected_data)

        assert message.type == MessageType.CONNECTED
        assert "user_id" in message.data
        assert "mode" in message.data

    def test_connected_session_started(self) -> None:
        """Verify session started connected message format."""
        session_id = uuid4()
        connected_data = {
            "status": "session_started",
            "session_id": str(session_id),
        }

        message = WebSocketMessage(
            type=MessageType.CONNECTED,
            session_id=session_id,
            data=connected_data,
        )

        assert message.session_id == session_id
        assert message.data["status"] == "session_started"

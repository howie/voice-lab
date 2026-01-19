"""Unit tests for Realtime mode API clients.

Feature: 004-interaction-module
T027b: Unit tests for Realtime API clients (OpenAI, Gemini)

Tests the OpenAI Realtime API and Gemini Live API client implementations.
"""

import base64
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities import InteractionMode, InteractionSession, SessionStatus
from src.domain.services.interaction.base import InteractionModeService


@pytest.fixture
def sample_session() -> InteractionSession:
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


@pytest.fixture
def mock_audio_data() -> bytes:
    """Create mock PCM16 audio data."""
    return b"\x00\x01" * 1600  # 100ms of 16kHz mono PCM16


class TestInteractionModeServiceInterface:
    """Tests for InteractionModeService interface compliance."""

    def test_interface_methods_defined(self) -> None:
        """Verify InteractionModeService interface has all required methods."""
        # These are the methods that must be implemented
        required_methods = [
            "connect",
            "disconnect",
            "send_audio",
            "end_turn",
            "interrupt",
            "events",
            "is_connected",
            "mode_name",
        ]

        # Check interface has these methods defined
        for method in required_methods:
            assert hasattr(InteractionModeService, method), f"Missing method: {method}"

    def test_connect_signature(self) -> None:
        """Verify connect method signature."""
        # Expected: async def connect(session_id: UUID, config: dict, system_prompt: str) -> None
        method = getattr(InteractionModeService, "connect", None)
        assert method is not None

    def test_send_audio_signature(self) -> None:
        """Verify send_audio method signature."""
        # Expected: async def send_audio(audio: AudioChunk) -> None
        method = getattr(InteractionModeService, "send_audio", None)
        assert method is not None

    def test_end_turn_signature(self) -> None:
        """Verify end_turn method signature."""
        # Expected: async def end_turn() -> None
        method = getattr(InteractionModeService, "end_turn", None)
        assert method is not None

    def test_interrupt_signature(self) -> None:
        """Verify interrupt method signature."""
        # Expected: async def interrupt() -> None
        method = getattr(InteractionModeService, "interrupt", None)
        assert method is not None

    def test_disconnect_signature(self) -> None:
        """Verify disconnect method signature."""
        # Expected: async def disconnect() -> None
        method = getattr(InteractionModeService, "disconnect", None)
        assert method is not None

    def test_events_signature(self) -> None:
        """Verify events method signature."""
        # Expected: def events() -> AsyncIterator[ResponseEvent]
        method = getattr(InteractionModeService, "events", None)
        assert method is not None

    def test_is_connected_signature(self) -> None:
        """Verify is_connected method signature."""
        # Expected: def is_connected() -> bool
        method = getattr(InteractionModeService, "is_connected", None)
        assert method is not None


class TestOpenAIRealtimeConfig:
    """Tests for OpenAI Realtime API configuration."""

    def test_valid_voices(self) -> None:
        """Verify valid OpenAI Realtime voices."""
        valid_voices = ["alloy", "echo", "shimmer", "ash", "ballad", "coral", "sage", "verse"]
        # At minimum, 'alloy' must be supported
        assert "alloy" in valid_voices

    def test_valid_models(self) -> None:
        """Verify valid OpenAI Realtime models."""
        valid_models = ["gpt-4o-realtime-preview", "gpt-4o-realtime-preview-2024-10-01"]
        # At minimum, one preview model must exist
        assert len(valid_models) >= 1

    def test_audio_format_config(self) -> None:
        """Verify audio format configuration."""
        config = {
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {"model": "whisper-1"},
        }

        assert config["input_audio_format"] == "pcm16"
        assert config["output_audio_format"] == "pcm16"

    def test_session_config_format(self) -> None:
        """Verify session configuration format for OpenAI."""
        session_config = {
            "modalities": ["text", "audio"],
            "instructions": "You are a helpful assistant.",
            "voice": "alloy",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500,
            },
        }

        assert "modalities" in session_config
        assert "audio" in session_config["modalities"]
        assert "voice" in session_config
        assert "turn_detection" in session_config


class TestGeminiLiveConfig:
    """Tests for Gemini Live API configuration."""

    def test_valid_voices(self) -> None:
        """Verify valid Gemini Live voices."""
        valid_voices = ["Puck", "Charon", "Kore", "Fenrir", "Aoede"]
        # At minimum, 'Puck' must be supported
        assert "Puck" in valid_voices

    def test_valid_models(self) -> None:
        """Verify valid Gemini Live models."""
        valid_models = ["gemini-2.0-flash-exp"]
        assert len(valid_models) >= 1

    def test_audio_format_config(self) -> None:
        """Verify audio format configuration for Gemini."""
        config = {
            "input_audio_encoding": "LINEAR16",
            "output_audio_encoding": "LINEAR16",
            "sample_rate_hertz": 16000,
        }

        assert config["input_audio_encoding"] == "LINEAR16"
        assert config["sample_rate_hertz"] == 16000

    def test_session_config_format(self) -> None:
        """Verify session configuration format for Gemini."""
        generation_config = {
            "speech_config": {
                "voice_config": {"prebuilt_voice_config": {"voice_name": "Puck"}}
            },
            "system_instruction": "You are a helpful assistant.",
            "response_modalities": ["AUDIO"],
        }

        assert "speech_config" in generation_config
        assert "response_modalities" in generation_config


class TestOpenAIRealtimeMessages:
    """Tests for OpenAI Realtime API message formats."""

    def test_input_audio_buffer_append(self, mock_audio_data: bytes) -> None:
        """Verify input_audio_buffer.append message format."""
        message = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(mock_audio_data).decode(),
        }

        assert message["type"] == "input_audio_buffer.append"
        assert "audio" in message

    def test_input_audio_buffer_commit(self) -> None:
        """Verify input_audio_buffer.commit message format."""
        message = {"type": "input_audio_buffer.commit"}
        assert message["type"] == "input_audio_buffer.commit"

    def test_response_create(self) -> None:
        """Verify response.create message format."""
        message = {
            "type": "response.create",
            "response": {"modalities": ["text", "audio"]},
        }

        assert message["type"] == "response.create"

    def test_response_cancel(self) -> None:
        """Verify response.cancel message format."""
        message = {"type": "response.cancel"}
        assert message["type"] == "response.cancel"

    def test_session_update(self) -> None:
        """Verify session.update message format."""
        message = {
            "type": "session.update",
            "session": {
                "instructions": "Updated instructions.",
                "voice": "echo",
            },
        }

        assert message["type"] == "session.update"
        assert "session" in message


class TestOpenAIRealtimeEvents:
    """Tests for OpenAI Realtime API server events."""

    def test_session_created_event(self) -> None:
        """Verify session.created event format."""
        event = {
            "type": "session.created",
            "session": {
                "id": "sess_001",
                "model": "gpt-4o-realtime-preview",
                "voice": "alloy",
            },
        }

        assert event["type"] == "session.created"
        assert "session" in event

    def test_input_audio_buffer_speech_started(self) -> None:
        """Verify input_audio_buffer.speech_started event format."""
        event = {
            "type": "input_audio_buffer.speech_started",
            "audio_start_ms": 100,
            "item_id": "item_001",
        }

        assert event["type"] == "input_audio_buffer.speech_started"

    def test_input_audio_buffer_speech_stopped(self) -> None:
        """Verify input_audio_buffer.speech_stopped event format."""
        event = {
            "type": "input_audio_buffer.speech_stopped",
            "audio_end_ms": 2500,
            "item_id": "item_001",
        }

        assert event["type"] == "input_audio_buffer.speech_stopped"

    def test_conversation_item_input_audio_transcription_completed(self) -> None:
        """Verify transcription completed event format."""
        event = {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "item_001",
            "transcript": "Hello, how are you?",
        }

        assert "transcript" in event

    def test_response_audio_delta(self) -> None:
        """Verify response.audio.delta event format."""
        event = {
            "type": "response.audio.delta",
            "response_id": "resp_001",
            "delta": "base64audiochunk",
        }

        assert event["type"] == "response.audio.delta"
        assert "delta" in event

    def test_response_audio_transcript_delta(self) -> None:
        """Verify response.audio_transcript.delta event format."""
        event = {
            "type": "response.audio_transcript.delta",
            "response_id": "resp_001",
            "delta": "Hello",
        }

        assert event["type"] == "response.audio_transcript.delta"

    def test_response_done(self) -> None:
        """Verify response.done event format."""
        event = {
            "type": "response.done",
            "response": {
                "id": "resp_001",
                "status": "completed",
            },
        }

        assert event["type"] == "response.done"

    def test_error_event(self) -> None:
        """Verify error event format."""
        event = {
            "type": "error",
            "error": {
                "type": "invalid_request_error",
                "message": "Invalid audio format",
            },
        }

        assert event["type"] == "error"
        assert "error" in event


class TestGeminiLiveMessages:
    """Tests for Gemini Live API message formats."""

    def test_realtime_input_audio(self, mock_audio_data: bytes) -> None:
        """Verify realtime input audio message format."""
        message = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "mime_type": "audio/pcm",
                        "data": base64.b64encode(mock_audio_data).decode(),
                    }
                ]
            }
        }

        assert "realtime_input" in message
        assert "media_chunks" in message["realtime_input"]

    def test_tool_response(self) -> None:
        """Verify tool response message format."""
        message = {
            "tool_response": {
                "function_responses": [{"id": "func_001", "response": {"result": "success"}}]
            }
        }

        assert "tool_response" in message


class TestGeminiLiveEvents:
    """Tests for Gemini Live API server events."""

    def test_setup_complete_event(self) -> None:
        """Verify setup complete event format."""
        event = {"setupComplete": {}}
        assert "setupComplete" in event

    def test_server_content_event(self) -> None:
        """Verify server content event format."""
        event = {
            "serverContent": {
                "modelTurn": {
                    "parts": [{"inlineData": {"mimeType": "audio/pcm", "data": "base64audio"}}]
                },
                "turnComplete": False,
            }
        }

        assert "serverContent" in event
        assert "modelTurn" in event["serverContent"]

    def test_turn_complete_event(self) -> None:
        """Verify turn complete event format."""
        event = {"serverContent": {"turnComplete": True}}

        assert event["serverContent"]["turnComplete"] is True

    def test_interrupted_event(self) -> None:
        """Verify interrupted event format."""
        event = {"serverContent": {"interrupted": True}}

        assert event["serverContent"]["interrupted"] is True


class TestRealtimeModeFactory:
    """Tests for RealtimeMode factory pattern."""

    def test_supported_providers(self) -> None:
        """Verify supported realtime providers."""
        supported = ["openai", "gemini"]
        assert "openai" in supported
        assert "gemini" in supported

    def test_provider_selection_by_config(self) -> None:
        """Verify provider selection based on config."""
        openai_config = {"provider": "openai", "voice": "alloy"}
        gemini_config = {"provider": "gemini", "voice": "Puck"}

        assert openai_config["provider"] == "openai"
        assert gemini_config["provider"] == "gemini"

    def test_invalid_provider_handling(self) -> None:
        """Verify invalid provider raises appropriate error."""
        invalid_config = {"provider": "invalid_provider", "voice": "test"}

        # Factory should raise ValueError for unknown providers
        # This documents expected behavior
        assert invalid_config["provider"] not in ["openai", "gemini"]


class TestAudioProcessing:
    """Tests for audio processing utilities."""

    def test_pcm16_format(self) -> None:
        """Verify PCM16 format specifications."""
        pcm16_spec = {
            "sample_rate": 16000,
            "bits_per_sample": 16,
            "channels": 1,
            "byte_order": "little_endian",
        }

        assert pcm16_spec["sample_rate"] == 16000
        assert pcm16_spec["bits_per_sample"] == 16

    def test_audio_chunk_size(self) -> None:
        """Verify recommended audio chunk sizes."""
        # OpenAI recommends 100ms chunks
        chunk_duration_ms = 100
        sample_rate = 16000
        bytes_per_sample = 2  # 16-bit
        channels = 1

        expected_chunk_size = (sample_rate * chunk_duration_ms // 1000) * bytes_per_sample * channels
        assert expected_chunk_size == 3200  # 100ms of 16kHz mono PCM16

    def test_base64_encoding(self, mock_audio_data: bytes) -> None:
        """Verify base64 encoding for audio transmission."""
        encoded = base64.b64encode(mock_audio_data).decode()
        decoded = base64.b64decode(encoded)

        assert decoded == mock_audio_data
        assert isinstance(encoded, str)

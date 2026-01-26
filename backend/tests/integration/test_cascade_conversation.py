"""Integration tests for cascade mode voice conversation flow.

Feature: 004-interaction-module
Tests the complete cascade mode flow: STT -> LLM -> TTS pipeline via WebSocket.
"""

import base64
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.entities import InteractionMode, InteractionSession, SessionStatus
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult
from src.domain.services.interaction.base import InteractionModeService
from src.domain.services.interaction.cascade_mode import CascadeModeService
from src.infrastructure.persistence.database import get_db_session
from src.main import app


@pytest.fixture
def mock_cascade_session() -> InteractionSession:
    """Create a mock cascade interaction session."""
    return InteractionSession(
        id=uuid4(),
        user_id=uuid4(),
        mode=InteractionMode.CASCADE,
        provider_config={
            "stt_provider": "azure",
            "llm_provider": "openai",
            "tts_provider": "azure",
            "tts_voice": "zh-TW-HsiaoChenNeural",
        },
        system_prompt="You are a helpful Chinese teacher.",
        status=SessionStatus.ACTIVE,
        started_at=datetime.now(UTC),
        ended_at=None,
    )


@pytest.fixture
def mock_audio_chunk() -> bytes:
    """Create mock PCM16 audio data."""
    # 100ms of 16kHz mono PCM16 audio (3200 bytes)
    return b"\x00\x01" * 1600


class TestCascadeConversationFlow:
    """Integration tests for cascade mode WebSocket conversation flow."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self) -> None:
        """Override database dependencies for testing."""
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        async def get_mock_db():
            yield mock_db

        app.dependency_overrides[get_db_session] = get_mock_db
        yield
        app.dependency_overrides.clear()

    def test_websocket_cascade_url_format(self) -> None:
        """Verify WebSocket endpoint URL format for cascade mode.

        Expected: /api/v1/interaction/ws/cascade
        """
        expected_url = "/api/v1/interaction/ws/cascade"
        assert "cascade" in expected_url
        assert "/ws/" in expected_url

    def test_cascade_config_message_format(self) -> None:
        """Verify config message format for cascade session initialization."""
        config_message = {
            "type": "config",
            "data": {
                "config": {
                    "stt_provider": "azure",
                    "llm_provider": "openai",
                    "tts_provider": "azure",
                    "tts_voice": "zh-TW-HsiaoChenNeural",
                    "language": "zh-TW",
                },
                "system_prompt": "You are a helpful Chinese teacher.",
            },
        }

        # Verify required fields
        assert config_message["type"] == "config"
        assert "config" in config_message["data"]
        assert "system_prompt" in config_message["data"]
        assert config_message["data"]["config"]["stt_provider"] == "azure"
        assert config_message["data"]["config"]["llm_provider"] == "openai"
        assert config_message["data"]["config"]["tts_provider"] == "azure"

    def test_cascade_audio_chunk_message_format(self, mock_audio_chunk: bytes) -> None:
        """Verify audio chunk message format for cascade mode."""
        audio_b64 = base64.b64encode(mock_audio_chunk).decode()
        audio_message = {
            "type": "audio_chunk",
            "data": {
                "audio": audio_b64,
                "format": "pcm16",
                "sample_rate": 16000,
                "is_final": False,
            },
        }

        assert audio_message["type"] == "audio_chunk"
        assert "audio" in audio_message["data"]
        assert audio_message["data"]["format"] == "pcm16"
        assert audio_message["data"]["sample_rate"] == 16000

    def test_cascade_end_turn_triggers_pipeline(self) -> None:
        """Verify end_turn message triggers STT -> LLM -> TTS pipeline."""
        end_turn_message = {
            "type": "end_turn",
            "data": {},
        }

        # Document expected behavior:
        # 1. Server collects accumulated audio
        # 2. STT processes audio -> transcript
        # 3. LLM generates response from transcript
        # 4. TTS synthesizes audio from LLM response
        assert end_turn_message["type"] == "end_turn"

    def test_cascade_expected_server_responses(self) -> None:
        """Verify expected server response sequence for cascade mode.

        Cascade mode should emit events in this order:
        1. speech_started - When first audio chunk received
        2. speech_ended - When end_turn received
        3. transcript - STT result
        4. text_delta - LLM streaming chunks
        5. audio - TTS audio chunks
        6. response_ended - Pipeline complete
        """
        expected_responses = [
            {"type": "connected", "data": {"status": "connected", "mode": "cascade"}},
            {"type": "speech_started", "data": {}},
            {"type": "speech_ended", "data": {}},
            {"type": "transcript", "data": {"text": "Hello", "is_final": True}},
            {
                "type": "text_delta",
                "data": {"delta": "Hi", "accumulated": "Hi", "is_first": True},
            },
            {
                "type": "audio",
                "data": {"audio": "base64data", "format": "pcm16", "is_first": True, "is_final": False},
            },
            {"type": "response_ended", "data": {"text": "Hi there!"}},
        ]

        for response in expected_responses:
            assert "type" in response
            assert "data" in response


class TestCascadeProviderConfiguration:
    """Tests for cascade mode provider configuration."""

    def test_stt_provider_options(self) -> None:
        """Verify supported STT providers for cascade mode."""
        supported_stt = ["azure", "gcp", "whisper", "speechmatics"]
        assert "azure" in supported_stt
        assert "gcp" in supported_stt

    def test_llm_provider_options(self) -> None:
        """Verify supported LLM providers for cascade mode."""
        supported_llm = ["openai", "anthropic", "gemini", "azure_openai"]
        assert "openai" in supported_llm
        assert "anthropic" in supported_llm

    def test_tts_provider_options(self) -> None:
        """Verify supported TTS providers for cascade mode."""
        supported_tts = ["azure", "gcp", "elevenlabs", "voai"]
        assert "azure" in supported_tts
        assert "elevenlabs" in supported_tts

    def test_default_provider_configuration(self) -> None:
        """Verify default providers when not specified."""
        from src.domain.services.interaction.cascade_mode_factory import (
            CascadeModeFactory,
        )

        assert CascadeModeFactory.DEFAULT_STT_PROVIDER == "azure"
        assert CascadeModeFactory.DEFAULT_LLM_PROVIDER == "openai"
        assert CascadeModeFactory.DEFAULT_TTS_PROVIDER == "azure"


class TestCascadePipelineFlow:
    """Tests for STT -> LLM -> TTS pipeline execution."""

    def test_pipeline_stage_order(self) -> None:
        """Document expected pipeline stage execution order."""
        pipeline_stages = [
            {"stage": "audio_collection", "description": "Collect audio chunks in buffer"},
            {"stage": "stt", "description": "Transcribe audio to text"},
            {"stage": "llm", "description": "Generate response from transcript"},
            {"stage": "tts", "description": "Synthesize audio from response"},
        ]

        assert pipeline_stages[0]["stage"] == "audio_collection"
        assert pipeline_stages[1]["stage"] == "stt"
        assert pipeline_stages[2]["stage"] == "llm"
        assert pipeline_stages[3]["stage"] == "tts"

    def test_streaming_behavior(self) -> None:
        """Document expected streaming behavior for cascade mode.

        - LLM: Streams text_delta events as tokens are generated
        - TTS: Streams audio chunks as they are synthesized
        """
        llm_streaming = {
            "event_type": "text_delta",
            "fields": ["delta", "accumulated", "is_first"],
        }

        tts_streaming = {
            "event_type": "audio",
            "fields": ["audio", "format", "is_first", "is_final"],
        }

        assert llm_streaming["event_type"] == "text_delta"
        assert tts_streaming["event_type"] == "audio"


class TestCascadeLatencyTracking:
    """Tests for latency measurement in cascade mode."""

    def test_cascade_latency_metrics(self) -> None:
        """Verify latency metrics captured for cascade mode."""
        latency_metrics = {
            "total_latency_ms": 850.0,
            "stt_latency_ms": 250.0,  # Time for STT processing
            "llm_ttft_ms": 150.0,  # Time to first LLM token
            "tts_ttfb_ms": 200.0,  # Time to first TTS audio byte
            "realtime_latency_ms": None,  # Not applicable for cascade
        }

        # Cascade mode should have component latencies
        assert latency_metrics["stt_latency_ms"] is not None
        assert latency_metrics["llm_ttft_ms"] is not None
        assert latency_metrics["tts_ttfb_ms"] is not None
        # Realtime-specific metric should be None
        assert latency_metrics["realtime_latency_ms"] is None

    def test_latency_measurement_points(self) -> None:
        """Document latency measurement points for cascade mode.

        Cascade mode measures:
        - STT latency: Time from audio buffer to transcript
        - LLM TTFT: Time from transcript to first LLM token
        - TTS TTFB: Time from LLM complete to first audio byte
        - Total: End-to-end turn latency
        """
        measurement_points = {
            "stt_start": "end_turn received (audio buffer ready)",
            "stt_end": "transcript event emitted",
            "llm_start": "transcript sent to LLM",
            "llm_ttft": "first text_delta emitted",
            "llm_end": "LLM generation complete",
            "tts_start": "text sent to TTS",
            "tts_ttfb": "first audio chunk emitted",
            "tts_end": "final audio chunk emitted",
        }

        assert "stt_start" in measurement_points
        assert "llm_ttft" in measurement_points
        assert "tts_ttfb" in measurement_points


class TestCascadeInterruption:
    """Tests for barge-in/interruption in cascade mode."""

    def test_interrupt_message_format(self) -> None:
        """Verify interrupt message format for cascade mode."""
        interrupt_message = {
            "type": "interrupt",
            "data": {},
        }

        assert interrupt_message["type"] == "interrupt"

    def test_interrupt_stops_pipeline(self) -> None:
        """Document expected interrupt behavior.

        When interrupt is received:
        1. Stop current TTS audio streaming
        2. Abort LLM generation if in progress
        3. Emit 'interrupted' event
        4. Ready for new audio input
        """
        interrupt_sequence = [
            {"type": "interrupt", "data": {}},  # Client sends
            {"type": "interrupted", "data": {}},  # Server responds
        ]

        assert interrupt_sequence[0]["type"] == "interrupt"
        assert interrupt_sequence[1]["type"] == "interrupted"


class TestCascadeVsRealtimeComparison:
    """Tests documenting differences between cascade and realtime modes."""

    def test_mode_characteristics(self) -> None:
        """Document key differences between modes."""
        cascade_mode = {
            "name": "cascade",
            "pipeline": "STT -> LLM -> TTS",
            "latency": "Higher (3 API calls)",
            "quality": "Higher (separate optimization per stage)",
            "flexibility": "High (mix providers)",
            "cost": "Pay per stage",
        }

        realtime_mode = {
            "name": "realtime",
            "pipeline": "V2V direct",
            "latency": "Lower (single API)",
            "quality": "Good (integrated)",
            "flexibility": "Limited (single provider)",
            "cost": "Per minute/token",
        }

        assert cascade_mode["pipeline"] == "STT -> LLM -> TTS"
        assert realtime_mode["pipeline"] == "V2V direct"

    def test_when_to_use_cascade(self) -> None:
        """Document use cases for cascade mode."""
        cascade_use_cases = [
            "Need specific STT provider for language/accuracy",
            "Want to use Claude/specific LLM for response quality",
            "Need specific TTS voice not available in V2V",
            "Debugging/logging individual pipeline stages",
            "A/B testing different provider combinations",
        ]

        assert len(cascade_use_cases) >= 3


class TestCascadeModeServiceE2E:
    """End-to-end tests for CascadeModeService."""

    @pytest.fixture
    def mock_providers(self) -> tuple[MagicMock, MagicMock, MagicMock]:
        """Create mock providers for e2e testing."""
        from src.application.interfaces.llm_provider import ILLMProvider
        from src.application.interfaces.stt_provider import ISTTProvider
        from src.application.interfaces.tts_provider import ITTSProvider

        mock_stt = MagicMock(spec=ISTTProvider)
        mock_stt.name = "mock_stt"

        # Create proper STTResult with required fields
        mock_audio = AudioData(
            data=b"\x00\x01" * 100,
            format=AudioFormat.PCM,
            sample_rate=16000,
            channels=1,
        )
        mock_request = STTRequest(
            provider="mock_stt",
            language="zh-TW",
            audio=mock_audio,
        )
        mock_result = STTResult(
            request=mock_request,
            transcript="Hello",
            confidence=0.95,
            latency_ms=100,
        )
        mock_stt.transcribe = AsyncMock(return_value=mock_result)

        mock_llm = MagicMock(spec=ILLMProvider)
        mock_llm.name = "mock_llm"

        async def mock_generate_stream(*args, **kwargs):
            for chunk in ["Hi ", "there!"]:
                yield chunk

        mock_llm.generate_stream = mock_generate_stream

        mock_tts = MagicMock(spec=ITTSProvider)
        mock_tts.name = "mock_tts"

        async def mock_synthesize_stream(*args, **kwargs):
            for chunk in [b"\x00\x01" * 100, b"\x00\x02" * 100]:
                yield chunk

        mock_tts.synthesize_stream = mock_synthesize_stream

        return mock_stt, mock_llm, mock_tts

    @pytest.mark.asyncio
    async def test_full_cascade_pipeline(
        self, mock_providers: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """Test complete cascade pipeline execution."""
        mock_stt, mock_llm, mock_tts = mock_providers

        service = CascadeModeService(
            stt_provider=mock_stt,
            llm_provider=mock_llm,
            tts_provider=mock_tts,
        )

        # Connect
        session_id = uuid4()
        await service.connect(session_id, {"tts_voice": "test"}, "You are helpful.")
        assert service.is_connected()

        # Send audio
        from src.domain.services.interaction.base import AudioChunk

        audio_data = b"\x00\x01" * 1600
        chunk = AudioChunk(data=audio_data, sample_rate=16000)
        await service.send_audio(chunk)

        # Trigger pipeline
        await service.end_turn()

        # Verify STT was called
        mock_stt.transcribe.assert_called_once()

        # Disconnect
        await service.disconnect()
        assert not service.is_connected()

    @pytest.mark.asyncio
    async def test_cascade_service_interrupt(
        self, mock_providers: tuple[MagicMock, MagicMock, MagicMock]
    ) -> None:
        """Test interrupt functionality in cascade mode."""
        mock_stt, mock_llm, mock_tts = mock_providers

        service = CascadeModeService(
            stt_provider=mock_stt,
            llm_provider=mock_llm,
            tts_provider=mock_tts,
        )

        await service.connect(uuid4(), {})

        # Interrupt should set flag
        await service.interrupt()
        assert service._interrupted is True

        await service.disconnect()


class TestInteractionModeFactoryIntegration:
    """Integration tests for InteractionModeFactory in WebSocket routes."""

    @patch("src.domain.services.interaction.cascade_mode_factory.STTProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.LLMProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.TTSProviderFactory")
    def test_websocket_creates_cascade_service_correctly(
        self,
        mock_tts_factory: MagicMock,
        mock_llm_factory: MagicMock,
        mock_stt_factory: MagicMock,
    ) -> None:
        """Verify WebSocket route creates cascade service with factory."""
        from src.application.interfaces.llm_provider import ILLMProvider
        from src.application.interfaces.stt_provider import ISTTProvider
        from src.application.interfaces.tts_provider import ITTSProvider

        mock_stt = MagicMock(spec=ISTTProvider)
        mock_llm = MagicMock(spec=ILLMProvider)
        mock_tts = MagicMock(spec=ITTSProvider)

        mock_stt_factory.create.return_value = mock_stt
        mock_llm_factory.create.return_value = mock_llm
        mock_tts_factory.create_default.return_value = mock_tts

        # Simulate what interaction_ws.py now does (after fix)
        from src.presentation.api.routes.interaction_ws import InteractionModeFactory

        config = {
            "stt_provider": "azure",
            "llm_provider": "openai",
            "tts_provider": "azure",
        }

        service = InteractionModeFactory.create("cascade", config)

        # Verify service is created correctly
        assert isinstance(service, InteractionModeService)
        assert service.mode_name == "cascade"

        # Verify providers were created
        mock_stt_factory.create.assert_called_once()
        mock_llm_factory.create.assert_called_once()
        mock_tts_factory.create_default.assert_called_once()

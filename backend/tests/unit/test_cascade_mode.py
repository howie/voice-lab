"""Unit tests for Cascade mode service and factory.

Feature: 004-interaction-module
Tests the CascadeModeService and CascadeModeFactory implementations.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.application.interfaces.llm_provider import ILLMProvider
from src.application.interfaces.stt_provider import ISTTProvider
from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest, STTResult
from src.domain.services.interaction.base import AudioChunk, InteractionModeService
from src.domain.services.interaction.cascade_mode import CascadeModeService
from src.domain.services.interaction.cascade_mode_factory import CascadeModeFactory


@pytest.fixture
def mock_stt_provider() -> MagicMock:
    """Create a mock STT provider."""
    provider = MagicMock(spec=ISTTProvider)
    provider.name = "mock_stt"

    # Create a proper STTResult with required fields
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
        transcript="Hello, how are you?",
        confidence=0.95,
        latency_ms=100,
    )
    provider.transcribe = AsyncMock(return_value=mock_result)
    return provider


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """Create a mock LLM provider."""
    provider = MagicMock(spec=ILLMProvider)
    provider.name = "mock_llm"

    async def mock_generate_stream(*args, **kwargs):
        for chunk in ["I'm ", "doing ", "well!"]:
            yield chunk

    provider.generate_stream = mock_generate_stream
    return provider


@pytest.fixture
def mock_tts_provider() -> MagicMock:
    """Create a mock TTS provider."""
    provider = MagicMock(spec=ITTSProvider)
    provider.name = "mock_tts"

    async def mock_synthesize_stream(*args, **kwargs):
        for chunk in [b"\x00\x01" * 100, b"\x00\x02" * 100]:
            yield chunk

    provider.synthesize_stream = mock_synthesize_stream
    return provider


@pytest.fixture
def cascade_service(
    mock_stt_provider: MagicMock,
    mock_llm_provider: MagicMock,
    mock_tts_provider: MagicMock,
) -> CascadeModeService:
    """Create a CascadeModeService with mock providers."""
    return CascadeModeService(
        stt_provider=mock_stt_provider,
        llm_provider=mock_llm_provider,
        tts_provider=mock_tts_provider,
    )


class TestCascadeModeServiceInit:
    """Tests for CascadeModeService initialization."""

    def test_requires_stt_provider(
        self, mock_llm_provider: MagicMock, mock_tts_provider: MagicMock
    ) -> None:
        """Verify STT provider is required."""
        with pytest.raises(TypeError):
            CascadeModeService(
                llm_provider=mock_llm_provider,
                tts_provider=mock_tts_provider,
            )

    def test_requires_llm_provider(
        self, mock_stt_provider: MagicMock, mock_tts_provider: MagicMock
    ) -> None:
        """Verify LLM provider is required."""
        with pytest.raises(TypeError):
            CascadeModeService(
                stt_provider=mock_stt_provider,
                tts_provider=mock_tts_provider,
            )

    def test_requires_tts_provider(
        self, mock_stt_provider: MagicMock, mock_llm_provider: MagicMock
    ) -> None:
        """Verify TTS provider is required."""
        with pytest.raises(TypeError):
            CascadeModeService(
                stt_provider=mock_stt_provider,
                llm_provider=mock_llm_provider,
            )

    def test_successful_initialization(
        self,
        mock_stt_provider: MagicMock,
        mock_llm_provider: MagicMock,
        mock_tts_provider: MagicMock,
    ) -> None:
        """Verify successful initialization with all providers."""
        service = CascadeModeService(
            stt_provider=mock_stt_provider,
            llm_provider=mock_llm_provider,
            tts_provider=mock_tts_provider,
        )
        assert service is not None
        assert service.mode_name == "cascade"

    def test_not_connected_initially(self, cascade_service: CascadeModeService) -> None:
        """Verify service is not connected after initialization."""
        assert cascade_service.is_connected() is False


class TestCascadeModeServiceInterface:
    """Tests for CascadeModeService interface compliance."""

    def test_implements_interaction_mode_service(self, cascade_service: CascadeModeService) -> None:
        """Verify CascadeModeService implements InteractionModeService."""
        assert isinstance(cascade_service, InteractionModeService)

    def test_has_required_methods(self, cascade_service: CascadeModeService) -> None:
        """Verify all required methods exist."""
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
        for method in required_methods:
            assert hasattr(cascade_service, method), f"Missing method: {method}"

    def test_mode_name_is_cascade(self, cascade_service: CascadeModeService) -> None:
        """Verify mode_name returns 'cascade'."""
        assert cascade_service.mode_name == "cascade"


class TestCascadeModeServiceConnect:
    """Tests for CascadeModeService connect method."""

    @pytest.mark.asyncio
    async def test_connect_sets_connected_state(self, cascade_service: CascadeModeService) -> None:
        """Verify connect sets service to connected state."""
        session_id = uuid4()
        config = {"tts_voice": "zh-TW-HsiaoChenNeural"}

        await cascade_service.connect(session_id, config, "You are helpful.")

        assert cascade_service.is_connected() is True

    @pytest.mark.asyncio
    async def test_connect_stores_session_id(self, cascade_service: CascadeModeService) -> None:
        """Verify connect stores session ID."""
        session_id = uuid4()
        config = {}

        await cascade_service.connect(session_id, config)

        assert cascade_service._session_id == session_id

    @pytest.mark.asyncio
    async def test_connect_stores_system_prompt(self, cascade_service: CascadeModeService) -> None:
        """Verify connect stores system prompt."""
        session_id = uuid4()
        system_prompt = "You are a helpful Chinese teacher."

        await cascade_service.connect(session_id, {}, system_prompt)

        assert cascade_service._system_prompt == system_prompt
        # System prompt should be added to messages
        assert len(cascade_service._messages) == 1
        assert cascade_service._messages[0].role == "system"


class TestCascadeModeServiceDisconnect:
    """Tests for CascadeModeService disconnect method."""

    @pytest.mark.asyncio
    async def test_disconnect_clears_connected_state(
        self, cascade_service: CascadeModeService
    ) -> None:
        """Verify disconnect clears connected state."""
        await cascade_service.connect(uuid4(), {})
        assert cascade_service.is_connected() is True

        await cascade_service.disconnect()

        assert cascade_service.is_connected() is False

    @pytest.mark.asyncio
    async def test_disconnect_clears_session_id(self, cascade_service: CascadeModeService) -> None:
        """Verify disconnect clears session ID."""
        await cascade_service.connect(uuid4(), {})
        await cascade_service.disconnect()

        assert cascade_service._session_id is None


class TestCascadeModeServiceSendAudio:
    """Tests for CascadeModeService send_audio method."""

    @pytest.mark.asyncio
    async def test_send_audio_accumulates_in_buffer(
        self, cascade_service: CascadeModeService
    ) -> None:
        """Verify audio chunks are accumulated in buffer."""
        await cascade_service.connect(uuid4(), {})

        audio_data = b"\x00\x01" * 100
        chunk = AudioChunk(data=audio_data, format="pcm16", sample_rate=16000)

        await cascade_service.send_audio(chunk)

        buffer_content = cascade_service._audio_buffer.getvalue()
        assert buffer_content == audio_data

    @pytest.mark.asyncio
    async def test_send_audio_ignores_when_not_connected(
        self, cascade_service: CascadeModeService
    ) -> None:
        """Verify send_audio is ignored when not connected."""
        audio_data = b"\x00\x01" * 100
        chunk = AudioChunk(data=audio_data, format="pcm16", sample_rate=16000)

        await cascade_service.send_audio(chunk)

        buffer_content = cascade_service._audio_buffer.getvalue()
        assert buffer_content == b""


class TestCascadeModeServiceEndTurn:
    """Tests for CascadeModeService end_turn method."""

    @pytest.mark.asyncio
    async def test_end_turn_processes_pipeline(
        self,
        cascade_service: CascadeModeService,
        mock_stt_provider: MagicMock,
    ) -> None:
        """Verify end_turn triggers STT -> LLM -> TTS pipeline."""
        await cascade_service.connect(uuid4(), {})

        # Send some audio
        audio_data = b"\x00\x01" * 1600
        chunk = AudioChunk(data=audio_data, format="pcm16", sample_rate=16000)
        await cascade_service.send_audio(chunk)

        # End turn to trigger processing
        await cascade_service.end_turn()

        # Give time for async processing
        await asyncio.sleep(0.1)

        # STT should have been called
        mock_stt_provider.transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_turn_does_nothing_without_audio(
        self,
        cascade_service: CascadeModeService,
        mock_stt_provider: MagicMock,
    ) -> None:
        """Verify end_turn does nothing if no audio was sent."""
        await cascade_service.connect(uuid4(), {})

        await cascade_service.end_turn()
        await asyncio.sleep(0.1)

        # STT should not have been called
        mock_stt_provider.transcribe.assert_not_called()


class TestCascadeModeServiceInterrupt:
    """Tests for CascadeModeService interrupt method."""

    @pytest.mark.asyncio
    async def test_interrupt_sets_interrupted_flag(
        self, cascade_service: CascadeModeService
    ) -> None:
        """Verify interrupt sets the interrupted flag."""
        await cascade_service.connect(uuid4(), {})

        await cascade_service.interrupt()

        assert cascade_service._interrupted is True


class TestCascadeModeFactoryCreate:
    """Tests for CascadeModeFactory.create method."""

    @patch("src.domain.services.interaction.cascade_mode_factory.STTProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.LLMProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.TTSProviderFactory")
    def test_create_with_default_providers(
        self,
        mock_tts_factory: MagicMock,
        mock_llm_factory: MagicMock,
        mock_stt_factory: MagicMock,
    ) -> None:
        """Verify create uses default providers when not specified."""
        # Setup mocks
        mock_stt = MagicMock(spec=ISTTProvider)
        mock_llm = MagicMock(spec=ILLMProvider)
        mock_tts = MagicMock(spec=ITTSProvider)

        mock_stt_factory.create.return_value = mock_stt
        mock_llm_factory.create.return_value = mock_llm
        mock_tts_factory.create_default.return_value = mock_tts

        factory = CascadeModeFactory()
        service = factory.create({})

        # Verify default providers are used
        mock_stt_factory.create.assert_called_once_with("azure", {})
        mock_llm_factory.create.assert_called_once_with("openai", {})
        mock_tts_factory.create_default.assert_called_once_with("azure")

        assert isinstance(service, CascadeModeService)

    @patch("src.domain.services.interaction.cascade_mode_factory.STTProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.LLMProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.TTSProviderFactory")
    def test_create_with_custom_providers(
        self,
        mock_tts_factory: MagicMock,
        mock_llm_factory: MagicMock,
        mock_stt_factory: MagicMock,
    ) -> None:
        """Verify create uses specified providers."""
        mock_stt = MagicMock(spec=ISTTProvider)
        mock_llm = MagicMock(spec=ILLMProvider)
        mock_tts = MagicMock(spec=ITTSProvider)

        mock_stt_factory.create.return_value = mock_stt
        mock_llm_factory.create.return_value = mock_llm
        mock_tts_factory.create_default.return_value = mock_tts

        factory = CascadeModeFactory()
        config = {
            "stt_provider": "gcp",
            "llm_provider": "anthropic",
            "tts_provider": "elevenlabs",
        }
        service = factory.create(config)

        mock_stt_factory.create.assert_called_once_with("gcp", {})
        mock_llm_factory.create.assert_called_once_with("anthropic", {})
        mock_tts_factory.create_default.assert_called_once_with("elevenlabs")

        assert isinstance(service, CascadeModeService)

    @patch("src.domain.services.interaction.cascade_mode_factory.STTProviderFactory")
    def test_create_raises_on_invalid_stt_provider(self, mock_stt_factory: MagicMock) -> None:
        """Verify create raises ValueError for invalid STT provider."""
        mock_stt_factory.create.side_effect = ValueError("Unknown provider")

        factory = CascadeModeFactory()

        with pytest.raises(ValueError, match="Invalid STT provider config"):
            factory.create({"stt_provider": "invalid"})


class TestCascadeModeFactoryProviderInfo:
    """Tests for CascadeModeFactory provider information methods."""

    def test_get_available_providers_returns_dict(self) -> None:
        """Verify get_available_providers returns a dict with expected keys."""
        providers = CascadeModeFactory.get_available_providers()

        assert isinstance(providers, dict)
        assert "stt" in providers
        assert "llm" in providers
        assert "tts" in providers

    def test_get_provider_info_returns_dict(self) -> None:
        """Verify get_provider_info returns a dict with expected keys."""
        info = CascadeModeFactory.get_provider_info()

        assert isinstance(info, dict)
        assert "stt" in info
        assert "llm" in info
        assert "tts" in info


class TestInteractionModeFactoryInWebSocket:
    """Tests for InteractionModeFactory used in WebSocket routes."""

    def test_cascade_mode_factory_import(self) -> None:
        """Verify CascadeModeFactory can be imported in WebSocket routes."""
        from src.domain.services.interaction.cascade_mode_factory import (
            CascadeModeFactory,
        )

        assert CascadeModeFactory is not None

    @patch("src.domain.services.interaction.cascade_mode_factory.STTProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.LLMProviderFactory")
    @patch("src.domain.services.interaction.cascade_mode_factory.TTSProviderFactory")
    def test_websocket_factory_creates_cascade_service(
        self,
        mock_tts_factory: MagicMock,
        mock_llm_factory: MagicMock,
        mock_stt_factory: MagicMock,
    ) -> None:
        """Verify WebSocket factory correctly creates cascade service."""
        mock_stt = MagicMock(spec=ISTTProvider)
        mock_llm = MagicMock(spec=ILLMProvider)
        mock_tts = MagicMock(spec=ITTSProvider)

        mock_stt_factory.create.return_value = mock_stt
        mock_llm_factory.create.return_value = mock_llm
        mock_tts_factory.create_default.return_value = mock_tts

        # Simulate what interaction_ws.py does
        from src.domain.services.interaction.cascade_mode_factory import (
            CascadeModeFactory,
        )

        factory = CascadeModeFactory()
        config = {"stt_provider": "azure", "llm_provider": "openai", "tts_provider": "azure"}
        service = factory.create(config)

        assert isinstance(service, InteractionModeService)
        assert service.mode_name == "cascade"

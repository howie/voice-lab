"""Unit tests for TTS provider adapters.

T022: Unit tests for provider adapters (Azure, GCP, ElevenLabs, VoAI)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest, TTSResult, VoiceProfile
from src.infrastructure.providers.tts.azure import AZURE_VOICES, AzureTTSProvider
from src.infrastructure.providers.tts.elevenlabs import (
    ELEVENLABS_VOICES,
    ElevenLabsTTSProvider,
)
from src.infrastructure.providers.tts.google import GOOGLE_VOICES, GoogleTTSProvider
from src.infrastructure.providers.tts.voai import VOAI_VOICES, VoAITTSProvider


@pytest.fixture
def sample_request() -> TTSRequest:
    """Create a sample TTS request for testing."""
    return TTSRequest(
        text="Hello, this is a test.",
        voice_id="en-US-JennyNeural",
        provider="azure",
        language="en-US",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


@pytest.fixture
def mock_audio_frame():
    """Create a mock Pipecat audio frame."""
    frame = MagicMock()
    frame.audio = b"\x00\x01\x02\x03" * 100
    return frame


class TestAzureTTSProvider:
    """Tests for Azure Speech Services TTS provider."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = AzureTTSProvider(api_key="test-key", region="eastasia")
        assert provider.name == "azure"

    def test_display_name(self):
        """Test display name property."""
        provider = AzureTTSProvider(api_key="test-key")
        assert provider.display_name == "Azure Speech Services"

    def test_supported_formats(self):
        """Test supported audio formats."""
        provider = AzureTTSProvider(api_key="test-key")
        formats = provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats

    @pytest.mark.asyncio
    async def test_synthesize_success(self, sample_request: TTSRequest):
        """Test successful synthesis."""
        with patch(
            "src.infrastructure.providers.tts.azure.AzureTTSService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_frame = MagicMock()
            mock_frame.audio = b"\x00\x01" * 500

            async def mock_run_tts(text):
                yield mock_frame

            mock_service.run_tts = mock_run_tts
            mock_service_class.return_value = mock_service

            provider = AzureTTSProvider(api_key="test-key", region="eastasia")
            result = await provider.synthesize(sample_request)

            assert isinstance(result, TTSResult)
            assert result.audio.data is not None
            assert len(result.audio.data) > 0
            assert result.duration_ms >= 0
            assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_synthesize_stream(self, sample_request: TTSRequest):
        """Test streaming synthesis."""
        with patch(
            "src.infrastructure.providers.tts.azure.AzureTTSService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_frame = MagicMock()
            mock_frame.audio = b"\x00\x01" * 100

            async def mock_run_tts(text):
                for _ in range(3):
                    yield mock_frame

            mock_service.run_tts = mock_run_tts
            mock_service_class.return_value = mock_service

            provider = AzureTTSProvider(api_key="test-key")
            chunks = []
            async for chunk in provider.synthesize_stream(sample_request):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert all(isinstance(c, bytes) for c in chunks)

    @pytest.mark.asyncio
    async def test_list_voices_all(self):
        """Test listing all voices."""
        provider = AzureTTSProvider(api_key="test-key")
        voices = await provider.list_voices()

        assert len(voices) > 0
        assert all(isinstance(v, VoiceProfile) for v in voices)
        assert all(v.provider == "azure" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_by_language(self):
        """Test listing voices filtered by language."""
        provider = AzureTTSProvider(api_key="test-key")
        voices = await provider.list_voices(language="zh-TW")

        assert len(voices) > 0
        assert all(v.language == "zh-TW" for v in voices)

    @pytest.mark.asyncio
    async def test_get_voice_exists(self):
        """Test getting a specific voice that exists."""
        provider = AzureTTSProvider(api_key="test-key")
        voice = await provider.get_voice("zh-TW-HsiaoChenNeural")

        assert voice is not None
        assert voice.id == "zh-TW-HsiaoChenNeural"
        assert voice.provider == "azure"

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self):
        """Test getting a voice that doesn't exist."""
        provider = AzureTTSProvider(api_key="test-key")
        voice = await provider.get_voice("non-existent-voice")

        assert voice is None

    def test_get_supported_params(self):
        """Test getting supported parameter ranges."""
        provider = AzureTTSProvider(api_key="test-key")
        params = provider.get_supported_params()

        assert "speed" in params
        assert "pitch" in params
        assert params["speed"]["min"] == 0.5
        assert params["speed"]["max"] == 2.0

    @pytest.mark.asyncio
    async def test_health_check_configured(self):
        """Test health check when properly configured."""
        provider = AzureTTSProvider(api_key="test-key", region="eastasia")
        is_healthy = await provider.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        """Test health check when not configured."""
        provider = AzureTTSProvider(api_key="", region="")
        is_healthy = await provider.health_check()
        assert is_healthy is False


class TestGoogleTTSProvider:
    """Tests for Google Cloud TTS provider."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = GoogleTTSProvider(credentials_path="/path/to/creds.json")
        assert provider.name == "gcp"

    def test_display_name(self):
        """Test display name property."""
        provider = GoogleTTSProvider()
        assert provider.display_name == "Google Cloud TTS"

    def test_supported_formats(self):
        """Test supported audio formats."""
        provider = GoogleTTSProvider()
        formats = provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats
        assert AudioFormat.OGG in formats

    @pytest.mark.asyncio
    async def test_list_voices_all(self):
        """Test listing all voices."""
        provider = GoogleTTSProvider()
        voices = await provider.list_voices()

        assert len(voices) > 0
        assert all(isinstance(v, VoiceProfile) for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_by_language(self):
        """Test listing voices filtered by language."""
        provider = GoogleTTSProvider()
        voices = await provider.list_voices(language="ja-JP")

        assert len(voices) > 0
        assert all(v.language == "ja-JP" for v in voices)

    @pytest.mark.asyncio
    async def test_get_voice_exists(self):
        """Test getting a specific voice that exists."""
        provider = GoogleTTSProvider()
        voice = await provider.get_voice("cmn-TW-Standard-A")

        assert voice is not None
        assert voice.id == "cmn-TW-Standard-A"

    def test_get_supported_params(self):
        """Test getting supported parameter ranges."""
        provider = GoogleTTSProvider()
        params = provider.get_supported_params()

        assert "speed" in params
        assert "pitch" in params
        assert params["speed"]["min"] == 0.25
        assert params["speed"]["max"] == 4.0


class TestElevenLabsTTSProvider:
    """Tests for ElevenLabs TTS provider."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = ElevenLabsTTSProvider(api_key="test-key")
        assert provider.name == "elevenlabs"

    def test_display_name(self):
        """Test display name property."""
        provider = ElevenLabsTTSProvider()
        assert provider.display_name == "ElevenLabs"

    def test_supported_formats(self):
        """Test supported audio formats."""
        provider = ElevenLabsTTSProvider()
        formats = provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.PCM in formats

    @pytest.mark.asyncio
    async def test_list_voices_all(self):
        """Test listing all voices."""
        provider = ElevenLabsTTSProvider()
        voices = await provider.list_voices()

        assert len(voices) == len(ELEVENLABS_VOICES)
        assert all(v.language == "multilingual" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_with_language(self):
        """Test listing voices with language filter (multilingual support)."""
        provider = ElevenLabsTTSProvider()
        voices = await provider.list_voices(language="zh-TW")

        assert len(voices) == len(ELEVENLABS_VOICES)
        assert all(v.language == "zh-TW" for v in voices)

    @pytest.mark.asyncio
    async def test_get_voice_exists(self):
        """Test getting a specific voice that exists."""
        provider = ElevenLabsTTSProvider()
        voice = await provider.get_voice("21m00Tcm4TlvDq8ikWAM")

        assert voice is not None
        assert voice.name == "Rachel"

    def test_get_supported_params(self):
        """Test getting supported parameter ranges."""
        provider = ElevenLabsTTSProvider()
        params = provider.get_supported_params()

        assert "speed" in params
        assert params["speed"]["min"] == 0.5
        assert params["speed"]["max"] == 2.0


class TestVoAITTSProvider:
    """Tests for VoAI TTS provider."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = VoAITTSProvider(api_key="test-key")
        assert provider.name == "voai"

    def test_display_name(self):
        """Test display name property."""
        provider = VoAITTSProvider()
        assert provider.display_name == "VoAI 台灣語音"

    def test_supported_formats(self):
        """Test supported audio formats."""
        provider = VoAITTSProvider()
        formats = provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats

    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful synthesis via REST API."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"\x00\x01\x02\x03" * 500

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            provider = VoAITTSProvider(
                api_key="test-key", api_endpoint="https://api.voai.tw/v1"
            )

            request = TTSRequest(
                text="你好",
                voice_id="voai-tw-female-1",
                provider="voai",
                language="zh-TW",
            )

            result = await provider.synthesize(request)

            assert isinstance(result, TTSResult)
            assert result.audio.data is not None
            assert len(result.audio.data) > 0

    @pytest.mark.asyncio
    async def test_synthesize_api_error(self):
        """Test handling of API errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            provider = VoAITTSProvider(api_key="test-key")

            request = TTSRequest(
                text="你好",
                voice_id="voai-tw-female-1",
                provider="voai",
            )

            with pytest.raises(Exception) as exc_info:
                await provider.synthesize(request)

            assert "VoAI API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_voices_all(self):
        """Test listing all voices."""
        provider = VoAITTSProvider()
        voices = await provider.list_voices()

        total_voices = sum(len(v) for v in VOAI_VOICES.values())
        assert len(voices) == total_voices

    @pytest.mark.asyncio
    async def test_list_voices_by_language(self):
        """Test listing voices filtered by language."""
        provider = VoAITTSProvider()
        voices = await provider.list_voices(language="zh-TW")

        assert len(voices) == len(VOAI_VOICES["zh-TW"])
        assert all(v.language == "zh-TW" for v in voices)

    @pytest.mark.asyncio
    async def test_get_voice_exists(self):
        """Test getting a specific voice that exists."""
        provider = VoAITTSProvider()
        voice = await provider.get_voice("voai-tw-female-1")

        assert voice is not None
        assert voice.name == "小美"
        assert voice.language == "zh-TW"

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self):
        """Test getting a voice that doesn't exist."""
        provider = VoAITTSProvider()
        voice = await provider.get_voice("non-existent-voice")

        assert voice is None

    def test_get_supported_params(self):
        """Test getting supported parameter ranges."""
        provider = VoAITTSProvider()
        params = provider.get_supported_params()

        assert "speed" in params
        assert params["speed"]["min"] == 0.5
        assert params["speed"]["max"] == 2.0

    @pytest.mark.asyncio
    async def test_health_check_configured(self):
        """Test health check when properly configured."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            provider = VoAITTSProvider(api_key="test-key")
            is_healthy = await provider.health_check()

            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        """Test health check when not configured."""
        provider = VoAITTSProvider(api_key="")
        is_healthy = await provider.health_check()
        assert is_healthy is False


class TestProviderVoiceMappings:
    """Tests for provider voice mappings consistency."""

    def test_azure_voices_have_required_fields(self):
        """Test Azure voice mappings have all required fields."""
        for _lang, voices in AZURE_VOICES.items():
            for voice in voices:
                assert "id" in voice
                assert "name" in voice
                assert "gender" in voice

    def test_google_voices_have_required_fields(self):
        """Test Google voice mappings have all required fields."""
        for _lang, voices in GOOGLE_VOICES.items():
            for voice in voices:
                assert "id" in voice
                assert "name" in voice
                assert "gender" in voice

    def test_elevenlabs_voices_have_required_fields(self):
        """Test ElevenLabs voice mappings have all required fields."""
        for voice in ELEVENLABS_VOICES:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice

    def test_voai_voices_have_required_fields(self):
        """Test VoAI voice mappings have all required fields."""
        for _lang, voices in VOAI_VOICES.items():
            for voice in voices:
                assert "id" in voice
                assert "name" in voice
                assert "gender" in voice

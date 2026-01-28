"""Unit tests for Gemini TTS provider.

Tests for the Gemini TTS provider implementation including:
- Voice listing and retrieval
- Synthesis with style prompts
- PCM to audio format conversion
- Health check functionality
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender
from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider


@pytest.fixture
def gemini_provider() -> GeminiTTSProvider:
    """Create a Gemini TTS provider for testing."""
    return GeminiTTSProvider(api_key="test-api-key")


@pytest.fixture
def sample_request() -> TTSRequest:
    """Create a sample TTS request for testing."""
    return TTSRequest(
        text="Hello, this is a test.",
        voice_id="Kore",
        provider="gemini",
        language="zh-TW",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


@pytest.fixture
def sample_request_with_style() -> TTSRequest:
    """Create a sample TTS request with style prompt."""
    return TTSRequest(
        text="Hello, this is a test.",
        voice_id="Kore",
        provider="gemini",
        language="zh-TW",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
        style_prompt="Say this cheerfully with excitement",
    )


class TestGeminiTTSProvider:
    """Tests for Gemini TTS provider."""

    def test_provider_name(self, gemini_provider: GeminiTTSProvider):
        """Test provider name property."""
        assert gemini_provider.name == "gemini"

    def test_display_name(self, gemini_provider: GeminiTTSProvider):
        """Test display name property."""
        assert gemini_provider.display_name == "Gemini TTS"

    def test_supported_formats(self, gemini_provider: GeminiTTSProvider):
        """Test supported audio formats."""
        formats = gemini_provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats
        assert AudioFormat.OGG in formats

    def test_default_model(self):
        """Test default model is set correctly."""
        provider = GeminiTTSProvider(api_key="test-key")
        assert provider._model == "gemini-2.5-pro-preview-tts"

    def test_custom_model(self):
        """Test custom model can be specified."""
        provider = GeminiTTSProvider(
            api_key="test-key",
            model="gemini-2.5-flash-preview-tts",
        )
        assert provider._model == "gemini-2.5-flash-preview-tts"

    @pytest.mark.asyncio
    async def test_list_voices_all(self, gemini_provider: GeminiTTSProvider):
        """Test listing all voices."""
        voices = await gemini_provider.list_voices()

        assert len(voices) == 30  # 30 prebuilt Gemini voices
        assert all(v.provider == "gemini" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_with_language(self, gemini_provider: GeminiTTSProvider):
        """Test listing voices with language filter."""
        voices = await gemini_provider.list_voices(language="zh-TW")

        assert len(voices) == 30
        assert all(v.language == "zh-TW" for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_multilingual_default(self, gemini_provider: GeminiTTSProvider):
        """Test voices default to multilingual when no language specified."""
        voices = await gemini_provider.list_voices()

        assert all(v.language == "multilingual" for v in voices)

    @pytest.mark.asyncio
    async def test_get_voice_exists(self, gemini_provider: GeminiTTSProvider):
        """Test getting a specific voice that exists."""
        voice = await gemini_provider.get_voice("Kore")

        assert voice is not None
        assert voice.voice_id == "Kore"
        assert voice.display_name == "Kore"
        assert voice.gender == Gender.FEMALE
        assert "friendly" in voice.description.lower()

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self, gemini_provider: GeminiTTSProvider):
        """Test getting a voice that doesn't exist."""
        voice = await gemini_provider.get_voice("non-existent-voice")

        assert voice is None

    def test_get_supported_params(self, gemini_provider: GeminiTTSProvider):
        """Test getting supported parameter ranges."""
        params = gemini_provider.get_supported_params()

        assert "speed" in params
        assert "pitch" in params
        assert "volume" in params
        assert "style_prompt" in params
        assert params["style_prompt"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_health_check_configured(self, gemini_provider: GeminiTTSProvider):
        """Test health check when properly configured."""
        with patch.object(gemini_provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            is_healthy = await gemini_provider.health_check()
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        """Test health check when not configured."""
        provider = GeminiTTSProvider(api_key="")
        is_healthy = await provider.health_check()
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self, gemini_provider: GeminiTTSProvider):
        """Test health check when API returns error."""
        with patch.object(gemini_provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection error")

            is_healthy = await gemini_provider.health_check()
            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_synthesize_success(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test successful synthesis."""
        # Create mock PCM data (simple silence)
        pcm_data = b"\x00\x00" * 24000  # 1 second of silence at 24kHz
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        # Mock the PCM conversion to avoid ffmpeg dependency
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            result = await gemini_provider.synthesize(sample_request)

            assert result is not None
            assert result.audio.data is not None
            assert len(result.audio.data) > 0
            assert result.audio.format == AudioFormat.MP3

    @pytest.mark.asyncio
    async def test_synthesize_with_style_prompt(
        self, gemini_provider: GeminiTTSProvider, sample_request_with_style: TTSRequest
    ):
        """Test synthesis with style prompt."""
        pcm_data = b"\x00\x00" * 24000
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        # Mock the PCM conversion to avoid ffmpeg dependency
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            await gemini_provider.synthesize(sample_request_with_style)

            # Verify style prompt was included in the request
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            text_content = payload["contents"][0]["parts"][0]["text"]
            assert "Say this cheerfully with excitement" in text_content

    @pytest.mark.asyncio
    async def test_synthesize_api_error(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test handling of API errors."""
        with patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="API Error"):
                await gemini_provider.synthesize(sample_request)

    @pytest.mark.asyncio
    async def test_synthesize_stream(
        self, gemini_provider: GeminiTTSProvider, sample_request: TTSRequest
    ):
        """Test streaming synthesis."""
        pcm_data = b"\x00\x00" * 24000
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        # Mock the PCM conversion to avoid ffmpeg dependency
        mock_mp3_data = b"mock-mp3-audio-data"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            chunks = []
            async for chunk in gemini_provider.synthesize_stream(sample_request):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert all(isinstance(c, bytes) for c in chunks)


class TestGeminiVoices:
    """Tests for Gemini voice definitions."""

    def test_voices_have_required_fields(self):
        """Test all Gemini voices have required fields."""
        for _voice_id, info in GeminiTTSProvider.VOICES.items():
            assert "gender" in info
            assert "description" in info
            assert info["gender"] in ("male", "female")

    def test_expected_voices_exist(self):
        """Test expected voices are defined."""
        expected_voices = ["Kore", "Charon", "Aoede", "Puck", "Zephyr"]
        for voice in expected_voices:
            assert voice in GeminiTTSProvider.VOICES

    def test_voice_count(self):
        """Test correct number of voices defined."""
        assert len(GeminiTTSProvider.VOICES) == 30

    def test_kore_recommended_for_chinese(self):
        """Test Kore is recommended for Chinese."""
        kore_info = GeminiTTSProvider.VOICES["Kore"]
        assert "chinese" in kore_info["description"].lower()

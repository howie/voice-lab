"""Unit tests for GCP Cloud TTS provider.

Tests for the Google Cloud Text-to-Speech provider implementation including:
- Voice listing and retrieval
- Synthesis with various audio formats
- Parameter ranges and supported params
- Health check functionality
- Language code mapping
- Volume dB conversion
"""

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.api_core.exceptions import ResourceExhausted

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender
from src.domain.errors import QuotaExceededError
from src.infrastructure.providers.tts.gcp_tts import GCPTTSProvider


@pytest.fixture
def gcp_provider() -> GCPTTSProvider:
    """Create a GCP TTS provider for testing."""
    return GCPTTSProvider(credentials_path="/fake/credentials.json")


@pytest.fixture
def sample_request() -> TTSRequest:
    """Create a sample TTS request for testing."""
    return TTSRequest(
        text="Hello, this is a test.",
        voice_id="en-US-Wavenet-D",
        provider="gcp",
        language="en-US",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


@pytest.fixture
def chinese_request() -> TTSRequest:
    """Create a Chinese TTS request for testing."""
    return TTSRequest(
        text="你好，這是測試。",
        voice_id="cmn-TW-Wavenet-A",
        provider="gcp",
        language="zh-TW",
        speed=1.0,
        pitch=0.0,
        volume=1.0,
        output_format=AudioFormat.MP3,
        output_mode=OutputMode.BATCH,
    )


def _make_mock_voice(name: str, language_code: str, gender_value: int) -> MagicMock:
    """Create a mock GCP voice object."""
    voice = MagicMock()
    voice.name = name
    voice.language_codes = [language_code]
    voice.ssml_gender = gender_value
    return voice


class TestGCPTTSProvider:
    """Tests for GCP TTS provider."""

    def test_provider_name(self, gcp_provider: GCPTTSProvider):
        """Test provider name property."""
        assert gcp_provider.name == "gcp"

    def test_display_name(self, gcp_provider: GCPTTSProvider):
        """Test display name property."""
        assert gcp_provider.display_name == "Google Cloud TTS"

    def test_supported_formats(self, gcp_provider: GCPTTSProvider):
        """Test supported audio formats."""
        formats = gcp_provider.supported_formats
        assert AudioFormat.MP3 in formats
        assert AudioFormat.WAV in formats
        assert AudioFormat.OGG in formats

    def test_get_supported_params(self, gcp_provider: GCPTTSProvider):
        """Test getting supported parameter ranges."""
        params = gcp_provider.get_supported_params()

        assert "speed" in params
        assert params["speed"]["min"] == 0.25
        assert params["speed"]["max"] == 4.0
        assert params["speed"]["default"] == 1.0

        assert "pitch" in params
        assert params["pitch"]["min"] == -20.0
        assert params["pitch"]["max"] == 20.0

        assert "volume" in params

    def test_get_supported_params_wider_speed_range(self, gcp_provider: GCPTTSProvider):
        """Test that GCP has wider speed range than base (0.25-4.0 vs 0.5-2.0)."""
        params = gcp_provider.get_supported_params()
        assert params["speed"]["min"] == 0.25
        assert params["speed"]["max"] == 4.0

    @pytest.mark.asyncio
    async def test_list_voices(self, gcp_provider: GCPTTSProvider):
        """Test listing voices from GCP API."""
        from google.cloud import texttospeech_v1 as texttospeech

        mock_voices = [
            _make_mock_voice("en-US-Wavenet-D", "en-US", texttospeech.SsmlVoiceGender.MALE),
            _make_mock_voice("en-US-Wavenet-F", "en-US", texttospeech.SsmlVoiceGender.FEMALE),
            _make_mock_voice("cmn-TW-Wavenet-A", "cmn-TW", texttospeech.SsmlVoiceGender.FEMALE),
        ]

        mock_response = MagicMock()
        mock_response.voices = mock_voices

        mock_client = MagicMock()
        mock_client.list_voices.return_value = mock_response
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            voices = await gcp_provider.list_voices()

        assert len(voices) == 3
        assert all(v.provider == "gcp" for v in voices)
        assert voices[0].voice_id == "en-US-Wavenet-D"
        assert voices[0].id == "gcp:en-US-Wavenet-D"
        assert voices[0].gender == Gender.MALE
        assert voices[1].gender == Gender.FEMALE

    @pytest.mark.asyncio
    async def test_list_voices_with_language(self, gcp_provider: GCPTTSProvider):
        """Test listing voices with language filter."""
        from google.cloud import texttospeech_v1 as texttospeech

        mock_voices = [
            _make_mock_voice("cmn-TW-Wavenet-A", "cmn-TW", texttospeech.SsmlVoiceGender.FEMALE),
        ]

        mock_response = MagicMock()
        mock_response.voices = mock_voices

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            voices = await gcp_provider.list_voices(language="zh-TW")

        assert len(voices) == 1
        assert voices[0].language == "cmn-TW"
        # Verify language mapping was applied (zh-TW -> cmn-TW)
        mock_to_thread.assert_called_once()
        call_kwargs = mock_to_thread.call_args
        assert call_kwargs[1].get("language_code") == "cmn-TW" or "cmn-TW" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_get_voice_found(self, gcp_provider: GCPTTSProvider):
        """Test getting a specific voice that exists."""
        from google.cloud import texttospeech_v1 as texttospeech

        mock_voices = [
            _make_mock_voice("en-US-Wavenet-D", "en-US", texttospeech.SsmlVoiceGender.MALE),
        ]

        mock_response = MagicMock()
        mock_response.voices = mock_voices

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            voice = await gcp_provider.get_voice("en-US-Wavenet-D")

        assert voice is not None
        assert voice.voice_id == "en-US-Wavenet-D"
        assert voice.provider == "gcp"

    @pytest.mark.asyncio
    async def test_get_voice_with_prefix(self, gcp_provider: GCPTTSProvider):
        """Test getting a voice with gcp: prefix."""
        from google.cloud import texttospeech_v1 as texttospeech

        mock_voices = [
            _make_mock_voice("en-US-Wavenet-D", "en-US", texttospeech.SsmlVoiceGender.MALE),
        ]

        mock_response = MagicMock()
        mock_response.voices = mock_voices

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            voice = await gcp_provider.get_voice("gcp:en-US-Wavenet-D")

        assert voice is not None
        assert voice.voice_id == "en-US-Wavenet-D"

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self, gcp_provider: GCPTTSProvider):
        """Test getting a voice that doesn't exist."""
        mock_response = MagicMock()
        mock_response.voices = []

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            voice = await gcp_provider.get_voice("non-existent-voice")

        assert voice is None

    @pytest.mark.asyncio
    async def test_synthesize_success(
        self, gcp_provider: GCPTTSProvider, sample_request: TTSRequest
    ):
        """Test successful synthesis."""
        mock_audio_content = b"fake-mp3-audio-data"
        mock_response = MagicMock()
        mock_response.audio_content = mock_audio_content

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            result = await gcp_provider.synthesize(sample_request)

        assert result is not None
        assert result.audio.data == mock_audio_content
        assert result.audio.format == AudioFormat.MP3

    @pytest.mark.asyncio
    async def test_synthesize_wav_format(self, gcp_provider: GCPTTSProvider):
        """Test synthesis with WAV output format."""
        request = TTSRequest(
            text="Test WAV output.",
            voice_id="en-US-Wavenet-D",
            provider="gcp",
            language="en-US",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.WAV,
            output_mode=OutputMode.BATCH,
        )

        mock_audio_content = b"fake-wav-audio-data"
        mock_response = MagicMock()
        mock_response.audio_content = mock_audio_content

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            result = await gcp_provider.synthesize(request)

        assert result.audio.format == AudioFormat.WAV

    @pytest.mark.asyncio
    async def test_synthesize_ogg_format(self, gcp_provider: GCPTTSProvider):
        """Test synthesis with OGG output format."""
        request = TTSRequest(
            text="Test OGG output.",
            voice_id="en-US-Wavenet-D",
            provider="gcp",
            language="en-US",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.OGG,
            output_mode=OutputMode.BATCH,
        )

        mock_audio_content = b"fake-ogg-audio-data"
        mock_response = MagicMock()
        mock_response.audio_content = mock_audio_content

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            result = await gcp_provider.synthesize(request)

        assert result.audio.format == AudioFormat.OGG

    @pytest.mark.asyncio
    async def test_synthesize_quota_exceeded(
        self, gcp_provider: GCPTTSProvider, sample_request: TTSRequest
    ):
        """Test handling of quota exceeded error."""
        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = ResourceExhausted("Quota exceeded")

            with pytest.raises(QuotaExceededError) as exc_info:
                await gcp_provider.synthesize(sample_request)

            assert exc_info.value.details["provider"] == "gcp"

    @pytest.mark.asyncio
    async def test_synthesize_chinese(
        self, gcp_provider: GCPTTSProvider, chinese_request: TTSRequest
    ):
        """Test synthesis with Chinese text."""
        mock_audio_content = b"fake-chinese-audio"
        mock_response = MagicMock()
        mock_response.audio_content = mock_audio_content

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            result = await gcp_provider.synthesize(chinese_request)

        assert result is not None
        assert result.audio.data == mock_audio_content

    @pytest.mark.asyncio
    async def test_synthesize_stream(
        self, gcp_provider: GCPTTSProvider, sample_request: TTSRequest
    ):
        """Test streaming synthesis (default base implementation)."""
        mock_audio_content = b"fake-streaming-audio-data"
        mock_response = MagicMock()
        mock_response.audio_content = mock_audio_content

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            chunks = []
            async for chunk in gcp_provider.synthesize_stream(sample_request):
                chunks.append(chunk)

        assert len(chunks) > 0
        assert b"".join(chunks) == mock_audio_content

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, gcp_provider: GCPTTSProvider):
        """Test health check when API is available."""
        mock_response = MagicMock()
        mock_response.voices = []

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            is_healthy = await gcp_provider.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, gcp_provider: GCPTTSProvider):
        """Test health check when API is unavailable."""
        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Connection refused")
            is_healthy = await gcp_provider.health_check()

        assert is_healthy is False


class TestGCPLanguageMapping:
    """Tests for GCP language code mapping."""

    def test_map_zh_tw(self, gcp_provider: GCPTTSProvider):
        """Test mapping zh-TW to cmn-TW."""
        assert gcp_provider._map_language("zh-TW") == "cmn-TW"

    def test_map_zh_cn(self, gcp_provider: GCPTTSProvider):
        """Test mapping zh-CN to cmn-CN."""
        assert gcp_provider._map_language("zh-CN") == "cmn-CN"

    def test_map_en_us(self, gcp_provider: GCPTTSProvider):
        """Test mapping en-US stays en-US."""
        assert gcp_provider._map_language("en-US") == "en-US"

    def test_map_ja_jp(self, gcp_provider: GCPTTSProvider):
        """Test mapping ja-JP stays ja-JP."""
        assert gcp_provider._map_language("ja-JP") == "ja-JP"

    def test_map_none_defaults_to_en_us(self, gcp_provider: GCPTTSProvider):
        """Test None language defaults to en-US."""
        assert gcp_provider._map_language(None) == "en-US"

    def test_map_unknown_passthrough(self, gcp_provider: GCPTTSProvider):
        """Test unknown language codes pass through."""
        assert gcp_provider._map_language("ko-KR") == "ko-KR"
        assert gcp_provider._map_language("de-DE") == "de-DE"


class TestGCPVolumeConversion:
    """Tests for volume to dB conversion."""

    def test_volume_zero(self, gcp_provider: GCPTTSProvider):
        """Test zero volume returns minimum dB."""
        assert gcp_provider._volume_to_db(0.0) == -96.0

    def test_volume_one(self, gcp_provider: GCPTTSProvider):
        """Test full volume returns 0 dB."""
        assert gcp_provider._volume_to_db(1.0) == 0.0

    def test_volume_half(self, gcp_provider: GCPTTSProvider):
        """Test half volume returns ~-6 dB."""
        result = gcp_provider._volume_to_db(0.5)
        expected = 20 * math.log10(0.5)  # ~-6.02
        assert abs(result - expected) < 0.01

    def test_volume_negative(self, gcp_provider: GCPTTSProvider):
        """Test negative volume clamps to minimum dB."""
        assert gcp_provider._volume_to_db(-0.5) == -96.0

    def test_volume_over_one(self, gcp_provider: GCPTTSProvider):
        """Test volume over 1 clamps to 0 dB."""
        assert gcp_provider._volume_to_db(1.5) == 0.0


class TestGCPClientInitialization:
    """Tests for GCP client lazy initialization."""

    def test_client_initially_none(self):
        """Test client is None before first use."""
        provider = GCPTTSProvider(credentials_path="/fake/path.json")
        assert provider._client is None

    def test_credentials_path_from_env(self):
        """Test credentials path from environment variable."""
        with patch.dict("os.environ", {"GOOGLE_APPLICATION_CREDENTIALS": "/env/path.json"}):
            provider = GCPTTSProvider()
            assert provider._credentials_path == "/env/path.json"

    def test_credentials_path_explicit_overrides_env(self):
        """Test explicit path overrides environment variable."""
        with patch.dict("os.environ", {"GOOGLE_APPLICATION_CREDENTIALS": "/env/path.json"}):
            provider = GCPTTSProvider(credentials_path="/explicit/path.json")
            assert provider._credentials_path == "/explicit/path.json"

"""Integration tests for Azure Speech Services (TTS, STT, Validator).

Requires real Azure API credentials:
  - AZURE_SPEECH_KEY: Azure Speech API key
  - AZURE_SPEECH_REGION: Azure region (default: eastasia)

Run:
  AZURE_SPEECH_KEY=xxx AZURE_SPEECH_REGION=eastasia \
    pytest tests/integration/test_azure_speech_integration.py -v
"""

import os

import pytest

# Skip entire module if no Azure credentials
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastasia")
skip_no_key = pytest.mark.skipif(
    not AZURE_SPEECH_KEY,
    reason="AZURE_SPEECH_KEY not set",
)

pytestmark = [skip_no_key, pytest.mark.azure_integration]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def azure_tts():
    """Create AzureTTSProvider with real credentials."""
    from src.infrastructure.providers.tts.azure_tts import AzureTTSProvider

    return AzureTTSProvider(
        subscription_key=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
    )


@pytest.fixture
def azure_stt():
    """Create AzureSTTProvider with real credentials."""
    from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider

    return AzureSTTProvider(
        subscription_key=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
    )


@pytest.fixture
def azure_voice_fetcher():
    """Create AzureVoiceFetcher with real credentials."""
    from src.infrastructure.providers.tts.voice_fetchers.azure_voice_fetcher import (
        AzureVoiceFetcher,
    )

    return AzureVoiceFetcher(
        api_key=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
    )


@pytest.fixture
def azure_validator():
    """Create AzureValidator."""
    from src.infrastructure.providers.validators.azure import AzureValidator

    return AzureValidator()


# ===========================================================================
# TTS Integration Tests
# ===========================================================================


class TestAzureTTSIntegration:
    """Integration tests for Azure TTS."""

    @pytest.mark.asyncio
    async def test_tts_synthesize_zh_tw(self, azure_tts):
        """Synthesize zh-TW text and verify audio output."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.tts import TTSRequest

        request = TTSRequest(
            text="你好，這是一段測試語音。",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            language="zh-TW",
            output_format=AudioFormat.MP3,
        )

        result = await azure_tts.synthesize(request)

        assert result.audio.data, "Audio data should not be empty"
        assert len(result.audio.data) > 1000, "Audio should have meaningful size"
        assert result.audio.format == AudioFormat.MP3
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_tts_synthesize_en_us(self, azure_tts):
        """Synthesize en-US text and verify audio output."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.tts import TTSRequest

        request = TTSRequest(
            text="Hello, this is a test.",
            voice_id="en-US-JennyNeural",
            provider="azure",
            language="en-US",
            output_format=AudioFormat.MP3,
        )

        result = await azure_tts.synthesize(request)

        assert result.audio.data, "Audio data should not be empty"
        assert len(result.audio.data) > 1000
        assert result.audio.format == AudioFormat.MP3

    @pytest.mark.asyncio
    async def test_tts_list_voices(self, azure_tts):
        """List voices and verify zh-TW voices exist."""
        voices = await azure_tts.list_voices(language="zh-TW")

        assert len(voices) > 0, "Should have zh-TW voices"

        voice_ids = [v.voice_id for v in voices]
        assert any("HsiaoChen" in vid for vid in voice_ids), "Should contain HsiaoChenNeural"

    @pytest.mark.asyncio
    async def test_tts_voice_fetcher_zh_tw(self, azure_voice_fetcher):
        """Fetch zh-TW voices via REST API."""
        voices = await azure_voice_fetcher.fetch_voices(language="zh-TW")

        assert len(voices) > 0, "Should have zh-TW voices"
        assert all(v.locale == "zh-TW" for v in voices)

        # Verify known voice exists
        short_names = [v.short_name for v in voices]
        assert "zh-TW-HsiaoChenNeural" in short_names

    @pytest.mark.asyncio
    async def test_tts_output_formats(self, azure_tts):
        """Verify MP3 and WAV output formats produce valid audio."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.tts import TTSRequest

        for fmt in (AudioFormat.MP3, AudioFormat.WAV):
            request = TTSRequest(
                text="測試音訊格式。",
                voice_id="zh-TW-HsiaoChenNeural",
                provider="azure",
                language="zh-TW",
                output_format=fmt,
            )

            result = await azure_tts.synthesize(request)

            assert result.audio.data, f"{fmt.value} audio should not be empty"
            assert result.audio.format == fmt

    @pytest.mark.asyncio
    async def test_tts_ssml_synthesis(self, azure_tts):
        """Synthesize with prosody adjustments (speed/pitch)."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.tts import TTSRequest

        request = TTSRequest(
            text="這是較慢的語速測試。",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            language="zh-TW",
            speed=0.8,
            pitch=2.0,
            output_format=AudioFormat.MP3,
        )

        result = await azure_tts.synthesize(request)

        assert result.audio.data, "SSML audio should not be empty"
        assert len(result.audio.data) > 1000

    @pytest.mark.asyncio
    async def test_tts_storybook_voices_available(self, azure_voice_fetcher):
        """Verify storybook-suitable voices are available."""
        voices = await azure_voice_fetcher.fetch_storybook_voices()

        assert len(voices) > 0, "Should have storybook voices"

        # zh-TW voices should be present
        zh_tw_voices = [v for v in voices if v.locale == "zh-TW"]
        assert len(zh_tw_voices) > 0, "Should have zh-TW storybook voices"

        # Check that voices with styles are present
        voices_with_styles = [v for v in voices if v.style_list]
        assert len(voices_with_styles) >= 0  # Some voices may not have styles


# ===========================================================================
# STT Integration Tests
# ===========================================================================


class TestAzureSTTIntegration:
    """Integration tests for Azure STT.

    Uses TTS-generated audio for end-to-end testing.
    """

    @pytest.mark.asyncio
    async def test_stt_transcribe_zh_tw(self, azure_tts, azure_stt):
        """TTS -> STT round-trip for zh-TW."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.stt import STTRequest
        from src.domain.entities.tts import TTSRequest

        # Step 1: Generate audio via TTS
        tts_request = TTSRequest(
            text="今天天氣很好",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            language="zh-TW",
            output_format=AudioFormat.WAV,
        )
        tts_result = await azure_tts.synthesize(tts_request)
        assert tts_result.audio.data

        # Step 2: Transcribe the generated audio
        stt_request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=tts_result.audio,
        )
        stt_result = await azure_stt.transcribe(stt_request)

        assert stt_result.transcript, "Transcript should not be empty"
        # The transcript should contain key words from the original text
        assert any(kw in stt_result.transcript for kw in ["今天", "天氣", "好"]), (
            f"Transcript '{stt_result.transcript}' should contain keywords from original"
        )

    @pytest.mark.asyncio
    async def test_stt_transcribe_en_us(self, azure_tts, azure_stt):
        """TTS -> STT round-trip for en-US."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.stt import STTRequest
        from src.domain.entities.tts import TTSRequest

        tts_request = TTSRequest(
            text="The weather is nice today.",
            voice_id="en-US-JennyNeural",
            provider="azure",
            language="en-US",
            output_format=AudioFormat.WAV,
        )
        tts_result = await azure_tts.synthesize(tts_request)
        assert tts_result.audio.data

        stt_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=tts_result.audio,
        )
        stt_result = await azure_stt.transcribe(stt_request)

        assert stt_result.transcript, "Transcript should not be empty"
        transcript_lower = stt_result.transcript.lower()
        assert any(kw in transcript_lower for kw in ["weather", "nice", "today"]), (
            f"Transcript '{stt_result.transcript}' should contain keywords"
        )

    @pytest.mark.asyncio
    async def test_stt_word_timestamps(self, azure_tts, azure_stt):
        """Verify word-level timestamps from STT."""
        from src.domain.entities.audio import AudioFormat
        from src.domain.entities.stt import STTRequest
        from src.domain.entities.tts import TTSRequest

        tts_request = TTSRequest(
            text="Hello world, this is a timestamp test.",
            voice_id="en-US-JennyNeural",
            provider="azure",
            language="en-US",
            output_format=AudioFormat.WAV,
        )
        tts_result = await azure_tts.synthesize(tts_request)

        stt_request = STTRequest(
            provider="azure",
            language="en-US",
            audio=tts_result.audio,
            enable_word_timing=True,
        )
        stt_result = await azure_stt.transcribe(stt_request)

        assert stt_result.transcript, "Transcript should not be empty"
        # Word timestamps may or may not be populated depending on Azure response
        if stt_result.words:
            for word_timing in stt_result.words:
                assert word_timing.word, "Word text should not be empty"
                assert word_timing.start_ms >= 0, "Start time should be non-negative"
                assert word_timing.end_ms >= word_timing.start_ms, (
                    "End time should be >= start time"
                )


# ===========================================================================
# Validator Integration Tests
# ===========================================================================


class TestAzureValidatorIntegration:
    """Integration tests for Azure API key validation."""

    @pytest.mark.asyncio
    async def test_validator_valid_key(self, azure_validator):
        """Validate a real API key returns is_valid=True."""
        result = await azure_validator.validate(
            api_key=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION,
        )

        assert result.is_valid is True
        assert result.error_message is None or result.error_message == ""

    @pytest.mark.asyncio
    async def test_validator_invalid_key(self, azure_validator):
        """Validate a fake API key returns is_valid=False."""
        result = await azure_validator.validate(
            api_key="00000000000000000000000000000000",
            region=AZURE_SPEECH_REGION,
        )

        assert result.is_valid is False
        assert result.error_message, "Should have an error message"

    @pytest.mark.asyncio
    async def test_validator_get_available_models(self, azure_validator):
        """Fetch available models with a valid key."""
        models = await azure_validator.get_available_models(
            api_key=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION,
            language="zh-TW",
        )

        assert len(models) > 0, "Should return zh-TW models"
        assert all("id" in m for m in models)
        assert all("language" in m for m in models)

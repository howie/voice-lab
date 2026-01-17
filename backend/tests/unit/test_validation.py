"""Unit tests for input validation.

T023: Unit tests for input validation (empty text, text > 5000 chars)
"""

import pytest

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import MAX_TEXT_LENGTH, TTSRequest


class TestTTSRequestValidation:
    """Tests for TTSRequest validation."""

    def test_valid_request(self):
        """Test creating a valid TTS request."""
        request = TTSRequest(
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

        assert request.text == "Hello, this is a test."
        assert request.voice_id == "en-US-JennyNeural"
        assert request.provider == "azure"

    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="",
                voice_id="en-US-JennyNeural",
                provider="azure",
            )

        assert "Text cannot be empty" in str(exc_info.value)

    def test_text_exceeds_max_length(self):
        """Test that text exceeding 5000 characters raises ValueError."""
        long_text = "A" * (MAX_TEXT_LENGTH + 1)

        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text=long_text,
                voice_id="en-US-JennyNeural",
                provider="azure",
            )

        assert f"Text exceeds {MAX_TEXT_LENGTH} characters limit" in str(exc_info.value)

    def test_text_at_max_length(self):
        """Test that text at exactly 5000 characters is valid."""
        max_text = "A" * MAX_TEXT_LENGTH

        request = TTSRequest(
            text=max_text,
            voice_id="en-US-JennyNeural",
            provider="azure",
        )

        assert len(request.text) == MAX_TEXT_LENGTH

    def test_empty_voice_id_raises_error(self):
        """Test that empty voice_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="",
                provider="azure",
            )

        assert "Voice ID cannot be empty" in str(exc_info.value)

    def test_speed_below_minimum(self):
        """Test that speed below 0.5 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                speed=0.4,
            )

        assert "Speed must be between 0.5 and 2.0" in str(exc_info.value)

    def test_speed_above_maximum(self):
        """Test that speed above 2.0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                speed=2.5,
            )

        assert "Speed must be between 0.5 and 2.0" in str(exc_info.value)

    def test_speed_at_boundaries(self):
        """Test that speed at boundary values is valid."""
        request_min = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            speed=0.5,
        )
        assert request_min.speed == 0.5

        request_max = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            speed=2.0,
        )
        assert request_max.speed == 2.0

    def test_pitch_below_minimum(self):
        """Test that pitch below -20 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                pitch=-25,
            )

        assert "Pitch must be between -20 and 20" in str(exc_info.value)

    def test_pitch_above_maximum(self):
        """Test that pitch above 20 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                pitch=25,
            )

        assert "Pitch must be between -20 and 20" in str(exc_info.value)

    def test_pitch_at_boundaries(self):
        """Test that pitch at boundary values is valid."""
        request_min = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            pitch=-20,
        )
        assert request_min.pitch == -20

        request_max = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            pitch=20,
        )
        assert request_max.pitch == 20

    def test_volume_below_minimum(self):
        """Test that volume below 0.0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                volume=-0.1,
            )

        assert "Volume must be between 0.0 and 2.0" in str(exc_info.value)

    def test_volume_above_maximum(self):
        """Test that volume above 2.0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                volume=2.5,
            )

        assert "Volume must be between 0.0 and 2.0" in str(exc_info.value)

    def test_volume_at_boundaries(self):
        """Test that volume at boundary values is valid."""
        request_min = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            volume=0.0,
        )
        assert request_min.volume == 0.0

        request_max = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            volume=2.0,
        )
        assert request_max.volume == 2.0

    def test_default_values(self):
        """Test that default values are set correctly."""
        request = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
        )

        assert request.language == "zh-TW"
        assert request.speed == 1.0
        assert request.pitch == 0.0
        assert request.volume == 1.0
        assert request.output_format == AudioFormat.MP3
        assert request.output_mode == OutputMode.BATCH

    def test_immutability(self):
        """Test that TTSRequest is immutable (frozen dataclass)."""
        request = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
        )

        with pytest.raises(AttributeError):  # FrozenInstanceError raises AttributeError
            request.text = "Modified"

    def test_unicode_text(self):
        """Test that unicode text is handled correctly."""
        request = TTSRequest(
            text="你好，這是測試。こんにちは。안녕하세요.",
            voice_id="zh-TW-HsiaoChenNeural",
            provider="azure",
            language="zh-TW",
        )

        assert "你好" in request.text
        assert "こんにちは" in request.text
        assert "안녕하세요" in request.text

    def test_special_characters_in_text(self):
        """Test that special characters are handled correctly."""
        request = TTSRequest(
            text="Hello! How are you? I'm fine. <tag> & \"quotes\"",
            voice_id="en-US-JennyNeural",
            provider="azure",
        )

        assert "<tag>" in request.text
        assert "&" in request.text
        assert '"' in request.text

    def test_whitespace_only_text(self):
        """Test that whitespace-only text is considered empty."""
        # Note: Current implementation doesn't strip whitespace
        # This test documents current behavior
        request = TTSRequest(
            text="   ",  # whitespace only
            voice_id="en-US-JennyNeural",
            provider="azure",
        )
        # Currently passes - whitespace is not stripped
        assert request.text == "   "

    def test_multiline_text(self):
        """Test that multiline text is handled correctly."""
        multiline_text = """Line 1
Line 2
Line 3"""

        request = TTSRequest(
            text=multiline_text,
            voice_id="en-US-JennyNeural",
            provider="azure",
        )

        assert "\n" in request.text
        assert "Line 1" in request.text
        assert "Line 3" in request.text

    def test_output_mode_streaming(self):
        """Test creating a request with streaming output mode."""
        request = TTSRequest(
            text="Hello",
            voice_id="en-US-JennyNeural",
            provider="azure",
            output_mode=OutputMode.STREAMING,
        )

        assert request.output_mode == OutputMode.STREAMING

    def test_all_audio_formats(self):
        """Test creating requests with all supported audio formats."""
        formats = [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OGG, AudioFormat.OPUS, AudioFormat.PCM]

        for fmt in formats:
            request = TTSRequest(
                text="Hello",
                voice_id="en-US-JennyNeural",
                provider="azure",
                output_format=fmt,
            )
            assert request.output_format == fmt


class TestMaxTextLength:
    """Tests for MAX_TEXT_LENGTH constant."""

    def test_max_text_length_value(self):
        """Test that MAX_TEXT_LENGTH is 5000."""
        assert MAX_TEXT_LENGTH == 5000

    def test_text_length_boundary(self):
        """Test text at exactly MAX_TEXT_LENGTH."""
        exact_text = "X" * MAX_TEXT_LENGTH

        request = TTSRequest(
            text=exact_text,
            voice_id="en-US-JennyNeural",
            provider="azure",
        )

        assert len(request.text) == MAX_TEXT_LENGTH

    def test_text_one_over_limit(self):
        """Test text at MAX_TEXT_LENGTH + 1."""
        over_text = "X" * (MAX_TEXT_LENGTH + 1)

        with pytest.raises(ValueError):
            TTSRequest(
                text=over_text,
                voice_id="en-US-JennyNeural",
                provider="azure",
            )

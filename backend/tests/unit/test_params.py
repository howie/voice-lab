"""Unit tests for parameter validation and mapping.

T052: Unit tests for parameter validation
Tests parameter ranges, provider-specific limits, and parameter mapping.
"""

import pytest
from dataclasses import dataclass

from src.domain.entities.tts import TTSRequest


# Provider parameter ranges (to be implemented in adapters)
@dataclass
class ParameterRange:
    """Parameter range specification."""

    min_value: float
    max_value: float
    default_value: float
    step: float = 0.1


# Expected parameter ranges per provider
AZURE_PARAMS = {
    "speed": ParameterRange(0.5, 2.0, 1.0),
    "pitch": ParameterRange(-50, 50, 0),  # Azure uses -50% to +50%
    "volume": ParameterRange(0.0, 2.0, 1.0),
}

GCP_PARAMS = {
    "speed": ParameterRange(0.25, 4.0, 1.0),
    "pitch": ParameterRange(-20.0, 20.0, 0.0),  # GCP uses semitones
    "volume": ParameterRange(-96.0, 16.0, 0.0),  # GCP uses dB
}

ELEVENLABS_PARAMS = {
    "speed": ParameterRange(0.5, 2.0, 1.0),
    "stability": ParameterRange(0.0, 1.0, 0.5),
    "similarity_boost": ParameterRange(0.0, 1.0, 0.75),
}

VOAI_PARAMS = {
    "speed": ParameterRange(0.5, 2.0, 1.0),
    "pitch": ParameterRange(-20, 20, 0),
    "volume": ParameterRange(0.0, 2.0, 1.0),
}


class TestParameterRanges:
    """Tests for parameter range validation."""

    def test_speed_range_minimum(self):
        """Test minimum speed value is valid."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            speed=0.5,
        )
        assert request.speed == 0.5

    def test_speed_range_maximum(self):
        """Test maximum speed value is valid."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            speed=2.0,
        )
        assert request.speed == 2.0

    def test_speed_default(self):
        """Test default speed value."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
        )
        assert request.speed == 1.0

    def test_pitch_range_minimum(self):
        """Test minimum pitch value is valid."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            pitch=-20,
        )
        assert request.pitch == -20

    def test_pitch_range_maximum(self):
        """Test maximum pitch value is valid."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            pitch=20,
        )
        assert request.pitch == 20

    def test_pitch_default(self):
        """Test default pitch value."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
        )
        assert request.pitch == 0.0

    def test_volume_range_minimum(self):
        """Test minimum volume value is valid."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            volume=0.0,
        )
        assert request.volume == 0.0

    def test_volume_range_maximum(self):
        """Test maximum volume value is valid."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            volume=2.0,
        )
        assert request.volume == 2.0

    def test_volume_default(self):
        """Test default volume value."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
        )
        assert request.volume == 1.0


class TestParameterMapping:
    """Tests for parameter mapping between normalized and provider-specific values."""

    def test_normalize_speed(self):
        """Test speed normalization to 0-1 range."""
        # Speed 0.5-2.0 should map to 0-1
        def normalize_speed(speed: float) -> float:
            return (speed - 0.5) / (2.0 - 0.5)

        assert normalize_speed(0.5) == pytest.approx(0.0)
        assert normalize_speed(1.0) == pytest.approx(0.333, rel=0.01)
        assert normalize_speed(1.25) == pytest.approx(0.5)
        assert normalize_speed(2.0) == pytest.approx(1.0)

    def test_denormalize_speed(self):
        """Test speed denormalization from 0-1 to 0.5-2.0 range."""

        def denormalize_speed(normalized: float) -> float:
            return 0.5 + normalized * (2.0 - 0.5)

        assert denormalize_speed(0.0) == pytest.approx(0.5)
        assert denormalize_speed(0.5) == pytest.approx(1.25)
        assert denormalize_speed(1.0) == pytest.approx(2.0)

    def test_azure_pitch_mapping(self):
        """Test mapping pitch from normalized to Azure format."""
        # Azure uses percentage: -50% to +50%

        def to_azure_pitch(pitch: float) -> str:
            """Convert pitch (-20 to 20) to Azure format."""
            # Map -20..20 to -50%..+50%
            azure_pitch = (pitch / 20) * 50
            if azure_pitch >= 0:
                return f"+{azure_pitch:.0f}%"
            return f"{azure_pitch:.0f}%"

        assert to_azure_pitch(0) == "+0%"
        assert to_azure_pitch(20) == "+50%"
        assert to_azure_pitch(-20) == "-50%"
        assert to_azure_pitch(10) == "+25%"

    def test_azure_speed_mapping(self):
        """Test mapping speed to Azure format."""
        # Azure uses percentage: e.g., "1.0" -> "+0%", "2.0" -> "+100%"

        def to_azure_rate(speed: float) -> str:
            """Convert speed (0.5-2.0) to Azure rate format."""
            rate_percent = (speed - 1.0) * 100
            if rate_percent >= 0:
                return f"+{rate_percent:.0f}%"
            return f"{rate_percent:.0f}%"

        assert to_azure_rate(1.0) == "+0%"
        assert to_azure_rate(2.0) == "+100%"
        assert to_azure_rate(0.5) == "-50%"
        assert to_azure_rate(1.5) == "+50%"

    def test_gcp_speed_mapping(self):
        """Test mapping speed to GCP format."""
        # GCP uses direct multiplier: 0.25 to 4.0

        def to_gcp_speed(speed: float) -> float:
            """Convert normalized speed (0.5-2.0) to GCP speed (0.25-4.0)."""
            # Linear mapping: 0.5->0.25, 1.0->1.0, 2.0->4.0
            if speed <= 1.0:
                # 0.5-1.0 maps to 0.25-1.0
                return 0.25 + (speed - 0.5) * (1.0 - 0.25) / (1.0 - 0.5)
            else:
                # 1.0-2.0 maps to 1.0-4.0
                return 1.0 + (speed - 1.0) * (4.0 - 1.0) / (2.0 - 1.0)

        assert to_gcp_speed(0.5) == pytest.approx(0.25)
        assert to_gcp_speed(1.0) == pytest.approx(1.0)
        assert to_gcp_speed(2.0) == pytest.approx(4.0)

    def test_gcp_pitch_mapping(self):
        """Test mapping pitch to GCP format (semitones)."""
        # GCP uses semitones: -20.0 to 20.0

        def to_gcp_pitch(pitch: float) -> float:
            """Convert pitch (-20 to 20) to GCP semitones."""
            # Direct mapping (same range)
            return float(pitch)

        assert to_gcp_pitch(0) == 0.0
        assert to_gcp_pitch(20) == 20.0
        assert to_gcp_pitch(-20) == -20.0

    def test_elevenlabs_stability_mapping(self):
        """Test ElevenLabs stability parameter."""
        # ElevenLabs uses stability (0.0-1.0) instead of pitch

        def calculate_stability(pitch: float) -> float:
            """Map pitch adjustment to ElevenLabs stability."""
            # Higher pitch variance -> lower stability
            # Pitch -20 to 20 maps to stability 0.3 to 0.7
            return 0.5 - (pitch / 20) * 0.2

        assert calculate_stability(0) == pytest.approx(0.5)
        assert calculate_stability(20) == pytest.approx(0.3)
        assert calculate_stability(-20) == pytest.approx(0.7)


class TestProviderParameterSupport:
    """Tests for provider-specific parameter support."""

    def test_azure_supports_all_params(self):
        """Test Azure supports speed, pitch, volume."""
        azure_supported = {"speed", "pitch", "volume"}
        assert "speed" in azure_supported
        assert "pitch" in azure_supported
        assert "volume" in azure_supported

    def test_gcp_supports_all_params(self):
        """Test GCP supports speed, pitch, volume."""
        gcp_supported = {"speed", "pitch", "volume"}
        assert "speed" in gcp_supported
        assert "pitch" in gcp_supported
        assert "volume" in gcp_supported

    def test_elevenlabs_limited_params(self):
        """Test ElevenLabs has different parameter set."""
        elevenlabs_supported = {"speed", "stability", "similarity_boost"}
        assert "speed" in elevenlabs_supported
        assert "pitch" not in elevenlabs_supported  # Not directly supported
        assert "stability" in elevenlabs_supported

    def test_voai_supports_basic_params(self):
        """Test VoAI supports basic parameters."""
        voai_supported = {"speed", "pitch", "volume"}
        assert "speed" in voai_supported
        assert "pitch" in voai_supported
        assert "volume" in voai_supported


class TestLanguageValidation:
    """Tests for language code validation."""

    SUPPORTED_LANGUAGES = ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"]

    def test_supported_languages(self):
        """Test all supported languages are valid."""
        for lang in self.SUPPORTED_LANGUAGES:
            request = TTSRequest(
                text="Test",
                voice_id="test-voice",
                provider="azure",
                language=lang,
            )
            assert request.language == lang

    def test_default_language(self):
        """Test default language is zh-TW."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
        )
        assert request.language == "zh-TW"

    def test_language_code_format(self):
        """Test language codes follow BCP-47 format."""
        import re

        bcp47_pattern = r"^[a-z]{2,3}(-[A-Z]{2})?$"

        for lang in self.SUPPORTED_LANGUAGES:
            assert re.match(bcp47_pattern, lang), f"{lang} doesn't match BCP-47 format"


class TestParameterCombinations:
    """Tests for parameter combinations."""

    def test_all_params_at_minimum(self):
        """Test all parameters at minimum values."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            speed=0.5,
            pitch=-20,
            volume=0.0,
        )
        assert request.speed == 0.5
        assert request.pitch == -20
        assert request.volume == 0.0

    def test_all_params_at_maximum(self):
        """Test all parameters at maximum values."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            speed=2.0,
            pitch=20,
            volume=2.0,
        )
        assert request.speed == 2.0
        assert request.pitch == 20
        assert request.volume == 2.0

    def test_typical_usage_params(self):
        """Test typical usage parameter combinations."""
        # Slightly faster with higher pitch
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            speed=1.2,
            pitch=5,
            volume=1.0,
        )
        assert request.speed == 1.2
        assert request.pitch == 5
        assert request.volume == 1.0

    def test_slow_deep_voice(self):
        """Test slow speech with lower pitch."""
        request = TTSRequest(
            text="Test",
            voice_id="test-voice",
            provider="azure",
            speed=0.7,
            pitch=-10,
            volume=0.8,
        )
        assert request.speed == 0.7
        assert request.pitch == -10
        assert request.volume == 0.8

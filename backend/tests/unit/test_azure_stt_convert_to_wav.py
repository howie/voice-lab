"""Unit tests for AzureSTTProvider._convert_to_wav.

Tests the audio format conversion logic that converts non-WAV audio
to WAV before passing to Azure SDK.
"""

import io
import struct

import pytest
from pydub import AudioSegment

from src.domain.entities.audio import AudioData, AudioFormat
from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider


def _make_wav_bytes(sample_rate: int = 16000, channels: int = 1, duration_ms: int = 100) -> bytes:
    """Generate minimal valid WAV bytes for testing."""
    num_samples = int(sample_rate * duration_ms / 1000)
    # Generate silent 16-bit PCM samples
    raw_data = struct.pack(f"<{num_samples * channels}h", *([0] * num_samples * channels))
    segment = AudioSegment(
        data=raw_data,
        sample_width=2,
        frame_rate=sample_rate,
        channels=channels,
    )
    buf = io.BytesIO()
    segment.export(buf, format="wav")
    return buf.getvalue()


def _make_pcm_bytes(sample_rate: int = 16000, channels: int = 1, duration_ms: int = 100) -> bytes:
    """Generate raw 16-bit PCM bytes for testing."""
    num_samples = int(sample_rate * duration_ms / 1000)
    return struct.pack(f"<{num_samples * channels}h", *([0] * num_samples * channels))


def _make_mp3_bytes(sample_rate: int = 16000, channels: int = 1, duration_ms: int = 100) -> bytes:
    """Generate valid MP3 bytes for testing via pydub."""
    pcm = _make_pcm_bytes(sample_rate, channels, duration_ms)
    segment = AudioSegment(
        data=pcm,
        sample_width=2,
        frame_rate=sample_rate,
        channels=channels,
    )
    buf = io.BytesIO()
    segment.export(buf, format="mp3")
    return buf.getvalue()


class TestConvertToWav:
    """Tests for AzureSTTProvider._convert_to_wav static method."""

    def test_mp3_to_wav(self):
        """MP3 audio should be converted to valid WAV."""
        mp3_bytes = _make_mp3_bytes()
        audio_data = AudioData(data=mp3_bytes, format=AudioFormat.MP3, sample_rate=16000)

        result = AzureSTTProvider._convert_to_wav(mp3_bytes, AudioFormat.MP3, audio_data)

        # Result should be valid WAV (starts with RIFF header)
        assert result[:4] == b"RIFF"
        assert result[8:12] == b"WAVE"

    def test_pcm_to_wav(self):
        """Raw PCM audio should be converted to valid WAV using metadata."""
        pcm_bytes = _make_pcm_bytes(sample_rate=16000, channels=1)
        audio_data = AudioData(
            data=pcm_bytes, format=AudioFormat.PCM, sample_rate=16000, channels=1
        )

        result = AzureSTTProvider._convert_to_wav(pcm_bytes, AudioFormat.PCM, audio_data)

        # Result should be valid WAV
        assert result[:4] == b"RIFF"
        assert result[8:12] == b"WAVE"
        # WAV should be larger than raw PCM (has headers)
        assert len(result) > len(pcm_bytes)

    def test_pcm_stereo_to_wav(self):
        """Stereo PCM should preserve channel count in WAV output."""
        pcm_bytes = _make_pcm_bytes(sample_rate=44100, channels=2)
        audio_data = AudioData(
            data=pcm_bytes, format=AudioFormat.PCM, sample_rate=44100, channels=2
        )

        result = AzureSTTProvider._convert_to_wav(pcm_bytes, AudioFormat.PCM, audio_data)

        # Parse WAV to verify channels
        segment = AudioSegment.from_wav(io.BytesIO(result))
        assert segment.channels == 2
        assert segment.frame_rate == 44100

    def test_flac_to_wav(self):
        """FLAC audio should be converted to valid WAV."""
        # Generate FLAC from PCM
        pcm = _make_pcm_bytes()
        segment = AudioSegment(data=pcm, sample_width=2, frame_rate=16000, channels=1)
        buf = io.BytesIO()
        segment.export(buf, format="flac")
        flac_bytes = buf.getvalue()

        audio_data = AudioData(data=flac_bytes, format=AudioFormat.FLAC, sample_rate=16000)

        result = AzureSTTProvider._convert_to_wav(flac_bytes, AudioFormat.FLAC, audio_data)

        assert result[:4] == b"RIFF"
        assert result[8:12] == b"WAVE"

    def test_corrupted_audio_raises_runtime_error(self):
        """Corrupted audio data should raise RuntimeError, not a raw pydub exception."""
        bad_bytes = b"this is not audio data at all"
        audio_data = AudioData(data=bad_bytes, format=AudioFormat.MP3, sample_rate=16000)

        with pytest.raises(RuntimeError, match="Failed to convert mp3 to WAV for Azure STT"):
            AzureSTTProvider._convert_to_wav(bad_bytes, AudioFormat.MP3, audio_data)

    def test_empty_audio_raises_runtime_error(self):
        """Empty audio bytes should raise RuntimeError."""
        audio_data = AudioData(data=b"", format=AudioFormat.MP3, sample_rate=16000)

        with pytest.raises(RuntimeError, match="Failed to convert mp3 to WAV for Azure STT"):
            AzureSTTProvider._convert_to_wav(b"", AudioFormat.MP3, audio_data)

    def test_error_preserves_original_cause(self):
        """RuntimeError should chain the original exception via __cause__."""
        bad_bytes = b"not audio"
        audio_data = AudioData(data=bad_bytes, format=AudioFormat.OGG, sample_rate=16000)

        with pytest.raises(RuntimeError) as exc_info:
            AzureSTTProvider._convert_to_wav(bad_bytes, AudioFormat.OGG, audio_data)

        assert exc_info.value.__cause__ is not None

    def test_wav_output_is_playable(self):
        """Converted WAV output should be loadable by pydub (valid format)."""
        mp3_bytes = _make_mp3_bytes(sample_rate=16000)
        audio_data = AudioData(data=mp3_bytes, format=AudioFormat.MP3, sample_rate=16000)

        result = AzureSTTProvider._convert_to_wav(mp3_bytes, AudioFormat.MP3, audio_data)

        # Should be loadable as WAV
        segment = AudioSegment.from_wav(io.BytesIO(result))
        assert segment.frame_rate == 16000
        assert segment.channels == 1

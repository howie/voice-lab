"""Audio-related domain entities."""

from dataclasses import dataclass
from enum import Enum


class OutputMode(Enum):
    """Output mode for TTS synthesis."""

    BATCH = "batch"  # Complete synthesis then return
    STREAMING = "streaming"  # Stream audio as it's synthesized


class AudioFormat(Enum):
    """Supported audio formats."""

    MP3 = "mp3"
    WAV = "wav"
    OPUS = "opus"
    WEBM = "webm"
    OGG = "ogg"
    PCM = "pcm"
    FLAC = "flac"
    M4A = "m4a"  # AAC audio in MP4 container

    @property
    def mime_type(self) -> str:
        """Get MIME type for the format."""
        mime_types = {
            AudioFormat.MP3: "audio/mpeg",
            AudioFormat.WAV: "audio/wav",
            AudioFormat.OPUS: "audio/opus",
            AudioFormat.WEBM: "audio/webm",
            AudioFormat.OGG: "audio/ogg",
            AudioFormat.PCM: "audio/pcm",
            AudioFormat.FLAC: "audio/flac",
            AudioFormat.M4A: "audio/mp4",
        }
        return mime_types[self]

    @property
    def file_extension(self) -> str:
        """Get file extension for the format."""
        return f".{self.value}"


@dataclass(frozen=True)
class AudioData:
    """Immutable audio data container."""

    data: bytes
    format: AudioFormat
    sample_rate: int = 24000
    channels: int = 1

    @property
    def size_bytes(self) -> int:
        """Get audio data size in bytes."""
        return len(self.data)

    def __len__(self) -> int:
        return self.size_bytes

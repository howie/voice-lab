"""AudioFile domain entity for STT persistence.

Feature: 003-stt-testing-module
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class AudioSource(StrEnum):
    """Source of the audio file."""

    UPLOAD = "upload"
    RECORDING = "recording"


class AudioFileFormat(StrEnum):
    """Supported audio file formats for STT."""

    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    FLAC = "flac"
    WEBM = "webm"
    OGG = "ogg"


@dataclass
class AudioFile:
    """Persisted audio file entity for STT transcription.

    Represents an uploaded or recorded audio file stored in the system.
    """

    user_id: UUID
    filename: str
    format: AudioFileFormat
    duration_ms: int
    sample_rate: int
    file_size_bytes: int
    storage_path: str
    source: AudioSource
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate audio file parameters."""
        if self.duration_ms <= 0:
            raise ValueError("duration_ms must be positive")
        if self.duration_ms > 600_000:  # 10 minutes max
            raise ValueError("duration_ms exceeds maximum of 10 minutes (600000ms)")
        if self.sample_rate < 8000:
            raise ValueError("sample_rate must be at least 8000 Hz")
        if self.file_size_bytes <= 0:
            raise ValueError("file_size_bytes must be positive")

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "filename": self.filename,
            "format": self.format.value,
            "duration_ms": self.duration_ms,
            "sample_rate": self.sample_rate,
            "file_size_bytes": self.file_size_bytes,
            "storage_path": self.storage_path,
            "source": self.source.value,
            "created_at": self.created_at.isoformat(),
        }

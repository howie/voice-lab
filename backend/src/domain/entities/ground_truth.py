"""GroundTruth domain entity for STT evaluation.

Feature: 003-stt-testing-module
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class GroundTruth:
    """Ground truth text entity for WER/CER calculation.

    Represents the correct transcription text for an audio file,
    used as reference for accuracy evaluation.
    """

    audio_file_id: UUID
    text: str
    language: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate ground truth parameters."""
        if not self.text or not self.text.strip():
            raise ValueError("Ground truth text cannot be empty")
        if len(self.text) > 10000:
            raise ValueError("Ground truth text exceeds maximum length of 10000 characters")

    @property
    def word_count(self) -> int:
        """Get word count of the text."""
        return len(self.text.split())

    @property
    def char_count(self) -> int:
        """Get character count (excluding spaces)."""
        return len(self.text.replace(" ", ""))

    @property
    def is_cjk(self) -> bool:
        """Check if language is CJK (use CER instead of WER)."""
        cjk_languages = {"zh-TW", "zh-CN", "ja-JP", "ko-KR"}
        return self.language in cjk_languages

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "audio_file_id": str(self.audio_file_id),
            "text": self.text,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
        }

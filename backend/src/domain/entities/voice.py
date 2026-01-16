"""Voice profile domain entity."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Gender(Enum):
    """Voice gender."""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class VoiceProfile:
    """Voice profile entity."""

    id: str
    provider: str
    voice_id: str  # Provider-specific voice ID
    display_name: str
    language: str
    gender: Gender | None = None
    description: str = ""
    sample_audio_url: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_chinese(self) -> bool:
        """Check if voice supports Chinese."""
        return self.language.startswith("zh")

    @property
    def locale(self) -> str:
        """Get locale from language code."""
        return self.language.split("-")[0] if "-" in self.language else self.language

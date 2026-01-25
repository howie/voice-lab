"""Voice profile domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Gender(Enum):
    """Voice gender."""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class AgeGroup(Enum):
    """Voice age group classification."""

    CHILD = "child"  # 兒童聲音
    YOUNG = "young"  # 青年聲音
    ADULT = "adult"  # 成人聲音
    SENIOR = "senior"  # 長者聲音


@dataclass(frozen=True)
class VoiceProfile:
    """Voice profile entity with extended metadata."""

    id: str  # provider:voice_id
    provider: str  # azure, gcp, elevenlabs
    voice_id: str  # Provider-specific voice ID
    display_name: str
    language: str  # zh-TW, en-US
    gender: Gender | None = None
    age_group: AgeGroup | None = None
    styles: tuple[str, ...] = ()  # news, conversation, cheerful
    use_cases: tuple[str, ...] = ()  # narration, assistant, character
    description: str = ""
    sample_audio_url: str | None = None
    is_deprecated: bool = False
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    synced_at: datetime | None = None

    @property
    def is_chinese(self) -> bool:
        """Check if voice supports Chinese."""
        return self.language.startswith("zh")

    @property
    def locale(self) -> str:
        """Get locale from language code."""
        return self.language.split("-")[0] if "-" in self.language else self.language

"""Story entities for StoryPal interactive story engine.

Feature: StoryPal - AI interactive story companion for children.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class StoryCategory(StrEnum):
    """Category of story template."""

    FAIRY_TALE = "fairy_tale"
    ADVENTURE = "adventure"
    SCIENCE = "science"
    FABLE = "fable"
    DAILY_LIFE = "daily_life"


class StorySessionStatus(StrEnum):
    """Status of a story session."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class StoryTurnType(StrEnum):
    """Type of story turn."""

    NARRATION = "narration"
    DIALOGUE = "dialogue"
    CHOICE_PROMPT = "choice_prompt"
    CHILD_RESPONSE = "child_response"
    QUESTION = "question"
    ANSWER = "answer"


@dataclass
class StoryCharacter:
    """A character in the story with voice configuration."""

    name: str
    description: str
    voice_provider: str
    voice_id: str
    voice_settings: dict[str, Any] = field(default_factory=dict)
    emotion: str = "neutral"


@dataclass
class SceneInfo:
    """Scene information with BGM configuration."""

    name: str
    description: str
    bgm_prompt: str = ""
    mood: str = "neutral"


@dataclass
class StoryTemplate:
    """A pre-built story template with characters and scenes."""

    name: str
    description: str
    category: StoryCategory
    target_age_min: int
    target_age_max: int
    language: str
    characters: list[StoryCharacter]
    scenes: list[SceneInfo]
    opening_prompt: str
    system_prompt: str
    id: UUID = field(default_factory=uuid4)
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StoryBranch:
    """A decision point in the story."""

    prompt_text: str
    options: list[str] = field(default_factory=list)
    context: str = ""


@dataclass
class StoryTurn:
    """A single turn in the story session."""

    session_id: UUID
    turn_number: int
    turn_type: StoryTurnType
    content: str
    id: UUID = field(default_factory=uuid4)
    character_name: str | None = None
    audio_path: str | None = None
    choice_options: list[str] | None = None
    child_choice: str | None = None
    bgm_scene: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StorySession:
    """An active story session tracking state and history."""

    title: str
    language: str
    id: UUID = field(default_factory=uuid4)
    user_id: str | None = None
    template_id: UUID | None = None
    status: StorySessionStatus = StorySessionStatus.ACTIVE
    story_state: dict[str, Any] = field(default_factory=dict)
    characters_config: list[StoryCharacter] = field(default_factory=list)
    interaction_session_id: UUID | None = None
    current_scene: str | None = None
    turns: list[StoryTurn] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_turn(self, turn: StoryTurn) -> None:
        """Add a turn to the session."""
        self.turns.append(turn)
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark the session as completed."""
        self.status = StorySessionStatus.COMPLETED
        self.ended_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause the session."""
        self.status = StorySessionStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """Resume a paused session."""
        self.status = StorySessionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

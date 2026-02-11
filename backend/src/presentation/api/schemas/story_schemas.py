"""Pydantic schemas for StoryPal API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Character & Scene Schemas
# =============================================================================


class StoryCharacterSchema(BaseModel):
    """Character configuration."""

    name: str
    description: str
    voice_provider: str
    voice_id: str
    voice_settings: dict[str, Any] = Field(default_factory=dict)
    emotion: str = "neutral"


class SceneInfoSchema(BaseModel):
    """Scene information."""

    name: str
    description: str
    bgm_prompt: str = ""
    mood: str = "neutral"


# =============================================================================
# Template Schemas
# =============================================================================


class StoryTemplateResponse(BaseModel):
    """Story template response."""

    id: str
    name: str
    description: str
    category: str
    target_age_min: int
    target_age_max: int
    language: str
    characters: list[StoryCharacterSchema]
    scenes: list[SceneInfoSchema]
    opening_prompt: str
    system_prompt: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class StoryTemplateListResponse(BaseModel):
    """List of story templates."""

    templates: list[StoryTemplateResponse]
    total: int


# =============================================================================
# Session Schemas
# =============================================================================


class CreateStorySessionRequest(BaseModel):
    """Request to create a new story session."""

    template_id: str | None = None
    title: str | None = None
    language: str = "zh-TW"
    characters_config: list[StoryCharacterSchema] | None = None
    custom_prompt: str | None = None


class StoryTurnResponse(BaseModel):
    """A single story turn."""

    id: str
    session_id: str
    turn_number: int
    turn_type: str
    character_name: str | None = None
    content: str
    audio_path: str | None = None
    choice_options: list[str] | None = None
    child_choice: str | None = None
    bgm_scene: str | None = None
    created_at: datetime


class StorySessionResponse(BaseModel):
    """Story session response."""

    id: str
    user_id: str
    template_id: str | None = None
    title: str
    language: str
    status: str
    story_state: dict[str, Any] = Field(default_factory=dict)
    characters_config: list[StoryCharacterSchema] = Field(default_factory=list)
    interaction_session_id: str | None = None
    current_scene: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    turns: list[StoryTurnResponse] | None = None


class StorySessionListResponse(BaseModel):
    """List of story sessions."""

    sessions: list[StorySessionResponse]
    total: int
    page: int
    page_size: int

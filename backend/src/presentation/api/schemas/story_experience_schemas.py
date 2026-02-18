"""API schemas for Story Experience MVP.

Feature: 016-story-experience-mvp
Pydantic models for request/response validation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# =============================================================================
# Content Generation
# =============================================================================


class GenerateContentRequest(BaseModel):
    """Request to generate story or song content."""

    age: int = Field(..., ge=2, le=12, description="Child's age (2-12)")
    educational_content: str = Field(
        ..., min_length=1, max_length=200, description="Educational topic"
    )
    values: list[str] = Field(..., min_length=1, description="Values to embed (e.g., 勇氣, 善良)")
    emotions: list[str] = Field(..., min_length=1, description="Emotional awareness targets")
    favorite_character: str = Field(
        ..., min_length=1, max_length=100, description="Child's favorite character"
    )
    content_type: str = Field(
        ..., pattern="^(story|song)$", description="Content type: story or song"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "age": 5,
                "educational_content": "認識顏色",
                "values": ["勇氣", "善良"],
                "emotions": ["快樂", "驚訝"],
                "favorite_character": "小恐龍",
                "content_type": "story",
            }
        }


class ParametersSummary(BaseModel):
    """Summary of parameters used for generation."""

    age: int
    educational_content: str
    values: list[str]
    emotions: list[str]
    favorite_character: str


class GenerateContentResponse(BaseModel):
    """Response with generated content."""

    content_id: str = Field(..., description="Unique content ID")
    content_type: str = Field(..., description="story or song")
    text_content: str = Field(..., description="Generated text content")
    parameters_summary: ParametersSummary


# =============================================================================
# Story Branching
# =============================================================================


class BranchRequest(BaseModel):
    """Request to generate branch options or continue from a branch."""

    content_id: str = Field(..., description="Original content ID")
    story_context: str = Field(..., description="Full story text so far")
    selected_branch: str | None = Field(
        None, description="Selected branch description (None = generate options)"
    )


class BranchOption(BaseModel):
    """A single story branch option."""

    id: str
    description: str


class BranchResponse(BaseModel):
    """Response with branch options or continuation text."""

    branches: list[BranchOption] | None = Field(
        None, description="Branch options (when no branch selected)"
    )
    content_id: str | None = Field(None, description="New content ID (when branch selected)")
    text_content: str | None = Field(None, description="Continuation text (when branch selected)")


# =============================================================================
# Q&A
# =============================================================================


class QARequest(BaseModel):
    """Request to generate questions or answer a question."""

    content_id: str = Field(..., description="Content ID")
    story_context: str = Field(..., description="Full story text")
    question: str | None = Field(None, description="Question to answer (None = generate questions)")


class QAQuestion(BaseModel):
    """A generated Q&A question."""

    id: str
    text: str


class QAResponse(BaseModel):
    """Response with questions or an answer."""

    questions: list[QAQuestion] | None = Field(
        None, description="Generated questions (when no question provided)"
    )
    question: str | None = Field(None, description="The answered question")
    answer: str | None = Field(None, description="Answer text")


# =============================================================================
# TTS
# =============================================================================


class TTSGenerateRequest(BaseModel):
    """Request to generate TTS audio."""

    text_content: str = Field(..., min_length=1, description="Text to synthesize")
    voice_id: str = Field(..., description="TTS voice ID")


class TTSGenerateResponse(BaseModel):
    """Response with TTS audio data."""

    audio_content: str = Field(..., description="Base64-encoded audio")
    content_type: str = Field(default="audio/mp3", description="Audio MIME type")
    duration_ms: int = Field(..., description="Audio duration in milliseconds")


# =============================================================================
# Voices
# =============================================================================


class VoiceOptionResponse(BaseModel):
    """A TTS voice option."""

    id: str
    name: str
    language: str
    gender: str | None = None

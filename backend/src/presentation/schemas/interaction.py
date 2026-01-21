"""Interaction API Schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.presentation.schemas.common import BaseSchema


class ConversationMessage(BaseSchema):
    """A message in the conversation history."""

    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")


class InteractionRequest(BaseSchema):
    """Request for voice interaction."""

    stt_provider: str = Field(..., description="STT provider name")
    llm_provider: str = Field(..., description="LLM provider name")
    tts_provider: str = Field(..., description="TTS provider name")
    voice_id: str = Field(..., description="TTS voice ID")
    system_prompt: str = Field(default="", description="System prompt for LLM")
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list, description="Previous conversation messages"
    )
    language: str = Field(default="zh-TW", description="Language code")
    max_response_tokens: int = Field(
        default=150, ge=50, le=500, description="Max LLM response tokens"
    )


class InteractionResponse(BaseSchema):
    """Response from voice interaction."""

    user_transcript: str = Field(..., description="User's speech transcribed to text")
    ai_response_text: str = Field(..., description="AI's text response")
    ai_response_audio_base64: str = Field(..., description="Base64 encoded AI audio response")
    audio_format: str = Field(..., description="Audio format of response")
    stt_latency_ms: int = Field(..., description="STT processing latency")
    llm_latency_ms: int = Field(..., description="LLM processing latency")
    tts_latency_ms: int = Field(..., description="TTS processing latency")
    total_latency_ms: int = Field(..., description="Total end-to-end latency")
    updated_history: list[ConversationMessage] = Field(
        ..., description="Updated conversation history"
    )


# =============================================================================
# Session Management Schemas (Phase 4 - Interaction Module)
# =============================================================================


class SessionCreateRequest(BaseSchema):
    """Request to create an interaction session."""

    mode: str = Field(..., description="Interaction mode: 'realtime' or 'cascade'")
    provider_config: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )
    system_prompt: str = Field(default="", description="System prompt for the AI")


class SessionResponse(BaseSchema):
    """Response containing session details."""

    id: UUID = Field(..., description="Session UUID")
    user_id: UUID = Field(..., description="User UUID")
    mode: str = Field(..., description="Interaction mode")
    provider_config: dict[str, Any] = Field(..., description="Provider configuration")
    system_prompt: str = Field(..., description="System prompt")
    status: str = Field(..., description="Session status")
    started_at: datetime = Field(..., description="Session start time")
    ended_at: datetime | None = Field(None, description="Session end time")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Record update time")


class SessionListResponse(BaseSchema):
    """Paginated list of sessions."""

    sessions: list[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")


class TurnResponse(BaseSchema):
    """Response containing conversation turn details."""

    id: UUID = Field(..., description="Turn UUID")
    session_id: UUID = Field(..., description="Session UUID")
    turn_number: int = Field(..., description="Turn number in session")
    user_audio_path: str | None = Field(None, description="Path to user audio file")
    user_transcript: str | None = Field(None, description="User speech transcript")
    ai_response_text: str | None = Field(None, description="AI response text")
    ai_audio_path: str | None = Field(None, description="Path to AI audio file")
    interrupted: bool = Field(False, description="Whether turn was interrupted")
    started_at: datetime = Field(..., description="Turn start time")
    ended_at: datetime | None = Field(None, description="Turn end time")


class LatencyStatsResponse(BaseSchema):
    """Response containing latency statistics for a session."""

    total_turns: int = Field(..., description="Total number of turns")
    avg_total_ms: float | None = Field(None, description="Average total latency")
    min_total_ms: float | None = Field(None, description="Minimum total latency")
    max_total_ms: float | None = Field(None, description="Maximum total latency")
    p95_total_ms: float | None = Field(None, description="95th percentile latency")
    avg_stt_ms: float | None = Field(None, description="Average STT latency")
    avg_llm_ttft_ms: float | None = Field(None, description="Average LLM TTFT")
    avg_tts_ttfb_ms: float | None = Field(None, description="Average TTS TTFB")


class SystemPromptTemplateResponse(BaseSchema):
    """Response containing a system prompt template."""

    id: UUID = Field(..., description="Template UUID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    prompt_content: str = Field(..., description="Prompt content")
    category: str = Field(..., description="Template category")
    is_default: bool = Field(False, description="Whether this is the default template")


class SystemPromptTemplateListResponse(BaseSchema):
    """List of system prompt templates."""

    templates: list[SystemPromptTemplateResponse] = Field(..., description="List of templates")


# =============================================================================
# Scenario Template Schemas (US4 - Role/Scenario Configuration)
# =============================================================================


class ScenarioTemplateResponse(BaseSchema):
    """Response containing a scenario template."""

    id: UUID = Field(..., description="Template UUID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    user_role: str = Field(..., description="User role name")
    ai_role: str = Field(..., description="AI role name")
    scenario_context: str = Field(..., description="Scenario context description")
    category: str = Field(..., description="Template category")
    is_default: bool = Field(False, description="Whether this is a default template")

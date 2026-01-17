"""Interaction API Schemas."""

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
    max_response_tokens: int = Field(default=150, ge=50, le=500, description="Max LLM response tokens")


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

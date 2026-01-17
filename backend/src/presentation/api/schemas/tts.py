"""TTS API Schemas.

T033: Update API schemas with proper validation
"""


from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    """Request schema for batch TTS synthesis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to synthesize (1-5000 characters)",
    )
    provider: str = Field(
        ...,
        pattern="^(azure|gcp|elevenlabs|voai)$",
        description="TTS provider (azure, gcp, elevenlabs, voai)",
    )
    voice_id: str = Field(
        ...,
        min_length=1,
        description="Voice ID for the selected provider",
    )
    language: str = Field(
        default="zh-TW",
        description="Language code (e.g., zh-TW, en-US, ja-JP)",
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed (0.5-2.0, default 1.0)",
    )
    pitch: float = Field(
        default=0.0,
        ge=-20.0,
        le=20.0,
        description="Voice pitch adjustment in semitones (-20 to +20)",
    )
    volume: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Volume level (0.0-2.0, default 1.0)",
    )
    output_format: str = Field(
        default="mp3",
        description="Output audio format (mp3, wav, ogg, opus, pcm)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "你好，這是一段測試語音。",
                "provider": "azure",
                "voice_id": "zh-TW-HsiaoChenNeural",
                "language": "zh-TW",
                "speed": 1.0,
                "pitch": 0.0,
                "volume": 1.0,
                "output_format": "mp3",
            }
        }


class StreamRequest(BaseModel):
    """Request schema for streaming TTS synthesis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to synthesize (1-5000 characters)",
    )
    provider: str = Field(
        ...,
        pattern="^(azure|gcp|elevenlabs|voai)$",
        description="TTS provider (azure, gcp, elevenlabs, voai)",
    )
    voice_id: str = Field(
        ...,
        min_length=1,
        description="Voice ID for the selected provider",
    )
    language: str = Field(
        default="zh-TW",
        description="Language code (e.g., zh-TW, en-US, ja-JP)",
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed (0.5-2.0, default 1.0)",
    )
    pitch: float = Field(
        default=0.0,
        ge=-20.0,
        le=20.0,
        description="Voice pitch adjustment in semitones (-20 to +20)",
    )
    volume: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Volume level (0.0-2.0, default 1.0)",
    )
    output_format: str = Field(
        default="mp3",
        description="Output audio format (mp3, wav, ogg, opus, pcm)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "這是串流語音合成測試。",
                "provider": "voai",
                "voice_id": "voai-tw-female-1",
                "language": "zh-TW",
                "speed": 1.0,
            }
        }


class SynthesizeResponse(BaseModel):
    """Response schema for batch TTS synthesis."""

    audio_content: str = Field(
        ...,
        description="Base64 encoded audio data",
    )
    content_type: str = Field(
        ...,
        description="MIME type of the audio (e.g., audio/mpeg)",
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Duration of the audio in milliseconds",
    )
    latency_ms: int | None = Field(
        default=None,
        ge=0,
        description="Time to first byte in milliseconds",
    )
    storage_path: str | None = Field(
        default=None,
        description="Path where audio is stored (if saved)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "audio_content": "//uQxAAAAAANIAAAAAExBTUUzLjEwMFVVVVVVVVVVVV...",
                "content_type": "audio/mpeg",
                "duration_ms": 2500,
                "latency_ms": 150,
                "storage_path": "storage/azure/abc123.mp3",
            }
        }


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str = Field(
        ...,
        description="Error code (e.g., VALIDATION_ERROR, SERVICE_UNAVAILABLE)",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    details: dict | None = Field(
        default=None,
        description="Additional error details",
    )
    request_id: str | None = Field(
        default=None,
        description="Request ID for tracing",
    )


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: ErrorDetail

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Text exceeds 5000 characters limit",
                    "details": {"length": 5500, "max_length": 5000},
                    "request_id": "abc-123-def-456",
                }
            }
        }

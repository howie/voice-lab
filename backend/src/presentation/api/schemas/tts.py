"""TTS API Schemas.

T033: Update API schemas with proper validation
"""

from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    """Request schema for batch TTS synthesis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Text to synthesize (1-50000 characters). Text exceeding provider limits will be automatically segmented.",
    )
    provider: str = Field(
        ...,
        pattern="^(azure|gemini|elevenlabs|voai)$",
        description="TTS provider (azure, gemini, elevenlabs, voai)",
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
    segment_gap_ms: int = Field(
        default=100,
        ge=0,
        le=2000,
        description="Gap between segments in ms (only used when text is auto-segmented)",
    )
    segment_crossfade_ms: int = Field(
        default=30,
        ge=0,
        le=500,
        description="Crossfade between segments in ms (only used when text is auto-segmented)",
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
        max_length=50000,
        description="Text to synthesize (1-50000 characters). Text exceeding provider limits will be automatically segmented.",
    )
    provider: str = Field(
        ...,
        pattern="^(azure|gemini|elevenlabs|voai)$",
        description="TTS provider (azure, gemini, elevenlabs, voai)",
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


class SegmentTiming(BaseModel):
    """Timing info for a single segment."""

    index: int
    start_ms: int
    end_ms: int


class SynthesisMetadata(BaseModel):
    """Metadata returned when text was auto-segmented."""

    segmented: bool = Field(description="Whether text was segmented")
    segment_count: int = Field(description="Number of segments synthesized")
    total_text_chars: int = Field(default=0)
    total_text_bytes: int = Field(default=0)
    segment_timings: list[SegmentTiming] = Field(default_factory=list)


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
    metadata: SynthesisMetadata | None = Field(
        default=None,
        description="Segmentation metadata (present when text was auto-segmented)",
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


class SegmentPreviewRequest(BaseModel):
    """Request schema for segmentation preview."""

    text: str = Field(..., min_length=1, max_length=50000)
    provider: str = Field(
        ...,
        pattern="^(azure|gemini|elevenlabs|voai)$",
    )


class SegmentPreviewItem(BaseModel):
    """Preview info for a single segment."""

    index: int
    text_preview: str = Field(description="First 50 characters of the segment")
    char_length: int
    byte_length: int
    boundary_type: str


class ProviderLimitInfo(BaseModel):
    """Provider limit info for preview response."""

    max_value: int
    limit_type: str


class SegmentPreviewResponse(BaseModel):
    """Response schema for segmentation preview."""

    needs_segmentation: bool
    segment_count: int
    segments: list[SegmentPreviewItem] = Field(default_factory=list)
    provider_limit: ProviderLimitInfo
    estimated_duration_seconds: float = Field(
        default=0.0,
        description="Rough estimate of total synthesis time",
    )


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

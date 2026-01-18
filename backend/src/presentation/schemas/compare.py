"""Comparison API Schemas."""

from pydantic import Field

from src.presentation.schemas.common import BaseSchema


class TTSCompareRequest(BaseSchema):
    """Request for TTS provider comparison."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_ids: dict[str, str] = Field(..., description="Mapping of provider name to voice ID")
    language: str = Field(default="zh-TW", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0, description="Pitch adjustment")


class TTSProviderResult(BaseSchema):
    """Result from a single TTS provider."""

    provider: str
    success: bool
    audio_base64: str | None = None
    audio_format: str | None = None
    latency_ms: int | None = None
    error: str | None = None


class TTSCompareResponse(BaseSchema):
    """Response from TTS comparison."""

    results: list[TTSProviderResult]
    fastest_provider: str | None = None
    summary: dict[str, int] = Field(default_factory=dict, description="Summary statistics")


class STTCompareRequest(BaseSchema):
    """Request for STT provider comparison."""

    providers: list[str] = Field(..., min_length=1, description="List of providers to compare")
    language: str = Field(default="zh-TW", description="Language code")
    child_mode: bool = Field(default=False, description="Enable child speech mode")
    ground_truth: str | None = Field(default=None, description="Ground truth for accuracy metrics")


class STTProviderResult(BaseSchema):
    """Result from a single STT provider."""

    provider: str
    success: bool
    transcript: str | None = None
    latency_ms: int | None = None
    confidence: float | None = None
    wer: float | None = None
    cer: float | None = None
    error: str | None = None


class STTCompareResponse(BaseSchema):
    """Response from STT comparison."""

    results: list[STTProviderResult]
    most_accurate_provider: str | None = None
    fastest_provider: str | None = None
    summary: dict[str, int] = Field(default_factory=dict, description="Summary statistics")

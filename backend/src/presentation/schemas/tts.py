"""TTS API Schemas."""

from pydantic import Field

from src.presentation.schemas.common import BaseSchema


class TTSSynthesizeRequest(BaseSchema):
    """Request for TTS synthesis."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    provider: str = Field(..., description="TTS provider name (gcp, azure, elevenlabs, voai)")
    voice_id: str = Field(..., description="Voice ID for the provider")
    language: str = Field(default="zh-TW", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0, description="Pitch adjustment")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Volume level")
    output_format: str = Field(default="mp3", description="Output audio format")
    save_to_history: bool = Field(default=True, description="Save to test history")


class TTSSynthesizeResponse(BaseSchema):
    """Response from TTS synthesis."""

    audio_base64: str = Field(..., description="Base64 encoded audio data")
    audio_format: str = Field(..., description="Audio format (mp3, wav, etc.)")
    provider: str = Field(..., description="Provider used")
    voice_id: str = Field(..., description="Voice ID used")
    latency_ms: int = Field(..., description="Processing latency in milliseconds")
    text_length: int = Field(..., description="Length of input text")
    audio_url: str | None = Field(default=None, description="URL to stored audio file")
    record_id: str | None = Field(default=None, description="Test record ID if saved")


class VoiceResponse(BaseSchema):
    """Voice profile response."""

    voice_id: str
    name: str
    provider: str
    language: str
    gender: str
    sample_audio_url: str | None = None
    description: str | None = None


class VoiceListResponse(BaseSchema):
    """Response with list of voices."""

    voices: list[VoiceResponse]
    total: int
    provider: str | None = None
    language: str | None = None

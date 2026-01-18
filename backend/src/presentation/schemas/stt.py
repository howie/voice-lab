"""STT API Schemas."""

from pydantic import Field

from src.presentation.schemas.common import BaseSchema


class WordTimingResponse(BaseSchema):
    """Word timing information."""

    word: str
    start_time: float
    end_time: float
    confidence: float | None = None


class STTTranscribeRequest(BaseSchema):
    """Request for STT transcription."""

    provider: str = Field(..., description="STT provider name (gcp, azure, whisper)")
    language: str = Field(default="zh-TW", description="Language code")
    child_mode: bool = Field(default=False, description="Enable child speech mode")
    ground_truth: str | None = Field(default=None, description="Ground truth for WER calculation")
    save_to_history: bool = Field(default=True, description="Save to test history")


class STTTranscribeResponse(BaseSchema):
    """Response from STT transcription."""

    transcript: str = Field(..., description="Transcribed text")
    provider: str = Field(..., description="Provider used")
    language: str = Field(..., description="Language detected/used")
    latency_ms: int = Field(..., description="Processing latency in milliseconds")
    confidence: float | None = Field(default=None, description="Transcription confidence")
    word_timings: list[WordTimingResponse] | None = Field(
        default=None, description="Word-level timing information"
    )
    audio_duration_ms: int | None = Field(default=None, description="Audio duration in ms")
    wer: float | None = Field(default=None, description="Word Error Rate if ground truth provided")
    cer: float | None = Field(
        default=None, description="Character Error Rate if ground truth provided"
    )
    record_id: str | None = Field(default=None, description="Test record ID if saved")

"""STT API Schemas.

Feature: 003-stt-testing-module
Schemas for STT endpoints matching frontend expectations.
"""

from typing import Literal

from pydantic import Field

from src.presentation.schemas.common import BaseSchema

# --- Provider Schemas ---


class STTProviderResponse(BaseSchema):
    """STT provider information matching frontend STTProvider type."""

    name: str = Field(..., description="Provider identifier (azure, gcp, whisper)")
    display_name: str = Field(..., description="Human-readable name")
    supports_streaming: bool = Field(..., description="Whether provider supports streaming")
    supports_child_mode: bool = Field(..., description="Whether provider supports child mode")
    max_duration_sec: int = Field(..., description="Maximum audio duration in seconds")
    max_file_size_mb: int = Field(..., description="Maximum file size in MB")
    supported_formats: list[str] = Field(..., description="Supported audio formats")
    supported_languages: list[str] = Field(..., description="Supported language codes")
    has_credentials: bool = Field(
        default=False, description="Whether user has credentials configured"
    )
    is_valid: bool = Field(default=False, description="Whether configured credentials are valid")


class STTProvidersListResponse(BaseSchema):
    """Response for GET /stt/providers."""

    providers: list[STTProviderResponse]


# --- Word Timing Schemas ---


class WordTimingResponse(BaseSchema):
    """Word timing information matching frontend WordTiming type."""

    word: str = Field(..., description="The transcribed word")
    start_ms: int = Field(..., description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    confidence: float | None = Field(default=None, description="Confidence score 0-1")


# --- Transcription Schemas ---


class STTTranscribeRequest(BaseSchema):
    """Request for STT transcription."""

    provider: str = Field(..., description="STT provider name (gcp, azure, whisper)")
    language: str = Field(default="zh-TW", description="Language code")
    child_mode: bool = Field(default=False, description="Enable child speech mode")
    ground_truth: str | None = Field(default=None, description="Ground truth for WER calculation")
    save_to_history: bool = Field(default=True, description="Save to test history")


class WERAnalysisRequest(BaseSchema):
    """Request for WER/CER analysis."""

    result_id: str = Field(..., description="Transcription result ID")
    ground_truth: str = Field(..., description="Ground truth text")


class WERAnalysisResponse(BaseSchema):
    """WER/CER analysis result matching frontend WERAnalysis type."""

    error_rate: float = Field(..., description="Error rate (0-1)")
    error_type: Literal["WER", "CER"] = Field(..., description="Type of error rate")
    insertions: int = Field(..., description="Number of inserted words/chars")
    deletions: int = Field(..., description="Number of deleted words/chars")
    substitutions: int = Field(..., description="Number of substituted words/chars")
    total_reference: int = Field(..., description="Total words/chars in reference")


class STTTranscribeResponse(BaseSchema):
    """Response from STT transcription matching frontend TranscriptionResponse."""

    id: str | None = Field(default=None, description="Transcription result ID")
    transcript: str = Field(..., description="Transcribed text")
    provider: str = Field(..., description="Provider used")
    language: str = Field(..., description="Language detected/used")
    latency_ms: int = Field(..., description="Processing latency in milliseconds")
    confidence: float = Field(default=0.0, description="Transcription confidence 0-1")
    words: list[WordTimingResponse] | None = Field(
        default=None, description="Word-level timing information"
    )
    audio_duration_ms: int | None = Field(default=None, description="Audio duration in ms")
    wer_analysis: WERAnalysisResponse | None = Field(
        default=None, description="WER/CER analysis if ground truth provided"
    )
    created_at: str | None = Field(default=None, description="ISO timestamp")

    # Legacy fields for backwards compatibility
    word_timings: list[WordTimingResponse] | None = Field(
        default=None, description="Deprecated: Use 'words' instead"
    )
    wer: float | None = Field(default=None, description="Deprecated: Use wer_analysis")
    cer: float | None = Field(default=None, description="Deprecated: Use wer_analysis")
    record_id: str | None = Field(default=None, description="Deprecated: Use 'id'")


class TranscriptionSummary(BaseSchema):
    """Summary of a transcription record."""

    id: str
    provider: str
    language: str
    transcript_preview: str
    duration_ms: int | None
    confidence: float
    has_ground_truth: bool
    error_rate: float | None
    created_at: str


class TranscriptionHistoryPage(BaseSchema):
    """Paginated transcription history."""

    items: list[TranscriptionSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class AudioFileResponse(BaseSchema):
    """Audio file details."""

    id: str
    filename: str
    duration_ms: int
    format: str
    download_url: str | None = None


class TranscriptionDetail(STTTranscribeResponse):
    """Detailed transcription record."""

    audio_file: AudioFileResponse
    ground_truth: str | None
    child_mode: bool


class ComparisonResponse(BaseSchema):
    """Comparison results for multiple providers."""

    audio_file_id: str
    results: list[STTTranscribeResponse]
    ground_truth: str | None
    comparison_table: list[dict]

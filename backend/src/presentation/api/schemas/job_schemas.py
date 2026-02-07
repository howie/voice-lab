"""Job API Schemas for async job management.

This module defines Pydantic schemas for job-related API endpoints.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.job import JobStatus, JobType


class DialogueTurn(BaseModel):
    """Schema for a single dialogue turn in multi-role TTS."""

    speaker: str = Field(
        ...,
        max_length=50,
        description="Speaker identifier",
        examples=["A"],
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Dialogue content",
        examples=["你好，很高興認識你！"],
    )
    index: int = Field(
        ...,
        ge=0,
        description="Turn order (0-based)",
    )


class VoiceAssignment(BaseModel):
    """Schema for voice assignment to a speaker."""

    speaker: str = Field(
        ...,
        description="Speaker identifier, must match DialogueTurn.speaker",
        examples=["A"],
    )
    voice_id: str = Field(
        ...,
        description="Provider-specific voice ID",
        examples=["zh-TW-HsiaoYuNeural"],
    )
    voice_name: str | None = Field(
        default=None,
        description="Voice display name",
        examples=["曉雨"],
    )


class CreateJobRequest(BaseModel):
    """Request schema for creating a new job."""

    provider: str = Field(
        ...,
        description="TTS provider name",
        examples=["azure"],
    )
    turns: list[DialogueTurn] = Field(
        ...,
        min_length=1,
        description="List of dialogue turns",
    )
    voice_assignments: list[VoiceAssignment] = Field(
        ...,
        min_length=1,
        description="List of voice assignments",
    )
    language: str = Field(
        default="zh-TW",
        description="Language code",
    )
    output_format: str = Field(
        default="mp3",
        pattern="^(mp3|wav)$",
        description="Output audio format",
    )
    gap_ms: int = Field(
        default=300,
        ge=0,
        le=2000,
        description="Gap between turns in milliseconds",
    )
    crossfade_ms: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Crossfade duration in milliseconds",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "azure",
                "turns": [
                    {"speaker": "A", "text": "你好，很高興認識你！", "index": 0},
                    {"speaker": "B", "text": "我也很高興認識你！", "index": 1},
                ],
                "voice_assignments": [
                    {"speaker": "A", "voice_id": "zh-TW-HsiaoYuNeural", "voice_name": "曉雨"},
                    {"speaker": "B", "voice_id": "zh-TW-YunJheNeural", "voice_name": "雲哲"},
                ],
                "language": "zh-TW",
                "output_format": "mp3",
                "gap_ms": 300,
                "crossfade_ms": 50,
            }
        }


class CreateSingleTTSJobRequest(BaseModel):
    """Request schema for creating a single TTS background job."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to synthesize",
        examples=["你好，歡迎使用語音合成服務！"],
    )
    provider: str = Field(
        ...,
        description="TTS provider name",
        examples=["azure"],
    )
    voice_id: str = Field(
        ...,
        description="Provider-specific voice ID",
        examples=["zh-TW-HsiaoChenNeural"],
    )
    language: str = Field(
        default="zh-TW",
        description="Language code",
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed",
    )
    pitch: float = Field(
        default=0.0,
        ge=-20.0,
        le=20.0,
        description="Speech pitch in semitones",
    )
    volume: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Speech volume",
    )
    output_format: str = Field(
        default="mp3",
        pattern="^(mp3|wav)$",
        description="Output audio format",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "你好，歡迎使用語音合成服務！",
                "provider": "azure",
                "voice_id": "zh-TW-HsiaoChenNeural",
                "language": "zh-TW",
                "speed": 1.0,
                "pitch": 0.0,
                "volume": 1.0,
                "output_format": "mp3",
            }
        }


class JobResponse(BaseModel):
    """Response schema for job summary."""

    id: UUID = Field(
        ...,
        description="Job ID",
    )
    status: JobStatus = Field(
        ...,
        description="Job status",
    )
    job_type: JobType = Field(
        ...,
        description="Job type",
    )
    provider: str = Field(
        ...,
        description="TTS provider",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Processing start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )

    class Config:
        from_attributes = True


class ResultMetadata(BaseModel):
    """Schema for job result metadata."""

    duration_ms: int | None = Field(
        default=None,
        description="Audio duration in milliseconds",
    )
    latency_ms: int | None = Field(
        default=None,
        description="Processing latency in milliseconds",
    )
    synthesis_mode: str | None = Field(
        default=None,
        description="Synthesis mode (native or segmented)",
    )


class JobDetailResponse(JobResponse):
    """Response schema for job details."""

    input_params: dict[str, Any] = Field(
        ...,
        description="Original input parameters",
    )
    result_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Result metadata (only when completed)",
    )
    audio_file_id: UUID | None = Field(
        default=None,
        description="Audio file ID (only when completed)",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message (only when failed)",
    )
    retry_count: int = Field(
        default=0,
        description="Retry count",
    )


class JobListResponse(BaseModel):
    """Response schema for job list."""

    items: list[JobResponse] = Field(
        ...,
        description="List of jobs",
    )
    total: int = Field(
        ...,
        description="Total count",
    )
    limit: int = Field(
        ...,
        description="Page size",
    )
    offset: int = Field(
        ...,
        description="Current offset",
    )

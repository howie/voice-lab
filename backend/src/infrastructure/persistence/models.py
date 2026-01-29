import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    ARRAY,
    DECIMAL,
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.entities.interaction_enums import InteractionMode, SessionStatus
from src.infrastructure.persistence.database import Base


class User(Base):
    """User model for Google SSO authentication (FR-020)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    synthesis_logs: Mapped[list["SynthesisLog"]] = relationship(
        "SynthesisLog", back_populates="user"
    )
    provider_credentials: Mapped[list["UserProviderCredentialModel"]] = relationship(
        "UserProviderCredentialModel", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        "AuditLogModel", back_populates="user", cascade="all, delete-orphan"
    )


class SynthesisLog(Base):
    """Synthesis log model for request logging (FR-010)."""

    __tablename__ = "synthesis_logs"
    __table_args__ = (
        Index("idx_synthesis_logs_provider", "provider"),
        Index("idx_synthesis_logs_status", "status"),
        Index("idx_synthesis_logs_created_at", "created_at"),
        Index("idx_synthesis_logs_text_hash", "text_hash"),
        Index("idx_synthesis_logs_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    text_preview: Mapped[str | None] = mapped_column(String(100), nullable=True)
    characters_count: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    output_format: Mapped[str] = mapped_column(String(10), default="mp3")
    output_mode: Mapped[str] = mapped_column(String(16), default="batch")
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'pending', 'processing', 'completed', 'failed'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_estimate: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="synthesis_logs")


class VoiceCache(Base):
    """Voice cache model for caching available voices.

    Enhanced for feature 008-voai-multi-role-voice-generation with age_group,
    styles, use_cases, and deprecation tracking.
    """

    __tablename__ = "voice_cache"
    __table_args__ = (
        Index("idx_voice_cache_provider", "provider"),
        Index("idx_voice_cache_language", "language"),
        Index("idx_voice_cache_age_group", "age_group"),
        Index("idx_voice_cache_deprecated", "is_deprecated"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # provider:voice_id
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    styles: Mapped[list[str]] = mapped_column(JSON, default=list)
    use_cases: Mapped[list[str]] = mapped_column(JSON, default=list)
    sample_audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProviderModel(Base):
    """Provider reference model for TTS/STT providers."""

    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[list[str]] = mapped_column(ARRAY(String(20)), nullable=False)
    supported_models: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    credentials: Mapped[list["UserProviderCredentialModel"]] = relationship(
        "UserProviderCredentialModel", back_populates="provider_ref"
    )


class UserProviderCredentialModel(Base):
    """User's API key credential for a TTS/STT provider."""

    __tablename__ = "user_provider_credentials"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider_credential"),
        Index("idx_credentials_user_id", "user_id"),
        Index("idx_credentials_provider", "provider"),
        Index("idx_credentials_user_provider", "user_id", "provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), ForeignKey("providers.id"), nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted at rest
    selected_model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="provider_credentials")
    provider_ref: Mapped["ProviderModel"] = relationship(
        "ProviderModel", back_populates="credentials"
    )


class AuditLogModel(Base):
    """Audit log model for security and compliance tracking."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_event_type", "event_type"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_provider", "provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")


# =============================================================================
# STT Module Models (Phase 3)
# =============================================================================


class AudioFileModel(Base):
    """Audio file model for STT testing."""

    __tablename__ = "audio_files"
    __table_args__ = (
        Index("idx_audio_file_user_id", "user_id"),
        Index("idx_audio_file_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # 'upload' or 'recording'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")
    ground_truth: Mapped["GroundTruthModel | None"] = relationship(
        "GroundTruthModel", back_populates="audio_file", uselist=False, cascade="all, delete-orphan"
    )
    transcription_requests: Mapped[list["TranscriptionRequestModel"]] = relationship(
        "TranscriptionRequestModel", back_populates="audio_file", cascade="all, delete-orphan"
    )


class GroundTruthModel(Base):
    """Ground truth text for accuracy calculation."""

    __tablename__ = "ground_truths"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audio_files.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    audio_file: Mapped["AudioFileModel"] = relationship(
        "AudioFileModel", back_populates="ground_truth"
    )
    wer_analyses: Mapped[list["WERAnalysisModel"]] = relationship(
        "WERAnalysisModel", back_populates="ground_truth", cascade="all, delete-orphan"
    )


class TranscriptionRequestModel(Base):
    """STT transcription request."""

    __tablename__ = "transcription_requests"
    __table_args__ = (
        Index("idx_transcription_request_audio", "audio_file_id"),
        Index("idx_transcription_request_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="zh-TW")
    child_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # 'pending', 'processing', 'completed', 'failed'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    audio_file: Mapped["AudioFileModel"] = relationship(
        "AudioFileModel", back_populates="transcription_requests"
    )
    result: Mapped["TranscriptionResultModel | None"] = relationship(
        "TranscriptionResultModel",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan",
    )


class TranscriptionResultModel(Base):
    """STT transcription result."""

    __tablename__ = "transcription_results"
    __table_args__ = (Index("idx_transcription_result_request", "request_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcription_requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    request: Mapped["TranscriptionRequestModel"] = relationship(
        "TranscriptionRequestModel", back_populates="result"
    )
    words: Mapped[list["WordTimingModel"]] = relationship(
        "WordTimingModel", back_populates="result", cascade="all, delete-orphan"
    )
    wer_analysis: Mapped["WERAnalysisModel | None"] = relationship(
        "WERAnalysisModel", back_populates="result", uselist=False, cascade="all, delete-orphan"
    )


class WordTimingModel(Base):
    """Word-level timing from STT."""

    __tablename__ = "word_timings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcription_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationships
    result: Mapped["TranscriptionResultModel"] = relationship(
        "TranscriptionResultModel", back_populates="words"
    )


class WERAnalysisModel(Base):
    """WER/CER analysis result."""

    __tablename__ = "wer_analyses"
    __table_args__ = (Index("idx_wer_analysis_result", "result_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcription_results.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    ground_truth_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ground_truths.id", ondelete="CASCADE"), nullable=False
    )
    error_rate: Mapped[float] = mapped_column(Float, nullable=False)
    error_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'WER' or 'CER'
    insertions: Mapped[int] = mapped_column(Integer, nullable=False)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False)
    substitutions: Mapped[int] = mapped_column(Integer, nullable=False)
    alignment: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    result: Mapped["TranscriptionResultModel"] = relationship(
        "TranscriptionResultModel", back_populates="wer_analysis"
    )
    ground_truth: Mapped["GroundTruthModel"] = relationship(
        "GroundTruthModel", back_populates="wer_analyses"
    )


# =============================================================================
# Interaction Module Models (Phase 4)
# =============================================================================


class InteractionSessionModel(Base):
    """SQLAlchemy model for interaction sessions."""

    __tablename__ = "interaction_sessions"
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[InteractionMode] = mapped_column(
        Enum(
            InteractionMode,
            name="interaction_mode",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    provider_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # US4: Role and scenario configuration
    user_role: Mapped[str] = mapped_column(String(100), nullable=False, default="使用者")
    ai_role: Mapped[str] = mapped_column(String(100), nullable=False, default="AI 助理")
    scenario_context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(
            SessionStatus,
            name="session_status",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SessionStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    turns: Mapped[list["ConversationTurnModel"]] = relationship(
        "ConversationTurnModel", back_populates="session", cascade="all, delete-orphan"
    )


class ConversationTurnModel(Base):
    """SQLAlchemy model for conversation turns."""

    __tablename__ = "conversation_turns"
    __table_args__ = (
        Index("idx_turn_session_id", "session_id"),
        Index("idx_turn_session_number", "session_id", "turn_number"),
        UniqueConstraint("session_id", "turn_number", name="uq_turn_session_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interaction_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interrupted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session: Mapped["InteractionSessionModel"] = relationship(
        "InteractionSessionModel", back_populates="turns"
    )
    latency_metrics: Mapped["LatencyMetricsModel | None"] = relationship(
        "LatencyMetricsModel", back_populates="turn", uselist=False, cascade="all, delete-orphan"
    )


class LatencyMetricsModel(Base):
    """SQLAlchemy model for latency metrics."""

    __tablename__ = "latency_metrics"
    __table_args__ = (Index("idx_latency_turn_id", "turn_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_turns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    total_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    stt_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_ttft_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tts_ttfb_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    realtime_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    turn: Mapped["ConversationTurnModel"] = relationship(
        "ConversationTurnModel", back_populates="latency_metrics"
    )


class SystemPromptTemplateModel(Base):
    """SQLAlchemy model for system prompt templates."""

    __tablename__ = "system_prompt_templates"
    __table_args__ = (Index("idx_template_category", "category"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt_content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# =============================================================================
# Async Job Management Models (Feature 007)
# =============================================================================


class JobModel(Base):
    """SQLAlchemy model for async TTS synthesis jobs."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index("idx_jobs_user_status", "user_id", "status"),
        Index("idx_jobs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Use PostgreSQL ENUM to match migration schema
    job_type: Mapped[str] = mapped_column(
        PgEnum("multi_role_tts", name="job_type", create_type=False),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            "pending",
            "processing",
            "completed",
            "failed",
            "cancelled",
            name="job_status",
            create_type=False,
        ),
        nullable=False,
        default="pending",
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    input_params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    audio_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="SET NULL"), nullable=True
    )
    result_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    audio_file: Mapped["AudioFileModel | None"] = relationship("AudioFileModel")


class ScenarioTemplateModel(Base):
    """SQLAlchemy model for scenario templates (US4).

    Contains role and context configuration for voice interactions.
    """

    __tablename__ = "scenario_templates"
    __table_args__ = (
        Index("idx_scenario_template_category", "category"),
        Index("idx_scenario_template_is_default", "is_default"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    user_role: Mapped[str] = mapped_column(String(100), nullable=False)
    ai_role: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_context: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# =============================================================================
# Voice Sync Models (Feature 008)
# =============================================================================


class VoiceSyncJobModel(Base):
    """SQLAlchemy model for voice sync job tracking.

    Tracks background sync operations that fetch voice metadata from providers.
    """

    __tablename__ = "voice_sync_jobs"
    __table_args__ = (
        Index("idx_voice_sync_jobs_status", "status"),
        Index("idx_voice_sync_jobs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID as string
    providers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # List of providers
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    voices_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    voices_deprecated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# =============================================================================
# DJ Models (Feature 011 - Magic DJ Audio Features)
# =============================================================================


class DJPresetModel(Base):
    """SQLAlchemy model for DJ preset (track collection).

    Represents a user's preset configuration for Magic DJ Controller.
    """

    __tablename__ = "dj_presets"
    __table_args__ = (
        Index("idx_dj_presets_user_id", "user_id"),
        UniqueConstraint("user_id", "name", name="uq_dj_presets_user_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    tracks: Mapped[list["DJTrackModel"]] = relationship(
        "DJTrackModel", back_populates="preset", cascade="all, delete-orphan"
    )


class DJTrackModel(Base):
    """SQLAlchemy model for DJ track.

    Represents an audio track within a DJ preset.
    """

    __tablename__ = "dj_tracks"
    __table_args__ = (
        Index("idx_dj_tracks_preset_id", "preset_id"),
        Index("idx_dj_tracks_sort_order", "preset_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    preset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dj_presets.id", ondelete="CASCADE"), nullable=False
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # dj_track_type enum
    hotkey: Mapped[str | None] = mapped_column(String(10), nullable=True)
    loop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Source info
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # dj_track_source enum

    # TTS fields
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tts_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tts_voice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tts_speed: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2), nullable=False, default=Decimal("1.0")
    )

    # Upload fields
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Audio info
    audio_storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="audio/mpeg")

    # Volume
    volume: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), nullable=False, default=Decimal("1.0"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    preset: Mapped["DJPresetModel"] = relationship("DJPresetModel", back_populates="tracks")


# =============================================================================
# Music Generation Models (Feature 012)
# =============================================================================


class MusicGenerationJobModel(Base):
    """SQLAlchemy model for music generation jobs via Mureka AI.

    Tracks async music generation tasks including songs, instrumentals, and lyrics.
    """

    __tablename__ = "music_generation_jobs"
    __table_args__ = (
        Index("ix_music_jobs_user_id", "user_id"),
        Index("ix_music_jobs_status", "status"),
        Index("ix_music_jobs_user_status", "user_id", "status"),
        Index("ix_music_jobs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        PgEnum("song", "instrumental", "lyrics", name="music_generation_type", create_type=False),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            "pending",
            "processing",
            "completed",
            "failed",
            name="music_generation_status",
            create_type=False,
        ),
        nullable=False,
        default="pending",
    )

    # Input parameters
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    lyrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(20), nullable=False, default="auto")

    # Mureka task tracking
    mureka_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Output
    result_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_lyrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User")

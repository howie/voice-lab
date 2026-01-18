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
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    """Voice cache model for caching available voices."""

    __tablename__ = "voice_cache"
    __table_args__ = (
        Index("idx_voice_cache_provider", "provider"),
        Index("idx_voice_cache_language", "language"),
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # provider:voice_id
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    styles: Mapped[dict[str, Any]] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=True)
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

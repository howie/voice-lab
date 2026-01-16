import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import String, Integer, DateTime, func, JSON, Float, Text, DECIMAL, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.database import Base


class User(Base):
    """User model for Google SSO authentication (FR-020)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    google_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    synthesis_logs: Mapped[list["SynthesisLog"]] = relationship(
        "SynthesisLog", back_populates="user"
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

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_estimate: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

# Data Model: VoAI Multi-Role Voice Generation Enhancement

**Feature**: 008-voai-multi-role-voice-generation
**Date**: 2026-01-22

---

## Entity Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Domain Entities                          │
├─────────────────────────────────────────────────────────────────┤
│  VoiceProfile (existing)     VoiceSyncJob (new)                 │
│  └── + AgeGroup enum         └── tracks sync operations         │
│                                                                 │
│  DialogueTurn (existing)     SynthesisMode (existing enum)      │
│  └── used by SSML/Dialogue   └── native | segmented             │
│      builders                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Models                        │
├─────────────────────────────────────────────────────────────────┤
│  VoiceCache (DB model - enhanced)                               │
│  └── + age_group: str | None                                    │
│  └── + styles: JSON (list[str])                                 │
│  └── + use_cases: JSON (list[str])                              │
│  └── + is_deprecated: bool                                      │
│  └── + synced_at: datetime                                      │
│  └── + sample_audio_url: str | None                             │
│                                                                 │
│  VoiceSyncJobModel (DB model - new)                             │
│  └── tracks background sync job status                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Domain Entities

### 1.1 AgeGroup (New Enum)

```python
# backend/src/domain/entities/voice.py

class AgeGroup(Enum):
    """Voice age group classification."""

    CHILD = "child"      # 兒童聲音
    YOUNG = "young"      # 青年聲音
    ADULT = "adult"      # 成人聲音
    SENIOR = "senior"    # 長者聲音
```

**Validation Rules**:
- 可為 None（未分類的聲音）
- 值必須為 enum 成員之一

### 1.2 VoiceProfile (Enhanced)

```python
# backend/src/domain/entities/voice.py

@dataclass(frozen=True)
class VoiceProfile:
    """Voice profile entity with extended metadata."""

    id: str                         # provider:voice_id
    provider: str                   # azure, gcp, elevenlabs
    voice_id: str                   # Provider-specific voice ID
    display_name: str
    language: str                   # zh-TW, en-US
    gender: Gender | None = None
    age_group: AgeGroup | None = None          # NEW
    styles: tuple[str, ...] = ()               # NEW: news, conversation, cheerful
    use_cases: tuple[str, ...] = ()            # NEW: narration, assistant, character
    description: str = ""
    sample_audio_url: str | None = None
    is_deprecated: bool = False                 # NEW
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    synced_at: datetime | None = None          # NEW
```

**Identity Rules**:
- `id` 為複合鍵：`{provider}:{voice_id}`
- 唯一性由 `id` 保證

**Lifecycle/State Transitions**:
```text
[New] ──sync──► [Active] ──provider_removes──► [Deprecated]
                   │                               │
                   └──sync_update──►───────────────┘

Note: Deprecated 聲音不會被刪除，僅標記狀態
```

### 1.3 VoiceSyncJob (New Entity)

```python
# backend/src/domain/entities/voice_sync_job.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

class VoiceSyncStatus(Enum):
    """Voice sync job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class VoiceSyncJob:
    """Voice synchronization job entity."""

    id: UUID
    provider: str | None           # None = all providers
    status: VoiceSyncStatus
    voices_added: int = 0
    voices_updated: int = 0
    voices_deprecated: int = 0
    error_message: str | None = None
    retry_count: int = 0           # 重試次數 (max: 3)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Identity Rules**:
- `id` 為 UUID，由系統產生
- 每個 sync 操作產生一個新的 job

**State Transitions**:
```text
[PENDING] ──start──► [RUNNING] ──success──► [COMPLETED]
                        │
                        └──failure──► [FAILED]
                                        │
                                        └──retry (if retry_count < 3)──► [PENDING]
```

---

## 2. Infrastructure Models (SQLAlchemy)

### 2.1 VoiceCache (Enhanced)

```python
# backend/src/infrastructure/persistence/models.py

class VoiceCache(Base):
    """Voice cache model for caching available voices."""

    __tablename__ = "voice_cache"
    __table_args__ = (
        Index("idx_voice_cache_provider", "provider"),
        Index("idx_voice_cache_language", "language"),
        Index("idx_voice_cache_age_group", "age_group"),     # NEW
        Index("idx_voice_cache_deprecated", "is_deprecated"), # NEW
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)  # NEW
    styles: Mapped[list[str]] = mapped_column(JSON, default=list)             # ENHANCED
    use_cases: Mapped[list[str]] = mapped_column(JSON, default=list)          # NEW
    sample_audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False)       # NEW
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # NEW
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### 2.2 VoiceSyncJobModel (New)

```python
# backend/src/infrastructure/persistence/models.py

class VoiceSyncJobModel(Base):
    """Voice sync job model for tracking synchronization operations."""

    __tablename__ = "voice_sync_jobs"
    __table_args__ = (
        Index("idx_voice_sync_jobs_status", "status"),
        Index("idx_voice_sync_jobs_provider", "provider"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    voices_added: Mapped[int] = mapped_column(Integer, default=0)
    voices_updated: Mapped[int] = mapped_column(Integer, default=0)
    voices_deprecated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

## 3. Repository Interfaces

### 3.1 VoiceCacheRepository (New Protocol)

```python
# backend/src/application/interfaces/voice_repository.py

from typing import Protocol
from collections.abc import Sequence
from src.domain.entities.voice import VoiceProfile, AgeGroup

class VoiceCacheRepository(Protocol):
    """Repository interface for voice cache operations."""

    async def get_by_id(self, voice_id: str) -> VoiceProfile | None:
        """Get voice by ID (provider:voice_id)."""
        ...

    async def get_by_provider(
        self,
        provider: str,
        *,
        language: str | None = None,
        gender: str | None = None,
        age_group: AgeGroup | None = None,
        style: str | None = None,
        include_deprecated: bool = False,
    ) -> Sequence[VoiceProfile]:
        """Get voices by provider with optional filters."""
        ...

    async def list_all(
        self,
        *,
        language: str | None = None,
        gender: str | None = None,
        age_group: AgeGroup | None = None,
        style: str | None = None,
        include_deprecated: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[VoiceProfile]:
        """List all voices with optional filters and pagination."""
        ...

    async def upsert(self, voice: VoiceProfile) -> VoiceProfile:
        """Insert or update a voice profile."""
        ...

    async def upsert_batch(self, voices: Sequence[VoiceProfile]) -> int:
        """Batch upsert voice profiles. Returns count of affected rows."""
        ...

    async def mark_deprecated(self, voice_ids: Sequence[str]) -> int:
        """Mark voices as deprecated. Returns count of affected rows."""
        ...

    async def get_last_sync_time(self, provider: str) -> datetime | None:
        """Get the last sync time for a provider."""
        ...
```

### 3.2 VoiceSyncJobRepository (New Protocol)

```python
# backend/src/application/interfaces/voice_sync_job_repository.py

from typing import Protocol
from uuid import UUID
from src.domain.entities.voice_sync_job import VoiceSyncJob, VoiceSyncStatus

class VoiceSyncJobRepository(Protocol):
    """Repository interface for voice sync job operations."""

    async def create(self, job: VoiceSyncJob) -> VoiceSyncJob:
        """Create a new sync job."""
        ...

    async def get_by_id(self, job_id: UUID) -> VoiceSyncJob | None:
        """Get sync job by ID."""
        ...

    async def update_status(
        self,
        job_id: UUID,
        status: VoiceSyncStatus,
        *,
        voices_added: int | None = None,
        voices_updated: int | None = None,
        voices_deprecated: int | None = None,
        error_message: str | None = None,
    ) -> VoiceSyncJob | None:
        """Update sync job status and metrics."""
        ...

    async def get_latest_by_provider(self, provider: str | None) -> VoiceSyncJob | None:
        """Get the latest sync job for a provider."""
        ...

    async def list_recent(self, limit: int = 10) -> Sequence[VoiceSyncJob]:
        """List recent sync jobs."""
        ...
```

---

## 4. Alembic Migration

```python
# backend/alembic/versions/xxx_add_voice_cache_fields.py

"""Add voice cache enhancement fields.

Revision ID: xxx
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to voice_cache
    op.add_column('voice_cache', sa.Column('age_group', sa.String(20), nullable=True))
    op.add_column('voice_cache', sa.Column('use_cases', sa.JSON(), default=list))
    op.add_column('voice_cache', sa.Column('sample_audio_url', sa.String(512), nullable=True))
    op.add_column('voice_cache', sa.Column('is_deprecated', sa.Boolean(), default=False))
    op.add_column('voice_cache', sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True))

    # Create indexes
    op.create_index('idx_voice_cache_age_group', 'voice_cache', ['age_group'])
    op.create_index('idx_voice_cache_deprecated', 'voice_cache', ['is_deprecated'])

    # Create voice_sync_jobs table
    op.create_table(
        'voice_sync_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('voices_added', sa.Integer(), default=0),
        sa.Column('voices_updated', sa.Integer(), default=0),
        sa.Column('voices_deprecated', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_voice_sync_jobs_status', 'voice_sync_jobs', ['status'])
    op.create_index('idx_voice_sync_jobs_provider', 'voice_sync_jobs', ['provider'])

def downgrade() -> None:
    op.drop_table('voice_sync_jobs')
    op.drop_index('idx_voice_cache_deprecated')
    op.drop_index('idx_voice_cache_age_group')
    op.drop_column('voice_cache', 'synced_at')
    op.drop_column('voice_cache', 'is_deprecated')
    op.drop_column('voice_cache', 'sample_audio_url')
    op.drop_column('voice_cache', 'use_cases')
    op.drop_column('voice_cache', 'age_group')
```

---

## 5. Data Volume & Scale

| Entity | 預估數量 | 成長率 |
|--------|---------|--------|
| VoiceCache | ~800 | 低（Provider 新增聲音時才增加） |
| VoiceSyncJob | ~365/year | 每日一次同步 |

**Storage 預估**：
- VoiceCache: ~800 rows × ~2 KB/row ≈ 1.6 MB
- VoiceSyncJob: ~365 rows/year × ~0.5 KB/row ≈ 180 KB/year

**Query 模式**：
- 高頻：`list_all()` with filters（聲音列表頁面）
- 中頻：`get_by_provider()` with filters（Provider 篩選）
- 低頻：`get_by_id()`（單一聲音詳情）

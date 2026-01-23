# Data Model: Audiobook Production System

**Feature**: 009-audiobook-production
**Date**: 2026-01-22

---

## Entity Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Domain Entities                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  AudiobookProject          Character              ScriptTurn                 │
│  └── 專案主體              └── 角色定義           └── 台詞片段               │
│                                                                              │
│  AudiobookGenerationJob    BackgroundMusic                                   │
│  └── 生成任務追蹤          └── 背景音樂                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Enums                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ProjectStatus: draft | generating | completed | failed                      │
│  TurnStatus: pending | generating | completed | failed                       │
│  JobStatus: pending | running | completed | failed | cancelled               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Domain Entities

### 1.1 ProjectStatus (Enum)

```python
# backend/src/domain/entities/audiobook_project.py

class ProjectStatus(Enum):
    """Audiobook project status."""

    DRAFT = "draft"            # 編輯中
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 生成失敗
```

### 1.2 TurnStatus (Enum)

```python
# backend/src/domain/entities/script_turn.py

class TurnStatus(Enum):
    """Script turn generation status."""

    PENDING = "pending"        # 等待生成
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失敗
```

### 1.3 AudiobookProject (Entity)

```python
# backend/src/domain/entities/audiobook_project.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass
class AudiobookProject:
    """Audiobook project entity."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.DRAFT
    script_content: str = ""                    # 劇本原始內容
    language: str = "zh-TW"                     # 預設語言
    background_music_id: UUID | None = None
    background_music_volume: float = 0.3        # 0.0 - 1.0
    output_audio_url: str | None = None         # 最終輸出 URL
    output_duration_ms: int | None = None       # 輸出時長
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

**Identity Rules**:
- `id` 為 UUID，由系統產生
- `user_id` 關聯到使用者（外部系統）

**State Transitions**:
```text
[DRAFT] ──start_generation──► [GENERATING] ──success──► [COMPLETED]
   │                               │
   └──edit──► [DRAFT]              └──failure──► [FAILED]
                                                    │
                                                    └──retry──► [GENERATING]
```

### 1.4 Character (Entity)

```python
# backend/src/domain/entities/character.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass
class Character:
    """Character entity for audiobook."""

    id: UUID
    project_id: UUID
    name: str                              # 角色名稱（從劇本提取）
    voice_id: str | None = None            # provider:voice_id
    gender: str | None = None              # male, female, neutral
    age_group: str | None = None           # child, young, adult, senior
    style: str | None = None               # cheerful, sad, news, etc.
    speech_rate: float = 1.0               # 語速 0.5 - 2.0
    pitch: float = 0.0                     # 音調 -50% - +50%
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

**Identity Rules**:
- `id` 為 UUID
- `project_id` + `name` 在專案內唯一

**Validation Rules**:
- `speech_rate`: 0.5 - 2.0
- `pitch`: -50.0 - 50.0
- `voice_id` 格式: `{provider}:{voice_id}`

### 1.5 ScriptTurn (Entity)

```python
# backend/src/domain/entities/script_turn.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass
class ScriptTurn:
    """Script turn (dialogue line) entity."""

    id: UUID
    project_id: UUID
    character_id: UUID
    sequence: int                          # 順序（從 1 開始）
    text: str                              # 台詞內容
    chapter: str | None = None             # 章節名稱
    audio_url: str | None = None           # 生成的音訊 URL
    duration_ms: int | None = None         # 音訊時長（毫秒）
    status: TurnStatus = TurnStatus.PENDING
    error_message: str | None = None
    retry_count: int = 0                   # 重試次數
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

**Identity Rules**:
- `id` 為 UUID
- `project_id` + `sequence` 唯一

**State Transitions**:
```text
[PENDING] ──start──► [GENERATING] ──success──► [COMPLETED]
                          │
                          └──failure (retry < 3)──► [PENDING]
                          │
                          └──failure (retry >= 3)──► [FAILED]
```

### 1.6 AudiobookGenerationJob (Entity)

```python
# backend/src/domain/entities/audiobook_job.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from enum import Enum

class JobStatus(Enum):
    """Generation job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AudiobookGenerationJob:
    """Audiobook generation job entity."""

    id: UUID
    project_id: UUID
    status: JobStatus = JobStatus.PENDING
    total_turns: int = 0
    completed_turns: int = 0
    failed_turns: int = 0
    current_turn_id: UUID | None = None    # 目前處理的 turn
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**State Transitions**:
```text
[PENDING] ──start──► [RUNNING] ──all_completed──► [COMPLETED]
              │                        │
              │                        └──has_failures──► [FAILED]
              │
              └──cancel──► [CANCELLED]
```

### 1.7 BackgroundMusic (Entity)

```python
# backend/src/domain/entities/background_music.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass
class BackgroundMusic:
    """Background music entity."""

    id: UUID
    project_id: UUID
    filename: str                          # 原始檔名
    file_url: str                          # 儲存 URL
    duration_ms: int                       # 時長（毫秒）
    format: str                            # mp3, wav
    file_size_bytes: int
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- `format`: mp3, wav
- `file_size_bytes`: < 50 MB (52,428,800 bytes)

---

## 2. Infrastructure Models (SQLAlchemy)

### 2.1 AudiobookProjectModel

```python
# backend/src/infrastructure/persistence/models.py

class AudiobookProjectModel(Base):
    """Audiobook project database model."""

    __tablename__ = "audiobook_projects"
    __table_args__ = (
        Index("idx_audiobook_projects_user_id", "user_id"),
        Index("idx_audiobook_projects_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    script_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="zh-TW")
    background_music_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    background_music_volume: Mapped[float] = mapped_column(Float, default=0.3)
    output_audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    characters: Mapped[list["CharacterModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    turns: Mapped[list["ScriptTurnModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    background_music: Mapped["BackgroundMusicModel | None"] = relationship(
        back_populates="project", uselist=False
    )
```

### 2.2 CharacterModel

```python
class CharacterModel(Base):
    """Character database model."""

    __tablename__ = "audiobook_characters"
    __table_args__ = (
        Index("idx_audiobook_characters_project_id", "project_id"),
        UniqueConstraint("project_id", "name", name="uq_character_project_name"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    speech_rate: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["AudiobookProjectModel"] = relationship(back_populates="characters")
    turns: Mapped[list["ScriptTurnModel"]] = relationship(back_populates="character")
```

### 2.3 ScriptTurnModel

```python
class ScriptTurnModel(Base):
    """Script turn database model."""

    __tablename__ = "audiobook_script_turns"
    __table_args__ = (
        Index("idx_script_turns_project_id", "project_id"),
        Index("idx_script_turns_status", "status"),
        UniqueConstraint("project_id", "sequence", name="uq_turn_project_sequence"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False
    )
    character_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("audiobook_characters.id", ondelete="CASCADE"),
        nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(100), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["AudiobookProjectModel"] = relationship(back_populates="turns")
    character: Mapped["CharacterModel"] = relationship(back_populates="turns")
```

### 2.4 AudiobookGenerationJobModel

```python
class AudiobookGenerationJobModel(Base):
    """Audiobook generation job database model."""

    __tablename__ = "audiobook_generation_jobs"
    __table_args__ = (
        Index("idx_generation_jobs_project_id", "project_id"),
        Index("idx_generation_jobs_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total_turns: Mapped[int] = mapped_column(Integer, default=0)
    completed_turns: Mapped[int] = mapped_column(Integer, default=0)
    failed_turns: Mapped[int] = mapped_column(Integer, default=0)
    current_turn_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

### 2.5 BackgroundMusicModel

```python
class BackgroundMusicModel(Base):
    """Background music database model."""

    __tablename__ = "audiobook_background_music"
    __table_args__ = (
        Index("idx_background_music_project_id", "project_id"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("audiobook_projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # 一個專案只能有一個背景音樂
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    project: Mapped["AudiobookProjectModel"] = relationship(back_populates="background_music")
```

---

## 3. Repository Interfaces

### 3.1 AudiobookProjectRepository

```python
# backend/src/application/interfaces/audiobook_repository.py

from typing import Protocol
from collections.abc import Sequence
from uuid import UUID
from src.domain.entities.audiobook_project import AudiobookProject, ProjectStatus

class AudiobookProjectRepository(Protocol):
    """Repository interface for audiobook project operations."""

    async def create(self, project: AudiobookProject) -> AudiobookProject:
        """Create a new project."""
        ...

    async def get_by_id(self, project_id: UUID) -> AudiobookProject | None:
        """Get project by ID."""
        ...

    async def get_by_user(
        self,
        user_id: UUID,
        *,
        status: ProjectStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[AudiobookProject]:
        """List projects by user."""
        ...

    async def update(self, project: AudiobookProject) -> AudiobookProject:
        """Update project."""
        ...

    async def delete(self, project_id: UUID) -> bool:
        """Delete project and all related data."""
        ...
```

### 3.2 CharacterRepository

```python
class CharacterRepository(Protocol):
    """Repository interface for character operations."""

    async def create(self, character: Character) -> Character:
        ...

    async def get_by_id(self, character_id: UUID) -> Character | None:
        ...

    async def get_by_project(self, project_id: UUID) -> Sequence[Character]:
        ...

    async def get_by_name(self, project_id: UUID, name: str) -> Character | None:
        ...

    async def update(self, character: Character) -> Character:
        ...

    async def delete(self, character_id: UUID) -> bool:
        ...

    async def upsert_batch(
        self, project_id: UUID, characters: Sequence[Character]
    ) -> Sequence[Character]:
        """Batch upsert characters (for script parsing)."""
        ...
```

### 3.3 ScriptTurnRepository

```python
class ScriptTurnRepository(Protocol):
    """Repository interface for script turn operations."""

    async def create_batch(self, turns: Sequence[ScriptTurn]) -> Sequence[ScriptTurn]:
        """Batch create turns."""
        ...

    async def get_by_project(
        self,
        project_id: UUID,
        *,
        status: TurnStatus | None = None,
    ) -> Sequence[ScriptTurn]:
        ...

    async def get_pending(self, project_id: UUID, limit: int = 10) -> Sequence[ScriptTurn]:
        """Get pending turns for processing."""
        ...

    async def update_status(
        self,
        turn_id: UUID,
        status: TurnStatus,
        *,
        audio_url: str | None = None,
        duration_ms: int | None = None,
        error_message: str | None = None,
    ) -> ScriptTurn | None:
        ...

    async def delete_by_project(self, project_id: UUID) -> int:
        """Delete all turns for a project (for re-parsing)."""
        ...
```

---

## 4. Alembic Migration

```python
# backend/alembic/versions/xxx_add_audiobook_tables.py

"""Add audiobook production tables.

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
    # Create audiobook_projects table
    op.create_table(
        'audiobook_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('script_content', sa.Text(), nullable=False, default=''),
        sa.Column('language', sa.String(10), nullable=False, default='zh-TW'),
        sa.Column('background_music_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('background_music_volume', sa.Float(), default=0.3),
        sa.Column('output_audio_url', sa.String(512), nullable=True),
        sa.Column('output_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_audiobook_projects_user_id', 'audiobook_projects', ['user_id'])
    op.create_index('idx_audiobook_projects_status', 'audiobook_projects', ['status'])

    # Create audiobook_characters table
    op.create_table(
        'audiobook_characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('voice_id', sa.String(255), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('age_group', sa.String(20), nullable=True),
        sa.Column('style', sa.String(50), nullable=True),
        sa.Column('speech_rate', sa.Float(), default=1.0),
        sa.Column('pitch', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['audiobook_projects.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('project_id', 'name', name='uq_character_project_name'),
    )
    op.create_index('idx_audiobook_characters_project_id', 'audiobook_characters', ['project_id'])

    # Create audiobook_script_turns table
    op.create_table(
        'audiobook_script_turns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('chapter', sa.String(100), nullable=True),
        sa.Column('audio_url', sa.String(512), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['audiobook_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['character_id'], ['audiobook_characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('project_id', 'sequence', name='uq_turn_project_sequence'),
    )
    op.create_index('idx_script_turns_project_id', 'audiobook_script_turns', ['project_id'])
    op.create_index('idx_script_turns_status', 'audiobook_script_turns', ['status'])

    # Create audiobook_generation_jobs table
    op.create_table(
        'audiobook_generation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('total_turns', sa.Integer(), default=0),
        sa.Column('completed_turns', sa.Integer(), default=0),
        sa.Column('failed_turns', sa.Integer(), default=0),
        sa.Column('current_turn_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['audiobook_projects.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_generation_jobs_project_id', 'audiobook_generation_jobs', ['project_id'])
    op.create_index('idx_generation_jobs_status', 'audiobook_generation_jobs', ['status'])

    # Create audiobook_background_music table
    op.create_table(
        'audiobook_background_music',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_url', sa.String(512), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['audiobook_projects.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_background_music_project_id', 'audiobook_background_music', ['project_id'])


def downgrade() -> None:
    op.drop_table('audiobook_background_music')
    op.drop_table('audiobook_generation_jobs')
    op.drop_table('audiobook_script_turns')
    op.drop_table('audiobook_characters')
    op.drop_table('audiobook_projects')
```

---

## 5. Data Volume & Scale

| Entity | 預估數量 | 成長率 |
|--------|---------|--------|
| AudiobookProject | 100/user/year | 中（依使用頻率） |
| Character | ~10/project | 低（專案內固定） |
| ScriptTurn | ~200/project | 低（專案內固定） |
| AudiobookGenerationJob | 1-3/project | 低 |
| BackgroundMusic | 0-1/project | 低 |

**Storage 預估**（per project）:
- Metadata: ~10 KB
- Script turns audio: ~20-40 MB (10-20 min)
- Background music: ~10 MB
- Final output: ~20-40 MB

**Query 模式**：
- 高頻：`get_by_user()` (專案列表)
- 中頻：`get_by_project()` (角色/台詞列表)
- 中頻：`get_pending()` (Worker 取得待處理項目)
- 低頻：`get_by_id()` (單一項目詳情)

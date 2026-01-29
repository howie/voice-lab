"""Add DJ presets and tracks tables for Magic DJ Controller

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

Revision ID: 20260129_100000
Revises: 20260122_100000
Create Date: 2026-01-29 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260129_100000"
down_revision: str | None = "20260122_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create dj_track_type enum
    dj_track_type_enum = postgresql.ENUM(
        "intro",
        "transition",
        "effect",
        "song",
        "filler",
        "rescue",
        name="dj_track_type",
        create_type=False,
    )
    dj_track_type_enum.create(op.get_bind(), checkfirst=True)

    # Create dj_track_source enum
    dj_track_source_enum = postgresql.ENUM(
        "tts",
        "upload",
        name="dj_track_source",
        create_type=False,
    )
    dj_track_source_enum.create(op.get_bind(), checkfirst=True)

    # Create dj_presets table
    op.create_table(
        "dj_presets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "settings",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "name", name="uq_dj_presets_user_name"),
    )

    # Create dj_tracks table
    op.create_table(
        "dj_tracks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("preset_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Basic info
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "intro",
                "transition",
                "effect",
                "song",
                "filler",
                "rescue",
                name="dj_track_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("hotkey", sa.String(10), nullable=True),
        sa.Column("loop", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        # Source info
        sa.Column(
            "source",
            postgresql.ENUM(
                "tts",
                "upload",
                name="dj_track_source",
                create_type=False,
            ),
            nullable=False,
        ),
        # TTS fields (source = 'tts')
        sa.Column("text_content", sa.Text, nullable=True),
        sa.Column("tts_provider", sa.String(50), nullable=True),
        sa.Column("tts_voice_id", sa.String(100), nullable=True),
        sa.Column("tts_speed", sa.Numeric(3, 2), nullable=False, server_default="1.0"),
        # Upload fields (source = 'upload')
        sa.Column("original_filename", sa.String(255), nullable=True),
        # Audio info
        sa.Column("audio_storage_path", sa.String(500), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("content_type", sa.String(100), nullable=False, server_default="'audio/mpeg'"),
        # Volume
        sa.Column("volume", sa.Numeric(3, 2), nullable=False, server_default="1.0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["preset_id"], ["dj_presets.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("idx_dj_presets_user_id", "dj_presets", ["user_id"])
    op.create_index("idx_dj_tracks_preset_id", "dj_tracks", ["preset_id"])
    op.create_index("idx_dj_tracks_sort_order", "dj_tracks", ["preset_id", "sort_order"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_dj_tracks_sort_order", table_name="dj_tracks")
    op.drop_index("idx_dj_tracks_preset_id", table_name="dj_tracks")
    op.drop_index("idx_dj_presets_user_id", table_name="dj_presets")

    # Drop tables
    op.drop_table("dj_tracks")
    op.drop_table("dj_presets")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS dj_track_source")
    op.execute("DROP TYPE IF EXISTS dj_track_type")

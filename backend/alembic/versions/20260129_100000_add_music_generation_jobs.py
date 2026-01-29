"""Add music_generation_jobs table for Mureka AI integration

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
    # Create music_generation_type enum
    music_type_enum = postgresql.ENUM(
        "song",
        "instrumental",
        "lyrics",
        name="music_generation_type",
        create_type=False,
    )
    music_type_enum.create(op.get_bind(), checkfirst=True)

    # Create music_generation_status enum
    music_status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="music_generation_status",
        create_type=False,
    )
    music_status_enum.create(op.get_bind(), checkfirst=True)

    # Create music_generation_jobs table
    op.create_table(
        "music_generation_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "song",
                "instrumental",
                "lyrics",
                name="music_generation_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "processing",
                "completed",
                "failed",
                name="music_generation_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        # Input parameters
        sa.Column("prompt", sa.Text, nullable=True),
        sa.Column("lyrics", sa.Text, nullable=True),
        sa.Column("model", sa.String(20), nullable=False, server_default="auto"),
        # Mureka task tracking
        sa.Column("mureka_task_id", sa.String(100), nullable=True),
        # Output
        sa.Column("result_url", sa.Text, nullable=True),
        sa.Column("original_url", sa.Text, nullable=True),
        sa.Column("cover_url", sa.Text, nullable=True),
        sa.Column("generated_lyrics", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Error handling
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for common queries
    op.create_index("ix_music_jobs_user_id", "music_generation_jobs", ["user_id"])
    op.create_index("ix_music_jobs_status", "music_generation_jobs", ["status"])
    op.create_index("ix_music_jobs_user_status", "music_generation_jobs", ["user_id", "status"])
    op.create_index(
        "ix_music_jobs_created_at",
        "music_generation_jobs",
        [sa.text("created_at DESC")],
    )

    # Create partial indexes for background tasks
    op.create_index(
        "ix_music_jobs_pending",
        "music_generation_jobs",
        ["status", "created_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "ix_music_jobs_processing_timeout",
        "music_generation_jobs",
        ["status", "started_at"],
        postgresql_where=sa.text("status = 'processing'"),
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_music_jobs_processing_timeout", table_name="music_generation_jobs")
    op.drop_index("ix_music_jobs_pending", table_name="music_generation_jobs")
    op.drop_index("ix_music_jobs_created_at", table_name="music_generation_jobs")
    op.drop_index("ix_music_jobs_user_status", table_name="music_generation_jobs")
    op.drop_index("ix_music_jobs_status", table_name="music_generation_jobs")
    op.drop_index("ix_music_jobs_user_id", table_name="music_generation_jobs")

    # Drop table
    op.drop_table("music_generation_jobs")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS music_generation_status")
    op.execute("DROP TYPE IF EXISTS music_generation_type")

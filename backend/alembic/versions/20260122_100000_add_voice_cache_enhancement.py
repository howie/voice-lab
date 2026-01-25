"""Add voice cache enhancement fields and voice sync jobs table

Feature: 008-voai-multi-role-voice-generation
T001: Create Alembic migration for VoiceCache enhancement and VoiceSyncJob table

Revision ID: 20260122_100000
Revises: 20260121_110000
Create Date: 2026-01-22 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260122_100000"
down_revision: str | None = "20260121_110000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add new columns to voice_cache table
    op.add_column(
        "voice_cache",
        sa.Column("age_group", sa.String(20), nullable=True),
    )
    op.add_column(
        "voice_cache",
        sa.Column("use_cases", sa.JSON(), nullable=True, server_default="[]"),
    )
    op.add_column(
        "voice_cache",
        sa.Column("sample_audio_url", sa.String(512), nullable=True),
    )
    op.add_column(
        "voice_cache",
        sa.Column("is_deprecated", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "voice_cache",
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for new columns
    op.create_index("idx_voice_cache_age_group", "voice_cache", ["age_group"])
    op.create_index("idx_voice_cache_deprecated", "voice_cache", ["is_deprecated"])

    # Create voice_sync_jobs table
    op.create_table(
        "voice_sync_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("provider", sa.String(50), nullable=True),  # None = all providers
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("voices_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("voices_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("voices_deprecated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for voice_sync_jobs
    op.create_index("idx_voice_sync_jobs_status", "voice_sync_jobs", ["status"])
    op.create_index("idx_voice_sync_jobs_provider", "voice_sync_jobs", ["provider"])
    op.create_index(
        "idx_voice_sync_jobs_created_at",
        "voice_sync_jobs",
        [sa.text("created_at DESC")],
    )


def downgrade() -> None:
    # Drop voice_sync_jobs indexes
    op.drop_index("idx_voice_sync_jobs_created_at", table_name="voice_sync_jobs")
    op.drop_index("idx_voice_sync_jobs_provider", table_name="voice_sync_jobs")
    op.drop_index("idx_voice_sync_jobs_status", table_name="voice_sync_jobs")

    # Drop voice_sync_jobs table
    op.drop_table("voice_sync_jobs")

    # Drop voice_cache indexes
    op.drop_index("idx_voice_cache_deprecated", table_name="voice_cache")
    op.drop_index("idx_voice_cache_age_group", table_name="voice_cache")

    # Drop voice_cache columns
    op.drop_column("voice_cache", "synced_at")
    op.drop_column("voice_cache", "is_deprecated")
    op.drop_column("voice_cache", "sample_audio_url")
    op.drop_column("voice_cache", "use_cases")
    op.drop_column("voice_cache", "age_group")

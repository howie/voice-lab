"""Fix voice_sync_jobs table schema to match model

Revision ID: 20260130_100000
Revises: 20260129_110000
Create Date: 2026-01-30 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260130_100000"
down_revision: str | None = "20260129_110000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop old indexes that reference provider column
    op.drop_index("idx_voice_sync_jobs_provider", table_name="voice_sync_jobs")

    # Drop old columns
    op.drop_column("voice_sync_jobs", "provider")
    op.drop_column("voice_sync_jobs", "voices_added")
    op.drop_column("voice_sync_jobs", "voices_updated")

    # Add new columns matching the model
    op.add_column(
        "voice_sync_jobs",
        sa.Column("providers", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "voice_sync_jobs",
        sa.Column("voices_synced", sa.Integer(), nullable=False, server_default="0"),
    )

    # Change id column type from UUID to String(36) to match model
    # Note: PostgreSQL UUID and String(36) are compatible for most operations
    op.alter_column(
        "voice_sync_jobs",
        "id",
        existing_type=sa.dialects.postgresql.UUID(),
        type_=sa.String(36),
        existing_nullable=False,
        postgresql_using="id::text",
    )


def downgrade() -> None:
    # Revert id column type
    op.alter_column(
        "voice_sync_jobs",
        "id",
        existing_type=sa.String(36),
        type_=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using="id::uuid",
    )

    # Drop new columns
    op.drop_column("voice_sync_jobs", "voices_synced")
    op.drop_column("voice_sync_jobs", "providers")

    # Add old columns back
    op.add_column(
        "voice_sync_jobs",
        sa.Column("voices_updated", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "voice_sync_jobs",
        sa.Column("voices_added", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "voice_sync_jobs",
        sa.Column("provider", sa.String(50), nullable=True),
    )

    # Recreate old index
    op.create_index("idx_voice_sync_jobs_provider", "voice_sync_jobs", ["provider"])

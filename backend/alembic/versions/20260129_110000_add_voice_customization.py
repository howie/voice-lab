"""Add voice_customization table for TTS voice role management

Feature: 013-tts-role-mgmt
Phase 1: Setup - Database Migration

Revision ID: 20260129_110000
Revises: 20260129_100000
Create Date: 2026-01-29 11:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260129_110000"
down_revision: str | None = "20260129_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create voice_customization table
    op.create_table(
        "voice_customization",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("voice_cache_id", sa.String(255), nullable=False),
        sa.Column("custom_name", sa.String(50), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["voice_cache_id"],
            ["voice_cache.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("voice_cache_id", name="uq_voice_customization_voice_cache_id"),
    )

    # Partial index for favorites (only index TRUE values)
    op.create_index(
        "ix_voice_customization_is_favorite",
        "voice_customization",
        ["is_favorite"],
        postgresql_where=sa.text("is_favorite = true"),
    )

    # Partial index for hidden (only index TRUE values)
    op.create_index(
        "ix_voice_customization_is_hidden",
        "voice_customization",
        ["is_hidden"],
        postgresql_where=sa.text("is_hidden = true"),
    )

    # Create trigger function for auto-updating updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_voice_customization_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER trg_voice_customization_updated_at
            BEFORE UPDATE ON voice_customization
            FOR EACH ROW
            EXECUTE FUNCTION update_voice_customization_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trg_voice_customization_updated_at ON voice_customization")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_voice_customization_updated_at()")

    # Drop indexes
    op.drop_index("ix_voice_customization_is_hidden", table_name="voice_customization")
    op.drop_index("ix_voice_customization_is_favorite", table_name="voice_customization")

    # Drop table
    op.drop_table("voice_customization")

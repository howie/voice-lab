"""Add 'cancelled' value to music_generation_status enum.

Feature: 012-music-generation
Allows users to cancel pending/processing music generation jobs.

Revision ID: 20260221_100000
Revises: 20260220_100000
Create Date: 2026-02-21
"""

from alembic import op

revision = "20260221_100000"
down_revision = "20260220_100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE music_generation_status ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values
    pass

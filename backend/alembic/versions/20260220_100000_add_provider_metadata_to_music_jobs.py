"""Add provider_metadata JSONB column to music_generation_jobs.

Feature: 016-integration-gemini-lyria-music
Stores provider-specific parameters (negative_prompt, seed, sample_count, batch_id).

Revision ID: 20260220_100000
Revises: 20260207_100000
Create Date: 2026-02-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260220_100000"
down_revision = "20260207_100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "music_generation_jobs",
        sa.Column("provider_metadata", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("music_generation_jobs", "provider_metadata")

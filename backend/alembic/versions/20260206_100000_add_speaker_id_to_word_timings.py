"""Add speaker_id to word_timings table for speaker diarization

Revision ID: 20260206_100000
Revises: 20260131_100000
Create Date: 2026-02-06 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260206_100000"
down_revision: str | None = "a3b4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("word_timings", sa.Column("speaker_id", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("word_timings", "speaker_id")

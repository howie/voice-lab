"""Add provider column to music_generation_jobs.

Revision ID: a3b4c5d6e7f8
Revises: 20260129_100000
Create Date: 2026-01-31 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add provider column with default 'mureka' for backward compatibility
    op.add_column(
        "music_generation_jobs",
        sa.Column("provider", sa.String(20), nullable=False, server_default="mureka"),
    )


def downgrade() -> None:
    op.drop_column("music_generation_jobs", "provider")

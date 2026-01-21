"""merge_jobs_table

Revision ID: 96b1d21df7c8
Revises: 20260119_200000, 20260120_100000
Create Date: 2026-01-21 22:02:45.257273

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "96b1d21df7c8"
down_revision: str | None = ("20260119_200000", "20260120_100000")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

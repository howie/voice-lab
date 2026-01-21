"""merge stt and interaction branches

Revision ID: 37230f605b1b
Revises: 20260119_200000, 477f0ffdd804
Create Date: 2026-01-21 08:56:15.191580

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "37230f605b1b"
down_revision: tuple[str, str] = ("20260119_200000", "477f0ffdd804")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

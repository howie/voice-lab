"""Add single_tts to job_type ENUM

Revision ID: 20260207_100000
Revises: 20260206_100000
Create Date: 2026-02-07 10:00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260207_100000"
down_revision: str | None = "20260206_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL's ALTER TYPE ... ADD VALUE cannot run inside a transaction block.
    # Alembic wraps each migration in a transaction by default, so we need to
    # commit the current transaction first, then execute ADD VALUE outside of it.
    op.execute("COMMIT")
    op.execute("ALTER TYPE job_type ADD VALUE IF NOT EXISTS 'single_tts'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an ENUM type.
    # The value will remain but be unused after downgrade.
    pass

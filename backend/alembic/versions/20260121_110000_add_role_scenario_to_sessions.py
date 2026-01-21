"""Add user_role, ai_role, scenario_context to interaction_sessions

Feature: 004-interaction-module
T073 [US4]: Add role and scenario configuration to sessions

Revision ID: 20260121_110000
Revises: 20260121_100000
Create Date: 2026-01-21 11:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260121_110000"
down_revision: str | None = "20260121_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add user_role column with default value
    op.add_column(
        "interaction_sessions",
        sa.Column("user_role", sa.String(100), nullable=False, server_default="使用者"),
    )

    # Add ai_role column with default value
    op.add_column(
        "interaction_sessions",
        sa.Column("ai_role", sa.String(100), nullable=False, server_default="AI 助理"),
    )

    # Add scenario_context column with default value
    op.add_column(
        "interaction_sessions",
        sa.Column("scenario_context", sa.Text, nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("interaction_sessions", "scenario_context")
    op.drop_column("interaction_sessions", "ai_role")
    op.drop_column("interaction_sessions", "user_role")

"""Add StoryPal tables (story_templates, story_sessions, story_turns)

Revision ID: 20260207_200000
Revises: 20260207_100000
Create Date: 2026-02-07 20:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260207_200000"
down_revision: str | None = "20260207_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create story_templates table
    op.create_table(
        "story_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("target_age_min", sa.Integer, nullable=False, server_default="3"),
        sa.Column("target_age_max", sa.Integer, nullable=False, server_default="8"),
        sa.Column("language", sa.String(10), nullable=False, server_default="zh-TW"),
        sa.Column("characters", postgresql.JSONB, nullable=False),
        sa.Column("scenes", postgresql.JSONB, nullable=False),
        sa.Column("opening_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("system_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_story_template_category", "story_templates", ["category"])
    op.create_index("idx_story_template_language", "story_templates", ["language"])

    # Create story_sessions table
    op.create_table(
        "story_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="zh-TW"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("story_state", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("characters_config", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("interaction_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["story_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["interaction_session_id"], ["interaction_sessions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("idx_story_session_user", "story_sessions", ["user_id"])
    op.create_index("idx_story_session_status", "story_sessions", ["status"])

    # Create story_turns table
    op.create_table(
        "story_turns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_number", sa.Integer, nullable=False),
        sa.Column("turn_type", sa.String(20), nullable=False),
        sa.Column("character_name", sa.String(100), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("audio_path", sa.String(500), nullable=True),
        sa.Column("choice_options", postgresql.JSONB, nullable=True),
        sa.Column("child_choice", sa.Text, nullable=True),
        sa.Column("bgm_scene", sa.String(100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["story_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", "turn_number", name="uq_story_turn_number"),
    )
    op.create_index("idx_story_turn_session", "story_turns", ["session_id"])
    op.create_index("idx_story_turn_number", "story_turns", ["session_id", "turn_number"])


def downgrade() -> None:
    op.drop_table("story_turns")
    op.drop_table("story_sessions")
    op.drop_table("story_templates")

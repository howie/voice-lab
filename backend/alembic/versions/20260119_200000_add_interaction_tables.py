"""Add interaction module tables (sessions, turns, latency_metrics, templates)

Revision ID: 20260119_200000
Revises: 20260118_100000
Create Date: 2026-01-19 20:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260119_200000"
down_revision: str | None = "20260118_100000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create interaction_mode enum
    interaction_mode_enum = postgresql.ENUM(
        "realtime", "cascade", name="interaction_mode", create_type=False
    )
    interaction_mode_enum.create(op.get_bind(), checkfirst=True)

    # Create session_status enum
    session_status_enum = postgresql.ENUM(
        "active", "completed", "disconnected", "error", name="session_status", create_type=False
    )
    session_status_enum.create(op.get_bind(), checkfirst=True)

    # T002: Create interaction_sessions table
    op.create_table(
        "interaction_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "mode",
            postgresql.ENUM("realtime", "cascade", name="interaction_mode", create_type=False),
            nullable=False,
        ),
        sa.Column("provider_config", postgresql.JSONB, nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "completed", "disconnected", "error",
                name="session_status", create_type=False
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_session_user_id", "interaction_sessions", ["user_id"])
    op.create_index("idx_session_status", "interaction_sessions", ["status"])
    op.create_index(
        "idx_session_started_at", "interaction_sessions", [sa.text("started_at DESC")]
    )

    # T003: Create conversation_turns table
    op.create_table(
        "conversation_turns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_number", sa.Integer, nullable=False),
        sa.Column("user_audio_path", sa.String(500), nullable=True),
        sa.Column("user_transcript", sa.Text, nullable=True),
        sa.Column("ai_response_text", sa.Text, nullable=True),
        sa.Column("ai_audio_path", sa.String(500), nullable=True),
        sa.Column("interrupted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["interaction_sessions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("session_id", "turn_number", name="uq_turn_session_number"),
    )
    op.create_index("idx_turn_session_id", "conversation_turns", ["session_id"])
    op.create_index(
        "idx_turn_session_number", "conversation_turns", ["session_id", "turn_number"]
    )

    # T004: Create latency_metrics table
    op.create_table(
        "latency_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("total_latency_ms", sa.Integer, nullable=False),
        sa.Column("stt_latency_ms", sa.Integer, nullable=True),
        sa.Column("llm_ttft_ms", sa.Integer, nullable=True),
        sa.Column("tts_ttfb_ms", sa.Integer, nullable=True),
        sa.Column("realtime_latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["turn_id"], ["conversation_turns.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("idx_latency_turn_id", "latency_metrics", ["turn_id"])

    # T005: Create system_prompt_templates table
    op.create_table(
        "system_prompt_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("prompt_content", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_template_category", "system_prompt_templates", ["category"])
    op.create_index(
        "idx_template_is_default",
        "system_prompt_templates",
        ["is_default"],
        postgresql_where=sa.text("is_default = true"),
    )

    # Insert default templates
    op.execute("""
        INSERT INTO system_prompt_templates (name, description, prompt_content, category, is_default)
        VALUES
        ('客服機器人', '專業友善的客戶服務代表', '你是一位專業且友善的客戶服務代表。請用禮貌、清晰的方式回答客戶的問題，並在需要時提供進一步的協助。', 'customer_service', true),
        ('語言教師', '耐心的語言學習助教', '你是一位耐心的語言學習助教。請用簡單易懂的方式教導學生，並在學生犯錯時給予鼓勵性的糾正。', 'education', false),
        ('技術支援', 'IT 技術問題解答專家', '你是一位專業的 IT 技術支援專家。請用清晰、步驟化的方式幫助使用者解決技術問題，並在需要時詢問更多細節。', 'technical', false),
        ('一般助理', '通用對話助理', '你是一位通用對話助理。請用自然、友善的方式與使用者對話，並盡力回答各種問題。', 'general', false)
    """)


def downgrade() -> None:
    op.drop_table("system_prompt_templates")
    op.drop_table("latency_metrics")
    op.drop_table("conversation_turns")
    op.drop_table("interaction_sessions")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS session_status")
    op.execute("DROP TYPE IF EXISTS interaction_mode")

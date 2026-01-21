"""Add scenario_templates table with role/context configuration

Feature: 004-interaction-module
T070 [US4]: Create scenario_templates table and seed default templates

Revision ID: 20260121_100000
Revises: 20260119_200000
Create Date: 2026-01-21 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260121_100000"
down_revision: str | None = "20260119_200000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create scenario_templates table
    op.create_table(
        "scenario_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("user_role", sa.String(100), nullable=False),
        sa.Column("ai_role", sa.String(100), nullable=False),
        sa.Column("scenario_context", sa.Text, nullable=False),
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
    op.create_index("idx_scenario_template_category", "scenario_templates", ["category"])
    op.create_index("idx_scenario_template_is_default", "scenario_templates", ["is_default"])

    # Insert default scenario templates
    op.execute("""
        INSERT INTO scenario_templates (name, description, user_role, ai_role, scenario_context, category, is_default)
        VALUES
        (
            '客服諮詢',
            '模擬客戶服務場景，適合練習客服對話',
            '顧客',
            '客服專員',
            '你正在處理一位顧客的諮詢。請用專業且友善的態度回應，協助解決問題並確保顧客滿意。',
            'customer_service',
            true
        ),
        (
            '醫療諮詢',
            '模擬醫療諮詢場景，適合練習醫病溝通',
            '病患',
            '醫療助理',
            '你是一位醫療助理，正在協助病患了解基本健康資訊。請用淺顯易懂的方式說明，並在需要時建議就醫。注意：你不能提供醫療診斷或處方建議。',
            'medical',
            true
        ),
        (
            '語言教學',
            '模擬語言學習場景，適合練習外語對話',
            '學生',
            '語言老師',
            '你是一位耐心的語言老師。請用清楚的發音和簡單的句子與學生對話，並在學生犯錯時給予鼓勵性的糾正和解釋。',
            'education',
            true
        ),
        (
            '技術支援',
            '模擬 IT 技術支援場景',
            '用戶',
            '技術工程師',
            '你是一位專業的技術支援工程師。請有耐心地詢問問題細節，並用步驟化的方式指導用戶解決技術問題。',
            'technical',
            true
        ),
        (
            '一般對話',
            '通用對話場景，適合自由練習',
            '使用者',
            'AI 助理',
            '你是一位友善的 AI 助理。請用自然、親切的方式與使用者對話，回答各種問題並提供協助。',
            'general',
            true
        )
    """)


def downgrade() -> None:
    op.drop_index("idx_scenario_template_is_default", "scenario_templates")
    op.drop_index("idx_scenario_template_category", "scenario_templates")
    op.drop_table("scenario_templates")

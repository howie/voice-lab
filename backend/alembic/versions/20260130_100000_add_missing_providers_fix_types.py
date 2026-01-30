"""Add missing providers and fix provider types

Adds providers: openai, anthropic, gcp, voai, speechmatics
Fixes: gemini type (remove stt, add llm), azure type (add llm)

Revision ID: 20260130_100000
Revises: 20260129_110000, 37230f605b1b, 96b1d21df7c8
Create Date: 2026-01-30 10:00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260130_100000"
down_revision: tuple[str, ...] = ("20260129_110000", "37230f605b1b", "96b1d21df7c8")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Insert missing providers
    op.execute(
        """
        INSERT INTO providers (id, name, display_name, type, is_active)
        VALUES
            ('openai', 'openai', 'OpenAI', ARRAY['stt', 'llm'], true),
            ('anthropic', 'anthropic', 'Anthropic', ARRAY['llm'], true),
            ('gcp', 'gcp', 'Google Cloud Platform', ARRAY['tts', 'stt'], true),
            ('voai', 'voai', 'VoAI', ARRAY['tts'], true),
            ('speechmatics', 'speechmatics', 'Speechmatics', ARRAY['stt'], true)
        ON CONFLICT (id) DO NOTHING
        """
    )

    # 2. Fix gemini type: remove stt, add llm
    op.execute(
        """
        UPDATE providers
        SET type = ARRAY['tts', 'llm']
        WHERE id = 'gemini'
        """
    )

    # 3. Fix azure type: add llm
    op.execute(
        """
        UPDATE providers
        SET type = ARRAY['tts', 'stt', 'llm']
        WHERE id = 'azure'
        """
    )


def downgrade() -> None:
    # Revert azure type
    op.execute(
        """
        UPDATE providers
        SET type = ARRAY['tts', 'stt']
        WHERE id = 'azure'
        """
    )

    # Revert gemini type
    op.execute(
        """
        UPDATE providers
        SET type = ARRAY['tts', 'stt']
        WHERE id = 'gemini'
        """
    )

    # Remove added providers
    op.execute(
        """
        DELETE FROM providers
        WHERE id IN ('openai', 'anthropic', 'gcp', 'voai', 'speechmatics')
        """
    )

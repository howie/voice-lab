"""Add provider credential management tables (providers, user_provider_credentials, audit_logs)

Revision ID: 20260118_100000
Revises: 20260116_222743
Create Date: 2026-01-18 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260118_100000"
down_revision: str | None = "20260116_222743"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create providers table (reference data)
    op.create_table(
        "providers",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column(
            "type",
            postgresql.ARRAY(sa.String(20)),
            nullable=False,
        ),
        sa.Column(
            "supported_models",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed provider reference data
    op.execute(
        """
        INSERT INTO providers (id, name, display_name, type, is_active)
        VALUES
            ('elevenlabs', 'elevenlabs', 'ElevenLabs', ARRAY['tts'], true),
            ('azure', 'azure', 'Azure Cognitive Services', ARRAY['tts', 'stt'], true),
            ('gemini', 'gemini', 'Google Gemini', ARRAY['tts', 'stt'], true)
        """
    )

    # Create user_provider_credentials table
    op.create_table(
        "user_provider_credentials",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("selected_model_id", sa.String(128), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["provider"],
            ["providers.id"],
        ),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider_credential"),
    )
    op.create_index(
        "idx_credentials_user_id", "user_provider_credentials", ["user_id"]
    )
    op.create_index(
        "idx_credentials_provider", "user_provider_credentials", ["provider"]
    )
    op.create_index(
        "idx_credentials_user_provider",
        "user_provider_credentials",
        ["user_id", "provider"],
    )

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_audit_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_event_type", "audit_logs", ["event_type"])
    op.create_index("idx_audit_timestamp", "audit_logs", ["timestamp"])
    op.create_index("idx_audit_provider", "audit_logs", ["provider"])


def downgrade() -> None:
    # Drop audit_logs table
    op.drop_index("idx_audit_provider", table_name="audit_logs")
    op.drop_index("idx_audit_timestamp", table_name="audit_logs")
    op.drop_index("idx_audit_event_type", table_name="audit_logs")
    op.drop_index("idx_audit_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    # Drop user_provider_credentials table
    op.drop_index("idx_credentials_user_provider", table_name="user_provider_credentials")
    op.drop_index("idx_credentials_provider", table_name="user_provider_credentials")
    op.drop_index("idx_credentials_user_id", table_name="user_provider_credentials")
    op.drop_table("user_provider_credentials")

    # Drop providers table
    op.drop_table("providers")

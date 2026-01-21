"""Add jobs table for async job management

Revision ID: 20260120_100000
Revises: 477f0ffdd804
Create Date: 2026-01-20 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260120_100000"
down_revision: str | None = "477f0ffdd804"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create job_status enum
    job_status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        "cancelled",
        name="job_status",
        create_type=False,
    )
    job_status_enum.create(op.get_bind(), checkfirst=True)

    # Create job_type enum
    job_type_enum = postgresql.ENUM(
        "multi_role_tts",
        name="job_type",
        create_type=False,
    )
    job_type_enum.create(op.get_bind(), checkfirst=True)

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_type",
            postgresql.ENUM("multi_role_tts", name="job_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "processing",
                "completed",
                "failed",
                "cancelled",
                name="job_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("input_params", postgresql.JSONB, nullable=False),
        sa.Column("audio_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_metadata", postgresql.JSONB, nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["audio_file_id"], ["audio_files.id"], ondelete="SET NULL"),
    )

    # Create indexes for common queries
    op.create_index("idx_jobs_user_status", "jobs", ["user_id", "status"])
    op.create_index("idx_jobs_created_at", "jobs", [sa.text("created_at DESC")])

    # Create partial indexes for background tasks
    op.create_index(
        "idx_jobs_pending",
        "jobs",
        ["status", "created_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "idx_jobs_processing_timeout",
        "jobs",
        ["status", "started_at"],
        postgresql_where=sa.text("status = 'processing'"),
    )

    # Create partial index for cleanup tasks
    op.create_index(
        "idx_jobs_completed_cleanup",
        "jobs",
        ["status", "completed_at"],
        postgresql_where=sa.text("status IN ('completed', 'failed', 'cancelled')"),
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_jobs_completed_cleanup", table_name="jobs")
    op.drop_index("idx_jobs_processing_timeout", table_name="jobs")
    op.drop_index("idx_jobs_pending", table_name="jobs")
    op.drop_index("idx_jobs_created_at", table_name="jobs")
    op.drop_index("idx_jobs_user_status", table_name="jobs")

    # Drop table
    op.drop_table("jobs")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS job_type")
    op.execute("DROP TYPE IF EXISTS job_status")

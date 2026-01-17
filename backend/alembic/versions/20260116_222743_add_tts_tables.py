"""Add TTS tables (users, synthesis_logs, voice_cache)

Revision ID: 20260116_222743
Revises:
Create Date: 2026-01-16 22:27:43

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260116_222743'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('google_id', sa.String(128), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('picture_url', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_google_id', 'users', ['google_id'])
    op.create_index('idx_users_email', 'users', ['email'])

    # Create synthesis_logs table
    op.create_table(
        'synthesis_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('text_hash', sa.String(64), nullable=False),
        sa.Column('text_preview', sa.String(100), nullable=True),
        sa.Column('characters_count', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('voice_id', sa.String(128), nullable=False),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('speed', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('output_format', sa.String(10), nullable=True, server_default="'mp3'"),
        sa.Column('output_mode', sa.String(16), nullable=True, server_default="'batch'"),
        sa.Column('storage_path', sa.String(512), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cost_estimate', sa.DECIMAL(10, 6), nullable=True),
        sa.Column('client_ip', sa.String(50), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('idx_synthesis_logs_provider', 'synthesis_logs', ['provider'])
    op.create_index('idx_synthesis_logs_status', 'synthesis_logs', ['status'])
    op.create_index('idx_synthesis_logs_created_at', 'synthesis_logs', ['created_at'])
    op.create_index('idx_synthesis_logs_text_hash', 'synthesis_logs', ['text_hash'])
    op.create_index('idx_synthesis_logs_user_id', 'synthesis_logs', ['user_id'])

    # Create voice_cache table
    op.create_table(
        'voice_cache',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('voice_id', sa.String(128), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('styles', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_voice_cache_provider', 'voice_cache', ['provider'])
    op.create_index('idx_voice_cache_language', 'voice_cache', ['language'])


def downgrade() -> None:
    op.drop_index('idx_voice_cache_language', table_name='voice_cache')
    op.drop_index('idx_voice_cache_provider', table_name='voice_cache')
    op.drop_table('voice_cache')

    op.drop_index('idx_synthesis_logs_user_id', table_name='synthesis_logs')
    op.drop_index('idx_synthesis_logs_text_hash', table_name='synthesis_logs')
    op.drop_index('idx_synthesis_logs_created_at', table_name='synthesis_logs')
    op.drop_index('idx_synthesis_logs_status', table_name='synthesis_logs')
    op.drop_index('idx_synthesis_logs_provider', table_name='synthesis_logs')
    op.drop_table('synthesis_logs')

    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_google_id', table_name='users')
    op.drop_table('users')

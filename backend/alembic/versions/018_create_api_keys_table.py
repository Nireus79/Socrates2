"""create api_keys table

Revision ID: 018
Revises: 017
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_auth database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url


def upgrade():
    """Create api_keys table"""
    if not _should_run():
        return

    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Primary key (UUID)'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to users table'),
        sa.Column('provider', sa.String(length=50), nullable=False, comment='LLM provider: claude, openai, gemini, ollama, other'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False, comment='Encrypted API key (AES-256)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether API key is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when API key was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when API key was last updated'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when API key was last used'),
        sa.CheckConstraint("provider IN ('claude', 'openai', 'gemini', 'ollama', 'other')", name='api_keys_provider_valid'),
        sa.UniqueConstraint('user_id', 'provider', name='api_keys_user_provider_unique')
    )

    # Create indexes
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_provider', 'api_keys', ['provider'])
    op.create_index('idx_api_keys_is_active', 'api_keys', ['is_active'], postgresql_where=sa.text('is_active = true'))


def downgrade():
    """Drop api_keys table"""
    if not _should_run():
        return

    op.drop_index('idx_api_keys_is_active', table_name='api_keys')
    op.drop_index('idx_api_keys_provider', table_name='api_keys')
    op.drop_index('idx_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')

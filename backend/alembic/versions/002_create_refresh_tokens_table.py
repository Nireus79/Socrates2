"""Create refresh_tokens table

Revision ID: 002
Revises: 001
Create Date: 2025-11-05

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_auth database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url


def upgrade():
    if not _should_run():
        return

    op.create_table(
        'refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key to users in socrates_auth database
    op.create_foreign_key(
        'fk_refresh_tokens_user_id',
        'refresh_tokens', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_token', 'refresh_tokens', ['token'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])


def downgrade():
    if not _should_run():
        return

    op.drop_index('idx_refresh_tokens_expires_at')
    op.drop_index('idx_refresh_tokens_token')
    op.drop_index('idx_refresh_tokens_user_id')
    op.drop_constraint('fk_refresh_tokens_user_id', 'refresh_tokens', type_='foreignkey')
    op.drop_table('refresh_tokens')

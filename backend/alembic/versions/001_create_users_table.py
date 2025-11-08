"""Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-05

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '001'
down_revision = None
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
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('surname', sa.String(100), nullable=False),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_status', 'users', ['status'])


def downgrade():
    if not _should_run():
        return

    op.drop_index('idx_users_status')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_users_email')
    op.drop_table('users')

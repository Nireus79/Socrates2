"""Create sessions table

Revision ID: 004
Revises: 003
Create Date: 2025-11-05

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    if not _should_run():
        return

    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False, server_default='socratic'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key to projects
    op.create_foreign_key(
        'fk_sessions_project_id',
        'sessions', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index('idx_sessions_project_id', 'sessions', ['project_id'])
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_mode', 'sessions', ['mode'])


def downgrade():
    if not _should_run():
        return

    op.drop_index('idx_sessions_mode')
    op.drop_index('idx_sessions_status')
    op.drop_index('idx_sessions_project_id')
    op.drop_constraint('fk_sessions_project_id', 'sessions', type_='foreignkey')
    op.drop_table('sessions')

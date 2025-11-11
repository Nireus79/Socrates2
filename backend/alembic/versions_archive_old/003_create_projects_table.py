"""Create projects table

Revision ID: 003
Revises: 002
Create Date: 2025-11-05

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '003'
down_revision = '002'
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
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('current_phase', sa.String(50), nullable=False, server_default='discovery'),
        sa.Column('maturity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('idx_projects_user_id', 'projects', ['user_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_current_phase', 'projects', ['current_phase'])
    op.create_index('idx_projects_maturity_score', 'projects', ['maturity_score'])

    # Add check constraint for maturity_score
    op.create_check_constraint(
        'check_projects_maturity_score',
        'projects',
        'maturity_score >= 0 AND maturity_score <= 100'
    )


def downgrade():
    if not _should_run():
        return

    op.drop_constraint('check_projects_maturity_score', 'projects', type_='check')
    op.drop_index('idx_projects_maturity_score')
    op.drop_index('idx_projects_current_phase')
    op.drop_index('idx_projects_status')
    op.drop_index('idx_projects_user_id')
    op.drop_table('projects')

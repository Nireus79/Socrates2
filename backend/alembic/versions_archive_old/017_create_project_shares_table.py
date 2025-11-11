"""create project_shares table

Revision ID: 017
Revises: 016
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create project_shares table"""
    if not _should_run():
        return

    op.create_table(
        'project_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to projects table'),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False, comment='References teams.id in socrates_auth database'),
        sa.Column('shared_by', postgresql.UUID(as_uuid=True), nullable=False, comment='References users.id in socrates_auth database'),
        sa.Column('permission_level', sa.String(length=20), nullable=False, comment='Permission level: read, write, admin'),
        sa.Column('shared_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when project was shared'),
        sa.CheckConstraint("permission_level IN ('read', 'write', 'admin')", name='project_shares_permission_valid'),
        sa.UniqueConstraint('project_id', 'team_id', name='project_shares_unique')
    )

    # Create indexes
    op.create_index('idx_project_shares_project_id', 'project_shares', ['project_id'])
    op.create_index('idx_project_shares_team_id', 'project_shares', ['team_id'])
    op.create_index('idx_project_shares_permission', 'project_shares', ['permission_level'])


def downgrade():
    """Drop project_shares table"""
    if not _should_run():
        return

    op.drop_index('idx_project_shares_permission', table_name='project_shares')
    op.drop_index('idx_project_shares_team_id', table_name='project_shares')
    op.drop_index('idx_project_shares_project_id', table_name='project_shares')
    op.drop_table('project_shares')

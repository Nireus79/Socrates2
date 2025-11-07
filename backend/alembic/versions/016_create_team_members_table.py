"""create team_members table

Revision ID: 016
Revises: 015
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create team_members table"""
    if not _should_run():
        return

    op.create_table(
        'team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to teams table'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to users table'),
        sa.Column('role', sa.String(length=50), nullable=False, comment='Member role: owner, lead, developer, viewer'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when member joined the team'),
        sa.CheckConstraint("role IN ('owner', 'lead', 'developer', 'viewer')", name='team_members_role_valid'),
        sa.UniqueConstraint('team_id', 'user_id', name='team_members_unique')
    )

    # Create indexes
    op.create_index('idx_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('idx_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('idx_team_members_role', 'team_members', ['role'])


def downgrade():
    """Drop team_members table"""
    if not _should_run():
        return

    op.drop_index('idx_team_members_role', table_name='team_members')
    op.drop_index('idx_team_members_user_id', table_name='team_members')
    op.drop_index('idx_team_members_team_id', table_name='team_members')
    op.drop_table('team_members')

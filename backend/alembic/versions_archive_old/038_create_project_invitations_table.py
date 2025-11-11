"""Create project invitations table for team collaboration.

Revision ID: 038_create_project_invitations_table
Revises: 037_create_activity_logs_table
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '038'
down_revision = '037'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade() -> None:
    """Create project_invitations table in specs database."""
    if not _should_run():
        return

    # Create enum type for invitation status
    status_enum = postgresql.ENUM(
        'pending', 'accepted', 'declined', 'expired', 'revoked',
        name='invitationstatus'
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    # Create project_invitations table
    op.create_table(
        'project_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=False),
        sa.Column('invited_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='editor'),
        sa.Column('status', status_enum, nullable=False, server_default='pending'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.String(50), nullable=True),
        sa.Column('accepted_at', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_project_invitations_project_id', 'project_invitations', ['project_id'])
    op.create_index('ix_project_invitations_invited_email', 'project_invitations', ['invited_email'])
    op.create_index('ix_project_invitations_invited_user_id', 'project_invitations', ['invited_user_id'])
    op.create_index('ix_project_invitations_status', 'project_invitations', ['status'])
    op.create_index('ix_project_invitations_created_at', 'project_invitations', ['created_at'])


def downgrade() -> None:
    """Drop project_invitations table."""
    if not _should_run():
        return

    op.drop_index('ix_project_invitations_created_at', table_name='project_invitations')
    op.drop_index('ix_project_invitations_status', table_name='project_invitations')
    op.drop_index('ix_project_invitations_invited_user_id', table_name='project_invitations')
    op.drop_index('ix_project_invitations_invited_email', table_name='project_invitations')
    op.drop_index('ix_project_invitations_project_id', table_name='project_invitations')
    op.drop_table('project_invitations')

    # Drop enum type
    op.execute("DROP TYPE invitationstatus")

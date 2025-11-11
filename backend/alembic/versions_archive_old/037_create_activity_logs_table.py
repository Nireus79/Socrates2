"""Create activity logs table for tracking user actions on projects.

Revision ID: 037_create_activity_logs_table
Revises: 036_create_notification_preferences_table
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade() -> None:
    """Create activity_logs table in specs database."""
    if not _should_run():
        return

    # Create activity_logs table for tracking user actions
    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_activity_logs_project_id', 'activity_logs', ['project_id'])
    op.create_index('ix_activity_logs_user_id', 'activity_logs', ['user_id'])
    op.create_index('ix_activity_logs_action_type', 'activity_logs', ['action_type'])
    op.create_index('ix_activity_logs_entity_type', 'activity_logs', ['entity_type'])
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'])
    op.create_index('ix_activity_logs_project_created', 'activity_logs', ['project_id', 'created_at'])


def downgrade() -> None:
    """Drop activity_logs table."""
    if not _should_run():
        return

    op.drop_index('ix_activity_logs_project_created', table_name='activity_logs')
    op.drop_index('ix_activity_logs_created_at', table_name='activity_logs')
    op.drop_index('ix_activity_logs_entity_type', table_name='activity_logs')
    op.drop_index('ix_activity_logs_action_type', table_name='activity_logs')
    op.drop_index('ix_activity_logs_user_id', table_name='activity_logs')
    op.drop_index('ix_activity_logs_project_id', table_name='activity_logs')
    op.drop_table('activity_logs')

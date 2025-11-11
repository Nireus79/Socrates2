"""Create notification preferences table for user notification settings.

Revision ID: 036_create_notification_preferences_table
Revises: 035_create_document_chunks_table
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '036'
down_revision = '035'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_auth database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url


def upgrade() -> None:
    """Create notification_preferences table in auth database."""
    if not _should_run():
        return

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('email_on_conflict', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_on_maturity', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_on_mention', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_on_activity', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('digest_frequency', sa.String(20), nullable=False, server_default='daily'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_notification_preferences_user_id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])


def downgrade() -> None:
    """Drop notification_preferences table."""
    if not _should_run():
        return

    op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')
    op.drop_table('notification_preferences')

"""Add project ownership tracking (creator_id, owner_id, collaborators).

Revision ID: 021
Revises: 020
Create Date: 2025-11-08 12:00:00.000000

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade() -> None:
    """Add project ownership fields and collaborator tracking."""
    if not _should_run():
        return
    # Add creator_id and owner_id to projects table
    op.add_column('projects', sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False, server_default='00000000-0000-0000-0000-000000000000'))
    op.add_column('projects', sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False, server_default='00000000-0000-0000-0000-000000000000'))

    # Create indexes
    op.create_index('idx_projects_creator_id', 'projects', ['creator_id'])
    op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])

    # Create collaborators table
    op.create_table(
        'project_collaborators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='viewer'),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_collaborators'),
        sa.Index('idx_project_collaborators_project_id', 'project_id'),
        sa.Index('idx_project_collaborators_user_id', 'user_id'),
    )

    # Create ownership history table for audit trail
    op.create_table(
        'project_ownership_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transferred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('transferred_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Index('idx_project_ownership_history_project_id', 'project_id'),
    )


def downgrade() -> None:
    """Revert changes."""
    if not _should_run():
        return
    # Drop tables
    op.drop_table('project_ownership_history')
    op.drop_table('project_collaborators')

    # Drop indexes
    op.drop_index('idx_projects_owner_id', table_name='projects')
    op.drop_index('idx_projects_creator_id', table_name='projects')

    # Drop columns
    op.drop_column('projects', 'owner_id')
    op.drop_column('projects', 'creator_id')

"""Fix Projects table schema - rename and add columns

Revision ID: 011
Revises: 009
Create Date: 2025-11-13

This migration fixes schema mismatches in the projects table:

Current Database Schema:
- phase → needs to be current_phase
- maturity_level → needs to be maturity_score
- Missing: creator_id (for audit trail)
- Missing: owner_id (for project ownership)

The Project model expects these columns but the migration that created
the table used different names, causing create operations to fail.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix projects table schema to match Project model"""

    # Rename phase to current_phase first
    op.alter_column('projects', 'phase', new_column_name='current_phase')

    # Rename maturity_level to maturity_score
    op.alter_column('projects', 'maturity_level', new_column_name='maturity_score')

    # Add creator_id column as nullable first
    op.add_column(
        'projects',
        sa.Column(
            'creator_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='UUID of user who created the project (immutable, audit trail)'
        )
    )

    # Add owner_id column as nullable first
    op.add_column(
        'projects',
        sa.Column(
            'owner_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='UUID of current project owner (transferable)'
        )
    )

    # Update existing rows: copy user_id to creator_id and owner_id
    op.execute(
        sa.text('UPDATE projects SET creator_id = user_id, owner_id = user_id WHERE creator_id IS NULL')
    )

    # Make the columns NOT NULL now that they have values
    op.alter_column('projects', 'creator_id', nullable=False)
    op.alter_column('projects', 'owner_id', nullable=False)

    # Create indexes for the new columns
    op.create_index('idx_projects_creator_id', 'projects', ['creator_id'])
    op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('idx_projects_current_phase', 'projects', ['current_phase'])
    op.create_index('idx_projects_maturity_score', 'projects', ['maturity_score'])


def downgrade() -> None:
    """Revert projects table schema changes"""

    # Drop indexes
    op.drop_index('idx_projects_current_phase', table_name='projects')
    op.drop_index('idx_projects_maturity_score', table_name='projects')
    op.drop_index('idx_projects_owner_id', table_name='projects')
    op.drop_index('idx_projects_creator_id', table_name='projects')

    # Rename columns back
    op.alter_column('projects', 'current_phase', new_column_name='phase')
    op.alter_column('projects', 'maturity_score', new_column_name='maturity_level')

    # Drop the new columns
    op.drop_column('projects', 'owner_id')
    op.drop_column('projects', 'creator_id')

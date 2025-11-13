"""Add mode column to sessions table.

Revision ID: 012_add_mode_to_sessions
Revises: 011_specs_fix_projects_schema
Create Date: 2025-11-13

This migration adds the 'mode' column to the sessions table to support
different conversation modes: 'socratic' (default) and 'direct_chat'.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add mode column to sessions table."""
    # Add mode column to sessions table
    op.add_column(
        'sessions',
        sa.Column(
            'mode',
            sa.String(20),
            nullable=False,
            server_default='socratic',
            comment='Chat mode: socratic, direct_chat'
        ),
        schema=None
    )


def downgrade() -> None:
    """Remove mode column from sessions table."""
    op.drop_column('sessions', 'mode', schema=None)

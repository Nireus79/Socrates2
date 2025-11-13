"""Add started_at and ended_at columns to sessions table.

Revision ID: 013
Revises: 012
Create Date: 2025-11-13

This migration adds timestamp columns to the sessions table for session lifecycle tracking.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add timestamp columns to sessions table."""
    # Add started_at column
    op.add_column(
        'sessions',
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='When the session started'
        ),
        schema=None
    )

    # Add ended_at column
    op.add_column(
        'sessions',
        sa.Column(
            'ended_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the session ended (NULL if still active)'
        ),
        schema=None
    )


def downgrade() -> None:
    """Remove timestamp columns from sessions table."""
    op.drop_column('sessions', 'ended_at', schema=None)
    op.drop_column('sessions', 'started_at', schema=None)

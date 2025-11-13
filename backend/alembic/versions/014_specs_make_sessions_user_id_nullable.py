"""Make user_id nullable in sessions table.

Revision ID: 014
Revises: 013
Create Date: 2025-11-13

This migration makes user_id nullable in the sessions table since user
ownership is tracked through the project relationship, not directly on sessions.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make user_id nullable."""
    op.alter_column(
        'sessions',
        'user_id',
        existing_type=sa.UUID(),
        nullable=True
    )


def downgrade() -> None:
    """Revert user_id to non-nullable."""
    op.alter_column(
        'sessions',
        'user_id',
        existing_type=sa.UUID(),
        nullable=False
    )

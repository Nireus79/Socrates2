"""Add updated_at column to refresh_tokens table

Revision ID: 010
Revises: 002
Create Date: 2025-11-13

This migration fixes a schema mismatch where the RefreshToken SQLAlchemy model
inherits updated_at from BaseModel, but the migration that created the
refresh_tokens table didn't include this column.

The error occurred during login when trying to insert and return the updated_at column.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '002'
branch_labels = None  # Only the first migration in a branch has branch_labels
depends_on = None


def upgrade() -> None:
    """Add updated_at column to refresh_tokens table"""

    # Add updated_at column to refresh_tokens
    op.add_column(
        'refresh_tokens',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Timestamp when token was last updated'
        )
    )

    # Add index for updated_at (useful for queries about recent updates)
    op.create_index('ix_refresh_tokens_updated_at', 'refresh_tokens', ['updated_at'])


def downgrade() -> None:
    """Remove updated_at column from refresh_tokens table"""

    # Drop the index
    op.drop_index('ix_refresh_tokens_updated_at', table_name='refresh_tokens')

    # Drop the column
    op.drop_column('refresh_tokens', 'updated_at')

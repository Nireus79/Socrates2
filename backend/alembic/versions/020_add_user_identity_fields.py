"""Add user identity fields (name, surname, username) and make email optional.

Revision ID: 020
Revises: 019
Create Date: 2025-11-08 12:00:00.000000

"""
import os
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_auth database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url


def upgrade() -> None:
    """Add name, surname, username columns and make email optional."""
    if not _should_run():
        return
    # First, make email optional (drop NOT NULL constraint)
    op.alter_column('users', 'email',
                    existing_type=sa.String(255),
                    nullable=True)

    # Add new columns as nullable first (for existing rows)
    # We'll make them NOT NULL in the application code/model
    op.add_column('users', sa.Column('name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('surname', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('username', sa.String(50), nullable=True))

    # Add index on username for faster lookups
    op.create_index('idx_users_username', 'users', ['username'])

    # Create unique constraint on username (works on nullable columns)
    op.create_unique_constraint('uq_users_username', 'users', ['username'])


def downgrade() -> None:
    """Revert changes."""
    if not _should_run():
        return
    # Drop index
    op.drop_index('idx_users_username', table_name='users')

    # Drop unique constraint
    op.drop_constraint('uq_users_username', 'users', type_='unique')

    # Drop columns
    op.drop_column('users', 'username')
    op.drop_column('users', 'surname')
    op.drop_column('users', 'name')

    # Restore email NOT NULL constraint
    op.alter_column('users', 'email',
                    existing_type=sa.String(255),
                    nullable=False)

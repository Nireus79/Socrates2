"""Add context column to questions table.

Revision ID: 015
Revises: 014_specs_make_sessions_user_id_nullable
Create Date: 2025-11-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add context column to questions table
    op.add_column('questions', sa.Column('context', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove context column from questions table
    op.drop_column('questions', 'context')

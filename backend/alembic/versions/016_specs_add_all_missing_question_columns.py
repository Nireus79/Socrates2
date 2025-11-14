"""Add all missing columns to questions table - comprehensive schema fix.

Revision ID: 016
Revises: 015
Create Date: 2025-11-14

This migration adds ALL columns that the Question model expects but are missing
from the database schema. This is a comprehensive fix to resolve cascade delete
errors when deleting projects.

Missing columns being added:
- context: Text, nullable (explanation of why question matters)
- quality_score: Numeric(3,2), default 1.0 (quality score 0.00-1.00)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if context column already exists and add if missing
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('questions')]

    if 'context' not in columns:
        op.add_column('questions', sa.Column('context', sa.Text(), nullable=True))

    if 'quality_score' not in columns:
        op.add_column('questions', sa.Column(
            'quality_score',
            sa.Numeric(precision=3, scale=2),
            nullable=False,
            server_default='1.0'
        ))


def downgrade() -> None:
    # Remove columns if they exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('questions')]

    if 'quality_score' in columns:
        op.drop_column('questions', 'quality_score')

    if 'context' in columns:
        op.drop_column('questions', 'context')

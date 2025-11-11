"""Add key and value columns to specifications table.

Revision ID: 023_add_key_value_to_specifications
Revises: 022_add_performance_indexes
Create Date: 2025-11-10

This migration adds the key and value columns to the specifications table,
enabling structured specification storage that aligns with the socrates-ai
library format.

Key/Value Structure:
- key: Identifier for the specification (e.g., "api_framework")
- value: The actual specification value (e.g., "FastAPI")
- content: Preserved for complex notes/context (optional)

Columns are added as nullable initially. After data migration, they will be
made required via migration 024.

Schema Changes:
- ADD COLUMN key VARCHAR(255) NULL
- ADD COLUMN value TEXT NULL
- ADD INDEX idx_specifications_category_key ON specifications(project_id, category, key)
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None



def _should_run():
    """Only run this migration for socrates_specs database"""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url

def upgrade() -> None:
    """
    Upgrade: Add key and value columns to specifications table.
    """
    if not _should_run():
        return

    # Add key column (VARCHAR 255, nullable for now)
    op.add_column(
        'specifications',
        sa.Column(
            'key',
            sa.String(255),
            nullable=True,
            comment='Specification identifier (e.g., "api_framework")'
        )
    )

    # Add value column (TEXT, nullable for now)
    op.add_column(
        'specifications',
        sa.Column(
            'value',
            sa.Text,
            nullable=True,
            comment='Specification value (e.g., "FastAPI")'
        )
    )

    # Create index for efficient queries by category and key
    op.create_index(
        'idx_specifications_category_key',
        'specifications',
        ['project_id', 'category', 'key'],
        postgresql_where=sa.text('is_current = true'),
        if_not_exists=True
    )


def downgrade() -> None:
    """
    Downgrade: Remove key and value columns from specifications table.
    """
    if not _should_run():
        return

    # Drop index
    op.drop_index(
        'idx_specifications_category_key',
        table_name='specifications',
        if_exists=True
    )

    # Drop columns
    op.drop_column('specifications', 'key')
    op.drop_column('specifications', 'value')

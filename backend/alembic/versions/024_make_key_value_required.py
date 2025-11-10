"""Make key and value columns required in specifications table.

Revision ID: 024_make_key_value_required
Revises: 023_add_key_value_to_specifications
Create Date: 2025-11-10

IMPORTANT: This migration should only be run AFTER the data migration script
(migrate_specifications_to_key_value.py) has successfully populated all key/value pairs.

This migration makes the key and value columns NOT NULL, enforcing that
all specifications have the required structured data.

Prerequisites:
- Migration 023 must be applied first
- Data migration script must be run successfully
- All specifications must have key and value populated

See: SPECIFICATION_KEY_VALUE_MIGRATION.md
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Make key and value columns NOT NULL.

    REQUIRES: All specifications must have key and value populated.
    """
    # Check if migration script has been run
    # This is a safety check - the script will verify this

    # Make key column required
    op.alter_column(
        'specifications',
        'key',
        existing_type=sa.String(255),
        nullable=False,
        existing_comment='Specification identifier (e.g., "api_framework")'
    )

    # Make value column required
    op.alter_column(
        'specifications',
        'value',
        existing_type=sa.Text,
        nullable=False,
        existing_comment='Specification value (e.g., "FastAPI")'
    )


def downgrade() -> None:
    """
    Downgrade: Make key and value columns nullable again.
    """
    # Make key column nullable
    op.alter_column(
        'specifications',
        'key',
        existing_type=sa.String(255),
        nullable=True,
        existing_comment='Specification identifier (e.g., "api_framework")'
    )

    # Make value column nullable
    op.alter_column(
        'specifications',
        'value',
        existing_type=sa.Text,
        nullable=True,
        existing_comment='Specification value (e.g., "FastAPI")'
    )

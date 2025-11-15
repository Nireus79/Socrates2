"""Add missing columns to specifications table

Revision ID: 017
Revises: 016
Create Date: 2025-11-15

This migration adds the missing category and content columns to the specifications table
that are required by the application models.

Tables modified:
- specifications: add category and content columns
"""

from alembic import op
import sqlalchemy as sa


revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to specifications table."""

    # Add category column
    op.add_column(
        'specifications',
        sa.Column(
            'category',
            sa.String(100),
            nullable=False,
            server_default='general',
            comment='Specification category (goals, requirements, design, etc.)'
        )
    )

    # Add content column
    op.add_column(
        'specifications',
        sa.Column(
            'content',
            sa.Text(),
            nullable=True,
            comment='Full specification content'
        )
    )

    # Add source column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'source',
            sa.String(100),
            nullable=True,
            comment='Source of specification (question, direct_input, extracted, etc.)'
        )
    )

    # Add confidence column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'confidence',
            sa.Float(),
            nullable=True,
            server_default='0.8',
            comment='Confidence score for extracted specifications (0-1)'
        )
    )

    # Add is_current column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'is_current',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment='Whether this is the current version of the specification'
        )
    )

    # Add spec_metadata column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'spec_metadata',
            sa.JSON(),
            nullable=True,
            comment='Additional specification metadata'
        )
    )

    # Add superseded_at column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'superseded_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When this specification was superseded'
        )
    )

    # Add superseded_by column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'superseded_by',
            sa.String(255),
            nullable=True,
            comment='ID of specification that superseded this one'
        )
    )

    # Add maturity_score column if it doesn't exist
    op.add_column(
        'specifications',
        sa.Column(
            'maturity_score',
            sa.Integer(),
            nullable=True,
            server_default='0',
            comment='Maturity score for this specification'
        )
    )

    # Create index on category
    op.create_index('ix_specifications_category', 'specifications', ['category'])

    # Create index on is_current
    op.create_index('ix_specifications_is_current', 'specifications', ['is_current'])


def downgrade() -> None:
    """Remove added columns from specifications table."""

    op.drop_index('ix_specifications_is_current', table_name='specifications')
    op.drop_index('ix_specifications_category', table_name='specifications')
    op.drop_column('specifications', 'maturity_score')
    op.drop_column('specifications', 'superseded_by')
    op.drop_column('specifications', 'superseded_at')
    op.drop_column('specifications', 'spec_metadata')
    op.drop_column('specifications', 'is_current')
    op.drop_column('specifications', 'confidence')
    op.drop_column('specifications', 'source')
    op.drop_column('specifications', 'content')
    op.drop_column('specifications', 'category')

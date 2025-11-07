"""create quality_metrics table

Revision ID: 008
Revises: 007
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create quality_metrics table"""
    if not _should_run():
        return

    op.create_table(
        'quality_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Primary key (UUID)'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to projects table'),
        sa.Column('metric_type', sa.String(length=100), nullable=False, comment='Type of metric (e.g., maturity, coverage, conflicts, bias)'),
        sa.Column('metric_value', sa.Numeric(10, 2), nullable=False, comment='Numeric value of the metric'),
        sa.Column('threshold', sa.Numeric(10, 2), nullable=True, comment='Threshold value for pass/fail determination'),
        sa.Column('passed', sa.Boolean(), nullable=False, comment='Whether the metric passed quality check'),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional details as JSON'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when metric was calculated'),
    )

    # Create indexes
    op.create_index('idx_quality_metrics_project_id', 'quality_metrics', ['project_id'])
    op.create_index('idx_quality_metrics_type', 'quality_metrics', ['metric_type'])
    op.create_index('idx_quality_metrics_calculated_at', 'quality_metrics', ['calculated_at'], postgresql_using='btree', postgresql_ops={'calculated_at': 'DESC'})


def downgrade():
    """Drop quality_metrics table"""
    if not _should_run():
        return

    op.drop_index('idx_quality_metrics_calculated_at', table_name='quality_metrics')
    op.drop_index('idx_quality_metrics_type', table_name='quality_metrics')
    op.drop_index('idx_quality_metrics_project_id', table_name='quality_metrics')
    op.drop_table('quality_metrics')

"""Add analytics tracking and aggregation tables.

Revision ID: 028
Revises: 027
Create Date: 2025-11-11 12:00:00.000000

This migration creates tables for analytics and metrics:
- analytics_events: User action tracking (raw events)
- project_metrics: Daily aggregated metrics per project (computed)

Enables Phase 1 Feature 3: Background Jobs & Analytics Aggregation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB


# revision identifiers, used by Alembic.
revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics tables."""

    # Create analytics_events table for raw event tracking
    op.create_table(
        'analytics_events',
        sa.Column(
            'id',
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=sa.text('gen_random_uuid()'),
            comment='Event ID (UUID)'
        ),
        sa.Column(
            'user_id',
            PG_UUID(as_uuid=True),
            nullable=False,
            comment='User who triggered the event'
        ),
        sa.Column(
            'event_type',
            sa.String(50),
            nullable=False,
            comment='Event type: project_created, spec_added, analysis_run, conflict_resolved, etc.'
        ),
        sa.Column(
            'event_data',
            JSONB,
            nullable=True,
            comment='Event context data as JSON (project_id, spec_id, etc.)'
        ),
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Event timestamp'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        )
    )

    # Create project_metrics table for daily aggregates
    op.create_table(
        'project_metrics',
        sa.Column(
            'id',
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=sa.text('gen_random_uuid()'),
            comment='Metric ID (UUID)'
        ),
        sa.Column(
            'project_id',
            PG_UUID(as_uuid=True),
            nullable=False,
            comment='Project ID'
        ),
        sa.Column(
            'date',
            sa.Date,
            nullable=False,
            comment='Date of the metric'
        ),
        sa.Column(
            'analyses_count',
            sa.Integer,
            nullable=False,
            server_default='0',
            comment='Number of analyses run this day'
        ),
        sa.Column(
            'specs_added',
            sa.Integer,
            nullable=False,
            server_default='0',
            comment='Number of specifications added this day'
        ),
        sa.Column(
            'conflicts_resolved',
            sa.Integer,
            nullable=False,
            server_default='0',
            comment='Number of conflicts resolved this day'
        ),
        sa.ForeignKeyConstraint(
            ['project_id'],
            ['projects.id'],
            ondelete='CASCADE'
        )
    )

    # Create indexes for efficient analytics queries
    op.create_index(
        'idx_analytics_events_user_id',
        'analytics_events',
        ['user_id']
    )

    op.create_index(
        'idx_analytics_events_event_type',
        'analytics_events',
        ['event_type']
    )

    op.create_index(
        'idx_analytics_events_timestamp',
        'analytics_events',
        ['timestamp']
    )

    op.create_index(
        'idx_project_metrics_project_date',
        'project_metrics',
        ['project_id', 'date']
    )

    op.create_index(
        'idx_project_metrics_date',
        'project_metrics',
        ['date']
    )


def downgrade() -> None:
    """Remove analytics tables."""

    # Drop indexes
    op.drop_index('idx_project_metrics_date', table_name='project_metrics')
    op.drop_index('idx_project_metrics_project_date', table_name='project_metrics')
    op.drop_index('idx_analytics_events_timestamp', table_name='analytics_events')
    op.drop_index('idx_analytics_events_event_type', table_name='analytics_events')
    op.drop_index('idx_analytics_events_user_id', table_name='analytics_events')

    # Drop tables
    op.drop_table('project_metrics')
    op.drop_table('analytics_events')

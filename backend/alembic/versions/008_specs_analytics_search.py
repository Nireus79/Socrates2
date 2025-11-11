"""Analytics and Search - Metrics, Document Chunks, and Notifications

Revision ID: 008
Revises: 007
Create Date: 2025-11-11

Creates tables for general analytics metrics, document chunk storage for RAG/search,
and user notification preferences.

Tables created:
- analytics_metrics: General analytics data for tracking and dashboards
- document_chunks: Document chunks for RAG (Retrieval Augmented Generation) and search
- notification_preferences: User notification settings and preferences

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics and search tables for socrates_specs database."""

    # Create analytics_metrics table - general analytics data for tracking and dashboards
    op.create_table(
        'analytics_metrics',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique analytics metric identifier (UUID)'
        ),
        sa.Column(
            'metric_name',
            sa.String(100),
            nullable=False,
            comment='Metric name (active_users, projects_created, avg_session_duration, etc.)'
        ),
        sa.Column(
            'metric_value',
            sa.Float(),
            nullable=True,
            comment='Metric value'
        ),
        sa.Column(
            'dimension_type',
            sa.String(50),
            nullable=True,
            comment='Dimension type (user, project, time_period, etc.)'
        ),
        sa.Column(
            'dimension_value',
            sa.String(255),
            nullable=True,
            comment='Dimension value (user_id, project_id, date, etc.)'
        ),
        sa.Column(
            'period',
            sa.String(20),
            nullable=True,
            comment='Time period (daily, weekly, monthly)'
        ),
        sa.Column(
            'period_start',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Period start date'
        ),
        sa.Column(
            'period_end',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Period end date'
        ),
        sa.Column(
            'tags',
            postgresql.ARRAY(sa.String()),
            nullable=True,
            server_default='{}',
            comment='Array of tags for categorization'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional metadata (data_source, calculation_method, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Metric creation timestamp'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='General analytics data for tracking and dashboards'
    )

    # Create indexes for analytics_metrics
    op.create_index('ix_analytics_metrics_metric_name', 'analytics_metrics', ['metric_name'])
    op.create_index('ix_analytics_metrics_dimension_type', 'analytics_metrics', ['dimension_type'])
    op.create_index('ix_analytics_metrics_dimension_value', 'analytics_metrics', ['dimension_value'])
    op.create_index('ix_analytics_metrics_period', 'analytics_metrics', ['period'])
    op.create_index('ix_analytics_metrics_period_start', 'analytics_metrics', ['period_start'])
    op.create_index('ix_analytics_metrics_created_at', 'analytics_metrics', ['created_at'])

    # Create document_chunks table - document chunks for RAG and search
    op.create_table(
        'document_chunks',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique document chunk identifier (UUID)'
        ),
        sa.Column(
            'document_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to knowledge_base_documents.id (optional)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to projects.id (optional - for project-specific chunks)'
        ),
        sa.Column(
            'chunk_index',
            sa.Integer(),
            nullable=False,
            comment='Sequential index of chunk within document'
        ),
        sa.Column(
            'content',
            sa.Text(),
            nullable=False,
            comment='Chunk content (text to be indexed and searched)'
        ),
        sa.Column(
            'chunk_type',
            sa.String(50),
            nullable=True,
            comment='Chunk type (paragraph, section, code_block, specification, etc.)'
        ),
        sa.Column(
            'source_section',
            sa.String(255),
            nullable=True,
            comment='Source section/heading of chunk'
        ),
        sa.Column(
            'tokens_count',
            sa.Integer(),
            nullable=True,
            comment='Number of tokens in chunk'
        ),
        sa.Column(
            'embedding_id',
            sa.String(255),
            nullable=True,
            comment='Reference to stored embedding (vector database ID)'
        ),
        sa.Column(
            'has_embedding',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether embedding has been generated'
        ),
        sa.Column(
            'relevance_score',
            sa.Float(),
            nullable=True,
            comment='Relevance score based on usage'
        ),
        sa.Column(
            'search_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times chunk appeared in search results'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Chunk metadata (language, keywords, summary, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Chunk creation timestamp'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            comment='Last update timestamp'
        ),
        sa.ForeignKeyConstraint(
            ['document_id'],
            ['knowledge_base_documents.id'],
            ondelete='CASCADE',
            name='fk_document_chunks_document_id'
        ),
        sa.ForeignKeyConstraint(
            ['project_id'],
            ['projects.id'],
            ondelete='CASCADE',
            name='fk_document_chunks_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Document chunks for RAG (Retrieval Augmented Generation) and search'
    )

    # Create indexes for document_chunks
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_project_id', 'document_chunks', ['project_id'])
    op.create_index('ix_document_chunks_chunk_type', 'document_chunks', ['chunk_type'])
    op.create_index('ix_document_chunks_has_embedding', 'document_chunks', ['has_embedding'])
    op.create_index('ix_document_chunks_search_count', 'document_chunks', ['search_count'])
    op.create_index('ix_document_chunks_created_at', 'document_chunks', ['created_at'])

    # Create notification_preferences table - user notification settings
    op.create_table(
        'notification_preferences',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique notification preference identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'notification_type',
            sa.String(100),
            nullable=False,
            comment='Type of notification (project_update, team_invitation, specification_complete, etc.)'
        ),
        sa.Column(
            'email_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment='Whether email notifications are enabled for this type'
        ),
        sa.Column(
            'in_app_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment='Whether in-app notifications are enabled for this type'
        ),
        sa.Column(
            'slack_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether Slack notifications are enabled for this type'
        ),
        sa.Column(
            'frequency',
            sa.String(50),
            nullable=True,
            server_default='immediate',
            comment='Notification frequency (immediate, daily, weekly, off)'
        ),
        sa.Column(
            'quiet_hours_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether quiet hours are enabled for this type'
        ),
        sa.Column(
            'quiet_hours_start',
            sa.String(5),
            nullable=True,
            comment='Quiet hours start time (HH:MM format)'
        ),
        sa.Column(
            'quiet_hours_end',
            sa.String(5),
            nullable=True,
            comment='Quiet hours end time (HH:MM format)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional notification settings (filter_by_project, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Preference creation timestamp'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            comment='Last update timestamp'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'notification_type', name='uq_notification_preferences_user_type'),
        comment='User notification settings and preferences'
    )

    # Create indexes for notification_preferences
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])
    op.create_index('ix_notification_preferences_notification_type', 'notification_preferences', ['notification_type'])
    op.create_index('ix_notification_preferences_email_enabled', 'notification_preferences', ['email_enabled'])
    op.create_index('ix_notification_preferences_in_app_enabled', 'notification_preferences', ['in_app_enabled'])
    op.create_index('ix_notification_preferences_created_at', 'notification_preferences', ['created_at'])


def downgrade() -> None:
    """Drop analytics and search tables."""

    # Drop in reverse dependency order
    op.drop_table('notification_preferences')
    op.drop_table('document_chunks')
    op.drop_table('analytics_metrics')

"""Tracking and Analytics - Quality Metrics and Learning Data

Revision ID: 005
Revises: 004
Create Date: 2025-11-11

Creates tables for tracking project quality metrics, user behavior patterns, question effectiveness,
and knowledge base documents for continuous learning and improvement.

Tables created:
- quality_metrics: Quality assessment data for projects and specifications
- user_behavior_patterns: Analytics on user interaction patterns
- question_effectiveness: Tracking question effectiveness and relevance
- knowledge_base_documents: Knowledge base for RAG and learning

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tracking and analytics tables for socrates_specs database."""

    # Create quality_metrics table - quality assessment data
    op.create_table(
        'quality_metrics',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique quality metric identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'metric_name',
            sa.String(100),
            nullable=False,
            comment='Metric name (completeness, clarity, consistency, etc.)'
        ),
        sa.Column(
            'metric_value',
            sa.Float(),
            nullable=False,
            comment='Metric value (typically 0-100 for scores)'
        ),
        sa.Column(
            'metric_type',
            sa.String(50),
            nullable=True,
            comment='Metric type (specification_quality, documentation_quality, code_quality, coverage, etc.)'
        ),
        sa.Column(
            'measured_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the metric was measured'
        ),
        sa.Column(
            'details',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Detailed metric data (component breakdown, sub-scores, etc.)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional metadata (measured_by, tool_version, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Metric creation timestamp'
        ),
        sa.ForeignKeyConstraint(
            ['project_id'],
            ['projects.id'],
            ondelete='CASCADE',
            name='fk_quality_metrics_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Quality assessment data for projects and specifications'
    )

    # Create indexes for quality_metrics
    op.create_index('ix_quality_metrics_project_id', 'quality_metrics', ['project_id'])
    op.create_index('ix_quality_metrics_metric_name', 'quality_metrics', ['metric_name'])
    op.create_index('ix_quality_metrics_metric_type', 'quality_metrics', ['metric_type'])
    op.create_index('ix_quality_metrics_created_at', 'quality_metrics', ['created_at'])

    # Create user_behavior_patterns table - analytics on user interaction patterns
    op.create_table(
        'user_behavior_patterns',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique behavior pattern identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'pattern_type',
            sa.String(100),
            nullable=False,
            comment='Pattern type (interaction_frequency, question_preference, tool_usage, etc.)'
        ),
        sa.Column(
            'pattern_data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Pattern data (frequency, preferences, statistics, etc.)'
        ),
        sa.Column(
            'confidence_score',
            sa.Float(),
            nullable=True,
            comment='Confidence in the pattern (0-1 scale)'
        ),
        sa.Column(
            'observation_period',
            sa.String(50),
            nullable=True,
            comment='Time period for observation (daily, weekly, monthly, all_time)'
        ),
        sa.Column(
            'sample_size',
            sa.Integer(),
            nullable=True,
            comment='Number of observations in pattern'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional metadata (detected_at, next_update, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Pattern creation timestamp'
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
        comment='Analytics on user interaction patterns and behavior'
    )

    # Create indexes for user_behavior_patterns
    op.create_index('ix_user_behavior_patterns_user_id', 'user_behavior_patterns', ['user_id'])
    op.create_index('ix_user_behavior_patterns_pattern_type', 'user_behavior_patterns', ['pattern_type'])
    op.create_index('ix_user_behavior_patterns_created_at', 'user_behavior_patterns', ['created_at'])

    # Create question_effectiveness table - tracking question effectiveness and relevance
    op.create_table(
        'question_effectiveness',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique effectiveness record identifier (UUID)'
        ),
        sa.Column(
            'question_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to questions.id (optional - pattern may be from template)'
        ),
        sa.Column(
            'question_text',
            sa.Text(),
            nullable=True,
            comment='Question text for reference'
        ),
        sa.Column(
            'project_type',
            sa.String(100),
            nullable=True,
            comment='Type of projects where question is asked (web_app, api, mobile, etc.)'
        ),
        sa.Column(
            'effectiveness_score',
            sa.Float(),
            nullable=True,
            comment='Effectiveness score (0-1 or 0-100 scale)'
        ),
        sa.Column(
            'relevance_score',
            sa.Float(),
            nullable=True,
            comment='Relevance score (how often is answer actually needed)'
        ),
        sa.Column(
            'clarity_score',
            sa.Float(),
            nullable=True,
            comment='Clarity score (how well users understand the question)'
        ),
        sa.Column(
            'times_asked',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times question was asked'
        ),
        sa.Column(
            'times_skipped',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times question was skipped'
        ),
        sa.Column(
            'average_response_time_seconds',
            sa.Float(),
            nullable=True,
            comment='Average time to answer question (seconds)'
        ),
        sa.Column(
            'feedback',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='User feedback and ratings'
        ),
        sa.Column(
            'recommendations',
            sa.Text(),
            nullable=True,
            comment='Recommendations for improving question'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional metadata (last_measured, trend, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Effectiveness record creation timestamp'
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
        comment='Tracking question effectiveness and relevance for continuous improvement'
    )

    # Create indexes for question_effectiveness
    op.create_index('ix_question_effectiveness_question_id', 'question_effectiveness', ['question_id'])
    op.create_index('ix_question_effectiveness_project_type', 'question_effectiveness', ['project_type'])
    op.create_index('ix_question_effectiveness_effectiveness_score', 'question_effectiveness', ['effectiveness_score'])
    op.create_index('ix_question_effectiveness_created_at', 'question_effectiveness', ['created_at'])

    # Create knowledge_base_documents table - knowledge base for RAG and learning
    op.create_table(
        'knowledge_base_documents',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique document identifier (UUID)'
        ),
        sa.Column(
            'title',
            sa.String(255),
            nullable=False,
            comment='Document title'
        ),
        sa.Column(
            'content',
            sa.Text(),
            nullable=True,
            comment='Document content (text, markdown, or structured data)'
        ),
        sa.Column(
            'document_type',
            sa.String(100),
            nullable=True,
            comment='Document type (best_practice, pattern, template, design_guide, etc.)'
        ),
        sa.Column(
            'category',
            sa.String(100),
            nullable=True,
            comment='Document category (architecture, testing, deployment, database, etc.)'
        ),
        sa.Column(
            'tags',
            postgresql.ARRAY(sa.String()),
            nullable=True,
            server_default='{}',
            comment='Array of tags for categorization and search'
        ),
        sa.Column(
            'source',
            sa.String(255),
            nullable=True,
            comment='Document source (extracted_from_projects, best_practices_db, user_contributed, etc.)'
        ),
        sa.Column(
            'version',
            sa.Integer(),
            nullable=False,
            server_default='1',
            comment='Document version number'
        ),
        sa.Column(
            'is_approved',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether document has been reviewed and approved'
        ),
        sa.Column(
            'relevance_score',
            sa.Float(),
            nullable=True,
            comment='Relevance score based on usage (0-1 scale)'
        ),
        sa.Column(
            'usage_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times referenced in projects'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Document metadata (author, approved_by, embedding_id, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Document creation timestamp'
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
        comment='Knowledge base documents for RAG and continuous learning'
    )

    # Create indexes for knowledge_base_documents
    op.create_index('ix_knowledge_base_documents_title', 'knowledge_base_documents', ['title'])
    op.create_index('ix_knowledge_base_documents_document_type', 'knowledge_base_documents', ['document_type'])
    op.create_index('ix_knowledge_base_documents_category', 'knowledge_base_documents', ['category'])
    op.create_index('ix_knowledge_base_documents_is_approved', 'knowledge_base_documents', ['is_approved'])
    op.create_index('ix_knowledge_base_documents_created_at', 'knowledge_base_documents', ['created_at'])


def downgrade() -> None:
    """Drop tracking and analytics tables."""

    # Drop in reverse dependency order
    op.drop_table('knowledge_base_documents')
    op.drop_table('question_effectiveness')
    op.drop_table('user_behavior_patterns')
    op.drop_table('quality_metrics')

"""create llm_usage_tracking table

Revision ID: 019
Revises: 018
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create llm_usage_tracking table"""
    if not _should_run():
        return

    op.create_table(
        'llm_usage_tracking',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True, comment='Primary key (auto-increment)'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='References users.id in socrates_auth database'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='Foreign key to projects table'),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True, comment='Foreign key to sessions table'),
        sa.Column('provider', sa.String(length=50), nullable=False, comment='LLM provider used'),
        sa.Column('model', sa.String(length=100), nullable=False, comment='Model name'),
        sa.Column('tokens_input', sa.Integer(), nullable=False, comment='Input tokens used'),
        sa.Column('tokens_output', sa.Integer(), nullable=False, comment='Output tokens generated'),
        sa.Column('tokens_total', sa.Integer(), nullable=False, comment='Total tokens used'),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=True, comment='Cost in USD'),
        sa.Column('latency_ms', sa.Integer(), nullable=True, comment='Request latency in milliseconds'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='When the LLM call was made')
    )

    # Create indexes
    op.create_index('idx_llm_usage_user_id', 'llm_usage_tracking', ['user_id'])
    op.create_index('idx_llm_usage_project_id', 'llm_usage_tracking', ['project_id'])
    op.create_index('idx_llm_usage_timestamp', 'llm_usage_tracking', ['timestamp'], postgresql_using='btree', postgresql_ops={'timestamp': 'DESC'})
    op.create_index('idx_llm_usage_provider', 'llm_usage_tracking', ['provider'])


def downgrade():
    """Drop llm_usage_tracking table"""
    if not _should_run():
        return

    op.drop_index('idx_llm_usage_provider', table_name='llm_usage_tracking')
    op.drop_index('idx_llm_usage_timestamp', table_name='llm_usage_tracking')
    op.drop_index('idx_llm_usage_project_id', table_name='llm_usage_tracking')
    op.drop_index('idx_llm_usage_user_id', table_name='llm_usage_tracking')
    op.drop_table('llm_usage_tracking')

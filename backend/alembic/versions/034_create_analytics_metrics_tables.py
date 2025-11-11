"""Create analytics metrics tables for Phase 3.

Revision ID: 034_create_analytics_metrics_tables
Revises: 033_create_admin_audit_logs_table
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '034_create_analytics_metrics_tables'
down_revision = '033_create_admin_audit_logs_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics metrics tables in specs database."""

    # Daily Active Users (DAU)
    op.create_table(
        'daily_active_users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('new_users', sa.Integer(), nullable=False),
        sa.Column('returning_users', sa.Integer(), nullable=False),
        sa.Column('breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_daily_active_users_date', 'daily_active_users', ['date'])

    # Monthly Recurring Revenue (MRR)
    op.create_table(
        'monthly_recurring_revenue',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('month_start', sa.Date(), nullable=False, unique=True),
        sa.Column('total_mrr', sa.Numeric(12, 2), nullable=False),
        sa.Column('new_mrr', sa.Numeric(12, 2), nullable=True),
        sa.Column('churned_mrr', sa.Numeric(12, 2), nullable=True),
        sa.Column('by_tier', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_monthly_recurring_revenue_month_start', 'monthly_recurring_revenue', ['month_start'])

    # Churn Analysis
    op.create_table(
        'churn_analysis',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('churned_users', sa.Integer(), nullable=False),
        sa.Column('churn_rate_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('by_tier', postgresql.JSONB(), nullable=True),
        sa.Column('by_region', postgresql.JSONB(), nullable=True),
        sa.Column('reasons', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_churn_analysis_date', 'churn_analysis', ['date'])

    # Feature Usage
    op.create_table(
        'feature_usage',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('feature_name', sa.String(100), nullable=False),
        sa.Column('users_using', sa.Integer(), nullable=False),
        sa.Column('total_uses', sa.Integer(), nullable=False),
        sa.Column('avg_uses_per_user', sa.Numeric(8, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'feature_name', name='uq_feature_usage_date_feature')
    )
    op.create_index('ix_feature_usage_date', 'feature_usage', ['date'])
    op.create_index('ix_feature_usage_feature_name', 'feature_usage', ['feature_name'])

    # Conversion Funnel
    op.create_table(
        'conversion_funnel',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('signups', sa.Integer(), nullable=False),
        sa.Column('trial_started', sa.Integer(), nullable=False),
        sa.Column('trial_to_paid', sa.Integer(), nullable=False),
        sa.Column('paid_users', sa.Integer(), nullable=False),
        sa.Column('conversion_rate_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversion_funnel_date', 'conversion_funnel', ['date'])


def downgrade() -> None:
    """Drop analytics metrics tables."""
    op.drop_index('ix_conversion_funnel_date', table_name='conversion_funnel')
    op.drop_table('conversion_funnel')

    op.drop_index('ix_feature_usage_feature_name', table_name='feature_usage')
    op.drop_index('ix_feature_usage_date', table_name='feature_usage')
    op.drop_table('feature_usage')

    op.drop_index('ix_churn_analysis_date', table_name='churn_analysis')
    op.drop_table('churn_analysis')

    op.drop_index('ix_monthly_recurring_revenue_month_start', table_name='monthly_recurring_revenue')
    op.drop_table('monthly_recurring_revenue')

    op.drop_index('ix_daily_active_users_date', table_name='daily_active_users')
    op.drop_table('daily_active_users')

"""Add subscription and billing fields to users table.

Revision ID: 027
Revises: 026
Create Date: 2025-11-11 12:00:00.000000

This migration adds billing/subscription fields to the User model:
- subscription_tier: Subscription level (free, pro, team, enterprise)
- stripe_customer_id: Stripe customer identifier
- trial_ends_at: When the trial period expires
- subscription_status: Subscription state (active, canceled, past_due, unpaid)

These fields are prerequisites for Phase 2: Monetization & Billing.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None



def _should_run():
    """Only run this migration for socrates_auth database"""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url

def upgrade() -> None:
    """Add subscription fields to users table."""
    if not _should_run():
        return

    # Add subscription tier (free, pro, team, enterprise)
    op.add_column(
        'users',
        sa.Column(
            'subscription_tier',
            sa.String(20),
            nullable=False,
            server_default='free',
            comment='Subscription tier: free, pro, team, enterprise'
        )
    )

    # Add Stripe customer ID (for Stripe integration)
    op.add_column(
        'users',
        sa.Column(
            'stripe_customer_id',
            sa.String(255),
            nullable=True,
            unique=True,
            comment='Stripe customer ID for billing integration'
        )
    )

    # Add trial end date (for free trial period)
    op.add_column(
        'users',
        sa.Column(
            'trial_ends_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the free trial expires (if user is on trial)'
        )
    )

    # Add subscription status (active, canceled, past_due, unpaid)
    op.add_column(
        'users',
        sa.Column(
            'subscription_status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='Subscription status: active, canceled, past_due, unpaid'
        )
    )

    # Create indexes for efficient queries
    op.create_index(
        'idx_users_subscription_tier',
        'users',
        ['subscription_tier']
    )

    op.create_index(
        'idx_users_stripe_customer_id',
        'users',
        ['stripe_customer_id']
    )

    op.create_index(
        'idx_users_trial_ends_at',
        'users',
        ['trial_ends_at']
    )

    op.create_index(
        'idx_users_subscription_status',
        'users',
        ['subscription_status']
    )


def downgrade() -> None:
    """Remove subscription fields from users table."""
    if not _should_run():
        return

    # Drop indexes
    op.drop_index('idx_users_subscription_status', table_name='users')
    op.drop_index('idx_users_trial_ends_at', table_name='users')
    op.drop_index('idx_users_stripe_customer_id', table_name='users')
    op.drop_index('idx_users_subscription_tier', table_name='users')

    # Drop columns
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'trial_ends_at')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'subscription_tier')

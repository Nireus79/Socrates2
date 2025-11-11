"""API and LLM Integration - Keys, Usage Tracking, and Billing

Revision ID: 007
Revises: 006
Create Date: 2025-11-11

Creates tables for API key management, LLM usage tracking, subscription management,
and billing/invoicing for the platform.

Tables created:
- api_keys: API key management with encryption
- llm_usage_tracking: LLM request tracking and cost analysis
- subscriptions: Subscription plans and management
- invoices: Billing records and payment tracking

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create API and LLM integration tables for socrates_specs database."""

    # Create api_keys table - API key management with encryption
    op.create_table(
        'api_keys',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique API key identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            comment='API key name/label for identification'
        ),
        sa.Column(
            'key_hash',
            sa.String(255),
            nullable=False,
            unique=True,
            comment='Hashed API key (only hash stored, not plain key)'
        ),
        sa.Column(
            'key_preview',
            sa.String(20),
            nullable=True,
            comment='Last 4 characters of key for preview (e.g., ...abcd)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='Key status (active, revoked, expired)'
        ),
        sa.Column(
            'scope',
            postgresql.ARRAY(sa.String()),
            nullable=True,
            server_default='{}',
            comment='Array of permission scopes (read, write, admin, projects:read, etc.)'
        ),
        sa.Column(
            'rate_limit',
            sa.Integer(),
            nullable=True,
            comment='Rate limit in requests per minute'
        ),
        sa.Column(
            'usage_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Total API requests made with this key'
        ),
        sa.Column(
            'last_used_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Last time key was used'
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Optional expiration date'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='API key metadata (ip_whitelist, associated_app, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='API key creation timestamp'
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
        sa.UniqueConstraint('key_hash', name='uq_api_keys_key_hash'),
        comment='API key management with encryption'
    )

    # Create indexes for api_keys
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_status', 'api_keys', ['status'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_created_at', 'api_keys', ['created_at'])

    # Create llm_usage_tracking table - LLM request tracking and cost analysis
    op.create_table(
        'llm_usage_tracking',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique usage record identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to projects.id (optional - for project-level tracking)'
        ),
        sa.Column(
            'model_name',
            sa.String(100),
            nullable=False,
            comment='LLM model used (e.g., claude-3-opus, gpt-4, etc.)'
        ),
        sa.Column(
            'operation_type',
            sa.String(100),
            nullable=True,
            comment='Type of operation (question_answering, code_generation, specification, etc.)'
        ),
        sa.Column(
            'input_tokens',
            sa.Integer(),
            nullable=False,
            comment='Number of input tokens used'
        ),
        sa.Column(
            'output_tokens',
            sa.Integer(),
            nullable=False,
            comment='Number of output tokens generated'
        ),
        sa.Column(
            'total_tokens',
            sa.Integer(),
            nullable=False,
            comment='Total tokens used (input + output)'
        ),
        sa.Column(
            'cost_usd',
            sa.Numeric(10, 6),
            nullable=True,
            comment='Cost in USD for this request'
        ),
        sa.Column(
            'latency_ms',
            sa.Integer(),
            nullable=True,
            comment='Request latency in milliseconds'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='success',
            comment='Request status (success, error, timeout, rate_limited)'
        ),
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Error message if request failed'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional metadata (api_key_id, temperature, context_size, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Request timestamp'
        ),
        sa.ForeignKeyConstraint(
            ['project_id'],
            ['projects.id'],
            ondelete='SET NULL',
            name='fk_llm_usage_tracking_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='LLM request tracking and cost analysis'
    )

    # Create indexes for llm_usage_tracking
    op.create_index('ix_llm_usage_tracking_user_id', 'llm_usage_tracking', ['user_id'])
    op.create_index('ix_llm_usage_tracking_project_id', 'llm_usage_tracking', ['project_id'])
    op.create_index('ix_llm_usage_tracking_model_name', 'llm_usage_tracking', ['model_name'])
    op.create_index('ix_llm_usage_tracking_operation_type', 'llm_usage_tracking', ['operation_type'])
    op.create_index('ix_llm_usage_tracking_status', 'llm_usage_tracking', ['status'])
    op.create_index('ix_llm_usage_tracking_created_at', 'llm_usage_tracking', ['created_at'])

    # Create subscriptions table - subscription plans and management
    op.create_table(
        'subscriptions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique subscription identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'plan_name',
            sa.String(100),
            nullable=False,
            comment='Subscription plan name (free, starter, professional, enterprise)'
        ),
        sa.Column(
            'plan_type',
            sa.String(50),
            nullable=True,
            comment='Plan type (monthly, yearly, usage-based)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='Subscription status (active, cancelled, suspended, expired, past_due)'
        ),
        sa.Column(
            'price_usd',
            sa.Numeric(10, 2),
            nullable=True,
            comment='Monthly subscription price in USD'
        ),
        sa.Column(
            'billing_cycle_start',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Start date of billing cycle'
        ),
        sa.Column(
            'billing_cycle_end',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='End date of billing cycle'
        ),
        sa.Column(
            'stripe_customer_id',
            sa.String(255),
            nullable=True,
            comment='Stripe customer ID for payment processing'
        ),
        sa.Column(
            'stripe_subscription_id',
            sa.String(255),
            nullable=True,
            comment='Stripe subscription ID'
        ),
        sa.Column(
            'features',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Plan features and limits (max_projects, token_limit, etc.)'
        ),
        sa.Column(
            'auto_renew',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment='Whether subscription auto-renews'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Subscription metadata (discount_code, promo_applied, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Subscription creation timestamp'
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
        comment='Subscription plans and management'
    )

    # Create indexes for subscriptions
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_plan_name', 'subscriptions', ['plan_name'])
    op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])
    op.create_index('ix_subscriptions_created_at', 'subscriptions', ['created_at'])

    # Create invoices table - billing records and payment tracking
    op.create_table(
        'invoices',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique invoice identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'subscription_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to subscriptions.id (null for one-time charges)'
        ),
        sa.Column(
            'invoice_number',
            sa.String(50),
            nullable=False,
            unique=True,
            comment='Unique invoice number for accounting'
        ),
        sa.Column(
            'amount_usd',
            sa.Numeric(10, 2),
            nullable=False,
            comment='Invoice amount in USD'
        ),
        sa.Column(
            'currency',
            sa.String(3),
            nullable=False,
            server_default='USD',
            comment='Currency code (USD, EUR, GBP, etc.)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='draft',
            comment='Invoice status (draft, sent, paid, overdue, cancelled)'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Invoice description/notes'
        ),
        sa.Column(
            'line_items',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Invoice line items with details'
        ),
        sa.Column(
            'issued_date',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Invoice issue date'
        ),
        sa.Column(
            'due_date',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Invoice due date'
        ),
        sa.Column(
            'paid_date',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When invoice was paid'
        ),
        sa.Column(
            'stripe_invoice_id',
            sa.String(255),
            nullable=True,
            comment='Stripe invoice ID for integration'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Invoice metadata (payment_method, tax_id, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Invoice creation timestamp'
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
            ['subscription_id'],
            ['subscriptions.id'],
            ondelete='SET NULL',
            name='fk_invoices_subscription_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number', name='uq_invoices_invoice_number'),
        comment='Billing records and payment tracking'
    )

    # Create indexes for invoices
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_subscription_id', 'invoices', ['subscription_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('ix_invoices_stripe_invoice_id', 'invoices', ['stripe_invoice_id'])
    op.create_index('ix_invoices_issued_date', 'invoices', ['issued_date'])
    op.create_index('ix_invoices_due_date', 'invoices', ['due_date'])
    op.create_index('ix_invoices_created_at', 'invoices', ['created_at'])


def downgrade() -> None:
    """Drop API and LLM integration tables."""

    # Drop in reverse dependency order
    op.drop_table('invoices')
    op.drop_table('subscriptions')
    op.drop_table('llm_usage_tracking')
    op.drop_table('api_keys')

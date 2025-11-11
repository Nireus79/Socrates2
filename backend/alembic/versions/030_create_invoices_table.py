"""Create invoices table for billing records.

Revision ID: 030
Revises: 029
Create Date: 2025-11-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(255), nullable=False),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('amount_due', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='usd'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hosted_invoice_url', sa.String(500), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_invoice_id'),
    )
    op.create_index('idx_invoice_user', 'invoices', ['user_id'], unique=False)
    op.create_index('idx_invoice_status', 'invoices', ['status'], unique=False)
    op.create_index('idx_invoice_stripe_id', 'invoices', ['stripe_invoice_id'], unique=False)
    op.create_index('idx_invoice_date', 'invoices', ['invoice_date'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_invoice_date', table_name='invoices')
    op.drop_index('idx_invoice_stripe_id', table_name='invoices')
    op.drop_index('idx_invoice_status', table_name='invoices')
    op.drop_index('idx_invoice_user', table_name='invoices')
    op.drop_table('invoices')

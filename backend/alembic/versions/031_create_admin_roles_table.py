"""Create admin roles table.

Revision ID: 031_create_admin_roles_table
Revises: 030_create_invoices_table
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '031_create_admin_roles_table'
down_revision = '030_create_invoices_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admin_roles table in auth database."""
    op.create_table(
        'admin_roles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_admin_roles_name', 'admin_roles', ['name'])
    op.create_index('ix_admin_roles_is_system_role', 'admin_roles', ['is_system_role'])


def downgrade() -> None:
    """Drop admin_roles table."""
    op.drop_index('ix_admin_roles_is_system_role', table_name='admin_roles')
    op.drop_index('ix_admin_roles_name', table_name='admin_roles')
    op.drop_table('admin_roles')

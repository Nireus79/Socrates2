"""Create admin users table.

Revision ID: 032_create_admin_users_table
Revises: 031_create_admin_roles_table
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None



def _should_run():
    """Only run this migration for socrates_specs database"""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_auth" in db_url

def upgrade() -> None:
    """Create admin_users table in auth database."""
    if not _should_run():
        return
    op.create_table(
        'admin_users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.Column('granted_by_id', sa.String(36), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['admin_roles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_admin_users_user_id', 'admin_users', ['user_id'])
    op.create_index('ix_admin_users_role_id', 'admin_users', ['role_id'])
    op.create_index('ix_admin_users_revoked_at', 'admin_users', ['revoked_at'])
    op.create_index('ix_admin_users_created_at', 'admin_users', ['created_at'])


def downgrade() -> None:
    """Drop admin_users table."""
    if not _should_run():
        return
    op.drop_index('ix_admin_users_created_at', table_name='admin_users')
    op.drop_index('ix_admin_users_revoked_at', table_name='admin_users')
    op.drop_index('ix_admin_users_role_id', table_name='admin_users')
    op.drop_index('ix_admin_users_user_id', table_name='admin_users')
    op.drop_table('admin_users')

"""Admin Management - Roles, Users, and Audit Logs

Revision ID: 002
Revises: 001
Create Date: 2025-11-11

Creates tables for admin role-based access control (RBAC) and audit logging.

Tables created:
- admin_roles: Role definitions with permission sets
- admin_users: Maps users to admin roles
- admin_audit_logs: Tracks admin actions for security

Target Database: socrates_auth
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admin RBAC and audit logging tables."""

    # Create admin_roles table - defines roles and their permissions
    op.create_table(
        'admin_roles',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique role identifier'
        ),
        sa.Column(
            'name',
            sa.String(100),
            nullable=False,
            unique=True,
            comment='Role name (e.g., super_admin, moderator, support)'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Role description'
        ),
        sa.Column(
            'permissions',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
            comment='Array of permission strings (e.g., [admin:users:read, admin:users:write])'
        ),
        sa.Column(
            'is_system_role',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether this is a built-in system role'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Role creation timestamp'
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
        sa.UniqueConstraint('name', name='uq_admin_roles_name'),
        comment='Admin role definitions with permission sets'
    )

    # Create indexes
    op.create_index('ix_admin_roles_name', 'admin_roles', ['name'], unique=True)
    op.create_index('ix_admin_roles_is_system_role', 'admin_roles', ['is_system_role'])

    # Create admin_users table - maps users to admin roles
    op.create_table(
        'admin_users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique assignment identifier'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id'
        ),
        sa.Column(
            'role_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to admin_roles.id'
        ),
        sa.Column(
            'granted_by_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to users.id of the admin who granted this role'
        ),
        sa.Column(
            'reason',
            sa.Text(),
            nullable=True,
            comment='Reason for granting this admin role'
        ),
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the admin role was revoked (if applicable)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='When role was granted'
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
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_admin_users_user_id'
        ),
        sa.ForeignKeyConstraint(
            ['role_id'],
            ['admin_roles.id'],
            ondelete='RESTRICT',
            name='fk_admin_users_role_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_admin_users_user_role'),
        comment='Admin user role assignments'
    )

    # Create indexes
    op.create_index('ix_admin_users_user_id', 'admin_users', ['user_id'])
    op.create_index('ix_admin_users_role_id', 'admin_users', ['role_id'])
    op.create_index('ix_admin_users_granted_by_id', 'admin_users', ['granted_by_id'])
    op.create_index('ix_admin_users_revoked_at', 'admin_users', ['revoked_at'])

    # Create admin_audit_logs table - audit trail for admin actions
    op.create_table(
        'admin_audit_logs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique log entry identifier'
        ),
        sa.Column(
            'admin_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id of the admin who performed action'
        ),
        sa.Column(
            'action',
            sa.String(100),
            nullable=False,
            comment='Type of action (e.g., user_created, user_suspended, role_assigned)'
        ),
        sa.Column(
            'resource_type',
            sa.String(100),
            nullable=False,
            comment='Type of resource affected (e.g., user, project, team)'
        ),
        sa.Column(
            'resource_id',
            sa.String(36),
            nullable=False,
            comment='ID of the resource that was affected'
        ),
        sa.Column(
            'changes',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='JSON object describing what changed'
        ),
        sa.Column(
            'ip_address',
            sa.String(45),
            nullable=True,
            comment='IP address from which action was performed'
        ),
        sa.Column(
            'user_agent',
            sa.String(500),
            nullable=True,
            comment='User agent string from request'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='When the action was performed'
        ),
        sa.ForeignKeyConstraint(
            ['admin_id'],
            ['users.id'],
            ondelete='RESTRICT',
            name='fk_admin_audit_logs_admin_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit log for all admin actions'
    )

    # Create indexes
    op.create_index('ix_admin_audit_logs_admin_id', 'admin_audit_logs', ['admin_id'])
    op.create_index('ix_admin_audit_logs_action', 'admin_audit_logs', ['action'])
    op.create_index('ix_admin_audit_logs_resource_type', 'admin_audit_logs', ['resource_type'])
    op.create_index(
        'ix_admin_audit_logs_resource',
        'admin_audit_logs',
        ['resource_type', 'resource_id']
    )
    op.create_index('ix_admin_audit_logs_created_at', 'admin_audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop admin tables."""

    # Drop in reverse dependency order
    op.drop_table('admin_audit_logs')
    op.drop_table('admin_users')
    op.drop_table('admin_roles')

"""Activity and Project Management - Audit Trail and Collaboration Invites

Revision ID: 009
Revises: 008
Create Date: 2025-11-11

Creates tables for activity logging (audit trail) and project invitation management
for collaboration and accountability tracking.

Tables created:
- activity_logs: Audit trail for all activities and changes
- project_invitations: Project collaboration invitations and requests

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create activity and project management tables for socrates_specs database."""

    # Create activity_logs table - audit trail for all activities and changes
    op.create_table(
        'activity_logs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique activity log identifier (UUID)'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (who performed action, no FK constraint - cross-database)'
        ),
        sa.Column(
            'action',
            sa.String(100),
            nullable=False,
            comment='Action type (created, updated, deleted, published, shared, etc.)'
        ),
        sa.Column(
            'resource_type',
            sa.String(100),
            nullable=False,
            comment='Type of resource affected (project, specification, file, question, etc.)'
        ),
        sa.Column(
            'resource_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='ID of the resource that was affected'
        ),
        sa.Column(
            'resource_name',
            sa.String(255),
            nullable=True,
            comment='Resource name for display (project name, file path, etc.)'
        ),
        sa.Column(
            'changes',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='JSON object describing what changed (before/after values)'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Human-readable description of the activity'
        ),
        sa.Column(
            'severity',
            sa.String(20),
            nullable=True,
            server_default='info',
            comment='Activity severity (info, warning, error, critical)'
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
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Additional metadata (client_app, api_key, session_id, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='When the activity was performed'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Audit trail for all activities and changes'
    )

    # Create indexes for activity_logs
    op.create_index('ix_activity_logs_user_id', 'activity_logs', ['user_id'])
    op.create_index('ix_activity_logs_action', 'activity_logs', ['action'])
    op.create_index('ix_activity_logs_resource_type', 'activity_logs', ['resource_type'])
    op.create_index('ix_activity_logs_resource_id', 'activity_logs', ['resource_id'])
    op.create_index(
        'ix_activity_logs_resource',
        'activity_logs',
        ['resource_type', 'resource_id']
    )
    op.create_index('ix_activity_logs_severity', 'activity_logs', ['severity'])
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'])

    # Create project_invitations table - project collaboration invitations and requests
    op.create_table(
        'project_invitations',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique invitation identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'invited_user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to users.id in socrates_auth database (invited user, null if email-based invite, no FK constraint)'
        ),
        sa.Column(
            'invited_email',
            sa.String(255),
            nullable=True,
            comment='Email address the invitation was sent to (for external/pre-signup invites)'
        ),
        sa.Column(
            'invited_by_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (who sent the invite, no FK constraint - cross-database)'
        ),
        sa.Column(
            'role',
            sa.String(50),
            nullable=False,
            server_default='member',
            comment='Role being offered (viewer, member, lead, admin)'
        ),
        sa.Column(
            'permission_level',
            sa.String(50),
            nullable=True,
            comment='Permission level (read, write, admin)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            comment='Invitation status (pending, accepted, declined, revoked, expired)'
        ),
        sa.Column(
            'invitation_token',
            sa.String(255),
            nullable=True,
            comment='Token for invitation link (if email-based)'
        ),
        sa.Column(
            'token_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the invitation token expires'
        ),
        sa.Column(
            'message',
            sa.Text(),
            nullable=True,
            comment='Custom message from inviter'
        ),
        sa.Column(
            'responded_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the invitation was accepted/declined'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Invitation metadata (reminder_sent, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Invitation creation timestamp'
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
            ['project_id'],
            ['projects.id'],
            ondelete='CASCADE',
            name='fk_project_invitations_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Project collaboration invitations and requests'
    )

    # Create indexes for project_invitations
    op.create_index('ix_project_invitations_project_id', 'project_invitations', ['project_id'])
    op.create_index('ix_project_invitations_invited_user_id', 'project_invitations', ['invited_user_id'])
    op.create_index('ix_project_invitations_invited_email', 'project_invitations', ['invited_email'])
    op.create_index('ix_project_invitations_invited_by_id', 'project_invitations', ['invited_by_id'])
    op.create_index('ix_project_invitations_status', 'project_invitations', ['status'])
    op.create_index('ix_project_invitations_role', 'project_invitations', ['role'])
    op.create_index('ix_project_invitations_invitation_token', 'project_invitations', ['invitation_token'])
    op.create_index('ix_project_invitations_created_at', 'project_invitations', ['created_at'])


def downgrade() -> None:
    """Drop activity and project management tables."""

    # Drop in reverse dependency order
    op.drop_table('project_invitations')
    op.drop_table('activity_logs')

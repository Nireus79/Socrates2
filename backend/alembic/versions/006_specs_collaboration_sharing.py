"""Collaboration and Sharing - Team and Project Management

Revision ID: 006
Revises: 005
Create Date: 2025-11-11

Creates tables for team management, team membership, and project sharing for collaborative development.

Tables created:
- teams: Team definitions and metadata
- team_members: Team membership and role assignments
- project_shares: Project sharing permissions and access control

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create collaboration and sharing tables for socrates_specs database."""

    # Create teams table - team definitions and metadata
    op.create_table(
        'teams',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique team identifier (UUID)'
        ),
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            comment='Team name'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Team description'
        ),
        sa.Column(
            'owner_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (team owner, no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='Team status (active, archived, suspended)'
        ),
        sa.Column(
            'member_count',
            sa.Integer(),
            nullable=False,
            server_default='1',
            comment='Current number of team members'
        ),
        sa.Column(
            'project_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of projects managed by team'
        ),
        sa.Column(
            'settings',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Team settings (visibility, permissions, etc.)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Team metadata (department, budget, tags, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Team creation timestamp'
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
        sa.UniqueConstraint('name', name='uq_teams_name'),
        comment='Team definitions and metadata'
    )

    # Create indexes for teams
    op.create_index('ix_teams_owner_id', 'teams', ['owner_id'])
    op.create_index('ix_teams_status', 'teams', ['status'])
    op.create_index('ix_teams_name', 'teams', ['name'], unique=True)
    op.create_index('ix_teams_created_at', 'teams', ['created_at'])

    # Create team_members table - team membership and role assignments
    op.create_table(
        'team_members',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique team membership identifier (UUID)'
        ),
        sa.Column(
            'team_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to teams.id'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'role',
            sa.String(50),
            nullable=False,
            server_default='member',
            comment='Team role (owner, admin, lead, member, viewer)'
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
            server_default='active',
            comment='Membership status (active, invited, inactive, suspended)'
        ),
        sa.Column(
            'invited_by_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to users.id who invited this member (no FK constraint - cross-database)'
        ),
        sa.Column(
            'joined_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When member joined the team'
        ),
        sa.Column(
            'contribution_score',
            sa.Float(),
            nullable=True,
            comment='Contribution score based on activity'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Member metadata (skills, interests, permissions, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Membership creation timestamp'
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
            ['team_id'],
            ['teams.id'],
            ondelete='CASCADE',
            name='fk_team_members_team_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id', name='uq_team_members_team_user'),
        comment='Team membership and role assignments'
    )

    # Create indexes for team_members
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('ix_team_members_role', 'team_members', ['role'])
    op.create_index('ix_team_members_status', 'team_members', ['status'])
    op.create_index('ix_team_members_created_at', 'team_members', ['created_at'])

    # Create project_shares table - project sharing permissions and access control
    op.create_table(
        'project_shares',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique share record identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'shared_with_user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to users.id in socrates_auth database (null if shared with team, no FK constraint)'
        ),
        sa.Column(
            'shared_with_team_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to teams.id (null if shared with user)'
        ),
        sa.Column(
            'shared_by_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id who shared the project (no FK constraint - cross-database)'
        ),
        sa.Column(
            'permission_level',
            sa.String(50),
            nullable=False,
            server_default='view',
            comment='Permission level (view, comment, edit, admin)'
        ),
        sa.Column(
            'access_type',
            sa.String(50),
            nullable=False,
            comment='Access type (shared_user, shared_team, public, link)'
        ),
        sa.Column(
            'expiry_date',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Optional expiry date for time-limited access'
        ),
        sa.Column(
            'password_protected',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether access is password protected'
        ),
        sa.Column(
            'access_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times shared resource was accessed'
        ),
        sa.Column(
            'last_accessed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Last access timestamp'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Share metadata (message, custom_permissions, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Share creation timestamp'
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
            name='fk_project_shares_project_id'
        ),
        sa.ForeignKeyConstraint(
            ['shared_with_team_id'],
            ['teams.id'],
            ondelete='CASCADE',
            name='fk_project_shares_shared_with_team_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Project sharing permissions and access control'
    )

    # Create indexes for project_shares
    op.create_index('ix_project_shares_project_id', 'project_shares', ['project_id'])
    op.create_index('ix_project_shares_shared_with_user_id', 'project_shares', ['shared_with_user_id'])
    op.create_index('ix_project_shares_shared_with_team_id', 'project_shares', ['shared_with_team_id'])
    op.create_index('ix_project_shares_shared_by_id', 'project_shares', ['shared_by_id'])
    op.create_index('ix_project_shares_permission_level', 'project_shares', ['permission_level'])
    op.create_index('ix_project_shares_access_type', 'project_shares', ['access_type'])
    op.create_index('ix_project_shares_created_at', 'project_shares', ['created_at'])


def downgrade() -> None:
    """Drop collaboration and sharing tables."""

    # Drop in reverse dependency order
    op.drop_table('project_shares')
    op.drop_table('team_members')
    op.drop_table('teams')

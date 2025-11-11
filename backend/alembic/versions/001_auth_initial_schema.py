"""Initial Auth Schema - Users and JWT tokens

Revision ID: 001
Revises: None
Create Date: 2025-11-11

This is the first migration for the socrates_auth database.
Creates the foundation tables for user authentication and JWT token management.

Tables created:
- users: User accounts with authentication credentials
- refresh_tokens: JWT refresh token tracking

Target Database: socrates_auth
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = ('auth',)
depends_on = None


def upgrade() -> None:
    """Create users and refresh_tokens tables in socrates_auth database."""

    # Create users table - the core authentication table
    op.create_table(
        'users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique user identifier (UUID)'
        ),
        sa.Column(
            'email',
            sa.String(255),
            nullable=False,
            unique=True,
            comment='User email address (must be unique)'
        ),
        sa.Column(
            'hashed_password',
            sa.String(255),
            nullable=False,
            comment='Bcrypt hashed password'
        ),
        sa.Column(
            'name',
            sa.String(100),
            nullable=True,
            comment='User first name'
        ),
        sa.Column(
            'surname',
            sa.String(100),
            nullable=True,
            comment='User last name'
        ),
        sa.Column(
            'username',
            sa.String(50),
            nullable=True,
            unique=True,
            comment='Unique username for user identification'
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment='Whether user account is active'
        ),
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether user email is verified'
        ),
        sa.Column(
            'role',
            sa.String(20),
            nullable=False,
            server_default='user',
            comment='User role: user, admin, moderator'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='User status: active, inactive, suspended, deleted'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Account creation timestamp'
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
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.CheckConstraint("role IN ('user', 'admin', 'moderator')", name='ck_users_role_valid'),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'deleted')",
            name='ck_users_status_valid'
        ),
        comment='User accounts with authentication credentials'
    )

    # Create indexes for common queries
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

    # Create refresh_tokens table - for JWT token management
    op.create_table(
        'refresh_tokens',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique token identifier'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id'
        ),
        sa.Column(
            'token',
            sa.String(500),
            nullable=False,
            unique=True,
            comment='The JWT refresh token value (hashed)'
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='When the refresh token expires'
        ),
        sa.Column(
            'is_revoked',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment='Whether token has been revoked'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Token creation timestamp'
        ),
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When token was revoked (if applicable)'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_refresh_tokens_user_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_refresh_tokens_token'),
        comment='JWT refresh token tracking for session management'
    )

    # Create indexes for token lookups
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('ix_refresh_tokens_is_revoked', 'refresh_tokens', ['is_revoked'])


def downgrade() -> None:
    """Drop users and refresh_tokens tables."""

    # Drop refresh_tokens first (has FK to users)
    op.drop_table('refresh_tokens')

    # Then drop users
    op.drop_table('users')

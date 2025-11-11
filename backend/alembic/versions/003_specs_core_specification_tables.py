"""Core Specification Tables - Projects, Sessions, Questions, Specifications

Revision ID: 003
Revises: None
Create Date: 2025-11-11

This is the first migration for the socrates_specs database.
Creates the foundation tables for project specification management and conversation tracking.

Tables created:
- projects: Project metadata, phases, and maturity tracking
- sessions: Conversation sessions within projects
- questions: Questions asked during specification process
- specifications: Project specifications with key-value storage
- conversation_history: Chat history and interactions
- conflicts: Conflicts identified during specification

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '003'
down_revision = None
branch_labels = ('specs',)
depends_on = None


def upgrade() -> None:
    """Create core specification tables for socrates_specs database."""

    # Create projects table - project metadata and state
    op.create_table(
        'projects',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique project identifier (UUID)'
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
            comment='Project name'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Project description'
        ),
        sa.Column(
            'phase',
            sa.String(50),
            nullable=False,
            server_default='discovery',
            comment='Current project phase (discovery, specification, generation, testing, deployment)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='Project status (active, archived, completed, on_hold)'
        ),
        sa.Column(
            'maturity_level',
            sa.Integer(),
            nullable=True,
            comment='Project maturity score (0-100)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Project metadata and custom fields as JSON'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Project creation timestamp'
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
        comment='Project metadata, phases, and maturity tracking'
    )

    # Create indexes for projects
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_phase', 'projects', ['phase'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])

    # Create sessions table - conversation sessions within projects
    op.create_table(
        'sessions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique session identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to users.id in socrates_auth database (no FK constraint - cross-database reference)'
        ),
        sa.Column(
            'title',
            sa.String(255),
            nullable=True,
            comment='Session title or topic'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            comment='Session status (active, archived, completed)'
        ),
        sa.Column(
            'message_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Total messages in session'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Session metadata and custom fields'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Session creation timestamp'
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
            name='fk_sessions_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Conversation sessions within projects'
    )

    # Create indexes for sessions
    op.create_index('ix_sessions_project_id', 'sessions', ['project_id'])
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_sessions_status', 'sessions', ['status'])
    op.create_index('ix_sessions_created_at', 'sessions', ['created_at'])

    # Create questions table - questions asked during specification process
    op.create_table(
        'questions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique question identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'session_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='Reference to sessions.id (optional - question may be from automated flow)'
        ),
        sa.Column(
            'text',
            sa.Text(),
            nullable=False,
            comment='Question text'
        ),
        sa.Column(
            'category',
            sa.String(100),
            nullable=True,
            comment='Question category (functional, non-functional, deployment, etc.)'
        ),
        sa.Column(
            'priority',
            sa.String(20),
            nullable=True,
            server_default='medium',
            comment='Question priority (low, medium, high, critical)'
        ),
        sa.Column(
            'answer',
            sa.Text(),
            nullable=True,
            comment='Answer provided by user or LLM'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            comment='Question status (pending, answered, skipped, resolved)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Question metadata (asked_by, confidence_score, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Question creation timestamp'
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
            name='fk_questions_project_id'
        ),
        sa.ForeignKeyConstraint(
            ['session_id'],
            ['sessions.id'],
            ondelete='SET NULL',
            name='fk_questions_session_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Questions asked during specification process'
    )

    # Create indexes for questions
    op.create_index('ix_questions_project_id', 'questions', ['project_id'])
    op.create_index('ix_questions_session_id', 'questions', ['session_id'])
    op.create_index('ix_questions_status', 'questions', ['status'])
    op.create_index('ix_questions_category', 'questions', ['category'])
    op.create_index('ix_questions_created_at', 'questions', ['created_at'])

    # Create specifications table - project specifications with key-value storage
    op.create_table(
        'specifications',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique specification identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'key',
            sa.String(255),
            nullable=False,
            comment='Specification key (e.g., database, authentication, api_design)'
        ),
        sa.Column(
            'value',
            sa.Text(),
            nullable=True,
            comment='Specification value (detailed specification text or JSON)'
        ),
        sa.Column(
            'type',
            sa.String(100),
            nullable=True,
            comment='Specification type (functional, non-functional, deployment, security, performance)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='draft',
            comment='Status (draft, approved, implemented, deprecated)'
        ),
        sa.Column(
            'version',
            sa.Integer(),
            nullable=False,
            server_default='1',
            comment='Specification version number'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Specification metadata (reviewed_by, approval_date, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Specification creation timestamp'
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
            name='fk_specifications_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'key', 'version', name='uq_specifications_project_key_version'),
        comment='Project specifications with key-value storage'
    )

    # Create indexes for specifications
    op.create_index('ix_specifications_project_id', 'specifications', ['project_id'])
    op.create_index('ix_specifications_key', 'specifications', ['key'])
    op.create_index('ix_specifications_status', 'specifications', ['status'])
    op.create_index('ix_specifications_type', 'specifications', ['type'])
    op.create_index('ix_specifications_created_at', 'specifications', ['created_at'])

    # Create conversation_history table - chat history and interactions
    op.create_table(
        'conversation_history',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique message identifier (UUID)'
        ),
        sa.Column(
            'session_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to sessions.id'
        ),
        sa.Column(
            'role',
            sa.String(20),
            nullable=False,
            comment='Message sender role (user, assistant, system)'
        ),
        sa.Column(
            'content',
            sa.Text(),
            nullable=False,
            comment='Message content'
        ),
        sa.Column(
            'message_type',
            sa.String(50),
            nullable=True,
            comment='Message type (question, answer, clarification, specification, error)'
        ),
        sa.Column(
            'tokens_used',
            sa.Integer(),
            nullable=True,
            comment='Number of tokens used in LLM response'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Message metadata (model, confidence, embedding_id, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Message timestamp'
        ),
        sa.ForeignKeyConstraint(
            ['session_id'],
            ['sessions.id'],
            ondelete='CASCADE',
            name='fk_conversation_history_session_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Chat history and conversation interactions'
    )

    # Create indexes for conversation_history
    op.create_index('ix_conversation_history_session_id', 'conversation_history', ['session_id'])
    op.create_index('ix_conversation_history_role', 'conversation_history', ['role'])
    op.create_index('ix_conversation_history_created_at', 'conversation_history', ['created_at'])

    # Create conflicts table - conflicts identified during specification
    op.create_table(
        'conflicts',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique conflict identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'title',
            sa.String(255),
            nullable=False,
            comment='Conflict title'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Detailed conflict description'
        ),
        sa.Column(
            'type',
            sa.String(100),
            nullable=True,
            comment='Conflict type (requirement_conflict, design_conflict, dependency_conflict, performance_conflict)'
        ),
        sa.Column(
            'severity',
            sa.String(20),
            nullable=False,
            server_default='medium',
            comment='Conflict severity (low, medium, high, critical)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='open',
            comment='Conflict status (open, in_progress, resolved, cancelled)'
        ),
        sa.Column(
            'resolution',
            sa.Text(),
            nullable=True,
            comment='Resolution description'
        ),
        sa.Column(
            'related_specifications',
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
            server_default='{}',
            comment='Array of related specification IDs'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Conflict metadata (identified_by, resolution_date, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Conflict creation timestamp'
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
            name='fk_conflicts_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Conflicts identified during specification process'
    )

    # Create indexes for conflicts
    op.create_index('ix_conflicts_project_id', 'conflicts', ['project_id'])
    op.create_index('ix_conflicts_status', 'conflicts', ['status'])
    op.create_index('ix_conflicts_severity', 'conflicts', ['severity'])
    op.create_index('ix_conflicts_type', 'conflicts', ['type'])
    op.create_index('ix_conflicts_created_at', 'conflicts', ['created_at'])


def downgrade() -> None:
    """Drop core specification tables."""

    # Drop in reverse dependency order
    op.drop_table('conflicts')
    op.drop_table('conversation_history')
    op.drop_table('specifications')
    op.drop_table('questions')
    op.drop_table('sessions')
    op.drop_table('projects')

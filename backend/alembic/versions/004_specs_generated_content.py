"""Generated Content - Projects and Files from Specifications

Revision ID: 004
Revises: 003
Create Date: 2025-11-11

Creates tables for storing generated projects and source code files created from specifications.

Tables created:
- generated_projects: Complete generated project artifacts
- generated_files: Individual source code files within generated projects

Target Database: socrates_specs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create generated content tables for socrates_specs database."""

    # Create generated_projects table - complete generated project artifacts
    op.create_table(
        'generated_projects',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique generated project identifier (UUID)'
        ),
        sa.Column(
            'project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to projects.id'
        ),
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            comment='Generated project name'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Project description'
        ),
        sa.Column(
            'language',
            sa.String(50),
            nullable=True,
            comment='Primary programming language (python, javascript, typescript, java, go, rust, etc.)'
        ),
        sa.Column(
            'framework',
            sa.String(100),
            nullable=True,
            comment='Primary framework (fastapi, django, react, angular, spring, etc.)'
        ),
        sa.Column(
            'version',
            sa.String(20),
            nullable=True,
            comment='Project version (e.g., 1.0.0)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='draft',
            comment='Status (draft, generated, reviewed, deployed, archived)'
        ),
        sa.Column(
            'file_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Total number of generated files'
        ),
        sa.Column(
            'total_lines_of_code',
            sa.Integer(),
            nullable=True,
            comment='Total lines of code in project'
        ),
        sa.Column(
            'structure',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Project structure/folder hierarchy as JSON'
        ),
        sa.Column(
            'configuration',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Project configuration (dependencies, build settings, etc.)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='Generated project metadata (generated_by_model, generation_date, quality_score, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Project generation timestamp'
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
            name='fk_generated_projects_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='Complete generated project artifacts from specifications'
    )

    # Create indexes for generated_projects
    op.create_index('ix_generated_projects_project_id', 'generated_projects', ['project_id'])
    op.create_index('ix_generated_projects_status', 'generated_projects', ['status'])
    op.create_index('ix_generated_projects_language', 'generated_projects', ['language'])
    op.create_index('ix_generated_projects_framework', 'generated_projects', ['framework'])
    op.create_index('ix_generated_projects_created_at', 'generated_projects', ['created_at'])

    # Create generated_files table - individual source code files within generated projects
    op.create_table(
        'generated_files',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Unique generated file identifier (UUID)'
        ),
        sa.Column(
            'generated_project_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment='Reference to generated_projects.id'
        ),
        sa.Column(
            'path',
            sa.String(500),
            nullable=False,
            comment='File path relative to project root (e.g., src/main.py, tests/test_api.py)'
        ),
        sa.Column(
            'filename',
            sa.String(255),
            nullable=False,
            comment='File name with extension'
        ),
        sa.Column(
            'file_type',
            sa.String(50),
            nullable=True,
            comment='File type (python, javascript, json, yaml, dockerfile, etc.)'
        ),
        sa.Column(
            'content',
            sa.Text(),
            nullable=True,
            comment='File content (source code or configuration)'
        ),
        sa.Column(
            'lines_of_code',
            sa.Integer(),
            nullable=True,
            comment='Number of lines in file'
        ),
        sa.Column(
            'purpose',
            sa.String(255),
            nullable=True,
            comment='File purpose/description (e.g., main application, unit tests, configuration)'
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='draft',
            comment='Status (draft, generated, reviewed, approved)'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment='File metadata (checksum, dependencies, test_coverage, etc.)'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='File generation timestamp'
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
            ['generated_project_id'],
            ['generated_projects.id'],
            ondelete='CASCADE',
            name='fk_generated_files_generated_project_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('generated_project_id', 'path', name='uq_generated_files_project_path'),
        comment='Individual source code files within generated projects'
    )

    # Create indexes for generated_files
    op.create_index('ix_generated_files_generated_project_id', 'generated_files', ['generated_project_id'])
    op.create_index('ix_generated_files_path', 'generated_files', ['path'])
    op.create_index('ix_generated_files_file_type', 'generated_files', ['file_type'])
    op.create_index('ix_generated_files_status', 'generated_files', ['status'])
    op.create_index('ix_generated_files_created_at', 'generated_files', ['created_at'])


def downgrade() -> None:
    """Drop generated content tables."""

    # Drop in reverse dependency order
    op.drop_table('generated_files')
    op.drop_table('generated_projects')

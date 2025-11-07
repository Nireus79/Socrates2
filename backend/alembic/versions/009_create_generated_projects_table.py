"""create generated_projects table

Revision ID: 009
Revises: 008
Create Date: 2025-11-07

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
    op.create_table(
        'generated_projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('generation_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_files', sa.Integer(), nullable=False),
        sa.Column('total_lines', sa.Integer(), nullable=False),
        sa.Column('test_coverage', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('traceability_score', sa.Integer(), nullable=True),
        sa.Column('download_url', sa.Text(), nullable=True),
        sa.Column('generation_started_at', sa.DateTime(), nullable=False),
        sa.Column('generation_completed_at', sa.DateTime(), nullable=True),
        sa.Column('generation_status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='generationstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("generation_status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')", name='generated_projects_status_valid'),
        sa.UniqueConstraint('project_id', 'generation_version', name='generated_projects_version_unique')
    )
    op.create_index('ix_generated_projects_project_id', 'generated_projects', ['project_id'])
    op.create_index('ix_generated_projects_status', 'generated_projects', ['generation_status'])
    op.create_index('ix_generated_projects_started_at', 'generated_projects', ['generation_started_at'])


def downgrade() -> None:
    op.drop_index('ix_generated_projects_started_at', table_name='generated_projects')
    op.drop_index('ix_generated_projects_status', table_name='generated_projects')
    op.drop_index('ix_generated_projects_project_id', table_name='generated_projects')
    op.drop_table('generated_projects')
    op.execute('DROP TYPE generationstatus')

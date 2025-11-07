"""create generated_files table

Revision ID: 010
Revises: 009
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'generated_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('generated_project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_content', sa.Text(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('spec_ids', postgresql.ARRAY(sa.String(length=36)), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['generated_project_id'], ['generated_projects.id'], ondelete='CASCADE')
    )
    op.create_index('ix_generated_files_project_id', 'generated_files', ['generated_project_id'])
    op.create_index('ix_generated_files_file_path', 'generated_files', ['file_path'])


def downgrade() -> None:
    op.drop_index('ix_generated_files_file_path', table_name='generated_files')
    op.drop_index('ix_generated_files_project_id', table_name='generated_files')
    op.drop_table('generated_files')

"""create knowledge_base_documents table

Revision ID: 014
Revises: 013
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade():
    """Create knowledge_base_documents table"""
    if not _should_run():
        return

    op.create_table(
        'knowledge_base_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, comment='Foreign key to projects table'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='References users(id) in socrates_auth'),
        sa.Column('filename', sa.String(length=255), nullable=False, comment='Original filename'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='File size in bytes'),
        sa.Column('content_type', sa.String(length=100), nullable=False, comment='MIME type'),
        sa.Column('content', sa.Text(), nullable=True, comment='Extracted text content'),
        sa.Column('embedding', sa.Text(), nullable=True, comment='Sentence embedding as JSON array (384 dimensions)'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Timestamp when document was uploaded'),
    )

    # Create indexes
    op.create_index('idx_knowledge_base_documents_project_id', 'knowledge_base_documents', ['project_id'])
    op.create_index('idx_knowledge_base_documents_user_id', 'knowledge_base_documents', ['user_id'])
    op.create_index('idx_knowledge_base_documents_uploaded_at', 'knowledge_base_documents', ['uploaded_at'], postgresql_using='btree', postgresql_ops={'uploaded_at': 'DESC'})


def downgrade():
    """Drop knowledge_base_documents table"""
    if not _should_run():
        return

    op.drop_index('idx_knowledge_base_documents_uploaded_at', table_name='knowledge_base_documents')
    op.drop_index('idx_knowledge_base_documents_user_id', table_name='knowledge_base_documents')
    op.drop_index('idx_knowledge_base_documents_project_id', table_name='knowledge_base_documents')
    op.drop_table('knowledge_base_documents')

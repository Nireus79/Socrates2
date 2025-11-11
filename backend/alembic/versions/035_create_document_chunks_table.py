"""Create document chunks table for RAG embeddings.

Revision ID: 035_create_document_chunks_table
Revises: 034_create_analytics_metrics_tables
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os


# revision identifiers, used by Alembic.
revision = '035_create_document_chunks_table'
down_revision = '034_create_analytics_metrics_tables'
branch_labels = None
depends_on = None


def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url


def upgrade() -> None:
    """Create document_chunks table in specs database."""
    if not _should_run():
        return

    # Create document_chunks table for storing document chunks with embeddings
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding_vector', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_base_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index')
    )

    # Create indexes for efficient querying
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_chunk_index', 'document_chunks', ['chunk_index'])


def downgrade() -> None:
    """Drop document_chunks table."""
    if not _should_run():
        return

    op.drop_index('ix_document_chunks_chunk_index', table_name='document_chunks')
    op.drop_index('ix_document_chunks_document_id', table_name='document_chunks')
    op.drop_table('document_chunks')

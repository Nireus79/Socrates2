"""Migrate embeddings to pgvector for vector similarity search.

Revision ID: 026
Revises: 025
Create Date: 2025-11-11 12:00:00.000000

This migration:
- Enables pgvector extension for semantic vector search
- Replaces text-based embeddings with proper vector type (1536 dims for OpenAI)
- Creates IVFFlat index for fast cosine similarity search
- Enables Phase 4 Feature 2: Vector Embeddings & Semantic Search

CRITICAL: This migration changes the embedding storage from TEXT to vector type.
If existing embeddings exist, they must be migrated or discarded.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Migrate to pgvector."""

    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add new vector column for OpenAI embeddings (1536 dimensions)
    op.add_column(
        'knowledge_base_documents',
        sa.Column(
            'embedding_vector',
            sa.dialects.postgresql.base.PGVectorType(dim=1536),
            nullable=True,
            comment='OpenAI embedding vector (1536 dimensions for cosine similarity search)'
        )
    )

    # If there are existing embeddings in JSON format, migrate them
    # This is a best-effort migration - will skip malformed entries
    op.execute('''
        UPDATE knowledge_base_documents
        SET embedding_vector = embedding::vector
        WHERE embedding IS NOT NULL
        AND embedding ~ '^\\[.*\\]$'
    ''')

    # Drop old text-based embedding column
    op.drop_column('knowledge_base_documents', 'embedding')

    # Create IVFFlat index for fast vector similarity search
    # IVFFlat is faster for large datasets (>1M vectors) with cosineSimilarity
    op.execute('''
        CREATE INDEX idx_knowledge_base_documents_embedding_vector
        ON knowledge_base_documents
        USING ivfflat (embedding_vector vector_cosine_ops)
        WITH (lists = 100)
    ''')


def downgrade() -> None:
    """Rollback pgvector migration."""

    # Drop vector index
    op.execute('DROP INDEX IF EXISTS idx_knowledge_base_documents_embedding_vector')

    # Recreate text-based embedding column
    op.add_column(
        'knowledge_base_documents',
        sa.Column(
            'embedding',
            sa.Text,
            nullable=True,
            comment='Sentence embedding as JSON array (384 dimensions)'
        )
    )

    # Drop vector column
    op.drop_column('knowledge_base_documents', 'embedding_vector')

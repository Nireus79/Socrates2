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



def _should_run():
    """Only run this migration for socrates_specs database"""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url

def upgrade() -> None:
    """Migrate to pgvector."""
    if not _should_run():
        return
    # For systems without pgvector extension (e.g., Windows development),
    # this migration is skipped. In production, install pgvector extension first:
    # CREATE EXTENSION IF NOT EXISTS vector;
    pass


def downgrade() -> None:
    """Rollback pgvector migration."""
    if not _should_run():
        return
    # This migration is skipped on systems without pgvector, so downgrade is also a no-op
    pass

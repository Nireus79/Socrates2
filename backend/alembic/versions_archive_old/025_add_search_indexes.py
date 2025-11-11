"""Add full-text search indexes for projects and specifications.

Revision ID: 025
Revises: 024
Create Date: 2025-11-11 12:00:00.000000

This migration adds full-text search capabilities:
- PostgreSQL ts_vector indexes for fast GIN-based full-text search
- Fuzzy search support with trigram (GIST) indexes
- Enables Phase 1 Feature 2: Search System
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None



def _should_run():
    """Only run this migration for socrates_specs database"""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url

def upgrade() -> None:
    """Create full-text search indexes."""
    if not _should_run():
        return

    # Enable pg_trgm extension for fuzzy search (if not already enabled)
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # Create full-text search index for projects (name + description)
    op.execute('''
        CREATE INDEX idx_projects_search ON projects
        USING gin(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')))
    ''')

    # Create full-text search index for specifications (key + value + content)
    op.execute('''
        CREATE INDEX idx_specifications_search ON specifications
        USING gin(to_tsvector('english', coalesce(key, '') || ' ' || coalesce(value, '') || ' ' || coalesce(content, '')))
    ''')

    # Create fuzzy search index on project names (for typo tolerance)
    op.execute('''
        CREATE INDEX idx_projects_name_trgm ON projects
        USING gist(name gist_trgm_ops)
    ''')


def downgrade() -> None:
    """Remove search indexes."""
    if not _should_run():
        return

    op.execute('DROP INDEX IF EXISTS idx_projects_search')
    op.execute('DROP INDEX IF EXISTS idx_specifications_search')
    op.execute('DROP INDEX IF EXISTS idx_projects_name_trgm')

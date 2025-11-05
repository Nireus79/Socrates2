# MIGRATION STRATEGY

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟡 MEDIUM - Plan before Phase 1, implement per phase

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Phase Transition Strategy](#phase-transition-strategy)
3. [Database Migrations](#database-migrations)
4. [API Versioning](#api-versioning)
5. [Data Migration Scripts](#data-migration-scripts)
6. [Backward Compatibility](#backward-compatibility)
7. [Rollback Strategy](#rollback-strategy)

---

## OVERVIEW

**Goal:** Smooth transitions between phases without breaking existing functionality.

###

 Principles

1. **Non-Breaking Changes**: Add features, don't modify existing
2. **Versioned APIs**: Old clients continue working
3. **Data Integrity**: Never lose data during migrations
4. **Rollback-Safe**: Every migration can be rolled back

---

## PHASE TRANSITION STRATEGY

### Phase 0 → Phase 1 (MVP Core)

**Changes:**
- Add `user_rules` table
- Add conflict detection service
- Add quality control validation

**Migration:**
```bash
alembic revision -m "Add user_rules table for Quality Control"
alembic upgrade head
```

**Compatibility:** Fully backward compatible (new tables only)

---

### Phase 1 → Phase 2 (Polish MVP)

**Changes:**
- Add `test_results` table
- Add real-time compatibility testing

**Migration:**
```bash
alembic revision -m "Add test_results table for compatibility testing"
alembic upgrade head
```

**Compatibility:** Fully backward compatible

---

### Phase 2 → Phase 3 (Multi-LLM)

**Changes:**
- Add `api_keys` table (socrates_auth)
- Add `llm_usage_tracking` table (socrates_specs)
- Add LLM provider selection UI

**Migration:**
```bash
alembic revision -m "Add api_keys and llm_usage_tracking tables"
alembic upgrade head
```

**Compatibility:** Fully backward compatible (Claude continues as default)

---

### Phase 3 → Phase 4 (Code Generation)

**Changes:**
- Add `generated_projects` table
- Add `generated_files` table
- Add generation pipeline

**Migration:**
```bash
alembic revision -m "Add project generation tables"
alembic upgrade head
```

**Compatibility:** Fully backward compatible (generation is opt-in)

---

### Phase 4 → Phase 5 (User Learning)

**Changes:**
- Add `user_behavior_patterns` table
- Add `question_effectiveness` table
- Add `knowledge_base_documents` table
- Enable pgvector extension
- Add vector embedding column

**Migration:**
```bash
alembic revision -m "Enable pgvector extension"
alembic revision -m "Add user learning tables"
alembic revision -m "Add embedding column to knowledge_base_documents"
alembic upgrade head
```

**Compatibility:** Mostly backward compatible (embeddings optional)

---

### Phase 5 → Phase 6 (Team Collaboration)

**Changes:**
- Add `teams` table (socrates_auth)
- Add `team_members` table (socrates_auth)
- Add `team_invitations` table (socrates_auth)
- Add `project_shares` table (socrates_specs)

**Migration:**
```bash
alembic revision -m "Add team collaboration tables"
alembic upgrade head
```

**Compatibility:** Fully backward compatible (teams optional, single-user continues working)

---

## DATABASE MIGRATIONS

### Migration Template

```python
# alembic/versions/xxx_description.py
"""Add new_table for Phase X feature

Revision ID: abc123
Revises: previous_revision
Create Date: 2025-11-05 10:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = 'abc123'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    """Apply migration."""
    op.create_table(
        'new_table',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id')),
        sa.Column('data', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    op.create_index('idx_new_table_project_id', 'new_table', ['project_id'])

def downgrade():
    """Rollback migration."""
    op.drop_index('idx_new_table_project_id', 'new_table')
    op.drop_table('new_table')
```

---

## API VERSIONING

### URL Versioning

```python
# api/v1/routes/projects.py
from fastapi import APIRouter

router_v1 = APIRouter(prefix="/api/v1")

@router_v1.get("/projects")
async def list_projects_v1():
    """Version 1 API endpoint."""
    pass

# api/v2/routes/projects.py
router_v2 = APIRouter(prefix="/api/v2")

@router_v2.get("/projects")
async def list_projects_v2():
    """Version 2 API endpoint with new features."""
    pass

# Both versions coexist:
# /api/v1/projects (old clients)
# /api/v2/projects (new clients)
```

---

## DATA MIGRATION SCRIPTS

### Example: Backfill Embeddings (Phase 5)

```python
# scripts/backfill_embeddings.py
"""
Backfill embeddings for existing knowledge base documents.

Run after Phase 5 migration to add embeddings to existing documents.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
from models.knowledge_base import KnowledgeBaseDocument
from tqdm import tqdm

def backfill_embeddings():
    """Backfill embeddings for all documents."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Load embedding model
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    # Get documents without embeddings
    documents = session.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.embedding == None
    ).all()

    print(f"Backfilling embeddings for {len(documents)} documents...")

    for doc in tqdm(documents):
        # Generate embedding
        embedding = embedder.encode(doc.content)
        doc.embedding = embedding.tolist()

    # Commit in batches
    session.commit()
    print("Backfill complete!")

if __name__ == "__main__":
    backfill_embeddings()
```

---

## BACKWARD COMPATIBILITY

### Guarantees

✅ **Guaranteed Compatible:**
- Adding new tables
- Adding new columns with defaults
- Adding new API endpoints
- Adding new LLM providers

❌ **Breaking Changes (Avoid!):**
- Renaming tables/columns
- Dropping tables/columns
- Changing column types
- Removing API endpoints

### Deprecation Policy

```python
# api/v1/routes/deprecated.py

@router.get("/old-endpoint")
@deprecated(
    since="2.1.0",
    alternative="/api/v2/new-endpoint",
    removal="3.0.0"
)
async def old_endpoint():
    """
    DEPRECATED: Use /api/v2/new-endpoint instead.
    Will be removed in version 3.0.0.
    """
    # Still functional, but logs warning
    logger.warning("old_endpoint called (deprecated since 2.1.0)")
    return {"warning": "This endpoint is deprecated"}
```

---

## ROLLBACK STRATEGY

### Safe Rollback Process

```bash
# 1. Check current migration
alembic current

# 2. Rollback last migration
alembic downgrade -1

# 3. Rollback to specific revision
alembic downgrade abc123

# 4. Rollback all migrations (DANGEROUS!)
alembic downgrade base
```

### Rollback Testing

```python
# tests/test_migrations.py

def test_migration_rollback():
    """Test migration can be safely rolled back."""

    # Apply migration
    alembic_upgrade()

    # Create test data
    create_test_data()

    # Rollback migration
    alembic_downgrade()

    # Verify data integrity (if applicable)
    verify_data_integrity()
```

---

**Document Status:** ✅ Complete
**Date:** November 5, 2025

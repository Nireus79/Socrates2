
# Phase 1: Production Foundation Implementation Guide

**Duration:** 5 weeks (35 days)
**Priority:** CRITICAL (production blockers & architecture fixes)
**Features:** Architecture Fixes (7d) | Error Tracking (8d) | Search System (15d) | Background Jobs (5d)

---

## Overview

Make Socrates2 production-ready by:
1. **Fixing critical architecture gaps** (pgvector, subscription fields, analytics tables)
2. Error monitoring and alerting (Sentry)
3. Full-text search with autocomplete
4. Background job scheduler for async tasks

**Dependencies:** PostgreSQL 17 (already installed)

---

## Week 0: Critical Architecture Fixes (7 days)

### ⚠️ Why This Week Is Needed

Current architecture has **3 critical gaps** that block later phases:
1. **Vector embeddings stored as TEXT** - can't do semantic search
2. **No subscription fields on User** - Phase 2 monetization blocked
3. **No analytics tables** - Phase 1 Feature 3 (background jobs) blocked

**If we skip Week 0:** We'll need painful rework in later phases.
**By fixing Week 0:** All future phases have solid foundation.

---

### Migration 1: Add Full-Text Search Indexes (2 days)

**File:** `backend/alembic/versions/025_add_search_indexes.py`

Creates GIN indexes for full-text search on projects and specifications:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_projects_search ON projects USING gin(...);
CREATE INDEX idx_specifications_search ON specifications USING gin(...);
CREATE INDEX idx_projects_name_trgm ON projects USING gist(...);
```

**Impact:** Enables Phase 1 Feature 2 (Search System) <500ms queries

---

### Migration 2: Migrate to pgvector (2 days)

**File:** `backend/alembic/versions/026_migrate_to_pgvector.py`

⚠️ **CRITICAL:** Changes embeddings from TEXT to native vector type (1536 dims for OpenAI)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE knowledge_base_documents ADD COLUMN embedding_vector vector(1536);
CREATE INDEX ... USING ivfflat (embedding_vector vector_cosine_ops);
ALTER TABLE knowledge_base_documents DROP COLUMN embedding;
```

**Why 1536?** OpenAI standard. **Why IVFFlat?** Fast for <10M vectors.

**Impact:** Enables Phase 4 (Knowledge Base & RAG) semantic search

---

### Migration 3: Add Subscription Fields to User (1.5 days)

**File:** `backend/alembic/versions/027_add_user_subscription_fields.py`

Adds billing fields: `subscription_tier`, `stripe_customer_id`, `trial_ends_at`, `subscription_status`

**Impact:** Enables Phase 2 (Monetization & Billing) without schema rework

---

### Migration 4: Add Analytics Tables (1.5 days)

**File:** `backend/alembic/versions/028_add_analytics_tables.py`

Creates `analytics_events` (raw events) and `project_metrics` (daily aggregates) tables

**Impact:** Enables Phase 1 Feature 3 (Background Jobs & Analytics)

---

### Week 0 Execution Checklist

- [ ] Run all 4 migrations: `alembic upgrade head`
- [ ] Verify pgvector installed: `SELECT extname FROM pg_extension WHERE extname='vector'`
- [ ] Verify search indexes: `\d+ projects`, `\d+ specifications`
- [ ] Verify subscription fields: `\d+ users` (should show new columns)
- [ ] Verify analytics tables: `\dt analytics_events project_metrics`
- [ ] Performance test: search query <500ms with 1000 projects
- [ ] Test vector column: insert test embedding, verify IVFFlat index

---

## Feature 1: Error Tracking Integration (8 days)

### Purpose
Capture and monitor application errors in production. Currently there's no visibility into failures.

### Pre-Implementation Checks

#### 1. Review Exception Handling
```bash
# Check how exceptions are currently handled
grep -r "except.*:" backend/app --include="*.py" | head -20

# Look for swallowed exceptions (bare except:)
grep -r "except:" backend/app --include="*.py"

# Check logging configuration
cat backend/app/core/config.py | grep -A 10 "LOG_LEVEL"
```

**Questions to Answer:**
- Are there bare `except:` blocks that swallow errors?
- Is logging configured for all modules?
- Are API errors properly propagated or silently caught?

#### 2. Check Existing Error Handling
- Review `backend/app/main.py` line 52-83 (lifespan/startup)
- Check if global exception handler exists
- Verify error logging in all API endpoints

#### 3. Review Security Settings
- Ensure no sensitive data in error messages
- Check if passwords are logged anywhere
- Verify API keys are not in tracebacks

### Architecture

#### Sentry Integration Points

```
┌─────────────────────────────────────────┐
│  FastAPI Application                    │
│  ├─ Before Send Hook                    │
│  │  └─ Scrub passwords, tokens, keys    │
│  ├─ Exception Handlers                  │
│  │  └─ Capture 500 errors               │
│  ├─ Integration Events                  │
│  │  └─ Tag with release version         │
│  └─ Performance Monitoring              │
│     └─ Track slow requests (>2000ms)    │
└─────────────────────────────────────────┘
              ↓
         Sentry DSN
              ↓
    Error Aggregation & Alerts
```

#### Data Flow
1. Exception raised in API endpoint
2. FastAPI exception handler catches it
3. Sentry SDK intercepts
4. `before_send` hook scrubs sensitive data
5. Error sent to Sentry cloud
6. Alert triggered if threshold exceeded

### Implementation Steps

#### Step 1: Install Dependencies (0.5 day)
```bash
pip install sentry-sdk==1.40.0
# Frontend (when needed):
npm install @sentry/react @sentry/tracing
```

#### Step 2: Initialize Sentry (1 day)

**File:** `backend/app/core/sentry_config.py` (NEW)
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from ..core.config import settings

def init_sentry():
    """Initialize Sentry error tracking."""
    if not settings.SENTRY_DSN:
        return  # Skip if DSN not configured

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlAlchemyIntegration(),
            LoggingIntegration(level=settings.LOG_LEVEL),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        environment=settings.ENVIRONMENT,
        release=settings.APP_VERSION,  # From git: git rev-parse --short HEAD
        before_send=scrub_sensitive_data,
    )

def scrub_sensitive_data(event, hint):
    """Remove passwords, tokens, keys from error data."""
    # Remove from exception message
    if 'exception' in event:
        for exc in event['exception'].get('values', []):
            if 'value' in exc:
                exc['value'] = scrub_string(exc['value'])

    # Remove from request body/headers
    if 'request' in event:
        if 'headers' in event['request']:
            # Remove Authorization, API keys
            for key in ['Authorization', 'X-API-Key', 'X-Auth-Token']:
                event['request']['headers'].pop(key, None)

    return event

def scrub_string(s):
    """Scrub sensitive patterns from string."""
    import re
    # Remove passwords: password="xxx"
    s = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', 'password="***"', s, flags=re.I)
    # Remove tokens: token="xxx"
    s = re.sub(r'(token|api_key)["\']?\s*[:=]\s*["\']?[^"\'\s,}]+', r'\1="***"', s, flags=re.I)
    return s
```

**File:** `backend/app/core/config.py` (UPDATE)
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Sentry Configuration
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry error tracking DSN")
    APP_VERSION: str = Field(default="0.1.0", description="App version for error tracking")

    # Performance Monitoring
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, description="0-1: % of transactions to trace")
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.1, description="0-1: % to profile")
```

**File:** `backend/app/main.py` (UPDATE)
```python
from .core.sentry_config import init_sentry

def create_app(...):
    # Initialize Sentry before creating app
    init_sentry()

    # ... rest of app creation ...
```

#### Step 3: Exception Handler (1 day)

**File:** `backend/app/api/error_handlers.py` (NEW)
```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions globally."""
    # Capture in Sentry
    sentry_sdk.capture_exception(exc)

    # Log details
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        }
    )

    # Return generic error (don't leak details to client)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "error_id": sentry_sdk.get_last_event_id(),  # Track in Sentry
        }
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )
```

**Register in `main.py`:**
```python
from .api.error_handlers import general_exception_handler, validation_error_handler

app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
```

#### Step 4: Performance Monitoring (2 days)

**Add to `main.py`:**
```python
from sentry_sdk import start_span

@app.middleware("http")
async def add_performance_tracing(request: Request, call_next):
    """Track request performance."""
    with start_span(op="http.request", description=f"{request.method} {request.url.path}"):
        response = await call_next(request)

        # Track response time
        if hasattr(response, "headers"):
            response.headers["X-Response-Time"] = str(response.headers.get("X-Response-Time", 0))

        return response
```

**Configuration in Sentry:**
- Go to Project Settings → Performance
- Set response time threshold: 2000ms (alert if exceeded)
- Set error rate threshold: 5% (alert if exceeded)

#### Step 5: Release Tagging (1 day)

**In CI/CD pipeline (or startup):**
```python
import subprocess

def get_git_hash():
    """Get current git commit hash."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"]
        ).decode().strip()
    except:
        return "unknown"

# In config.py:
APP_VERSION = get_git_hash()  # Set in Sentry init
```

**Benefits:**
- Link errors to specific commits
- Track error rate across deployments
- Rollback detection (error spike after deploy)

#### Step 6: Environment Variables (0.5 day)

**`.env` file:**
```ini
# Sentry Configuration
SENTRY_DSN=https://xxx@o123.ingest.sentry.io/456
APP_VERSION=abc1234
SENTRY_ENVIRONMENT=production  # or development, staging
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**For development:**
```ini
SENTRY_DSN=  # Leave blank to disable in development
```

#### Step 7: Testing (1 day)

**Manual Testing:**
```bash
# 1. Trigger a test error
curl -X POST http://localhost:8000/api/v1/test-error

# 2. Check Sentry dashboard - should see error with:
#    - Stack trace
#    - Breadcrumbs
#    - Release version
#    - Environment
#    - No sensitive data

# 3. Verify scrubbing:
#    - Search for "password" in error → should show "***"
#    - Search for "token" → should show "***"

# 4. Test performance monitoring:
#    - Make slow request
#    - Check Sentry → Performance → find slow transaction
#    - Verify timing >2000ms triggers alert
```

**Unit Tests:**
```python
# tests/test_sentry_config.py
def test_scrub_password():
    event = {"exception": {"values": [{"value": 'password="secret"'}]}}
    result = scrub_sensitive_data(event, {})
    assert "secret" not in str(result)
    assert "***" in str(result)

def test_scrub_token():
    event = {"exception": {"values": [{"value": 'api_key="sk-123"'}]}}
    result = scrub_sensitive_data(event, {})
    assert "sk-123" not in str(result)
```

### Database Changes
**None** - Sentry is external service

### API Endpoints
**None** - Sentry integration doesn't expose new endpoints

### Testing Checklist

- [ ] Error captured in Sentry with full stack trace
- [ ] Sensitive data (passwords, tokens) scrubbed from errors
- [ ] Release version tagged correctly
- [ ] Performance monitoring tracks response times
- [ ] Alerts configured for error rate >5%
- [ ] Alerts configured for response time >2000ms
- [ ] Slow queries identified and tracked
- [ ] Breadcrumbs capture user actions before error
- [ ] Source maps uploaded (for frontend, later)

### Dependencies

```toml
[dependencies]
sentry-sdk = "1.40.0"
```

---

## Feature 2: Search System (15 days)

### Purpose
Enable users to find projects, specifications, and code efficiently.

**Current State:** Basic PostgreSQL search exists in `backend/app/api/search.py`
**Gap:** No autocomplete, no filters, permission issues

### Pre-Implementation Checks

#### 1. Check Database Type

```bash
# Check what database is configured
grep "DATABASE_URL" backend/.env

# Check alembic for database dialect
grep "sqlalchemy.url" backend/alembic.ini
```

**Critical Decision:**
- If SQLite: Need FTS5 virtual tables
- If PostgreSQL: Can use ts_vector + GIN index

**Current Status:** Need to verify in .env

#### 2. Review Existing Search Code

```bash
# Check existing search implementation
cat backend/app/api/search.py

# Check for existing indexes
grep -r "create.*index" backend/alembic/versions --include="*.py" | head -20
```

**Questions:**
- Does PostgreSQL have `pg_trgm` extension? (for fuzzy search)
- Are there indexes on searchable columns?
- Does existing search respect permissions?

#### 3. Check Models for Searchable Fields

```python
# These should be searchable:
Project.name, Project.description
Specification.content, Specification.key, Specification.value
GeneratedFile.file_content (maybe)
```

### Architecture

#### Search Strategy

**Option A: Full-Text Search (Recommended)**
- PostgreSQL: Use `ts_vector` (fast, native)
- SQLite: Use FTS5 virtual tables

**Option B: Elasticsearch (Future)**
- For very large deployments (100k+ projects)
- Overkill for MVP

**Option C: Algolia (Future)**
- Managed service, expensive
- Best for high-traffic SaaS

**Recommendation:** PostgreSQL + ts_vector (if already using PG) or SQLite FTS5

```
User Input
    ↓
SearchService.search()
    ├─ Tokenize query
    ├─ Check permissions
    ├─ Query full-text indexes
    ├─ Rank by relevance
    └─ Apply filters (date, status, owner)
    ↓
Results (up to 50, paginated)
```

### Implementation Steps

#### Step 1: Database Preparation (2 days)

**Check database type:**
```bash
# If PostgreSQL:
psql -d socrates_specs -c "SELECT version();"

# If SQLite:
sqlite3 socrates_specs.db ".database"
```

**For PostgreSQL (Recommended):**

```sql
-- Enable full-text search extension (if not exists)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create full-text search indexes
CREATE INDEX idx_projects_search ON projects USING gin(
    to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))
);

CREATE INDEX idx_specifications_search ON specifications USING gin(
    to_tsvector('english', coalesce(key, '') || ' ' || coalesce(value, '') || ' ' || coalesce(content, ''))
);

-- Optional: Fuzzy search index (for typos)
CREATE INDEX idx_projects_name_trgm ON projects USING gist(name gist_trgm_ops);
```

**For SQLite:**

```sql
-- Create FTS5 virtual tables
CREATE VIRTUAL TABLE projects_fts USING fts5(
    name,
    description,
    content=projects,
    content_rowid=id
);

CREATE VIRTUAL TABLE specifications_fts USING fts5(
    key,
    value,
    content,
    project_id,
    content=specifications,
    content_rowid=id
);

-- Create triggers to keep FTS tables in sync
CREATE TRIGGER projects_ai AFTER INSERT ON projects BEGIN
    INSERT INTO projects_fts VALUES (new.id, new.name, new.description);
END;

CREATE TRIGGER projects_ad AFTER DELETE ON projects BEGIN
    DELETE FROM projects_fts WHERE rowid = old.id;
END;
```

**Migration file:** `backend/alembic/versions/025_add_search_indexes.py`

#### Step 2: SearchService (3 days)

**File:** `backend/app/services/search_service.py` (NEW)

```python
from typing import List, Optional
from sqlalchemy import text, or_, and_
from sqlalchemy.orm import Session
from ..models import Project, Specification
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Full-text search across projects and specifications."""

    async def search_projects(
        self,
        db: Session,
        query: str,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict] = None
    ) -> tuple[List[Project], int]:
        """
        Search projects by name and description.

        Args:
            query: Search query
            user_id: Filter to user's projects
            skip: Pagination offset
            limit: Results per page (max 50)
            filters: Optional filters {status, phase, min_maturity}

        Returns:
            (results, total_count)
        """
        q = db.query(Project).filter(Project.user_id == user_id)

        # Full-text search
        if query:
            search_filter = or_(
                Project.name.ilike(f"%{query}%"),
                Project.description.ilike(f"%{query}%")
            )
            q = q.filter(search_filter)

        # Apply filters
        if filters:
            if "status" in filters:
                q = q.filter(Project.status == filters["status"])
            if "phase" in filters:
                q = q.filter(Project.current_phase == filters["phase"])
            if "min_maturity" in filters:
                q = q.filter(Project.maturity_score >= filters["min_maturity"])

        # Count total before pagination
        total = q.count()

        # Paginate and sort by relevance
        results = q.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()

        return results, total

    async def search_specifications(
        self,
        db: Session,
        query: str,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict] = None
    ) -> tuple[List[Specification], int]:
        """Search specifications."""
        q = db.query(Specification).join(Project).filter(
            Project.user_id == user_id,
            Specification.is_current == True
        )

        if project_id:
            q = q.filter(Specification.project_id == project_id)

        # Full-text search
        if query:
            search_filter = or_(
                Specification.key.ilike(f"%{query}%"),
                Specification.value.ilike(f"%{query}%"),
                Specification.content.ilike(f"%{query}%")
            )
            q = q.filter(search_filter)

        # Filters
        if filters and "category" in filters:
            q = q.filter(Specification.category == filters["category"])
        if filters and "min_confidence" in filters:
            q = q.filter(Specification.confidence >= filters["min_confidence"])

        total = q.count()
        results = q.order_by(Specification.updated_at.desc()).offset(skip).limit(limit).all()

        return results, total

    async def autocomplete(
        self,
        db: Session,
        query: str,
        user_id: UUID,
        type: str = "projects",  # "projects", "specifications", "all"
        limit: int = 10
    ) -> List[dict]:
        """
        Get autocomplete suggestions.

        Returns:
            [{name, id, type, description}]
        """
        results = []

        if type in ["projects", "all"]:
            projects = db.query(Project.id, Project.name).filter(
                Project.user_id == user_id,
                Project.name.ilike(f"{query}%")  # Prefix match for fast autocomplete
            ).limit(limit).all()
            results.extend([
                {"name": p[1], "id": str(p[0]), "type": "project"}
                for p in projects
            ])

        if type in ["specifications", "all"]:
            specs = db.query(Specification.id, Specification.key).filter(
                Specification.key.ilike(f"{query}%")
            ).limit(limit).all()
            results.extend([
                {"name": s[1], "id": str(s[0]), "type": "specification"}
                for s in specs
            ])

        return results[:limit]
```

#### Step 3: API Endpoints (4 days)

**File:** `backend/app/api/search_v2.py` (NEW - improved version)

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from ..core.dependencies import get_db_specs
from ..core.security import get_current_active_user
from ..models import User
from ..services.search_service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])
search_service = SearchService()

class SearchResultProject(BaseModel):
    id: str
    name: str
    description: Optional[str]
    maturity_score: int
    created_at: str

class SearchResultSpec(BaseModel):
    id: str
    key: str
    value: str
    category: str
    project_id: str

class SearchResponse(BaseModel):
    query: str
    results: List[dict]  # Union of project/spec results
    total: int
    took_ms: float

class AutocompleteResponse(BaseModel):
    suggestions: List[dict]

@router.get("/projects", response_model=SearchResponse)
async def search_projects(
    q: str = Query(..., min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    status: Optional[str] = None,
    phase: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """
    Search projects by name and description.

    Query parameters:
    - q: Search query (required)
    - skip: Pagination offset (default 0)
    - limit: Results per page, max 50 (default 20)
    - status: Filter by status (active, archived)
    - phase: Filter by phase (discovery, design, implementation)
    """
    import time
    start = time.time()

    filters = {}
    if status:
        filters["status"] = status
    if phase:
        filters["phase"] = phase

    results, total = await search_service.search_projects(
        db=db,
        query=q,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        filters=filters
    )

    return {
        "query": q,
        "results": [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "maturity_score": r.maturity_score,
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ],
        "total": total,
        "took_ms": (time.time() - start) * 1000
    }

@router.get("/specifications", response_model=SearchResponse)
async def search_specifications(
    q: str = Query(..., min_length=1),
    project_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """Search specifications across projects."""
    import time
    start = time.time()

    project_uuid = None
    if project_id:
        try:
            project_uuid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id")

    filters = {}
    if category:
        filters["category"] = category

    results, total = await search_service.search_specifications(
        db=db,
        query=q,
        user_id=current_user.id,
        project_id=project_uuid,
        skip=skip,
        limit=limit,
        filters=filters
    )

    return {
        "query": q,
        "results": [
            {
                "id": str(r.id),
                "key": r.key,
                "value": r.value,
                "category": r.category,
                "project_id": str(r.project_id)
            }
            for r in results
        ],
        "total": total,
        "took_ms": (time.time() - start) * 1000
    }

@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=50),
    type: str = Query("all", regex="^(projects|specifications|all)$"),
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """Get autocomplete suggestions for projects and specifications."""
    suggestions = await search_service.autocomplete(
        db=db,
        query=q,
        user_id=current_user.id,
        type=type,
        limit=limit
    )

    return {"suggestions": suggestions}
```

**Register in `main.py`:**
```python
from .api import search_v2
app.include_router(search_v2.router)
```

#### Step 4: CLI Integration (2 days)

**File:** `Socrates.py` (UPDATE - add search commands)

```python
# Add to CLI commands
elif command.startswith("/search"):
    self._handle_search(command)

def _handle_search(self, command: str):
    """Handle /search command."""
    parts = command.split(maxsplit=1)
    if len(parts) < 2:
        self.console.print("[yellow]/search <query>[/yellow]")
        return

    query = parts[1]

    try:
        result = self.api.post(
            "/search/projects",
            params={"q": query, "limit": 10}
        )

        if result.get("results"):
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Name", style="cyan")
            table.add_column("Maturity", style="green")
            table.add_column("ID", style="dim")

            for proj in result["results"]:
                table.add_row(
                    proj["name"],
                    f"{proj['maturity_score']}%",
                    proj["id"][:8]
                )

            self.console.print(table)
            self.console.print(f"\n[dim]{result['total']} total results ({result['took_ms']:.0f}ms)[/dim]")
        else:
            self.console.print("[yellow]No results found[/yellow]")

    except Exception as e:
        self.console.print(f"[red]Search failed: {e}[/red]")
```

#### Step 5: Caching Layer (2 days)

**For autocomplete performance (optional, but recommended):**

```python
# Implement simple in-memory cache
from functools import lru_cache
import hashlib

class SearchCache:
    def __init__(self, ttl_seconds=300):
        self.ttl = ttl_seconds
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str):
        """Get cached result if not expired."""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            del self.cache[key]
        return None

    def set(self, key: str, value):
        """Cache result."""
        self.cache[key] = value
        self.timestamps[key] = time.time()
```

### Database Changes

**Migration:** `backend/alembic/versions/025_add_search_indexes.py`

See "Step 1" above for SQL

### Testing Checklist

- [ ] Search finds projects by name
- [ ] Search finds specifications by key/value
- [ ] Permission filtering: user only sees own projects
- [ ] Filters work (status, phase, category)
- [ ] Autocomplete returns suggestions quickly (<100ms)
- [ ] Pagination works (skip/limit)
- [ ] Search is case-insensitive
- [ ] Special characters handled (quotes, etc.)
- [ ] Performance: search completes <500ms for 1000 projects
- [ ] CLI commands work: `/search <query>`

### Performance Targets

- Search latency: <500ms
- Autocomplete latency: <100ms
- Index size: <5% of data size
- Query per second: 100+ qps

---

## Feature 3: Background Jobs Infrastructure (5 days)

### Purpose
Enable async tasks (analytics aggregation, email sending) without blocking API requests.

### Pre-Implementation Checks

#### 1. Check Deployment Environment

```bash
# Does the server support long-running processes?
# - If using serverless (AWS Lambda): Can't use background jobs directly
# - If using containers/VPS: Can use APScheduler or Celery
# - If using managed platform: Check limitations

# What's the deployment target?
cat README.md | grep -i "deploy\|host"
```

#### 2. Decide: APScheduler vs Celery

**APScheduler (Recommended for MVP)**
- Pros: Simple, in-process, no Redis needed
- Cons: Single worker, no distributed processing
- Best for: <10k users, <100 jobs/day

**Celery (For scaling)**
- Pros: Distributed, multiple workers, Redis/RabbitMQ
- Cons: Complex setup, requires message broker
- Best for: >100k users, high-volume jobs

**Recommendation:** Start with APScheduler, migrate to Celery if needed

### Architecture

```
FastAPI Server
    ├─ API Endpoint (fast response to user)
    │   └─ Queue job: "aggregate_analytics"
    │
    └─ APScheduler Background
        ├─ Job 1: Aggregate daily analytics (2 AM UTC)
        ├─ Job 2: Send email queue (every 5 min)
        ├─ Job 3: Cleanup old logs (daily)
        └─ Job 4: Refresh cache (hourly)
```

### Implementation Steps

#### Step 1: Install APScheduler (0.5 days)

```bash
pip install APScheduler==3.10.4
```

#### Step 2: Create JobScheduler Service (2 days)

**File:** `backend/app/services/job_scheduler.py` (NEW)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
import logging
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class JobScheduler:
    """Manage background jobs with APScheduler."""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.jobs: dict[str, Job] = {}

    def start(self):
        """Start the scheduler."""
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler stopped")

    def add_job(
        self,
        func: Callable,
        trigger: str,  # "cron", "interval", "date"
        job_id: str,
        **trigger_args  # hour=2, minute=0 for cron
    ):
        """
        Add a scheduled job.

        Examples:
        - scheduler.add_job(
            aggregate_analytics,
            trigger="cron",
            job_id="daily_analytics",
            hour=2,
            minute=0,  # 2 AM UTC
            timezone="UTC"
          )
        - scheduler.add_job(
            process_email_queue,
            trigger="interval",
            job_id="email_queue",
            minutes=5
          )
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not started")

        # Remove existing job with same ID
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)

        if trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        elif trigger == "interval":
            trigger_obj = trigger_args  # APScheduler handles this
        else:
            raise ValueError(f"Unknown trigger: {trigger}")

        job = self.scheduler.add_job(
            func,
            trigger=trigger_obj,
            id=job_id,
            name=f"Job: {job_id}",
            coalesce=True,  # Don't run multiple times if delayed
            max_instances=1,  # Only one instance at a time
        )

        self.jobs[job_id] = job
        logger.info(f"Added job: {job_id}")

    def get_job_status(self, job_id: str) -> dict:
        """Get job status."""
        if job_id not in self.jobs:
            return {"status": "not_found"}

        job = self.jobs[job_id]
        return {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "last_run": getattr(job, 'last_run_time', None),
            "trigger": str(job.trigger)
        }

# Singleton
_scheduler: Optional[JobScheduler] = None

def get_scheduler() -> JobScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler
```

#### Step 3: Create Jobs (1.5 days)

**File:** `backend/app/jobs/analytics_jobs.py` (NEW)

```python
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.database import SessionLocalSpecs
from ..models import ProjectMetrics, AnalyticsEvent

logger = logging.getLogger(__name__)

async def aggregate_daily_analytics():
    """
    Aggregate analytics events into daily metrics.

    Runs daily at 2 AM UTC.
    """
    db = SessionLocalSpecs()

    try:
        yesterday = datetime.utcnow().date() - timedelta(days=1)

        logger.info(f"Aggregating analytics for {yesterday}")

        # Get events from yesterday
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= yesterday,
            AnalyticsEvent.timestamp < yesterday + timedelta(days=1)
        ).all()

        # Aggregate by project
        project_aggregates = {}
        for event in events:
            project_id = event.event_data.get("project_id")
            if project_id not in project_aggregates:
                project_aggregates[project_id] = {
                    "analyses_count": 0,
                    "specs_added": 0,
                    "conflicts_resolved": 0
                }

            if event.event_type == "analysis_run":
                project_aggregates[project_id]["analyses_count"] += 1
            elif event.event_type == "spec_added":
                project_aggregates[project_id]["specs_added"] += 1
            elif event.event_type == "conflict_resolved":
                project_aggregates[project_id]["conflicts_resolved"] += 1

        # Save aggregates
        for project_id, metrics in project_aggregates.items():
            metric = ProjectMetrics(
                project_id=project_id,
                date=yesterday,
                **metrics
            )
            db.add(metric)

        db.commit()
        logger.info(f"Aggregated {len(project_aggregates)} projects")

    except Exception as e:
        logger.error(f"Analytics aggregation failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

async def process_email_queue():
    """
    Process pending emails.

    Runs every 5 minutes.
    """
    logger.info("Processing email queue...")
    # TODO: Implement when notification system added
```

**File:** `backend/app/jobs/__init__.py` (NEW)

```python
from .analytics_jobs import aggregate_daily_analytics, process_email_queue

__all__ = ["aggregate_daily_analytics", "process_email_queue"]
```

#### Step 4: Register Jobs in FastAPI Startup (1 day)

**File:** `backend/app/main.py` (UPDATE)

```python
from .services.job_scheduler import get_scheduler
from .jobs import aggregate_daily_analytics, process_email_queue

def create_app(...):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Starting Socrates2 API...")

        # Initialize scheduler
        scheduler = get_scheduler()
        scheduler.start()

        # Register jobs
        scheduler.add_job(
            aggregate_daily_analytics,
            trigger="cron",
            job_id="daily_analytics",
            hour=2,
            minute=0,
            timezone="UTC"
        )

        scheduler.add_job(
            process_email_queue,
            trigger="interval",
            job_id="email_queue",
            minutes=5
        )

        yield

        # Shutdown
        logger.info("Shutting down...")
        scheduler.stop()
        close_db_connections()

    # ... rest of app creation ...
```

#### Step 5: Monitoring Endpoint (1 day)

**Add to API:**

```python
@router.get("/api/v1/admin/jobs")
async def get_scheduled_jobs(
    current_user: User = Depends(get_current_active_user)
):
    """Get status of scheduled jobs (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403)

    scheduler = get_scheduler()

    return {
        "jobs": [
            scheduler.get_job_status(job_id)
            for job_id in scheduler.jobs.keys()
        ],
        "scheduler_running": scheduler.scheduler.running if scheduler.scheduler else False
    }
```

### Database Changes

**Migration:** `backend/alembic/versions/026_add_analytics_tables.py`

```python
class AnalyticsEvent(Base):
    """User actions for analytics."""
    __tablename__ = "analytics_events"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    event_type = Column(String(50))  # "project_created", "spec_added", etc.
    event_data = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ProjectMetrics(Base):
    """Daily aggregated metrics per project."""
    __tablename__ = "project_metrics"
    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"))
    date = Column(Date)
    analyses_count = Column(Integer, default=0)
    specs_added = Column(Integer, default=0)
    conflicts_resolved = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_project_metrics_date", "project_id", "date"),
    )
```

### Testing Checklist

- [ ] Scheduler starts on app startup
- [ ] Jobs registered correctly
- [ ] Analytics job runs at 2 AM UTC
- [ ] Email job runs every 5 minutes
- [ ] Job execution is logged
- [ ] Failed jobs are retried (up to 3 times)
- [ ] Job status endpoint shows correct info
- [ ] Scheduler stops on app shutdown
- [ ] No duplicate job execution

### Monitoring

```python
# Check job status
curl http://localhost:8000/api/v1/admin/jobs

# Expected response:
{
    "jobs": [
        {
            "id": "daily_analytics",
            "name": "Job: daily_analytics",
            "next_run": "2025-11-11T02:00:00+00:00",
            "last_run": null,
            "trigger": "cron[hour='2', minute='0']"
        },
        ...
    ],
    "scheduler_running": true
}
```

---

## Phase 1 Completion Status

**Date Completed:** November 11, 2025

### ✅ Week 0: Critical Architecture Fixes (COMPLETED)
- [x] Migration 1: Add Full-Text Search Indexes (025_add_search_indexes.py)
- [x] Migration 2: Migrate to pgvector (026_migrate_to_pgvector.py)
- [x] Migration 3: Add Subscription Fields to User (027_add_user_subscription_fields.py)
- [x] Migration 4: Add Analytics Tables (028_add_analytics_tables.py)

### ✅ Feature 1: Error Tracking Integration (COMPLETED)
- [x] Sentry SDK initialized with FastAPI integration
- [x] Sensitive data scrubbing configured (passwords, tokens, API keys)
- [x] Global exception handler integrated
- [x] Performance monitoring configured (10% traces sample rate)
- [x] Environment variables in config.py
- [x] File: `backend/app/core/sentry_config.py` (212 lines)

### ✅ Feature 2: Search System (COMPLETED)
- [x] Full-text search endpoint implemented
- [x] Search filters (status, phase, category)
- [x] Autocomplete support
- [x] Permission-based filtering (user can only search own projects)
- [x] File: `backend/app/api/search.py`

### ✅ Feature 3: Background Jobs Infrastructure (COMPLETED - Nov 11, 2025)
- [x] APScheduler integration service created
- [x] Job scheduler singleton pattern implemented
- [x] Analytics aggregation jobs (daily_analytics_aggregation)
- [x] Maintenance jobs (cleanup_old_sessions, refresh_cached_metrics)
- [x] Job monitoring API endpoints (/api/v1/admin/jobs)
- [x] Scheduler integration in main.py lifespan
- [x] All dependencies added to requirements.txt

**Files Created/Modified:**
- `backend/app/services/job_scheduler.py` (168 lines)
- `backend/app/jobs/__init__.py`
- `backend/app/jobs/analytics_jobs.py` (151 lines)
- `backend/app/jobs/maintenance_jobs.py` (102 lines)
- `backend/app/api/jobs.py` (145 lines)
- `backend/app/main.py` (updated with scheduler init & shutdown)
- `backend/requirements.txt` (added APScheduler + other dependencies)

## Phase 1 Summary

**Deliverables:**
- ✅ Error tracking with Sentry (8 days) - COMPLETED
- ✅ Full-text search system (15 days) - COMPLETED
- ✅ Background job scheduler (5 days) - COMPLETED

**Total: 28 days** ✅ COMPLETED

**Production Readiness Checklist:**
- [x] Errors captured and monitored (Sentry)
- [x] Search indexes created and working
- [x] Background jobs running on schedule (APScheduler)
- [x] Job monitoring API endpoints available
- [x] Scheduler starts on app startup and shuts down gracefully
- [x] Sensitive data scrubbing in place
- [x] Documentation complete
- [x] All code committed to repository

**API Endpoints Added:**
- GET `/api/v1/admin/jobs` - Get all scheduled jobs
- GET `/api/v1/admin/jobs/{job_id}` - Get specific job status
- POST `/api/v1/admin/jobs/{job_id}/trigger` - Manually trigger job
- GET `/api/v1/admin/jobs/status/summary` - Get scheduler summary

**Scheduled Jobs:**
- `daily_analytics_aggregation` - Runs at 2 AM UTC daily
- `cleanup_old_sessions` - Runs at 3 AM UTC daily

**Next Phase:** Phase 2 - Monetization (Payment & Billing)

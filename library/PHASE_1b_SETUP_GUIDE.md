# Phase 1b Setup Guide - Infrastructure & Database

**Status:** Ready to apply
**Last Updated:** November 13, 2025
**Scope:** Database infrastructure, security, configuration

---

## Overview

Phase 1b enables database persistence and security features. This guide walks through setting up and verifying the infrastructure.

## What Phase 1b Adds

### From Phase 1a (Pure Logic - 27 exports)

✅ QuestionGenerator, ConflictDetectionEngine, BiasDetectionEngine, LearningEngine
✅ ProjectData, SpecificationData, QuestionData, ConflictData, etc.
✅ Conversion functions (project_db_to_data, etc.)

### Phase 1b Additions (Infrastructure - 15+ new exports)

**Configuration:**
- `Settings` - Environment configuration class
- `get_settings()` - Get settings instance

**Database Sessions:**
- `engine_auth` - Auth database engine
- `engine_specs` - Specs database engine
- `SessionLocalAuth` - Auth DB session factory
- `SessionLocalSpecs` - Specs DB session factory
- `ScopedSessionAuth` - Thread-safe auth sessions
- `ScopedSessionSpecs` - Thread-safe specs sessions
- `get_db_auth()` - Get auth database session
- `get_db_specs()` - Get specs database session
- `Base` - SQLAlchemy declarative base

**Security & JWT:**
- `create_access_token()` - Create JWT tokens
- `decode_access_token()` - Validate JWT tokens
- `create_refresh_token()` - Create refresh tokens
- `validate_refresh_token()` - Validate refresh tokens
- `get_current_user()` - FastAPI dependency for current user
- `get_current_active_user()` - FastAPI dependency for active user
- `get_current_admin_user()` - FastAPI dependency for admin user
- `oauth2_scheme` - OAuth2 scheme for API

**Dependency Injection:**
- `ServiceContainer` - Central dependency container

---

## Current Status

### Verified Working ✅

- PostgreSQL is running and accessible
- Databases `socrates_auth` and `socrates_specs` exist
- Environment file (.env) created with required configuration
- Settings load successfully (DEBUG, ENVIRONMENT, DATABASE_URLs)
- Database connectivity works (both auth and specs databases)
- Dependency injection container works
- All Phase 1b imports are accessible

### Ready to Apply ⏳

- Alembic migrations (9 files) ready
- 29 database tables to be created
- 5 auth tables + 24 specs tables

---

## Database Schema Overview

### Auth Database (socrates_auth)

**Created by migrations:**

| Migration | Tables Created |
|-----------|-----------------|
| 001_auth_initial_schema | users, refresh_tokens |
| 002_auth_admin_management | admin_roles, admin_users, admin_audit_logs |

**Total: 5 tables for authentication**

```
users (User model)
  - User accounts with credentials
  - Email, password_hash, role, status
  - Foreign key to admin_roles (optional)

refresh_tokens (RefreshToken model)
  - JWT refresh token tracking
  - User ID, token, expiration

admin_roles (AdminRole model)
  - Role definitions (admin, moderator, etc.)

admin_users (AdminUser model)
  - Admin user assignments

admin_audit_logs (AdminAuditLog model)
  - Admin action logging
```

### Specs Database (socrates_specs)

**Created by migrations:**

| Migration | Tables Created |
|-----------|-----------------|
| 003_specs_core_specification_tables | projects, sessions, questions, specifications, conversation_history, conflicts |
| 004_specs_generated_content | generated_projects, generated_files |
| 005_specs_tracking_analytics | quality_metrics, user_behavior_patterns, question_effectiveness, knowledge_base_documents |
| 006_specs_collaboration_sharing | teams, team_members, project_shares |
| 007_specs_api_llm_integration | api_keys, llm_usage_tracking, subscriptions, invoices |
| 008_specs_analytics_search | analytics_metrics, document_chunks, notification_preferences |
| 009_specs_activity_project_management | activity_logs, project_invitations |

**Total: 24 tables for specifications and projects**

```
Phase 1b Core (minimum for functionality):
  - projects (Project model) - Project metadata
  - sessions (Session model) - Specification gathering sessions
  - questions (Question model) - Generated/asked questions
  - specifications (Specification model) - Requirements specs
  - conversation_history (ConversationHistory model) - Dialog history
  - conflicts (Conflict model) - Detected conflicts

Plus extended tables for analytics, collaboration, and tracking.
```

---

## Migration Alignment

### ✅ Verified Alignment with Public API

**Phase 1a/1b Models Match Migrations:**

```
Migration Table           -> SQLAlchemy Model      -> Phase 1a Export
================================================================================
users                     -> User                  -> Exported as User model
refresh_tokens            -> RefreshToken          -> Exported as RefreshToken
admin_roles               -> AdminRole             -> Exported as AdminRole
admin_users               -> AdminUser             -> Exported as AdminUser
admin_audit_logs          -> AdminAuditLog         -> Exported as AdminAuditLog
projects                  -> Project               -> Exported as Project
sessions                  -> Session               -> Exported as Session
questions                 -> Question              -> Exported as Question
specifications            -> Specification         -> Exported as Specification
conversation_history      -> ConversationHistory   -> Exported as ConversationHistory
conflicts                 -> Conflict              -> Exported as Conflict
```

**Conclusion:** Migrations create the exact tables needed for the public API models.

---

## Setup Steps

### Step 1: Verify .env File ✅ (Already Done)

Check that `.env` exists with required variables:

```bash
ls -la backend/.env
```

Expected variables:
- `DATABASE_URL_AUTH` - postgresql://postgres@localhost:5432/socrates_auth
- `DATABASE_URL_SPECS` - postgresql://postgres@localhost:5432/socrates_specs
- `SECRET_KEY` - JWT signing key
- `ANTHROPIC_API_KEY` - Claude API key
- `DEBUG` - True
- `ENVIRONMENT` - development

### Step 2: Run Verification Script ✅ (Already Done)

```bash
cd backend
python scripts/verify_phase1b_setup.py
```

Expected result: 5/6 checks passed (migrations not applied yet - that's OK)

### Step 3: Apply Migrations ⏳ (Next Step)

```bash
cd backend
python -m alembic upgrade head
```

This will:
1. Create 5 tables in socrates_auth database
2. Create 24 tables in socrates_specs database
3. Add alembic_version tracking table to both databases

### Step 4: Verify Migrations ✅ (After Step 3)

```bash
python scripts/verify_phase1b_setup.py
```

Expected result: 6/6 checks passed

### Step 5: Uncomment Phase 1b Imports (Next Implementation)

In `backend/socrates/__init__.py`, uncomment Phase 1b sections:

```python
# Uncomment Phase 1b imports
from app.core.config import Settings, get_settings
from app.core.dependencies import ServiceContainer
from app.core.database import (
    engine_auth, engine_specs,
    SessionLocalAuth, SessionLocalSpecs,
    ScopedSessionAuth, ScopedSessionSpecs,
    Base, get_db_auth, get_db_specs,
    init_db, close_db_connections,
)
from app.core.security import (
    create_access_token, decode_access_token,
    create_refresh_token, validate_refresh_token,
    get_current_user, get_current_active_user,
    get_current_admin_user, oauth2_scheme,
)
```

Then add to `__all__`:

```python
__all__ = [
    # ... Phase 1a exports ...

    # Phase 1b Infrastructure
    "Settings", "get_settings",
    "ServiceContainer",
    "engine_auth", "engine_specs",
    "SessionLocalAuth", "SessionLocalSpecs",
    "ScopedSessionAuth", "ScopedSessionSpecs",
    "Base", "get_db_auth", "get_db_specs",
    "init_db", "close_db_connections",
    "create_access_token", "decode_access_token",
    "create_refresh_token", "validate_refresh_token",
    "get_current_user", "get_current_active_user",
    "get_current_admin_user", "oauth2_scheme",
]
```

---

## Testing Phase 1b Imports

Once migrations are applied and imports uncommented:

```python
from socrates import (
    # Phase 1a - pure logic (still works)
    QuestionGenerator,
    # Phase 1b - infrastructure (newly available)
    Settings, get_settings,
    ServiceContainer,
    get_db_auth, get_db_specs,
    create_access_token, decode_access_token,
)

# Get settings
settings = get_settings()
print(f"Environment: {settings.ENVIRONMENT}")

# Get database session
db = get_db_auth()
try:
    # Use database
    pass
finally:
    db.close()

# Create JWT token
token = create_access_token({"sub": "user@example.com"})
```

---

## Troubleshooting

### Migrations Failed

**Problem:** Alembic upgrade fails
**Solution:**
1. Check .env file is configured correctly
2. Verify PostgreSQL is running
3. Check databases exist: `socrates_auth` and `socrates_specs`
4. Try again with `alembic downgrade base` then `alembic upgrade head`

### Database Connection Error

**Problem:** "could not connect to server"
**Solution:**
1. Verify PostgreSQL is running: `pg_isready`
2. Check DATABASE_URL in .env
3. Test connection: `psql -U postgres -d socrates_auth`

### Import Errors

**Problem:** "ModuleNotFoundError" when importing Phase 1b
**Solution:**
1. Ensure migrations were applied: `python scripts/verify_phase1b_setup.py`
2. Check .env file exists and is readable
3. Verify Python dependencies: `pip install -e .`

---

## What Gets Exported

### Phase 1b Infrastructure Exports (~15 new)

When Phase 1b is enabled, socrates package provides:

```python
# Configuration
Settings              # Pydantic settings class
get_settings()       # Get settings instance

# Database
engine_auth          # SQLAlchemy engine for auth DB
engine_specs         # SQLAlchemy engine for specs DB
SessionLocalAuth     # Auth DB session factory
SessionLocalSpecs    # Specs DB session factory
ScopedSessionAuth    # Thread-safe auth sessions
ScopedSessionSpecs   # Thread-safe specs sessions
Base                 # SQLAlchemy declarative base
get_db_auth()       # Get auth DB session (dependency injection)
get_db_specs()      # Get specs DB session (dependency injection)

# Security
create_access_token()      # Create JWT access token
decode_access_token()      # Validate JWT access token
create_refresh_token()     # Create refresh token
validate_refresh_token()   # Validate refresh token
get_current_user()         # FastAPI dependency: get current user
get_current_active_user()  # FastAPI dependency: active user
get_current_admin_user()   # FastAPI dependency: admin user
oauth2_scheme              # OAuth2PasswordBearer scheme

# Dependency Injection
ServiceContainer   # Central service container

# Lifecycle
init_db()             # Initialize database (for testing)
close_db_connections() # Close all connections (on shutdown)
```

---

## Total Exports After Phase 1b

| Phase | Exports | Categories |
|-------|---------|-----------|
| Phase 1a | 27 | Pure engines, dataclasses, conversions |
| Phase 1b | +15 | Config, database, security, DI |
| **Total** | **42** | **Full infrastructure** |

---

## Next: Phase 2 Services

After Phase 1b is working, Phase 2 adds:

- NLU Service (natural language understanding)
- Subscription management
- Rate limiting
- Action logging
- Additional validators

See `LIBRARY_GUIDE.md` for Phase 2 roadmap.

---

## Files Reference

| File | Purpose |
|------|---------|
| `backend/.env` | Environment configuration (created) |
| `backend/.env.example` | Configuration template (reference only) |
| `backend/alembic/versions/` | 9 migration files (ready to apply) |
| `backend/scripts/verify_phase1b_setup.py` | Verification tool (created) |
| `backend/socrates/__init__.py` | Public API (Phase 1b imports commented out) |

---

## Summary

**Status:** Phase 1b infrastructure is ready to deploy.

**What's Done:**
- ✅ .env file created
- ✅ Settings load without errors
- ✅ Database connectivity verified
- ✅ Dependency injection works
- ✅ Imports available (pending uncomment)

**What's Next:**
1. Apply migrations: `alembic upgrade head`
2. Uncomment Phase 1b imports in `socrates/__init__.py`
3. Test Phase 1b imports
4. Plan Phase 2 services

**Estimated Time:** 15 minutes to apply and verify

---

**Ready to proceed? Ask to "apply Phase 1b migrations"**

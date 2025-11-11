# Socrates - Database Migration Plan (Starting from Scratch)

**Status:** Starting with empty databases
**Target:** Phase 1 MVP implementation
**Last Updated:** 2025-11-05

---

## Overview

Since Socrates is starting from scratch, you need to:
1. Initialize Alembic (database migration tool)
2. Create 4 migration files for Phase 1
3. Run migrations against two databases

---

## Two-Database Architecture

### Database 1: `socrates_auth`
**Purpose:** Authentication & user management
**Tables Needed (Phase 1):**
- `users` (Migration 001)
- `refresh_tokens` (Migration 002)

### Database 2: `socrates_specs`
**Purpose:** Projects & specifications
**Tables Needed (Phase 1):**
- `projects` (Migration 003)
- `sessions` (Migration 004)

**Note:** Additional tables will be added in Phase 2+ (specifications, conversation_history, conflicts, etc.)

---

## Phase 1: Required Migrations (4 Files)

### Migration 001: Create users table
**Database:** socrates_auth
**File:** `backend/alembic/versions/001_create_users_table.py`

**Creates:**
- users table with columns:
  - id (UUID, primary key)
  - email (unique, indexed)
  - hashed_password
  - is_active, is_verified
  - status, role
  - created_at, updated_at
- 3 indexes (email, is_active, status)

**Purpose:** Store user accounts for authentication

---

### Migration 002: Create refresh_tokens table
**Database:** socrates_auth
**File:** `backend/alembic/versions/002_create_refresh_tokens_table.py`
**Depends on:** Migration 001

**Creates:**
- refresh_tokens table with columns:
  - id (UUID, primary key)
  - user_id (foreign key to users)
  - token (unique, indexed)
  - expires_at, is_revoked
  - created_at
- Foreign key constraint: refresh_tokens.user_id → users.id (CASCADE delete)
- 3 indexes (user_id, token, expires_at)

**Purpose:** JWT refresh token management

---

### Migration 003: Create projects table
**Database:** socrates_specs
**File:** `backend/alembic/versions/003_create_projects_table.py`

**Creates:**
- projects table with columns:
  - id (UUID, primary key)
  - user_id (references users in socrates_auth - NO foreign key constraint)
  - name, description
  - current_phase (default: 'discovery')
  - maturity_score (0-100, default: 0)
  - status (default: 'active')
  - created_at, updated_at
- 4 indexes (user_id, status, current_phase, maturity_score)
- Check constraint: maturity_score >= 0 AND maturity_score <= 100

**Purpose:** Store project metadata

**Important:** user_id references users table in socrates_auth database, but NO foreign key constraint (cross-database reference not supported)

---

### Migration 004: Create sessions table
**Database:** socrates_specs
**File:** `backend/alembic/versions/004_create_sessions_table.py`
**Depends on:** Migration 003

**Creates:**
- sessions table with columns:
  - id (UUID, primary key)
  - project_id (foreign key to projects)
  - mode (default: 'socratic')
  - status (default: 'active')
  - started_at, ended_at
  - created_at, updated_at
- Foreign key constraint: sessions.project_id → projects.id (CASCADE delete)
- 3 indexes (project_id, status, mode)

**Purpose:** Track conversation sessions within projects

---

## Migration Execution Plan

### Step 1: Initialize Alembic

```powershell
cd C:\Users\themi\PycharmProjects\Socrates\backend

# Initialize Alembic (creates alembic/ directory and alembic.ini)
alembic init alembic
```

**Creates:**
- `alembic.ini` (configuration file)
- `alembic/` directory
- `alembic/env.py` (migration environment)
- `alembic/versions/` (migration files directory)

---

### Step 2: Configure Alembic for Two Databases

**Problem:** Alembic supports only ONE database URL in `alembic.ini`

**Solution:** Run migrations separately for each database

#### For socrates_auth:

**Edit `alembic.ini`:**
```ini
sqlalchemy.url = postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_auth
```

**Run migrations 001-002:**
```powershell
# Create the 4 migration files first (see code below)
# Then run:
alembic upgrade head
```

#### For socrates_specs:

**Edit `alembic.ini` again:**
```ini
sqlalchemy.url = postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_specs
```

**Run migrations 003-004:**
```powershell
alembic upgrade head
```

**Alternative:** Use environment variables instead of editing `alembic.ini`:
```powershell
# For socrates_auth
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_auth"
alembic upgrade head

# For socrates_specs
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_specs"
alembic upgrade head
```

---

### Step 3: Create Migration Files

After `alembic init alembic`, create these 4 files manually:

#### File 1: `backend/alembic/versions/001_create_users_table.py`

```python
"""Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_status', 'users', ['status'])

def downgrade():
    op.drop_index('idx_users_status')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

---

#### File 2: `backend/alembic/versions/002_create_refresh_tokens_table.py`

```python
"""Create refresh_tokens table

Revision ID: 002
Revises: 001
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key to users in socrates_auth database
    op.create_foreign_key(
        'fk_refresh_tokens_user_id',
        'refresh_tokens', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_token', 'refresh_tokens', ['token'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])

def downgrade():
    op.drop_index('idx_refresh_tokens_expires_at')
    op.drop_index('idx_refresh_tokens_token')
    op.drop_index('idx_refresh_tokens_user_id')
    op.drop_constraint('fk_refresh_tokens_user_id', 'refresh_tokens', type_='foreignkey')
    op.drop_table('refresh_tokens')
```

---

#### File 3: `backend/alembic/versions/003_create_projects_table.py`

```python
"""Create projects table

Revision ID: 003
Revises: 002
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('current_phase', sa.String(50), nullable=False, server_default='discovery'),
        sa.Column('maturity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('idx_projects_user_id', 'projects', ['user_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_current_phase', 'projects', ['current_phase'])
    op.create_index('idx_projects_maturity_score', 'projects', ['maturity_score'])

    # Add check constraint for maturity_score
    op.create_check_constraint(
        'check_projects_maturity_score',
        'projects',
        'maturity_score >= 0 AND maturity_score <= 100'
    )

def downgrade():
    op.drop_constraint('check_projects_maturity_score', 'projects', type_='check')
    op.drop_index('idx_projects_maturity_score')
    op.drop_index('idx_projects_current_phase')
    op.drop_index('idx_projects_status')
    op.drop_index('idx_projects_user_id')
    op.drop_table('projects')
```

---

#### File 4: `backend/alembic/versions/004_create_sessions_table.py`

```python
"""Create sessions table

Revision ID: 004
Revises: 003
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False, server_default='socratic'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key to projects
    op.create_foreign_key(
        'fk_sessions_project_id',
        'sessions', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index('idx_sessions_project_id', 'sessions', ['project_id'])
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_mode', 'sessions', ['mode'])

def downgrade():
    op.drop_index('idx_sessions_mode')
    op.drop_index('idx_sessions_status')
    op.drop_index('idx_sessions_project_id')
    op.drop_constraint('fk_sessions_project_id', 'sessions', type_='foreignkey')
    op.drop_table('sessions')
```

---

## Complete Migration Execution Steps

### Windows PowerShell Commands:

```powershell
# 1. Navigate to backend directory
cd C:\Users\themi\PycharmProjects\Socrates\backend

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Initialize Alembic (first time only)
alembic init alembic

# 4. Create the 4 migration files
# (manually create files in alembic/versions/ using code above)

# 5. Run migrations for socrates_auth database
# Edit alembic.ini to point to socrates_auth database
# OR use environment variable:
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_auth"
alembic upgrade head

# 6. Verify socrates_auth tables created
psql -U postgres -d socrates_auth -c "\dt"
# Should show: users, refresh_tokens

# 7. Run migrations for socrates_specs database
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_specs"
alembic upgrade head

# 8. Verify socrates_specs tables created
psql -U postgres -d socrates_specs -c "\dt"
# Should show: projects, sessions
```

---

## Verification Checklist

After running all migrations:

### Database: socrates_auth

```powershell
psql -U postgres -d socrates_auth -c "\dt"
```

**Expected tables:**
- [x] users
- [x] refresh_tokens
- [x] alembic_version (created automatically by Alembic)

```powershell
psql -U postgres -d socrates_auth -c "\d users"
```

**Expected columns:**
- id, email, hashed_password, is_active, is_verified, status, role, created_at, updated_at

---

### Database: socrates_specs

```powershell
psql -U postgres -d socrates_specs -c "\dt"
```

**Expected tables:**
- [x] projects
- [x] sessions
- [x] alembic_version

```powershell
psql -U postgres -d socrates_specs -c "\d projects"
```

**Expected columns:**
- id, user_id, name, description, current_phase, maturity_score, status, created_at, updated_at

---

## What About Phase 2+ Tables?

### Phase 2 will add:
- specifications table (socrates_specs)
- conversation_history table (socrates_specs)
- questions table (socrates_specs)
- conflicts table (socrates_specs)

### Phase 3+ will add:
- llm_providers table
- llm_usage_tracking table
- api_keys table

**These will be added later as new migrations (005, 006, 007, etc.)**

---

## Troubleshooting

### Issue: "alembic command not found"
**Solution:**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Verify alembic installed
pip show alembic
```

---

### Issue: "Can't locate revision identified by '001'"
**Solution:**
```powershell
# Ensure you're in the backend directory
cd backend

# Verify migration files exist
ls alembic\versions\
```

---

### Issue: "relation already exists"
**Solution:**
```powershell
# Check Alembic version state
alembic current

# If tables exist but not tracked, stamp the database
alembic stamp head

# If need to start fresh (DANGEROUS - deletes data):
psql -U postgres -d socrates_auth -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

---

## Summary

**Total Migrations Needed for Phase 1:** 4

1. **001_create_users_table.py** → socrates_auth
2. **002_create_refresh_tokens_table.py** → socrates_auth
3. **003_create_projects_table.py** → socrates_specs
4. **004_create_sessions_table.py** → socrates_specs

**Next Step:** Follow READY_TO_RUN.md to:
1. Run setup_env.py to create .env file
2. Create PostgreSQL databases
3. Initialize Alembic
4. Create migration files
5. Run migrations

---

**Status:** Ready to execute once .env file is configured

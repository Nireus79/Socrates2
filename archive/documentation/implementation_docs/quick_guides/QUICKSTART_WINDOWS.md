# Socrates - Quick Start Guide (Windows)

**Platform:** Windows PowerShell
**Status:** Ready for Phase 1 Setup

---

## Prerequisites Checklist

- [x] Python 3.12.3 installed
- [x] Virtual environment created (`.venv`)
- [x] All dependencies installed (40 packages)
- [x] Dependencies verified (all green checkmarks)
- [ ] PostgreSQL installed
- [ ] `.env` file created
- [ ] Databases created
- [ ] Migrations run

---

## Step 1: Pull Latest Code (Migration Files Added)

```powershell
cd C:\Users\themi\PycharmProjects\Socrates
git pull origin master
```

**New files you'll get:**
- `backend/alembic/versions/001_create_users_table.py`
- `backend/alembic/versions/002_create_refresh_tokens_table.py`
- `backend/alembic/versions/003_create_projects_table.py`
- `backend/alembic/versions/004_create_sessions_table.py`
- `backend/scripts/run_migrations.ps1` (automated migration script)

---

## Step 2: Create .env File

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python scripts\setup_env.py
```

**What to enter:**
- PostgreSQL username: `postgres` (press Enter)
- PostgreSQL password: **[your PostgreSQL password]**
- PostgreSQL host: `localhost` (press Enter)
- PostgreSQL port: `5432` (press Enter)
- Claude API key: Press Enter (auto-detected)
- Debug mode: `True` (press Enter)
- Environment: `development` (press Enter)
- Log level: `DEBUG` (press Enter)

**Result:** `.env` file created with all configuration

---

## Step 3: Verify PostgreSQL Installed

```powershell
psql --version
```

**Expected:** `psql (PostgreSQL) 15.x` or higher

**If not installed:**
1. Download: https://www.postgresql.org/download/windows/
2. Install and remember the password for `postgres` user
3. Add to PATH: `C:\Program Files\PostgreSQL\15\bin`
4. Restart PowerShell

---

## Step 4: Create Databases

```powershell
# Create socrates_auth database
psql -U postgres -c "CREATE DATABASE socrates_auth;"

# Create socrates_specs database
psql -U postgres -c "CREATE DATABASE socrates_specs;"

# Verify both databases created
psql -U postgres -l
```

**Expected output:** Both `socrates_auth` and `socrates_specs` listed

**Note:** Use double quotes `"` in PowerShell, not single quotes `'`

---

## Step 5: Run Migrations (Automated)

```powershell
cd C:\Users\themi\PycharmProjects\Socrates\backend
.\venv\Scripts\Activate.ps1
.\scripts\run_migrations.ps1
```

**What the script does:**
1. Loads database URLs from `.env`
2. Initializes Alembic (if not already done)
3. Verifies all 4 migration files exist
4. Runs migrations for `socrates_auth` (migrations 001-002)
5. Runs migrations for `socrates_specs` (migrations 003-004)
6. Verifies success

**Expected output:**
```
======================================================================
Socrates - Database Migration Script
======================================================================

Loading configuration from .env file...
  Database URLs loaded successfully

Checking if databases exist...
  Auth Database: socrates_auth
  Specs Database: socrates_specs

All 4 migration files found

======================================================================
Step 1: Running migrations for socrates_auth
======================================================================

Setting DATABASE_URL to: socrates_auth
Checking current migration state...
Running 'alembic upgrade head'...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Create users table
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Create refresh_tokens table

SUCCESS: Migrations completed for socrates_auth

======================================================================
Step 2: Running migrations for socrates_specs
======================================================================

Setting DATABASE_URL to: socrates_specs
Checking current migration state...
Running 'alembic upgrade head'...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, Create projects table
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004, Create sessions table

SUCCESS: Migrations completed for socrates_specs

======================================================================
ALL MIGRATIONS COMPLETED SUCCESSFULLY!
======================================================================

Database: socrates_auth
  Tables: users, refresh_tokens, alembic_version

Database: socrates_specs
  Tables: projects, sessions, alembic_version
```

---

## Step 6: Verify Tables Created

```powershell
# Check socrates_auth tables
psql -U postgres -d socrates_auth -c "\dt"

# Check socrates_specs tables
psql -U postgres -d socrates_specs -c "\dt"
```

**Expected tables in socrates_auth:**
- `users`
- `refresh_tokens`
- `alembic_version` (tracks migration state)

**Expected tables in socrates_specs:**
- `projects`
- `sessions`
- `alembic_version`

---

## Troubleshooting

### Issue: PowerShell won't run .ps1 script

**Error:**
```
.\scripts\run_migrations.ps1 : File cannot be loaded because running scripts is disabled
```

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Issue: "psql: error: connection to server failed"

**Possible causes:**
1. PostgreSQL service not running
2. Wrong password
3. Wrong port

**Fix - Start PostgreSQL service:**
```powershell
# Check if service is running
Get-Service -Name postgresql*

# Start service if stopped
Start-Service postgresql-x64-15  # (adjust version number)
```

---

### Issue: "database does not exist"

**Fix:**
```powershell
# Create the missing database
psql -U postgres -c "CREATE DATABASE socrates_auth;"
psql -U postgres -c "CREATE DATABASE socrates_specs;"
```

---

### Issue: "relation already exists"

This means tables were already created (maybe manually or from a previous attempt).

**Option 1 - Mark as migrated (safe):**
```powershell
cd backend
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_auth"
alembic stamp head
```

**Option 2 - Start fresh (DELETES ALL DATA):**
```powershell
psql -U postgres -d socrates_auth -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
.\scripts\run_migrations.ps1
```

---

### Issue: Migration script fails with "DATABASE_URL not found"

**Fix:**
Ensure `.env` file exists and has correct format:
```ini
DATABASE_URL_AUTH=postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://postgres:YOUR_PASSWORD@localhost:5432/socrates_specs
```

Run `python scripts\setup_env.py` if needed.

---

## What's Next?

Once all migrations succeed, you're ready for **Phase 1 implementation**:

### Start Development Server

```powershell
cd C:\Users\themi\PycharmProjects\Socrates\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Expected:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Access API Documentation

Open browser: **http://localhost:8000/docs**

You'll see interactive API documentation (Swagger UI)

---

## Summary - What We Set Up

✅ **Backend Dependencies:** 40 packages installed (FastAPI, SQLAlchemy, Alembic, PostgreSQL drivers, etc.)
✅ **Environment Configuration:** `.env` file with database URLs, secret key, Claude API key
✅ **PostgreSQL Databases:** 2 databases created (socrates_auth, socrates_specs)
✅ **Database Schema:** 4 tables created across 2 databases
  - `socrates_auth`: users, refresh_tokens
  - `socrates_specs`: projects, sessions
✅ **Migration System:** Alembic initialized with 4 migration files

**Next:** Implement Phase 1 components (models, API endpoints, authentication)

---

## Need More Help?

- **READY_TO_RUN.md** - Detailed step-by-step guide
- **MIGRATION_PLAN.md** - Complete migration documentation
- **WINDOWS_SETUP_GUIDE.md** - Windows-specific setup notes
- **PHASE_1.md** - Phase 1 implementation guide (in `implementation_documents/`)

---

**Last Updated:** 2025-11-05
**Status:** Ready for Phase 1 implementation

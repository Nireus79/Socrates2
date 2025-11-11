# DEVELOPMENT SETUP GUIDE

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟡 MEDIUM - Complete before onboarding developers

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Detailed Setup](#detailed-setup)
5. [Environment Variables](#environment-variables)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [Development Workflow](#development-workflow)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## OVERVIEW

This guide walks you through setting up a local development environment for Socrates.

**Estimated Time:** 15-30 minutes (first time)

**What You'll Need:**
- Python 3.12
- PostgreSQL 15
- Git
- Text editor / IDE
- Terminal / Command Prompt

---

## PREREQUISITES

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4GB | 8GB+ |
| **Disk** | 2GB free | 10GB+ free |
| **OS** | Windows 10, Ubuntu 20.04, macOS 11 | Latest versions |

### Software Requirements

**1. Python 3.12**

```bash
# Check if installed
python --version
# Expected: Python 3.12.x

# If not installed, see CROSS_PLATFORM_GUIDE.md
```

**2. PostgreSQL 15**

```bash
# Check if installed
psql --version
# Expected: psql (PostgreSQL) 15.x

# If not installed, see CROSS_PLATFORM_GUIDE.md
```

**3. Git**

```bash
# Check if installed
git --version
# Expected: git version 2.x

# Install if needed
# Windows: https://git-scm.com/download/win
# Linux: sudo apt install git
# macOS: brew install git
```

**4. pip (Python package manager)**

```bash
# Check if installed
pip --version
# Expected: pip 23.x

# Usually comes with Python 3.12
```

---

## QUICK START (5 MINUTES)

For experienced developers who want to get running immediately:

```bash
# 1. Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# 2. Create virtual environment
python3.12 -m venv .venv

# 3. Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment template
cp .env.example .env
# Edit .env and add your API keys

# 6. Create databases
createdb socrates_auth
createdb socrates_specs

# 7. Run migrations
alembic upgrade head

# 8. Run tests
pytest

# 9. Start CLI
python -m cli.main --help
```

If everything works, skip to [Development Workflow](#development-workflow).

If you encounter issues, follow the [Detailed Setup](#detailed-setup) below.

---

## DETAILED SETUP

### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/Nireus79/Socrates.git

# Navigate to project directory
cd Socrates

# Verify files
ls -la
# You should see: README.md, requirements.txt, foundation_docs/, etc.
```

### Step 2: Create Virtual Environment

**Why?** Isolates project dependencies from system Python.

**Windows:**

```powershell
# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\activate

# Verify
which python
# Expected: .venv/Scripts/python.exe
```

**Linux/macOS:**

```bash
# Create virtual environment
python3.12 -m venv .venv

# Activate
source .venv/bin/activate

# Verify
which python
# Expected: /path/to/project/.venv/bin/python
```

**Confirmation:**

Your terminal prompt should now show `(.venv)` prefix:

```bash
(.venv) user@machine:~/Socrates$
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list
# You should see: fastapi, sqlalchemy, pydantic, anthropic, etc.
```

**Expected dependencies:**

- fastapi >= 0.121.0
- sqlalchemy >= 2.0.44
- pydantic >= 2.12.3
- alembic >= 1.12.0
- anthropic >= 0.25.0
- psycopg2-binary >= 2.9.9
- python-dotenv >= 1.0.0
- python-jose[cryptography] >= 3.3.0
- passlib[bcrypt] >= 1.7.4
- pytest >= 7.4.0
- pytest-cov >= 4.1.0

**If installation fails:**

```bash
# Check Python version
python --version
# Must be 3.12.x

# Check pip version
pip --version
# Should be 23.x+

# Try installing one package at a time to identify issue
pip install fastapi
pip install sqlalchemy
# ... etc
```

---

## ENVIRONMENT VARIABLES

### Step 4: Create .env File

```bash
# Copy template
cp .env.example .env

# Edit .env file
# Windows: notepad .env
# Linux/macOS: nano .env or vim .env
```

### Step 5: Configure .env

```bash
# .env file

# ======================
# Database Configuration
# ======================

# Auth database (user accounts, authentication)
DATABASE_URL_AUTH=postgresql://socrates_user:your_password@localhost:5432/socrates_auth

# Specs database (projects, specifications, conversations)
DATABASE_URL_SPECS=postgresql://socrates_user:your_password@localhost:5432/socrates_specs

# Database user credentials
DB_USER=socrates_user
DB_PASSWORD=your_password  # Change this!
DB_HOST=localhost
DB_PORT=5432

# ======================
# LLM API Keys
# ======================

# Anthropic (Claude) - REQUIRED for MVP
ANTHROPIC_API_KEY=sk-ant-api03-...  # Get from: https://console.anthropic.com

# OpenAI (GPT) - OPTIONAL (Phase 3+)
OPENAI_API_KEY=sk-...  # Get from: https://platform.openai.com

# ======================
# Application Settings
# ======================

ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# ======================
# Security Settings
# ======================

# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=generate-a-32-char-secret-key-here
JWT_SECRET_KEY=generate-a-32-char-jwt-secret-here

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ======================
# CORS (for React UI later)
# ======================

CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ======================
# Rate Limiting
# ======================

RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

### Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output to .env → SECRET_KEY

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output to .env → JWT_SECRET_KEY
```

### Get Anthropic API Key

1. Go to https://console.anthropic.com
2. Sign up / Log in
3. Navigate to "API Keys"
4. Create new key
5. Copy key (starts with `sk-ant-api03-...`)
6. Paste into `.env` → `ANTHROPIC_API_KEY`

⚠️ **Never commit `.env` to Git!** (already in `.gitignore`)

---

## DATABASE SETUP

### Step 6: Install PostgreSQL

If not already installed, follow [CROSS_PLATFORM_GUIDE.md](./CROSS_PLATFORM_GUIDE.md#postgresql-15-installation).

### Step 7: Start PostgreSQL Service

**Windows:**

```powershell
# Check service status
Get-Service postgresql*

# Start service if not running
Start-Service postgresql-x64-15
```

**Linux:**

```bash
# Check service status
sudo systemctl status postgresql

# Start service if not running
sudo systemctl start postgresql

# Enable on boot
sudo systemctl enable postgresql
```

**macOS:**

```bash
# Check service status
brew services list

# Start service if not running
brew services start postgresql@15
```

### Step 8: Create PostgreSQL User

**Connect to PostgreSQL:**

```bash
# Windows
psql -U postgres -h 127.0.0.1

# Linux
sudo -u postgres psql

# macOS
psql postgres
```

**Create user:**

```sql
-- Create user for Socrates
CREATE USER socrates_user WITH PASSWORD 'your_password';

-- Grant user ability to create databases (needed for testing)
ALTER USER socrates_user CREATEDB;

-- Exit
\q
```

### Step 9: Create Databases

**Method 1: Using createdb command**

```bash
# Create auth database
createdb -U socrates_user -h localhost socrates_auth

# Create specs database
createdb -U socrates_user -h localhost socrates_specs

# Verify databases exist
psql -U socrates_user -h localhost -c "\l"
```

**Method 2: Using psql**

```bash
# Connect as socrates_user
psql -U socrates_user -h localhost

# Create databases
CREATE DATABASE socrates_auth;
CREATE DATABASE socrates_specs;

# Verify
\l

# Exit
\q
```

### Step 10: Verify Database Connection

```bash
# Test connection to auth database
psql -U socrates_user -h localhost -d socrates_auth -c "SELECT version();"

# Test connection to specs database
psql -U socrates_user -h localhost -d socrates_specs -c "SELECT version();"

# If both commands show PostgreSQL version, you're good!
```

### Step 11: Run Database Migrations

```bash
# Ensure virtual environment is activated
(.venv) $

# Run Alembic migrations
alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema
```

**Verify tables were created:**

```bash
# Connect to auth database
psql -U socrates_user -h localhost -d socrates_auth

# List tables
\dt

# You should see:
# - users
# - refresh_tokens
# - password_reset_requests
# - audit_logs

# Exit
\q

# Connect to specs database
psql -U socrates_user -h localhost -d socrates_specs

# List tables
\dt

# You should see:
# - projects
# - sessions
# - specifications
# - conversation_history
# - conflicts
# - quality_metrics
# - maturity_tracking

# Exit
\q
```

---

## RUNNING THE APPLICATION

### Step 12: Run Tests (Verify Setup)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

**Expected output:**

```
============================= test session starts ==============================
collected 42 items

tests/test_auth.py::test_user_registration PASSED                        [  2%]
tests/test_auth.py::test_password_hashing PASSED                         [  4%]
tests/test_auth.py::test_jwt_token_creation PASSED                       [  7%]
...
============================== 42 passed in 3.45s ===============================
```

### Step 13: Run CLI (Command Line Interface)

```bash
# Show help
python -m cli.main --help

# Expected output:
# Socrates CLI v2.0.0
# Usage: socrates [OPTIONS] COMMAND [ARGS]...
#
# Commands:
#   create-project    Create a new project
#   list-projects     List all projects
#   chat              Start chat session
#   ...

# Create a project
python -m cli.main create-project "My E-commerce App"

# Start chat session
python -m cli.main chat --project-id abc123
```

### Step 14: Run Backend Server (Optional)

```bash
# Start FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Server will start at: http://localhost:8000

# Visit API docs: http://localhost:8000/docs
# Visit health check: http://localhost:8000/health
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## DEVELOPMENT WORKFLOW

### Daily Development Routine

```bash
# 1. Pull latest changes
git pull origin main

# 2. Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate  # Windows

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. Run migrations (if new)
alembic upgrade head

# 5. Run tests
pytest

# 6. Start coding!
```

### Before Committing Changes

```bash
# 1. Run tests
pytest

# 2. Check code formatting (if using black)
black src/ tests/

# 3. Check linting (if using flake8)
flake8 src/ tests/

# 4. Check types (if using mypy)
mypy src/

# 5. Stage changes
git add .

# 6. Commit
git commit -m "feat: Add user authentication"

# 7. Push
git push origin your-branch-name
```

### Creating Database Migrations

```bash
# 1. Make changes to models
# Edit: src/models/user.py

# 2. Generate migration
alembic revision --autogenerate -m "Add email_verified column to users"

# 3. Review migration file
# File: alembic/versions/abc123_add_email_verified.py

# 4. Apply migration
alembic upgrade head

# 5. Test migration
pytest tests/test_database.py

# 6. Commit migration file
git add alembic/versions/abc123_add_email_verified.py
git commit -m "db: Add email_verified column to users"
```

### Reverting Database Migrations

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

---

## TESTING

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_user_registration

# Run with coverage
pytest --cov=src --cov-report=html
# Open: htmlcov/index.html

# Run with verbose output
pytest -v

# Run with output (print statements)
pytest -s

# Run only failed tests from last run
pytest --lf

# Run tests in parallel (faster)
pytest -n 4  # 4 workers
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Authentication tests
├── test_projects.py         # Project management tests
├── test_socratic.py         # Socratic questioning tests
├── test_quality_control.py  # Quality Control tests
└── test_integration.py      # End-to-end tests
```

### Writing Tests

```python
# tests/test_auth.py
import pytest
from services.auth_service import AuthService

def test_user_registration(db_session):
    """Test user registration with valid data."""
    auth_service = AuthService(db_session)

    user = auth_service.register_user(
        email="test@example.com",
        password="SecurePassword123!",
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.password_hash != "SecurePassword123!"  # Password is hashed
    assert user.is_active is True

def test_user_registration_duplicate_email(db_session):
    """Test user registration fails with duplicate email."""
    auth_service = AuthService(db_session)

    # Create first user
    auth_service.register_user(
        email="test@example.com",
        password="SecurePassword123!",
    )

    # Try to create second user with same email
    with pytest.raises(ValueError, match="Email already registered"):
        auth_service.register_user(
            email="test@example.com",
            password="SecurePassword456!",
        )
```

---

## TROUBLESHOOTING

### Issue 1: Virtual Environment Not Activating

**Symptoms:**

```bash
(.venv) does not appear in terminal prompt
which python shows system python, not .venv python
```

**Solutions:**

```bash
# Linux/macOS: Try different shell
# If using bash:
source .venv/bin/activate

# If using zsh:
source .venv/bin/activate

# If using fish:
source .venv/bin/activate.fish

# Windows: Try different activation script
# PowerShell:
.\.venv\Scripts\Activate.ps1

# Command Prompt:
.\.venv\Scripts\activate.bat

# If "execution policy" error on Windows:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 2: PostgreSQL Connection Failed

**Symptoms:**

```python
sqlalchemy.exc.OperationalError: could not connect to server
psycopg2.OperationalError: connection refused
```

**Solutions:**

```bash
# 1. Check PostgreSQL is running
# Windows:
Get-Service postgresql*
# If not running:
Start-Service postgresql-x64-15

# Linux:
sudo systemctl status postgresql
# If not running:
sudo systemctl start postgresql

# macOS:
brew services list
# If not running:
brew services start postgresql@15

# 2. Check connection parameters
psql -U socrates_user -h localhost -d socrates_auth
# If fails, check:
# - Username: socrates_user
# - Password: (from .env)
# - Host: localhost (or 127.0.0.1 on Windows)
# - Port: 5432

# 3. Check .env file
cat .env | grep DATABASE_URL
# Verify URLs match your actual database setup

# 4. On Windows: Try 127.0.0.1 instead of localhost
DATABASE_URL_AUTH=postgresql://socrates_user:password@127.0.0.1:5432/socrates_auth
```

### Issue 3: Alembic Migration Fails

**Symptoms:**

```bash
alembic upgrade head
# ERROR: Target database is not up to date
# ERROR: Table 'users' already exists
```

**Solutions:**

```bash
# 1. Check migration history
alembic current
# Shows current migration version

alembic history
# Shows all migrations

# 2. If database has tables but no migration history:
# Stamp database with current migration
alembic stamp head

# 3. If migrations are broken:
# Rollback all
alembic downgrade base

# Drop all tables (DESTRUCTIVE!)
# Connect to database:
psql -U socrates_user -h localhost -d socrates_auth
# Drop all tables:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q

# Re-run migrations:
alembic upgrade head
```

### Issue 4: Module Not Found

**Symptoms:**

```python
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'src'
```

**Solutions:**

```bash
# 1. Ensure virtual environment is activated
which python
# Should show .venv path

# 2. Reinstall dependencies
pip install -r requirements.txt

# 3. If "No module named 'src'":
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%CD%\src  # Windows

# Or install package in development mode
pip install -e .
```

### Issue 5: Tests Fail

**Symptoms:**

```bash
pytest
# E       AssertionError: assert 1 == 2
# FAILED tests/test_auth.py::test_user_registration
```

**Solutions:**

```bash
# 1. Run tests with verbose output
pytest -v

# 2. Run tests with output (see print statements)
pytest -s

# 3. Run specific failing test
pytest tests/test_auth.py::test_user_registration -v -s

# 4. Check test database is clean
# Tests should use separate test database or fixtures

# 5. Check .env file has correct settings
cat .env | grep ENVIRONMENT
# Should be: ENVIRONMENT=development or ENVIRONMENT=test

# 6. Reset test database
pytest --create-db  # If using pytest-django
```

### Issue 6: .env File Not Loaded

**Symptoms:**

```python
ValueError: Missing required environment variables: ANTHROPIC_API_KEY
KeyError: 'DATABASE_URL_AUTH'
```

**Solutions:**

```bash
# 1. Check .env file exists
ls -la .env

# 2. Check .env file location
# Must be in project root, same directory as main.py

# 3. Check .env file is loaded in code
# In settings.py or config.py:
from dotenv import load_dotenv
load_dotenv()  # Must be called before accessing os.getenv()

# 4. Manually specify .env path
from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# 5. Verify variables are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"
```

### Issue 7: Port Already in Use

**Symptoms:**

```bash
uvicorn api.main:app --port 8000
# ERROR: Address already in use
```

**Solutions:**

```bash
# 1. Find process using port 8000
# Linux/macOS:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# 2. Kill process
# Linux/macOS:
kill -9 <PID>
# Windows:
taskkill /PID <PID> /F

# 3. Use different port
uvicorn api.main:app --port 8001
```

---

## VERIFICATION CHECKLIST

Before starting development, verify:

- [ ] Python 3.12 installed (`python --version`)
- [ ] PostgreSQL 15 installed (`psql --version`)
- [ ] Git installed (`git --version`)
- [ ] Repository cloned (`cd Socrates && git status`)
- [ ] Virtual environment created (`.venv/` directory exists)
- [ ] Virtual environment activated (`(.venv)` in prompt)
- [ ] Dependencies installed (`pip list` shows fastapi, sqlalchemy, etc.)
- [ ] .env file created (`ls .env`)
- [ ] .env file configured (API keys, database URLs, secrets)
- [ ] PostgreSQL running (`psql -U socrates_user -h localhost -d socrates_auth`)
- [ ] Databases created (`socrates_auth` and `socrates_specs`)
- [ ] Migrations run (`alembic current` shows latest)
- [ ] Tests pass (`pytest` shows all passing)
- [ ] CLI works (`python -m cli.main --help`)

If all checkboxes are ✅, you're ready to develop!

---

## NEXT STEPS

After completing setup:

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand system design
2. Read [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) for test approach
3. Check [VISION.md](./VISION.md) for project goals
4. Review [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for code organization
5. Start coding! 🚀

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This guide ensures any developer can set up Socrates locally in under 30 minutes.*

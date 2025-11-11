# PyCharm Local Setup Roadmap for Socrates2

**Version:** 1.0
**Date:** November 11, 2025
**Status:** Production Ready
**PyPI Package:** `socrates-ai==0.2.0`

---

## Overview

This document provides step-by-step instructions to get Socrates2 running locally in PyCharm on your machine. The project is now production-ready with comprehensive testing, documentation, and PyPI publication.

---

## Prerequisites

**System Requirements:**
- **Python:** 3.12+ (required by project)
- **OS:** Windows, macOS, or Linux
- **RAM:** 4GB minimum (8GB recommended)
- **Disk Space:** 2GB for full development setup

**Required Software:**
- PyCharm IDE (Professional or Community Edition)
- PostgreSQL 12+ (for database)
- Git (for version control)

---

## Step 1: Clone and Setup (5 minutes)

### 1.1 Clone Repository
```bash
git clone https://github.com/Nireus79/Socrates2.git
cd Socrates2
git checkout main  # or your working branch
```

### 1.2 Open in PyCharm
1. **File → Open** → Select `Socrates2` directory
2. **Configure Python Interpreter:**
   - File → Settings → Project: Socrates2 → Python Interpreter
   - Click gear icon → Add Interpreter → Add Local Interpreter
   - Select Python 3.12+ or install it

### 1.3 Create Virtual Environment
```bash
cd backend
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

---

## Step 2: Install Dependencies (3 minutes)

```bash
# Install in editable mode with dev tools
pip install -e ".[dev]"

# This installs:
# - Production deps (28 packages): FastAPI, SQLAlchemy, Pydantic, etc.
# - Dev deps (12 packages): pytest, black, ruff, mypy, etc.
```

**Verify Installation:**
```bash
python -c "import socrates_ai; print('✅ socrates-ai library loaded')"
python -c "from app.main import app; print('✅ FastAPI app loaded')"
```

---

## Step 3: Database Setup (10 minutes)

### 3.1 Create PostgreSQL Databases
```bash
# Connect to PostgreSQL
psql -U postgres

# Create two databases
CREATE DATABASE socrates_auth;
CREATE DATABASE socrates_specs;
\q
```

### 3.2 Configure Environment
```bash
cd /home/user/Socrates2/backend

# Copy environment template
cp .env.example .env

# Edit .env with your settings:
# DATABASE_URL_AUTH=postgresql://postgres:password@localhost:5432/socrates_auth
# DATABASE_URL_SPECS=postgresql://postgres:password@localhost:5432/socrates_specs
# SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
# ANTHROPIC_API_KEY=<your-key-here>
```

### 3.3 Run Migrations
```bash
# From backend directory
alembic upgrade head

# Verify (check that migration history updated)
alembic history
```

---

## Step 4: PyCharm Configuration (5 minutes)

### 4.1 Configure Interpreter in PyCharm
1. **File → Settings → Project: Socrates2 → Python Interpreter**
2. Click **⚙️ (gear icon) → Add**
3. Select **Existing Environment**
4. Navigate to: `Socrates2/backend/.venv/bin/python` (or `.venv/Scripts/python.exe` on Windows)
5. Click **OK**

### 4.2 Configure Run Configuration
1. **Run → Edit Configurations**
2. Click **+ → Python**
3. **Script path:** `/home/user/Socrates2/backend/app/main.py`
4. **Module name:** `uvicorn app.main:app --reload`
5. **Working directory:** `/home/user/Socrates2/backend`
6. **Environment variables:** (auto-loaded from `.env`)
7. Click **OK**

### 4.3 Mark Directories
1. Right-click `backend/app` → **Mark Directory as → Sources Root**
2. Right-click `backend/tests` → **Mark Directory as → Test Sources Root**

### 4.4 Enable Code Quality Tools
**File → Settings → Tools**

**Black (Formatter):**
- Search for "Black"
- Enable with line length: 100

**Ruff (Linter):**
- Search for "Ruff"
- Enable and configure

**Mypy (Type Checker):**
- Search for "Mypy"
- Enable for project

---

## Step 5: Verification (5 minutes)

### 5.1 Run Tests
```bash
cd backend

# Run all tests
pytest tests/ -v

# Expected: 274+ tests passing ✅

# With coverage
pytest tests/ --cov=app --cov-report=html
# View coverage at: htmlcov/index.html
```

### 5.2 Start Development Server
```bash
# From backend directory
python -m uvicorn app.main:app --reload

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### 5.3 Access API Documentation
Open browser and visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/v1/admin/health

---

## Step 6: Daily Development Workflow

### 6.1 Start Development Session
```bash
cd backend

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Start dev server in terminal or PyCharm
python -m uvicorn app.main:app --reload
```

### 6.2 Code Quality Before Commit
```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/ --fix

# Type checking
mypy app/ --explicit-package-bases

# Run tests
pytest tests/ -v
```

### 6.3 Git Workflow
```bash
# Check status
git status

# Stage changes
git add .

# Commit with message
git commit -m "feat: Your feature description"

# Push to branch
git push origin your-branch-name
```

---

## Project Structure

```
Socrates2/
├── backend/                      # Main Python backend
│   ├── .venv/                   # Virtual environment (created locally)
│   ├── app/                     # FastAPI application
│   │   ├── api/                # REST endpoints
│   │   ├── domains/            # 7 knowledge domains
│   │   ├── cli/                # CLI commands
│   │   ├── models/             # SQLAlchemy models
│   │   ├── services/           # Business logic
│   │   ├── agents/             # AI agents
│   │   ├── core/               # Core utilities
│   │   └── main.py             # FastAPI app
│   ├── tests/                  # 274+ unit & integration tests
│   ├── alembic/                # Database migrations (38 total)
│   ├── pyproject.toml          # Package configuration
│   ├── requirements.txt        # Production dependencies
│   ├── requirements-dev.txt    # Dev dependencies
│   ├── .env.example            # Environment template
│   └── README.md               # Backend documentation
├── docs/                        # Documentation
├── foundation_docs/             # Architecture documentation
├── extensions/vs-code/          # VS Code extension
└── archive/                     # Historical phase documentation
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution:**
```bash
cd backend
pip install -e .
# Or manually set PYTHONPATH
export PYTHONPATH=/path/to/Socrates2/backend
```

### Issue: PostgreSQL Connection Refused

**Solution:**
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT version();"

# If not running, start it:
# Windows: Services app → PostgreSQL
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql
```

### Issue: Tests Fail with "Domain not found"

**Solution:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null

# Reinstall package
pip install -e ".[dev]"

# Run tests again
pytest tests/ -v
```

### Issue: Port 8000 Already in Use

**Solution:**
```bash
# Use different port
python -m uvicorn app.main:app --reload --port 8001

# Or kill existing process on port 8000
# Windows: netstat -ano | findstr :8000 → taskkill /PID {pid} /F
# Linux: lsof -i :8000 → kill -9 {pid}
```

### Issue: "Environment variable not found"

**Solution:**
1. Verify `.env` file exists in `/backend` directory
2. Restart PyCharm or run server
3. Check PyCharm Run Configuration includes Environment variables

---

## API Documentation

### Key Endpoints

**Domains (11 endpoints)**
```bash
GET    /api/v1/domains                      # List all domains
GET    /api/v1/domains/{domain_id}          # Get domain details
GET    /api/v1/domains/{domain_id}/questions
GET    /api/v1/domains/{domain_id}/exporters
```

**Workflows (11 endpoints)**
```bash
POST   /api/v1/workflows                    # Create workflow
GET    /api/v1/workflows/{workflow_id}      # Get workflow
POST   /api/v1/workflows/{workflow_id}/validate
GET    /api/v1/workflows/{workflow_id}/conflicts
```

**Analytics (8 endpoints)**
```bash
GET    /api/v1/analytics                    # Overall report
GET    /api/v1/analytics/domains/{domain_id}
GET    /api/v1/analytics/quality-summary
```

**Auth (5 endpoints)**
```bash
POST   /api/v1/auth/register                # Register user
POST   /api/v1/auth/login                   # Login
GET    /api/v1/auth/me                      # Current user
```

See http://localhost:8000/docs for interactive API explorer.

---

## CLI Tools

```bash
# Domain commands
socrates domains list
socrates domains info programming
socrates domains questions data_engineering

# Workflow commands
socrates workflows create my_project
socrates workflows add my_project programming
socrates workflows validate my_project

# Analytics commands
socrates analytics report
socrates analytics quality

# Auth commands
socrates auth login
socrates auth token --generate
```

---

## Testing Strategy

### Run All Tests
```bash
pytest tests/ -v                          # Verbose output
pytest tests/ -v --tb=short               # Short traceback
pytest tests/ --cov=app --cov-report=html # With coverage
```

### Run Specific Tests
```bash
pytest tests/test_domains/                # Domain tests
pytest tests/test_workflows.py -v         # Workflow tests
pytest tests/ -k "workflow" -v            # Tests matching pattern
pytest tests/test_analytics.py::test_track_domain_access -v  # Single test
```

### Test Coverage
- **Domain System:** 80+ tests
- **Workflows:** 29 tests
- **Analytics:** 27 tests
- **CLI:** 21 tests
- **Infrastructure:** 100+ tests
- **Total:** 274+ tests (all passing ✅)

---

## Code Quality Standards

### Before Committing

1. **Format Code (Black)**
   ```bash
   black app/ tests/
   ```

2. **Lint Code (Ruff)**
   ```bash
   ruff check app/ tests/ --fix
   ```

3. **Type Check (Mypy)**
   ```bash
   mypy app/ --explicit-package-bases
   ```

4. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

### PyCharm Integration

All tools are configured in `pyproject.toml`. PyCharm will:
- Auto-format with Black on save (if enabled)
- Show Ruff warnings in editor
- Run Mypy in background
- Highlight test issues

---

## Deployment

### Production Build
```bash
# Build distribution
python -m build

# Upload to PyPI (already published!)
twine upload dist/*
```

### Running Server
```bash
# Development
python -m uvicorn app.main:app --reload --port 8000

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment for Production
```env
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL_AUTH=postgresql://user:pass@db-host:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://user:pass@db-host:5432/socrates_specs
```

---

## Support & Resources

### Documentation
- **Project README:** `/backend/README.md`
- **API Docs:** http://localhost:8000/docs (when running)
- **CHANGELOG:** `/backend/CHANGELOG.md`
- **Architecture:** `/foundation_docs/ARCHITECTURE.md`

### GitHub Resources
- **Issues:** https://github.com/Nireus79/Socrates2/issues
- **Discussions:** https://github.com/Nireus79/Socrates2/discussions
- **Pull Requests:** https://github.com/Nireus79/Socrates2/pulls

### PyPI Package
- **Package:** https://pypi.org/project/socrates-ai/0.2.0/
- **Install:** `pip install socrates-ai==0.2.0`

---

## Troubleshooting Checklist

- [ ] Python 3.12+ installed: `python --version`
- [ ] Virtual environment created and activated
- [ ] Dependencies installed: `pip list | grep socrates`
- [ ] PostgreSQL running: `psql -U postgres -c "SELECT 1"`
- [ ] Databases created: `socrates_auth` and `socrates_specs`
- [ ] `.env` file exists with valid database URLs
- [ ] Migrations run: `alembic history`
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Server starts: `python -m uvicorn app.main:app --reload`
- [ ] API accessible: http://localhost:8000/docs

---

## Next Steps

1. **Complete Setup:** Follow Steps 1-6 above
2. **Run Tests:** `pytest tests/ -v` (verify 274+ pass)
3. **Start Development:** `python -m uvicorn app.main:app --reload`
4. **Make Changes:** Edit code in PyCharm
5. **Run Quality Checks:** `black app/` → `ruff check app/` → `pytest`
6. **Commit & Push:** `git add .` → `git commit -m "..."` → `git push`

---

## Quick Reference

| Task | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Install deps | `pip install -e ".[dev]"` |
| Run migrations | `alembic upgrade head` |
| Start server | `python -m uvicorn app.main:app --reload` |
| Run tests | `pytest tests/ -v` |
| Format code | `black app/ tests/` |
| Lint code | `ruff check app/ --fix` |
| Type check | `mypy app/ --explicit-package-bases` |
| View API docs | http://localhost:8000/docs |
| Run CLI | `socrates domains list` |

---

**Status:** ✅ **Ready for Local Development**

All systems are configured, tested, and ready. Follow the steps above and you'll have a fully functional development environment in 30 minutes.

Questions? See the documentation or check GitHub issues.

Happy coding! 🚀

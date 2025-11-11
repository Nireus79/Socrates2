# Socrates Backend - Installation Guide

## Proper Installation (Works on Any System)

### Method 1: Editable Install (Recommended for Development)

This installs the package in "editable" mode, so imports work from anywhere:

```bash
cd Socrates/backend

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or production only (no test tools)
pip install -e .
```

**Benefits:**
- ✅ Works on any system (Windows, Linux, macOS, Docker)
- ✅ No IDE-specific configuration needed
- ✅ Imports work from anywhere: `from app.core.config import settings`
- ✅ Changes to code are immediately reflected (no reinstall needed)
- ✅ Professional standard practice

**Verify it worked:**
```bash
python -c "import app; print(app.__file__)"
# Should print: /path/to/Socrates/backend/app/__init__.py

python -c "from app.models.user import User; print('Success!')"
# Should print: Success!
```

### Method 2: Working Directory (Production/Docker)

Always run from the `backend/` directory:

```bash
cd Socrates/backend

# Set PYTHONPATH to current directory
export PYTHONPATH="${PYTHONPATH}:."  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;.       # Windows CMD
$env:PYTHONPATH+=";."               # Windows PowerShell

# Run commands
pytest tests/
python -m uvicorn app.main:app --reload
```

**Benefits:**
- ✅ No installation needed
- ✅ Works in Docker containers
- ✅ Good for CI/CD pipelines

**Drawback:**
- ⚠️ Must always be in `backend/` directory
- ⚠️ PYTHONPATH must be set

---

## ❌ What NOT to Do

### Don't Rely on IDE Configuration

**Bad Practice:**
```
"Just mark 'backend' as Sources Root in PyCharm"
```

**Why it's bad:**
- ❌ Only works in PyCharm (not VSCode, Vim, production)
- ❌ Not portable to Docker/CI/CD
- ❌ Other developers won't have same IDE setup
- ❌ Production servers don't have PyCharm

### Don't Modify sys.path in Code

**Bad Practice:**
```python
# Don't do this!
import sys
sys.path.insert(0, '/path/to/backend')
```

**Why it's bad:**
- ❌ Hardcoded paths break on other systems
- ❌ Makes code non-portable
- ❌ Hides real dependency issues

---

## Installation Options Comparison

| Method | Portability | Development | Production | Docker | CI/CD |
|--------|-------------|-------------|------------|--------|-------|
| `pip install -e .` | ✅ Excellent | ✅ Best | ✅ Good | ✅ Yes | ✅ Yes |
| Working Dir + PYTHONPATH | ✅ Good | ⚠️ OK | ✅ Good | ✅ Yes | ✅ Yes |
| IDE Sources Root | ❌ PyCharm only | ⚠️ OK | ❌ No | ❌ No | ❌ No |
| sys.path hacks | ❌ Bad | ❌ Bad | ❌ Bad | ❌ Bad | ❌ Bad |

---

## Full Setup Instructions

### 1. Install Python 3.12+

**Windows:**
```bash
python --version  # Should be 3.12+
```

**Linux:**
```bash
sudo apt install python3.12 python3.12-venv
```

### 2. Create Virtual Environment

```bash
cd Socrates/backend

# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\activate      # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Install Socrates in Editable Mode

```bash
# Install with dev dependencies (testing, linting)
pip install -e ".[dev]"

# Or production only
pip install -e .
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# - Database URLs
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - ANTHROPIC_API_KEY
```

### 5. Setup Database

```bash
# Make sure PostgreSQL is running
# Create databases
createdb socrates_auth
createdb socrates_specs

# Run migrations
alembic upgrade head
```

### 6. Verify Installation

```bash
# Test imports
python test_imports.py
# Should show: ✅ ALL IMPORTS SUCCESSFUL!

# Run critical tests
pytest tests/test_data_persistence.py -v
# All 4 tests must pass

# Run all tests
pytest tests/ -v
```

### 7. Start Development Server

```bash
# Start FastAPI server
python -m uvicorn app.main:app --reload

# Open browser
# http://localhost:8000/docs
```

---

## Docker Installation

For Docker, use working directory method:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY .env .

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

**Solution 1 (Recommended):**
```bash
cd backend
pip install -e .
```

**Solution 2:**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:."
python -m pytest tests/
```

### "Unresolved reference 'app'" in PyCharm

After `pip install -e .`, PyCharm should automatically detect it. If not:
1. File → Invalidate Caches → Restart
2. Verify Python interpreter is set to your venv

### Tests can't find modules

```bash
# Make sure you installed in editable mode
cd backend
pip install -e ".[dev]"

# Or set PYTHONPATH
cd backend
export PYTHONPATH=.
pytest tests/
```

---

## Summary

**For Development (Recommended):**
```bash
cd Socrates/backend
pip install -e ".[dev]"
pytest tests/
python -m uvicorn app.main:app --reload
```

**For Production/Docker:**
```bash
cd Socrates/backend
export PYTHONPATH=.
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0
```

**For CI/CD:**
```bash
cd Socrates/backend
pip install -r requirements.txt -r requirements-dev.txt
export PYTHONPATH=.
pytest tests/ --cov=app
```

✅ **No IDE configuration required**
✅ **Works on any system**
✅ **Professional standard practice**

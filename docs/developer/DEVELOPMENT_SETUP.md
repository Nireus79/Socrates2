# Development Setup Guide

**Level:** Beginner to Intermediate
**Time:** 30 minutes
**Goal:** Set up local development environment

---

## Prerequisites

### System Requirements
- macOS 10.15+, Linux, or Windows (WSL2)
- Git 2.30+
- Python 3.12+ (check: `python --version`)
- PostgreSQL 13+ (local or Docker)
- RAM: 4GB minimum, 8GB recommended
- Disk: 5GB free space

### Required Software

```bash
# macOS (using Homebrew)
brew install git python@3.12 postgresql

# Ubuntu/Debian
sudo apt-get install git python3.12 python3.12-venv postgresql postgresql-contrib

# Windows
# Download from: https://www.python.org/, https://git-scm.com/, https://www.postgresql.org/

# Docker (alternative to local PostgreSQL)
# Download from: https://www.docker.com/products/docker-desktop
```

---

## Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Verify you're on main development branch
git branch -a
git checkout master  # or main
```

---

## Step 2: Create Virtual Environment

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment

## macOS/Linux
source .venv/bin/activate

## Windows (Command Prompt)
.venv\Scripts\activate.bat

## Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Verify activation (you should see (.venv) in prompt)
which python  # macOS/Linux
where python  # Windows
```

---

## Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# OR install editable with all extras
pip install -e ".[dev]"

# Verify installation
pip list | grep -E "fastapi|sqlalchemy|pytest"
```

---

## Step 4: Set Up Database

### Option A: PostgreSQL Local

```bash
# Start PostgreSQL service
# macOS (Homebrew)
brew services start postgresql

# Ubuntu/Debian
sudo service postgresql start

# Windows
# Start PostgreSQL service via Services.msc or command:
# pg_ctl -D "C:\Program Files\PostgreSQL\17\data" start

# Create databases
createdb socrates_auth
createdb socrates_specs

# Verify databases created
psql -l | grep socrates
```

### Option B: PostgreSQL with Docker

```bash
# Start PostgreSQL container
docker run --name socrates-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 \
  -d postgres:17

# Verify container is running
docker ps | grep socrates-postgres

# Create databases
docker exec -it socrates-postgres psql -U postgres -c "CREATE DATABASE socrates_auth;"
docker exec -it socrates-postgres psql -U postgres -c "CREATE DATABASE socrates_specs;"
```

---

## Step 5: Configure Environment Variables

```bash
# Create .env file in backend directory
cd /path/to/Socrates/backend
touch .env

# Add environment variables (copy from .env.example if available)
cat > .env << 'EOF'
# Database URLs
DATABASE_URL_AUTH=postgresql://postgres:password@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://postgres:password@localhost:5432/socrates_specs

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API
ANTHROPIC_API_KEY=your-anthropic-api-key

# Application
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF

# Generate secure SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output and update .env file
```

**⚠️ Important:** Never commit .env to version control!

---

## Step 6: Run Database Migrations

```bash
# Navigate to backend directory
cd /path/to/Socrates/backend

# Verify alembic configuration
cat alembic.ini | grep -A 5 "sqlalchemy.url"

# Run migrations
alembic upgrade head

# Verify tables created
psql -U postgres -d socrates_auth -c "\dt"
psql -U postgres -d socrates_specs -c "\dt"

# Expected tables:
# socrates_auth: users, refresh_tokens
# socrates_specs: projects, sessions, specifications, workflows
```

---

## Step 7: Verify Installation

```bash
# Check Python version
python --version
# Should show: Python 3.12.x

# Check installed packages
pip list | head -20

# Check database connection
python -c "
from app.core.database import SessionLocal
try:
    db = SessionLocal()
    db.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Check imports
python -c "
import fastapi
import sqlalchemy
import pydantic
import anthropic
print('✅ All imports successful')
"
```

---

## Step 8: Start Development Server

```bash
# Start FastAPI development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Application startup complete
# INFO:     Uvicorn running on http://0.0.0.0:8000

# Verify API is running
# Open browser: http://localhost:8000/docs
# Or: curl http://localhost:8000/api/v1/admin/health
```

---

## Step 9: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth_endpoints.py -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## IDE Setup

### PyCharm

See [PyCharm Setup Guide](../../PYCHARM_LOCAL_SETUP_ROADMAP.md)

Quick setup:
1. File → Open → Select Socrates folder
2. Python interpreter: .venv
3. Mark backend/ as Sources Root
4. Run configurations: uvicorn app.main:app --reload

### VS Code

```bash
# Open VS Code
code .

# Install extensions:
# - Python (Microsoft)
# - Pylance
# - FastAPI (with Swagger support)
# - SQLTools (PostgreSQL)
# - REST Client (for API testing)
```

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Uvicorn FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### VIM/Neovim

```bash
# Install Python LSP
pip install python-lsp-server pylsp-mypy

# Configure in your .vimrc or init.vim
# Use coc-python or pyright for IDE features
```

---

## Common Commands

```bash
# Development
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload

# Testing
pytest tests/ -v
pytest tests/test_auth_endpoints.py::TestUserRegistration -v
pytest -m api  # Run only API tests

# Code Quality
black app/
ruff check app/ --fix
mypy app/

# Database
alembic revision --autogenerate -m "Migration message"
alembic upgrade head
alembic downgrade -1

# Dependencies
pip install package-name
pip freeze > requirements.txt
pip install -r requirements.txt
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

**Solution:** Virtual environment not activated
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate  # Windows
```

### "psycopg2 connection error"

**Solution:** PostgreSQL not running
```bash
# Check PostgreSQL status
pg_isready

# Start PostgreSQL
brew services start postgresql  # macOS
sudo service postgresql start  # Ubuntu
```

### "Database does not exist"

**Solution:** Create databases
```bash
createdb socrates_auth
createdb socrates_specs
```

### "Cannot connect to PostgreSQL"

**Check connection string in .env:**
```
DATABASE_URL_AUTH=postgresql://user:password@host:port/dbname
                  ├─ user: postgres
                  ├─ password: your-password
                  ├─ host: localhost
                  ├─ port: 5432
                  └─ dbname: socrates_auth
```

### "ANTHROPIC_API_KEY not set"

**Solution:** Add to .env
```bash
# Get key from https://console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-...
```

### "Port 8000 already in use"

**Solution:** Use different port
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### "Alembic migration fails"

**Solution:** Check database exists
```bash
alembic current  # Show current revision
alembic history  # Show all revisions
alembic upgrade head  # Apply all pending
```

---

## Docker Development

```bash
# Build development image
docker build -f Dockerfile.dev -t socrates2-dev .

# Run container
docker run -p 8000:8000 \
  -v $(pwd):/app \
  -e DATABASE_URL_AUTH=postgresql://postgres:password@host.docker.internal:5432/socrates_auth \
  socrates2-dev

# Or use docker-compose
docker-compose -f docker-compose.dev.yml up
```

---

## Next Steps

1. **Read [Architecture Guide](ARCHITECTURE.md)** - Understand codebase structure
2. **Read [Testing Guide](TESTING_GUIDE.md)** - Learn testing approach
3. **Review [Code Style](CODE_STYLE.md)** - Follow coding standards
4. **Check [Contributing Guide](CONTRIBUTING.md)** - Before submitting code
5. **Explore [API Reference](API_REFERENCE.md)** - Available endpoints

---

## Getting Help

- **Documentation:** [View Docs](../INDEX.md)
- **Issues:** [GitHub Issues](https://github.com/Nireus79/Socrates/issues)
- **Email:** support@socrates.app

---

**[← Back to Documentation Index](../INDEX.md)**

# CROSS-PLATFORM COMPATIBILITY GUIDE

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🔴 CRITICAL - Must complete before Phase 0

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Supported Platforms](#supported-platforms)
3. [Python 3.12 Installation](#python-312-installation)
4. [PostgreSQL 15 Installation](#postgresql-15-installation)
5. [Path Handling](#path-handling)
6. [Environment Variables](#environment-variables)
7. [Database Connection Strings](#database-connection-strings)
8. [CLI Executable Creation](#cli-executable-creation)
9. [Platform-Specific Considerations](#platform-specific-considerations)
10. [Testing Strategy](#testing-strategy)
11. [Common Issues & Solutions](#common-issues--solutions)

---

## OVERVIEW

**Socrates MUST work seamlessly on Windows, Linux, and macOS without code changes.**

### Why Cross-Platform Matters

1. **User Base Diversity**: Developers use all three platforms
2. **Team Collaboration**: Teams have mixed platform environments
3. **Development Flexibility**: Contributors shouldn't be locked to one OS
4. **Testing Coverage**: CI/CD needs to verify all platforms
5. **Professional Polish**: Production-grade software works everywhere

### Design Principles

✅ **Write Once, Run Everywhere**: No platform-specific branches
✅ **Use Standard Libraries**: Prefer `pathlib` over `os.path`
✅ **Test on All Platforms**: Automated CI/CD testing
✅ **Document Platform Differences**: Clear guidance when differences exist
✅ **Fail Gracefully**: Provide helpful error messages for platform issues

---

## SUPPORTED PLATFORMS

| Platform | Versions | Status | Notes |
|----------|----------|--------|-------|
| **Windows** | 10, 11 | ✅ Supported | PowerShell or CMD |
| **Linux** | Ubuntu 20.04+, Debian 11+, Fedora 35+ | ✅ Supported | Most distros work |
| **macOS** | 11 (Big Sur)+, 12 (Monterey), 13 (Ventura), 14 (Sonoma) | ✅ Supported | Intel & Apple Silicon |

### Minimum Requirements

- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB (8GB recommended)
- **Disk**: 2GB free space
- **Network**: Internet access for LLM APIs

---

## PYTHON 3.12 INSTALLATION

### Why Python 3.12?

- ✅ **Stable**: Released September 2023, battle-tested
- ✅ **Modern**: Latest features, performance improvements
- ✅ **Compatible**: Works with all our dependencies
- ❌ **Not 3.13/3.14**: Too new, potential edge cases

### Windows Installation

**Method 1: Official Installer (Recommended)**

```powershell
# 1. Download Python 3.12 from python.org
# URL: https://www.python.org/downloads/windows/

# 2. Run installer
# ✅ Check "Add Python 3.12 to PATH"
# ✅ Check "Install pip"
# ✅ Choose "Customize installation"
# ✅ Check "Install for all users"

# 3. Verify installation
python --version
# Expected output: Python 3.12.x

pip --version
# Expected output: pip 23.x from ...
```

**Method 2: Chocolatey**

```powershell
# Install Chocolatey first (if not installed)
# See: https://chocolatey.org/install

choco install python312 -y
python --version
```

**Method 3: winget (Windows Package Manager)**

```powershell
winget install Python.Python.3.12
python --version
```

### Linux Installation

**Ubuntu/Debian:**

```bash
# Update package list
sudo apt update

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Verify installation
python3.12 --version
# Expected output: Python 3.12.x

# Install pip
sudo apt install -y python3-pip

# Set Python 3.12 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

**Fedora/RHEL:**

```bash
# Install Python 3.12
sudo dnf install -y python3.12 python3.12-devel

# Verify installation
python3.12 --version
```

**Arch Linux:**

```bash
# Install Python 3.12
sudo pacman -S python312

# Verify installation
python3.12 --version
```

### macOS Installation

**Method 1: Homebrew (Recommended)**

```bash
# Install Homebrew first (if not installed)
# See: https://brew.sh

# Install Python 3.12
brew install python@3.12

# Verify installation
python3.12 --version
# Expected output: Python 3.12.x

# Link python3 to python3.12
brew link python@3.12
```

**Method 2: Official Installer**

```bash
# 1. Download Python 3.12 from python.org
# URL: https://www.python.org/downloads/macos/

# 2. Run .pkg installer

# 3. Verify installation
python3.12 --version
```

**Method 3: pyenv (Advanced)**

```bash
# Install pyenv
brew install pyenv

# Install Python 3.12
pyenv install 3.12.0

# Set as global version
pyenv global 3.12.0

# Verify
python --version
```

### Virtual Environment Setup (All Platforms)

**Windows:**

```powershell
# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\activate

# Verify
python --version
which python
```

**Linux/macOS:**

```bash
# Create virtual environment
python3.12 -m venv .venv

# Activate
source .venv/bin/activate

# Verify
python --version
which python
```

---

## POSTGRESQL 15 INSTALLATION

### Why PostgreSQL 15?

- ✅ **Production-Ready**: Stable, battle-tested
- ✅ **JSON Support**: Native JSONB for flexible metadata
- ✅ **ACID Compliance**: Data integrity guaranteed
- ✅ **Extensions**: pgvector for future semantic search
- ✅ **Concurrent Access**: Multi-user from day 1

### Windows Installation

**Method 1: Official Installer (Recommended)**

```powershell
# 1. Download PostgreSQL 15 from postgresql.org
# URL: https://www.postgresql.org/download/windows/

# 2. Run installer
# - Port: 5432 (default)
# - Superuser: postgres
# - Password: [choose strong password]
# - Locale: Default

# 3. Verify installation
psql --version
# Expected output: psql (PostgreSQL) 15.x

# 4. Test connection
psql -U postgres -h 127.0.0.1
# Enter password when prompted
```

**Method 2: Chocolatey**

```powershell
choco install postgresql15 -y

# Start service
Start-Service postgresql-x64-15

# Verify
psql --version
```

### Linux Installation

**Ubuntu/Debian:**

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Update and install
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify
psql --version
# Expected output: psql (PostgreSQL) 15.x

# Test connection
sudo -u postgres psql
```

**Fedora/RHEL:**

```bash
# Install PostgreSQL 15
sudo dnf install -y postgresql15-server postgresql15-contrib

# Initialize database
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb

# Start service
sudo systemctl start postgresql-15
sudo systemctl enable postgresql-15

# Verify
psql --version
```

### macOS Installation

**Method 1: Homebrew (Recommended)**

```bash
# Install PostgreSQL 15
brew install postgresql@15

# Start service
brew services start postgresql@15

# Verify
psql --version
# Expected output: psql (PostgreSQL) 15.x

# Test connection
psql postgres
```

**Method 2: Postgres.app**

```bash
# 1. Download Postgres.app from postgresapp.com
# 2. Drag to Applications folder
# 3. Open Postgres.app
# 4. Click "Initialize" for PostgreSQL 15

# Verify
psql --version
```

### Create Socrates Databases (All Platforms)

```bash
# Connect as postgres user
# Windows: psql -U postgres -h 127.0.0.1
# Linux: sudo -u postgres psql
# macOS: psql postgres

-- Create databases
CREATE DATABASE socrates_auth;
CREATE DATABASE socrates_specs;

-- Create user (optional, for production)
CREATE USER socrates_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE socrates_auth TO socrates_user;
GRANT ALL PRIVILEGES ON DATABASE socrates_specs TO socrates_user;

-- Verify databases exist
\l
-- Should show socrates_auth and socrates_specs

-- Exit
\q
```

---

## PATH HANDLING

### ❌ WRONG: Platform-Specific Path Code

```python
# BAD: Breaks on Windows
import os
config_path = "/home/user/.socrates/config.json"  # Unix-only

# BAD: Breaks on Linux/Mac
config_path = "C:\\Users\\user\\.socrates\\config.json"  # Windows-only

# BAD: String concatenation
config_path = base_dir + "/" + "config.json"  # Fragile
```

### ✅ CORRECT: Cross-Platform Path Handling

```python
from pathlib import Path

# Get home directory (works everywhere)
home = Path.home()
# Windows: C:\Users\username
# Linux: /home/username
# macOS: /Users/username

# Build paths using / operator (works on all platforms)
socrates_dir = home / ".socrates"
config_file = socrates_dir / "config.json"
projects_dir = socrates_dir / "projects"

# Create directories
socrates_dir.mkdir(parents=True, exist_ok=True)
projects_dir.mkdir(parents=True, exist_ok=True)

# Read/write files
config_data = config_file.read_text()
config_file.write_text(json.dumps(config))

# Check if exists
if config_file.exists():
    print(f"Config found at: {config_file}")

# Iterate directory
for project_file in projects_dir.glob("*.json"):
    print(f"Project: {project_file.name}")

# Convert to string when needed
config_path_str = str(config_file)
```

### Real Examples from Socrates

```python
# settings.py
from pathlib import Path

class Settings:
    """Cross-platform settings."""

    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent

    # User data directory
    USER_DATA_DIR = Path.home() / ".socrates"

    # Projects directory
    PROJECTS_DIR = USER_DATA_DIR / "projects"

    # Logs directory
    LOGS_DIR = USER_DATA_DIR / "logs"

    # Database files (if using SQLite for dev)
    DB_FILE = USER_DATA_DIR / "socrates.db"

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Usage in code
settings = Settings()
settings.ensure_directories()

# Load project
project_id = "abc123"
project_file = settings.PROJECTS_DIR / f"{project_id}.json"
if project_file.exists():
    project_data = json.loads(project_file.read_text())
```

---

## ENVIRONMENT VARIABLES

### Why .env Files?

- ✅ **Cross-Platform**: Same format on Windows/Linux/macOS
- ✅ **Security**: Keep secrets out of code
- ✅ **Flexibility**: Different configs per environment (dev/staging/prod)
- ✅ **Standard**: Widely supported by tools

### .env File Format

```bash
# .env file (works on all platforms)

# Database connections (auth database)
DATABASE_URL_AUTH=postgresql://socrates_user:password@localhost:5432/socrates_auth

# Database connections (specs database)
DATABASE_URL_SPECS=postgresql://socrates_user:password@localhost:5432/socrates_specs

# LLM API keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# Application settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (for React UI later)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Loading .env in Python

```python
# config/settings.py
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """Application settings loaded from environment variables."""

    # Database URLs
    DATABASE_URL_AUTH = os.getenv("DATABASE_URL_AUTH")
    DATABASE_URL_SPECS = os.getenv("DATABASE_URL_SPECS")

    # LLM API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Application
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    def validate(self):
        """Validate required settings are present."""
        required = [
            "DATABASE_URL_AUTH",
            "DATABASE_URL_SPECS",
            "ANTHROPIC_API_KEY",
            "SECRET_KEY",
            "JWT_SECRET_KEY",
        ]

        missing = [key for key in required if not getattr(self, key)]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Usage
settings = Settings()
settings.validate()
```

### .env.example Template

```bash
# .env.example
# Copy this file to .env and fill in your values

# Database connections
DATABASE_URL_AUTH=postgresql://socrates_user:password@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://socrates_user:password@localhost:5432/socrates_specs

# LLM API keys (get from providers)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Application settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=generate-a-secret-key-here
JWT_SECRET_KEY=generate-a-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (for React UI)
CORS_ORIGINS=http://localhost:3000
```

---

## DATABASE CONNECTION STRINGS

### The Windows DNS Problem

**Issue**: On Windows, `localhost` sometimes fails to resolve to `127.0.0.1`, causing connection failures.

**Solution**: Detect platform and use `127.0.0.1` on Windows.

### Cross-Platform Database URLs

```python
# config/database.py
import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def get_db_host():
    """Get database host (fixes Windows localhost DNS issues)."""
    if platform.system() == "Windows":
        return "127.0.0.1"
    return "localhost"

def get_database_url(db_name: str) -> str:
    """
    Build database URL with platform-specific host.

    Args:
        db_name: Database name (socrates_auth or socrates_specs)

    Returns:
        Database URL string
    """
    host = get_db_host()
    user = os.getenv("DB_USER", "socrates_user")
    password = os.getenv("DB_PASSWORD", "password")
    port = os.getenv("DB_PORT", "5432")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

# Create engines
engine_auth = create_engine(
    get_database_url("socrates_auth"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Test connections before using
)

engine_specs = create_engine(
    get_database_url("socrates_specs"),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Create session factories
SessionAuth = sessionmaker(bind=engine_auth)
SessionSpecs = sessionmaker(bind=engine_specs)
```

### Alternative: Direct .env Configuration

```bash
# .env file

# Option 1: Let Python detect platform (recommended)
DB_HOST=auto  # Will use 127.0.0.1 on Windows, localhost elsewhere

# Option 2: Explicit IP (works everywhere)
DB_HOST=127.0.0.1

# Option 3: Explicit localhost (may fail on Windows)
DB_HOST=localhost
```

```python
def get_db_host():
    """Get database host from env or auto-detect."""
    host = os.getenv("DB_HOST", "auto")

    if host == "auto":
        return "127.0.0.1" if platform.system() == "Windows" else "localhost"

    return host
```

---

## CLI EXECUTABLE CREATION

### Goal: Run Socrates CLI Cross-Platform

**Windows**: `socrates` or `socrates.exe`
**Linux/macOS**: `socrates`

### Method 1: setup.py (Deprecated but Works)

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="socrates",
    version="2.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.121.0",
        "sqlalchemy>=2.0.44",
        "pydantic>=2.12.3",
        "anthropic>=0.25.0",
        # ... other dependencies
    ],
    entry_points={
        "console_scripts": [
            "socrates=cli.main:main",  # socrates command → cli/main.py:main()
        ],
    },
    python_requires=">=3.12",
)

# Install: pip install -e .
# Run: socrates
```

### Method 2: pyproject.toml (Modern, Recommended)

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "socrates"
version = "2.0.0"
description = "Socrates: AI-powered specification system"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.121.0",
    "sqlalchemy>=2.0.44",
    "pydantic>=2.12.3",
    "alembic>=1.12.0",
    "anthropic>=0.25.0",
    "python-dotenv>=1.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "psycopg2-binary>=2.9.9",
]

[project.scripts]
socrates = "cli.main:main"

[tool.setuptools.packages.find]
where = ["src"]
```

```bash
# Install in development mode (all platforms)
pip install -e .

# Now 'socrates' command works everywhere
socrates --help
socrates create-project "My App"
socrates chat
```

### Method 3: Direct Python Module (Quick Dev)

```python
# cli/main.py
def main():
    print("Socrates CLI v2.0.0")
    # ... CLI logic

if __name__ == "__main__":
    main()

# Run directly (all platforms)
python -m cli.main
```

```bash
# Create alias/shortcut

# Windows (PowerShell profile)
function socrates { python -m cli.main @args }

# Linux/macOS (bash/zsh)
alias socrates='python -m cli.main'
```

---

## PLATFORM-SPECIFIC CONSIDERATIONS

### File Permissions

**Linux/macOS:**

```bash
# Make CLI executable
chmod +x cli/main.py

# Run directly
./cli/main.py
```

**Windows:**

No need for permissions; `.py` files associated with Python.

### Line Endings

**Issue**: Windows uses `\r\n` (CRLF), Linux/macOS use `\n` (LF).

**Solution**: Configure Git to normalize line endings.

```bash
# .gitattributes file
* text=auto
*.py text eol=lf
*.sh text eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf
```

### Shell Scripts

**Linux/macOS (bash):**

```bash
#!/usr/bin/env bash
# scripts/start_server.sh

source .venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Windows (PowerShell):**

```powershell
# scripts/start_server.ps1

.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Windows (Batch):**

```batch
@echo off
REM scripts/start_server.bat

call .venv\Scripts\activate.bat
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Process Management

**Linux/macOS:**

```python
import subprocess

# Run background process
process = subprocess.Popen(
    ["python", "-m", "uvicorn", "api.main:app"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Kill process
process.terminate()
```

**Windows:**

```python
import subprocess
import platform

def start_server():
    """Start FastAPI server (cross-platform)."""
    if platform.system() == "Windows":
        # Windows: use CREATE_NEW_CONSOLE to avoid terminal issues
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "api.main:app"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    else:
        # Linux/macOS: standard
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "api.main:app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    return process
```

---

## TESTING STRATEGY

### Automated Cross-Platform Testing

**GitHub Actions CI/CD:**

```yaml
# .github/workflows/test.yml
name: Cross-Platform Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Manual Testing Checklist

**Before Each Release:**

- [ ] **Windows 10**: Test installation, run tests, create project, chat
- [ ] **Windows 11**: Test installation, run tests, create project, chat
- [ ] **Ubuntu 22.04**: Test installation, run tests, create project, chat
- [ ] **macOS 13 (Intel)**: Test installation, run tests, create project, chat
- [ ] **macOS 14 (Apple Silicon)**: Test installation, run tests, create project, chat

**Test Cases:**

1. Python 3.12 installation
2. Virtual environment creation
3. Dependency installation
4. PostgreSQL connection
5. Database creation
6. CLI commands (`socrates --help`)
7. Create project
8. Start chat session
9. Toggle modes
10. Path handling (read/write files)
11. Environment variable loading
12. Server start/stop

---

## COMMON ISSUES & SOLUTIONS

### Issue 1: Python Not Found

**Symptoms:**

```bash
python: command not found  # Linux/macOS
'python' is not recognized  # Windows
```

**Solutions:**

```bash
# Try python3 instead
python3 --version

# Or use full path
/usr/bin/python3.12 --version  # Linux
C:\Python312\python.exe --version  # Windows

# Fix PATH
# Linux/macOS: Add to ~/.bashrc or ~/.zshrc
export PATH="/usr/local/bin:$PATH"

# Windows: Add to System Environment Variables
# Control Panel → System → Advanced → Environment Variables
# Add C:\Python312 to PATH
```

### Issue 2: PostgreSQL Connection Failed

**Symptoms:**

```python
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**

**Check PostgreSQL is running:**

```bash
# Windows
Get-Service postgresql*

# Linux
sudo systemctl status postgresql

# macOS
brew services list
```

**Start PostgreSQL:**

```bash
# Windows
Start-Service postgresql-x64-15

# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql@15
```

**Check connection:**

```bash
# Windows
psql -U postgres -h 127.0.0.1

# Linux
sudo -u postgres psql

# macOS
psql postgres
```

**Fix localhost DNS (Windows):**

```python
# Use 127.0.0.1 instead of localhost
DATABASE_URL="postgresql://user:pass@127.0.0.1:5432/socrates_auth"
```

### Issue 3: Permission Denied

**Symptoms:**

```bash
PermissionError: [Errno 13] Permission denied: '/home/user/.socrates'
```

**Solutions:**

```bash
# Linux/macOS: Check permissions
ls -la ~/.socrates
chmod 755 ~/.socrates

# Windows: Run as Administrator (only if necessary)
# Right-click Command Prompt → Run as Administrator
```

### Issue 4: Module Not Found

**Symptoms:**

```python
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**

```bash
# Ensure virtual environment is activated
# Windows
.\.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# Verify correct environment
which python
python -m pip list

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 5: .env File Not Loaded

**Symptoms:**

```python
ValueError: Missing required environment variables
```

**Solutions:**

```bash
# Check .env file exists
ls -la .env  # Linux/macOS
dir .env  # Windows

# Check .env file location (should be in project root)
# .env must be in same directory as main.py or explicitly loaded

# Explicitly load .env
from dotenv import load_dotenv
load_dotenv(dotenv_path="/absolute/path/to/.env")
```

### Issue 6: Line Ending Issues

**Symptoms:**

```bash
bash: ./script.sh: /bin/bash^M: bad interpreter
```

**Solutions:**

```bash
# Convert CRLF to LF (Windows to Unix)
# Linux/macOS
dos2unix script.sh

# Or use sed
sed -i 's/\r$//' script.sh

# Git config (prevent in future)
git config --global core.autocrlf input  # Linux/macOS
git config --global core.autocrlf true  # Windows
```

---

## VERIFICATION CHECKLIST

Before proceeding to Phase 0, verify:

### Windows

- [ ] Python 3.12 installed and in PATH
- [ ] PostgreSQL 15 installed and running
- [ ] Virtual environment creates successfully
- [ ] Dependencies install without errors
- [ ] Database connection works (using 127.0.0.1)
- [ ] CLI command runs (`socrates --help`)
- [ ] Path handling works (files read/write to `.socrates/`)
- [ ] Environment variables load from `.env`

### Linux

- [ ] Python 3.12 installed
- [ ] PostgreSQL 15 installed and running
- [ ] Virtual environment creates successfully
- [ ] Dependencies install without errors
- [ ] Database connection works
- [ ] CLI command runs (`socrates --help`)
- [ ] Path handling works (files read/write to `~/.socrates/`)
- [ ] Environment variables load from `.env`
- [ ] Scripts have correct permissions (`chmod +x`)

### macOS

- [ ] Python 3.12 installed (Intel & Apple Silicon)
- [ ] PostgreSQL 15 installed and running
- [ ] Virtual environment creates successfully
- [ ] Dependencies install without errors
- [ ] Database connection works
- [ ] CLI command runs (`socrates --help`)
- [ ] Path handling works (files read/write to `~/.socrates/`)
- [ ] Environment variables load from `.env`

### All Platforms

- [ ] Automated tests pass (pytest)
- [ ] Path handling uses `pathlib` (not `os.path`)
- [ ] No hardcoded paths (use `Path.home()`)
- [ ] Database URLs use platform detection for host
- [ ] `.env` file loads correctly
- [ ] CLI executable works without `.py` extension
- [ ] No platform-specific code branches (unless documented here)

---

## NEXT STEPS

After completing this guide:

1. ✅ Review and approve this document
2. → Create SECURITY_GUIDE.md (JWT, bcrypt, secrets)
3. → Create DEVELOPMENT_SETUP.md (step-by-step setup)
4. → Create TESTING_STRATEGY.md (test plan)
5. → Create LLM_ABSTRACTION_LAYER.md (multi-LLM support)

**Estimated Time to Complete All 5 Critical Docs:** 4-5 days

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This document ensures Socrates works seamlessly on Windows, Linux, and macOS without code changes.*

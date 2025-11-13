# Socrates2 Inconsistency Resolution Plan

**Date:** November 12, 2025
**Status:** PLANNING PHASE
**Priority:** CRITICAL (blocks production release)

---

## Overview

This document provides a detailed plan to resolve the 4 major architectural inconsistencies identified in the deep investigation. The plan is organized by priority and includes specific steps, impact analysis, and success criteria.

---

## Issue #1: Wrong CLI Entry Point (CRITICAL)

### Current State
```toml
# pyproject.toml Line 70
[project.scripts]
socrates = "app.cli:main"  ✗ WRONG - Function doesn't exist
```

```python
# backend/app/cli/__init__.py Line 7
from .main import cli  # Exports "cli", not "main"

# backend/app/cli/main.py Line 32
@click.group(invoke_without_command=True)
def cli(ctx):  # Function named "cli", NOT "main"
```

### Fix Strategy: SIMPLE (1 line change)

**Step 1: Update pyproject.toml**
```diff
  [project.scripts]
- socrates = "app.cli:main"
+ socrates = "app.cli:cli"
```

**Step 2: Verify Fix**
```bash
cd /home/user/Socrates2/backend
pip install -e .  # Should succeed without errors
which socrates    # Should show path to executable
socrates --help   # Should display Click help menu
```

**Step 3: Create Test**
```python
# backend/test_cli_entry_point.py
def test_cli_entry_point_exists():
    """Verify app.cli:cli exists and is callable"""
    from app.cli import cli
    assert callable(cli)
    assert cli.name == "cli"  # Click group name

def test_package_installation():
    """Verify pip install -e . works"""
    result = subprocess.run(["pip", "install", "-e", "."],
                          cwd="backend/")
    assert result.returncode == 0

    # Verify socrates command works
    result = subprocess.run(["socrates", "--help"])
    assert result.returncode == 0
```

### Impact
- ✓ Package can be installed
- ✓ `socrates` command becomes available
- ✓ Entry point matches implementation
- ⚠ Only affects app/cli (not root Socrates.py)

### Success Criteria
- [ ] `pip install -e backend/` succeeds
- [ ] `socrates --help` works
- [ ] Tests pass for entry point

---

## Issue #2: Two CLI Implementations (HIGH)

### Current State
| Aspect | Socrates.py (Root) | app/cli/main.py (Backend) |
|--------|-------------------|---------------------------|
| Location | /Socrates.py | /backend/app/cli/main.py |
| Type | HTTP client | Click admin tool |
| Framework | Rich + prompt_toolkit | Click |
| Purpose | Interactive GUI client | Domain/workflow admin |
| Status | Actively tested | Exists but unclear role |
| Version | Implicit | v0.1.0 |

### Problem
1. Two separate entry points exist
2. Different purposes but similar names
3. Tests only cover one
4. Users confused which to use

### Fix Strategy: CLARIFICATION + MINIMAL CONSOLIDATION

#### Option A: Recommended (Keep Both, Clarify Roles)

**Architecture Decision:**
```
Socrates.py (Root)
├─ Purpose: End-user interactive CLI client
├─ Entry: Direct execution: python Socrates.py
├─ Communication: HTTP to backend server
├─ Maintained: Actively
└─ Version: Match pyproject.toml version (0.2.0)

backend/app/cli/main.py
├─ Purpose: Backend admin/management CLI
├─ Entry: Via pip: socrates domain list
├─ Communication: Direct imports (no HTTP)
├─ Maintained: Actively
├─ Rename to: app/admin_cli (avoid confusion)
└─ Version: Independent version tracking
```

**Implementation Steps:**

**Step 1: Rename Backend CLI Module**
```bash
cd /home/user/Socrates2/backend/app
mv cli admin_cli
```

**Step 2: Update Imports**
```python
# backend/pyproject.toml
[project.scripts]
- socrates = "app.cli:cli"
+ socrates-admin = "app.admin_cli:cli"  # Different name, different purpose
```

**Step 3: Update __init__ files**
```python
# backend/app/__init__.py
- from . import cli
+ from . import admin_cli
```

**Step 4: Update imports in backend/app/main.py**
```python
# If main.py imports from app.cli, update to:
- from app.cli.main import cli
+ from app.admin_cli.main import cli
```

**Step 5: Document in README**
```markdown
## Socrates CLI - Two Tools

### 1. End-User CLI: Socrates.py
Usage: `python Socrates.py [--api-url URL] [--debug]`
- Interactive GUI for creating specifications
- Requires backend server running
- Uses HTTP API

### 2. Admin CLI: socrates-admin
Usage: `socrates-admin domain list`
- Backend administration tool
- Manage domains, workflows, configurations
- Direct database access
```

**Step 6: Create Integration Tests**
```python
# backend/test_cli_integration.py
def test_socrates_py_available():
    """User CLI available at project root"""
    assert Path("/Socrates.py").exists()
    result = subprocess.run(["python", "/Socrates.py", "--help"])
    assert result.returncode == 0

def test_admin_cli_available():
    """Admin CLI available via pip install"""
    result = subprocess.run(["socrates-admin", "--help"])
    assert result.returncode == 0

def test_cli_apis_different():
    """Verify CLIs have different command structures"""
    # Socrates.py uses different commands than admin CLI
    socrates_help = subprocess.check_output(
        ["python", "/Socrates.py", "--help"],
        text=True
    )
    admin_help = subprocess.check_output(
        ["socrates-admin", "--help"],
        text=True
    )
    assert socrates_help != admin_help
    assert "domain" not in socrates_help  # User CLI doesn't need domain cmds
    assert "domain" in admin_help         # Admin CLI has domain cmds
```

#### Option B: Merge into One (Complex, Not Recommended)

Would require:
1. Rewriting one CLI to match the other
2. Deciding on framework (Click vs Rich)
3. Rewriting communication layer
4. Extensive testing

**Recommendation:** Not worth it. Option A is cleaner.

---

## Issue #3: Circular Dependency (HIGH)

### Current State
```bash
# backend/requirements.txt
fastapi==0.121.0
...
# socrates-ai is installed from the local backend directory via setup.py
```

```toml
# backend/pyproject.toml
[project]
name = "socrates-ai"
version = "0.2.0"
```

### Problem
1. Confusing comment
2. Creates ambiguity about which version is used
3. Breaks standard Python packaging conventions
4. Can't upload to PyPI with this setup

### Fix Strategy: REMOVE REFERENCE (Simple)

**Step 1: Remove from requirements.txt**
```diff
  fastapi==0.121.0
  uvicorn[standard]==0.34.0
- # socrates-ai is installed from the local backend directory via setup.py
```

**Step 2: Update Installation Instructions**

In `backend/README.md`:
```markdown
## Installation

### Development Setup
```bash
cd backend/
pip install -e .              # Install socrates-ai package
pip install -r requirements-dev.txt  # Install dev dependencies
```

This replaces explicit requirement with implicit local installation.
```

**Step 3: Update Setup Instructions**

In root `README.md`:
```markdown
## Local Development Setup

1. Install backend package:
   ```bash
   cd backend/
   pip install -e .            # Installs socrates-ai locally
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```bash
   python -m pytest tests/
   ```
```

### Impact
- ✓ Removes confusion
- ✓ Follows Python packaging standards
- ✓ Allows future PyPI distribution
- ✓ No functional change (backward compatible)

### Success Criteria
- [ ] requirements.txt doesn't mention socrates-ai
- [ ] `pip install -e backend/` still works
- [ ] README clearly explains installation order

---

## Issue #4: Database Setup Conflicts (MEDIUM)

### Current State
```
Production/Testing: Alembic migrations
├─ backend/alembic/versions/001_create_users_table.py
├─ backend/alembic/versions/002_create_refresh_tokens_table.py
├─ backend/alembic/versions/003_create_projects_table.py
└─ backend/alembic/versions/004_create_sessions_table.py

Quick Testing: SQLAlchemy create_all
└─ backend/init_test_db.py (Base.metadata.create_all)
```

### Problem
1. Two different initialization paths
2. No clear guidance on which to use
3. Can conflict in edge cases
4. Tests use init_test_db.py, but production needs Alembic

### Fix Strategy: FORMALIZE AND DOCUMENT

**Step 1: Keep Both, Clarify Purpose**

```markdown
# Database Setup Strategy

## For Production/Staging
Use Alembic migrations for version control and audit trail:
```bash
cd backend/
alembic upgrade head
```

## For Local Development/Testing
Use fast SQLAlchemy initialization:
```bash
cd backend/
python init_test_db.py
```

## Important: Don't Mix Methods
- ✗ Don't run alembic after init_test_db.py (confuses version tracking)
- ✗ Don't run init_test_db.py after alembic (overwrites migration state)
- ✓ Pick one method and stick with it per environment
```

**Step 2: Enhance init_test_db.py with Warning**

```python
# backend/init_test_db.py
"""
Initialize test databases using SQLAlchemy create_all.

⚠️ WARNING: Use this ONLY for local development/testing!
For production deployments, use Alembic migrations instead:
    cd backend/
    alembic upgrade head

Mixing init_test_db.py and Alembic can cause schema conflicts.
"""

import logging
logger = logging.getLogger(__name__)

def init_test_databases():
    """Create all tables in both test databases."""
    logger.warning("=" * 70)
    logger.warning("Using SQLAlchemy create_all for database initialization")
    logger.warning("This is for LOCAL TESTING ONLY")
    logger.warning("For production, use: alembic upgrade head")
    logger.warning("=" * 70)

    # ... rest of initialization
```

**Step 3: Create init_database.py Wrapper**

```python
# backend/init_database.py
"""
Database initialization wrapper with environment detection.
Automatically chooses the right initialization method.
"""

import os
import subprocess
from pathlib import Path

def init_database(mode="auto"):
    """
    Initialize database based on mode.

    Args:
        mode: 'production' (alembic), 'test' (create_all), 'auto' (detect)
    """

    if mode == "auto":
        # Detect based on environment
        env = os.getenv("ENVIRONMENT", "development")
        mode = "production" if env == "production" else "test"

    if mode == "production":
        print("Running Alembic migrations...")
        result = subprocess.run(["alembic", "upgrade", "head"])
        return result.returncode == 0

    elif mode == "test":
        print("Running SQLAlchemy create_all...")
        from init_test_db import init_test_databases
        init_test_databases()
        return True

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    success = init_database(mode)
    sys.exit(0 if success else 1)
```

**Step 4: Document in README**

```markdown
## Database Initialization

### For Development (Quick)
```bash
python backend/init_database.py test
# or
python backend/init_test_db.py
```

### For Production (Versioned)
```bash
alembic upgrade head
```

### Automatic Detection
```bash
python backend/init_database.py
# Automatically chooses based on ENVIRONMENT variable
```
```

**Step 5: Add Tests**

```python
# backend/test_database_setup.py
def test_alembic_migrations_exist():
    """Verify migration files exist"""
    migrations_dir = Path("alembic/versions")
    migration_files = list(migrations_dir.glob("*.py"))
    assert len(migration_files) >= 4
    assert any("users" in f.name for f in migration_files)

def test_init_test_db_works():
    """Verify quick initialization works"""
    result = subprocess.run(["python", "init_test_db.py"])
    assert result.returncode == 0

def test_alembic_upgrade_works():
    """Verify alembic upgrade succeeds"""
    # Setup fresh test DB
    os.environ["DATABASE_URL_AUTH"] = "sqlite:///test_alembic.db"
    result = subprocess.run(["alembic", "upgrade", "head"])
    assert result.returncode == 0

def test_dont_mix_methods():
    """Warn against mixing initialization methods"""
    # This test documents the warning
    assert "Don't mix" in Path("backend/README.md").read_text()
```

### Impact
- ✓ Both methods still available
- ✓ Clear guidance on when to use each
- ✓ Prevents conflicts through documentation
- ✓ Automated selection available

---

## Implementation Timeline

### Week 1: CRITICAL FIXES
- [ ] Fix CLI entry point (1 hour)
- [ ] Verify package installation (1 hour)
- [ ] Remove circular dependency (30 mins)
- [ ] Test all three fixes (2 hours)
- **Total: ~4.5 hours**

### Week 2: HIGH PRIORITY
- [ ] Rename backend CLI module (2 hours)
- [ ] Update all imports (2 hours)
- [ ] Create CLI integration tests (3 hours)
- [ ] Document two CLI roles (2 hours)
- **Total: ~9 hours**

### Week 3: MEDIUM PRIORITY
- [ ] Formalize database strategy (2 hours)
- [ ] Create init_database.py wrapper (2 hours)
- [ ] Add database conflict tests (2 hours)
- [ ] Update documentation (2 hours)
- **Total: ~8 hours**

### Week 4: VALIDATION
- [ ] Run full test suite (1 hour)
- [ ] Test package installation from scratch (1 hour)
- [ ] Verify all CLIs work (1 hour)
- [ ] Create end-to-end test (2 hours)
- **Total: ~5 hours**

**Grand Total: ~26.5 hours (approximately 1 person-week)**

---

## Rollback Plan

If issues arise during implementation:

### Quick Rollback (if needed mid-implementation)
```bash
# Revert recent commits
git revert <commit-hash>

# Or for incomplete work
git reset --hard origin/branch-name
```

### Testing Strategy
1. All changes made on feature branch
2. Full test suite run before merge
3. Integration tests verify functionality
4. Code review before merge to main

---

## Success Metrics

After completing all fixes:

| Metric | Current | Target | Test |
|--------|---------|--------|------|
| Package installation | ✗ Fails | ✓ Works | `pip install -e .` |
| CLI entry point | ✗ Wrong | ✓ Correct | `socrates --help` |
| Circular dependency | ✗ Exists | ✓ Removed | Check requirements.txt |
| Database strategy | ✗ Unclear | ✓ Clear | Documentation |
| Integration tests | ✗ 0 | ✓ 10+ | Test suite |
| Package ready | ✗ No | ✓ Yes | Can upload to PyPI |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Breaking existing tests | Medium | High | Run full test suite before merge |
| Import path confusion | Low | Medium | Update all imports systematically |
| Database migration issues | Low | High | Test both initialization methods |
| User confusion | High | Low | Document clearly in README |

---

## Dependencies

- All work depends on fixing the CLI entry point first
- Database fixes can proceed in parallel with CLI fixes
- Documentation updates should happen last

---

## Approval & Sign-Off

- [ ] Technical review of plan
- [ ] Timeline agreement
- [ ] Risk mitigation approval
- [ ] Start implementation


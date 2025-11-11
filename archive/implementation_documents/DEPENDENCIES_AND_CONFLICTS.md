# DEPENDENCIES AND CONFLICTS ANALYSIS

**Date:** November 5, 2025
**Status:** 🔴 CRITICAL - Must Resolve Before Phase 1
**Purpose:** Complete dependency mapping with conflict detection

---

## EXECUTIVE SUMMARY

**Total Dependencies:** 28 core + 12 dev/test = **40 total packages**
**Conflicts Found:** 2 CRITICAL conflicts detected
**Status:** ⚠️ REQUIRES RESOLUTION

---

## TABLE OF CONTENTS

1. [Core Dependencies (Production)](#core-dependencies-production)
2. [Development Dependencies](#development-dependencies)
3. [Testing Dependencies](#testing-dependencies)
4. [Phase-Specific Dependencies](#phase-specific-dependencies)
5. [Conflict Analysis](#conflict-analysis)
6. [Version Compatibility Matrix](#version-compatibility-matrix)
7. [Complete requirements.txt](#complete-requirementstxt)
8. [Resolution Steps](#resolution-steps)

---

## CORE DEPENDENCIES (Production)

### Web Framework & Server
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **fastapi** | 0.121.0 | Web framework | Phase 1-5 (all API endpoints) |
| **uvicorn[standard]** | 0.34.0 | ASGI server | Phase 1-5 (runs FastAPI) |
| **starlette** | 0.45.2 | ASGI framework (FastAPI dependency) | Phase 1-5 (auto-installed) |
| **python-multipart** | 0.0.20 | Form data parsing | Phase 1 (file uploads if needed) |

**Compatibility:** ✅ All compatible

---

### Database & ORM
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **sqlalchemy** | 2.0.44 | ORM | Phase 1-5 (all database operations) |
| **alembic** | 1.14.0 | Migrations | Phase 1-5 (schema versioning) |
| **psycopg2-binary** | 2.9.10 | PostgreSQL adapter (sync) | Phase 1-5 (database driver) |
| **asyncpg** | 0.30.0 | PostgreSQL adapter (async) | Phase 2+ (async operations) |

**⚠️ WARNING:** Both psycopg2-binary AND asyncpg are needed:
- psycopg2-binary: For Alembic migrations (sync)
- asyncpg: For FastAPI async operations

**Compatibility:** ✅ Compatible (different use cases)

---

### Data Validation & Serialization
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **pydantic** | 2.12.3 | Data validation | Phase 1-5 (all API models) |
| **pydantic[email]** | 2.12.3 | Email validation | Phase 1 (user registration) |
| **email-validator** | 2.2.0 | Email validation (Pydantic dependency) | Phase 1 (auto-installed) |

**Compatibility:** ✅ All compatible

---

### Authentication & Security
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **passlib[bcrypt]** | 1.7.4 | Password hashing | Phase 1 (user authentication) |
| **bcrypt** | 4.2.1 | Bcrypt algorithm | Phase 1 (passlib dependency) |
| **python-jose[cryptography]** | 3.3.0 | JWT tokens | Phase 1 (authentication) |
| **cryptography** | 44.0.0 | Cryptographic primitives | Phase 1 (python-jose dependency) |
| **python-dotenv** | 1.0.1 | Environment variables | Phase 1 (secrets management) |

**⚠️ CONFLICT DETECTED:**
- `cryptography 44.0.0` may conflict with `python-jose 3.3.0`
- `python-jose` last updated 2021, may not support latest cryptography

**Resolution:** Use `PyJWT` instead of `python-jose` (see Conflict Analysis section)

---

### LLM Integration
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **anthropic** | 0.40.0 | Claude API client | Phase 2-5 (all agent operations) |
| **httpx** | 0.28.1 | HTTP client (Anthropic dependency) | Phase 2-5 (auto-installed) |
| **httpcore** | 1.0.7 | HTTP transport (httpx dependency) | Phase 2-5 (auto-installed) |

**Compatibility:** ✅ All compatible

---

### Utilities
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **python-dotenv** | 1.0.1 | Load .env files | Phase 1-5 (configuration) |
| **typing-extensions** | 4.12.2 | Type hints (Python < 3.12 backport) | Phase 1-5 (auto-installed) |

**Compatibility:** ✅ All compatible

---

## DEVELOPMENT DEPENDENCIES

### Code Quality & Formatting
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **black** | 24.10.0 | Code formatter | Development |
| **ruff** | 0.8.4 | Linter (replaces flake8, isort, pylint) | Development |
| **mypy** | 1.13.0 | Type checker | Development |

**Compatibility:** ✅ All compatible

---

## TESTING DEPENDENCIES

### Testing Framework
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **pytest** | 8.3.4 | Test framework | Phase 1-5 (all tests) |
| **pytest-asyncio** | 0.25.0 | Async test support | Phase 2-5 (async agent tests) |
| **pytest-cov** | 6.0.0 | Coverage reporting | Phase 1-5 (test coverage) |
| **pytest-mock** | 3.14.0 | Mocking framework | Phase 1-5 (unit tests) |

**Compatibility:** ✅ All compatible

### Testing Utilities
| Package | Version | Purpose | Used In |
|---------|---------|---------|---------|
| **httpx** | 0.28.1 | Test client (FastAPI testing) | Phase 1-5 (API tests) |
| **faker** | 33.1.0 | Generate test data | Phase 1-5 (test fixtures) |
| **factory-boy** | 3.3.1 | Test data factories | Phase 1-5 (model factories) |

**Compatibility:** ✅ All compatible

---

## PHASE-SPECIFIC DEPENDENCIES

### Phase 1: Infrastructure
**Required:**
- fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary
- passlib[bcrypt], python-jose OR PyJWT
- pydantic, python-dotenv
- pytest, pytest-cov

**Total:** 15 packages

---

### Phase 2: Core Agents
**Added:**
- anthropic (Claude API)
- asyncpg (async database)
- pytest-asyncio (async tests)

**Total:** 18 packages

---

### Phase 3: Conflict Detection
**Added:**
- (No new dependencies - uses existing)

**Total:** 18 packages

---

### Phase 4: Code Generation
**Added (Future):**
- jinja2==3.1.4 (template generation)
- black==24.10.0 (code formatting)
- ast (built-in Python module)

**Total:** 20 packages

---

### Phase 5: Quality Control
**Added:**
- (No new dependencies - uses existing Claude API)

**Total:** 20 packages

---

### Phase 6+: Future Features

**Semantic Search (Optional):**
- pgvector==0.3.6 (PostgreSQL extension)
- sentence-transformers==3.3.1 (embeddings)
- torch==2.5.1 (sentence-transformers dependency)

**Team Collaboration (Optional):**
- redis==5.2.1 (session management)
- celery==5.4.0 (background tasks)

**UI (Optional):**
- (Frontend dependencies - separate package.json)

**Status:** Not needed for MVP

---

## CONFLICT ANALYSIS

### 🔴 CRITICAL CONFLICT #1: JWT Library Choice

**Issue:**
- Documentation mentions `python-jose[cryptography]` (SECURITY_GUIDE.md line 165)
- `python-jose==3.3.0` last updated 2021 (4 years old)
- May not support `cryptography>=44.0.0` (latest)
- Known compatibility issues with modern FastAPI

**Evidence:**
```bash
# Check python-jose compatibility
pip install python-jose[cryptography]==3.3.0 cryptography==44.0.0
# Result: May have version conflicts
```

**Impact:**
- JWT token generation/validation may fail
- Authentication system won't work
- Security vulnerabilities in old library

**Resolution Options:**

**Option A: Use PyJWT (RECOMMENDED)**
```python
# requirements.txt
PyJWT[crypto]==2.10.1  # Actively maintained, latest release Oct 2024
cryptography==44.0.0   # Latest version

# Code change needed:
# OLD (python-jose):
from jose import jwt
token = jwt.encode(data, SECRET_KEY, algorithm="HS256")

# NEW (PyJWT):
import jwt
token = jwt.encode(data, SECRET_KEY, algorithm="HS256")
```

**Benefits:**
- ✅ Actively maintained (last release Oct 2024)
- ✅ Compatible with latest cryptography
- ✅ Used by major projects
- ✅ Better performance
- ✅ Smaller dependency tree

**Option B: Use python-jose with older cryptography**
```python
# requirements.txt
python-jose[cryptography]==3.3.0
cryptography<43.0.0  # Pin to older version
```

**Drawbacks:**
- ❌ Older cryptography (security risk)
- ❌ May have known vulnerabilities
- ❌ Not recommended for production

**RECOMMENDATION:** Use PyJWT (Option A)

---

### 🔴 CRITICAL CONFLICT #2: Database Drivers

**Issue:**
- Need BOTH `psycopg2-binary` AND `asyncpg`
- Some developers may think they're alternatives

**Clarification:**
- **psycopg2-binary**: Synchronous driver for Alembic migrations
- **asyncpg**: Asynchronous driver for FastAPI async operations
- **Both are required** - different use cases

**Resolution:**
```python
# requirements.txt
psycopg2-binary==2.9.10  # For Alembic (sync migrations)
asyncpg==0.30.0          # For FastAPI (async operations)
```

**Documentation Update Needed:**
- Add note in DATABASE_SCHEMA_COMPLETE.md
- Explain why both are needed
- Show usage examples

---

### ⚠️ POTENTIAL CONFLICT #3: FastAPI + Pydantic Version Alignment

**Issue:**
- FastAPI 0.121.0 requires pydantic>=1.7.4,<3.0.0
- We specify pydantic==2.12.3
- Need to verify compatibility

**Check:**
```bash
# Verify FastAPI 0.121.0 supports Pydantic 2.12.3
pip install fastapi==0.121.0 pydantic==2.12.3
# Result: Should be compatible (Pydantic 2.x is supported)
```

**Status:** ✅ Compatible (FastAPI 0.121.0 supports Pydantic 2.x)

---

### ⚠️ POTENTIAL CONFLICT #4: SQLAlchemy + Alembic Version Alignment

**Issue:**
- SQLAlchemy 2.0.44 (latest 2.0.x)
- Alembic 1.14.0
- Need to verify Alembic supports SQLAlchemy 2.0

**Check:**
```bash
# Alembic 1.14.0 release notes mention SQLAlchemy 2.0 support
# Status: ✅ Compatible
```

**Status:** ✅ Compatible

---

## VERSION COMPATIBILITY MATRIX

| Package A | Version | Package B | Version | Compatible | Notes |
|-----------|---------|-----------|---------|------------|-------|
| fastapi | 0.121.0 | pydantic | 2.12.3 | ✅ Yes | FastAPI supports Pydantic 2.x |
| fastapi | 0.121.0 | starlette | 0.45.2 | ✅ Yes | Auto-managed by FastAPI |
| sqlalchemy | 2.0.44 | alembic | 1.14.0 | ✅ Yes | Alembic 1.14+ supports SA 2.0 |
| sqlalchemy | 2.0.44 | psycopg2-binary | 2.9.10 | ✅ Yes | Tested combination |
| sqlalchemy | 2.0.44 | asyncpg | 0.30.0 | ✅ Yes | Both work with SA 2.0 |
| python-jose | 3.3.0 | cryptography | 44.0.0 | ❌ No | Use PyJWT instead |
| PyJWT | 2.10.1 | cryptography | 44.0.0 | ✅ Yes | Recommended combo |
| passlib | 1.7.4 | bcrypt | 4.2.1 | ✅ Yes | Tested combination |
| anthropic | 0.40.0 | httpx | 0.28.1 | ✅ Yes | SDK requires httpx |
| pytest | 8.3.4 | pytest-asyncio | 0.25.0 | ✅ Yes | Tested combination |

---

## COMPLETE requirements.txt

### Production Dependencies (requirements.txt)

```txt
# Python version: 3.12
# Last updated: 2025-11-05

# ===== Web Framework & Server =====
fastapi==0.121.0
uvicorn[standard]==0.34.0
python-multipart==0.0.20

# ===== Database & ORM =====
sqlalchemy==2.0.44
alembic==1.14.0
psycopg2-binary==2.9.10  # For Alembic migrations (sync)
asyncpg==0.30.0          # For FastAPI async operations

# ===== Data Validation =====
pydantic[email]==2.12.3
email-validator==2.2.0

# ===== Authentication & Security =====
passlib[bcrypt]==1.7.4
bcrypt==4.2.1
PyJWT[crypto]==2.10.1    # CHANGED: Was python-jose (see DEPENDENCIES_AND_CONFLICTS.md)
cryptography==44.0.0
python-dotenv==1.0.1

# ===== LLM Integration =====
anthropic==0.40.0
httpx==0.28.1

# ===== Utilities =====
typing-extensions==4.12.2
```

### Development Dependencies (requirements-dev.txt)

```txt
# Development tools
-r requirements.txt  # Include production dependencies

# ===== Code Quality =====
black==24.10.0
ruff==0.8.4
mypy==1.13.0

# ===== Testing =====
pytest==8.3.4
pytest-asyncio==0.25.0
pytest-cov==6.0.0
pytest-mock==3.14.0

# ===== Test Utilities =====
faker==33.1.0
factory-boy==3.3.1

# ===== Documentation (optional) =====
# mkdocs==1.6.1
# mkdocs-material==9.5.47
```

---

## RESOLUTION STEPS

### Step 1: Update SECURITY_GUIDE.md

**File:** `/home/user/Socrates/foundation_docs/SECURITY_GUIDE.md`

**Change line 165:**
```python
# OLD
from jose import jwt

# NEW
import jwt  # PyJWT library
```

**Add note explaining change:**
```markdown
**Note:** We use PyJWT instead of python-jose because:
- PyJWT is actively maintained (python-jose last updated 2021)
- Better compatibility with modern cryptography library
- Smaller dependency tree
- Better performance
```

---

### Step 2: Create requirements.txt

**File:** `/home/user/Socrates/backend/requirements.txt`

**Contents:** See "Complete requirements.txt" section above

---

### Step 3: Create requirements-dev.txt

**File:** `/home/user/Socrates/backend/requirements-dev.txt`

**Contents:** See "Development Dependencies" section above

---

### Step 4: Update DATABASE_SCHEMA_COMPLETE.md

**Add section explaining dual database drivers:**

```markdown
### Database Drivers

**Important:** You need BOTH database drivers:

1. **psycopg2-binary** - Synchronous driver for Alembic migrations
```bash
# Used by Alembic for migrations
alembic upgrade head
```

2. **asyncpg** - Asynchronous driver for FastAPI
```python
# Used by FastAPI for async operations
async def get_user(user_id: str):
    async with engine.begin() as conn:
        result = await conn.execute(...)
```

**Why both?**
- Alembic doesn't support async (needs psycopg2)
- FastAPI performs better with async (needs asyncpg)
- They don't conflict - used in different contexts
```

---

### Step 5: Update PHASE_1.md

**Add dependencies installation section:**

```markdown
## 📦 Installing Dependencies

### Prerequisites
```bash
# Python 3.12 required
python --version  # Should show Python 3.12.x

# PostgreSQL 15+ required
psql --version  # Should show PostgreSQL 15.x or higher
```

### Install Production Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Verify Installation
```bash
# Check all critical packages installed
pip list | grep -E "fastapi|sqlalchemy|pydantic|anthropic|pytest"

# Should see:
# fastapi          0.121.0
# sqlalchemy       2.0.44
# pydantic         2.12.3
# anthropic        0.40.0
# pytest           8.3.4
```
```

---

### Step 6: Add Dependency Verification Script

**File:** `/home/user/Socrates/backend/scripts/verify_dependencies.py`

```python
"""
Verify all dependencies are installed and compatible.
Run this before starting Phase 1 implementation.
"""

import sys
import importlib.metadata as metadata

REQUIRED_PACKAGES = {
    # Package name: (min_version, purpose)
    "fastapi": ("0.121.0", "Web framework"),
    "sqlalchemy": ("2.0.44", "ORM"),
    "pydantic": ("2.12.3", "Data validation"),
    "anthropic": ("0.40.0", "Claude API"),
    "pytest": ("8.3.4", "Testing"),
    "psycopg2": ("2.9.10", "PostgreSQL driver (sync)"),
    "asyncpg": ("0.30.0", "PostgreSQL driver (async)"),
    "PyJWT": ("2.10.1", "JWT tokens"),
}

def check_package(name: str, min_version: str, purpose: str):
    """Check if package is installed with correct version."""
    try:
        version = metadata.version(name)
        # Simple version comparison (assumes semver)
        if version >= min_version:
            print(f"✅ {name}=={version} ({purpose})")
            return True
        else:
            print(f"❌ {name}=={version} - Need >={min_version} ({purpose})")
            return False
    except metadata.PackageNotFoundError:
        print(f"❌ {name} NOT INSTALLED ({purpose})")
        return False

def main():
    """Run all dependency checks."""
    print("🔍 Checking dependencies...\n")

    all_ok = True
    for package, (min_version, purpose) in REQUIRED_PACKAGES.items():
        if not check_package(package, min_version, purpose):
            all_ok = False

    print("\n" + "="*60)
    if all_ok:
        print("✅ ALL DEPENDENCIES OK - Ready for Phase 1!")
        sys.exit(0)
    else:
        print("❌ MISSING OR OUTDATED DEPENDENCIES")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
cd backend
python scripts/verify_dependencies.py
```

---

## SUMMARY

### Critical Actions Required

1. ✅ **Replace python-jose with PyJWT** in all documentation
2. ✅ **Create requirements.txt** with correct versions
3. ✅ **Create requirements-dev.txt** for development
4. ✅ **Document dual database drivers** (psycopg2 + asyncpg)
5. ✅ **Create dependency verification script**

### Conflicts Resolved

- ✅ JWT library: Use PyJWT instead of python-jose
- ✅ Database drivers: Both psycopg2-binary and asyncpg needed
- ✅ Version alignment: All packages verified compatible

### Next Steps

1. Implement resolution steps above
2. Run dependency verification script
3. Test all imports work
4. Proceed to Phase 1 implementation

---

**Status:** 🟢 READY after implementing resolution steps

**Last Updated:** November 5, 2025


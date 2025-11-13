# Socrates Operational Fix Plan

**Date:** November 13, 2025
**Status:** Planning Phase
**Goal:** Make Socrates fully operational and tested

---

## CRITICAL ISSUES TO FIX

### Issue #1: CIRCULAR IMPORT (BLOCKING)
- **Location:** socrates/__init__.py (line 150) ↔ app/agents/conflict_detector.py (line 20)
- **Problem:** Agents import from socrates, socrates exports agents → circular dependency
- **Impact:** All agent tests fail immediately with ImportError
- **Solution:** Move agent imports in socrates/__init__.py to lazy loading

### Issue #2: INCOMPLETE REQUIREMENTS
- **Problem:** requirements-dev.txt has only 1 line (pytest setup reference)
- **Missing:** All dev dependencies like black, ruff, mypy, faker, factory-boy, pytest-asyncio, pytest-cov, etc.
- **Impact:** Cannot run dev tools, cannot run tests properly
- **Solution:** Populate requirements-dev.txt with full dev dependencies from pyproject.toml

### Issue #3: DATABASE VERIFICATION MISSING
- **Problem:** No confirmation PostgreSQL is running or databases exist
- **Missing:** Migration status check, schema verification
- **Impact:** API will fail with database connection errors
- **Solution:** Create and run database setup verification script

### Issue #4: NO CLI INTEGRATION TEST
- **Problem:** Socrates.py (3058 lines) not tested
- **Missing:** Test verifying CLI connects to API
- **Impact:** Don't know if main entry point works
- **Solution:** Create test_socrates_cli.py with basic connectivity test

---

## FIX EXECUTION ORDER

### STEP 1: Fix Circular Import (15 min)
```python
# In socrates/__init__.py, move agents imports to lazy loading
# Instead of importing at module level, use function to import on first access
```

**Files to modify:**
- backend/socrates/__init__.py

**Expected result:**
- Can import from socrates without circular import error
- Tests for pure logic (Phase 1a) should pass
- Agent tests may still fail until test is run after import fix

### STEP 2: Fix requirements-dev.txt (10 min)
```
# Current: Just references pytest config
# Target: All dev dependencies from pyproject.toml
```

**Files to modify:**
- backend/requirements-dev.txt

**Expected result:**
- `pip install -e ".[dev]"` works
- Can run black, ruff, mypy, pytest, etc.

### STEP 3: Verify/Setup Database (30 min)
```bash
# Check PostgreSQL
# Create databases if needed  
# Run migrations
# Verify tables
```

**Files to modify/create:**
- Create backend/scripts/verify_database_setup.py
- Check alembic/versions/

**Expected result:**
- PostgreSQL confirmed running
- socrates_auth and socrates_specs databases exist
- All tables created and accessible

### STEP 4: Test API Startup (10 min)
```bash
# Run: uvicorn app.main:app --reload
# Verify: API starts without errors
# Check: http://localhost:8000/docs loads
```

**Expected result:**
- FastAPI server starts
- Swagger docs available
- No database connection errors
- No import errors

### STEP 5: Test Socrates.py CLI (15 min)
```bash
# Verify CLI can connect to running API
# Test basic commands
```

**Files to create:**
- backend/tests/test_socrates_cli_integration.py

**Expected result:**
- CLI connects to API successfully
- Can call API endpoints from CLI
- No errors in integration

### STEP 6: Test Admin CLI (10 min)
```bash
# Test: python -m app.cli domains list
# Test: python -m app.cli workflows create test
```

**Expected result:**
- Admin CLI works with database
- Can list domains
- Can create workflows

### STEP 7: Run Full Test Suite (20 min)
```bash
# Run: pytest tests/ -v
# Should see significant improvement
# Fix remaining failures
```

**Expected result:**
- Circular import fixed → agent tests pass
- Database setup → DB tests pass
- CLI tests pass
- Endpoint tests pass

### STEP 8: Interconnection Testing (30 min)
```
Verify these flows work end-to-end:
1. Socrates.py → API → Database → Response
2. CLI admin commands → Database → Results
3. All 25+ routers responding
4. All endpoints accessible
```

**Files to create:**
- backend/tests/test_interconnections_full.py

**Expected result:**
- Full system works together
- No missing connections
- All endpoints functional

---

## VERIFICATION CHECKLIST

### After Each Step - Verify
- ✓ No import errors
- ✓ Tests can run (even if they fail)
- ✓ No circular dependencies

### Before Declaring "Operational"
- ✓ PostgreSQL running
- ✓ Databases created  
- ✓ Migrations applied
- ✓ API starts without errors
- ✓ Socrates.py CLI works
- ✓ Admin CLI works
- ✓ All tests pass OR known skipped with reason
- ✓ All endpoints accessible
- ✓ All interconnections tested

---

## TIME ESTIMATE

- **Step 1 (Fix Circular Import):** 15 min
- **Step 2 (Fix requirements):** 10 min
- **Step 3 (Database Setup):** 30 min
- **Step 4 (API Test):** 10 min
- **Step 5 (CLI Test):** 15 min
- **Step 6 (Admin CLI):** 10 min
- **Step 7 (Test Suite):** 20 min
- **Step 8 (Interconnection):** 30 min

**Total Estimated Time:** ~2.5 hours

---

## SUCCESS CRITERIA

✅ Socrates is "OPERATIONAL" when:

1. **No Critical Errors**
   - No circular imports
   - No missing dependencies
   - No database connection errors

2. **All Components Working**
   - Backend API running
   - Socrates.py CLI running
   - Admin CLI running
   - Database accessible

3. **Tests Passing**
   - All unit tests pass
   - All integration tests pass
   - No unexplained test failures

4. **Manual Verification**
   - User can follow README to start system
   - All endpoints respond correctly
   - All CLI commands work
   - Database operations succeed

5. **Documentation Complete**
   - How to run Socrates locally
   - How to use Socrates.py CLI
   - How to use admin CLI
   - What endpoints exist
   - How interconnections work

---

## NEXT: START STEP 1

Ready to fix the circular import!


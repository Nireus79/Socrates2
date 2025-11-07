# Socrates CLI Testing Guide

## Overview

Comprehensive testing suite for the Socrates CLI, including unit tests and integration tests.

## Test Files

| File | Type | Description | Requires Backend |
|------|------|-------------|------------------|
| `test_cli.py` | Unit Tests | Mocked API tests | ❌ No |
| `test_cli_integration.py` | Integration Tests | Real API tests | ✅ Yes |
| `run_cli_tests.sh` | Test Runner | Runs all tests | Optional |

## Quick Start

### Run All Tests (Recommended)

```bash
# Linux/Mac
./run_cli_tests.sh

# Windows (PowerShell)
python test_cli.py
python test_cli_integration.py
```

### Run Unit Tests Only

```bash
python test_cli.py
```

**No backend required!** Uses mocked API responses.

### Run Integration Tests Only

```bash
# Start backend first
cd backend
uvicorn app.main:app --reload

# In another terminal
python test_cli_integration.py
```

## Test Structure

### Unit Tests (`test_cli.py`)

Tests CLI functionality with mocked API responses. No network calls.

**Test Classes:**
1. **TestSocratesConfig** (5 tests)
   - Config file creation
   - Set/get config values
   - Config persistence
   - Clear config
   - Default values

2. **TestSocratesAPI** (7 tests)
   - API initialization
   - Token management
   - Request headers
   - Registration
   - Login
   - Project creation
   - Connection error handling

3. **TestSocratesCLI** (12 tests)
   - CLI initialization
   - Authentication checks
   - Project selection checks
   - Registration command
   - Login command
   - Mode toggling
   - Command parsing
   - Help system
   - Whoami command

4. **TestCLIWorkflow** (2 tests)
   - Complete registration → login → project workflow
   - Complete session workflow

**Total:** 26 unit tests

### Integration Tests (`test_cli_integration.py`)

Tests CLI with real backend API. Requires running backend.

**Tests (15 total):**
1. User Registration
2. Duplicate Registration (should fail)
3. User Login
4. Invalid Login (should fail)
5. Create Project
6. List Projects
7. Get Project Details
8. Start Socratic Session
9. Get Next Question
10. Submit Answer
11. List Sessions
12. Get Session History
13. End Session
14. Delete Project (cleanup)
15. Logout

## Bug Fixes Applied

### Fix 1: Registration Response Handling

**Problem:** CLI checked for `success` field, but backend returns `user_id`, `email`, `message`.

**Before:**
```python
if result.get("success"):  # Never true!
    print("Success")
else:
    print(f"Failed: {result.get('message')}")
```

**After:**
```python
if result.get("user_id"):  # Check for user_id instead
    print("Success")
else:
    print(f"Failed: {result.get('message')}")
```

### Fix 2: Registration Request Format

**Problem:** CLI sent `full_name`, but backend only accepts `email` and `password`.

**Before:**
```python
def register(email, password, full_name):
    api.post("/register", {
        "email": email,
        "password": password,
        "full_name": full_name  # Not expected by API
    })
```

**After:**
```python
def register(email, password):
    api.post("/register", {
        "email": email,
        "password": password
    })
```

### Fix 3: Login Request Format

**Problem:** CLI sent JSON, but backend expects `application/x-www-form-urlencoded` (OAuth2 format).

**Before:**
```python
def login(email, password):
    api.post("/login", json={
        "email": email,      # Should be "username"
        "password": password
    })
```

**After:**
```python
def login(email, password):
    api.post("/login", data={
        "username": email,   # OAuth2 uses "username"
        "password": password
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
```

## Running Tests

### Prerequisites

```bash
# Install CLI dependencies
pip install -r cli-requirements.txt

# For integration tests, install backend dependencies
cd backend
pip install -r requirements.txt
```

### Unit Test Execution

```bash
python test_cli.py
```

**Expected Output:**
```
test_clear_config (__main__.TestSocratesConfig) ... ok
test_config_directory_created (__main__.TestSocratesConfig) ... ok
test_config_persistence (__main__.TestSocratesConfig) ... ok
test_get_default_value (__main__.TestSocratesConfig) ... ok
test_set_and_get_config (__main__.TestSocratesConfig) ... ok
...

----------------------------------------------------------------------
Ran 26 tests in 0.123s

OK
```

### Integration Test Execution

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload

# 2. In another terminal
python test_cli_integration.py
```

**Expected Output:**
```
═══════════════════════════════════════════════════
   Socrates CLI Integration Tests
═══════════════════════════════════════════════════

Checking backend connection...
✓ Backend is running at http://localhost:8000

Test 1: User Registration
  ✓ Response contains user_id
  ✓ Response contains email
  ✓ Email matches
  ✓ Response contains message
  → Created user: test_a1b2c3d4...

Test 2: Duplicate Registration
  ✓ Correctly rejected duplicate: Email already registered...

Test 3: User Login
  ✓ Response contains access_token
  ✓ Response contains user_id
  ✓ Response contains email
  ✓ Token type is bearer
  → Token: eyJhbGciOiJIUzI1NiIs...

[... more tests ...]

═══════════════════════════════════════════════════
Test Summary
═══════════════════════════════════════════════════
Passed: 45
Failed: 0
Success Rate: 100.0%
```

## Test Runner Script

The `run_cli_tests.sh` script runs all tests automatically:

```bash
./run_cli_tests.sh
```

**Features:**
- Checks dependencies
- Runs unit tests
- Checks backend connection
- Runs integration tests (if backend available)
- Provides summary

**Example Output:**
```
═══════════════════════════════════════════════════
   Socrates CLI Test Suite
═══════════════════════════════════════════════════

Checking dependencies...
✓ Dependencies installed

═══════════════════════════════════════════════════
Running Unit Tests (no backend required)
═══════════════════════════════════════════════════

[Unit test output]

✓ Unit tests passed

═══════════════════════════════════════════════════
Checking backend connection...
═══════════════════════════════════════════════════

Testing connection to: http://localhost:8000
✓ Backend is running

═══════════════════════════════════════════════════
Running Integration Tests (requires backend)
═══════════════════════════════════════════════════

[Integration test output]

✓ Integration tests passed

═══════════════════════════════════════════════════
   Test Results Summary
═══════════════════════════════════════════════════
✓ Unit Tests: PASSED
✓ Integration Tests: PASSED
═══════════════════════════════════════════════════
```

## Writing New Tests

### Adding Unit Tests

```python
# In test_cli.py

class TestNewFeature(unittest.TestCase):
    """Test new feature"""

    def setUp(self):
        """Setup for each test"""
        self.cli = SocratesCLI("http://test.example.com")
        self.cli.console = Mock()
        self.cli.api = Mock()

    def test_new_feature(self):
        """Test description"""
        # Arrange
        self.cli.api.some_method.return_value = {"success": True}

        # Act
        result = self.cli.some_command()

        # Assert
        self.assertTrue(result)
```

### Adding Integration Tests

```python
# In test_cli_integration.py

class CLIIntegrationTest:
    def test_16_new_feature(self):
        """Test 16: New Feature"""
        self.log("\n[bold]Test 16: New Feature[/bold]")

        try:
            result = self.api.new_endpoint()

            self.assert_in("expected_field", result, "Has expected field")
            self.assert_true(result["success"], "Success is true")

        except Exception as e:
            self.log(f"  ✗ New feature failed: {e}", "error")
            self.failed += 1
            raise
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: CLI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r cli-requirements.txt
          pip install -r backend/requirements.txt

      - name: Run unit tests
        run: python test_cli.py

      - name: Setup database
        run: |
          # Setup PostgreSQL databases
          psql -U postgres -c "CREATE DATABASE socrates_auth;"
          psql -U postgres -c "CREATE DATABASE socrates_specs;"

      - name: Run migrations
        run: |
          cd backend
          alembic upgrade head

      - name: Start backend
        run: |
          cd backend
          uvicorn app.main:app &
          sleep 5

      - name: Run integration tests
        run: python test_cli_integration.py
```

## Troubleshooting

### Unit Tests Fail

**Issue:** `ModuleNotFoundError: No module named 'Socrates'`

**Fix:**
```bash
# Make sure Socrates.py is in the same directory
ls Socrates.py test_cli.py
```

### Integration Tests Can't Connect

**Issue:** `✗ Backend not running at http://localhost:8000`

**Fix:**
```bash
# Start backend in separate terminal
cd backend
uvicorn app.main:app --reload

# Check it's running
curl http://localhost:8000/docs
```

### Database Errors in Integration Tests

**Issue:** `psycopg2.OperationalError: connection refused`

**Fix:**
```bash
# Make sure PostgreSQL is running
# And databases are created
psql -U postgres -c "CREATE DATABASE socrates_auth;"
psql -U postgres -c "CREATE DATABASE socrates_specs;"

# Run migrations
cd backend
alembic upgrade head
```

### Tests Pass Locally But Fail in CI

**Common Issues:**
1. Environment variables not set
2. Database not initialized
3. Ports already in use
4. Dependencies not installed

**Debug:**
```bash
# Add verbose output
python test_cli.py -v

# Check backend logs
cd backend
uvicorn app.main:app --log-level debug
```

## Test Coverage

To measure test coverage:

```bash
# Install coverage tool
pip install coverage

# Run with coverage
coverage run test_cli.py
coverage run -a test_cli_integration.py

# Generate report
coverage report
coverage html  # Creates htmlcov/index.html
```

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 41 (26 unit + 15 integration) |
| **Coverage** | Config, API, CLI, Workflows |
| **Runtime** | ~0.1s (unit) + ~30s (integration) |
| **Backend Required** | Only for integration tests |
| **Bugs Fixed** | 3 critical bugs |

## Next Steps

1. ✅ Run unit tests: `python test_cli.py`
2. ✅ Fix any failures
3. ✅ Start backend
4. ✅ Run integration tests: `python test_cli_integration.py`
5. ✅ Review results
6. ✅ Add to CI/CD pipeline

---

**All tests passing = CLI is ready for production! 🚀**

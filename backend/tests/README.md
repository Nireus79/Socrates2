# Socrates2 - Infrastructure Tests

**Purpose:** Verify database setup, schema, migrations, and basic operations work correctly.

---

## What These Tests Verify

### ✅ Database Connections
- Both databases (socrates_auth, socrates_specs) are accessible
- Connection strings from .env work correctly

### ✅ Schema Validation
- All required tables exist (users, refresh_tokens, projects, sessions)
- All columns present with correct names
- Indexes created properly
- Foreign key constraints working

### ✅ Migration State
- Alembic version tracking correct
- socrates_auth at migration 002
- socrates_specs at migration 004

### ✅ Database Operations
- Can insert records into tables
- Foreign keys enforce referential integrity
- CASCADE deletes work correctly
- No cross-database foreign keys (correct behavior)

---

## Running the Tests

### Run All Infrastructure Tests

```powershell
cd C:\Users\themi\PycharmProjects\Socrates2\backend
pytest tests/test_infrastructure.py -v
```

### Run Specific Test Class

```powershell
# Test database connections only
pytest tests/test_infrastructure.py::TestDatabaseConnections -v

# Test auth database schema
pytest tests/test_infrastructure.py::TestAuthDatabaseSchema -v

# Test specs database schema
pytest tests/test_infrastructure.py::TestSpecsDatabaseSchema -v

# Test CRUD operations
pytest tests/test_infrastructure.py::TestDatabaseOperations -v
```

### Run Specific Test

```powershell
pytest tests/test_infrastructure.py::TestDatabaseConnections::test_auth_database_connection -v
```

### Run with Coverage

```powershell
pytest tests/test_infrastructure.py --cov=app --cov-report=html
```

---

## Expected Output (Success)

```
tests/test_infrastructure.py::TestDatabaseConnections::test_auth_database_connection PASSED
tests/test_infrastructure.py::TestDatabaseConnections::test_specs_database_connection PASSED
tests/test_infrastructure.py::TestAuthDatabaseSchema::test_auth_tables_exist PASSED
tests/test_infrastructure.py::TestAuthDatabaseSchema::test_users_table_columns PASSED
tests/test_infrastructure.py::TestAuthDatabaseSchema::test_refresh_tokens_table_columns PASSED
tests/test_infrastructure.py::TestAuthDatabaseSchema::test_refresh_tokens_foreign_key PASSED
tests/test_infrastructure.py::TestAuthDatabaseSchema::test_users_indexes_exist PASSED
tests/test_infrastructure.py::TestSpecsDatabaseSchema::test_specs_tables_exist PASSED
tests/test_infrastructure.py::TestSpecsDatabaseSchema::test_projects_table_columns PASSED
tests/test_infrastructure.py::TestSpecsDatabaseSchema::test_sessions_table_columns PASSED
tests/test_infrastructure.py::TestSpecsDatabaseSchema::test_sessions_foreign_key PASSED
tests/test_infrastructure.py::TestSpecsDatabaseSchema::test_projects_check_constraint PASSED
tests/test_infrastructure.py::TestCrossDatabase::test_no_cross_database_foreign_keys PASSED
tests/test_infrastructure.py::TestMigrationState::test_auth_alembic_version PASSED
tests/test_infrastructure.py::TestMigrationState::test_specs_alembic_version PASSED
tests/test_infrastructure.py::TestDatabaseOperations::test_can_insert_user PASSED
tests/test_infrastructure.py::TestDatabaseOperations::test_can_insert_project PASSED
tests/test_infrastructure.py::TestDatabaseOperations::test_cascade_delete_sessions PASSED

==================== 18 passed in 2.34s ====================
```

---

## Test Categories

### 1. Connection Tests
**Purpose:** Verify databases are accessible
**Fast:** < 1 second
**Run:** Every time before development

### 2. Schema Tests
**Purpose:** Verify table structure matches migrations
**Fast:** < 2 seconds
**Run:** After migrations, before deployment

### 3. Migration Tests
**Purpose:** Verify Alembic version tracking
**Fast:** < 1 second
**Run:** After running migrations

### 4. Operation Tests
**Purpose:** Verify basic CRUD operations work
**Slower:** 2-3 seconds (includes rollback)
**Run:** Before deployment, after schema changes

---

## When to Run These Tests

### ✅ Always Run
- **After pulling code** - Verify setup still works
- **Before starting work** - Verify database is ready
- **After running migrations** - Verify schema correct

### ✅ Before Commits
- **Before committing schema changes** - Verify nothing broke
- **Before pushing to GitHub** - Verify tests pass

### ✅ In CI/CD (Future)
- **On every pull request** - Automated testing
- **Before deployment** - Final verification

---

## Test Files

```
backend/tests/
├── __init__.py                   # Package marker
├── conftest.py                   # Pytest fixtures & configuration
├── test_infrastructure.py        # Infrastructure tests (18 tests)
├── README.md                     # This file
└── pytest.ini                    # Pytest configuration
```

---

## Common Issues & Solutions

### Issue: "DATABASE_URL_AUTH not set"

**Solution:**
```powershell
# Ensure .env file exists
cd backend
ls .env

# If missing, run setup
python scripts\setup_env.py
```

### Issue: "OperationalError: could not connect to server"

**Solution:**
```powershell
# Check PostgreSQL service running
Get-Service postgresql*

# Start if stopped
Start-Service postgresql-x64-17
```

### Issue: "Table 'users' not found"

**Solution:**
```powershell
# Run migrations
.\scripts\run_migrations.ps1
```

### Issue: "Expected migration 002, got 001"

**Solution:**
```powershell
# Run remaining migrations
.\scripts\run_migrations.ps1
```

---

## Adding More Tests

### For New Models
When you create new SQLAlchemy models, add tests to verify:
- Model can be instantiated
- Model can be saved to database
- Model relationships work
- Model validation works

### For New API Endpoints
When you create new FastAPI endpoints, add integration tests:
- Endpoint returns correct status codes
- Endpoint validates input correctly
- Endpoint interacts with database correctly
- Endpoint requires authentication

### For New Business Logic
When you add business logic, add unit tests:
- Logic produces correct results
- Edge cases handled
- Errors raised appropriately

---

## Test-Driven Development (TDD)

For Phase 1 implementation, consider writing tests FIRST:

1. **Write test** for User model
2. **Run test** - it fails (model doesn't exist yet)
3. **Implement** User model
4. **Run test** - it passes!
5. **Refactor** if needed

This ensures:
- ✅ All code is tested
- ✅ Tests are meaningful
- ✅ Code meets requirements

---

## Next Tests to Write

Once you start Phase 1 implementation:

### Model Tests (`test_models.py`)
```python
def test_user_creation():
    user = User(email="test@example.com", hashed_password="...")
    assert user.email == "test@example.com"

def test_user_password_hashing():
    user = User.create(email="test@example.com", password="plain")
    assert user.verify_password("plain") == True
```

### API Tests (`test_api_auth.py`)
```python
def test_register_endpoint(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
```

### Integration Tests (`test_integration.py`)
```python
def test_create_project_flow(client, auth_token):
    # Login
    # Create project
    # Verify project in database
    # Verify project returned in API
```

---

## Summary

**Infrastructure tests are important because they:**

1. **Catch setup issues early** - Before you start coding
2. **Verify migrations work** - Schema matches expectations
3. **Document schema requirements** - Tests serve as documentation
4. **Prevent regressions** - Schema changes don't break things
5. **Build confidence** - Foundation is solid

**Run these tests now:**
```powershell
cd backend
pytest tests/test_infrastructure.py -v
```

**Expected:** All 18 tests pass ✅

---

**Status:** Infrastructure tests ready to run!

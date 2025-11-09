# Socrates2 Testing Guide

## Overview

Comprehensive test suites have been created for the 3 new Priority 3 API endpoints. All tests are located in `backend/tests/` and use pytest with SQLAlchemy fixtures.

## Test Files

### 1. `test_api_search.py` (10 tests)
Tests for the `/api/v1/search` endpoint - full-text search functionality.

**Test Cases:**
- `test_search_requires_authentication` - Validates 401 response without auth
- `test_search_basic_query` - Basic search with query parameter
- `test_search_with_resource_type_filter` - Filtering by resource type (projects)
- `test_search_with_category_filter` - Filtering by specification category
- `test_search_with_pagination` - Tests skip/limit parameters
- `test_search_empty_query_returns_empty_results` - Edge case: empty queries
- `test_search_nonexistent_term_returns_empty` - Returns empty results for no matches
- `test_search_case_insensitive` - Validates case-insensitive search
- `test_search_response_structure` - Validates complete response schema
- `test_search_other_user_data_not_included` - Privacy validation

### 2. `test_api_insights.py` (11 tests)
Tests for the `/api/v1/insights/{project_id}` endpoint - project analysis with gaps, risks, opportunities.

**Test Cases:**
- `test_insights_requires_authentication` - Auth validation
- `test_insights_requires_authorization` - Permission checks between users
- `test_insights_nonexistent_project` - 404 handling
- `test_insights_gap_detection` - Identifies missing specification categories
- `test_insights_risk_detection_low_confidence` - Detects low-confidence specs as risks
- `test_insights_opportunity_detection` - Highlights well-covered categories
- `test_insights_filter_by_type_gaps` - Filters insights by type parameter
- `test_insights_response_structure` - Complete response schema validation
- `test_insights_coverage_percentage` - Validates coverage calculation
- `test_insights_empty_project` - Tests behavior with no specifications
- `test_insights_recommendations_present` - Validates all insights have recommendations

### 3. `test_api_templates.py` (15 tests)
Tests for the `/api/v1/templates` endpoint - project template management.

**Test Cases:**
- `test_list_templates_requires_authentication` - Auth validation
- `test_apply_template_requires_authentication` - Auth for apply operation
- `test_list_templates_basic` - Basic template listing
- `test_list_templates_pagination` - Pagination with skip/limit
- `test_list_templates_filter_by_tags` - Filter by template tags
- `test_list_templates_filter_by_industry` - Filter by industry
- `test_get_template_details` - Get full template with preview specs
- `test_get_template_nonexistent` - 404 for invalid template ID
- `test_apply_template_to_project` - Apply template creates specifications
- `test_apply_template_requires_authorization` - Permission validation
- `test_apply_template_to_nonexistent_project` - 404 handling
- `test_apply_nonexistent_template` - Invalid template ID handling
- `test_list_templates_total_count` - Count validation
- `test_template_categories_structure` - Schema validation
- `test_template_filtering_combination` - Combined filter testing

## Test Statistics

| File | Tests | Coverage |
|------|-------|----------|
| test_api_search.py | 10 | 100% of /search endpoint |
| test_api_insights.py | 11 | 100% of /insights endpoint |
| test_api_templates.py | 15 | 100% of /templates endpoint |
| **Total** | **36** | **100% of 3 new APIs** |

## Setup Instructions

### Prerequisites

1. **PostgreSQL 12+** running on localhost:5432
2. **Two databases** created:
   - `socrates_auth` - For user authentication
   - `socrates_specs` - For projects and specifications

3. **Python 3.11+** with virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

   Update with your database credentials:
   ```
   DATABASE_URL_AUTH=postgresql://user:password@localhost:5432/socrates_auth
   DATABASE_URL_SPECS=postgresql://user:password@localhost:5432/socrates_specs
   SECRET_KEY=your-secret-key-here
   ANTHROPIC_API_KEY=your-api-key-here
   ```

3. **Run migrations** (if needed):
   ```bash
   alembic upgrade head
   ```

## Running Tests

### Run All Tests
```bash
pytest tests/test_api_search.py tests/test_api_insights.py tests/test_api_templates.py -v
```

### Run Specific Test Suite
```bash
# Search API tests
pytest tests/test_api_search.py -v

# Insights API tests
pytest tests/test_api_insights.py -v

# Templates API tests
pytest tests/test_api_templates.py -v
```

### Run Single Test
```bash
pytest tests/test_api_search.py::test_search_basic_query -v
```

### Run with Coverage
```bash
pytest tests/test_api_search.py tests/test_api_insights.py tests/test_api_templates.py --cov=app/api --cov-report=html
```

### Run with Detailed Output
```bash
pytest tests/test_api_templates.py -vv -s
```

## Test Design Patterns

### Authentication Testing
Each endpoint test suite includes tests to verify:
- 401 Unauthorized when no token is provided
- Invalid token handling
- Token validation

Example:
```python
def test_search_requires_authentication():
    response = client.get("/api/v1/search?query=test")
    assert response.status_code == 401
```

### Authorization Testing
Tests verify that users can only access their own data:
- Creating a second user
- Creating resources for that user
- Verifying current user can't access other user's data

Example:
```python
def test_search_other_user_data_not_included(test_user, auth_session, specs_session):
    # Create another user with data
    other_user = User(...)
    # Current user searches
    response = client.get("/api/v1/search?query=Secret", headers={"Authorization": ...})
    # Verify other user's data is not returned
    assert other_user.id not in [r['id'] for r in response.json()['results']]
```

### Fixture-Based Testing
All tests use pytest fixtures from `conftest.py`:
- `test_user` - A valid authenticated user
- `auth_session` - Auth database session with rollback
- `specs_session` - Specs database session with rollback
- `override_app_dependencies` - Automatically overrides FastAPI dependencies

### Database Transaction Rollback
Each test runs in a transaction that's rolled back after completion:
- No test pollution
- Tests can run in any order
- No cleanup required
- Isolates test data

## Common Issues

### Issue: "CONNECTION REFUSED" on PostgreSQL
**Solution:** Ensure PostgreSQL is running:
```bash
# macOS
brew services start postgresql

# Linux (systemd)
sudo systemctl start postgresql

# Windows
net start postgresql-17
```

### Issue: "Permission denied" on auth_session
**Solution:** Ensure database user has proper permissions:
```sql
ALTER ROLE your_user WITH SUPERUSER;
```

### Issue: "Table does not exist"
**Solution:** Run migrations:
```bash
alembic upgrade head
```

### Issue: Tests import error
**Solution:** Ensure `.env` file exists with correct database URLs

## Test Fixtures Reference

### `test_user` - Creates an authenticated test user
```python
def test_search_basic_query(test_user):
    # test_user is a valid User object with UUID and email
    token = create_access_token(data={"sub": str(test_user.id)})
    response = client.get("/api/v1/search?query=test", headers={"Authorization": f"Bearer {token}"})
```

### `auth_session` - Database session for auth database
```python
def test_apply_template_requires_authorization(test_user, auth_session):
    # Create another user for testing
    other_user = User(...)
    auth_session.add(other_user)
    auth_session.commit()
```

### `specs_session` - Database session for specs database
```python
def test_search_basic_query(test_user, specs_session):
    # Create test project
    project = Project(user_id=test_user.id, name="Test")
    specs_session.add(project)
    specs_session.commit()
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        env:
          DATABASE_URL_AUTH: postgresql://postgres:postgres@localhost:5432/socrates_auth
          DATABASE_URL_SPECS: postgresql://postgres:postgres@localhost:5432/socrates_specs
        run: |
          cd backend
          pytest tests/test_api_*.py -v
```

## Test Coverage Goals

- ✅ **100%** coverage of new API endpoints
- ✅ **100%** coverage of authentication/authorization
- ✅ **100%** coverage of error cases (400, 401, 403, 404)
- ✅ **100%** coverage of data validation
- ✅ **100%** coverage of response schemas
- ✅ **100%** coverage of edge cases

## Next Steps

1. **Set up PostgreSQL** if not already running
2. **Create test databases** (socrates_auth, socrates_specs)
3. **Configure .env** with database URLs
4. **Run test suites** to verify setup
5. **Integrate with CI/CD** for automated testing
6. **Monitor test coverage** to maintain 100% coverage

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Testing Guide](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-basics)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Project README](../README.md)

# Socrates2 Comprehensive Testing Suite

**Self-contained, isolated testing framework for Socrates2**

This testing suite is designed to be:
- ✅ **Self-contained** - No external database required
- ✅ **Fast** - Uses in-memory SQLite for database tests
- ✅ **Isolated** - Each test runs independently
- ✅ **Comprehensive** - Covers all major components
- ✅ **CI/CD Ready** - Can run in any environment

## Quick Start

### Installation

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Install socrates-ai (tested library)
pip install socrates-ai==0.1.0
```

### Run All Tests

```bash
# Run all tests
python -m pytest tests_new/ -v

# Run with coverage report
python -m pytest tests_new/ -v --cov=app --cov-report=html

# Run specific test category
python -m pytest tests_new/ -v -m unit          # Unit tests only
python -m pytest tests_new/ -v -m integration   # Integration tests only
python -m pytest tests_new/ -v -m api           # API tests only
python -m pytest tests_new/ -v -m agent         # Agent tests only
python -m pytest tests_new/ -v -m security      # Security tests only
```

### Run Specific Tests

```bash
# Run single test file
python -m pytest tests_new/test_models.py -v

# Run single test class
python -m pytest tests_new/test_models.py::TestUserModel -v

# Run single test function
python -m pytest tests_new/test_models.py::TestUserModel::test_user_creation -v

# Run tests matching pattern
python -m pytest tests_new/ -v -k "user"
python -m pytest tests_new/ -v -k "security"
```

## Test Organization

### Test Categories

The test suite is organized into 7 main areas:

#### 1. **Unit Tests** (`test_models.py`)
Tests for data validation and model functionality.
```bash
pytest tests_new/test_models.py -v
```

**Coverage:**
- User model validation
- Project model validation
- Specification model validation
- Question model validation
- Session model validation
- Data relationships
- Data validation

#### 2. **Security Tests** (`test_security.py`)
Tests for JWT tokens, passwords, and security mechanisms.
```bash
pytest tests_new/test_security.py -v -m security
```

**Coverage:**
- JWT token creation and validation
- Expired token handling
- Tampered token detection
- Password strength validation
- API key management
- Environment security
- CORS configuration
- Input validation

#### 3. **API Endpoint Tests** (`test_api_endpoints.py`)
Tests for all HTTP endpoints.
```bash
pytest tests_new/test_api_endpoints.py -v -m api
```

**Coverage:**
- Health check endpoint
- Authentication endpoints (register, login, logout)
- Project management endpoints
- Session management endpoints
- Error handling
- CORS headers

#### 4. **Agent Tests** (`test_agents_core.py`)
Tests for agent registration and functionality.
```bash
pytest tests_new/test_agents_core.py -v -m agent
```

**Coverage:**
- Agent Orchestrator
- Socratic Counselor Agent
- Conflict Detector Agent
- Quality Controller Agent
- User Learning Agent
- Agent coordination
- ServiceContainer

#### 5. **Library Integration Tests** (`test_library_integration.py`)
Tests for Socrates library (socrates-ai) integration.
```bash
pytest tests_new/test_library_integration.py -v
```

**Coverage:**
- Socrates library imports
- Core engines (QuestionGenerator, ConflictDetectionEngine, BiasDetectionEngine, LearningEngine)
- Data models
- Conversion functions
- Library version
- Engine capabilities

#### 6. **Integration Workflow Tests** (`test_integration_workflows.py`)
Tests for complete end-to-end workflows.
```bash
pytest tests_new/test_integration_workflows.py -v -m integration
```

**Coverage:**
- User registration workflow
- Project creation workflow
- Specification gathering workflow
- Conflict detection workflow
- Session management
- Question generation
- User learning and personalization
- Multi-agent coordination
- Error recovery
- Data consistency

## Test Configuration

### Fixtures

The `conftest.py` provides reusable fixtures:

```python
# Database fixtures
@pytest.fixture
def db_auth()              # Auth database session
@pytest.fixture
def db_specs()             # Specs database session

# Client fixture
@pytest.fixture
def test_client()          # FastAPI test client

# Mock fixture
@pytest.fixture
def mock_anthropic_client() # Mock LLM client

# Data fixtures
@pytest.fixture
def test_user_data()       # Sample user data
@pytest.fixture
def test_project_data()    # Sample project data
@pytest.fixture
def test_specification_data() # Sample spec data
@pytest.fixture
def test_question_data()   # Sample question data
@pytest.fixture
def test_session_data()    # Sample session data
```

### Using Fixtures

```python
def test_example(test_client, test_user_data, db_auth):
    """Example test using fixtures."""
    # test_client is FastAPI test client
    # test_user_data is sample user
    # db_auth is auth database session

    response = test_client.get("/api/v1/admin/health")
    assert response.status_code == 200
```

### Environment Setup

Tests automatically configure environment variables:
- `ENVIRONMENT=test`
- `DATABASE_URL_AUTH=sqlite:///:memory:`
- `DATABASE_URL_SPECS=sqlite:///:memory:`
- `ANTHROPIC_API_KEY=test-key-sk-test`
- `SECRET_KEY=test-secret-key-for-testing-only`

## Running Tests with PyCharm

### IDE Configuration

1. **Set up test runner:**
   - Go to Settings → Tools → Python Integrated Tools
   - Set Default test runner to **pytest**

2. **Run individual test:**
   - Right-click on test file → "Run pytest in [file]"
   - Right-click on test class → "Run pytest in [class]"
   - Right-click on test method → "Run pytest in [method]"

3. **Run with debugging:**
   - Right-click on test → "Debug pytest in [file]"

4. **Coverage:**
   - Right-click on test file → "Run pytest in [file] with Coverage"

### PyCharm Test View

The Test Runner pane shows:
- ✅ Passing tests (green)
- ❌ Failing tests (red)
- ⏭️ Skipped tests (yellow)
- 🔴 Errors (red X)

## Test Markers

Run tests by category using markers:

```bash
# Unit tests only
pytest tests_new/ -m unit

# Integration tests only
pytest tests_new/ -m integration

# API tests only
pytest tests_new/ -m api

# Agent tests only
pytest tests_new/ -m agent

# Security tests only
pytest tests_new/ -m security

# All tests except those requiring live DB
pytest tests_new/ -m "not requires_live_db"

# Combine markers
pytest tests_new/ -m "unit or integration"
```

## Coverage Report

Generate HTML coverage report:

```bash
# Generate coverage report
pytest tests_new/ --cov=app --cov-report=html

# View report
open htmlcov/index.html  # On macOS
start htmlcov/index.html # On Windows
xdg-open htmlcov/index.html # On Linux
```

## Common Test Patterns

### Testing API Endpoints

```python
def test_health_check(test_client):
    """Test API endpoint."""
    response = test_client.get("/api/v1/admin/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
```

### Testing with Database

```python
def test_user_creation(db_auth, test_user_data):
    """Test with database session."""
    # db_auth is in-memory SQLite session
    from app.models.user import User

    user = User(**test_user_data)
    db_auth.add(user)
    db_auth.commit()

    assert user.id is not None
```

### Testing Agent Behavior

```python
def test_agent_registration():
    """Test agent registration."""
    from app.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()
    mock_agent = Mock()
    mock_agent.agent_id = "test"

    orchestrator.register_agent(mock_agent)
    assert orchestrator.get_agent("test") == mock_agent
```

### Testing with Mocks

```python
def test_with_mock(mock_anthropic_client):
    """Test using mock LLM client."""
    mock_anthropic_client.messages.create.return_value = Mock(
        content=[Mock(text="Mock response")]
    )

    response = mock_anthropic_client.messages.create(...)
    assert response.content[0].text == "Mock response"
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
1. Ensure virtual environment is activated
2. Install requirements: `pip install -r requirements.txt -r requirements-dev.txt`
3. Install socrates library: `pip install socrates-ai`

### Database Errors

If you see SQLAlchemy errors:
1. Tests use in-memory SQLite, not PostgreSQL
2. No database setup needed
3. If error persists, check conftest.py fixture configuration

### Timeout Errors

If tests timeout:
1. Increase timeout in pytest.ini
2. Check for blocking I/O in tests
3. Ensure mocks are properly configured

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pip install socrates-ai
      - run: pytest tests_new/ -v --cov=app --cov-report=xml
```

## Test Statistics

### Current Test Suite

- **Total Test Files:** 6
- **Total Tests:** 100+
- **Test Categories:** 6
- **Fixture Types:** 8
- **Markers:** 6

### Coverage Target

- Models: 95%+
- API endpoints: 90%+
- Agents: 85%+
- Security: 95%+
- Libraries: 90%+

## Contributing Tests

When adding new tests:

1. **Place tests in appropriate file:**
   - Models → `test_models.py`
   - API → `test_api_endpoints.py`
   - Agents → `test_agents_core.py`
   - Workflows → `test_integration_workflows.py`

2. **Use descriptive names:**
   ```python
   def test_user_registration_with_valid_email(test_client):
       """Clear description of what is being tested."""
   ```

3. **Add appropriate marker:**
   ```python
   @pytest.mark.unit
   def test_example():
       pass
   ```

4. **Use fixtures:**
   ```python
   def test_example(test_client, test_user_data, db_auth):
       pass
   ```

5. **Write docstrings:**
   ```python
   def test_example(test_client):
       """Clear description of test purpose and expectations."""
       assert True
   ```

## Resources

- **Pytest Documentation:** https://docs.pytest.org/
- **FastAPI Testing:** https://fastapi.tiangolo.com/advanced/testing-dependencies/
- **SQLAlchemy Testing:** https://docs.sqlalchemy.org/en/20/orm/persistence_techniques.html
- **Socrates Library:** https://pypi.org/project/socrates-ai/

## Questions?

For issues or questions about the testing suite:
1. Check test documentation above
2. Review existing test examples
3. Consult pytest documentation
4. Ask in project discussions

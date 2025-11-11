# TESTING STRATEGY

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟡 MEDIUM - Must complete before Phase 1 implementation

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Types](#test-types)
4. [Coverage Requirements](#coverage-requirements)
5. [Critical Tests (Archive Killers)](#critical-tests-archive-killers)
6. [Test Organization](#test-organization)
7. [Testing Tools](#testing-tools)
8. [Writing Tests](#writing-tests)
9. [Mocking Strategy](#mocking-strategy)
10. [Test Database Strategy](#test-database-strategy)
11. [CI/CD Integration](#cicd-integration)
12. [Performance Testing](#performance-testing)

---

## OVERVIEW

**Testing prevents failures.** Previous Socrates versions failed because:
- Database persistence wasn't tested (data loss on restart)
- Integration between components wasn't tested (agents couldn't communicate)
- Edge cases weren't tested (system broke on unexpected inputs)

**Socrates will succeed because:**
- ✅ Comprehensive test coverage (70%+ target)
- ✅ Critical paths tested first (database persistence, auth, QC system)
- ✅ Automated testing (CI/CD catches regressions)
- ✅ Real-world scenarios tested (workflow simulations)

---

## TESTING PHILOSOPHY

### Principle 1: Test Behavior, Not Implementation

❌ **BAD**: Testing internal implementation details

```python
def test_password_hashing():
    """Tests bcrypt internals (fragile)."""
    hasher = PasswordHasher()
    assert hasher.rounds == 12  # Implementation detail
    assert hasher.algorithm == "bcrypt"  # Implementation detail
```

✅ **GOOD**: Testing observable behavior

```python
def test_password_hashing():
    """Tests password hashing behavior (robust)."""
    auth_service = AuthService(db)

    # Register user with password
    user = auth_service.register_user("test@example.com", "MyPassword123!")

    # Password should be hashed (not stored as plain text)
    assert user.password_hash != "MyPassword123!"

    # Original password should verify successfully
    assert pwd_context.verify("MyPassword123!", user.password_hash) is True

    # Wrong password should fail
    assert pwd_context.verify("WrongPassword", user.password_hash) is False
```

### Principle 2: Test One Thing Per Test

❌ **BAD**: Testing multiple unrelated things

```python
def test_user_lifecycle():
    """Tests everything at once (hard to debug)."""
    user = register_user()
    login(user)
    create_project(user)
    start_chat(user, project)
    update_specs(user, project)
    # If this fails, which part failed?
```

✅ **GOOD**: Focused tests

```python
def test_user_registration():
    """Tests only registration."""
    user = auth_service.register_user("test@example.com", "Password123!")
    assert user.id is not None
    assert user.email == "test@example.com"

def test_user_login():
    """Tests only login."""
    user = create_test_user()
    tokens = auth_service.login(user.email, "Password123!")
    assert "access_token" in tokens
    assert "refresh_token" in tokens

def test_project_creation():
    """Tests only project creation."""
    user = create_test_user()
    project = project_service.create_project(user.id, "My App")
    assert project.id is not None
    assert project.name == "My App"
```

### Principle 3: Test Pyramid

```
        /\
       /  \
      / E2E \         ← Few (10%): Slow, expensive, full system
     /--------\
    /  Integ-  \      ← Some (30%): Moderate speed, test interactions
   /   ration   \
  /--------------\
 /      Unit      \   ← Most (60%): Fast, cheap, test individual functions
/------------------\
```

**60% Unit Tests**: Test individual functions/classes in isolation
**30% Integration Tests**: Test interactions between components
**10% E2E Tests**: Test complete user workflows

---

## TEST TYPES

### 1. Unit Tests

**What**: Test individual functions/classes in isolation

**When**: Test every function with business logic

**Tools**: pytest, unittest.mock

**Example:**

```python
# tests/unit/test_auth_service.py
import pytest
from services.auth_service import AuthService
from unittest.mock import Mock

def test_validate_email_format():
    """Test email validation logic."""
    auth_service = AuthService(Mock())

    # Valid emails
    assert auth_service._is_valid_email("test@example.com") is True
    assert auth_service._is_valid_email("user.name+tag@example.co.uk") is True

    # Invalid emails
    assert auth_service._is_valid_email("not-an-email") is False
    assert auth_service._is_valid_email("@example.com") is False
    assert auth_service._is_valid_email("test@") is False

def test_validate_password_strength():
    """Test password strength validation."""
    auth_service = AuthService(Mock())

    # Strong passwords
    assert auth_service._is_strong_password("SecurePass123!") is True
    assert auth_service._is_strong_password("Tr0ng&Secur3Pa$$") is True

    # Weak passwords
    assert auth_service._is_strong_password("short") is False  # Too short
    assert auth_service._is_strong_password("alllowercase123!") is False  # No uppercase
    assert auth_service._is_strong_password("ALLUPPERCASE123!") is False  # No lowercase
    assert auth_service._is_strong_password("NoDigitsHere!") is False  # No digits
    assert auth_service._is_strong_password("NoSpecialChars123") is False  # No special
```

### 2. Integration Tests

**What**: Test interactions between components

**When**: Test service → database, agent → service, API → service

**Tools**: pytest, test database

**Example:**

```python
# tests/integration/test_project_workflow.py
import pytest
from services.auth_service import AuthService
from services.project_service import ProjectService
from services.socratic_service import SocraticService

def test_project_creation_workflow(db_session):
    """Test complete project creation flow."""
    auth_service = AuthService(db_session)
    project_service = ProjectService(db_session)

    # 1. Register user
    user = auth_service.register_user("test@example.com", "Password123!")

    # 2. Create project
    project = project_service.create_project(
        user_id=user.id,
        name="E-commerce App",
        description="Online store for artisans",
    )

    # 3. Verify project exists
    assert project.id is not None
    assert project.user_id == user.id
    assert project.name == "E-commerce App"

    # 4. Verify project is in database
    db_project = project_service.get_project(project.id)
    assert db_project is not None
    assert db_project.id == project.id

    # 5. Verify user can access their projects
    user_projects = project_service.get_user_projects(user.id)
    assert len(user_projects) == 1
    assert user_projects[0].id == project.id
```

### 3. End-to-End Tests

**What**: Test complete user workflows

**When**: Test critical user paths (register → create project → chat → generate)

**Tools**: pytest, test database, mocked LLM

**Example:**

```python
# tests/e2e/test_discovery_phase.py
import pytest

def test_complete_discovery_phase(db_session, mock_llm):
    """Test complete Discovery phase workflow."""
    # 1. User registers
    auth_service = AuthService(db_session)
    user = auth_service.register_user("test@example.com", "Password123!")

    # 2. User creates project
    project_service = ProjectService(db_session)
    project = project_service.create_project(user.id, "My App")

    # 3. User starts chat session
    session_service = SessionService(db_session)
    session = session_service.create_session(project.id)

    # 4. System asks first question (Socratic mode)
    socratic_service = SocraticService(db_session, mock_llm)
    question = socratic_service.get_next_question(session.id, role="product_manager")

    assert question is not None
    assert "What problem does your project solve?" in question

    # 5. User answers question
    answer = "I want to build an e-commerce platform for artisans"
    socratic_service.process_answer(session.id, question, answer)

    # 6. System extracts specifications
    specs = socratic_service.get_extracted_specs(session.id)
    assert len(specs) > 0
    assert any("e-commerce" in spec.content.lower() for spec in specs)

    # 7. System calculates maturity
    maturity_service = MaturityService(db_session)
    maturity = maturity_service.calculate_maturity(project.id)
    assert maturity.overall_score > 0

    # 8. Verify persistence (CRITICAL - Archive killer test)
    # Simulate application restart by creating new service instances
    new_project_service = ProjectService(db_session)
    loaded_project = new_project_service.get_project(project.id)

    assert loaded_project is not None
    assert loaded_project.id == project.id
    assert loaded_project.name == "My App"

    # Verify specifications persisted
    loaded_specs = socratic_service.get_extracted_specs(session.id)
    assert len(loaded_specs) == len(specs)
```

---

## COVERAGE REQUIREMENTS

### Minimum Coverage Targets

| Component | Coverage | Priority |
|-----------|----------|----------|
| **Auth System** | 90%+ | 🔴 CRITICAL |
| **Database Persistence** | 95%+ | 🔴 CRITICAL |
| **Quality Control** | 90%+ | 🔴 CRITICAL |
| **Socratic Engine** | 85%+ | 🔴 CRITICAL |
| **Conflict Detection** | 85%+ | 🟡 HIGH |
| **Maturity System** | 80%+ | 🟡 HIGH |
| **API Endpoints** | 80%+ | 🟡 HIGH |
| **CLI Commands** | 75%+ | 🟢 MEDIUM |
| **Utilities** | 70%+ | 🟢 MEDIUM |
| **Overall** | 75%+ | 🟡 HIGH |

### Measuring Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open: htmlcov/index.html

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=75

# Coverage report example:
# Name                                 Stmts   Miss  Cover   Missing
# ------------------------------------------------------------------
# src/services/auth_service.py          120      6    95%   45-48, 89
# src/services/project_service.py        85      8    91%   102-109
# src/agents/socratic_agent.py          145     18    88%   67-72, 145-150
# ------------------------------------------------------------------
# TOTAL                                 1250     92    93%
```

---

## CRITICAL TESTS (ARCHIVE KILLERS)

These tests MUST pass or Socrates will fail like Archive did.

### Test 1: Database Persistence (ARCHIVE KILLER #1)

**Problem in Archive**: Data lost on application restart (no real database)

**Test**:

```python
def test_data_persists_across_sessions(db_session):
    """
    CRITICAL: Verify data persists when application restarts.

    This is the #1 reason previous Socrates versions failed.
    """
    # Session 1: Create data
    user = create_test_user(db_session, "user1@example.com")
    project = create_test_project(db_session, user.id, "My Project")
    spec = create_test_spec(db_session, project.id, "User authentication required")

    # Get IDs
    user_id = user.id
    project_id = project.id
    spec_id = spec.id

    # Simulate application restart: Close session
    db_session.close()

    # Session 2: Create NEW session (simulates restart)
    new_session = create_new_db_session()

    # Verify data still exists
    loaded_user = new_session.query(User).filter(User.id == user_id).first()
    assert loaded_user is not None
    assert loaded_user.email == "user1@example.com"

    loaded_project = new_session.query(Project).filter(Project.id == project_id).first()
    assert loaded_project is not None
    assert loaded_project.name == "My Project"

    loaded_spec = new_session.query(Specification).filter(Specification.id == spec_id).first()
    assert loaded_spec is not None
    assert loaded_spec.content == "User authentication required"

    new_session.close()
```

### Test 2: Agent Communication (ARCHIVE KILLER #2)

**Problem in Archive**: Agents couldn't communicate, orchestrator broken

**Test**:

```python
def test_agent_orchestration(db_session, mock_llm):
    """
    CRITICAL: Verify AgentOrchestrator coordinates agents correctly.
    """
    orchestrator = AgentOrchestrator(db_session, mock_llm)

    # Create project
    user = create_test_user(db_session)
    project = create_test_project(db_session, user.id)
    session = create_test_session(db_session, project.id)

    # 1. Socratic agent asks question
    question = orchestrator.run_agent("socratic", session_id=session.id)
    assert question is not None

    # 2. User provides answer
    answer = "I need user authentication with JWT tokens"

    # 3. Specification extractor processes answer
    specs = orchestrator.run_agent(
        "spec_extractor",
        session_id=session.id,
        user_input=answer,
    )
    assert len(specs) > 0

    # 4. Conflict detector checks for conflicts
    conflicts = orchestrator.run_agent("conflict_detector", project_id=project.id)
    assert conflicts is not None  # May be empty list

    # 5. Quality Control validates specs
    qc_result = orchestrator.run_agent("quality_control", project_id=project.id)
    assert qc_result is not None
    assert "is_blocking" in qc_result

    # Verify all agent results are persisted
    db_session.refresh(session)
    assert len(session.conversation_history) > 0
```

### Test 3: Conflict Detection (ARCHIVE KILLER #3)

**Problem in Archive**: Conflicts not detected, contradictory specs allowed

**Test**:

```python
def test_conflict_detection_prevents_contradictions(db_session):
    """
    CRITICAL: Verify conflict detection catches contradictions.
    """
    user = create_test_user(db_session)
    project = create_test_project(db_session, user.id)
    conflict_service = ConflictDetectionService(db_session)

    # Add spec: Use PostgreSQL
    spec1 = create_test_spec(db_session, project.id, "Use PostgreSQL for database")

    # Add conflicting spec: Use MongoDB
    spec2 = create_test_spec(db_session, project.id, "Use MongoDB for database")

    # Detect conflicts
    conflicts = conflict_service.detect_conflicts(project.id)

    # Should detect database conflict
    assert len(conflicts) > 0
    assert any(c.type == "technology" for c in conflicts)
    assert any("PostgreSQL" in c.description and "MongoDB" in c.description for c in conflicts)

    # Verify conflict prevents phase advancement
    quality_service = QualityControlService(db_session)
    result = quality_service.validate_phase_advancement(project.id)

    assert result["is_blocking"] is True
    assert "conflicts" in result["reason"].lower()
```

### Test 4: Quality Control Gates (ARCHIVE KILLER #4)

**Problem in Archive**: No quality gates, bad decisions allowed

**Test**:

```python
def test_quality_control_blocks_bad_decisions(db_session):
    """
    CRITICAL: Verify Quality Control prevents greedy decisions.
    """
    user = create_test_user(db_session)
    project = create_test_project(db_session, user.id)
    qc_service = QualityControlService(db_session)

    # Scenario: User wants to skip gap analysis (greedy decision)
    # Maturity: 45% (below 60% threshold)
    set_project_maturity(db_session, project.id, overall=45)

    # User requests phase advancement
    result = qc_service.validate_phase_advancement(project.id)

    # Should be BLOCKED
    assert result["is_blocking"] is True
    assert "maturity" in result["reason"].lower()
    assert "60%" in result["reason"]

    # Should provide alternatives
    assert "alternatives" in result
    assert len(result["alternatives"]) > 0
```

### Test 5: Authentication Security (ARCHIVE KILLER #5)

**Problem in Archive**: No authentication, anyone could access any data

**Test**:

```python
def test_authentication_prevents_unauthorized_access(db_session):
    """
    CRITICAL: Verify authentication prevents unauthorized access.
    """
    auth_service = AuthService(db_session)
    project_service = ProjectService(db_session)

    # Create two users
    user1 = create_test_user(db_session, "user1@example.com")
    user2 = create_test_user(db_session, "user2@example.com")

    # User 1 creates project
    project1 = project_service.create_project(user1.id, "User 1 Project")

    # User 2 tries to access User 1's project (should fail)
    with pytest.raises(PermissionError, match="Access denied"):
        project_service.get_project(project1.id, requesting_user_id=user2.id)

    # User 1 can access their own project (should succeed)
    loaded_project = project_service.get_project(project1.id, requesting_user_id=user1.id)
    assert loaded_project.id == project1.id
```

---

## TEST ORGANIZATION

### Directory Structure

```
tests/
├── conftest.py                      # Shared fixtures and configuration
├── unit/                            # Unit tests (60%)
│   ├── test_auth_service.py
│   ├── test_project_service.py
│   ├── test_socratic_service.py
│   ├── test_conflict_service.py
│   ├── test_quality_control.py
│   └── test_maturity_calculator.py
├── integration/                     # Integration tests (30%)
│   ├── test_database_operations.py
│   ├── test_agent_communication.py
│   ├── test_api_endpoints.py
│   └── test_cli_commands.py
├── e2e/                            # End-to-end tests (10%)
│   ├── test_discovery_phase.py
│   ├── test_analysis_phase.py
│   ├── test_design_phase.py
│   └── test_implementation_phase.py
└── fixtures/                       # Test data and fixtures
    ├── sample_projects.json
    ├── sample_specs.json
    └── mock_llm_responses.json
```

### conftest.py (Shared Fixtures)

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
from services.auth_service import AuthService
from unittest.mock import Mock

# Test database URL
TEST_DB_URL = "postgresql://socrates_user:password@localhost:5432/socrates_test"

@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """Create fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_llm():
    """Mock LLM client for testing."""
    mock = Mock()
    mock.generate.return_value = "Mocked LLM response"
    return mock

@pytest.fixture
def test_user(db_session):
    """Create test user."""
    auth_service = AuthService(db_session)
    user = auth_service.register_user("test@example.com", "Password123!")
    return user

@pytest.fixture
def test_project(db_session, test_user):
    """Create test project."""
    project_service = ProjectService(db_session)
    project = project_service.create_project(test_user.id, "Test Project")
    return project
```

---

## TESTING TOOLS

### Core Tools

```python
# requirements-dev.txt
pytest>=7.4.0              # Test runner
pytest-cov>=4.1.0          # Coverage plugin
pytest-xdist>=3.3.0        # Parallel test execution
pytest-mock>=3.11.1        # Mocking plugin
pytest-asyncio>=0.21.1     # Async test support
faker>=19.6.0              # Generate fake test data
factory-boy>=3.3.0         # Test data factories
freezegun>=1.2.2           # Mock datetime
responses>=0.23.0          # Mock HTTP requests
```

### Install Dev Dependencies

```bash
pip install -r requirements-dev.txt
```

---

## WRITING TESTS

### Test Naming Convention

```python
# Format: test_<what>_<condition>_<expected>

def test_user_registration_with_valid_data_succeeds():
    """Clear what's being tested."""
    pass

def test_user_registration_with_duplicate_email_fails():
    """Clear expected outcome."""
    pass

def test_jwt_token_creation_includes_user_id():
    """Clear verification."""
    pass
```

### AAA Pattern (Arrange, Act, Assert)

```python
def test_project_creation():
    # Arrange: Set up test data
    user = create_test_user()
    project_service = ProjectService(db_session)

    # Act: Perform the action being tested
    project = project_service.create_project(user.id, "My Project")

    # Assert: Verify expected outcome
    assert project.id is not None
    assert project.name == "My Project"
    assert project.user_id == user.id
```

---

## MOCKING STRATEGY

### When to Mock

✅ **DO Mock:**
- External LLM API calls (expensive, slow, rate-limited)
- External HTTP requests
- File system operations (in unit tests)
- Time/dates (for consistent tests)

❌ **DON'T Mock:**
- Database operations (use test database)
- Internal business logic
- Simple functions (just call them)

### Mocking LLM Calls

```python
# tests/test_socratic_service.py
from unittest.mock import Mock, patch

def test_ask_question_calls_llm(db_session):
    """Test Socratic service calls LLM correctly."""
    # Create mock LLM
    mock_llm = Mock()
    mock_llm.generate.return_value = "What problem does your app solve?"

    # Create service with mock
    socratic_service = SocraticService(db_session, llm_client=mock_llm)

    # Ask question
    question = socratic_service.ask_question(
        session_id="test-session",
        role="product_manager",
    )

    # Verify LLM was called
    assert mock_llm.generate.called
    assert "product_manager" in str(mock_llm.generate.call_args)

    # Verify question returned
    assert question == "What problem does your app solve?"
```

---

## TEST DATABASE STRATEGY

### Separate Test Database

```bash
# Create test database
createdb socrates_auth_test
createdb socrates_specs_test

# .env.test file
DATABASE_URL_AUTH=postgresql://socrates_user:password@localhost:5432/socrates_auth_test
DATABASE_URL_SPECS=postgresql://socrates_user:password@localhost:5432/socrates_specs_test
```

### Transaction Rollback (Fast Tests)

```python
@pytest.fixture
def db_session(engine):
    """
    Create database session with transaction rollback.

    Each test gets fresh database state:
    1. Begin transaction
    2. Run test
    3. Rollback transaction (nothing persisted)
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()  # Rollback, nothing saved
    connection.close()
```

---

## CI/CD INTEGRATION

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

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
      - uses: actions/checkout@v3

      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Create test databases
        run: |
          createdb -h localhost -U postgres socrates_auth_test
          createdb -h localhost -U postgres socrates_specs_test

      - name: Run tests
        env:
          DATABASE_URL_AUTH: postgresql://postgres:postgres@localhost:5432/socrates_auth_test
          DATABASE_URL_SPECS: postgresql://postgres:postgres@localhost:5432/socrates_specs_test
        run: |
          pytest --cov=src --cov-fail-under=75

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## PERFORMANCE TESTING

### Load Testing Critical Paths

```python
import time

def test_specification_extraction_performance(db_session, mock_llm):
    """Verify spec extraction completes in < 5 seconds."""
    user = create_test_user(db_session)
    project = create_test_project(db_session, user.id)
    session = create_test_session(db_session, project.id)

    spec_service = SpecificationService(db_session, mock_llm)

    # Measure time
    start = time.time()
    specs = spec_service.extract_specs(
        session_id=session.id,
        user_input="I need user authentication with JWT, PostgreSQL database, and React frontend",
    )
    elapsed = time.time() - start

    # Should complete in < 5 seconds
    assert elapsed < 5.0

    # Should extract multiple specs
    assert len(specs) >= 3
```

---

## VERIFICATION CHECKLIST

Before Phase 0 implementation:

- [ ] All 5 CRITICAL tests passing (Archive killers)
- [ ] Overall test coverage ≥ 75%
- [ ] Auth system coverage ≥ 90%
- [ ] Database persistence coverage ≥ 95%
- [ ] Quality Control coverage ≥ 90%
- [ ] Socratic engine coverage ≥ 85%
- [ ] CI/CD pipeline configured
- [ ] Test database setup documented
- [ ] Mocking strategy documented
- [ ] Performance tests for critical paths

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This testing strategy ensures Socrates doesn't repeat the failures of previous versions.*

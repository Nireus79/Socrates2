"""
Test configuration and fixtures for Socrates testing suite.

Provides:
- In-memory SQLite databases for testing
- FastAPI test client
- Pre-configured test users and projects
- Mock Anthropic client for LLM testing
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from typing import Generator

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL_AUTH"] = "sqlite:///:memory:"
os.environ["DATABASE_URL_SPECS"] = "sqlite:///:memory:"
os.environ["ANTHROPIC_API_KEY"] = "test-key-sk-test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG"] = "True"

# Security and token configuration
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# CORS configuration
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173"

# Logging configuration
os.environ["LOG_LEVEL"] = "INFO"


@pytest.fixture(scope="session")
def test_db_auth():
    """Create in-memory SQLite database for auth database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session")
def test_db_specs():
    """Create in-memory SQLite database for specs database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session")
def session_factory_auth(test_db_auth):
    """Create session factory for auth database."""
    # Import here to ensure environment variables are set
    from app.models.user import Base as AuthBase

    AuthBase.metadata.create_all(bind=test_db_auth)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_auth)
    return SessionLocal


@pytest.fixture(scope="session")
def session_factory_specs(test_db_specs):
    """Create session factory for specs database."""
    from app.models.project import Base as SpecsBase

    SpecsBase.metadata.create_all(bind=test_db_specs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_specs)
    return SessionLocal


@pytest.fixture
def db_auth(session_factory_auth) -> Generator[Session, None, None]:
    """Provide auth database session for each test."""
    session = session_factory_auth()
    yield session
    session.close()


@pytest.fixture
def db_specs(session_factory_specs) -> Generator[Session, None, None]:
    """Provide specs database session for each test."""
    session = session_factory_specs()
    yield session
    session.close()


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from app.main import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_anthropic_client():
    """Create mock Anthropic client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Mock LLM response")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def test_project_data():
    """Provide test project data."""
    return {
        "name": "Test Project",
        "description": "A test project for Socrates",
        "maturity_score": 0.5,
    }


@pytest.fixture
def test_specification_data():
    """Provide test specification data."""
    return {
        "category": "Performance",
        "key": "response_time",
        "value": "< 200ms",
        "confidence": 0.9,
    }


@pytest.fixture
def test_question_data():
    """Provide test question data."""
    return {
        "category": "Performance",
        "text": "What is your target response time?",
        "template_id": "perf_response_time",
        "confidence": 0.85,
    }


@pytest.fixture
def test_session_data():
    """Provide test conversation session data."""
    return {
        "name": "Specification Gathering Session 1",
        "description": "Initial requirements gathering session",
        "status": "active",
    }


# Markers for test organization
def pytest_configure(config):
    """Register pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "api: mark test as API endpoint test")
    config.addinivalue_line("markers", "agent: mark test as agent test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "database: mark test as database test")


# Pytest collection hook to skip tests requiring live database
def pytest_collection_modifyitems(config, items):
    """Skip tests that require external database if not available."""
    skip_marker = pytest.mark.skip(reason="Requires external database")
    for item in items:
        if "requires_live_db" in item.keywords:
            item.add_marker(skip_marker)


# ============================================================================
# ADDITIONAL FIXTURES FOR COMPREHENSIVE TESTING
# ============================================================================


@pytest.fixture
def test_user_data_alt():
    """Alternative test user data for multi-user scenarios."""
    return {
        "email": "user2@example.com",
        "password": "AnotherSecurePassword456!",
        "full_name": "Another User",
    }


@pytest.fixture
def authenticated_user(test_client, test_user_data):
    """Create authenticated user and return token."""
    # Register user
    test_client.post("/api/v1/auth/register", json=test_user_data)

    # Login and get token
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]}
    )

    if response.status_code == 200:
        data = response.json()
        return {
            "email": test_user_data["email"],
            "token": data.get("access_token"),
            "user_id": data.get("user_id"),
            "full_name": test_user_data["full_name"],
        }
    return None


@pytest.fixture
def auth_headers(authenticated_user):
    """Return authorization headers with Bearer token."""
    if authenticated_user and authenticated_user.get("token"):
        return {"Authorization": f"Bearer {authenticated_user['token']}"}
    return {}


@pytest.fixture
def test_project_data_alt():
    """Alternative project data for multi-project scenarios."""
    return {
        "name": "Alternative Project",
        "description": "Another test project",
        "maturity_score": 0.7,
    }


@pytest.fixture
def test_team_data():
    """Test team data."""
    return {
        "name": "Engineering Team",
        "description": "Core engineering team",
        "role": "owner",
    }


@pytest.fixture
def test_workflow_data():
    """Test workflow data."""
    return {
        "name": "Architecture Review Workflow",
        "description": "Comprehensive architecture specifications",
        "domains": ["architecture", "testing"],
        "status": "active",
    }


@pytest.fixture
def test_question_data_alt():
    """Alternative question data."""
    return {
        "category": "Architecture",
        "text": "What is your system architecture pattern?",
        "template_id": "arch_pattern",
        "confidence": 0.9,
    }


@pytest.fixture
def test_specification_data_alt():
    """Alternative specification data."""
    return {
        "category": "Architecture",
        "key": "architecture_pattern",
        "value": "Microservices",
        "confidence": 0.95,
    }


@pytest.fixture
def test_analytics_data():
    """Test analytics query data."""
    return {
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "metric_type": "domain_usage",
        "groupBy": "domain",
    }


@pytest.fixture
def test_export_data():
    """Test export configuration."""
    return {
        "format": "markdown",
        "include_analytics": True,
        "include_recommendations": True,
    }


@pytest.fixture
def mock_github_client():
    """Mock GitHub API client."""
    mock_client = MagicMock()
    mock_client.repos.get_readme.return_value = "# Test Repository"
    mock_client.repos.get_contents.return_value = [
        MagicMock(name="file.py", path="file.py", type="file")
    ]
    return mock_client


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response."""
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text="This is a comprehensive analysis of your specification.")
    ]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=150)
    return mock_response


# Add markers for new test types
def pytest_configure(config):
    """Register additional pytest markers."""
    config.addinivalue_line("markers", "api: mark test as API endpoint test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "cli: mark test as CLI test")
    config.addinivalue_line("markers", "service: mark test as service layer test")
    config.addinivalue_line("markers", "feature: mark test as feature test")
    config.addinivalue_line("markers", "workflow: mark test as workflow test")
    config.addinivalue_line("markers", "error: mark test as error handling test")

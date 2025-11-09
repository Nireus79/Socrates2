"""
Test configuration and fixtures for Socrates2 testing suite.

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
        "description": "A test project for Socrates2",
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

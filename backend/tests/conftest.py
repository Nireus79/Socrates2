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
    from app.core.database import Base
    # Import all auth models to register them with Base.metadata
    from app.models import (
        User, RefreshToken, AdminUser, AdminRole, AdminAuditLog
    )

    Base.metadata.create_all(bind=test_db_auth)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_auth)
    return SessionLocal


@pytest.fixture(scope="session")
def session_factory_specs(test_db_specs):
    """Create session factory for specs database."""
    from app.core.database import Base
    # Import specs models to register them with Base.metadata
    # Use alias for Session model to avoid conflict with sqlalchemy.orm.Session
    # Importing just the core models that tests actually use; other models are auto-registered
    # when they're imported by their modules
    from app.models import (
        Project, Session as SessionModel, Question, Specification, ConversationHistory,
        Conflict, GeneratedProject, GeneratedFile, QualityMetric,
        UserBehaviorPattern, QuestionEffectiveness, KnowledgeBaseDocument,
        Team, TeamMember, ProjectShare, APIKey, LLMUsageTracking,
        Subscription, Invoice, AnalyticsMetrics, DocumentChunk,
        NotificationPreferences, ActivityLog, ProjectInvitation
    )

    Base.metadata.create_all(bind=test_db_specs)
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


@pytest.fixture(autouse=True)
def cleanup_databases(session_factory_auth, session_factory_specs):
    """Clean up databases before each test."""
    from app.models import User, RefreshToken, Project, Session as SessionModel

    # Clear auth database tables before test
    session_auth = session_factory_auth()
    try:
        session_auth.query(RefreshToken).delete()
        session_auth.query(User).delete()
        session_auth.commit()
    except Exception:
        session_auth.rollback()
    finally:
        session_auth.close()

    # Clear specs database tables before test
    session_specs = session_factory_specs()
    try:
        session_specs.query(SessionModel).delete()
        session_specs.query(Project).delete()
        session_specs.commit()
    except Exception:
        session_specs.rollback()
    finally:
        session_specs.close()

    yield


@pytest.fixture
def test_client(session_factory_auth, session_factory_specs):
    """Create FastAPI test client with overridden database dependencies."""
    from app.main import create_app
    from app.core.database import get_db_auth, get_db_specs

    app = create_app()

    # Override database dependencies with test sessions
    def override_get_db_auth():
        db = session_factory_auth()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def override_get_db_specs():
        db = session_factory_specs()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db_auth] = override_get_db_auth
    app.dependency_overrides[get_db_specs] = override_get_db_specs

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
        "name": "Test",
        "surname": "User",
        "username": "testuser123",
        "email": "test@example.com",
        "password": "SecurePassword123!",
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
        "name": "Another",
        "surname": "User",
        "username": "anotheruser456",
        "email": "user2@example.com",
        "password": "AnotherSecurePassword456!",
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
            "name": test_user_data["name"],
            "surname": test_user_data["surname"],
            "username": test_user_data["username"],
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
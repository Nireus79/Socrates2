"""
Pytest configuration and fixtures for Socrates2 tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def database_url_auth():
    """Get auth database URL from environment"""
    url = os.getenv("DATABASE_URL_AUTH")
    if not url:
        pytest.skip("DATABASE_URL_AUTH not set in environment")
    return url


@pytest.fixture(scope="session")
def database_url_specs():
    """Get specs database URL from environment"""
    url = os.getenv("DATABASE_URL_SPECS")
    if not url:
        pytest.skip("DATABASE_URL_SPECS not set in environment")
    return url


@pytest.fixture(scope="session")
def auth_engine(database_url_auth):
    """Create SQLAlchemy engine for auth database"""
    engine = create_engine(database_url_auth)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def specs_engine(database_url_specs):
    """Create SQLAlchemy engine for specs database"""
    engine = create_engine(database_url_specs)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def auth_session(auth_engine):
    """Create a database session for auth database (with rollback)"""
    connection = auth_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def specs_session(specs_engine):
    """Create a database session for specs database (with rollback)"""
    from sqlalchemy import text

    connection = specs_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Create quality_metrics table if it doesn't exist
    # This is needed because Project model has a relationship to QualityMetric
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                metric_type VARCHAR(100) NOT NULL,
                metric_value NUMERIC(10, 2) NOT NULL,
                threshold NUMERIC(10, 2),
                passed BOOLEAN NOT NULL,
                details JSONB,
                calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """))
        session.commit()
    except:
        pass  # Table might already exist

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude API client for testing"""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def service_container(specs_session, auth_session, mock_claude_client):
    """Create service container for testing."""
    from app.core.dependencies import ServiceContainer

    container = ServiceContainer()
    container._db_session_specs = specs_session
    container._db_session_auth = auth_session
    container._claude_client = mock_claude_client
    return container


@pytest.fixture
def test_user(auth_session):
    """Create a test user in auth database."""
    from app.models.user import User
    import uuid

    user = User(
        id=uuid.uuid4(),
        email=f"test{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=User.hash_password("testpassword123"),
        is_active=True,
        is_verified=True,
        status='active',
        role='user'
    )
    auth_session.add(user)
    auth_session.commit()
    auth_session.refresh(user)
    return user


@pytest.fixture
def phase4_specs_session(specs_session):
    """Create specs session with Phase 4 tables for code generation tests."""
    from sqlalchemy import text

    # Create generated_projects table
    specs_session.execute(text("""
        CREATE TABLE IF NOT EXISTS generated_projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            generation_version INTEGER NOT NULL,
            total_files INTEGER,
            total_lines INTEGER,
            test_coverage NUMERIC(5, 2),
            quality_score NUMERIC(5, 2),
            traceability_score NUMERIC(5, 2),
            download_url VARCHAR(500),
            generation_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            generation_completed_at TIMESTAMP WITH TIME ZONE,
            generation_status VARCHAR(50) NOT NULL,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """))

    # Create generated_files table
    specs_session.execute(text("""
        CREATE TABLE IF NOT EXISTS generated_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            generated_project_id UUID NOT NULL REFERENCES generated_projects(id) ON DELETE CASCADE,
            file_path VARCHAR(500) NOT NULL,
            file_content TEXT NOT NULL,
            file_size INTEGER,
            spec_ids TEXT[],
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """))

    # Create indexes
    specs_session.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_projects_project_id ON generated_projects(project_id)"))
    specs_session.execute(text("CREATE INDEX IF NOT EXISTS idx_generated_files_generated_project_id ON generated_files(generated_project_id)"))

    specs_session.commit()

    yield specs_session

    # Cleanup
    try:
        specs_session.execute(text("DROP TABLE IF EXISTS generated_files CASCADE"))
        specs_session.execute(text("DROP TABLE IF EXISTS generated_projects CASCADE"))
        specs_session.commit()
    except:
        specs_session.rollback()


@pytest.fixture
def phase5_specs_session(phase4_specs_session):
    """Create specs session with Phase 5 tables for quality control tests."""
    from sqlalchemy import text

    # Create quality_metrics table if it doesn't exist
    # This allows Phase 5 tests to run independently without relying on migrations
    phase4_specs_session.execute(text("""
        CREATE TABLE IF NOT EXISTS quality_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            metric_type VARCHAR(100) NOT NULL,
            metric_value NUMERIC(10, 2) NOT NULL,
            threshold NUMERIC(10, 2),
            passed BOOLEAN NOT NULL,
            details JSONB,
            calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """))

    # Create indexes
    phase4_specs_session.execute(text("CREATE INDEX IF NOT EXISTS idx_quality_metrics_project_id ON quality_metrics(project_id)"))
    phase4_specs_session.execute(text("CREATE INDEX IF NOT EXISTS idx_quality_metrics_type ON quality_metrics(metric_type)"))
    phase4_specs_session.execute(text("CREATE INDEX IF NOT EXISTS idx_quality_metrics_calculated_at ON quality_metrics(calculated_at)"))

    phase4_specs_session.commit()

    yield phase4_specs_session

    # Cleanup: Drop table after test
    try:
        phase4_specs_session.execute(text("DROP TABLE IF EXISTS quality_metrics CASCADE"))
        phase4_specs_session.commit()
    except:
        phase4_specs_session.rollback()


@pytest.fixture
def phase4_service_container(phase4_specs_session, auth_session, mock_claude_client):
    """Create service container for Phase 4 tests with generated_projects table."""
    from app.core.dependencies import ServiceContainer

    container = ServiceContainer()
    container._db_session_specs = phase4_specs_session
    container._db_session_auth = auth_session
    container._claude_client = mock_claude_client
    return container


@pytest.fixture
def phase5_service_container(phase5_specs_session, auth_session, mock_claude_client):
    """Create service container for Phase 5 tests with quality_metrics table."""
    from app.core.dependencies import ServiceContainer

    container = ServiceContainer()
    container._db_session_specs = phase5_specs_session
    container._db_session_auth = auth_session
    container._claude_client = mock_claude_client
    return container

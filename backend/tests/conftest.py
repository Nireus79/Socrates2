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

    mock_client = Mock()
    # Mock the messages.create() method to return a proper response
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a test response from Claude.")]
    mock_response.usage = Mock(total_tokens=100)
    mock_client.messages.create.return_value = mock_response

    return mock_client


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

    user_id = uuid.uuid4()
    user_hex = user_id.hex[:8]

    user = User(
        id=user_id,
        name="Test",
        surname="User",
        username=f"testuser{user_hex}",
        email=f"test{user_hex}@example.com",
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


def _register_test_agents(auth_session, specs_session, mock_claude_client):
    """
    Register all agents for testing.
    This is called by the app factory to populate the orchestrator with agents.
    """
    from app.agents.orchestrator import AgentOrchestrator, set_orchestrator
    from app.agents.project import ProjectManagerAgent
    from app.agents.socratic import SocraticCounselorAgent
    from app.agents.context import ContextAnalyzerAgent
    from app.agents.conflict_detector import ConflictDetectorAgent
    from app.agents.code_generator import CodeGeneratorAgent
    from app.agents.quality_controller import QualityControllerAgent
    from app.agents.user_learning import UserLearningAgent
    from app.agents.direct_chat import DirectChatAgent
    from app.agents.team_collaboration import TeamCollaborationAgent
    from app.agents.export import ExportAgent
    from app.agents.multi_llm import MultiLLMManager
    from app.agents.github_integration import GitHubIntegrationAgent
    from app.core.dependencies import ServiceContainer

    # Create service container for tests
    services = ServiceContainer()
    services._db_session_auth = auth_session
    services._db_session_specs = specs_session
    services._claude_client = mock_claude_client

    # Create orchestrator directly with test services (don't use get_orchestrator)
    # because it would create a new one with production services
    orchestrator = AgentOrchestrator(services)

    # Register all agents
    pm_agent = ProjectManagerAgent("project", "Project Manager", services)
    socratic_agent = SocraticCounselorAgent("socratic", "Socratic Counselor", services)
    context_agent = ContextAnalyzerAgent("context", "Context Analyzer", services)
    conflict_agent = ConflictDetectorAgent("conflict", "Conflict Detector", services)
    code_gen_agent = CodeGeneratorAgent("code_generator", "Code Generator", services)
    quality_agent = QualityControllerAgent("quality", "Quality Controller", services)
    learning_agent = UserLearningAgent("learning", "User Learning", services)
    direct_chat_agent = DirectChatAgent("direct_chat", "Direct Chat", services)
    team_agent = TeamCollaborationAgent("team", "Team Collaboration", services)
    export_agent = ExportAgent("export", "Export Agent", services)
    llm_agent = MultiLLMManager("llm", "Multi-LLM Manager", services)
    github_agent = GitHubIntegrationAgent("github", "GitHub Integration", services)

    orchestrator.register_agent(pm_agent)
    orchestrator.register_agent(socratic_agent)
    orchestrator.register_agent(context_agent)
    orchestrator.register_agent(conflict_agent)
    orchestrator.register_agent(code_gen_agent)
    orchestrator.register_agent(quality_agent)
    orchestrator.register_agent(learning_agent)
    orchestrator.register_agent(direct_chat_agent)
    orchestrator.register_agent(team_agent)
    orchestrator.register_agent(export_agent)
    orchestrator.register_agent(llm_agent)
    orchestrator.register_agent(github_agent)

    # Set the orchestrator globally so it's used by the app
    set_orchestrator(orchestrator)


@pytest.fixture(autouse=True)
def override_app_dependencies(auth_session, specs_session, mock_claude_client):
    """Automatically override FastAPI app dependencies for API tests to use test sessions."""
    try:
        from app.main import create_app
        from app.core.database import get_db_auth, get_db_specs
        from fastapi.testclient import TestClient

        # Create app with test agent registration
        test_app = create_app(register_agents_fn=lambda: _register_test_agents(
            auth_session, specs_session, mock_claude_client
        ))

        # Override database dependencies
        def override_get_db_auth():
            return auth_session

        def override_get_db_specs():
            return specs_session

        test_app.dependency_overrides[get_db_auth] = override_get_db_auth
        test_app.dependency_overrides[get_db_specs] = override_get_db_specs

        # Create test client
        global _test_app
        _test_app = test_app

        yield

        # Clean up overrides after test
        test_app.dependency_overrides.clear()
    except Exception:
        # If import fails, just skip the override (fixture is optional for non-API tests)
        yield


_test_app = None


@pytest.fixture
def client():
    """
    Provide a TestClient that uses the app with overridden database dependencies.
    This fixture should be used by API tests instead of importing app directly.
    """
    from fastapi.testclient import TestClient

    if _test_app is not None:
        return TestClient(_test_app)
    else:
        # Fallback to importing app directly if override_app_dependencies fixture hasn't run
        from app.main import app
        return TestClient(app)


# ============================================================================
# COMPREHENSIVE TEST FIXTURES (Option 3B)
# ============================================================================

@pytest.fixture
def complete_user_and_project(auth_session, specs_session, test_user):
    """
    Create a complete test setup with user in auth DB and project in specs DB.

    Returns:
        dict with keys: user, project
    """
    from app.models.project import Project

    # User already created by test_user fixture in auth DB

    # Create project in specs DB (references user_id without FK constraint)
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Test Complete Project",
        description="Project with auth user reference",
        current_phase="discovery",
        maturity_score=0,
        status="active"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    return {
        "user": test_user,
        "project": project
    }


@pytest.fixture
def complete_user_project_session(complete_user_and_project, specs_session):
    """
    Create a complete test setup with user, project, AND session.

    Returns:
        dict with keys: user, project, session
    """
    from app.models.session import Session
    from datetime import datetime

    data = complete_user_and_project
    project = data["project"]

    # Create session in specs DB
    session = Session(
        project_id=project.id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )
    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)

    data["session"] = session
    return data


@pytest.fixture
def multiple_test_users(auth_session):
    """Create multiple test users for testing user-related features."""
    from app.models.user import User
    import uuid

    users = []
    for i in range(3):
        user_hex = uuid.uuid4().hex[:8]
        user = User(
            name=f"User{i}",
            surname=f"Test{i}",
            username=f"testuser{i}_{user_hex}",
            email=f"testuser{i}_{user_hex}@example.com",
            hashed_password=User.hash_password(f"password{i}"),
            is_active=True,
            is_verified=True,
            status="active",
            role="user"
        )
        auth_session.add(user)
        users.append(user)

    auth_session.commit()
    for user in users:
        auth_session.refresh(user)

    return users


# ============================================================================
# MARKER-BASED SESSION FIXTURES (Option 5C)
# ============================================================================

@pytest.fixture
def auth_session_smart(request, auth_engine):
    """
    Smart session - commits for @pytest.mark.persist, rolls back otherwise.

    This allows persistence tests to actually see committed data,
    while normal tests are isolated with rollback.

    Usage:
        @pytest.mark.persist
        def test_user_persists(auth_session_smart):
            user = User(...)
            auth_session_smart.add(user)
            auth_session_smart.commit()
    """
    from sqlalchemy.orm import sessionmaker

    connection = auth_engine.connect()

    # Check if test has @pytest.mark.persist
    should_commit = "persist" in request.keywords

    if should_commit:
        # For persistence tests, actually commit
        transaction = connection.begin()
    else:
        # For normal tests, use rollback
        transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()

    if should_commit:
        # Persistence tests: commit the transaction
        transaction.commit()
    else:
        # Normal tests: rollback for isolation
        transaction.rollback()

    connection.close()


@pytest.fixture
def specs_session_smart(request, specs_engine):
    """
    Smart session for specs DB - commits for @pytest.mark.persist, rolls back otherwise.

    Same behavior as auth_session_smart but for the specs database.
    """
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    connection = specs_engine.connect()

    # Check if test has @pytest.mark.persist
    should_commit = "persist" in request.keywords

    if should_commit:
        # For persistence tests, actually commit
        transaction = connection.begin()
    else:
        # For normal tests, use rollback
        transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    # Create quality_metrics table if it doesn't exist (needed for some tests)
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

    if should_commit:
        # Persistence tests: commit the transaction
        transaction.commit()
    else:
        # Normal tests: rollback for isolation
        transaction.rollback()

    connection.close()

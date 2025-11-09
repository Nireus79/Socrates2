"""
Phase 1 ↔ Phase 2 Interconnection Tests

Tests verify that Phase 1 infrastructure properly supports Phase 2 agents:
- BaseAgent pattern works with all Phase 2 agents
- ServiceContainer provides resources to Phase 2 agents
- AgentOrchestrator routes to Phase 2 agents
- Database relationships between Phase 1 and Phase 2 models
- Two-database architecture (auth + specs) works correctly
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from app.models.user import User
from app.models.project import Project
from app.models.session import Session
from app.models.question import Question
from app.models.specification import Specification
from app.agents.base import BaseAgent
from app.agents.project import ProjectManagerAgent
from app.agents.socratic import SocraticCounselorAgent
from app.agents.context import ContextAnalyzerAgent
from app.agents.orchestrator import AgentOrchestrator
from app.core.dependencies import ServiceContainer


# ============================================================================
# INTERCONNECTION TEST 1: BaseAgent → Phase 2 Agents
# ============================================================================

def test_phase2_agents_inherit_baseagent(service_container):
    """Verify all Phase 2 agents properly inherit from BaseAgent"""
    pm_agent = ProjectManagerAgent("pm", "PM", service_container)
    socratic_agent = SocraticCounselorAgent("socratic", "Socratic", service_container)
    context_agent = ContextAnalyzerAgent("context", "Context", service_container)

    # All should be instances of BaseAgent
    assert isinstance(pm_agent, BaseAgent)
    assert isinstance(socratic_agent, BaseAgent)
    assert isinstance(context_agent, BaseAgent)

    # All should have BaseAgent properties
    assert hasattr(pm_agent, 'agent_id')
    assert hasattr(pm_agent, 'name')
    assert hasattr(pm_agent, 'services')
    assert hasattr(pm_agent, 'stats')

    # All should have BaseAgent methods
    assert hasattr(pm_agent, 'process_request')
    assert hasattr(pm_agent, 'get_capabilities')
    assert hasattr(pm_agent, 'get_stats')


def test_phase2_agents_get_capabilities(service_container):
    """Verify Phase 2 agents implement get_capabilities from BaseAgent"""
    pm_agent = ProjectManagerAgent("pm", "PM", service_container)
    socratic_agent = SocraticCounselorAgent("socratic", "Socratic", service_container)
    context_agent = ContextAnalyzerAgent("context", "Context", service_container)

    pm_caps = pm_agent.get_capabilities()
    socratic_caps = socratic_agent.get_capabilities()
    context_caps = context_agent.get_capabilities()

    # All should return list of capabilities
    assert isinstance(pm_caps, list)
    assert len(pm_caps) > 0

    assert isinstance(socratic_caps, list)
    assert len(socratic_caps) > 0

    assert isinstance(context_caps, list)
    assert len(context_caps) > 0


def test_phase2_agents_statistics_tracking(service_container, test_user):
    """Verify Phase 2 agents track statistics via BaseAgent"""
    pm_agent = ProjectManagerAgent("pm", "PM", service_container)

    # Initial stats
    initial_stats = pm_agent.get_stats()
    assert initial_stats['stats']['requests_processed'] == 0

    # Process request
    pm_agent.process_request('create_project', {
        'user_id': str(test_user.id),
        'name': 'Test',
        'description': 'Test'
    })

    # Stats should update
    updated_stats = pm_agent.get_stats()
    assert updated_stats['stats']['requests_processed'] == 1
    assert updated_stats['stats']['last_activity'] is not None


# ============================================================================
# INTERCONNECTION TEST 2: ServiceContainer → Phase 2 Agents
# ============================================================================

def test_servicecontainer_provides_to_phase2_agents(service_container):
    """Verify ServiceContainer provides all resources to Phase 2 agents"""
    pm_agent = ProjectManagerAgent("pm", "PM", service_container)

    # Agent should have access to all ServiceContainer resources
    assert pm_agent.services is not None

    # Database access
    db_auth = pm_agent.services.get_database_auth()
    db_specs = pm_agent.services.get_database_specs()
    assert db_auth is not None
    assert db_specs is not None

    # Logger access
    logger = pm_agent.services.get_logger("test")
    assert logger is not None

    # Config access
    config = pm_agent.services.get_config()
    assert isinstance(config, dict)


def test_phase2_agents_use_two_database_architecture(service_container, test_user):
    """Verify Phase 2 agents correctly use two-database architecture"""
    pm_agent = ProjectManagerAgent("pm", "PM", service_container)

    # ProjectManager should:
    # 1. Query users from auth database
    # 2. Create projects in specs database

    result = pm_agent.process_request('create_project', {
        'user_id': str(test_user.id),
        'name': 'Test Project',
        'description': 'Test'
    })

    assert result['success'] is True

    # Verify user came from auth database
    db_auth = service_container.get_database_auth()
    user = db_auth.query(User).filter(User.id == test_user.id).first()
    assert user is not None

    # Verify project was created in specs database
    db_specs = service_container.get_database_specs()
    project = db_specs.query(Project).filter(Project.id == result['project_id']).first()
    assert project is not None
    assert project.user_id == test_user.id


# ============================================================================
# INTERCONNECTION TEST 3: AgentOrchestrator → Phase 2 Agents
# ============================================================================

def test_orchestrator_routes_to_phase2_agents(service_container, test_user):
    """Verify AgentOrchestrator can route to Phase 2 agents"""
    orchestrator = AgentOrchestrator(service_container)

    # Register Phase 2 agents
    pm_agent = ProjectManagerAgent("project", "PM", service_container)
    orchestrator.register_agent(pm_agent)

    # Route request through orchestrator
    result = orchestrator.route_request('project', 'create_project', {
        'user_id': str(test_user.id),
        'name': 'Orchestrated Project',
        'description': 'Created via orchestrator'
    })

    assert result['success'] is True
    assert result['project']['name'] == 'Orchestrated Project'


def test_orchestrator_validates_phase2_agent_capabilities(service_container):
    """Verify orchestrator checks Phase 2 agent capabilities"""
    orchestrator = AgentOrchestrator(service_container)

    pm_agent = ProjectManagerAgent("project", "PM", service_container)
    orchestrator.register_agent(pm_agent)

    # Valid capability should work
    result = orchestrator.route_request('project', 'create_project', {
        'user_id': '123',
        'name': 'Test'
    })
    # Will fail validation but capability is supported
    assert 'error_code' in result  # Validation error, not capability error

    # Invalid capability should fail
    result = orchestrator.route_request('project', 'invalid_action', {})
    assert result['success'] is False
    assert 'does not support action' in result['error']


# ============================================================================
# INTERCONNECTION TEST 4: Database Relationships (Phase 1 ↔ Phase 2)
# ============================================================================

def test_project_references_user_across_databases(auth_session, specs_session, test_user):
    """Verify Project (specs DB) can reference User (auth DB) via user_id"""
    # Create project referencing user from other database
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Cross-DB Project",
        description="Tests cross-database reference",
        current_phase="discovery",
        maturity_score=0,
        status="active"
    )

    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Verify user_id matches
    assert project.user_id == test_user.id

    # Verify user exists in auth database
    user = auth_session.query(User).filter(User.id == test_user.id).first()
    assert user is not None
    assert user.email == test_user.email


def test_session_references_project(specs_session, test_project):
    """Verify Session references Project correctly"""
    session = Session(
        project_id=test_project.id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )

    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)

    # Verify relationship
    assert session.project_id == test_project.id

    # Verify bidirectional relationship
    project = specs_session.query(Project).filter(Project.id == test_project.id).first()
    assert len(project.sessions) > 0
    assert project.sessions[0].id == session.id


def test_question_references_project_and_session(specs_session, test_project, test_session):
    """Verify Question references both Project and Session"""
    from decimal import Decimal

    question = Question(
        project_id=test_project.id,
        session_id=test_session.id,
        text="Test question?",
        category="goals",
        quality_score=Decimal('1.0')
    )

    specs_session.add(question)
    specs_session.commit()
    specs_session.refresh(question)

    # Verify relationships
    assert question.project_id == test_project.id
    assert question.session_id == test_session.id

    # Verify bidirectional relationships
    project = specs_session.query(Project).filter(Project.id == test_project.id).first()
    session = specs_session.query(Session).filter(Session.id == test_session.id).first()

    assert len(project.questions) > 0
    assert len(session.questions) > 0


def test_specification_references_project_and_session(specs_session, test_project, test_session):
    """Verify Specification references both Project and Session"""
    from decimal import Decimal

    spec = Specification(
        project_id=test_project.id,
        session_id=test_session.id,
        category="tech_stack",
        content="Use PostgreSQL",
        source="extracted",
        confidence=Decimal('0.9'),
        is_current=True
    )

    specs_session.add(spec)
    specs_session.commit()
    specs_session.refresh(spec)

    # Verify relationships
    assert spec.project_id == test_project.id
    assert spec.session_id == test_session.id

    # Verify bidirectional relationships
    project = specs_session.query(Project).filter(Project.id == test_project.id).first()
    session = specs_session.query(Session).filter(Session.id == test_session.id).first()

    assert len(project.specifications) > 0
    assert len(session.specifications) > 0


def test_cascade_delete_project_deletes_children(specs_session, test_user):
    """Verify deleting project cascades to sessions, questions, specs"""
    # Create project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Cascade Test",
        description="Test cascade delete",
        maturity_score=0,
        status="active"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Create session
    session = Session(
        project_id=project.id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )
    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)

    # Create question
    from decimal import Decimal
    question = Question(
        project_id=project.id,
        session_id=session.id,
        text="Test?",
        category="goals",
        quality_score=Decimal('1.0')
    )
    specs_session.add(question)
    specs_session.commit()

    # Remember IDs
    project_id = project.id
    session_id = session.id
    question_id = question.id

    # Delete project
    specs_session.delete(project)
    specs_session.commit()

    # Verify cascades
    assert specs_session.query(Project).filter(Project.id == project_id).first() is None
    assert specs_session.query(Session).filter(Session.id == session_id).first() is None
    assert specs_session.query(Question).filter(Question.id == question_id).first() is None


# ============================================================================
# INTERCONNECTION TEST 5: Data Flow (Phase 1 → Phase 2)
# ============================================================================

def test_data_flows_from_user_to_project(auth_session, specs_session, test_user):
    """Test data flows correctly: User (Phase 1) → Project (Phase 2)"""
    # Phase 1: User created in auth database
    assert test_user.id is not None

    # Phase 2: Project references user
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Flow Test",
        description="Testing data flow",
        maturity_score=0,
        status="active"
    )
    specs_session.add(project)
    specs_session.commit()

    # Verify flow
    assert project.user_id == test_user.id

    # Verify user is accessible from both databases
    user_from_auth = auth_session.query(User).filter(User.id == test_user.id).first()
    assert user_from_auth is not None
    assert user_from_auth.email == test_user.email


def test_data_flows_project_to_session_to_question(specs_session, test_project):
    """Test data flows: Project → Session → Question"""
    from decimal import Decimal

    # Phase 2: Session created for project
    session = Session(
        project_id=test_project.id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )
    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)

    # Phase 2: Question created for session
    question = Question(
        project_id=test_project.id,
        session_id=session.id,
        text="Test flow?",
        category="goals",
        quality_score=Decimal('1.0')
    )
    specs_session.add(question)
    specs_session.commit()
    specs_session.refresh(question)

    # Verify flow
    assert question.session_id == session.id
    assert question.project_id == test_project.id
    assert session.project_id == test_project.id


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_user(auth_session):
    """Create test user"""
    import uuid
    user_hex = uuid.uuid4().hex[:8]
    user = User(
        name="Test",
        surname="User",
        username=f"testuser{user_hex}",
        email="interconnect@example.com",
        hashed_password=User.hash_password("test123"),
        is_active=True,
        is_verified=True,
        status="active",
        role="user"
    )
    auth_session.add(user)
    auth_session.commit()
    auth_session.refresh(user)
    return user


@pytest.fixture
def test_project(specs_session, test_user):
    """Create test project"""
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Interconnection Test Project",
        description="For testing interconnections",
        current_phase="discovery",
        maturity_score=0,
        status="active"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)
    return project


@pytest.fixture
def test_session(specs_session, test_project):
    """Create test session"""
    session = Session(
        project_id=test_project.id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )
    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)
    return session


@pytest.fixture
def service_container(auth_session, specs_session):
    """Create service container with test databases"""
    container = ServiceContainer()
    container._db_session_auth = auth_session
    container._db_session_specs = specs_session
    return container

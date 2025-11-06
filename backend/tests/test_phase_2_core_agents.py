"""
Phase 2 Tests: Core Agents (ProjectManager, Socratic, ContextAnalyzer)

Tests cover:
- Model creation and relationships (Project, Session, Question, Specification)
- ProjectManagerAgent CRUD operations
- SocraticCounselorAgent question generation (mocked)
- ContextAnalyzerAgent specification extraction (mocked)
- Full workflow integration test
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from decimal import Decimal

from app.models.user import User
from app.models.project import Project
from app.models.session import Session
from app.models.question import Question
from app.models.specification import Specification
from app.models.conversation_history import ConversationHistory
from app.agents.project import ProjectManagerAgent
from app.agents.socratic import SocraticCounselorAgent
from app.agents.context import ContextAnalyzerAgent
from app.agents.orchestrator import AgentOrchestrator
from app.core.dependencies import ServiceContainer


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_user(auth_session):
    """Create test user in auth database"""
    user = User(
        email="testuser@example.com",
        hashed_password=User.hash_password("testpass123"),
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
    """Create test project in specs database"""
    project = Project(
        user_id=test_user.id,
        name="Test Project",
        description="Test project description",
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
def test_question(specs_session, test_project, test_session):
    """Create test question"""
    question = Question(
        project_id=test_project.id,
        session_id=test_session.id,
        text="What is the main goal of your project?",
        category="goals",
        context="Understanding project objectives",
        quality_score=Decimal('1.0')
    )
    specs_session.add(question)
    specs_session.commit()
    specs_session.refresh(question)
    return question


@pytest.fixture
def service_container(auth_session, specs_session):
    """Create service container with test databases"""
    container = ServiceContainer()
    # Override database sessions with test databases
    container._db_session_auth = auth_session
    container._db_session_specs = specs_session
    return container


# ============================================================================
# MODEL TESTS
# ============================================================================

def test_project_model_creation(specs_session, test_user):
    """Test Project model can be created"""
    project = Project(
        user_id=test_user.id,
        name="My Project",
        description="A test project",
        current_phase="discovery",
        maturity_score=0,
        status="active"
    )

    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    assert project.id is not None
    assert project.name == "My Project"
    assert project.maturity_score == 0
    assert project.status == "active"
    assert project.created_at is not None


def test_session_model_creation(specs_session, test_project):
    """Test Session model can be created"""
    session = Session(
        project_id=test_project.id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )

    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)

    assert session.id is not None
    assert session.project_id == test_project.id
    assert session.mode == "socratic"
    assert session.status == "active"


def test_question_model_creation(specs_session, test_project, test_session):
    """Test Question model can be created"""
    question = Question(
        project_id=test_project.id,
        session_id=test_session.id,
        text="What technologies will you use?",
        category="tech_stack",
        context="Identifying technical requirements",
        quality_score=Decimal('0.95')
    )

    specs_session.add(question)
    specs_session.commit()
    specs_session.refresh(question)

    assert question.id is not None
    assert question.text == "What technologies will you use?"
    assert question.category == "tech_stack"
    assert question.quality_score == Decimal('0.95')


def test_specification_model_creation(specs_session, test_project, test_session):
    """Test Specification model can be created"""
    spec = Specification(
        project_id=test_project.id,
        session_id=test_session.id,
        category="tech_stack",
        content="Use PostgreSQL as primary database",
        source="extracted",
        confidence=Decimal('0.9'),
        is_current=True
    )

    specs_session.add(spec)
    specs_session.commit()
    specs_session.refresh(spec)

    assert spec.id is not None
    assert spec.content == "Use PostgreSQL as primary database"
    assert spec.confidence == Decimal('0.9')
    assert spec.is_current is True


def test_conversation_history_model_creation(specs_session, test_session):
    """Test ConversationHistory model can be created"""
    message = ConversationHistory(
        session_id=test_session.id,
        role="user",
        content="I want to build an e-commerce platform",
        timestamp=datetime.utcnow()
    )

    specs_session.add(message)
    specs_session.commit()
    specs_session.refresh(message)

    assert message.id is not None
    assert message.role == "user"
    assert message.content == "I want to build an e-commerce platform"


# ============================================================================
# PROJECTMANAGERAGENT TESTS
# ============================================================================

def test_project_manager_agent_create_project(service_container, test_user):
    """Test ProjectManagerAgent can create a project"""
    agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    result = agent.process_request('create_project', {
        'user_id': str(test_user.id),
        'name': 'New Project',
        'description': 'A brand new project'
    })

    assert result['success'] is True
    assert 'project_id' in result
    assert result['project']['name'] == 'New Project'
    assert result['project']['maturity_score'] == 0


def test_project_manager_agent_get_project(service_container, test_project):
    """Test ProjectManagerAgent can get a project"""
    agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    result = agent.process_request('get_project', {
        'project_id': str(test_project.id)
    })

    assert result['success'] is True
    assert result['project']['name'] == test_project.name


def test_project_manager_agent_list_projects(service_container, test_user, test_project):
    """Test ProjectManagerAgent can list projects"""
    agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    result = agent.process_request('list_projects', {
        'user_id': str(test_user.id)
    })

    assert result['success'] is True
    assert result['count'] >= 1
    assert len(result['projects']) >= 1


def test_project_manager_agent_update_project(service_container, test_project):
    """Test ProjectManagerAgent can update a project"""
    agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    result = agent.process_request('update_project', {
        'project_id': str(test_project.id),
        'name': 'Updated Project Name',
        'description': 'Updated description'
    })

    assert result['success'] is True
    assert result['project']['name'] == 'Updated Project Name'


def test_project_manager_agent_update_maturity(service_container, test_project):
    """Test ProjectManagerAgent can update maturity score"""
    agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    result = agent.process_request('update_maturity', {
        'project_id': str(test_project.id),
        'maturity_score': 45
    })

    assert result['success'] is True
    assert result['maturity_score'] == 45


def test_project_manager_agent_delete_project(service_container, test_project):
    """Test ProjectManagerAgent can archive a project"""
    agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    result = agent.process_request('delete_project', {
        'project_id': str(test_project.id)
    })

    assert result['success'] is True

    # Verify project is archived
    db_specs = service_container.get_database_specs()
    project = db_specs.query(Project).filter(Project.id == test_project.id).first()
    assert project.status == 'archived'


# ============================================================================
# SOCRATICCOUNSELLORAGENT TESTS (with mocked Claude API)
# ============================================================================

@patch('app.agents.socratic.SocraticCounselorAgent.services')
def test_socratic_agent_generate_question(mock_services, service_container, test_project, test_session):
    """Test SocraticCounselorAgent can generate a question (mocked)"""

    # Mock Claude API response
    mock_claude_response = Mock()
    mock_claude_response.content = [
        Mock(text='{"text": "What is your primary business goal?", "category": "goals", "context": "Understanding core objectives"}')
    ]

    mock_claude_client = Mock()
    mock_claude_client.messages.create.return_value = mock_claude_response

    service_container._claude_client = mock_claude_client

    agent = SocraticCounselorAgent(
        agent_id="socratic",
        name="Socratic Counselor",
        services=service_container
    )

    result = agent.process_request('generate_question', {
        'project_id': str(test_project.id),
        'session_id': str(test_session.id)
    })

    assert result['success'] is True
    assert 'question' in result
    assert result['question']['category'] == 'goals'
    assert 'text' in result['question']


def test_socratic_agent_calculate_coverage(service_container, test_project, specs_session):
    """Test coverage calculation"""
    agent = SocraticCounselorAgent(
        agent_id="socratic",
        name="Socratic Counselor",
        services=service_container
    )

    # Create some specs
    specs = [
        Specification(
            project_id=test_project.id,
            category="goals",
            content="Spec 1",
            source="extracted",
            confidence=Decimal('0.9'),
            is_current=True
        ),
        Specification(
            project_id=test_project.id,
            category="goals",
            content="Spec 2",
            source="extracted",
            confidence=Decimal('0.9'),
            is_current=True
        ),
    ]

    for spec in specs:
        specs_session.add(spec)
    specs_session.commit()

    # Calculate coverage
    all_specs = specs_session.query(Specification).filter(
        Specification.project_id == test_project.id
    ).all()

    coverage = agent._calculate_coverage(all_specs)

    assert 'goals' in coverage
    assert coverage['goals'] > 0


# ============================================================================
# CONTEXTANALYZERAGENT TESTS (with mocked Claude API)
# ============================================================================

@patch('app.agents.context.ContextAnalyzerAgent.services')
def test_context_agent_extract_specifications(mock_services, service_container, test_question, test_session, test_project):
    """Test ContextAnalyzerAgent can extract specifications (mocked)"""

    # Mock Claude API response
    mock_claude_response = Mock()
    mock_claude_response.content = [
        Mock(text='[{"category": "tech_stack", "content": "Use Python and FastAPI", "confidence": 0.95, "reasoning": "User explicitly mentioned these technologies"}]')
    ]

    mock_claude_client = Mock()
    mock_claude_client.messages.create.return_value = mock_claude_response

    service_container._claude_client = mock_claude_client

    agent = ContextAnalyzerAgent(
        agent_id="context",
        name="Context Analyzer",
        services=service_container
    )

    result = agent.process_request('extract_specifications', {
        'session_id': str(test_session.id),
        'question_id': str(test_question.id),
        'answer': 'I want to build a REST API using Python and FastAPI'
    })

    assert result['success'] is True
    assert result['specs_extracted'] > 0
    assert 'specifications' in result
    assert 'maturity_score' in result


def test_context_agent_calculate_maturity(service_container, test_project, specs_session):
    """Test maturity calculation"""
    agent = ContextAnalyzerAgent(
        agent_id="context",
        name="Context Analyzer",
        services=service_container
    )

    # Create specs in different categories
    specs = [
        Specification(
            project_id=test_project.id,
            category="goals",
            content="Build e-commerce platform",
            source="extracted",
            confidence=Decimal('0.9'),
            is_current=True
        ),
        Specification(
            project_id=test_project.id,
            category="requirements",
            content="Support 1000 concurrent users",
            source="extracted",
            confidence=Decimal('0.8'),
            is_current=True
        ),
        Specification(
            project_id=test_project.id,
            category="tech_stack",
            content="Use PostgreSQL",
            source="extracted",
            confidence=Decimal('0.95'),
            is_current=True
        ),
    ]

    for spec in specs:
        specs_session.add(spec)
    specs_session.commit()

    # Calculate maturity
    maturity = agent._calculate_maturity(str(test_project.id), specs_session)

    assert maturity >= 0
    assert maturity <= 100
    assert isinstance(maturity, int)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow_integration(service_container, test_user, specs_session):
    """
    Integration test: Full workflow from project creation to spec extraction
    Tests all 3 agents working together
    """
    # Mock Claude API
    mock_claude_response_question = Mock()
    mock_claude_response_question.content = [
        Mock(text='{"text": "What problem does your project solve?", "category": "goals", "context": "Understanding project purpose"}')
    ]

    mock_claude_response_specs = Mock()
    mock_claude_response_specs.content = [
        Mock(text='[{"category": "goals", "content": "Build payment processing system", "confidence": 0.9, "reasoning": "User stated primary goal"}]')
    ]

    mock_claude_client = Mock()
    mock_claude_client.messages.create.side_effect = [
        mock_claude_response_question,
        mock_claude_response_specs
    ]

    service_container._claude_client = mock_claude_client

    # Step 1: Create project with ProjectManagerAgent
    pm_agent = ProjectManagerAgent(
        agent_id="project_manager",
        name="Project Manager",
        services=service_container
    )

    project_result = pm_agent.process_request('create_project', {
        'user_id': str(test_user.id),
        'name': 'Integration Test Project',
        'description': 'Testing full workflow'
    })

    assert project_result['success'] is True
    project_id = project_result['project_id']

    # Step 2: Create session
    session = Session(
        project_id=project_id,
        mode="socratic",
        status="active",
        started_at=datetime.utcnow()
    )
    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)

    # Step 3: Generate question with SocraticCounselorAgent
    socratic_agent = SocraticCounselorAgent(
        agent_id="socratic",
        name="Socratic Counselor",
        services=service_container
    )

    question_result = socratic_agent.process_request('generate_question', {
        'project_id': project_id,
        'session_id': str(session.id)
    })

    assert question_result['success'] is True
    question_id = question_result['question_id']

    # Step 4: Extract specs with ContextAnalyzerAgent
    context_agent = ContextAnalyzerAgent(
        agent_id="context",
        name="Context Analyzer",
        services=service_container
    )

    specs_result = context_agent.process_request('extract_specifications', {
        'session_id': str(session.id),
        'question_id': question_id,
        'answer': 'I want to build a payment processing system for small businesses'
    })

    assert specs_result['success'] is True
    assert specs_result['specs_extracted'] > 0
    assert specs_result['maturity_score'] > 0

    # Step 5: Verify project maturity was updated
    project = specs_session.query(Project).filter(Project.id == project_id).first()
    assert project.maturity_score > 0


def test_agent_orchestrator_registration(service_container):
    """Test all Phase 2 agents can be registered with orchestrator"""
    orchestrator = AgentOrchestrator(service_container)

    # Register all agents
    pm_agent = ProjectManagerAgent("project", "Project Manager", service_container)
    socratic_agent = SocraticCounselorAgent("socratic", "Socratic", service_container)
    context_agent = ContextAnalyzerAgent("context", "Context", service_container)

    orchestrator.register_agent(pm_agent)
    orchestrator.register_agent(socratic_agent)
    orchestrator.register_agent(context_agent)

    # Verify registration
    agents = orchestrator.get_all_agents()
    assert len(agents) == 3

    agent_ids = [a['agent_id'] for a in agents]
    assert 'project' in agent_ids
    assert 'socratic' in agent_ids
    assert 'context' in agent_ids

"""
Phase 3: Conflict Detection Tests

Test suite for:
- Conflict detection
- Conflict resolution
- Integration with ContextAnalyzerAgent
- API endpoints
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import uuid

from app.agents.conflict_detector import ConflictDetectorAgent
from app.agents.context import ContextAnalyzerAgent
from app.agents.project import ProjectManagerAgent
from app.agents.socratic import SocraticCounselorAgent
from app.agents.orchestrator import AgentOrchestrator
from app.models.conflict import Conflict, ConflictType, ConflictSeverity, ConflictStatus
from app.models.specification import Specification
from app.models.project import Project
from app.models.session import Session
from app.models.question import Question
from app.core.dependencies import ServiceContainer


@pytest.fixture
def service_container(specs_session, auth_session):
    """Create service container for testing."""
    from unittest.mock import Mock
    container = ServiceContainer()
    container._db_session_specs = specs_session
    container._db_session_auth = auth_session
    mock_claude_client = Mock()
    container._claude_client = mock_claude_client
    return container


@pytest.fixture
def conflict_agent(service_container):
    """Create ConflictDetectorAgent for testing."""
    return ConflictDetectorAgent("conflict", "Conflict Detector", service_container)


@pytest.fixture
def test_project(specs_session):
    """Create a test project."""
    user_id = uuid.uuid4()
    project = Project(
        creator_id=user_id,
        owner_id=user_id,
        user_id=user_id,
        name="Test Project",
        description="Test description",
        maturity_score=0.0
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)
    return project


@pytest.fixture
def test_session(specs_session, test_project):
    """Create a test session."""
    session = Session(
        project_id=test_project.id,
        mode="socratic",
        started_at=datetime.now(timezone.utc)
    )
    specs_session.add(session)
    specs_session.commit()
    specs_session.refresh(session)
    return session


@pytest.fixture
def test_question(specs_session, test_project, test_session):
    """Create a test question."""
    question = Question(
        project_id=test_project.id,
        session_id=test_session.id,
        text="What database do you want to use?",
        category="tech_stack",
        quality_score=1.0
    )
    specs_session.add(question)
    specs_session.commit()
    specs_session.refresh(question)
    return question


# ==================== Conflict Detection Tests ====================


def test_conflict_detector_agent_initialization(conflict_agent):
    """Test ConflictDetectorAgent can be initialized."""
    assert conflict_agent is not None
    assert conflict_agent.agent_id == "conflict"
    assert conflict_agent.name == "Conflict Detector"


def test_conflict_detector_capabilities(conflict_agent):
    """Test ConflictDetectorAgent exposes correct capabilities."""
    capabilities = conflict_agent.get_capabilities()
    assert 'detect_conflicts' in capabilities
    assert 'resolve_conflict' in capabilities
    assert 'list_conflicts' in capabilities
    assert 'get_conflict_details' in capabilities


def test_detect_conflicts_no_existing_specs(conflict_agent, test_project):
    """Test no conflicts detected when no existing specs."""
    new_specs = [
        {
            'category': 'tech_stack',
            'key': 'database',
            'value': 'PostgreSQL',
            'confidence': 0.9
        }
    ]

    result = conflict_agent.process_request('detect_conflicts', {
        'project_id': test_project.id,
        'new_specs': new_specs,
        'source_id': 'test-question-id'
    })

    assert result['success'] is True
    assert result['conflicts_detected'] is False
    assert len(result['conflicts']) == 0
    assert result['safe_to_save'] is True


@patch('anthropic.Anthropic')
def test_detect_conflicts_with_contradiction(mock_anthropic, conflict_agent, test_project, test_session, specs_session):
    """Test conflict detection when specs contradict."""
    # Create existing spec
    existing_spec = Specification(
        project_id=test_project.id,
        session_id=test_session.id,
        category="tech_stack",
        content="Use PostgreSQL as primary database",
        source='extracted',
        confidence=0.9,
        is_current=True
    )
    specs_session.add(existing_spec)
    specs_session.commit()
    specs_session.refresh(existing_spec)

    # Mock Claude response indicating conflict
    mock_response = Mock()
    mock_response.content = [
        Mock(text='{"conflicts_detected": true, "conflicts": [{"type": "technology", "description": "Conflicting database choices: PostgreSQL vs MySQL", "severity": "high", "spec_ids": ["' + str(existing_spec.id) + '"], "reasoning": "Cannot use both databases"}]}')
    ]
    conflict_agent.services.get_claude_client().messages.create.return_value = mock_response

    # New spec that conflicts
    new_specs = [
        {
            'category': 'tech_stack',
            'key': 'database',
            'value': 'MySQL',
            'confidence': 0.9
        }
    ]

    result = conflict_agent.process_request('detect_conflicts', {
        'project_id': test_project.id,
        'new_specs': new_specs,
        'source_id': 'test-question-id'
    })

    assert result['success'] is True
    assert result['conflicts_detected'] is True
    assert len(result['conflicts']) > 0
    assert result['safe_to_save'] is False

    # Verify conflict was saved to database
    conflict = specs_session.query(Conflict).filter(
        Conflict.project_id == test_project.id
    ).first()
    assert conflict is not None
    assert conflict.type == ConflictType.TECHNOLOGY
    assert conflict.status == ConflictStatus.OPEN


def test_detect_conflicts_validation_error(conflict_agent):
    """Test detect_conflicts returns error when required data missing."""
    result = conflict_agent.process_request('detect_conflicts', {})

    assert result['success'] is False
    assert result['error_code'] == 'VALIDATION_ERROR'


# ==================== Conflict Resolution Tests ====================


def test_resolve_conflict_keep_old(conflict_agent, test_project, specs_session):
    """Test resolving conflict by keeping old specification."""
    # Create a conflict
    conflict = Conflict(
        project_id=test_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Database conflict",
        spec_ids=["spec-1", "spec-2"],
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    specs_session.add(conflict)
    specs_session.commit()
    specs_session.refresh(conflict)

    # Resolve conflict
    result = conflict_agent.process_request('resolve_conflict', {
        'conflict_id': conflict.id,
        'resolution': 'keep_old',
        'resolution_notes': 'User prefers original choice'
    })

    assert result['success'] is True
    assert result['conflict']['status'] == 'resolved'
    assert 'keep_old' in result['conflict']['resolution']

    # Verify in database
    specs_session.refresh(conflict)
    assert conflict.status == ConflictStatus.RESOLVED
    assert conflict.resolved_at is not None
    assert conflict.resolved_by_user is True


def test_resolve_conflict_ignore(conflict_agent, test_project, specs_session):
    """Test resolving conflict by ignoring it."""
    # Create a conflict
    conflict = Conflict(
        project_id=test_project.id,
        type=ConflictType.REQUIREMENT,
        description="Minor requirement conflict",
        spec_ids=["spec-1"],
        severity=ConflictSeverity.LOW,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    specs_session.add(conflict)
    specs_session.commit()
    specs_session.refresh(conflict)

    # Resolve by ignoring
    result = conflict_agent.process_request('resolve_conflict', {
        'conflict_id': conflict.id,
        'resolution': 'ignore'
    })

    assert result['success'] is True
    assert result['conflict']['status'] == 'ignored'

    # Verify in database
    specs_session.refresh(conflict)
    assert conflict.status == ConflictStatus.IGNORED


def test_resolve_conflict_invalid_resolution(conflict_agent, test_project, specs_session):
    """Test resolve_conflict rejects invalid resolution type."""
    # Create a conflict
    conflict = Conflict(
        project_id=test_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Test conflict",
        spec_ids=["spec-1"],
        severity=ConflictSeverity.MEDIUM,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    specs_session.add(conflict)
    specs_session.commit()
    specs_session.refresh(conflict)

    # Try invalid resolution
    result = conflict_agent.process_request('resolve_conflict', {
        'conflict_id': conflict.id,
        'resolution': 'invalid_option'
    })

    assert result['success'] is False
    assert result['error_code'] == 'INVALID_RESOLUTION'


def test_resolve_conflict_not_found(conflict_agent):
    """Test resolve_conflict returns error for non-existent conflict."""
    result = conflict_agent.process_request('resolve_conflict', {
        'conflict_id': 'non-existent-id',
        'resolution': 'keep_old'
    })

    assert result['success'] is False
    assert result['error_code'] == 'CONFLICT_NOT_FOUND'


# ==================== List Conflicts Tests ====================


def test_list_conflicts(conflict_agent, test_project, specs_session):
    """Test listing conflicts for a project."""
    # Create multiple conflicts
    conflict1 = Conflict(
        project_id=test_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Database conflict",
        spec_ids=["spec-1"],
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    conflict2 = Conflict(
        project_id=test_project.id,
        type=ConflictType.REQUIREMENT,
        description="Requirement conflict",
        spec_ids=["spec-2"],
        severity=ConflictSeverity.MEDIUM,
        status=ConflictStatus.RESOLVED,
        detected_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc)
    )
    specs_session.add_all([conflict1, conflict2])
    specs_session.commit()

    # List all conflicts
    result = conflict_agent.process_request('list_conflicts', {
        'project_id': test_project.id
    })

    assert result['success'] is True
    assert result['count'] == 2
    assert len(result['conflicts']) == 2


def test_list_conflicts_filtered_by_status(conflict_agent, test_project, specs_session):
    """Test listing conflicts filtered by status."""
    # Create conflicts with different statuses
    conflict1 = Conflict(
        project_id=test_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Open conflict",
        spec_ids=["spec-1"],
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    conflict2 = Conflict(
        project_id=test_project.id,
        type=ConflictType.REQUIREMENT,
        description="Resolved conflict",
        spec_ids=["spec-2"],
        severity=ConflictSeverity.MEDIUM,
        status=ConflictStatus.RESOLVED,
        detected_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc)
    )
    specs_session.add_all([conflict1, conflict2])
    specs_session.commit()

    # List only open conflicts
    result = conflict_agent.process_request('list_conflicts', {
        'project_id': test_project.id,
        'status': 'open'
    })

    assert result['success'] is True
    assert result['count'] == 1
    assert result['conflicts'][0]['status'] == 'open'


# ==================== Get Conflict Details Tests ====================


def test_get_conflict_details(conflict_agent, test_project, test_session, specs_session):
    """Test getting detailed conflict information."""
    # Create a conflict with related specs
    spec1 = Specification(
        project_id=test_project.id,
        session_id=test_session.id,
        category="tech_stack",
        content="Use PostgreSQL",
        source='extracted',
        confidence=0.9,
        is_current=True
    )
    specs_session.add(spec1)
    specs_session.commit()
    specs_session.refresh(spec1)

    conflict = Conflict(
        project_id=test_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Database conflict",
        spec_ids=[str(spec1.id)],
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    specs_session.add(conflict)
    specs_session.commit()
    specs_session.refresh(conflict)

    # Get details
    result = conflict_agent.process_request('get_conflict_details', {
        'conflict_id': conflict.id
    })

    assert result['success'] is True
    assert result['conflict']['id'] == str(conflict.id)
    assert len(result['specifications']) == 1
    assert result['specifications'][0]['id'] == str(spec1.id)


# ==================== Integration Tests ====================


@patch('anthropic.Anthropic')
def test_context_analyzer_blocks_on_conflict(
    mock_anthropic,
    service_container,
    test_project,
    test_session,
    test_question,
    specs_session
):
    """Test ContextAnalyzerAgent blocks saving when conflicts detected."""
    # Create existing spec
    existing_spec = Specification(
        project_id=test_project.id,
        session_id=test_session.id,
        category="tech_stack",
        content="Use PostgreSQL",
        source='extracted',
        confidence=0.9,
        is_current=True
    )
    specs_session.add(existing_spec)
    specs_session.commit()

    # Setup orchestrator with agents (get the one from service_container to ensure consistency)
    orchestrator = service_container.get_orchestrator()
    context_agent = ContextAnalyzerAgent("context", "Context Analyzer", service_container)
    conflict_agent = ConflictDetectorAgent("conflict", "Conflict Detector", service_container)
    orchestrator.register_agent(context_agent)
    orchestrator.register_agent(conflict_agent)

    # Mock Claude responses
    # First response: extract specs
    extract_response = Mock()
    extract_response.content = [
        Mock(text='[{"category": "tech_stack", "content": "Use MySQL", "confidence": 0.9, "reasoning": "User wants MySQL"}]')
    ]

    # Second response: detect conflict
    conflict_response = Mock()
    conflict_response.content = [
        Mock(text='{"conflicts_detected": true, "conflicts": [{"type": "technology", "description": "Database conflict: PostgreSQL vs MySQL", "severity": "high", "spec_ids": ["' + str(existing_spec.id) + '"], "reasoning": "Cannot use both"}]}')
    ]

    service_container.get_claude_client().messages.create.side_effect = [
        extract_response,
        conflict_response
    ]

    # Try to extract specs that conflict
    result = context_agent.process_request('extract_specifications', {
        'session_id': test_session.id,
        'question_id': test_question.id,
        'answer': 'I want to use MySQL database'
    })

    # Should fail due to conflict
    assert result['success'] is False
    assert result['conflicts_detected'] is True
    assert len(result['conflicts']) > 0

    # Verify no specs were saved
    spec_count = specs_session.query(Specification).filter(
        Specification.content.like('%MySQL%')
    ).count()
    assert spec_count == 0

    # Verify conflict was saved
    conflict_count = specs_session.query(Conflict).filter(
        Conflict.project_id == test_project.id
    ).count()
    assert conflict_count > 0


@patch('anthropic.Anthropic')
def test_context_analyzer_saves_when_no_conflict(
    mock_anthropic,
    service_container,
    test_project,
    test_session,
    test_question,
    specs_session
):
    """Test ContextAnalyzerAgent saves specs when no conflicts."""
    # Setup orchestrator with agents (get the one from service_container to ensure consistency)
    orchestrator = service_container.get_orchestrator()
    context_agent = ContextAnalyzerAgent("context", "Context Analyzer", service_container)
    conflict_agent = ConflictDetectorAgent("conflict", "Conflict Detector", service_container)
    orchestrator.register_agent(context_agent)
    orchestrator.register_agent(conflict_agent)

    # Mock Claude responses
    # First response: extract specs
    extract_response = Mock()
    extract_response.content = [
        Mock(text='[{"category": "tech_stack", "content": "Use PostgreSQL", "confidence": 0.9, "reasoning": "User wants PostgreSQL"}]')
    ]

    # Second response: no conflict
    conflict_response = Mock()
    conflict_response.content = [
        Mock(text='{"conflicts_detected": false, "conflicts": []}')
    ]

    service_container.get_claude_client().messages.create.side_effect = [
        extract_response,
        conflict_response
    ]

    # Extract specs
    result = context_agent.process_request('extract_specifications', {
        'session_id': test_session.id,
        'question_id': test_question.id,
        'answer': 'I want to use PostgreSQL database'
    })

    # Should succeed
    assert result['success'] is True
    assert result['specs_extracted'] > 0

    # Verify specs were saved
    spec_count = specs_session.query(Specification).filter(
        Specification.content.like('%PostgreSQL%')
    ).count()
    assert spec_count > 0

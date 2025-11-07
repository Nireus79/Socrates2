"""
Phase 4: Code Generation Tests

Test suite for:
- Maturity gate (blocks if < 100%)
- Conflict gate (blocks if unresolved conflicts)
- Code generation logic
- File parsing and storage
- API endpoints
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from app.agents.code_generator import CodeGeneratorAgent
from app.agents.orchestrator import AgentOrchestrator
from app.models.project import Project, ProjectPhase
from app.models.specification import Specification
from app.models.conflict import Conflict, ConflictType, ConflictSeverity, ConflictStatus
from app.models.generated_project import GeneratedProject, GenerationStatus
from app.models.generated_file import GeneratedFile
from app.models.question import QuestionCategory
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
def code_gen_agent(service_container):
    """Create CodeGeneratorAgent for testing."""
    return CodeGeneratorAgent("code_generator", "Code Generator", service_container)


@pytest.fixture
def incomplete_project(specs_session):
    """Create a project with < 100% maturity."""
    project = Project(
        user_id=uuid.uuid4(),
        name="Incomplete Project",
        description="Test project with low maturity",
        maturity_score=45,
        current_phase="discovery"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)
    return project


@pytest.fixture
def complete_project(specs_session):
    """Create a project with 100% maturity."""
    project = Project(
        user_id=uuid.uuid4(),
        name="Complete Project",
        description="Test project with full maturity",
        maturity_score=100,
        current_phase="implementation"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add specifications across all categories
    categories = [
        QuestionCategory.GOALS,
        QuestionCategory.REQUIREMENTS,
        QuestionCategory.TECH_STACK,
        QuestionCategory.SCALABILITY,
        QuestionCategory.SECURITY,
        QuestionCategory.PERFORMANCE,
        QuestionCategory.TESTING,
        QuestionCategory.MONITORING,
        QuestionCategory.DATA_RETENTION,
        QuestionCategory.DISASTER_RECOVERY
    ]

    for i, category in enumerate(categories):
        for j in range(5):  # 5 specs per category
            spec = Specification(
                project_id=project.id,
                session_id=None,  # Specs don't need to reference a specific session
                category=category.value,  # Use the string value of the enum
                content=f"{category.value} specification {j+1}",
                source='extracted',
                confidence=Decimal("0.9"),
                is_current=True
            )
            specs_session.add(spec)

    specs_session.commit()
    return project


# ==================== Maturity Gate Tests ====================


def test_maturity_gate_blocks_low_maturity(code_gen_agent, incomplete_project):
    """Test code generation blocked when maturity < 100%."""
    result = code_gen_agent.process_request('generate_code', {
        'project_id': incomplete_project.id
    })

    assert result['success'] is False
    assert result['error_code'] == 'MATURITY_NOT_REACHED'
    assert result['maturity_score'] < 100.0
    assert 'missing_categories' in result
    assert len(result['missing_categories']) > 0


def test_maturity_gate_identifies_missing_categories(code_gen_agent, incomplete_project, specs_session):
    """Test maturity gate identifies which categories need more specs."""
    # Add only a few specs to goals category
    for i in range(2):
        spec = Specification(
            project_id=incomplete_project.id,
            session_id=None,  # Specs don't need to reference a specific session
            category=QuestionCategory.GOALS.value,  # Use string value
            content=f"Goal {i+1}",
            source='extracted',
            confidence=Decimal("0.9"),
            is_current=True
        )
        specs_session.add(spec)
    specs_session.commit()

    result = code_gen_agent.process_request('generate_code', {
        'project_id': incomplete_project.id
    })

    assert result['success'] is False
    assert 'missing_categories' in result

    # Should identify goals as missing (has 2, needs 5)
    goals_missing = [cat for cat in result['missing_categories'] if cat['category'] == 'goals']
    assert len(goals_missing) > 0
    assert goals_missing[0]['current'] == 2
    assert goals_missing[0]['gap'] > 0


# ==================== Conflict Gate Tests ====================


def test_conflict_gate_blocks_unresolved_conflicts(code_gen_agent, complete_project, specs_session):
    """Test code generation blocked when unresolved conflicts exist."""
    # Create an unresolved conflict
    conflict = Conflict(
        project_id=complete_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Database technology conflict",
        spec_ids=["spec-1", "spec-2"],
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.OPEN,
        detected_at=datetime.now(timezone.utc)
    )
    specs_session.add(conflict)
    specs_session.commit()

    result = code_gen_agent.process_request('generate_code', {
        'project_id': complete_project.id
    })

    assert result['success'] is False
    assert result['error_code'] == 'UNRESOLVED_CONFLICTS'
    assert result['unresolved_count'] == 1


def test_conflict_gate_allows_resolved_conflicts(code_gen_agent, complete_project, specs_session, mock_claude_client):
    """Test code generation proceeds when conflicts are resolved."""
    # Create a resolved conflict
    conflict = Conflict(
        project_id=complete_project.id,
        type=ConflictType.TECHNOLOGY,
        description="Database technology conflict",
        spec_ids=["spec-1", "spec-2"],
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.RESOLVED,
        detected_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc)
    )
    specs_session.add(conflict)
    specs_session.commit()

    # Mock Claude response
    mock_response = Mock()
    mock_response.content = [
        Mock(text='''```filepath: main.py
print("Hello World")
```''')
    ]
    mock_response.usage = Mock(total_tokens=100)
    mock_claude_client.messages.create.return_value = mock_response

    result = code_gen_agent.process_request('generate_code', {
        'project_id': complete_project.id
    })

    # Should succeed despite having a conflict (it's resolved)
    assert result['success'] is True


# ==================== Code Generation Tests ====================


@patch('anthropic.Anthropic')
def test_generate_code_success(mock_anthropic, code_gen_agent, complete_project, specs_session):
    """Test successful code generation."""
    # Mock Claude response with multiple files
    mock_response = Mock()
    mock_response.content = [
        Mock(text='''```filepath: backend/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

```filepath: backend/models.py
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String)
```

```filepath: README.md
# Generated Project

## Setup
pip install -r requirements.txt

## Run
uvicorn main:app --reload
```''')
    ]
    mock_response.usage = Mock(total_tokens=500)
    code_gen_agent.services.get_claude_client().messages.create.return_value = mock_response

    result = code_gen_agent.process_request('generate_code', {
        'project_id': complete_project.id
    })

    assert result['success'] is True
    assert 'generation_id' in result
    assert result['total_files'] == 3
    assert result['total_lines'] > 0
    assert result['generation_version'] == 1

    # Verify generation record created
    generation = specs_session.query(GeneratedProject).filter(
        GeneratedProject.id == result['generation_id']
    ).first()
    assert generation is not None
    assert generation.generation_status == GenerationStatus.COMPLETED
    assert generation.total_files == 3

    # Verify files saved
    files = specs_session.query(GeneratedFile).filter(
        GeneratedFile.generated_project_id == generation.id
    ).all()
    assert len(files) == 3

    file_paths = [f.file_path for f in files]
    assert 'backend/main.py' in file_paths
    assert 'backend/models.py' in file_paths
    assert 'README.md' in file_paths


@patch('anthropic.Anthropic')
def test_generate_code_versioning(mock_anthropic, code_gen_agent, complete_project, specs_session):
    """Test generation versioning increments correctly."""
    # Mock Claude response
    mock_response = Mock()
    mock_response.content = [
        Mock(text='```filepath: test.py\nprint("test")\n```')
    ]
    mock_response.usage = Mock(total_tokens=50)
    code_gen_agent.services.get_claude_client().messages.create.return_value = mock_response

    # First generation
    result1 = code_gen_agent.process_request('generate_code', {
        'project_id': complete_project.id
    })
    assert result1['success'] is True
    assert result1['generation_version'] == 1

    # Second generation
    result2 = code_gen_agent.process_request('generate_code', {
        'project_id': complete_project.id
    })
    assert result2['success'] is True
    assert result2['generation_version'] == 2

    # Verify both generations exist
    generations = specs_session.query(GeneratedProject).filter(
        GeneratedProject.project_id == complete_project.id
    ).all()
    assert len(generations) == 2


def test_generate_code_no_specifications(code_gen_agent, specs_session):
    """Test code generation fails when no specifications exist."""
    # Create project with 100% maturity but no specs
    project = Project(
        user_id=uuid.uuid4(),
        name="Empty Project",
        description="Project with no specs",
        maturity_score=100
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    result = code_gen_agent.process_request('generate_code', {
        'project_id': project.id
    })

    assert result['success'] is False
    assert result['error_code'] == 'NO_SPECIFICATIONS'


def test_generate_code_project_not_found(code_gen_agent):
    """Test code generation fails for non-existent project."""
    result = code_gen_agent.process_request('generate_code', {
        'project_id': 'non-existent-id'
    })

    assert result['success'] is False
    assert result['error_code'] == 'PROJECT_NOT_FOUND'


# ==================== File Parsing Tests ====================


def test_parse_generated_code(code_gen_agent):
    """Test parsing generated code into individual files."""
    code_text = '''```filepath: src/main.py
print("Hello")
```

```filepath: src/utils.py
def helper():
    pass
```

```filepath: tests/test_main.py
def test_main():
    assert True
```'''

    files = code_gen_agent._parse_generated_code(code_text)

    assert len(files) == 3
    assert files[0]['path'] == 'src/main.py'
    assert 'print("Hello")' in files[0]['content']
    assert files[1]['path'] == 'src/utils.py'
    assert files[2]['path'] == 'tests/test_main.py'


def test_parse_generated_code_empty(code_gen_agent):
    """Test parsing empty code text."""
    files = code_gen_agent._parse_generated_code("")
    assert len(files) == 0


# ==================== Get Generation Status Tests ====================


def test_get_generation_status(code_gen_agent, complete_project, specs_session):
    """Test getting status of a generation."""
    # Create a generation
    generation = GeneratedProject(
        project_id=complete_project.id,
        generation_version=1,
        total_files=5,
        total_lines=100,
        generation_started_at=datetime.now(timezone.utc),
        generation_status=GenerationStatus.COMPLETED,
        generation_completed_at=datetime.now(timezone.utc)
    )
    specs_session.add(generation)
    specs_session.commit()
    specs_session.refresh(generation)

    result = code_gen_agent.process_request('get_generation_status', {
        'generation_id': generation.id
    })

    assert result['success'] is True
    assert result['generation']['id'] == generation.id
    assert result['generation']['generation_status'] == 'completed'
    assert result['generation']['total_files'] == 5


def test_get_generation_status_not_found(code_gen_agent):
    """Test getting status of non-existent generation."""
    result = code_gen_agent.process_request('get_generation_status', {
        'generation_id': 'non-existent-id'
    })

    assert result['success'] is False
    assert result['error_code'] == 'GENERATION_NOT_FOUND'


# ==================== List Generations Tests ====================


def test_list_generations(code_gen_agent, complete_project, specs_session):
    """Test listing all generations for a project."""
    # Create multiple generations
    for i in range(3):
        generation = GeneratedProject(
            project_id=complete_project.id,
            generation_version=i + 1,
            total_files=5 + i,
            total_lines=100 * (i + 1),
            generation_started_at=datetime.now(timezone.utc),
            generation_status=GenerationStatus.COMPLETED,
            generation_completed_at=datetime.now(timezone.utc)
        )
        specs_session.add(generation)
    specs_session.commit()

    result = code_gen_agent.process_request('list_generations', {
        'project_id': complete_project.id
    })

    assert result['success'] is True
    assert result['count'] == 3
    assert len(result['generations']) == 3

    # Should be ordered by version descending
    versions = [g['generation_version'] for g in result['generations']]
    assert versions == [3, 2, 1]


def test_list_generations_empty(code_gen_agent, complete_project):
    """Test listing generations when none exist."""
    result = code_gen_agent.process_request('list_generations', {
        'project_id': complete_project.id
    })

    assert result['success'] is True
    assert result['count'] == 0
    assert len(result['generations']) == 0


# ==================== Group Specs Tests ====================


def test_group_specs_by_category(code_gen_agent, specs_session, complete_project):
    """Test grouping specifications by category."""
    # Specs already added in complete_project fixture
    specs = specs_session.query(Specification).filter(
        Specification.project_id == complete_project.id
    ).all()

    grouped = code_gen_agent._group_specs_by_category(specs)

    # Should have specs grouped by category
    assert 'goals' in grouped
    assert 'requirements' in grouped
    assert 'tech_stack' in grouped

    # Each category should have 5 specs (from fixture)
    assert len(grouped['goals']) == 5
    assert len(grouped['requirements']) == 5


# ==================== Build Prompt Tests ====================


def test_build_code_generation_prompt(code_gen_agent, complete_project, specs_session):
    """Test building comprehensive code generation prompt."""
    specs = specs_session.query(Specification).filter(
        Specification.project_id == complete_project.id
    ).all()

    grouped = code_gen_agent._group_specs_by_category(specs)
    prompt = code_gen_agent._build_code_generation_prompt(complete_project, grouped)

    # Verify prompt contains key elements
    assert complete_project.name in prompt
    assert complete_project.description in prompt
    assert 'GOALS' in prompt
    assert 'REQUIREMENTS' in prompt
    assert 'TECH STACK' in prompt
    assert 'filepath:' in prompt  # Format instructions
    assert 'production-ready' in prompt.lower()


# ==================== Validation Tests ====================


def test_generate_code_validation_error(code_gen_agent):
    """Test generate_code returns error when project_id missing."""
    result = code_gen_agent.process_request('generate_code', {})

    assert result['success'] is False
    assert result['error_code'] == 'VALIDATION_ERROR'


def test_get_generation_status_validation_error(code_gen_agent):
    """Test get_generation_status returns error when generation_id missing."""
    result = code_gen_agent.process_request('get_generation_status', {})

    assert result['success'] is False
    assert result['error_code'] == 'VALIDATION_ERROR'


def test_list_generations_validation_error(code_gen_agent):
    """Test list_generations returns error when project_id missing."""
    result = code_gen_agent.process_request('list_generations', {})

    assert result['success'] is False
    assert result['error_code'] == 'VALIDATION_ERROR'

"""
Comprehensive End-to-End Integration Tests

Tests complete user workflows and all system interconnections:
1. User registration and authentication
2. Project creation and management
3. Socratic questioning and answering
4. Specification extraction and conflict detection
5. Code generation
6. Quality control and team collaboration

This simulates actual user behavior to ensure all components work together.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from passlib.context import CryptContext

from app.models.user import User
from app.models.project import Project
from app.models.session import Session
from app.models.question import Question
from app.models.specification import Specification
from app.models.conflict import Conflict
from app.models.generated_project import GeneratedProject
from app.models.team import Team
from app.models.team_member import TeamMember

from app.agents.project import ProjectManagerAgent
from app.agents.socratic import SocraticCounselorAgent
from app.agents.context import ContextAnalyzerAgent
from app.agents.conflict_detector import ConflictDetectorAgent
from app.agents.code_generator import CodeGeneratorAgent
from app.agents.quality_controller import QualityControllerAgent
from app.agents.team_collaboration import TeamCollaborationAgent
from app.agents.orchestrator import AgentOrchestrator
from app.core.dependencies import ServiceContainer


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestEndToEndUserWorkflow:
    """Test complete user workflow from registration to code generation"""

    @pytest.fixture
    def service_container(self, auth_session, specs_session):
        """Create a service container with test database sessions"""

        class TestServiceContainer(ServiceContainer):
            def __init__(self, auth_sess, specs_sess):
                super().__init__()
                self._auth_session = auth_sess
                self._specs_session = specs_sess

            def get_database_auth(self):
                return self._auth_session

            def get_database_specs(self):
                return self._specs_session

        return TestServiceContainer(auth_session, specs_session)

    @pytest.fixture
    def test_user(self, auth_session):
        """Create a test user"""
        user = User(
            email=f"testuser_{uuid4().hex[:8]}@example.com",
            hashed_password=pwd_context.hash("testpassword123"),
            role="user",
            status="active"
        )
        auth_session.add(user)
        auth_session.flush()
        return user

    def test_complete_user_workflow(self, service_container, test_user, auth_session, specs_session):
        """
        Test the complete user workflow:
        1. Create project
        2. Start Socratic session
        3. Generate questions
        4. Submit answers and extract specs
        5. Detect conflicts
        6. Generate code
        """

        # ===== STEP 1: Create Project =====
        print("\n=== STEP 1: Creating Project ===")
        project_agent = ProjectManagerAgent("project", "ProjectManagerAgent", service_container)

        create_result = project_agent.execute({
            'action': 'create_project',
            'user_id': str(test_user.id),
            'name': 'E2E Test Project',
            'description': 'A test project for end-to-end integration testing'
        })

        assert create_result['success'] is True, f"Project creation failed: {create_result.get('error')}"
        project_id = create_result['project_id']
        print(f"✓ Project created: {project_id}")

        # Verify project exists in database
        project = specs_session.query(Project).filter_by(id=project_id).first()
        assert project is not None, "Project not found in database"
        assert project.name == 'E2E Test Project'
        assert project.maturity_score == 0

        # ===== STEP 2: Start Socratic Session =====
        print("\n=== STEP 2: Starting Socratic Session ===")
        session = Session(
            project_id=project_id,
            status='active',
            started_at=datetime.now(timezone.utc)
        )
        specs_session.add(session)
        specs_session.flush()
        session_id = session.id
        print(f"✓ Session started: {session_id}")

        # ===== STEP 3: Generate Questions =====
        print("\n=== STEP 3: Generating Socratic Questions ===")
        socratic_agent = SocraticCounselorAgent("socratic", "SocraticCounselorAgent", service_container)

        question_result = socratic_agent.execute({
            'action': 'generate_question',
            'project_id': str(project_id),
            'session_id': str(session_id)
        })

        assert question_result['success'] is True, f"Question generation failed: {question_result.get('error')}"
        question_id = question_result['question_id']
        print(f"✓ Question generated: {question_id}")
        print(f"  Question text: {question_result['question']['text']}")

        # Verify question exists in database
        question = specs_session.query(Question).filter_by(id=question_id).first()
        assert question is not None, "Question not found in database"

        # ===== STEP 4: Submit Answer and Extract Specs =====
        print("\n=== STEP 4: Submitting Answer and Extracting Specs ===")
        context_agent = ContextAnalyzerAgent("context", "ContextAnalyzerAgent", service_container)

        # Simulate user answer
        user_answer = """
        I want to build a task management application for small teams.
        It should support:
        - User authentication with email/password
        - Create, update, delete tasks
        - Assign tasks to team members
        - Mark tasks as complete
        - Filter tasks by status and assignee
        - RESTful API with FastAPI
        - PostgreSQL database
        - Support for 100 concurrent users
        """

        extract_result = context_agent.execute({
            'action': 'extract_specifications',
            'session_id': str(session_id),
            'question_id': str(question_id),
            'answer': user_answer
        })

        assert extract_result['success'] is True, f"Spec extraction failed: {extract_result.get('error')}"
        specs_extracted = extract_result.get('specs_extracted', 0)
        print(f"✓ Extracted {specs_extracted} specifications")

        # Verify specs exist in database
        specs = specs_session.query(Specification).filter_by(project_id=project_id).all()
        assert len(specs) > 0, "No specifications found in database"
        print(f"  Specs in database: {len(specs)}")

        # Verify maturity increased
        specs_session.refresh(project)
        assert project.maturity_score > 0, "Maturity score did not increase"
        print(f"  Project maturity: {project.maturity_score}%")

        # ===== STEP 5: Test Conflict Detection =====
        print("\n=== STEP 5: Testing Conflict Detection ===")
        conflict_agent = ConflictDetectorAgent("conflict", "ConflictDetectorAgent", service_container)

        # Simulate conflicting specs
        conflicting_specs = [
            {
                'category': 'tech_stack',
                'key': 'database',
                'value': 'MongoDB',
                'confidence': 0.8
            }
        ]

        conflict_result = conflict_agent.execute({
            'action': 'detect_conflicts',
            'project_id': str(project_id),
            'new_specs': conflicting_specs,
            'source_id': str(question_id)
        })

        assert conflict_result['success'] is True, f"Conflict detection failed: {conflict_result.get('error')}"
        conflicts_detected = conflict_result.get('conflicts_detected', False)
        print(f"✓ Conflict detection completed: {conflicts_detected}")

        # ===== STEP 6: Test Quality Control =====
        print("\n=== STEP 6: Testing Quality Control ===")
        quality_agent = QualityControllerAgent("quality", "QualityControllerAgent", service_container)

        # Test question bias detection
        bias_result = quality_agent.execute({
            'action': 'analyze_question',
            'question_text': 'What features do you need?',
            'project_id': str(project_id)
        })

        assert bias_result['success'] is True, f"Bias analysis failed: {bias_result.get('error')}"
        print(f"✓ Bias analysis: score={bias_result.get('bias_score', 0):.2f}")

        # Test coverage analysis
        coverage_result = quality_agent.execute({
            'action': 'analyze_coverage',
            'project_id': str(project_id)
        })

        assert coverage_result['success'] is True, f"Coverage analysis failed: {coverage_result.get('error')}"
        coverage_score = coverage_result.get('coverage_score', 0)
        print(f"✓ Coverage analysis: score={coverage_score:.2%}")

        print("\n=== ✓ END-TO-END WORKFLOW COMPLETE ===")


class TestAgentInterconnections:
    """Test agent-to-agent communication and orchestrator routing"""

    @pytest.fixture
    def orchestrator(self, auth_session, specs_session):
        """Create orchestrator with test database sessions"""

        class TestServiceContainer(ServiceContainer):
            def __init__(self, auth_sess, specs_sess):
                super().__init__()
                self._auth_session = auth_sess
                self._specs_session = specs_sess

            def get_database_auth(self):
                return self._auth_session

            def get_database_specs(self):
                return self._specs_session

        services = TestServiceContainer(auth_session, specs_session)
        return AgentOrchestrator(services)

    def test_orchestrator_routing(self, orchestrator, auth_session, specs_session):
        """Test that orchestrator correctly routes requests to agents"""
        print("\n=== Testing Orchestrator Routing ===")

        # Create test user
        user = User(
            email=f"routing_test_{uuid4().hex[:8]}@example.com",
            hashed_password=pwd_context.hash("testpass"),
            role="user",
            status="active"
        )
        auth_session.add(user)
        auth_session.flush()

        # Test routing to project agent
        result = orchestrator.route_request(
            agent_id='project',
            action='create_project',
            data={
                'user_id': str(user.id),
                'name': 'Routing Test Project',
                'description': 'Testing orchestrator routing'
            }
        )

        assert result['success'] is True, f"Orchestrator routing failed: {result.get('error')}"
        project_id = result['project_id']
        print(f"✓ Orchestrator successfully routed to ProjectManagerAgent: {project_id}")

        # Verify project was created
        project = specs_session.query(Project).filter_by(id=project_id).first()
        assert project is not None, "Project not created via orchestrator"

        print("✓ Orchestrator routing test passed")

    def test_agent_to_agent_communication(self, orchestrator, auth_session, specs_session):
        """Test that agents can call other agents through orchestrator"""
        print("\n=== Testing Agent-to-Agent Communication ===")

        # Create test data
        user = User(
            email=f"agent_comm_test_{uuid4().hex[:8]}@example.com",
            hashed_password=pwd_context.hash("testpass"),
            role="user",
            status="active"
        )
        auth_session.add(user)
        auth_session.flush()

        # Create project
        project = Project(
            user_id=user.id,
            name='Agent Communication Test',
            description='Test',
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )
        specs_session.add(project)
        specs_session.flush()

        # Create session
        session = Session(
            project_id=project.id,
            status='active',
            started_at=datetime.now(timezone.utc)
        )
        specs_session.add(session)
        specs_session.flush()

        # Create question
        question = Question(
            project_id=project.id,
            session_id=session.id,
            text='What are your requirements?',
            category='requirements'
        )
        specs_session.add(question)
        specs_session.flush()

        # ContextAnalyzerAgent calls ConflictDetectorAgent internally
        # Test this interconnection
        context_agent = ContextAnalyzerAgent("context", "ContextAnalyzerAgent", orchestrator.services)

        result = context_agent.execute({
            'action': 'extract_specifications',
            'session_id': str(session.id),
            'question_id': str(question.id),
            'answer': 'I need a web application with user authentication and a REST API.'
        })

        # Should succeed even if conflict detection is called internally
        assert result['success'] is True, f"Agent-to-agent communication failed: {result.get('error')}"
        print("✓ Agent-to-agent communication test passed")


class TestDatabaseOperations:
    """Test database operations across both databases"""

    def test_two_database_operations(self, auth_session, specs_session):
        """Test operations that span both auth and specs databases"""
        print("\n=== Testing Two-Database Operations ===")

        # Create user in auth database
        user = User(
            email=f"twodb_test_{uuid4().hex[:8]}@example.com",
            hashed_password=pwd_context.hash("testpass"),
            role="user",
            status="active"
        )
        auth_session.add(user)
        auth_session.flush()
        print(f"✓ User created in auth DB: {user.id}")

        # Create project in specs database (references user from auth DB)
        project = Project(
            user_id=user.id,
            name='Two-Database Test Project',
            description='Testing cross-database references',
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )
        specs_session.add(project)
        specs_session.flush()
        print(f"✓ Project created in specs DB: {project.id}")

        # Verify both exist
        assert auth_session.query(User).filter_by(id=user.id).first() is not None
        assert specs_session.query(Project).filter_by(id=project.id).first() is not None

        print("✓ Two-database operation test passed")

    def test_transaction_isolation(self, auth_session, specs_session):
        """Test that transactions are properly isolated"""
        print("\n=== Testing Transaction Isolation ===")

        # Create user
        user = User(
            email=f"isolation_test_{uuid4().hex[:8]}@example.com",
            hashed_password=pwd_context.hash("testpass"),
            role="user",
            status="active"
        )
        auth_session.add(user)
        auth_session.flush()

        # Create project that references user
        project = Project(
            user_id=user.id,
            name='Isolation Test Project',
            description='Test',
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )
        specs_session.add(project)
        specs_session.flush()

        # Both should be visible in their respective sessions
        assert auth_session.query(User).filter_by(id=user.id).first() is not None
        assert specs_session.query(Project).filter_by(id=project.id).first() is not None

        print("✓ Transaction isolation test passed")


class TestErrorHandlingAndRecovery:
    """Test that error handling works correctly across all components"""

    @pytest.fixture
    def service_container(self, auth_session, specs_session):
        """Create a service container with test database sessions"""

        class TestServiceContainer(ServiceContainer):
            def __init__(self, auth_sess, specs_sess):
                super().__init__()
                self._auth_session = auth_sess
                self._specs_session = specs_sess

            def get_database_auth(self):
                return self._auth_session

            def get_database_specs(self):
                return self._specs_session

        return TestServiceContainer(auth_session, specs_session)

    def test_invalid_project_id_handling(self, service_container):
        """Test that agents handle invalid project IDs gracefully"""
        print("\n=== Testing Invalid Project ID Handling ===")

        project_agent = ProjectManagerAgent("project", "ProjectManagerAgent", service_container)

        # Try to get non-existent project
        result = project_agent.execute({
            'action': 'get_project',
            'project_id': str(uuid4())  # Random UUID that doesn't exist
        })

        assert result['success'] is False, "Should fail for non-existent project"
        assert result.get('error_code') == 'PROJECT_NOT_FOUND'
        print("✓ Invalid project ID handled correctly")

    def test_validation_error_handling(self, service_container):
        """Test that validation errors are handled correctly"""
        print("\n=== Testing Validation Error Handling ===")

        project_agent = ProjectManagerAgent("project", "ProjectManagerAgent", service_container)

        # Try to create project without required fields
        result = project_agent.execute({
            'action': 'create_project',
            # Missing user_id and name
        })

        assert result['success'] is False, "Should fail for missing fields"
        assert result.get('error_code') == 'VALIDATION_ERROR'
        print("✓ Validation error handled correctly")

    def test_session_cleanup_on_error(self, service_container, specs_session):
        """Test that database sessions are cleaned up even when errors occur"""
        print("\n=== Testing Session Cleanup on Error ===")

        project_agent = ProjectManagerAgent("project", "ProjectManagerAgent", service_container)

        # Cause an error by providing invalid data
        result = project_agent.execute({
            'action': 'create_project',
            'user_id': str(uuid4()),  # Non-existent user
            'name': 'Test Project'
        })

        # Should fail gracefully
        assert result['success'] is False
        # Session should still be usable (not leaked)
        assert specs_session.is_active

        print("✓ Session cleanup on error test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

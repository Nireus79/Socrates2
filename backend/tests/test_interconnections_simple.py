"""
Simplified Integration Tests for Testing Interconnections

These tests verify that all components work together correctly
without requiring a full environment setup.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone


def test_import_all_models():
    """Test that all models can be imported successfully"""
    print("\n=== Testing Model Imports ===")

    try:
        from app.models.user import User
        from app.models.project import Project
        from app.models.session import Session
        from app.models.question import Question
        from app.models.specification import Specification
        from app.models.conflict import Conflict
        from app.models.generated_project import GeneratedProject
        from app.models.team import Team
        from app.models.team_member import TeamMember
        from app.models.api_key import APIKey
        from app.models.llm_usage_tracking import LLMUsageTracking
        print("✓ All models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Model import failed: {e}")
        return False


def test_import_all_agents():
    """Test that all agents can be imported successfully"""
    print("\n=== Testing Agent Imports ===")

    try:
        from app.agents.base import BaseAgent
        from app.agents.project import ProjectManagerAgent
        from app.agents.socratic import SocraticCounselorAgent
        from app.agents.context import ContextAnalyzerAgent
        from app.agents.conflict_detector import ConflictDetectorAgent
        from app.agents.code_generator import CodeGeneratorAgent
        from app.agents.quality_controller import QualityControllerAgent
        from app.agents.team_collaboration import TeamCollaborationAgent
        from app.agents.orchestrator import AgentOrchestrator
        print("✓ All agents imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Agent import failed: {e}")
        return False


def test_agent_capabilities():
    """Test that all agents expose their capabilities correctly"""
    print("\n=== Testing Agent Capabilities ===")

    from app.agents.project import ProjectManagerAgent
    from app.agents.socratic import SocraticCounselorAgent
    from app.agents.context import ContextAnalyzerAgent
    from app.agents.conflict_detector import ConflictDetectorAgent
    from app.agents.code_generator import CodeGeneratorAgent
    from app.agents.quality_controller import QualityControllerAgent
    from app.agents.team_collaboration import TeamCollaborationAgent

    # Create mock service container
    mock_services = Mock()

    agents = [
        ProjectManagerAgent("project", "ProjectManagerAgent", mock_services),
        SocraticCounselorAgent("socratic", "SocraticCounselorAgent", mock_services),
        ContextAnalyzerAgent("context", "ContextAnalyzerAgent", mock_services),
        ConflictDetectorAgent("conflict", "ConflictDetectorAgent", mock_services),
        CodeGeneratorAgent("code", "CodeGeneratorAgent", mock_services),
        QualityControllerAgent("quality", "QualityControllerAgent", mock_services),
        TeamCollaborationAgent("team", "TeamCollaborationAgent", mock_services)
    ]

    for agent in agents:
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list), f"{agent.__class__.__name__} capabilities must be a list"
        assert len(capabilities) > 0, f"{agent.__class__.__name__} must expose capabilities"
        print(f"✓ {agent.__class__.__name__}: {len(capabilities)} capabilities")

    print("✓ All agents expose capabilities correctly")
    return True


def test_agent_error_handling():
    """Test that agents handle errors gracefully with proper error codes"""
    print("\n=== Testing Agent Error Handling ===")

    from app.agents.project import ProjectManagerAgent

    # Create mock service container with mock database session
    mock_db = MagicMock()
    mock_services = Mock()
    mock_services.get_database_specs.return_value = mock_db
    mock_services.get_database_auth.return_value = mock_db

    agent = ProjectManagerAgent("project", "ProjectManagerAgent", mock_services)

    # Test validation error
    result = agent.execute({
        'action': 'create_project'
        # Missing required fields
    })

    assert result['success'] is False, "Should return success=False for validation errors"
    assert 'error' in result, "Should return error message"
    assert 'error_code' in result, "Should return error_code"
    assert result['error_code'] == 'VALIDATION_ERROR', "Should return VALIDATION_ERROR code"
    print("✓ Validation error handling works correctly")

    # Test invalid action
    result = agent.execute({
        'action': 'invalid_action'
    })

    assert result['success'] is False, "Should return success=False for invalid actions"
    print("✓ Invalid action handling works correctly")

    return True


def test_orchestrator_agent_registration():
    """Test that orchestrator can register and retrieve agents"""
    print("\n=== Testing Orchestrator Agent Registration ===")

    from app.agents.orchestrator import AgentOrchestrator
    from app.agents.project import ProjectManagerAgent

    # Create mock service container
    mock_services = Mock()

    orchestrator = AgentOrchestrator(mock_services)

    # Verify agents are registered
    registered_agents = list(orchestrator.agents.keys())
    print(f"  Registered agents: {registered_agents}")

    assert 'project' in registered_agents, "ProjectManagerAgent should be registered"
    assert 'socratic' in registered_agents, "SocraticCounselorAgent should be registered"
    assert 'context' in registered_agents, "ContextAnalyzerAgent should be registered"
    assert 'conflict' in registered_agents, "ConflictDetectorAgent should be registered"
    assert 'code' in registered_agents, "CodeGeneratorAgent should be registered"
    assert 'quality' in registered_agents, "QualityControllerAgent should be registered"
    assert 'team' in registered_agents, "TeamCollaborationAgent should be registered"

    print(f"✓ All {len(registered_agents)} agents registered in orchestrator")
    return True


def test_database_session_cleanup():
    """Test that database sessions are properly cleaned up in finally blocks"""
    print("\n=== Testing Database Session Cleanup ===")

    from app.agents.project import ProjectManagerAgent

    # Create mock database session
    mock_db = MagicMock()
    mock_db.close = Mock()
    mock_db.rollback = Mock()

    mock_services = Mock()
    mock_services.get_database_specs.return_value = mock_db
    mock_services.get_database_auth.return_value = mock_db

    agent = ProjectManagerAgent("project", "ProjectManagerAgent", mock_services)

    # Trigger an error by providing invalid data
    result = agent.execute({
        'action': 'get_project',
        'project_id': str(uuid4())  # Non-existent project
    })

    # Session.close() should have been called even though there was an error
    assert mock_db.close.called, "Database session should be closed in finally block"
    print("✓ Database session cleanup verified")

    return True


def test_error_logging():
    """Test that errors are logged with proper information"""
    print("\n=== Testing Error Logging ===")

    from app.agents.project import ProjectManagerAgent

    mock_db = MagicMock()
    mock_services = Mock()
    mock_services.get_database_specs.return_value = mock_db
    mock_services.get_database_auth.return_value = mock_db

    agent = ProjectManagerAgent("project", "ProjectManagerAgent", mock_services)

    # Agent should have a logger
    assert hasattr(agent, 'logger'), "Agent should have a logger"

    # Trigger a warning (validation error)
    with patch.object(agent.logger, 'warning') as mock_warning:
        result = agent.execute({
            'action': 'create_project'
            # Missing required fields
        })

        # Logger warning should have been called
        assert mock_warning.called, "Logger.warning should be called for validation errors"
        print("✓ Validation errors are logged with logger.warning()")

    # Trigger an error (database operation)
    mock_db.query.side_effect = Exception("Database error")

    with patch.object(agent.logger, 'error') as mock_error:
        result = agent.execute({
            'action': 'get_project',
            'project_id': str(uuid4())
        })

        # Logger error should have been called
        assert mock_error.called, "Logger.error should be called for database errors"
        # Check if exc_info=True was used (for stack traces)
        call_kwargs = mock_error.call_args[1] if mock_error.call_args else {}
        assert call_kwargs.get('exc_info') is True, "Logger.error should be called with exc_info=True"
        print("✓ Database errors are logged with logger.error() and stack traces")

    return True


def test_all_interconnections():
    """Run all interconnection tests"""
    print("\n" + "="*60)
    print("COMPREHENSIVE INTERCONNECTION TESTS")
    print("="*60)

    tests = [
        ("Model Imports", test_import_all_models),
        ("Agent Imports", test_import_all_agents),
        ("Agent Capabilities", test_agent_capabilities),
        ("Error Handling", test_agent_error_handling),
        ("Orchestrator Registration", test_orchestrator_agent_registration),
        ("Session Cleanup", test_database_session_cleanup),
        ("Error Logging", test_error_logging),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = test_all_interconnections()
    sys.exit(0 if success else 1)

"""
Phase 7 Tests: Direct Chat Mode

Tests for DirectChatAgent functionality including:
- Mode toggling between Socratic and Direct Chat
- Processing chat messages with context awareness
- Conversation history maintenance
- Specification extraction from natural conversation
- Conflict detection in direct chat mode
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.models import (
    User, Project, Session, ConversationHistory,
    Specification, Conflict
)
from app.agents.direct_chat import DirectChatAgent
from app.agents.orchestrator import AgentOrchestrator


def create_session(session_id, project_id, mode="socratic", status="active"):
    """Helper to create a session with required fields"""
    return Session(
        id=session_id,
        project_id=project_id,
        mode=mode,
        status=status,
        started_at=datetime.now(timezone.utc)
    )


class TestDirectChatAgentInitialization:
    """Test DirectChatAgent creation and capabilities"""

    def test_direct_chat_agent_initialization(self, service_container):
        """Test that DirectChatAgent initializes correctly"""
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        assert agent.agent_id == "direct_chat"
        assert agent.name == "Direct Chat"
        assert agent.services is not None

    def test_direct_chat_agent_capabilities(self, service_container):
        """Test that agent has correct capabilities"""
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        capabilities = agent.get_capabilities()

        expected_capabilities = [
            'process_chat_message',
            'toggle_mode',
            'get_mode',
            'maintain_context'
        ]

        for cap in expected_capabilities:
            assert cap in capabilities


class TestSessionModeToggling:
    """Test toggling between Socratic and Direct Chat modes"""

    def test_toggle_from_socratic_to_direct_chat(
        self, specs_session, service_container, test_user
    ):
        """Test toggling from Socratic to Direct Chat mode"""
        # Create a project and session
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="socratic")
        specs_session.add(session)
        specs_session.commit()

        # Toggle mode
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('toggle_mode', {
            'session_id': session.id,
            'mode': 'direct_chat'
        })

        assert result['success'] is True
        assert result['old_mode'] == 'socratic'
        assert result['new_mode'] == 'direct_chat'

        # Verify database updated
        specs_session.refresh(session)
        assert session.mode == 'direct_chat'

    def test_toggle_from_direct_chat_to_socratic(
        self, specs_session, service_container, test_user
    ):
        """Test toggling from Direct Chat back to Socratic mode"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="direct_chat")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('toggle_mode', {
            'session_id': session.id,
            'mode': 'socratic'
        })

        assert result['success'] is True
        assert result['old_mode'] == 'direct_chat'
        assert result['new_mode'] == 'socratic'

    def test_toggle_invalid_mode(
        self, specs_session, service_container, test_user
    ):
        """Test that invalid mode raises error"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="socratic")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('toggle_mode', {
            'session_id': session.id,
            'mode': 'invalid_mode'
        })

        assert result['success'] is False
        assert 'error' in result

    def test_toggle_nonexistent_session(self, service_container):
        """Test toggling mode for non-existent session"""
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('toggle_mode', {
            'session_id': uuid4(),
            'mode': 'direct_chat'
        })

        assert result['success'] is False
        assert 'error' in result


class TestGetSessionMode:
    """Test retrieving current session mode"""

    def test_get_socratic_mode(
        self, specs_session, service_container, test_user
    ):
        """Test getting mode when in Socratic"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="socratic")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('get_mode', {
            'session_id': session.id
        })

        assert result['success'] is True
        assert result['mode'] == 'socratic'
        assert result['session_id'] == str(session.id)
        assert result['project_id'] == str(project.id)

    def test_get_direct_chat_mode(
        self, specs_session, service_container, test_user
    ):
        """Test getting mode when in Direct Chat"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="direct_chat")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('get_mode', {
            'session_id': session.id
        })

        assert result['success'] is True
        assert result['mode'] == 'direct_chat'

    def test_get_mode_nonexistent_session(self, service_container):
        """Test getting mode for non-existent session"""
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('get_mode', {
            'session_id': uuid4()
        })

        assert result['success'] is False
        assert 'error' in result


class TestProcessChatMessage:
    """Test processing direct chat messages"""

    def test_process_chat_message_success(
        self, specs_session, service_container, test_user, mock_claude_client
    ):
        """Test processing a direct chat message"""
        # Setup
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="direct_chat")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)

        result = agent.process_request('process_chat_message', {
            'session_id': session.id,
            'user_id': test_user.id,
            'message': 'I want to build a REST API',
            'project_id': project.id
        })

        assert result['success'] is True
        assert 'response' in result
        assert isinstance(result['response'], str)
        assert len(result['response']) > 0
        assert 'specs_extracted' in result
        assert 'conflicts_detected' in result
        assert 'maturity_score' in result

    def test_process_chat_message_wrong_mode(
        self, specs_session, service_container, test_user
    ):
        """Test that processing message fails when in Socratic mode"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="socratic")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)

        result = agent.process_request('process_chat_message', {
            'session_id': session.id,
            'user_id': test_user.id,
            'message': 'Test message',
            'project_id': project.id
        })

        assert result['success'] is False
        assert 'error' in result

    def test_process_chat_message_nonexistent_session(
        self, service_container, test_user
    ):
        """Test processing message for non-existent session"""
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)

        result = agent.process_request('process_chat_message', {
            'session_id': uuid4(),
            'user_id': test_user.id,
            'message': 'Test',
            'project_id': uuid4()
        })

        assert result['success'] is False
        assert 'error' in result


class TestConversationHistory:
    """Test conversation history maintenance"""

    def test_conversation_saved_after_message(
        self, specs_session, service_container, test_user, mock_claude_client
    ):
        """Test that conversation is saved to database"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="direct_chat")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        user_message = "I want to build a web app"

        result = agent.process_request('process_chat_message', {
            'session_id': session.id,
            'user_id': test_user.id,
            'message': user_message,
            'project_id': project.id
        })

        assert result['success'] is True

        # Verify conversation history was saved
        history = specs_session.query(ConversationHistory).filter_by(
            session_id=session.id
        ).all()

        # Should have both user message and assistant response
        assert len(history) == 2
        assert history[0].role == 'user'
        assert history[0].content == user_message
        assert history[1].role == 'assistant'
        assert len(history[1].content) > 0

    def test_conversation_context_loaded(
        self, specs_session, service_container, test_user, mock_claude_client
    ):
        """Test that conversation context is loaded for subsequent messages"""
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="direct_chat")
        specs_session.add(session)
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)

        # Send first message
        agent.process_request('process_chat_message', {
            'session_id': session.id,
            'user_id': test_user.id,
            'message': 'First message',
            'project_id': project.id
        })

        # Send second message
        result = agent.process_request('process_chat_message', {
            'session_id': session.id,
            'user_id': test_user.id,
            'message': 'Second message',
            'project_id': project.id
        })

        assert result['success'] is True

        # Should have 4 total messages (2 user, 2 assistant)
        history = specs_session.query(ConversationHistory).filter_by(
            session_id=session.id
        ).all()
        assert len(history) == 4

    def test_maintain_context_action(
        self, specs_session, service_container, test_user
    ):
        """Test the maintain_context action"""
        # Create project first
        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="direct_chat")
        specs_session.add(session)
        specs_session.commit()

        # Add some conversation history
        msg1 = ConversationHistory(
            session_id=session.id,
            role='user',
            content='First message',
            timestamp=datetime.now(timezone.utc)
        )
        msg2 = ConversationHistory(
            session_id=session.id,
            role='assistant',
            content='Response to first',
            timestamp=datetime.now(timezone.utc)
        )
        specs_session.add_all([msg1, msg2])
        specs_session.commit()

        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        result = agent.process_request('maintain_context', {
            'session_id': session.id
        })

        assert result['success'] is True
        assert 'recent_messages' in result
        assert 'message_count' in result
        assert result['message_count'] == 2
        assert len(result['recent_messages']) == 2


class TestIntegrationWithOrchestrator:
    """Test DirectChatAgent integration with AgentOrchestrator"""

    def test_direct_chat_agent_registered_in_orchestrator(
        self, service_container
    ):
        """Test that DirectChatAgent can be registered with orchestrator"""
        orchestrator = AgentOrchestrator(service_container)
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)

        orchestrator.register_agent(agent)

        assert 'direct_chat' in orchestrator.agents
        assert orchestrator.agents['direct_chat'] == agent

    def test_route_toggle_mode_through_orchestrator(
        self, specs_session, service_container, test_user
    ):
        """Test routing toggle_mode through orchestrator"""
        orchestrator = AgentOrchestrator(service_container)
        agent = DirectChatAgent("direct_chat", "Direct Chat", service_container)
        orchestrator.register_agent(agent)

        project = Project(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Project",
            description="Test",
            current_phase="DISCOVERY",
            status="active",
            maturity_score=0
        )
        specs_session.add(project)
        specs_session.commit()

        session = create_session(uuid4(), project.id, mode="socratic")
        specs_session.add(session)
        specs_session.commit()

        result = orchestrator.route_request('direct_chat', 'toggle_mode', {
            'session_id': session.id,
            'mode': 'direct_chat'
        })

        assert result['success'] is True
        assert result['new_mode'] == 'direct_chat'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

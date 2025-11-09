#!/usr/bin/env python3
"""
Tests for Conversational CLI system.

Tests the natural language understanding, intent parsing, and command execution.
"""

import json
import pytest
from unittest.mock import Mock, patch
from implementation_documents.conversational_cli import ConversationalCLI, MenuContext


class TestConversationalCLI:
    """Test suite for ConversationalCLI"""

    @pytest.fixture
    def cli(self):
        """Create a ConversationalCLI instance for testing"""
        with patch('conversational_cli.Anthropic'):
            cli = ConversationalCLI()
            return cli

    # ===== Test Initialization =====
    def test_initialization(self, cli):
        """Test CLI initializes with correct defaults"""
        assert cli.current_user is None
        assert cli.current_project is None
        assert cli.current_session is None
        assert cli.auth_token is None
        assert len(cli.menu_stack) == 0

    def test_model_selection_available(self, cli):
        """Test that all models are available"""
        assert '1' in cli.AVAILABLE_MODELS
        assert '2' in cli.AVAILABLE_MODELS
        assert '3' in cli.AVAILABLE_MODELS

    def test_operations_defined(self, cli):
        """Test that all operations are defined"""
        expected_ops = [
            'register_user', 'login_user', 'logout_user',
            'create_project', 'list_projects', 'start_session',
            'ask_question', 'resolve_conflict', 'view_insights',
            'export_project'
        ]
        for op in expected_ops:
            assert op in cli.AVAILABLE_OPERATIONS

    # ===== Test Menu Management =====
    def test_push_menu(self, cli):
        """Test pushing a menu onto the stack"""
        cli._push_menu("test_menu")
        assert len(cli.menu_stack) == 1
        assert cli.menu_stack[0].name == "test_menu"

    def test_pop_menu(self, cli):
        """Test popping a menu from the stack"""
        cli._push_menu("test_menu")
        cli._pop_menu()
        assert len(cli.menu_stack) == 0

    def test_pop_menu_empty_stack(self, cli):
        """Test popping from empty stack doesn't crash"""
        cli._pop_menu()  # Should not raise
        assert len(cli.menu_stack) == 0

    def test_menu_exit_handler_called(self, cli):
        """Test that exit handler is called when popping menu"""
        exit_handler = Mock()
        cli._push_menu("test_menu", exit_handler)
        cli._pop_menu()
        exit_handler.assert_called_once()

    # ===== Test User Operations =====
    def test_register_user(self, cli):
        """Test user registration"""
        result = cli._mock_register_user({
            'name': 'John Doe',
            'email': 'john@example.com'
        })

        assert result['success'] is True
        assert cli.current_user is not None
        assert cli.current_user['email'] == 'john@example.com'

    def test_register_user_missing_email(self, cli):
        """Test registration fails without email"""
        result = cli._mock_register_user({'name': 'John'})
        assert result['success'] is False
        assert 'Email' in result['error']

    def test_login_user(self, cli):
        """Test user login"""
        result = cli._mock_login_user({'email': 'john@example.com'})

        assert result['success'] is True
        assert cli.current_user is not None
        assert cli.auth_token is not None

    def test_logout_user(self, cli):
        """Test user logout"""
        # First login
        cli._mock_login_user({'email': 'john@example.com'})
        assert cli.current_user is not None

        # Then logout
        result = cli._mock_logout_user()

        assert result['success'] is True
        assert cli.current_user is None
        assert cli.auth_token is None

    def test_logout_when_not_logged_in(self, cli):
        """Test logout fails when not logged in"""
        result = cli._mock_logout_user()
        assert result['success'] is False

    # ===== Test Project Operations =====
    def test_create_project(self, cli):
        """Test project creation"""
        # Must be logged in
        cli._mock_login_user({'email': 'john@example.com'})

        result = cli._mock_create_project({
            'name': 'Mobile App',
            'description': 'A mobile application'
        })

        assert result['success'] is True
        assert cli.current_project is not None
        assert cli.current_project['name'] == 'Mobile App'

    def test_create_project_not_logged_in(self, cli):
        """Test project creation fails when not logged in"""
        result = cli._mock_create_project({
            'name': 'Mobile App',
            'description': 'A mobile application'
        })

        assert result['success'] is False
        assert 'logged in' in result['error'].lower()

    def test_list_projects(self, cli):
        """Test listing projects"""
        # Must be logged in
        cli._mock_login_user({'email': 'john@example.com'})

        result = cli._mock_list_projects()

        assert result['success'] is True
        assert 'projects' in result['message'].lower()

    def test_list_projects_not_logged_in(self, cli):
        """Test listing projects fails when not logged in"""
        result = cli._mock_list_projects()
        assert result['success'] is False

    # ===== Test Session Operations =====
    def test_start_session(self, cli):
        """Test starting a session"""
        # Must be logged in
        cli._mock_login_user({'email': 'john@example.com'})

        result = cli._mock_start_session({})

        assert result['success'] is True
        assert cli.current_session is not None

    def test_start_session_not_logged_in(self, cli):
        """Test session start fails when not logged in"""
        result = cli._mock_start_session({})
        assert result['success'] is False

    def test_ask_question(self, cli):
        """Test asking a question"""
        result = cli._mock_ask_question({
            'question': 'What is the target audience?'
        })

        assert result['success'] is True
        assert 'recorded' in result['message'].lower()

    def test_ask_question_missing_question(self, cli):
        """Test asking question fails without question text"""
        result = cli._mock_ask_question({})
        assert result['success'] is False

    # ===== Test Intent Parsing =====
    @patch('conversational_cli.Anthropic')
    def test_intent_parsing_operation(self, mock_anthropic_class, cli):
        """Test parsing natural language to operation intent"""
        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "is_operation": True,
            "operation": "register_user",
            "params": {"name": "John", "email": "john@x.com", "password": "pass123"},
            "explanation": "Creating new user"
        }))]

        cli.client.messages.create = Mock(return_value=mock_response)

        intent = cli._get_intent_from_claude("Register a user named John")

        assert intent is not None
        assert intent['operation'] == 'register_user'
        assert 'name' in intent['params']

    @patch('conversational_cli.Anthropic')
    def test_intent_parsing_conversation(self, mock_anthropic_class, cli):
        """Test parsing conversational input"""
        # Mock Claude response for conversation
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "is_operation": False,
            "response": "That sounds like a great project!"
        }))]

        cli.client.messages.create = Mock(return_value=mock_response)

        intent = cli._get_intent_from_claude("Tell me about specifications")

        assert intent is None  # Conversation, not operation

    # ===== Test Execute Intent =====
    def test_execute_register_intent(self, cli):
        """Test executing registration intent"""
        intent = {
            'operation': 'register_user',
            'params': {'name': 'John', 'email': 'john@x.com', 'password': 'pass123'}
        }

        result = cli._execute_intent(intent)

        assert result['success'] is True
        assert cli.current_user is not None

    def test_execute_login_intent(self, cli):
        """Test executing login intent"""
        intent = {
            'operation': 'login_user',
            'params': {'email': 'john@x.com', 'password': 'pass123'}
        }

        result = cli._execute_intent(intent)

        assert result['success'] is True
        assert cli.current_user is not None

    def test_execute_create_project_intent(self, cli):
        """Test executing create project intent"""
        # Must be logged in first
        cli._mock_login_user({'email': 'john@x.com'})

        intent = {
            'operation': 'create_project',
            'params': {'name': 'App', 'description': 'An app'}
        }

        result = cli._execute_intent(intent)

        assert result['success'] is True
        assert cli.current_project is not None

    def test_execute_unknown_intent(self, cli):
        """Test executing unknown operation fails gracefully"""
        intent = {
            'operation': 'unknown_operation',
            'params': {}
        }

        result = cli._execute_intent(intent)

        assert result['success'] is False
        assert 'unknown' in result['error'].lower()

    # ===== Test Model Selection =====
    def test_available_models(self, cli):
        """Test that all models are properly configured"""
        for key, model_info in cli.AVAILABLE_MODELS.items():
            assert 'name' in model_info
            assert 'display' in model_info
            assert model_info['name'] is not None

    def test_model_defaults_to_sonnet(self, cli):
        """Test that Sonnet is the default model"""
        assert 'sonnet' in cli.current_model.lower()

    # ===== Test Conversation History =====
    def test_conversation_history_tracking(self, cli):
        """Test that conversation history is tracked"""
        cli.conversation_history.append({"role": "user", "content": "Hello"})
        cli.conversation_history.append({"role": "assistant", "content": "Hi!"})

        assert len(cli.conversation_history) == 2
        assert cli.conversation_history[0]['role'] == 'user'
        assert cli.conversation_history[1]['role'] == 'assistant'

    # ===== Test Workflow Integration =====
    def test_full_workflow(self, cli):
        """Test a complete user workflow"""
        # Register
        reg_result = cli._mock_register_user({
            'name': 'John',
            'email': 'john@x.com'
        })
        assert reg_result['success']

        # Login
        login_result = cli._mock_login_user({'email': 'john@x.com'})
        assert login_result['success']

        # Create project
        proj_result = cli._mock_create_project({
            'name': 'App',
            'description': 'My app'
        })
        assert proj_result['success']

        # Start session
        session_result = cli._mock_start_session({})
        assert session_result['success']

        # Ask question
        question_result = cli._mock_ask_question({
            'question': 'What is the target audience?'
        })
        assert question_result['success']

        # Verify final state
        assert cli.current_user is not None
        assert cli.current_project is not None
        assert cli.current_session is not None


class TestMenuContext:
    """Test MenuContext class"""

    def test_menu_context_creation(self):
        """Test creating a menu context"""
        context = MenuContext("test_menu")
        assert context.name == "test_menu"
        assert context.exit_handler is None

    def test_menu_context_with_handler(self):
        """Test menu context with exit handler"""
        handler = Mock()
        context = MenuContext("test_menu", handler)
        assert context.exit_handler is handler


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

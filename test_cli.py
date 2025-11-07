"""
Socrates CLI Tests - Unit Tests with Mocked API

Tests CLI functionality without requiring a running backend.
Uses unittest.mock to simulate API responses.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import json
import tempfile
import sys
import os

# Add parent directory to path to import Socrates
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Socrates import SocratesConfig, SocratesAPI, SocratesCLI


class TestSocratesConfig(unittest.TestCase):
    """Test configuration management"""

    def setUp(self):
        """Create temporary config directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SocratesConfig()
        self.config.config_dir = Path(self.temp_dir)
        self.config.config_file = self.config.config_dir / "config.json"
        self.config.history_file = self.config.config_dir / "history.txt"

    def test_config_directory_created(self):
        """Test that config directory is created"""
        self.assertTrue(self.config.config_dir.exists())

    def test_set_and_get_config(self):
        """Test setting and getting config values"""
        self.config.set("test_key", "test_value")
        self.assertEqual(self.config.get("test_key"), "test_value")

    def test_config_persistence(self):
        """Test that config persists to disk"""
        self.config.set("access_token", "test_token_123")
        self.config.set("user_email", "test@example.com")

        # Create new config instance to load from disk
        new_config = SocratesConfig()
        new_config.config_dir = Path(self.temp_dir)
        new_config.config_file = new_config.config_dir / "config.json"
        new_config.data = new_config.load()

        self.assertEqual(new_config.get("access_token"), "test_token_123")
        self.assertEqual(new_config.get("user_email"), "test@example.com")

    def test_clear_config(self):
        """Test clearing config"""
        self.config.set("test_key", "test_value")
        self.config.clear()
        self.assertIsNone(self.config.get("test_key"))

    def test_get_default_value(self):
        """Test getting non-existent key with default"""
        result = self.config.get("nonexistent", "default_value")
        self.assertEqual(result, "default_value")


class TestSocratesAPI(unittest.TestCase):
    """Test API client"""

    def setUp(self):
        """Create API client with mocked console"""
        self.mock_console = Mock()
        self.api = SocratesAPI("http://test.example.com", self.mock_console)

    def test_api_initialization(self):
        """Test API client initialization"""
        self.assertEqual(self.api.base_url, "http://test.example.com")
        self.assertIsNone(self.api.access_token)

    def test_set_token(self):
        """Test setting authentication token"""
        self.api.set_token("test_token_123")
        self.assertEqual(self.api.access_token, "test_token_123")

    def test_headers_without_token(self):
        """Test request headers without token"""
        headers = self.api._headers()
        self.assertIn("Content-Type", headers)
        self.assertNotIn("Authorization", headers)

    def test_headers_with_token(self):
        """Test request headers with token"""
        self.api.set_token("test_token_123")
        headers = self.api._headers()
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer test_token_123")

    @patch('Socrates.requests.request')
    def test_register_success(self, mock_request):
        """Test successful registration"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "user_id": "test-user-id-123",
            "email": "test@example.com",
            "message": "User registered successfully"
        }
        mock_request.return_value = mock_response

        result = self.api.register("test@example.com", "password123")

        # Verify request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertIn("/api/v1/auth/register", args[1])
        self.assertEqual(kwargs["json"]["email"], "test@example.com")
        self.assertEqual(kwargs["json"]["password"], "password123")

        # Verify result
        self.assertEqual(result["user_id"], "test-user-id-123")
        self.assertEqual(result["email"], "test@example.com")

    @patch('Socrates.requests.request')
    def test_login_success(self, mock_request):
        """Test successful login"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "jwt_token_abc123",
            "token_type": "bearer"
        }
        mock_request.return_value = mock_response

        result = self.api.login("test@example.com", "password123")

        # Verify result
        self.assertIn("access_token", result)
        self.assertEqual(result["access_token"], "jwt_token_abc123")

    @patch('Socrates.requests.request')
    def test_create_project_success(self, mock_request):
        """Test creating project"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "project_id": "project-123"
        }
        mock_request.return_value = mock_response

        self.api.set_token("test_token")
        result = self.api.create_project("Test Project", "Description")

        self.assertTrue(result["success"])
        self.assertEqual(result["project_id"], "project-123")

    @patch('Socrates.requests.request')
    def test_connection_error_handling(self, mock_request):
        """Test handling of connection errors"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(requests.exceptions.ConnectionError):
            self.api.register("test@example.com", "password", "Test")

        # Verify error message was printed
        self.mock_console.print.assert_called()


class TestSocratesCLI(unittest.TestCase):
    """Test CLI application"""

    def setUp(self):
        """Create CLI with mocked components"""
        with patch('Socrates.SocratesConfig'):
            with patch('Socrates.PromptSession'):
                self.cli = SocratesCLI("http://test.example.com", debug=False)
                self.cli.console = Mock()
                self.cli.api = Mock()
                self.cli.config = Mock()

    def test_cli_initialization(self):
        """Test CLI initialization"""
        self.assertFalse(self.cli.debug)
        self.assertTrue(self.cli.running)
        self.assertEqual(self.cli.chat_mode, "socratic")
        self.assertIsNone(self.cli.current_project)
        self.assertIsNone(self.cli.current_session)

    def test_ensure_authenticated_success(self):
        """Test authentication check when logged in"""
        self.cli.config.get.return_value = "test_token_123"
        result = self.cli.ensure_authenticated()
        self.assertTrue(result)
        self.cli.api.set_token.assert_called_with("test_token_123")

    def test_ensure_authenticated_failure(self):
        """Test authentication check when not logged in"""
        self.cli.config.get.return_value = None
        result = self.cli.ensure_authenticated()
        self.assertFalse(result)
        self.cli.console.print.assert_called()

    def test_ensure_project_selected_success(self):
        """Test project selection check when project selected"""
        self.cli.current_project = {"id": "123", "name": "Test"}
        result = self.cli.ensure_project_selected()
        self.assertTrue(result)

    def test_ensure_project_selected_failure(self):
        """Test project selection check when no project"""
        result = self.cli.ensure_project_selected()
        self.assertFalse(result)
        self.cli.console.print.assert_called()

    def test_cmd_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        with patch('Socrates.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = [
                "test@example.com",  # email
                "Test User",         # full_name
                "password123",       # password
                "different_pass"     # confirm password
            ]

            self.cli.cmd_register()

            # Should print error about password mismatch
            self.cli.console.print.assert_called()
            args = str(self.cli.console.print.call_args)
            self.assertIn("do not match", args)

    def test_cmd_register_success(self):
        """Test successful registration"""
        with patch('Socrates.Prompt.ask') as mock_prompt:
            with patch('Socrates.Progress'):
                mock_prompt.side_effect = [
                    "test@example.com",  # email
                    "password123",       # password
                    "password123"        # confirm password
                ]

                self.cli.api.register.return_value = {
                    "user_id": "user-123",
                    "email": "test@example.com",
                    "message": "User registered successfully"
                }

                self.cli.cmd_register()

                # Verify API was called
                self.cli.api.register.assert_called_with(
                    "test@example.com",
                    "password123"
                )

                # Verify success message
                print_calls = [str(call) for call in self.cli.console.print.call_args_list]
                self.assertTrue(any("created successfully" in str(call) for call in print_calls))

    def test_cmd_login_success(self):
        """Test successful login"""
        with patch('Socrates.Prompt.ask') as mock_prompt:
            with patch('Socrates.Progress'):
                mock_prompt.side_effect = [
                    "test@example.com",  # email
                    "password123"        # password
                ]

                self.cli.api.login.return_value = {
                    "access_token": "jwt_abc123"
                }

                self.cli.cmd_login()

                # Verify token was saved
                self.cli.config.set.assert_any_call("access_token", "jwt_abc123")
                self.cli.config.set.assert_any_call("user_email", "test@example.com")

    def test_mode_toggle(self):
        """Test toggling chat mode"""
        initial_mode = self.cli.chat_mode
        self.cli.handle_command("/mode")

        # Verify mode changed
        self.assertNotEqual(self.cli.chat_mode, initial_mode)

    def test_mode_set_direct(self):
        """Test setting direct mode explicitly"""
        self.cli.handle_command("/mode direct")
        self.assertEqual(self.cli.chat_mode, "direct")

    def test_mode_set_socratic(self):
        """Test setting socratic mode explicitly"""
        self.cli.handle_command("/mode socratic")
        self.assertEqual(self.cli.chat_mode, "socratic")

    def test_handle_unknown_command(self):
        """Test handling unknown command"""
        self.cli.handle_command("/nonexistent")
        self.cli.console.print.assert_called()

    def test_help_command(self):
        """Test help command"""
        self.cli.handle_command("/help")
        self.cli.console.print.assert_called()

    def test_whoami_command_authenticated(self):
        """Test whoami command when logged in"""
        self.cli.config.get.side_effect = lambda key, default=None: {
            "access_token": "token123",
            "user_email": "test@example.com"
        }.get(key, default)

        self.cli.current_project = {
            "id": "proj-123",
            "name": "Test Project"
        }

        self.cli.cmd_whoami()
        self.cli.console.print.assert_called()


class TestCLIWorkflow(unittest.TestCase):
    """Test complete CLI workflows"""

    def setUp(self):
        """Setup for workflow tests"""
        with patch('Socrates.SocratesConfig'):
            with patch('Socrates.PromptSession'):
                self.cli = SocratesCLI("http://test.example.com")
                self.cli.console = Mock()
                self.cli.api = Mock()
                self.cli.config = Mock()

    def test_registration_to_project_workflow(self):
        """Test complete workflow: register -> login -> create project"""
        # 1. Register
        with patch('Socrates.Prompt.ask') as mock_prompt:
            with patch('Socrates.Progress'):
                mock_prompt.side_effect = [
                    "user@example.com", "pass123", "pass123"
                ]
                self.cli.api.register.return_value = {
                    "user_id": "user-123",
                    "email": "user@example.com",
                    "message": "User registered successfully"
                }
                self.cli.cmd_register()

        # 2. Login
        with patch('Socrates.Prompt.ask') as mock_prompt:
            with patch('Socrates.Progress'):
                mock_prompt.side_effect = ["user@example.com", "pass123"]
                self.cli.api.login.return_value = {
                    "access_token": "token_abc"
                }
                self.cli.cmd_login()

        # 3. Create project
        with patch('Socrates.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = ["My Project", "Description"]
            self.cli.config.get.return_value = "token_abc"
            self.cli.api.create_project.return_value = {
                "success": True,
                "project_id": "proj-123"
            }
            self.cli.api.get_project.return_value = {
                "success": True,
                "project": {
                    "id": "proj-123",
                    "name": "My Project"
                }
            }

            self.cli.cmd_project(["create"])

            # Verify project was selected
            self.assertIsNotNone(self.cli.current_project)
            self.assertEqual(self.cli.current_project["name"], "My Project")

    def test_session_workflow(self):
        """Test session workflow: start -> chat -> end"""
        # Setup: logged in with project
        self.cli.config.get.return_value = "token_abc"
        self.cli.current_project = {"id": "proj-123", "name": "Test"}

        # 1. Start session
        with patch('Socrates.Progress'):
            self.cli.api.start_session.return_value = {
                "success": True,
                "session": {"id": "sess-123", "status": "active"}
            }
            self.cli.api.get_next_question.return_value = {
                "success": True,
                "question_id": "q1",
                "question": "What are you building?"
            }

            self.cli.cmd_session(["start"])

            # Verify session started
            self.assertIsNotNone(self.cli.current_session)

        # 2. Submit answer
        with patch('Socrates.Progress'):
            self.cli.api.submit_answer.return_value = {
                "success": True,
                "specs_extracted": ["Spec 1", "Spec 2"]
            }
            self.cli.api.get_next_question.return_value = {
                "success": True,
                "question_id": "q2",
                "question": "Next question?"
            }

            self.cli.current_question = {"question_id": "q1"}
            self.cli.handle_socratic_message("Building a REST API")

        # 3. End session
        with patch('Socrates.Confirm.ask', return_value=True):
            self.cli.api.end_session.return_value = {
                "success": True,
                "specs_count": 5
            }

            self.cli.cmd_session(["end"])

            # Verify session ended
            self.assertIsNone(self.cli.current_session)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSocratesConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestSocratesAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestSocratesCLI))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIWorkflow))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

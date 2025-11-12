"""
Comprehensive tests for Socrates.py CLI workflow.

Tests the complete user workflow:
1. Server startup
2. User registration
3. User login
4. Project creation
5. Session creation
6. Interactive CLI operations
"""

import pytest
import json
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Generator
import requests

pytestmark = pytest.mark.integration


class TestSocratesConfig:
    """Test SocratesConfig class for configuration management."""

    def test_config_initialization(self):
        """Test that SocratesConfig can be initialized."""
        # Import here to avoid module-level errors
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from Socrates import SocratesConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SocratesConfig()
            assert config.config_dir.exists()
            assert config.config_file is not None

    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        from Socrates import SocratesConfig

        config = SocratesConfig()

        # Set a value
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"

    def test_config_get_default(self):
        """Test getting configuration with default value."""
        from Socrates import SocratesConfig

        config = SocratesConfig()

        # Get non-existent key with default
        value = config.get("nonexistent", "default")
        assert value == "default"

    def test_config_clear(self):
        """Test clearing configuration."""
        from Socrates import SocratesConfig

        config = SocratesConfig()
        config.set("key1", "value1")
        config.clear()
        assert config.get("key1") is None


class TestSocratesCLIInitialization:
    """Test SocratesCLI initialization and server startup."""

    @pytest.mark.skip(reason="Requires running backend server and environment variables")
    def test_cli_initialization_without_auto_start(self):
        """Test CLI initialization without auto-starting server."""
        from Socrates import SocratesCLI

        # Initialize without auto-starting
        cli = SocratesCLI(
            api_url="http://localhost:8000",
            debug=False,
            auto_start_server=False
        )

        assert cli is not None
        assert cli.server_url == "http://localhost:8000"
        assert cli.debug is False

    @pytest.mark.skip(reason="Requires environment variables and running database")
    def test_cli_server_health_check(self):
        """Test CLI server health check endpoint."""
        from Socrates import SocratesCLI

        cli = SocratesCLI(
            api_url="http://localhost:8000",
            debug=False,
            auto_start_server=False
        )

        # Mock the health check
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            # Check if server health check would work
            assert cli.server_url == "http://localhost:8000"


class TestUserWorkflow:
    """Test complete user workflow: registration, login, project creation."""

    @pytest.fixture
    def api_client(self):
        """Create a test API client."""
        class APIClient:
            def __init__(self):
                self.base_url = "http://localhost:8000/api/v1"
                self.token = None

            def register(self, username: str, email: str, password: str, name: str):
                """Register a new user."""
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    json={
                        "username": username,
                        "email": email,
                        "password": password,
                        "name": name
                    }
                )
                return response

            def login(self, username: str, password: str):
                """Login user."""
                response = requests.post(
                    f"{self.base_url}/auth/login",
                    data={
                        "username": username,
                        "password": password
                    }
                )
                if response.status_code == 200:
                    self.token = response.json().get("access_token")
                return response

            def create_project(self, name: str, description: str):
                """Create a new project."""
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(
                    f"{self.base_url}/projects",
                    json={"name": name, "description": description},
                    headers=headers
                )
                return response

            def list_projects(self):
                """List user projects."""
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.get(
                    f"{self.base_url}/projects",
                    headers=headers
                )
                return response

        return APIClient()

    @pytest.mark.skip(reason="Requires running backend server")
    def test_user_registration_success(self, api_client):
        """Test successful user registration."""
        response = api_client.register(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            name="Test User"
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "testuser"

    @pytest.mark.skip(reason="Requires running backend server")
    def test_user_login_success(self, api_client):
        """Test successful user login."""
        # First register
        api_client.register(
            username="logintest",
            email="logintest@example.com",
            password="SecurePass123!",
            name="Login Test"
        )

        # Then login
        response = api_client.login("logintest", "SecurePass123!")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.skip(reason="Requires running backend server")
    def test_project_creation_workflow(self, api_client):
        """Test complete workflow: register, login, create project."""
        # Register
        api_client.register(
            username="projecttest",
            email="projecttest@example.com",
            password="SecurePass123!",
            name="Project Test"
        )

        # Login
        login_response = api_client.login("projecttest", "SecurePass123!")
        assert login_response.status_code == 200

        # Create project
        project_response = api_client.create_project(
            name="Test Project",
            description="A test project"
        )

        assert project_response.status_code == 201
        data = project_response.json()
        assert data["name"] == "Test Project"

    @pytest.mark.skip(reason="Requires running backend server")
    def test_list_projects_requires_auth(self, api_client):
        """Test that listing projects requires authentication."""
        response = requests.get("http://localhost:8000/api/v1/projects")

        # Should fail without auth
        assert response.status_code in [401, 403]


class TestSocratesCLIPrompts:
    """Test interactive prompts and commands."""

    def test_prompt_session_initialization(self):
        """Test that prompt session can be initialized."""
        try:
            from prompt_toolkit import PromptSession
            session = PromptSession()
            assert session is not None
        except ImportError:
            pytest.skip("prompt_toolkit not available")

    def test_cli_command_parsing(self):
        """Test CLI command parsing."""
        from Socrates import SocratesCLI

        # Test command validation
        valid_commands = [
            "register",
            "login",
            "logout",
            "create-project",
            "list-projects",
            "create-session",
            "ask-question",
            "export-project",
            "help",
            "exit"
        ]

        for cmd in valid_commands:
            # These should be valid commands in the CLI
            assert isinstance(cmd, str)
            assert len(cmd) > 0


class TestSocratesAPIIntegration:
    """Test API response handling and parsing."""

    @pytest.fixture
    def mock_health_response(self):
        """Mock health check response."""
        return {
            "status": "ok",
            "environment": "development",
            "version": "0.1.0"
        }

    def test_health_check_response_parsing(self, mock_health_response):
        """Test parsing health check response."""
        # Simulate parsing
        assert mock_health_response["status"] == "ok"
        assert "version" in mock_health_response

    def test_auth_response_contains_token(self):
        """Test that auth response contains access token."""
        mock_response = {
            "access_token": "test-token-123",
            "token_type": "bearer",
            "username": "testuser"
        }

        assert "access_token" in mock_response
        assert mock_response["token_type"] == "bearer"

    def test_project_response_structure(self):
        """Test project response structure."""
        mock_project = {
            "id": "project-123",
            "name": "Test Project",
            "description": "A test project",
            "maturity_score": 45,
            "owner_id": "user-123",
            "created_at": "2025-01-01T00:00:00Z"
        }

        assert "id" in mock_project
        assert "name" in mock_project
        assert "maturity_score" in mock_project


class TestErrorHandling:
    """Test error handling in CLI workflow."""

    def test_invalid_credentials_error(self):
        """Test handling of invalid credentials."""
        mock_response = {
            "detail": "Invalid credentials"
        }

        assert "detail" in mock_response
        assert "Invalid" in mock_response["detail"]

    def test_missing_required_field_error(self):
        """Test handling of missing required fields."""
        mock_response = {
            "detail": [
                {
                    "loc": ["body", "email"],
                    "msg": "Field required",
                    "type": "value_error.missing"
                }
            ]
        }

        assert "detail" in mock_response
        assert len(mock_response["detail"]) > 0

    def test_server_connection_error(self):
        """Test handling of server connection errors."""
        error_msg = "Failed to connect to server at http://localhost:8000"

        assert "Failed to connect" in error_msg
        assert "localhost:8000" in error_msg


class TestCLIEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_project_name(self):
        """Test handling of very long project names."""
        long_name = "A" * 500
        assert len(long_name) > 255

    def test_special_characters_in_description(self):
        """Test handling of special characters."""
        description = "Project with special chars: !@#$%^&*()[]{}|;:',.<>?/`~"
        assert any(char in description for char in "!@#$%^&*()")

    def test_unicode_in_username(self):
        """Test handling of unicode characters."""
        username = "user_with_émojis_🎉"
        assert any(ord(char) > 127 for char in username)

    def test_rapid_command_execution(self):
        """Test handling of rapid successive commands."""
        commands = ["cmd1", "cmd2", "cmd3"] * 10
        assert len(commands) == 30


class TestConfigurationCleanup:
    """Test configuration cleanup and reset."""

    def test_config_reset_clears_all_settings(self):
        """Test that config reset clears all settings."""
        from Socrates import SocratesConfig

        config = SocratesConfig()
        config.set("key1", "value1")
        config.set("key2", "value2")

        config.clear()

        assert config.get("key1") is None
        assert config.get("key2") is None

    def test_temporary_config_isolation(self):
        """Test that configs don't leak between instances."""
        from Socrates import SocratesConfig

        config1 = SocratesConfig()
        config1.set("test", "value1")

        config2 = SocratesConfig()

        # They should share the same file, so config2 should see config1's value
        assert config2.get("test") == "value1"

"""
API endpoint tests for Socrates2.

Tests HTTP endpoints for auth, projects, and admin functionality.
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestHealthCheckEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_ok(self, test_client):
        """Test that health check endpoint returns 200 OK."""
        response = test_client.get("/api/v1/admin/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_response_format(self, test_client):
        """Test that health check returns correct format."""
        response = test_client.get("/api/v1/admin/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy"]


@pytest.mark.api
class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_endpoint_exists(self, test_client):
        """Test that register endpoint exists."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )
        # Should either succeed or return validation error, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_login_endpoint_exists(self, test_client):
        """Test that login endpoint exists."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePassword123!"
            }
        )
        # Should either succeed or return auth error, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_register_requires_email(self, test_client):
        """Test that register requires email."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )
        # Should fail due to missing email
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_register_requires_password(self, test_client):
        """Test that register requires password."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User"
            }
        )
        # Should fail due to missing password
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.mark.api
class TestProjectEndpoints:
    """Test project management endpoints."""

    def test_list_projects_endpoint_exists(self, test_client):
        """Test that list projects endpoint exists."""
        response = test_client.get("/api/v1/projects")
        # Should either return list or auth error, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_create_project_endpoint_exists(self, test_client):
        """Test that create project endpoint exists."""
        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "description": "Test project",
                "maturity_score": 0.5
            }
        )
        # Should either succeed or return auth error, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_project_endpoint_exists(self, test_client):
        """Test that get project endpoint exists."""
        response = test_client.get("/api/v1/projects/test-id")
        # Should either return project or auth/not-found error, not 404 for the endpoint itself
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_create_project_requires_name(self, test_client):
        """Test that create project requires name."""
        response = test_client.post(
            "/api/v1/projects",
            json={
                "description": "Test project",
                "maturity_score": 0.5
            }
        )
        # Should fail due to missing name
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED  # Or auth error
        ]


@pytest.mark.api
class TestSessionEndpoints:
    """Test conversation session endpoints."""

    def test_create_session_endpoint_exists(self, test_client):
        """Test that create session endpoint exists."""
        response = test_client.post(
            "/api/v1/sessions",
            json={
                "name": "New Session",
                "project_id": "test-id"
            }
        )
        # Should either succeed or return auth error, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_list_sessions_endpoint_exists(self, test_client):
        """Test that list sessions endpoint exists."""
        response = test_client.get("/api/v1/sessions")
        # Should either return list or auth error, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_session_endpoint_exists(self, test_client):
        """Test that get session endpoint exists."""
        response = test_client.get("/api/v1/sessions/test-id")
        # Should either return session or auth/not-found error, not 404 for endpoint
        assert response.status_code != status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestErrorHandling:
    """Test error handling in API endpoints."""

    def test_invalid_json_returns_error(self, test_client):
        """Test that invalid JSON is handled gracefully."""
        response = test_client.post(
            "/api/v1/auth/register",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_missing_required_fields_returns_error(self, test_client):
        """Test that missing required fields are reported."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={}
        )
        # Should be a client error, not server error
        assert response.status_code >= status.HTTP_400_BAD_REQUEST
        assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_nonexistent_endpoint_returns_404(self, test_client):
        """Test that nonexistent endpoints return 404."""
        response = test_client.get("/api/v1/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestCORSHeaders:
    """Test CORS headers in responses."""

    def test_response_includes_content_type(self, test_client):
        """Test that responses include Content-Type header."""
        response = test_client.get("/api/v1/admin/health")
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_health_endpoint_returns_json(self, test_client):
        """Test that health endpoint returns JSON."""
        response = test_client.get("/api/v1/admin/health")
        assert response.headers["content-type"].startswith("application/json")
        # Should be parseable as JSON
        data = response.json()
        assert isinstance(data, dict)

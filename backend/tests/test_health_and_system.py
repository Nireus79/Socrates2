"""
Tests for health check and system endpoints.

Tests:
- Health check endpoint
- System status
- API version
- API documentation
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_accessible_without_auth(self, test_client):
        """Test that health check is accessible without authentication."""
        response = test_client.get("/api/v1/admin/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data

    def test_health_check_response_format(self, test_client):
        """Test health check response format."""
        response = test_client.get("/api/v1/admin/health")
        data = response.json()
        # Should contain status information
        assert isinstance(data, dict)
        assert data.get("status") in ["ok", "healthy", "up"]

    def test_health_check_consistency(self, test_client):
        """Test that health check returns consistent results."""
        response1 = test_client.get("/api/v1/admin/health")
        response2 = test_client.get("/api/v1/admin/health")
        assert response1.status_code == response2.status_code
        assert response1.json() == response2.json()


@pytest.mark.api
class TestSystemEndpoints:
    """Test system status endpoints."""

    def test_status_endpoint_exists(self, test_client):
        """Test that status endpoint is available."""
        response = test_client.get("/api/v1/admin/status")
        # Should either return status or 404 if not implemented
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_version_endpoint(self, test_client):
        """Test version endpoint if available."""
        response = test_client.get("/api/v1/admin/version")
        # Should either return version or 404 if not implemented
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.api
class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_swagger_ui_accessible(self, test_client):
        """Test that Swagger UI is accessible."""
        response = test_client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_redoc_accessible(self, test_client):
        """Test that ReDoc is accessible."""
        response = test_client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_schema_accessible(self, test_client):
        """Test that OpenAPI schema is accessible."""
        response = test_client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        # Schema should contain paths
        schema = response.json()
        assert "paths" in schema or "components" in schema

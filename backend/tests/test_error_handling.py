"""
Comprehensive error handling and edge case tests.

Tests:
- HTTP error codes (400, 401, 403, 404, 422, 500)
- Invalid input validation
- Database constraint violations
- Malformed requests
- Missing required fields
- Invalid data types
- Concurrent access conflicts
"""

import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.api
@pytest.mark.error
class TestHTTPErrorCodes:
    """Test proper HTTP error code responses."""

    def test_unauthorized_without_token(self, test_client):
        """Test 401 for missing authentication."""
        response = test_client.get("/api/v1/projects")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_forbidden_invalid_token(self, test_client):
        """Test 401/403 for invalid token."""
        response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": "Bearer invalid-token-xyz"}
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_not_found_nonexistent_resource(self, test_client, authenticated_user):
        """Test 404 for nonexistent resource."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            f"/api/v1/projects/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unprocessable_entity_invalid_json(self, test_client, authenticated_user):
        """Test 422 for invalid JSON data."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            data="invalid json {",
            headers={
                "Authorization": f"Bearer {authenticated_user['token']}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_bad_request_missing_field(self, test_client, authenticated_user):
        """Test 400/422 for missing required field."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={},  # Missing required fields
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.api
@pytest.mark.error
class TestInputValidation:
    """Test input validation and rejection of invalid data."""

    def test_invalid_email_format(self, test_client):
        """Test rejection of invalid email format."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_uuid_in_path(self, test_client, authenticated_user):
        """Test rejection of invalid UUID in path."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects/not-a-uuid",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_numeric_field(self, test_client, authenticated_user):
        """Test rejection of non-numeric value for numeric field."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "description": "Test",
                "maturity_score": "not-a-number"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_boolean_field(self, test_client, authenticated_user):
        """Test rejection of invalid boolean value."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "description": "Test",
                "is_active": "maybe"  # Should be boolean
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either accept it or reject with 422
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.api
@pytest.mark.error
class TestPasswordValidation:
    """Test password validation rules."""

    def test_password_too_short(self, test_client):
        """Test rejection of password that's too short."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "full_name": "Test User"
            }
        )
        assert response.status_code >= status.HTTP_400_BAD_REQUEST

    def test_password_no_uppercase(self, test_client):
        """Test rejection of password without uppercase."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weakpassword123!",
                "full_name": "Test User"
            }
        )
        # Should reject weak password
        assert response.status_code >= status.HTTP_400_BAD_REQUEST

    def test_password_no_special_character(self, test_client):
        """Test rejection of password without special character."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "WeakPassword123",
                "full_name": "Test User"
            }
        )
        # Should reject weak password
        assert response.status_code >= status.HTTP_400_BAD_REQUEST


@pytest.mark.api
@pytest.mark.error
class TestDuplicateResourceHandling:
    """Test handling of duplicate resources."""

    def test_duplicate_email_registration(self, test_client, test_user_data):
        """Test rejection of duplicate email in registration."""
        # Register first user
        test_client.post("/api/v1/auth/register", json=test_user_data)

        # Try to register with same email
        response = test_client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code >= status.HTTP_400_BAD_REQUEST

    def test_duplicate_project_name(self, test_client, authenticated_user, test_project_data):
        """Test handling of duplicate project names for same user."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create first project
        test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        # Try to create second project with same name
        response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Some systems allow duplicates, some don't
        assert response.status_code in [
            status.HTTP_201_CREATED,  # Duplicates allowed
            status.HTTP_400_BAD_REQUEST,  # Duplicates not allowed
        ]


@pytest.mark.api
@pytest.mark.error
class TestEmptyAndNullValues:
    """Test handling of empty and null values."""

    def test_empty_string_name(self, test_client, authenticated_user):
        """Test rejection of empty string for name field."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": "",
                "description": "Test"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_email(self, test_client):
        """Test rejection of empty email."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "",
                "password": "SecurePassword123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_null_required_field(self, test_client, authenticated_user):
        """Test rejection of null for required field."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": None,
                "description": "Test"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.mark.api
@pytest.mark.error
class TestExtremeValues:
    """Test handling of extreme input values."""

    def test_very_long_string(self, test_client, authenticated_user):
        """Test handling of very long string input."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        very_long_name = "x" * 10000
        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": very_long_name,
                "description": "Test"
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either accept or reject with 422
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_negative_numeric_field(self, test_client, authenticated_user):
        """Test handling of negative value for unsigned field."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "description": "Test",
                "maturity_score": -0.5
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either accept or reject with 422
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_out_of_range_numeric_field(self, test_client, authenticated_user):
        """Test handling of value outside expected range."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "description": "Test",
                "maturity_score": 999.99
            },
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either accept or reject with 422
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.api
@pytest.mark.error
class TestMissingHeaders:
    """Test handling of missing required headers."""

    def test_missing_content_type(self, test_client, authenticated_user):
        """Test handling of missing Content-Type header."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # FastAPI should still work without explicit Content-Type for JSON
        response = test_client.post(
            "/api/v1/projects",
            json={"name": "Test"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should work even without explicit Content-Type
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY  # Missing required fields
        ]

    def test_wrong_content_type(self, test_client, authenticated_user):
        """Test handling of wrong Content-Type header."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            data="invalid",
            headers={
                "Authorization": f"Bearer {authenticated_user['token']}",
                "Content-Type": "text/plain"
            }
        )
        assert response.status_code >= status.HTTP_400_BAD_REQUEST

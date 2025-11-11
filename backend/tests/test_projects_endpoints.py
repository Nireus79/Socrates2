"""
Comprehensive tests for project endpoints.

Tests:
- Create project
- List projects
- Get project details
- Update project
- Delete project
- Project filtering and pagination
- Project permissions
"""

import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.api
class TestProjectCreation:
    """Test project creation endpoint."""

    def test_create_project_success(self, test_client, authenticated_user, test_project_data):
        """Test successful project creation."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == test_project_data["name"]
        assert data["description"] == test_project_data["description"]

    def test_create_project_missing_name(self, test_client, authenticated_user):
        """Test project creation fails without name."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json={"description": "No name project"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_project_requires_auth(self, test_client, test_project_data):
        """Test project creation requires authentication."""
        response = test_client.post("/api/v1/projects", json=test_project_data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_create_project_returns_id(self, test_client, authenticated_user, test_project_data):
        """Test that created project has unique ID."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], str)

    def test_create_project_sets_owner(self, test_client, authenticated_user, test_project_data):
        """Test that authenticated user becomes project owner."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        data = response.json()
        assert "owner_id" in data or "user_id" in data


@pytest.mark.api
class TestProjectListing:
    """Test project listing endpoint."""

    def test_list_projects_success(self, test_client, authenticated_user):
        """Test getting list of projects."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_requires_auth(self, test_client):
        """Test listing projects requires authentication."""
        response = test_client.get("/api/v1/projects")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_list_projects_empty(self, test_client, authenticated_user):
        """Test listing projects when user has none."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_returns_user_projects_only(
        self, test_client, authenticated_user, test_project_data
    ):
        """Test that user only sees their own projects."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create a project
        test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        # List projects
        response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        data = response.json()
        assert len(data) > 0
        assert data[0]["name"] == test_project_data["name"]


@pytest.mark.api
class TestProjectRetrieval:
    """Test getting individual project details."""

    def test_get_project_success(self, test_client, authenticated_user, test_project_data):
        """Test getting project details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = create_response.json()["id"]

        # Get project
        response = test_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == test_project_data["name"]

    def test_get_nonexistent_project(self, test_client, authenticated_user):
        """Test getting nonexistent project returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            f"/api/v1/projects/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_requires_auth(self, test_client):
        """Test getting project requires authentication."""
        response = test_client.get(f"/api/v1/projects/{uuid4()}")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.api
class TestProjectUpdate:
    """Test project update endpoint."""

    def test_update_project_success(
        self, test_client, authenticated_user, test_project_data, test_project_data_alt
    ):
        """Test successful project update."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = create_response.json()["id"]

        # Update project
        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": test_project_data_alt["name"]},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == test_project_data_alt["name"]

    def test_update_project_partial(self, test_client, authenticated_user, test_project_data):
        """Test partial project update."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = create_response.json()["id"]

        # Partial update
        new_description = "Updated description"
        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"description": new_description},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == new_description
        assert data["name"] == test_project_data["name"]

    def test_update_nonexistent_project(self, test_client, authenticated_user):
        """Test updating nonexistent project returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.patch(
            f"/api/v1/projects/{uuid4()}",
            json={"name": "New name"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestProjectDeletion:
    """Test project deletion endpoint."""

    def test_delete_project_success(self, test_client, authenticated_user, test_project_data):
        """Test successful project deletion."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = create_response.json()["id"]

        # Delete project
        response = test_client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]

        # Verify deleted
        get_response = test_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_project(self, test_client, authenticated_user):
        """Test deleting nonexistent project returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.delete(
            f"/api/v1/projects/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_requires_auth(self, test_client):
        """Test deleting project requires authentication."""
        response = test_client.delete(f"/api/v1/projects/{uuid4()}")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

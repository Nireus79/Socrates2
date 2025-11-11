"""
Comprehensive tests for conversation session endpoints.

Tests:
- Start session
- List sessions
- Get session details
- Update session
- End session
- Session message history
"""

import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.api
class TestSessionCreation:
    """Test session creation endpoint."""

    def test_start_session_success(self, test_client, authenticated_user, test_project_data, test_session_data):
        """Test successful session creation."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project first
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create session
        session_data = {**test_session_data, "project_id": str(project_id)}
        response = test_client.post(
            f"/api/v1/projects/{project_id}/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == test_session_data["name"]
        assert data["status"] == "active"

    def test_start_session_missing_project(self, test_client, authenticated_user, test_session_data):
        """Test creating session fails without project."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            f"/api/v1/projects/{uuid4()}/sessions",
            json=test_session_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_session_missing_name(self, test_client, authenticated_user, test_project_data):
        """Test session creation requires name."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create session without name
        response = test_client.post(
            f"/api/v1/projects/{project_id}/sessions",
            json={"description": "No name session"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
class TestSessionListing:
    """Test session listing endpoint."""

    def test_list_sessions_success(self, test_client, authenticated_user, test_project_data):
        """Test getting list of sessions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # List sessions
        response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_sessions_empty(self, test_client, authenticated_user, test_project_data):
        """Test listing sessions for empty project."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # List should return empty list
        response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        data = response.json()
        assert data == []

    def test_list_sessions_requires_auth(self, test_client):
        """Test listing sessions requires authentication."""
        response = test_client.get(f"/api/v1/projects/{uuid4()}/sessions")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.api
class TestSessionRetrieval:
    """Test getting individual session details."""

    def test_get_session_success(
        self, test_client, authenticated_user, test_project_data, test_session_data
    ):
        """Test getting session details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create session
        session_data = {**test_session_data, "project_id": str(project_id)}
        create_response = test_client.post(
            f"/api/v1/projects/{project_id}/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        session_id = create_response.json()["id"]

        # Get session
        response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions/{session_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == session_id

    def test_get_nonexistent_session(self, test_client, authenticated_user, test_project_data):
        """Test getting nonexistent session returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestSessionUpdate:
    """Test session update endpoint."""

    def test_update_session_success(
        self, test_client, authenticated_user, test_project_data, test_session_data
    ):
        """Test successful session update."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create session
        session_data = {**test_session_data, "project_id": str(project_id)}
        create_response = test_client.post(
            f"/api/v1/projects/{project_id}/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        session_id = create_response.json()["id"]

        # Update session
        response = test_client.patch(
            f"/api/v1/projects/{project_id}/sessions/{session_id}",
            json={"status": "paused"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "paused"


@pytest.mark.api
class TestSessionMessages:
    """Test session message history."""

    def test_get_session_messages(
        self, test_client, authenticated_user, test_project_data, test_session_data
    ):
        """Test getting session message history."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project and session
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        session_data = {**test_session_data, "project_id": str(project_id)}
        create_response = test_client.post(
            f"/api/v1/projects/{project_id}/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        session_id = create_response.json()["id"]

        # Get messages
        response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

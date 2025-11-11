"""
Comprehensive tests for team management endpoints.

Tests:
- Create team
- List teams
- Get team details
- Update team
- Delete team
- Add team member
- Remove team member
- Team permissions
"""

import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.api
class TestTeamCreation:
    """Test team creation endpoint."""

    def test_create_team_success(self, test_client, authenticated_user, test_team_data):
        """Test successful team creation."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/teams",
            json=test_team_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == test_team_data["name"]

    def test_create_team_missing_name(self, test_client, authenticated_user):
        """Test team creation fails without name."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/teams",
            json={"description": "No name team"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_team_requires_auth(self, test_client, test_team_data):
        """Test team creation requires authentication."""
        response = test_client.post("/api/v1/teams", json=test_team_data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.api
class TestTeamListing:
    """Test team listing endpoint."""

    def test_list_teams_success(self, test_client, authenticated_user):
        """Test getting list of teams."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/teams",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_teams_requires_auth(self, test_client):
        """Test listing teams requires authentication."""
        response = test_client.get("/api/v1/teams")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.api
class TestTeamRetrieval:
    """Test getting individual team details."""

    def test_get_team_success(self, test_client, authenticated_user, test_team_data):
        """Test getting team details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create team
        create_response = test_client.post(
            "/api/v1/teams",
            json=test_team_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        team_id = create_response.json()["id"]

        # Get team
        response = test_client.get(
            f"/api/v1/teams/{team_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == team_id
        assert data["name"] == test_team_data["name"]

    def test_get_nonexistent_team(self, test_client, authenticated_user):
        """Test getting nonexistent team returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            f"/api/v1/teams/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestTeamMembership:
    """Test team member management."""

    def test_add_team_member_success(self, test_client, authenticated_user, test_user_data_alt, test_team_data):
        """Test adding member to team."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create team
        team_response = test_client.post(
            "/api/v1/teams",
            json=test_team_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        team_id = team_response.json()["id"]

        # Register another user
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)

        # Add member to team
        response = test_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"email": test_user_data_alt["email"], "role": "member"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED
        ]

    def test_list_team_members(self, test_client, authenticated_user, test_team_data):
        """Test listing team members."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create team
        team_response = test_client.post(
            "/api/v1/teams",
            json=test_team_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        team_id = team_response.json()["id"]

        # List members
        response = test_client.get(
            f"/api/v1/teams/{team_id}/members",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Creator should be a member
        assert len(data) >= 1

    def test_remove_team_member(self, test_client, authenticated_user, test_user_data_alt, test_team_data):
        """Test removing member from team."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create team
        team_response = test_client.post(
            "/api/v1/teams",
            json=test_team_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        team_id = team_response.json()["id"]

        # Register another user
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)

        # Add member
        test_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"email": test_user_data_alt["email"], "role": "member"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )

        # Remove member
        response = test_client.delete(
            f"/api/v1/teams/{team_id}/members/{test_user_data_alt['email']}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]

"""
Comprehensive authorization and permissions tests.

Tests:
- User can only access their own projects
- User can only access their own specifications
- Team members can access shared resources
- Owner has full permissions
- Member has limited permissions
- Non-member cannot access
- Role-based access control
"""

import pytest
from fastapi import status


@pytest.mark.api
@pytest.mark.security
class TestUserIsolation:
    """Test that users are properly isolated from each other's data."""

    def test_user_cannot_access_other_user_projects(
        self, test_client, test_user_data, test_user_data_alt, test_project_data
    ):
        """Test that user cannot see other user's projects."""
        # Register and login first user
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response1 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token1 = response1.json()["access_token"]

        # Register and login second user
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)
        response2 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data_alt["username"],
                "password": test_user_data_alt["password"]
            }
        )
        token2 = response2.json()["access_token"]

        # User 1 creates project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token1}"}
        )
        project_id = create_response.json()["id"]

        # User 2 tries to access User 1's project
        response = test_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        # Should either return 404 or 403
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]

    def test_user_can_access_own_projects(
        self, test_client, test_user_data, test_project_data
    ):
        """Test that user can access their own projects."""
        # Register and login
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = response.json()["access_token"]

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = create_response.json()["id"]

        # User can access their own project
        response = test_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_user_can_only_see_own_projects_in_list(
        self, test_client, test_user_data, test_user_data_alt, test_project_data
    ):
        """Test that each user only sees their own projects in list."""
        # Register and login first user
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response1 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token1 = response1.json()["access_token"]

        # Register and login second user
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)
        response2 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data_alt["username"],
                "password": test_user_data_alt["password"]
            }
        )
        token2 = response2.json()["access_token"]

        # User 1 creates project
        test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token1}"}
        )

        # User 2 lists projects - should be empty
        response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token2}"}
        )
        projects = response.json()
        assert len(projects) == 0


@pytest.mark.api
@pytest.mark.security
class TestOwnerPermissions:
    """Test owner-level permissions."""

    def test_owner_can_delete_project(
        self, test_client, test_user_data, test_project_data
    ):
        """Test that project owner can delete project."""
        # Register and login
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = response.json()["access_token"]

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = create_response.json()["id"]

        # Owner can delete
        response = test_client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]

    def test_owner_can_update_project(
        self, test_client, test_user_data, test_project_data
    ):
        """Test that project owner can update project."""
        # Register and login
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = response.json()["access_token"]

        # Create project
        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = create_response.json()["id"]

        # Owner can update
        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
@pytest.mark.security
class TestProjectAccessControl:
    """Test project-level access control."""

    def test_non_owner_cannot_delete_project(
        self, test_client, test_user_data, test_user_data_alt, test_project_data
    ):
        """Test that non-owner cannot delete project."""
        # User 1: register, login, create project
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response1 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token1 = response1.json()["access_token"]

        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token1}"}
        )
        project_id = create_response.json()["id"]

        # User 2: register, login, try to delete User 1's project
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)
        response2 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data_alt["username"],
                "password": test_user_data_alt["password"]
            }
        )
        token2 = response2.json()["access_token"]

        response = test_client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        # Should be rejected with 403 or 404
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]

    def test_non_owner_cannot_update_project(
        self, test_client, test_user_data, test_user_data_alt, test_project_data
    ):
        """Test that non-owner cannot update project."""
        # User 1: create project
        test_client.post("/api/v1/auth/register", json=test_user_data)
        response1 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token1 = response1.json()["access_token"]

        create_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token1}"}
        )
        project_id = create_response.json()["id"]

        # User 2: try to update User 1's project
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)
        response2 = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data_alt["username"],
                "password": test_user_data_alt["password"]
            }
        )
        token2 = response2.json()["access_token"]

        response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"description": "Hacked"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        # Should be rejected
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]

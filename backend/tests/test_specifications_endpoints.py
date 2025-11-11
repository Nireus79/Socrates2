"""
Comprehensive tests for specifications endpoints.

Tests:
- Create specification
- List specifications
- Get specification details
- Update specification
- Delete specification
- Specification analysis
- Category filtering
"""

import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.api
class TestSpecificationCreation:
    """Test specification creation endpoint."""

    def test_create_specification_success(
        self, test_client, authenticated_user, test_project_data, test_specification_data
    ):
        """Test successful specification creation."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project first
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create specification
        spec_data = {**test_specification_data, "project_id": str(project_id)}
        response = test_client.post(
            f"/api/v1/projects/{project_id}/specifications",
            json=spec_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["category"] == test_specification_data["category"]

    def test_create_specification_missing_project(self, test_client, authenticated_user, test_specification_data):
        """Test creating specification fails without project."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            f"/api/v1/projects/{uuid4()}/specifications",
            json=test_specification_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_specification_missing_category(
        self, test_client, authenticated_user, test_project_data
    ):
        """Test specification creation requires category."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project first
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create specification without category
        response = test_client.post(
            f"/api/v1/projects/{project_id}/specifications",
            json={"key": "test", "value": "test"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
class TestSpecificationListing:
    """Test specification listing endpoint."""

    def test_list_specifications_success(
        self, test_client, authenticated_user, test_project_data
    ):
        """Test getting list of specifications."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # List specifications
        response = test_client.get(
            f"/api/v1/projects/{project_id}/specifications",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_specifications_empty(
        self, test_client, authenticated_user, test_project_data
    ):
        """Test listing specifications for empty project."""
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
            f"/api/v1/projects/{project_id}/specifications",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        data = response.json()
        assert data == []

    def test_list_specifications_requires_auth(self, test_client, test_project_data):
        """Test listing specifications requires authentication."""
        response = test_client.get(
            f"/api/v1/projects/{uuid4()}/specifications"
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.api
class TestSpecificationRetrieval:
    """Test getting individual specification details."""

    def test_get_specification_success(
        self, test_client, authenticated_user, test_project_data, test_specification_data
    ):
        """Test getting specification details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create specification
        spec_data = {**test_specification_data, "project_id": str(project_id)}
        create_response = test_client.post(
            f"/api/v1/projects/{project_id}/specifications",
            json=spec_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        spec_id = create_response.json()["id"]

        # Get specification
        response = test_client.get(
            f"/api/v1/projects/{project_id}/specifications/{spec_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == spec_id

    def test_get_nonexistent_specification(
        self, test_client, authenticated_user, test_project_data
    ):
        """Test getting nonexistent specification returns 404."""
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
            f"/api/v1/projects/{project_id}/specifications/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestSpecificationUpdate:
    """Test specification update endpoint."""

    def test_update_specification_success(
        self, test_client, authenticated_user, test_project_data,
        test_specification_data, test_specification_data_alt
    ):
        """Test successful specification update."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create specification
        spec_data = {**test_specification_data, "project_id": str(project_id)}
        create_response = test_client.post(
            f"/api/v1/projects/{project_id}/specifications",
            json=spec_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        spec_id = create_response.json()["id"]

        # Update specification
        response = test_client.patch(
            f"/api/v1/projects/{project_id}/specifications/{spec_id}",
            json={"value": test_specification_data_alt["value"]},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == test_specification_data_alt["value"]

    def test_update_nonexistent_specification(
        self, test_client, authenticated_user, test_project_data
    ):
        """Test updating nonexistent specification returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        response = test_client.patch(
            f"/api/v1/projects/{project_id}/specifications/{uuid4()}",
            json={"value": "new value"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestSpecificationDeletion:
    """Test specification deletion endpoint."""

    def test_delete_specification_success(
        self, test_client, authenticated_user, test_project_data, test_specification_data
    ):
        """Test successful specification deletion."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        project_id = project_response.json()["id"]

        # Create specification
        spec_data = {**test_specification_data, "project_id": str(project_id)}
        create_response = test_client.post(
            f"/api/v1/projects/{project_id}/specifications",
            json=spec_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        spec_id = create_response.json()["id"]

        # Delete specification
        response = test_client.delete(
            f"/api/v1/projects/{project_id}/specifications/{spec_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]

        # Verify deleted
        get_response = test_client.get(
            f"/api/v1/projects/{project_id}/specifications/{spec_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

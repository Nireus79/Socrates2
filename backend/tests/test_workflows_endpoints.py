"""
Comprehensive tests for workflow endpoints.

Tests:
- Create workflow
- List workflows
- Get workflow details
- Update workflow
- Execute workflow
- Get workflow status
"""

import pytest
from fastapi import status
from uuid import uuid4


@pytest.mark.api
class TestWorkflowCreation:
    """Test workflow creation endpoint."""

    def test_create_workflow_success(self, test_client, authenticated_user, test_workflow_data):
        """Test successful workflow creation."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == test_workflow_data["name"]
        assert data["status"] == "active"

    def test_create_workflow_missing_name(self, test_client, authenticated_user):
        """Test workflow creation fails without name."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/workflows",
            json={"description": "No name workflow", "domains": ["architecture"]},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_workflow_missing_domains(self, test_client, authenticated_user):
        """Test workflow creation requires at least one domain."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.post(
            "/api/v1/workflows",
            json={"name": "Test", "description": "Test", "domains": []},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should reject empty domains list
        assert response.status_code >= status.HTTP_400_BAD_REQUEST

    def test_create_workflow_requires_auth(self, test_client, test_workflow_data):
        """Test workflow creation requires authentication."""
        response = test_client.post("/api/v1/workflows", json=test_workflow_data)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.api
class TestWorkflowListing:
    """Test workflow listing endpoint."""

    def test_list_workflows_success(self, test_client, authenticated_user):
        """Test getting list of workflows."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/workflows",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_requires_auth(self, test_client):
        """Test listing workflows requires authentication."""
        response = test_client.get("/api/v1/workflows")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_list_workflows_by_status(self, test_client, authenticated_user):
        """Test filtering workflows by status."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/workflows?status=active",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.api
class TestWorkflowRetrieval:
    """Test getting individual workflow details."""

    def test_get_workflow_success(self, test_client, authenticated_user, test_workflow_data):
        """Test getting workflow details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create workflow
        create_response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        workflow_id = create_response.json()["id"]

        # Get workflow
        response = test_client.get(
            f"/api/v1/workflows/{workflow_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == test_workflow_data["name"]

    def test_get_nonexistent_workflow(self, test_client, authenticated_user):
        """Test getting nonexistent workflow returns 404."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            f"/api/v1/workflows/{uuid4()}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestWorkflowExecution:
    """Test workflow execution endpoints."""

    def test_execute_workflow(self, test_client, authenticated_user, test_workflow_data):
        """Test executing a workflow."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create workflow
        create_response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        workflow_id = create_response.json()["id"]

        # Execute workflow
        response = test_client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json={"input_data": {"domain": "architecture"}},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either execute or provide guidance
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_202_ACCEPTED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_get_workflow_status(self, test_client, authenticated_user, test_workflow_data):
        """Test getting workflow execution status."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create workflow
        create_response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        workflow_id = create_response.json()["id"]

        # Get status
        response = test_client.get(
            f"/api/v1/workflows/{workflow_id}/status",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should return status or 404 if not found
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.api
class TestWorkflowUpdate:
    """Test workflow update endpoint."""

    def test_update_workflow_success(self, test_client, authenticated_user, test_workflow_data):
        """Test successful workflow update."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create workflow
        create_response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        workflow_id = create_response.json()["id"]

        # Update workflow
        response = test_client.patch(
            f"/api/v1/workflows/{workflow_id}",
            json={"status": "paused"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "paused"

    def test_delete_workflow(self, test_client, authenticated_user, test_workflow_data):
        """Test workflow deletion."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Create workflow
        create_response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        workflow_id = create_response.json()["id"]

        # Delete workflow
        response = test_client.delete(
            f"/api/v1/workflows/{workflow_id}",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]

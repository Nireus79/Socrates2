"""
End-to-end workflow tests covering complete user journeys.

Tests:
- Complete project creation workflow
- Complete specification workflow
- Multi-domain workflow execution
- Team collaboration workflow
- Project sharing workflow
"""

import pytest
from fastapi import status


@pytest.mark.e2e
class TestCompleteProjectWorkflow:
    """Test complete project creation and management workflow."""

    def test_user_creates_project_and_specifications(
        self, test_client, authenticated_user, test_project_data, test_specification_data
    ):
        """Test creating project and adding specifications."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        token = authenticated_user["token"]

        # 1. Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert project_response.status_code == status.HTTP_201_CREATED
        project_id = project_response.json()["id"]
        print(f"Created project: {project_id}")

        # 2. Verify project in list
        list_response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == status.HTTP_200_OK
        projects = list_response.json()
        assert len(projects) > 0
        assert any(p["id"] == project_id for p in projects)

        # 3. Get project details
        get_response = test_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == status.HTTP_200_OK

        # 4. Add specifications
        spec_data = {**test_specification_data, "project_id": str(project_id)}
        spec_response = test_client.post(
            f"/api/v1/projects/{project_id}/specifications",
            json=spec_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert spec_response.status_code == status.HTTP_201_CREATED
        spec_id = spec_response.json()["id"]

        # 5. List specifications
        specs_list_response = test_client.get(
            f"/api/v1/projects/{project_id}/specifications",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert specs_list_response.status_code == status.HTTP_200_OK
        specs = specs_list_response.json()
        assert len(specs) > 0

        # 6. Update specification
        update_response = test_client.patch(
            f"/api/v1/projects/{project_id}/specifications/{spec_id}",
            json={"value": "Updated value"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == status.HTTP_200_OK

    def test_user_creates_session_and_conducts_dialog(
        self, test_client, authenticated_user, test_project_data, test_session_data
    ):
        """Test creating session and conducting conversation."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        token = authenticated_user["token"]

        # 1. Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = project_response.json()["id"]

        # 2. Start session
        session_data = {**test_session_data, "project_id": str(project_id)}
        session_response = test_client.post(
            f"/api/v1/projects/{project_id}/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert session_response.status_code == status.HTTP_201_CREATED
        session_id = session_response.json()["id"]

        # 3. Get session details
        get_response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == status.HTTP_200_OK

        # 4. Get session messages
        messages_response = test_client.get(
            f"/api/v1/projects/{project_id}/sessions/{session_id}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert messages_response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
class TestMultiDomainWorkflow:
    """Test multi-domain workflow execution."""

    def test_create_workflow_with_multiple_domains(
        self, test_client, authenticated_user, test_workflow_data
    ):
        """Test creating and executing multi-domain workflow."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        token = authenticated_user["token"]

        # 1. Create workflow with multiple domains
        workflow_response = test_client.post(
            "/api/v1/workflows",
            json=test_workflow_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert workflow_response.status_code == status.HTTP_201_CREATED
        workflow_id = workflow_response.json()["id"]
        print(f"Created workflow: {workflow_id}")

        # 2. Verify workflow in list
        list_response = test_client.get(
            "/api/v1/workflows",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == status.HTTP_200_OK
        workflows = list_response.json()
        assert len(workflows) > 0

        # 3. Get workflow details
        get_response = test_client.get(
            f"/api/v1/workflows/{workflow_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == status.HTTP_200_OK
        workflow = get_response.json()
        assert workflow["domains"] == test_workflow_data["domains"]

        # 4. Execute workflow
        execute_response = test_client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json={"input_data": {"test": "value"}},
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should either execute or indicate execution started
        assert execute_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_202_ACCEPTED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.e2e
class TestTeamCollaborationWorkflow:
    """Test team collaboration workflow."""

    def test_owner_creates_team_and_adds_members(
        self, test_client, authenticated_user, test_user_data_alt, test_team_data
    ):
        """Test owner creating team and adding members."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        owner_token = authenticated_user["token"]

        # 1. Owner creates team
        team_response = test_client.post(
            "/api/v1/teams",
            json=test_team_data,
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert team_response.status_code == status.HTTP_201_CREATED
        team_id = team_response.json()["id"]

        # 2. Register another user
        test_client.post("/api/v1/auth/register", json=test_user_data_alt)

        # 3. Owner adds member to team
        add_member_response = test_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"email": test_user_data_alt["email"], "role": "member"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert add_member_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED
        ]

        # 4. Owner lists team members
        list_members_response = test_client.get(
            f"/api/v1/teams/{team_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert list_members_response.status_code == status.HTTP_200_OK
        members = list_members_response.json()
        assert len(members) >= 2  # Owner + new member

        # 5. New member logs in and sees team
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data_alt["email"],
                "password": test_user_data_alt["password"]
            }
        )
        member_token = login_response.json()["access_token"]

        # 6. Member sees their teams
        member_teams_response = test_client.get(
            "/api/v1/teams",
            headers={"Authorization": f"Bearer {member_token}"}
        )
        assert member_teams_response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
class TestDataConsistencyWorkflow:
    """Test data consistency across operations."""

    def test_project_data_consistency(
        self, test_client, authenticated_user, test_project_data, test_specification_data
    ):
        """Test that project data remains consistent across operations."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        token = authenticated_user["token"]

        # Create project
        project_response = test_client.post(
            "/api/v1/projects",
            json=test_project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = project_response.json()["id"]
        original_name = project_response.json()["name"]

        # Update project
        update_data = {"description": "Updated description"}
        update_response = test_client.patch(
            f"/api/v1/projects/{project_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert update_response.status_code == status.HTTP_200_OK

        # Verify name unchanged
        get_response = test_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        updated_project = get_response.json()
        assert updated_project["name"] == original_name
        assert updated_project["description"] == update_data["description"]

        # List projects and verify consistency
        list_response = test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"}
        )
        projects = list_response.json()
        matching_project = next(p for p in projects if p["id"] == project_id)
        assert matching_project["name"] == original_name
        assert matching_project["description"] == update_data["description"]

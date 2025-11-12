"""
Debug test for list projects API endpoint.

Tests the projects listing functionality using test client and fixtures.
"""
import pytest
from uuid import uuid4


@pytest.mark.api
def test_list_projects_with_auth(test_client, db_auth, db_specs):
    """Test list_projects API endpoint with proper authentication."""
    from app.models import User, Project
    from app.core.security import create_access_token
    from datetime import timedelta
    from app.core.config import settings

    # Create a test user
    test_user = User(
        username="testuser",
        name="Test",
        surname="User",
        email="test@example.com",
        hashed_password="$2b$12$hashedpassword"  # Dummy hashed password
    )
    db_auth.add(test_user)
    db_auth.commit()
    db_auth.refresh(test_user)

    # Create access token
    access_token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Create some test projects
    for i in range(3):
        project = Project(
            name=f"Test Project {i}",
            description=f"Test project {i} description",
            creator_id=str(test_user.id),
            owner_id=str(test_user.id),
            user_id=str(test_user.id),
            current_phase="discovery",
            maturity_score=0.5 + (i * 0.1),
            status="active"
        )
        db_specs.add(project)
    db_specs.commit()

    # Call list_projects endpoint with authentication
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = test_client.get(
        "/api/v1/projects?skip=0&limit=100",
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert "projects" in data or isinstance(data, list)
    projects = data if isinstance(data, list) else data.get('projects', [])
    print(f"✓ Successfully listed {len(projects)} projects")


@pytest.mark.api
def test_list_projects_without_auth(test_client):
    """Test list_projects endpoint returns 401 without authentication."""
    response = test_client.get("/api/v1/projects?skip=0&limit=100")

    print(f"Status: {response.status_code}")
    assert response.status_code == 401
    print("✓ Correctly requires authentication")

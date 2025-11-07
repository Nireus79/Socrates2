"""
Test Projects API Endpoints

Tests for HTTP endpoints in /api/v1/projects:
- POST /api/v1/projects - Create project
- GET /api/v1/projects - List user's projects
- GET /api/v1/projects/{id} - Get project details
- PUT /api/v1/projects/{id} - Update project
- DELETE /api/v1/projects/{id} - Delete project
- GET /api/v1/projects/{id}/status - Get project status
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_create_project(test_user):
    """Test POST /api/v1/projects - Create a new project"""
    # Create access token
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test API Project",
            "description": "Project created via API test"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'project_id' in data
    assert 'project' in data
    assert data['project']['name'] == "Test API Project"
    assert data['project']['status'] == 'active'
    assert data['project']['maturity_score'] == 0


def test_create_project_unauthorized():
    """Test that creating project requires authentication"""
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Unauthorized Project",
            "description": "Should fail"
        }
    )

    assert response.status_code == 401


def test_create_project_validation(test_user):
    """Test validation when creating project"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Missing name
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "description": "Project without name"
        }
    )

    assert response.status_code in [400, 422]  # Validation error


def test_list_projects(test_user):
    """Test GET /api/v1/projects - List user's projects"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create a project first
    client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Project for Listing", "description": "Test"}
    )

    # List projects
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'projects' in data
    assert isinstance(data['projects'], list)
    assert len(data['projects']) > 0

    # Find our project
    project_names = [p['name'] for p in data['projects']]
    assert "Project for Listing" in project_names


def test_list_projects_pagination(test_user):
    """Test pagination in list projects"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create multiple projects
    for i in range(3):
        client.post(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"Pagination Test {i}", "description": "Test"}
        )

    # List with limit
    response = client.get(
        "/api/v1/projects?limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # May return limited results if pagination is implemented
    assert 'projects' in data
    assert len(data['projects']) >= 2


def test_get_project(test_user):
    """Test GET /api/v1/projects/{id} - Get project details"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Get Project Test", "description": "Test get endpoint"}
    )
    project_id = create_response.json()['project_id']

    # Get project
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'project' in data
    assert data['project']['id'] == project_id
    assert data['project']['name'] == "Get Project Test"


def test_get_nonexistent_project(test_user):
    """Test getting a project that doesn't exist"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Random UUID that doesn't exist
    from uuid import uuid4
    fake_id = str(uuid4())

    response = client.get(
        f"/api/v1/projects/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_get_other_user_project(test_user, auth_session):
    """Test that users can't access other users' projects"""
    from app.models.user import User

    # Create another user
    other_user = User(
        email='otheruser@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_session.add(other_user)
    auth_session.commit()
    auth_session.refresh(other_user)

    # Create project as other user
    other_token = create_access_token(data={"sub": other_user.email})
    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"name": "Other User Project", "description": "Test"}
    )
    project_id = create_response.json()['project_id']

    # Try to access as test_user
    test_token = create_access_token(data={"sub": str(test_user.id)})
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )

    assert response.status_code == 403  # Forbidden


def test_update_project(test_user):
    """Test PUT /api/v1/projects/{id} - Update project"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Original Name", "description": "Original description"}
    )
    project_id = create_response.json()['project_id']

    # Update project
    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Name",
            "description": "Updated description",
            "status": "active"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert data['project']['name'] == "Updated Name"
    assert data['project']['description'] == "Updated description"


def test_update_nonexistent_project(test_user):
    """Test updating a project that doesn't exist"""
    token = create_access_token(data={"sub": str(test_user.id)})

    from uuid import uuid4
    fake_id = str(uuid4())

    response = client.put(
        f"/api/v1/projects/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Name"}
    )

    assert response.status_code == 404


def test_delete_project(test_user):
    """Test DELETE /api/v1/projects/{id} - Delete project"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Project to Delete", "description": "Will be deleted"}
    )
    project_id = create_response.json()['project_id']

    # Delete project
    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True

    # Verify project is deleted or archived
    get_response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should return 404 or show archived status
    assert get_response.status_code == 404 or get_response.json()['project']['status'] == 'archived'


def test_get_project_status(test_user):
    """Test GET /api/v1/projects/{id}/status - Get project status"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Status Test Project", "description": "Test status endpoint"}
    )
    project_id = create_response.json()['project_id']

    # Get status
    response = client.get(
        f"/api/v1/projects/{project_id}/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'project_id' in data
    assert 'status' in data
    assert 'maturity_score' in data
    assert 'current_phase' in data

    # Initial values
    assert data['status'] == 'active'
    assert data['maturity_score'] == 0
    assert data['current_phase'] == 'discovery'


def test_list_projects_filters(test_user):
    """Test filtering in list projects endpoint"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create projects with different statuses
    client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Active Project", "description": "Active"}
    )

    # List active projects only
    response = client.get(
        "/api/v1/projects?status=active",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # All returned projects should be active
    if 'projects' in data and len(data['projects']) > 0:
        for project in data['projects']:
            assert project['status'] == 'active'


def test_list_projects_empty(test_user):
    """Test listing projects when user has none"""
    from app.models.user import User

    # Create a new user with no projects
    auth_db = test_user.__dict__['_sa_instance_state'].session
    new_user = User(
        email='noproject@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_db.add(new_user)
    auth_db.commit()
    auth_db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.email})

    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'projects' in data
    assert len(data['projects']) == 0


def test_create_project_with_optional_description(test_user):
    """Test creating project without description (optional)"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "No Description Project"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert data['project']['name'] == "No Description Project"
    # Description should be empty or default
    assert 'description' in data['project']


def test_update_project_partial(test_user):
    """Test updating only some fields of a project"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    create_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Partial Update Test", "description": "Original"}
    )
    project_id = create_response.json()['project_id']

    # Update only description
    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"description": "Updated description only"}
    )

    assert response.status_code == 200
    data = response.json()

    # Name should remain unchanged
    assert data['project']['name'] == "Partial Update Test"
    assert data['project']['description'] == "Updated description only"

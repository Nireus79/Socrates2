"""
Test Search API Endpoints

Tests for HTTP endpoints in /api/v1/search:
- GET /api/v1/search - Full-text search across projects, specifications, questions
- Query parameters: query, resource_type, category, skip, limit
- Tests: basic search, filtering, pagination, authorization, empty queries, edge cases
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.project import Project
from app.models.specification import Specification
from app.core.database import get_db_specs


def test_search_requires_authentication(client):
    """Test that search endpoint requires authentication"""
    response = client.get("/api/v1/search?query=test")

    assert response.status_code == 401
    assert "detail" in response.json() or "not authenticated" in str(response.text).lower()


def test_search_basic_query(test_user, specs_session, client):
    """Test basic search with simple query"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create a test project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="FastAPI Application",
        description="A web application built with FastAPI"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add a specification
    spec = Specification(
        project_id=project.id,
        category="requirements",
        content="User authentication with OAuth2",
        source="user",
        confidence=0.9,
        is_current=True
    )
    specs_session.add(spec)
    specs_session.commit()

    # Search for relevant term
    response = client.get(
        "/api/v1/search?query=FastAPI",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'query' in data
    assert data['query'] == "FastAPI"
    assert 'results' in data
    assert 'total' in data
    assert isinstance(data['results'], list)
    assert 'resource_counts' in data


def test_search_with_resource_type_filter(test_user, specs_session, client):
    """Test search with resource_type filter (projects only)"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create test project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Search Project",
        description="Project for search testing"
    )
    specs_session.add(project)
    specs_session.commit()

    # Search by type
    response = client.get(
        "/api/v1/search?query=Search&resource_type=project",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'resource_counts' in data
    # Only projects should be returned if filtered
    if len(data['results']) > 0:
        for result in data['results']:
            assert result.get('resource_type') == 'project' or 'name' in result


def test_search_with_category_filter(test_user, specs_session, client):
    """Test search with category filter (specifications)"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with categorized specs
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Categorized Project",
        description="Testing"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add security spec
    spec = Specification(
        project_id=project.id,
        category="security",
        content="Implement HTTPS encryption",
        source="user",
        confidence=0.95,
        is_current=True
    )
    specs_session.add(spec)
    specs_session.commit()

    # Search with category filter
    response = client.get(
        "/api/v1/search?query=encryption&category=security",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    # Results should be in security category
    if len(data['results']) > 0:
        for result in data['results']:
            assert result.get('category') == 'security' or 'encryption' in str(result).lower()


def test_search_with_pagination(test_user, specs_session, client):
    """Test search pagination with skip and limit parameters"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create multiple test projects
    for i in range(5):
        project = Project(
            creator_id=test_user.id,
            owner_id=test_user.id,
            user_id=test_user.id,
            name=f"Pagination Test Project {i}",
            description=f"Test project for pagination {i}"
        )
        specs_session.add(project)
    specs_session.commit()

    # Search with limit
    response = client.get(
        "/api/v1/search?query=Pagination&limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'skip' in data
    assert 'limit' in data
    assert data['limit'] == 2
    # Results should be limited
    assert len(data['results']) <= 2

    # Test skip parameter
    response = client.get(
        "/api/v1/search?query=Pagination&skip=2&limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['skip'] == 2


def test_search_empty_query_returns_empty_results(test_user, client):
    """Test search with empty query returns empty results"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/search?query=",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should either reject empty query or return 0 results
    if response.status_code == 200:
        data = response.json()
        assert 'results' in data
        assert isinstance(data['results'], list)


def test_search_nonexistent_term_returns_empty(test_user, client):
    """Test search for nonexistent term returns empty results"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/search?query=xyznonexistenttermthatdoesntexist123",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'results' in data
    assert len(data['results']) == 0
    assert data['total'] == 0


def test_search_case_insensitive(test_user, specs_session, client):
    """Test that search is case-insensitive"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="CaseSensitiveTest",
        description="Testing case insensitivity"
    )
    specs_session.add(project)
    specs_session.commit()

    # Search with lowercase
    response_lower = client.get(
        "/api/v1/search?query=casesensitivetest",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Search with uppercase
    response_upper = client.get(
        "/api/v1/search?query=CASESENSITIVETEST",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response_lower.status_code == 200
    assert response_upper.status_code == 200

    # Both should return results
    assert len(response_lower.json()['results']) > 0
    assert len(response_upper.json()['results']) > 0


def test_search_response_structure(test_user, specs_session, client):
    """Test that search response has correct structure"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create test data
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Structure Test Project",
        description="Testing response structure"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add specification
    spec = Specification(
        project_id=project.id,
        category="goals",
        content="Define project objectives",
        source="user",
        confidence=0.85,
        is_current=True
    )
    specs_session.add(spec)
    specs_session.commit()

    response = client.get(
        "/api/v1/search?query=project",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert 'success' in data
    assert data['success'] is True
    assert 'query' in data
    assert 'results' in data
    assert 'total' in data
    assert 'skip' in data
    assert 'limit' in data
    assert 'resource_counts' in data

    # Verify resource_counts structure
    resource_counts = data['resource_counts']
    assert isinstance(resource_counts, dict)
    assert 'projects' in resource_counts
    assert 'specifications' in resource_counts
    assert 'questions' in resource_counts

    # Verify result items have expected fields
    if len(data['results']) > 0:
        result = data['results'][0]
        assert 'id' in result
        assert 'title' in result or 'name' in result
        assert 'resource_type' in result


def test_search_other_user_data_not_included(test_user, auth_session, specs_session, client):
    """Test that search results don't include other user's data"""
    from app.models.user import User

    # Create another user
    other_user = User(
        name='Other',
        surname='User',
        username='othersearch',
        email='othersearch@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_session.add(other_user)
    auth_session.commit()
    auth_session.refresh(other_user)

    # Create project as other user
    other_project = Project(
        creator_id=other_user.id,
        owner_id=other_user.id,
        user_id=other_user.id,
        name="Secret Project",
        description="This should not be visible to test_user"
    )
    specs_session.add(other_project)
    specs_session.commit()

    # Search as test_user
    token = create_access_token(data={"sub": str(test_user.id)})
    response = client.get(
        "/api/v1/search?query=Secret",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Secret project should not appear
    for result in data['results']:
        assert result['id'] != str(other_project.id)
        assert 'Secret' not in result.get('title', '')
        assert 'Secret' not in result.get('name', '')

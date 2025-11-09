"""
Test Templates API Endpoints

Tests for HTTP endpoints in /api/v1/templates:
- GET /api/v1/templates - List available project templates with filtering
- GET /api/v1/templates/{template_id} - Get template details with preview specs
- POST /api/v1/templates/{template_id}/apply - Apply template to project
- Tests: listing, filtering, pagination, authorization, application, edge cases
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.project import Project
from app.models.specification import Specification


def test_list_templates_requires_authentication(client):
    """Test that listing templates requires authentication"""
    response = client.get("/api/v1/templates")

    assert response.status_code == 401
    assert "detail" in response.json() or "not authenticated" in str(response.text).lower()


def test_apply_template_requires_authentication(test_user, specs_session, client):
    """Test that applying template requires authentication"""
    # Create a project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Test Project",
        description="For template test"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Try to apply template without auth
    response = client.post(
        "/api/v1/templates/template-web-app/apply?project_id=" + str(project.id)
    )

    assert response.status_code == 401


def test_list_templates_basic(test_user, client):
    """Test basic template listing"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/templates",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'templates' in data
    assert isinstance(data['templates'], list)
    assert len(data['templates']) > 0, "Should have at least one built-in template"

    # Verify template structure
    for template in data['templates']:
        assert 'id' in template
        assert 'name' in template
        assert 'description' in template
        assert 'use_case' in template
        assert 'categories' in template
        assert 'estimated_specs' in template
        assert 'difficulty' in template
        assert 'tags' in template


def test_list_templates_pagination(test_user, client):
    """Test template listing with pagination"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Request with limit
    response = client.get(
        "/api/v1/templates?limit=1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'skip' in data
    assert 'limit' in data
    assert data['limit'] == 1
    assert len(data['templates']) <= 1

    # Request with skip
    response = client.get(
        "/api/v1/templates?skip=1&limit=1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['skip'] == 1
    assert len(data['templates']) <= 1


def test_list_templates_filter_by_tags(test_user, client):
    """Test filtering templates by tags"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Filter by 'web' tag
    response = client.get(
        "/api/v1/templates?tags=web",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'templates' in data

    # All returned templates should have 'web' tag or similar
    for template in data['templates']:
        assert 'tags' in template
        assert isinstance(template['tags'], list)


def test_list_templates_filter_by_industry(test_user, client):
    """Test filtering templates by industry"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Filter by industry
    response = client.get(
        "/api/v1/templates?industry=SaaS",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'templates' in data

    # Returned templates should match industry or be generic (Any)
    for template in data['templates']:
        assert template.get('industry') in ['SaaS', 'Any']


def test_get_template_details(test_user, client):
    """Test getting template details with preview specifications"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # First, list templates to get a valid ID
    list_response = client.get(
        "/api/v1/templates",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert list_response.status_code == 200
    templates = list_response.json()['templates']
    assert len(templates) > 0

    template_id = templates[0]['id']

    # Get template details
    response = client.get(
        f"/api/v1/templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'template' in data
    assert 'preview_specs' in data

    # Verify template structure
    template = data['template']
    assert template['id'] == template_id
    assert 'name' in template
    assert 'categories' in template

    # Verify preview specs
    preview_specs = data['preview_specs']
    assert isinstance(preview_specs, list)
    # Should have some preview specs from categories
    assert len(preview_specs) > 0

    # Each preview spec should have category and content
    for spec in preview_specs:
        assert 'category' in spec
        assert 'content' in spec


def test_get_template_nonexistent(test_user, client):
    """Test getting nonexistent template returns 404"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/templates/nonexistent-template-id",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_apply_template_requires_authentication(test_user, specs_db, client):
    """Test that applying template requires authentication"""
    # Create a project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Test Project",
        description="For template test"
    )
    specs_db.add(project)
    specs_db.commit()
    specs_db.refresh(project)

    # Try to apply template without auth
    response = client.post(
        "/api/v1/templates/template-web-app/apply?project_id=" + str(project.id)
    )

    assert response.status_code == 401


def test_apply_template_to_project(test_user, specs_session, client):
    """Test applying a template to a project creates specifications"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create a project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Template Test Project",
        description="Testing template application"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Apply template
    response = client.post(
        f"/api/v1/templates/template-web-app/apply?project_id={project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'project_id' in data
    assert data['project_id'] == str(project.id)
    assert 'specs_created' in data
    assert data['specs_created'] > 0, "Template should create specifications"
    assert 'message' in data

    # Verify specifications were created
    specs = specs_session.query(Specification).where(
        Specification.project_id == project.id
    ).all()

    assert len(specs) > 0
    assert len(specs) == data['specs_created']

    # Verify specs have expected properties
    for spec in specs:
        assert spec.project_id == project.id
        assert spec.category is not None
        assert spec.content is not None
        assert spec.is_current is True
        assert spec.source == "template"


def test_apply_template_requires_authorization(test_user, auth_session, specs_session, client):
    """Test that users can only apply templates to their own projects"""
    from app.models.user import User

    # Create another user's project
    other_user = User(
        email='othertemplate@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_session.add(other_user)
    auth_session.commit()
    auth_session.refresh(other_user)

    other_project = Project(
        creator_id=other_user.id,
        owner_id=other_user.id,
        user_id=other_user.id,
        name="Other User's Project",
        description="Should not allow template application"
    )
    specs_session.add(other_project)
    specs_session.commit()
    specs_session.refresh(other_project)

    # Try to apply template to other user's project
    token = create_access_token(data={"sub": str(test_user.id)})
    response = client.post(
        f"/api/v1/templates/template-web-app/apply?project_id={other_project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_apply_template_to_nonexistent_project(test_user, client):
    """Test applying template to nonexistent project returns 404"""
    token = create_access_token(data={"sub": str(test_user.id)})

    from uuid import uuid4
    fake_id = str(uuid4())

    response = client.post(
        f"/api/v1/templates/template-web-app/apply?project_id={fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_apply_nonexistent_template(test_user, specs_session, client):
    """Test applying nonexistent template returns 404"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create a project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Valid Project",
        description="For testing"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Apply nonexistent template
    response = client.post(
        f"/api/v1/templates/nonexistent-template/apply?project_id={project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_list_templates_total_count(test_user, client):
    """Test that template list returns correct total count"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/templates",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert 'total' in data
    assert data['total'] > 0
    # Total should match or exceed returned templates
    assert data['total'] >= len(data['templates'])


def test_template_categories_structure(test_user, client):
    """Test that template categories have correct structure"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/templates",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    for template in data['templates']:
        assert 'categories' in template
        assert isinstance(template['categories'], list)
        assert len(template['categories']) > 0

        for category in template['categories']:
            assert 'name' in category
            assert 'description' in category
            assert 'examples' in category
            assert isinstance(category['examples'], list)
            assert len(category['examples']) > 0


def test_apply_template_specs_have_correct_properties(test_user, specs_session, client):
    """Test that template-created specs have expected properties"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Property Test Project",
        description="Testing"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Apply template
    response = client.post(
        f"/api/v1/templates/template-web-app/apply?project_id={project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    # Get created specs
    specs = specs_session.query(Specification).where(
        Specification.project_id == project.id
    ).all()

    # Verify all specs have required properties
    for spec in specs:
        assert spec.project_id == project.id
        assert spec.category is not None
        assert spec.content is not None
        assert spec.source == "template"
        assert spec.confidence is not None
        assert spec.confidence > 0, "Template specs should have positive confidence"
        assert spec.is_current is True
        assert spec.created_at is not None


def test_template_filtering_combination(test_user, client):
    """Test combining multiple filters when listing templates"""
    token = create_access_token(data={"sub": str(test_user.id)})

    response = client.get(
        "/api/v1/templates?industry=SaaS&tags=web&limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'templates' in data
    assert data['limit'] == 5

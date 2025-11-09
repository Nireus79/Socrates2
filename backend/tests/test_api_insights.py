"""
Test Insights API Endpoints

Tests for HTTP endpoints in /api/v1/insights:
- GET /api/v1/insights/{project_id} - Project analysis with gaps, risks, opportunities
- Query parameters: insight_type (gaps, risks, opportunities, all)
- Tests: gap detection, risk identification, opportunity highlighting, authorization, edge cases
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.project import Project
from app.models.specification import Specification


def test_insights_requires_authentication(test_user, specs_session, client):
    """Test that insights endpoint requires authentication"""
    # Create a project to get its ID
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Test Project",
        description="For testing"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Try without token
    response = client.get(f"/api/v1/insights/{project.id}")

    assert response.status_code == 401
    assert "detail" in response.json() or "not authenticated" in str(response.text).lower()


def test_insights_requires_authorization(test_user, auth_session, specs_session, client):
    """Test that users can only access their own project insights"""
    from app.models.user import User

    # Create another user
    other_user = User(
        name='Other',
        surname='User',
        username='otherinsights',
        email='otherinsights@example.com',
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
        name="Other User Project",
        description="Private"
    )
    specs_session.add(other_project)
    specs_session.commit()

    # Try to access as test_user
    token = create_access_token(data={"sub": str(test_user.id)})
    response = client.get(
        f"/api/v1/insights/{other_project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_insights_nonexistent_project(test_user, client):
    """Test insights on nonexistent project returns 404"""
    token = create_access_token(data={"sub": str(test_user.id)})

    from uuid import uuid4
    fake_id = str(uuid4())

    response = client.get(
        f"/api/v1/insights/{fake_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_insights_gap_detection(test_user, specs_session, client):
    """Test that insights correctly identify specification gaps"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with minimal specs
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Incomplete Project",
        description="Missing many categories"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add only goals spec
    spec = Specification(
        project_id=project.id,
        category="goals",
        content="Build a web app",
        source="user",
        confidence=0.9,
        is_current=True
    )
    specs_session.add(spec)
    specs_session.commit()

    # Get insights
    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    assert 'insights' in data
    assert 'summary' in data

    # Should detect gaps for missing categories
    gaps = [i for i in data['insights'] if i['type'] == 'gap']
    assert len(gaps) > 0, "Should detect missing specification categories"

    # Verify gap structure
    for gap in gaps:
        assert 'title' in gap
        assert 'description' in gap
        assert 'severity' in gap
        assert 'recommendations' in gap
        assert isinstance(gap['recommendations'], list)


def test_insights_risk_detection_low_confidence(test_user, specs_session, client):
    """Test that insights detect low-confidence specs as risks"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with low-confidence specs
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Risky Project",
        description="Has low confidence specs"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add specs with low confidence
    for i in range(3):
        spec = Specification(
            project_id=project.id,
            category="requirements",
            content=f"Uncertain requirement {i}",
            source="user",
            confidence=0.5,  # Low confidence
            is_current=True
        )
        specs_session.add(spec)
    specs_session.commit()

    # Get insights
    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True

    # Should detect risks for low-confidence specs
    risks = [i for i in data['insights'] if i['type'] == 'risk']
    assert len(risks) > 0, "Should detect low-confidence specification risks"

    # Verify risk structure
    for risk in risks:
        assert 'title' in risk
        assert 'description' in risk
        assert 'severity' in risk
        assert 'recommendations' in risk


def test_insights_opportunity_detection(test_user, specs_session, client):
    """Test that insights detect well-specified areas as opportunities"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with many specs in one category
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Well Specified Project",
        description="Has detailed specs"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add many high-confidence security specs
    for i in range(6):
        spec = Specification(
            project_id=project.id,
            category="security",
            content=f"Security requirement {i}",
            source="user",
            confidence=0.95,
            is_current=True
        )
        specs_session.add(spec)
    specs_session.commit()

    # Get insights
    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True

    # Should detect opportunities for well-covered categories
    opportunities = [i for i in data['insights'] if i['type'] == 'opportunity']
    assert len(opportunities) > 0, "Should detect well-specified areas as opportunities"

    # Verify opportunity structure
    for opp in opportunities:
        assert 'title' in opp
        assert 'description' in opp
        assert 'recommendations' in opp


def test_insights_filter_by_type_gaps(test_user, specs_session, client):
    """Test filtering insights by type=gaps"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with gaps
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Gap Analysis Project",
        description="Testing"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add only one category
    spec = Specification(
        project_id=project.id,
        category="goals",
        content="Project goal",
        source="user",
        confidence=0.9,
        is_current=True
    )
    specs_session.add(spec)
    specs_session.commit()

    # Get insights with filter
    response = client.get(
        f"/api/v1/insights/{project.id}?insight_type=gaps",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should only contain gaps
    for insight in data['insights']:
        assert insight['type'] == 'gap'


def test_insights_response_structure(test_user, specs_session, client):
    """Test that insights response has correct structure"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project
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

    # Add some specs
    for i in range(3):
        spec = Specification(
            project_id=project.id,
            category="requirements",
            content=f"Requirement {i}",
            source="user",
            confidence=0.85,
            is_current=True
        )
        specs_session.add(spec)
    specs_session.commit()

    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify main response structure
    assert 'success' in data
    assert data['success'] is True
    assert 'project_id' in data
    assert 'project_name' in data
    assert 'insights' in data
    assert 'summary' in data

    # Verify insights structure
    assert isinstance(data['insights'], list)
    for insight in data['insights']:
        assert 'type' in insight
        assert insight['type'] in ['gap', 'risk', 'opportunity']
        assert 'title' in insight
        assert 'description' in insight
        assert 'severity' in insight
        assert 'recommendations' in insight
        assert isinstance(insight['recommendations'], list)

    # Verify summary structure
    summary = data['summary']
    assert 'total_insights' in summary
    assert 'gaps_count' in summary
    assert 'risks_count' in summary
    assert 'opportunities_count' in summary
    assert 'coverage_percentage' in summary
    assert 'most_covered_category' in summary
    assert 'least_covered_category' in summary

    # Verify summary counts match insights
    assert summary['total_insights'] == len(data['insights'])
    assert summary['gaps_count'] == len([i for i in data['insights'] if i['type'] == 'gap'])
    assert summary['risks_count'] == len([i for i in data['insights'] if i['type'] == 'risk'])
    assert summary['opportunities_count'] == len([i for i in data['insights'] if i['type'] == 'opportunity'])


def test_insights_coverage_percentage(test_user, specs_session, client):
    """Test that coverage percentage is calculated correctly"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with only goals specs
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Partial Coverage Project",
        description="Testing coverage calculation"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add specs for only 2 out of 10 expected categories
    for category in ['goals', 'requirements']:
        spec = Specification(
            project_id=project.id,
            category=category,
            content=f"{category} spec",
            source="user",
            confidence=0.9,
            is_current=True
        )
        specs_session.add(spec)
    specs_session.commit()

    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    summary = data['summary']
    # Coverage should be around 20% (2 out of 10 categories)
    assert 0 <= summary['coverage_percentage'] <= 100
    assert summary['coverage_percentage'] > 0  # Should have some coverage


def test_insights_empty_project(test_user, specs_session, client):
    """Test insights on project with no specifications"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create empty project
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Empty Project",
        description="No specifications yet"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data['success'] is True
    # Should detect gaps for all missing categories
    gaps = [i for i in data['insights'] if i['type'] == 'gap']
    assert len(gaps) > 0, "Empty project should have many gaps"

    # Coverage should be 0
    assert data['summary']['coverage_percentage'] == 0.0


def test_insights_recommendations_present(test_user, specs_session, client):
    """Test that all insights include actionable recommendations"""
    token = create_access_token(data={"sub": str(test_user.id)})

    # Create project with mixed specs
    project = Project(
        creator_id=test_user.id,
        owner_id=test_user.id,
        user_id=test_user.id,
        name="Recommendations Test",
        description="Testing"
    )
    specs_session.add(project)
    specs_session.commit()
    specs_session.refresh(project)

    # Add one spec
    spec = Specification(
        project_id=project.id,
        category="goals",
        content="Define project goals",
        source="user",
        confidence=0.9,
        is_current=True
    )
    specs_session.add(spec)
    specs_session.commit()

    response = client.get(
        f"/api/v1/insights/{project.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Every insight should have at least one recommendation
    for insight in data['insights']:
        assert 'recommendations' in insight
        assert isinstance(insight['recommendations'], list)
        assert len(insight['recommendations']) > 0, f"Insight '{insight['title']}' has no recommendations"

        # Each recommendation should be non-empty string
        for rec in insight['recommendations']:
            assert isinstance(rec, str)
            assert len(rec) > 0

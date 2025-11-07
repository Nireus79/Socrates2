"""
Test Phase 8 - Team Collaboration

Tests for:
- TeamCollaborationAgent
- Team creation and management
- Team member roles and permissions
- Project sharing with teams
- Team activity tracking
"""
import pytest
from uuid import uuid4

from app.agents.team_collaboration import TeamCollaborationAgent
from app.models import User, Project, Team, TeamMember, ProjectShare


def test_team_collaboration_agent_capabilities(service_container):
    """Test TeamCollaborationAgent exposes correct capabilities"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    capabilities = agent.get_capabilities()

    assert 'create_team' in capabilities
    assert 'add_team_member' in capabilities
    assert 'remove_team_member' in capabilities
    assert 'create_team_project' in capabilities
    assert 'share_project' in capabilities
    assert 'get_team_details' in capabilities
    assert 'get_team_activity' in capabilities


def test_create_team(service_container, test_user):
    """Test creating a team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    result = agent.process_request('create_team', {
        'name': 'Engineering Team',
        'description': 'Core engineering team for Socrates2',
        'created_by': str(test_user.id)
    })

    assert result['success'] is True
    assert 'team_id' in result

    # Verify team was created
    auth_db = service_container.get_database_auth()
    team = auth_db.query(Team).filter(Team.id == result['team_id']).first()

    assert team is not None
    assert team.name == 'Engineering Team'
    assert team.created_by == test_user.id

    # Creator should be added as owner
    member = auth_db.query(TeamMember).filter(
        TeamMember.team_id == team.id,
        TeamMember.user_id == test_user.id
    ).first()

    assert member is not None
    assert member.role == 'owner'

    auth_db.close()


def test_add_team_member(service_container, test_user):
    """Test adding a member to a team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team first
    team_result = agent.process_request('create_team', {
        'name': 'Test Team',
        'description': 'Team for testing',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Create another user
    auth_db = service_container.get_database_auth()
    new_user = User(
        email='newmember@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_db.add(new_user)
    auth_db.commit()
    auth_db.refresh(new_user)
    auth_db.close()

    # Add new user as member
    result = agent.process_request('add_team_member', {
        'team_id': team_id,
        'user_id': str(new_user.id),
        'role': 'member',
        'added_by': str(test_user.id)
    })

    assert result['success'] is True

    # Verify member was added
    auth_db = service_container.get_database_auth()
    member = auth_db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == new_user.id
    ).first()

    assert member is not None
    assert member.role == 'member'

    auth_db.close()


def test_remove_team_member(service_container, test_user):
    """Test removing a member from a team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Setup: Create team and add a member
    team_result = agent.process_request('create_team', {
        'name': 'Test Team',
        'description': 'Team for testing',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    auth_db = service_container.get_database_auth()
    member_user = User(
        email='member@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_db.add(member_user)
    auth_db.commit()
    auth_db.refresh(member_user)
    auth_db.close()

    agent.process_request('add_team_member', {
        'team_id': team_id,
        'user_id': str(member_user.id),
        'role': 'member',
        'added_by': str(test_user.id)
    })

    # Remove the member
    result = agent.process_request('remove_team_member', {
        'team_id': team_id,
        'user_id': str(member_user.id),
        'removed_by': str(test_user.id)
    })

    assert result['success'] is True

    # Verify member was removed
    auth_db = service_container.get_database_auth()
    member = auth_db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == member_user.id
    ).first()

    assert member is None

    auth_db.close()


def test_create_team_project(service_container, test_user):
    """Test creating a project for a team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team first
    team_result = agent.process_request('create_team', {
        'name': 'Dev Team',
        'description': 'Development team',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Create team project
    result = agent.process_request('create_team_project', {
        'team_id': team_id,
        'name': 'Team Project Alpha',
        'description': 'Collaborative project for the team',
        'created_by': str(test_user.id)
    })

    assert result['success'] is True
    assert 'project_id' in result

    # Verify project was created
    specs_db = service_container.get_database_specs()
    project = specs_db.query(Project).filter(Project.id == result['project_id']).first()

    assert project is not None
    assert project.name == 'Team Project Alpha'

    specs_db.close()


def test_share_project(service_container, test_user, test_project):
    """Test sharing an existing project with a team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team
    team_result = agent.process_request('create_team', {
        'name': 'Share Team',
        'description': 'Team to share with',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Share project with team
    result = agent.process_request('share_project', {
        'project_id': str(test_project.id),
        'team_id': team_id,
        'permission_level': 'read',
        'shared_by': str(test_user.id)
    })

    assert result['success'] is True
    assert 'share_id' in result

    # Verify share was created
    specs_db = service_container.get_database_specs()
    share = specs_db.query(ProjectShare).filter(
        ProjectShare.project_id == test_project.id,
        ProjectShare.team_id == team_id
    ).first()

    assert share is not None
    assert share.permission_level == 'read'

    specs_db.close()


def test_get_team_details(service_container, test_user):
    """Test getting team details"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team with members
    team_result = agent.process_request('create_team', {
        'name': 'Details Team',
        'description': 'Team for getting details',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Add a member
    auth_db = service_container.get_database_auth()
    member_user = User(
        email='details_member@example.com',
        hashed_password='fake_hash',
        status='active',
        role='user'
    )
    auth_db.add(member_user)
    auth_db.commit()
    auth_db.refresh(member_user)
    auth_db.close()

    agent.process_request('add_team_member', {
        'team_id': team_id,
        'user_id': str(member_user.id),
        'role': 'member',
        'added_by': str(test_user.id)
    })

    # Get details
    result = agent.process_request('get_team_details', {
        'team_id': team_id
    })

    assert result['success'] is True
    assert 'team' in result
    assert result['team']['name'] == 'Details Team'
    assert 'members' in result
    assert len(result['members']) == 2  # Owner + member


def test_get_team_activity(service_container, test_user, test_project):
    """Test getting team activity"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team
    team_result = agent.process_request('create_team', {
        'name': 'Activity Team',
        'description': 'Team for activity tracking',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Share a project
    agent.process_request('share_project', {
        'project_id': str(test_project.id),
        'team_id': team_id,
        'permission_level': 'write',
        'shared_by': str(test_user.id)
    })

    # Get activity
    result = agent.process_request('get_team_activity', {
        'team_id': team_id
    })

    assert result['success'] is True
    assert 'team_members' in result
    assert 'shared_projects' in result
    assert len(result['shared_projects']) > 0


def test_create_team_validation(service_container, test_user):
    """Test validation in create_team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Missing name
    result = agent.process_request('create_team', {
        'description': 'Team without name',
        'created_by': str(test_user.id)
    })

    assert result['success'] is False
    assert 'error' in result or 'error_code' in result


def test_add_member_validation(service_container, test_user):
    """Test validation in add_team_member"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team
    team_result = agent.process_request('create_team', {
        'name': 'Test Team',
        'description': 'Team for testing',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Try to add member with invalid user_id
    result = agent.process_request('add_team_member', {
        'team_id': team_id,
        'user_id': str(uuid4()),  # Doesn't exist
        'role': 'member',
        'added_by': str(test_user.id)
    })

    assert result['success'] is False
    assert 'error' in result or 'error_code' in result


def test_share_project_validation(service_container, test_user):
    """Test validation in share_project"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Try to share non-existent project
    result = agent.process_request('share_project', {
        'project_id': str(uuid4()),  # Doesn't exist
        'team_id': str(uuid4()),
        'permission_level': 'read',
        'shared_by': str(test_user.id)
    })

    assert result['success'] is False
    assert 'error' in result or 'error_code' in result


def test_remove_team_owner(service_container, test_user):
    """Test that owner cannot be removed from team"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team
    team_result = agent.process_request('create_team', {
        'name': 'Owner Test Team',
        'description': 'Team for owner removal test',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Try to remove the owner
    result = agent.process_request('remove_team_member', {
        'team_id': team_id,
        'user_id': str(test_user.id),  # The owner
        'removed_by': str(test_user.id)
    })

    # Should fail or prevent removal
    assert result['success'] is False or result.get('error_code') == 'CANNOT_REMOVE_OWNER'


def test_permission_levels(service_container, test_user, test_project):
    """Test different permission levels for shared projects"""
    agent = TeamCollaborationAgent("team", "Team Collaboration", service_container)

    # Create team
    team_result = agent.process_request('create_team', {
        'name': 'Permission Team',
        'description': 'Team for permission testing',
        'created_by': str(test_user.id)
    })
    team_id = team_result['team_id']

    # Test read permission
    result = agent.process_request('share_project', {
        'project_id': str(test_project.id),
        'team_id': team_id,
        'permission_level': 'read',
        'shared_by': str(test_user.id)
    })
    assert result['success'] is True

    # Verify permission level
    specs_db = service_container.get_database_specs()
    share = specs_db.query(ProjectShare).filter(
        ProjectShare.project_id == test_project.id
    ).first()

    assert share.permission_level == 'read'
    specs_db.close()

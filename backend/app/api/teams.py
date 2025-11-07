"""
Teams API endpoints.

Provides:
- Create teams
- Manage team members
- Create team projects
- Share projects with teams
- View team activity
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


class CreateTeamRequest(BaseModel):
    """Request model for creating a team."""
    name: str
    description: Optional[str] = ""


class AddMemberRequest(BaseModel):
    """Request model for adding a team member."""
    user_id: str  # UUID as string
    role: str  # owner, lead, developer, viewer


class CreateTeamProjectRequest(BaseModel):
    """Request model for creating a team project."""
    name: str
    description: Optional[str] = ""


class ShareProjectRequest(BaseModel):
    """Request model for sharing a project."""
    team_id: str  # UUID as string
    permission_level: str = "read"  # read, write, admin


@router.post("")
def create_team(
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Create a new team.

    Args:
        request: Team creation details
        current_user: Authenticated user (becomes team owner)
        db: Database session

    Returns:
        {
            'success': bool,
            'team_id': str,
            'name': str
        }

    Example:
        POST /api/v1/teams
        Authorization: Bearer <token>
        {
            "name": "Engineering Team",
            "description": "Our development team"
        }

        Response:
        {
            "success": true,
            "team_id": "abc-123",
            "name": "Engineering Team"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='create_team',
        data={
            'name': request.name,
            'description': request.description,
            'created_by': current_user.id
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to create team')
        )

    return result


@router.get("")
def list_user_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    List all teams the current user is a member of.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'teams': List[dict]
        }

    Example:
        GET /api/v1/teams
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "teams": [
                {
                    "team_id": "abc-123",
                    "name": "Engineering Team",
                    "role": "owner",
                    ...
                }
            ]
        }
    """
    from ..models.team_member import TeamMember
    from ..models.team import Team

    # Get all team memberships for this user
    memberships = db.query(TeamMember).filter_by(user_id=current_user.id).all()

    teams_data = []
    for membership in memberships:
        team = db.query(Team).filter_by(id=membership.team_id).first()
        if team:
            teams_data.append({
                'team_id': str(team.id),
                'name': team.name,
                'description': team.description,
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat()
            })

    return {
        'success': True,
        'teams': teams_data
    }


@router.get("/{team_id}")
def get_team_details(
    team_id: str = Path(..., description="Team ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Get team details including members.

    Args:
        team_id: Team UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'team': dict,
            'members': List[dict]
        }

    Example:
        GET /api/v1/teams/abc-123
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "team": {
                "id": "abc-123",
                "name": "Engineering Team",
                ...
            },
            "members": [
                {
                    "user_id": "user-1",
                    "email": "user@example.com",
                    "role": "owner",
                    ...
                }
            ]
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='get_team_details',
        data={'team_id': team_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 400,
            detail=result.get('error', 'Failed to get team details')
        )

    return result


@router.post("/{team_id}/members")
def add_team_member(
    team_id: str,
    request: AddMemberRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Add a member to the team.

    Only owners and leads can invite new members.

    Args:
        team_id: Team UUID
        request: Member details (user_id, role)
        current_user: Authenticated user (must be owner/lead)
        db: Database session

    Returns:
        {
            'success': bool,
            'member_id': str,
            'role': str
        }

    Example:
        POST /api/v1/teams/abc-123/members
        Authorization: Bearer <token>
        {
            "user_id": "user-456",
            "role": "developer"
        }

        Response:
        {
            "success": true,
            "member_id": "member-789",
            "role": "developer"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='add_team_member',
        data={
            'team_id': team_id,
            'user_id': request.user_id,
            'role': request.role,
            'invited_by': current_user.id
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to add team member')
        if 'permission denied' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        elif 'already exists' in error.lower():
            raise HTTPException(status_code=409, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@router.delete("/{team_id}/members/{user_id}")
def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_auth)
) -> Dict[str, Any]:
    """
    Remove a member from the team.

    Only owners can remove members.

    Args:
        team_id: Team UUID
        user_id: User UUID to remove
        current_user: Authenticated user (must be owner)
        db: Database session

    Returns:
        {
            'success': bool,
            'removed_user_id': str
        }

    Example:
        DELETE /api/v1/teams/abc-123/members/user-456
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "removed_user_id": "user-456"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='remove_team_member',
        data={
            'team_id': team_id,
            'user_id': user_id,
            'removed_by': current_user.id
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to remove team member')
        if 'permission denied' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        elif 'not found' in error.lower():
            raise HTTPException(status_code=404, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@router.post("/{team_id}/projects")
def create_team_project(
    team_id: str,
    request: CreateTeamProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Create a project owned by the team.

    All team members can create team projects.

    Args:
        team_id: Team UUID
        request: Project details (name, description)
        current_user: Authenticated user (must be team member)
        db_auth: Auth database session
        db_specs: Specs database session

    Returns:
        {
            'success': bool,
            'project_id': str,
            'team_id': str
        }

    Example:
        POST /api/v1/teams/abc-123/projects
        Authorization: Bearer <token>
        {
            "name": "Team Project",
            "description": "Collaborative project"
        }

        Response:
        {
            "success": true,
            "project_id": "proj-456",
            "team_id": "abc-123"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='create_team_project',
        data={
            'team_id': team_id,
            'name': request.name,
            'description': request.description,
            'created_by': current_user.id
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to create team project')
        if 'permission denied' in error.lower() or 'not a team member' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@router.get("/{team_id}/activity")
def get_team_activity(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get team activity summary.

    Args:
        team_id: Team UUID
        current_user: Authenticated user
        db_auth: Auth database session
        db_specs: Specs database session

    Returns:
        {
            'success': bool,
            'team_members': List[dict],
            'shared_projects': List[dict]
        }

    Example:
        GET /api/v1/teams/abc-123/activity
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "team_members": [...],
            "shared_projects": [...]
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='get_team_activity',
        data={'team_id': team_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to get team activity')
        )

    return result


# Project endpoints (under /api/v1/projects prefix in separate router)
projects_router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    description: Optional[str] = ""


class CreateSessionRequest(BaseModel):
    """Request model for creating a session."""
    mode: str = "socratic"  # socratic or direct_chat


@projects_router.post("")
def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Create a new project for the current user.

    Args:
        request: Project creation details (name, description)
        current_user: Authenticated user (becomes project owner)
        db_specs: Specs database session

    Returns:
        {
            'id': str,
            'name': str,
            'description': str,
            'user_id': str,
            'status': str,
            'created_at': str
        }

    Example:
        POST /api/v1/projects
        Authorization: Bearer <token>
        {
            "name": "My Project",
            "description": "A cool project"
        }

        Response:
        {
            "id": "proj-123",
            "name": "My Project",
            "description": "A cool project",
            "user_id": "user-456",
            "status": "active",
            "created_at": "2025-11-07T12:00:00"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='create_project',
        data={
            'user_id': str(current_user.id),
            'name': request.name,
            'description': request.description
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to create project')
        )

    return result


@projects_router.get("")
def list_projects(
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> List[Dict[str, Any]]:
    """
    List all projects for the current user.

    Args:
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        List of project dictionaries with id, name, description, etc.

    Example:
        GET /api/v1/projects
        Authorization: Bearer <token>

        Response:
        [
            {
                "id": "proj-123",
                "name": "My Project",
                "description": "A cool project",
                "user_id": "user-456",
                "status": "active",
                "created_at": "2025-11-07T12:00:00"
            }
        ]
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='list_projects',
        data={
            'user_id': str(current_user.id)
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to list projects')
        )

    # Return projects list (result['projects'] or empty list)
    return result.get('projects', [])


@projects_router.post("/{project_id}/sessions")
def create_session(
    project_id: str,
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Create a new session for a project.

    Args:
        project_id: Project UUID
        request: Session creation details (mode)
        current_user: Authenticated user (must own the project)
        db_specs: Specs database session

    Returns:
        {
            'id': str,
            'project_id': str,
            'mode': str,
            'status': str,
            'created_at': str
        }

    Example:
        POST /api/v1/projects/proj-123/sessions
        Authorization: Bearer <token>
        {
            "mode": "socratic"
        }

        Response:
        {
            "id": "session-789",
            "project_id": "proj-123",
            "mode": "socratic",
            "status": "active",
            "created_at": "2025-11-07T12:00:00"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='create_session',
        data={
            'project_id': project_id,
            'user_id': str(current_user.id),
            'mode': request.mode
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to create session')
        if 'not found' in error.lower():
            raise HTTPException(status_code=404, detail=error)
        elif 'permission denied' in error.lower() or 'not the owner' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@projects_router.post("/{project_id}/share")
def share_project(
    project_id: str,
    request: ShareProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Share a project with a team.

    Only project owner can share.

    Args:
        project_id: Project UUID
        request: Share details (team_id, permission_level)
        current_user: Authenticated user (must be project owner)
        db: Database session

    Returns:
        {
            'success': bool,
            'share_id': str
        }

    Example:
        POST /api/v1/projects/proj-123/share
        Authorization: Bearer <token>
        {
            "team_id": "team-456",
            "permission_level": "write"
        }

        Response:
        {
            "success": true,
            "share_id": "share-789"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='team',
        action='share_project',
        data={
            'project_id': project_id,
            'team_id': request.team_id,
            'shared_by': current_user.id,
            'permission_level': request.permission_level
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to share project')
        if 'permission denied' in error.lower() or 'only project owner' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        elif 'not found' in error.lower():
            raise HTTPException(status_code=404, detail=error)
        elif 'already shared' in error.lower():
            raise HTTPException(status_code=409, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result

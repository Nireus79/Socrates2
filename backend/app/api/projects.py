"""
Projects API endpoints.

Provides:
- Create projects
- List user's projects
- Get project details
- Update project
- Delete project
- Get project status/maturity

All CRUD operations are routed through the ProjectManagerAgent via the orchestrator.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..agents.orchestrator import get_orchestrator
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    description: Optional[str] = ""


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    maturity_score: Optional[int] = None


@router.post("")
def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new project.

    Args:
        request: Project details (name, description)
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'project_id': str,
            'project': dict
        }

    Example:
        POST /api/v1/projects
        Authorization: Bearer <token>
        {
            "name": "My Web App",
            "description": "A FastAPI web application"
        }

        Response:
        {
            "success": true,
            "project_id": "abc-123",
            "project": {
                "id": "abc-123",
                "name": "My Web App",
                "description": "A FastAPI web application",
                "current_phase": "discovery",
                "maturity_score": 0,
                "status": "active",
                ...
            }
        }
    """
    # Route through ProjectManagerAgent
    orchestrator = get_orchestrator()
    result = orchestrator.route_request(
        'project',
        'create_project',
        {
            'user_id': str(current_user.id),
            'name': request.name,
            'description': request.description or ''
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to create project')
        )

    return {
        'success': True,
        'project_id': result.get('project_id'),
        'project': result.get('project')
    }


@router.get("")
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List all projects for the current user.

    Args:
        skip: Number of projects to skip (pagination)
        limit: Maximum number of projects to return
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'projects': List[dict],
            'total': int,
            'skip': int,
            'limit': int
        }

    Example:
        GET /api/v1/projects?skip=0&limit=10
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "projects": [
                {
                    "id": "abc-123",
                    "name": "My Web App",
                    "maturity_score": 45,
                    ...
                },
                ...
            ],
            "total": 5,
            "skip": 0,
            "limit": 10
        }
    """
    # Route through ProjectManagerAgent
    orchestrator = get_orchestrator()
    result = orchestrator.route_request(
        'project',
        'list_projects',
        {
            'user_id': str(current_user.id),
            'skip': skip,
            'limit': limit
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=500,
            detail=result.get('error', 'Failed to list projects')
        )

    return {
        'success': True,
        'projects': result.get('projects', []),
        'total': result.get('count', 0),  # Agent returns 'count', API returns 'total'
        'skip': skip,
        'limit': limit
    }


@router.get("/{project_id}")
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get project details.

    Args:
        project_id: Project UUID
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'project': dict
        }

    Example:
        GET /api/v1/projects/abc-123
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "project": {
                "id": "abc-123",
                "name": "My Web App",
                "description": "A FastAPI web application",
                "current_phase": "discovery",
                "maturity_score": 45,
                "status": "active",
                "created_at": "2025-01-01T00:00:00Z",
                ...
            }
        }
    """
    # Route through ProjectManagerAgent
    orchestrator = get_orchestrator()
    result = orchestrator.route_request(
        'project',
        'get_project',
        {'project_id': project_id}
    )

    # Handle not found
    if not result.get('success'):
        error_code = result.get('error_code')
        if error_code == 'PROJECT_NOT_FOUND':
            raise HTTPException(
                status_code=404,
                detail=result.get('error', f'Project not found: {project_id}')
            )
        raise HTTPException(
            status_code=500,
            detail=result.get('error', 'Failed to get project')
        )

    # Validate permissions (user must have access to this project)
    project = result.get('project', {})
    if str(project.get('user_id')) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Permission denied: you don't have access to this project"
        )

    return {
        'success': True,
        'project': project
    }


@router.put("/{project_id}")
def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update project details.

    Args:
        project_id: Project UUID
        request: Fields to update
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'project': dict
        }

    Example:
        PUT /api/v1/projects/abc-123
        Authorization: Bearer <token>
        {
            "name": "Updated Project Name",
            "description": "Updated description"
        }

        Response:
        {
            "success": true,
            "project": {...}
        }
    """
    orchestrator = get_orchestrator()

    # First, get project to validate permissions
    get_result = orchestrator.route_request(
        'project',
        'get_project',
        {'project_id': project_id}
    )

    if not get_result.get('success'):
        error_code = get_result.get('error_code')
        if error_code == 'PROJECT_NOT_FOUND':
            raise HTTPException(
                status_code=404,
                detail=get_result.get('error', f'Project not found: {project_id}')
            )
        raise HTTPException(
            status_code=500,
            detail=get_result.get('error', 'Failed to get project')
        )

    # Validate permissions (only owner can update)
    project = get_result.get('project', {})
    if str(project.get('owner_id')) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Permission denied: only project owner can update project"
        )

    # Build update data (only include fields that are provided)
    update_data = {'project_id': project_id}
    if request.name is not None:
        update_data['name'] = request.name
    if request.description is not None:
        update_data['description'] = request.description
    if request.current_phase is not None:
        update_data['current_phase'] = request.current_phase
    if request.status is not None:
        update_data['status'] = request.status
    if request.maturity_score is not None:
        update_data['maturity_score'] = request.maturity_score

    # Route update through agent
    result = orchestrator.route_request(
        'project',
        'update_project',
        update_data
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=500,
            detail=result.get('error', 'Failed to update project')
        )

    return {
        'success': True,
        'project': result.get('project')
    }


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Delete (archive) a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'message': str
        }

    Example:
        DELETE /api/v1/projects/abc-123
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "message": "Project deleted"
        }
    """
    orchestrator = get_orchestrator()

    # First, get project to validate permissions
    get_result = orchestrator.route_request(
        'project',
        'get_project',
        {'project_id': project_id}
    )

    if not get_result.get('success'):
        error_code = get_result.get('error_code')
        if error_code == 'PROJECT_NOT_FOUND':
            raise HTTPException(
                status_code=404,
                detail=get_result.get('error', f'Project not found: {project_id}')
            )
        raise HTTPException(
            status_code=500,
            detail=get_result.get('error', 'Failed to get project')
        )

    # Validate permissions (only creator can delete)
    project = get_result.get('project', {})
    if str(project.get('creator_id')) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Permission denied: only project creator can delete project"
        )

    # Route delete through agent (archives the project)
    result = orchestrator.route_request(
        'project',
        'delete_project',
        {'project_id': project_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=500,
            detail=result.get('error', 'Failed to delete project')
        )

    return {
        'success': True,
        'message': 'Project deleted'
    }


@router.get("/{project_id}/status")
def get_project_status(
    project_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get project status including maturity score and phase.

    Args:
        project_id: Project UUID
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'status': str,
            'current_phase': str,
            'maturity_score': float
        }

    Example:
        GET /api/v1/projects/abc-123/status
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "status": "active",
            "current_phase": "discovery",
            "maturity_score": 45.5
        }
    """
    # Route through ProjectManagerAgent
    orchestrator = get_orchestrator()
    result = orchestrator.route_request(
        'project',
        'get_project',
        {'project_id': project_id}
    )

    # Handle not found
    if not result.get('success'):
        error_code = result.get('error_code')
        if error_code == 'PROJECT_NOT_FOUND':
            raise HTTPException(
                status_code=404,
                detail=result.get('error', f'Project not found: {project_id}')
            )
        raise HTTPException(
            status_code=500,
            detail=result.get('error', 'Failed to get project')
        )

    # Validate permissions
    project = result.get('project', {})
    if str(project.get('user_id')) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    # Extract and return status fields
    return {
        'success': True,
        'project_id': project_id,
        'status': project.get('status'),
        'current_phase': project.get('current_phase'),
        'maturity_score': project.get('maturity_score')
    }

"""
Projects API endpoints.

Provides:
- Create projects
- List user's projects
- Get project details
- Update project
- Delete project
- Get project status/maturity
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..agents.orchestrator import get_orchestrator

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


@router.post("")
def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Create a new project.

    Args:
        request: Project details (name, description)
        current_user: Authenticated user
        db: Database session

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
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='create_project',
        data={
            'user_id': current_user.id,
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


@router.get("")
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    List all projects for the current user.

    Args:
        skip: Number of projects to skip (pagination)
        limit: Maximum number of projects to return
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'projects': List[dict],
            'total': int
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
            "total": 5
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='list_projects',
        data={
            'user_id': current_user.id,
            'skip': skip,
            'limit': limit
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to list projects')
        )

    return result


@router.get("/{project_id}")
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get project details.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

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
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='get_project',
        data={
            'project_id': project_id,
            'user_id': current_user.id
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to get project')
        if 'not found' in error.lower():
            raise HTTPException(status_code=404, detail=error)
        elif 'permission denied' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@router.put("/{project_id}")
def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Update project details.

    Args:
        project_id: Project UUID
        request: Fields to update
        current_user: Authenticated user
        db: Database session

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

    # Build updates dict (only include fields that were provided)
    updates = {}
    if request.name is not None:
        updates['name'] = request.name
    if request.description is not None:
        updates['description'] = request.description
    if request.status is not None:
        updates['status'] = request.status
    if request.current_phase is not None:
        updates['current_phase'] = request.current_phase

    result = orchestrator.route_request(
        agent_id='project',
        action='update_project',
        data={
            'project_id': project_id,
            'user_id': current_user.id,
            'updates': updates
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to update project')
        if 'not found' in error.lower():
            raise HTTPException(status_code=404, detail=error)
        elif 'permission denied' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Delete (archive) a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'project_id': str
        }

    Example:
        DELETE /api/v1/projects/abc-123
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "project_id": "abc-123"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='project',
        action='delete_project',
        data={
            'project_id': project_id,
            'user_id': current_user.id
        }
    )

    if not result.get('success'):
        error = result.get('error', 'Failed to delete project')
        if 'not found' in error.lower():
            raise HTTPException(status_code=404, detail=error)
        elif 'permission denied' in error.lower():
            raise HTTPException(status_code=403, detail=error)
        else:
            raise HTTPException(status_code=400, detail=error)

    return result


@router.get("/{project_id}/status")
def get_project_status(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Get project status including maturity score and phase.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'project_id': str,
            'maturity_score': float,
            'current_phase': str,
            'status': str,
            'total_specs': int,
            'specs_by_category': dict
        }

    Example:
        GET /api/v1/projects/abc-123/status
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "project_id": "abc-123",
            "maturity_score": 45.5,
            "current_phase": "discovery",
            "status": "active",
            "total_specs": 25,
            "specs_by_category": {
                "goals": 8,
                "requirements": 12,
                "tech_stack": 5
            }
        }
    """
    from ..models.project import Project
    from ..models.specification import Specification

    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Verify user has access
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Count specifications by category
    specs = db.query(Specification).filter(Specification.project_id == project_id).all()
    specs_by_category = {}
    for spec in specs:
        category = spec.category
        specs_by_category[category] = specs_by_category.get(category, 0) + 1

    return {
        'success': True,
        'project_id': str(project.id),
        'maturity_score': float(project.maturity_score),
        'current_phase': project.current_phase,
        'status': project.status,
        'total_specs': len(specs),
        'specs_by_category': specs_by_category
    }

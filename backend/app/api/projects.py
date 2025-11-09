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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    # DEBUG - This should be first thing
    import os
    try:
        debug_file = os.path.join(os.path.dirname(__file__), '..', '..', 'debug_route.txt')
        with open(debug_file, 'a') as f:
            f.write(f"ROUTE REACHED: current_user={current_user}, request={request}\n")
    except Exception as e:
        pass
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
    # Create project directly in database
    from app.models.project import Project
    from sqlalchemy.exc import IntegrityError

    try:
        project = Project(
            creator_id=current_user.id,
            owner_id=current_user.id,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            'success': True,
            'project_id': str(project.id),
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'current_phase': project.current_phase,
                'maturity_score': project.maturity_score,
                'status': project.status,
                'creator_id': str(project.creator_id),
                'owner_id': str(project.owner_id),
                'user_id': str(project.user_id),
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            }
        }
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create project: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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
    from app.models.project import Project

    try:
        # Query projects where user_id = current_user.id
        query = db.query(Project).filter(Project.user_id == current_user.id)

        # Get total count
        total = query.count()

        # Get paginated results
        projects = query.offset(skip).limit(limit).all()

        # Convert to dict list
        projects_list = [
            {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'current_phase': project.current_phase,
                'maturity_score': project.maturity_score,
                'status': project.status,
                'creator_id': str(project.creator_id),
                'owner_id': str(project.owner_id),
                'user_id': str(project.user_id),
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            }
            for project in projects
        ]

        return {
            'success': True,
            'projects': projects_list,
            'total': total,
            'skip': skip,
            'limit': limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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
    from app.models.project import Project

    try:
        # First, check if project exists at all
        project = db.query(Project).filter(Project.id == project_id).first()

        # Return 404 if project doesn't exist
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # Then check if user has permission to view it
        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: you don't have access to this project"
            )

        # Return project
        return {
            'success': True,
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'current_phase': project.current_phase,
                'maturity_score': project.maturity_score,
                'status': project.status,
                'creator_id': str(project.creator_id),
                'owner_id': str(project.owner_id),
                'user_id': str(project.user_id),
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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
    from app.models.project import Project

    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()

        # Return 404 if not found
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # Only allow updates if user is owner (owner_id = current_user.id)
        if str(project.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: only project owner can update project"
            )

        # Update fields: name, description, current_phase, status, maturity_score
        if request.name is not None:
            project.name = request.name
        if request.description is not None:
            project.description = request.description
        if request.current_phase is not None:
            project.current_phase = request.current_phase
        if request.status is not None:
            project.status = request.status
        if request.maturity_score is not None:
            project.maturity_score = request.maturity_score

        # Commit changes
        db.commit()
        db.refresh(project)

        return {
            'success': True,
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'current_phase': project.current_phase,
                'maturity_score': project.maturity_score,
                'status': project.status,
                'creator_id': str(project.creator_id),
                'owner_id': str(project.owner_id),
                'user_id': str(project.user_id),
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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
    from app.models.project import Project

    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()

        # Return 404 if not found
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # Only allow deletion if user is creator (creator_id = current_user.id)
        if str(project.creator_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: only project creator can delete project"
            )

        # Delete project
        db.delete(project)
        db.commit()

        return {
            'success': True,
            'message': 'Project deleted'
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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
    from app.models.project import Project

    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()

        # Return 404 if not found
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # Verify user has access
        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        return {
            'success': True,
            'project_id': str(project.id),
            'status': project.status,
            'current_phase': project.current_phase,
            'maturity_score': project.maturity_score
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

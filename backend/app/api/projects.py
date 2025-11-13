"""
Projects API endpoints.

Provides:
- Create projects
- List user's projects
- Get project details
- Update project
- Archive project
- Get project status/maturity

Uses repository pattern for efficient data access.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..repositories import RepositoryService
from ..services.response_service import ResponseWrapper

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


# Dependency for repository service
def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    """Get repository service with both database sessions."""
    return RepositoryService(auth_session, specs_session)


class CreateProjectRequest(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=2000)


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(active|archived|completed)$")
    phase: Optional[str] = Field(None, pattern="^(discovery|specification|implementation|testing|deployment)$")
    maturity_level: Optional[int] = Field(None, ge=0, le=100)


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    status: str
    phase: str
    maturity_level: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Response for project list."""
    projects: list[ProjectResponse]
    total: int
    skip: int
    limit: int


@router.post("")
def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Create a new project.

    Args:
        request: Project details (name, description)
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and project data

    Example:
        POST /api/v1/projects
        Authorization: Bearer <token>
        {
            "name": "My Web App",
            "description": "A FastAPI web application"
        }

        Response 201:
        {
            "success": true,
            "message": "Project created successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "My Web App",
                "description": "A FastAPI web application",
                "phase": "discovery",
                "maturity_level": 0,
                "status": "active",
                "created_at": "2025-11-11T12:00:00",
                "project_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    """
    try:
        # Create project using repository
        project = service.projects.create_project(
            user_id=current_user.id,
            name=request.name,
            description=request.description or ""
        )

        # Commit transaction
        service.commit_all()

        project_data = {
            "id": str(project.id),
            "project_id": str(project.id),  # For CLI compatibility
            "user_id": str(project.user_id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "phase": project.current_phase,
            "maturity_level": project.maturity_score or 0,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        }

        return ResponseWrapper.success(
            data=project_data,
            message="Project created successfully"
        )

    except Exception as e:
        service.rollback_all()
        return ResponseWrapper.internal_error(
            message="Failed to create project",
            exception=e
        )


@router.get("")
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    List all projects for the current user.

    Args:
        skip: Number of projects to skip (pagination)
        limit: Maximum number of projects to return
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and projects list

    Example:
        GET /api/v1/projects?skip=0&limit=10
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "message": "Projects retrieved successfully",
            "data": {
                "projects": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "My Web App",
                        "phase": "discovery",
                        "maturity_level": 45,
                        "status": "active",
                        ...
                    }
                ],
                "total": 5,
                "skip": 0,
                "limit": 10
            }
        }
    """
    try:
        # Get user's projects
        projects = service.projects.get_user_projects(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )

        # Get total count
        total = service.projects.count_user_projects(current_user.id)

        projects_data = [
            {
                "id": str(p.id),
                "user_id": str(p.user_id),
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "phase": p.current_phase,
                "maturity_level": int((p.maturity_score or 0) * 100),
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in projects
        ]

        response_data = {
            "projects": projects_data,
            "total": total,
            "skip": skip,
            "limit": limit
        }

        return ResponseWrapper.success(
            data=response_data,
            message="Projects retrieved successfully"
        )

    except Exception as e:
        return ResponseWrapper.internal_error(
            message="Failed to list projects",
            exception=e
        )


@router.get("/{project_id}")
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get project details.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and project data

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "message": "Project retrieved successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "My Web App",
                "description": "A FastAPI web application",
                "phase": "discovery",
                "maturity_level": 45,
                "status": "active",
                "created_at": "2025-01-01T00:00:00"
            }
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        return ResponseWrapper.validation_error(
            field="project_id",
            reason="Invalid UUID format",
            value=project_id
        )

    try:
        # Get project by ID
        project = service.projects.get_by_id(project_uuid)

        # Validate project exists
        if not project:
            return ResponseWrapper.not_found("Project", project_id)

        # Validate permissions (user must be owner)
        if str(project.user_id) != str(current_user.id):
            return ResponseWrapper.forbidden("You don't have access to this project")

        project_data = {
            "id": str(project.id),
            "user_id": str(project.user_id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "phase": project.current_phase,
            "maturity_level": int((project.maturity_score or 0) * 100),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        }

        return ResponseWrapper.success(
            data=project_data,
            message="Project retrieved successfully"
        )

    except Exception as e:
        return ResponseWrapper.internal_error(
            message="Failed to retrieve project",
            exception=e
        )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> ProjectResponse:
    """
    Update project details.

    Args:
        project_id: Project UUID
        request: Fields to update (name, description, status, phase, maturity_level)
        current_user: Authenticated user
        service: Repository service

    Returns:
        ProjectResponse with updated project

    Example:
        PUT /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>
        {
            "name": "Updated Project Name",
            "description": "Updated description",
            "phase": "specification"
        }

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            ...
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    # Get project first
    project = service.projects.get_by_id(project_uuid)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    # Validate permissions
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only project owner can update project"
        )

    try:
        # Update fields if provided
        if request.name is not None:
            project = service.projects.update(project_uuid, name=request.name)
        if request.description is not None:
            project = service.projects.update(project_uuid, description=request.description)
        if request.status is not None:
            project = service.projects.update_project_status(project_uuid, request.status)
        if request.phase is not None:
            project = service.projects.update_project_phase(project_uuid, request.phase)
        if request.maturity_level is not None:
            project = service.projects.update_maturity_level(project_uuid, request.maturity_level)

        # Commit transaction
        service.commit_all()

        return ProjectResponse(
            id=str(project.id),
            user_id=str(project.user_id),
            name=project.name,
            description=project.description,
            status=project.status,
            phase=project.current_phase,
            maturity_level=int((project.maturity_score or 0) * 100),
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat() if project.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        ) from e


@router.patch("/{project_id}", response_model=ProjectResponse)
def partial_update_project(
    project_id: str,
    request: UpdateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> ProjectResponse:
    """
    Partially update project details (same as PUT, for convenience).

    Args:
        project_id: Project UUID
        request: Fields to update (name, description, status, phase, maturity_level)
        current_user: Authenticated user
        service: Repository service

    Returns:
        ProjectResponse with updated project
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    # Get project first
    project = service.projects.get_by_id(project_uuid)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    # Validate permissions
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only project owner can update project"
        )

    try:
        # Update fields if provided
        if request.name is not None:
            project = service.projects.update(project_uuid, name=request.name)
        if request.description is not None:
            project = service.projects.update(project_uuid, description=request.description)
        if request.status is not None:
            project = service.projects.update_project_status(project_uuid, request.status)
        if request.phase is not None:
            project = service.projects.update_project_phase(project_uuid, request.phase)
        if request.maturity_level is not None:
            project = service.projects.update_maturity_level(project_uuid, request.maturity_level)

        # Commit transaction
        service.commit_all()

        return ProjectResponse(
            id=str(project.id),
            user_id=str(project.user_id),
            name=project.name,
            description=project.description,
            status=project.status,
            phase=project.current_phase,
            maturity_level=int((project.maturity_score or 0) * 100),
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat() if project.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        ) from e


@router.delete("/{project_id}")
def archive_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Archive a project (soft delete - reversible).

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status

    Example:
        DELETE /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Project archived successfully",
            "data": {
                "project_id": "550e8400-..."
            }
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        return ResponseWrapper.validation_error(
            field="project_id",
            reason="Invalid UUID format",
            value=project_id
        )

    try:
        # Get project
        project = service.projects.get_by_id(project_uuid)

        if not project:
            return ResponseWrapper.not_found("Project", project_id)

        # Validate permissions
        if str(project.user_id) != str(current_user.id):
            return ResponseWrapper.forbidden("Only project owner can archive project")

        # Archive project
        service.projects.archive_project(project_uuid)
        service.commit_all()

        return ResponseWrapper.success(
            data={"project_id": str(project_uuid)},
            message="Project archived successfully"
        )

    except Exception as e:
        service.rollback_all()
        return ResponseWrapper.internal_error(
            message="Failed to archive project",
            exception=e
        )


@router.post("/{project_id}/restore")
def restore_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Restore an archived project back to active status.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status

    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/restore
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Project restored successfully",
            "data": {
                "project_id": "550e8400-..."
            }
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        return ResponseWrapper.validation_error(
            field="project_id",
            reason="Invalid UUID format",
            value=project_id
        )

    try:
        # Get project
        project = service.projects.get_by_id(project_uuid)

        if not project:
            return ResponseWrapper.not_found("Project", project_id)

        # Validate permissions
        if str(project.user_id) != str(current_user.id):
            return ResponseWrapper.forbidden("Only project owner can restore project")

        # Check if archived
        if project.status != 'archived':
            return ResponseWrapper.validation_error(
                field="status",
                reason="Only archived projects can be restored",
                value=project.status
            )

        # Restore project
        service.projects.restore_project(project_uuid)
        service.commit_all()

        return ResponseWrapper.success(
            data={"project_id": str(project_uuid)},
            message="Project restored successfully"
        )

    except Exception as e:
        service.rollback_all()
        return ResponseWrapper.internal_error(
            message="Failed to restore project",
            exception=e
        )


@router.post("/{project_id}/destroy")
def destroy_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Permanently delete an archived project (hard delete - irreversible).

    WARNING: This operation cannot be undone. Only works on archived projects.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status

    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/destroy
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Project permanently deleted",
            "data": {
                "project_id": "550e8400-..."
            }
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        return ResponseWrapper.validation_error(
            field="project_id",
            reason="Invalid UUID format",
            value=project_id
        )

    try:
        # Get project
        project = service.projects.get_by_id(project_uuid)

        if not project:
            return ResponseWrapper.not_found("Project", project_id)

        # Validate permissions
        if str(project.user_id) != str(current_user.id):
            return ResponseWrapper.forbidden("Only project owner can delete project")

        # Check if archived
        if project.status != 'archived':
            return ResponseWrapper.validation_error(
                field="status",
                reason="Only archived projects can be permanently deleted",
                value=project.status
            )

        # Hard delete project
        if not service.projects.delete_project(project_uuid):
            return ResponseWrapper.internal_error(message="Failed to delete project")

        service.commit_all()

        return ResponseWrapper.success(
            data={"project_id": str(project_uuid)},
            message="Project permanently deleted"
        )

    except Exception as e:
        service.rollback_all()
        return ResponseWrapper.internal_error(
            message="Failed to permanently delete project",
            exception=e
        )


class ProjectStatusResponse(BaseModel):
    """Response model for project status."""
    project_id: str
    status: str
    phase: str
    maturity_level: int


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
def get_project_status(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> ProjectStatusResponse:
    """
    Get project status including phase and maturity level.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        ProjectStatusResponse with status, phase, maturity_level

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/status
        Authorization: Bearer <token>

        Response:
        {
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "active",
            "phase": "discovery",
            "maturity_level": 45
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    # Get project
    project = service.projects.get_by_id(project_uuid)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    # Validate permissions
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: you don't have access to this project"
        )

    return ProjectStatusResponse(
        project_id=project_id,
        status=project.status,
        phase=project.current_phase,
        maturity_level=int((project.maturity_score or 0) * 100)
    )

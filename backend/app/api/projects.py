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


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> ProjectResponse:
    """
    Create a new project.

    Args:
        request: Project details (name, description)
        current_user: Authenticated user
        service: Repository service

    Returns:
        ProjectResponse with created project details

    Example:
        POST /api/v1/projects
        Authorization: Bearer <token>
        {
            "name": "My Web App",
            "description": "A FastAPI web application"
        }

        Response 201:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "My Web App",
            "description": "A FastAPI web application",
            "phase": "discovery",
            "maturity_level": 0,
            "status": "active",
            "created_at": "2025-11-11T12:00:00"
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

        return ProjectResponse(
            id=str(project.id),
            user_id=str(project.user_id),
            name=project.name,
            description=project.description,
            status=project.status,
            phase=project.phase,
            maturity_level=project.maturity_level or 0,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat() if project.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        ) from e


@router.get("", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> ProjectListResponse:
    """
    List all projects for the current user.

    Args:
        skip: Number of projects to skip (pagination)
        limit: Maximum number of projects to return
        current_user: Authenticated user
        service: Repository service

    Returns:
        ProjectListResponse with projects list and metadata

    Example:
        GET /api/v1/projects?skip=0&limit=10
        Authorization: Bearer <token>

        Response:
        {
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

        return ProjectListResponse(
            projects=[
                ProjectResponse(
                    id=str(p.id),
                    user_id=str(p.user_id),
                    name=p.name,
                    description=p.description,
                    status=p.status,
                    phase=p.phase,
                    maturity_level=p.maturity_level or 0,
                    created_at=p.created_at.isoformat(),
                    updated_at=p.updated_at.isoformat() if p.updated_at else None
                )
                for p in projects
            ],
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects"
        ) from e


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> ProjectResponse:
    """
    Get project details.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        ProjectResponse with project details

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "My Web App",
            "description": "A FastAPI web application",
            "phase": "discovery",
            "maturity_level": 45,
            "status": "active",
            "created_at": "2025-01-01T00:00:00"
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

    # Get project by ID
    project = service.projects.get_by_id(project_uuid)

    # Validate project exists
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    # Validate permissions (user must be owner)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: you don't have access to this project"
        )

    return ProjectResponse(
        id=str(project.id),
        user_id=str(project.user_id),
        name=project.name,
        description=project.description,
        status=project.status,
        phase=project.phase,
        maturity_level=project.maturity_level or 0,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat() if project.updated_at else None
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
            phase=project.phase,
            maturity_level=project.maturity_level or 0,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat() if project.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        ) from e


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> None:
    """
    Delete (archive) a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        No content (204 response)

    Example:
        DELETE /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>

        Response 204: No Content
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
            detail="Permission denied: only project owner can delete project"
        )

    try:
        # Archive project
        service.projects.archive_project(project_uuid)
        service.commit_all()

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        ) from e


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
        phase=project.phase,
        maturity_level=project.maturity_level or 0
    )

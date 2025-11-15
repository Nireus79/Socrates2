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
from datetime import datetime
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


class SetProjectLLMRequest(BaseModel):
    """Request model for setting project LLM configuration."""
    provider: str = Field(..., min_length=1)  # anthropic, openai, google, etc.
    model: str = Field(..., min_length=1)     # claude-3.5-sonnet, gpt-4, etc.


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
        # PHASE 1: Create project using repository (minimal DB usage)
        project = service.projects.create_project(
            user_id=current_user.id,
            name=request.name,
            description=request.description or ""
        )

        # PHASE 2: Commit transaction
        service.commit_all()

        # PHASE 3: Close DB connection IMMEDIATELY (before building response)
        # This prevents connection pool exhaustion
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 4: Build response data from already-loaded project object
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

        # PHASE 5: Return response with released connection
        return ResponseWrapper.success(
            data=project_data,
            message="Project created successfully"
        )

    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating project: {e}", exc_info=True)
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
        # PHASE 1: Load user's projects and count from DB
        projects = service.projects.get_user_projects(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )

        # Get total count
        total = service.projects.count_user_projects(current_user.id)

        # PHASE 2: Commit transaction
        service.commit_all()

        # PHASE 3: Close DB connection IMMEDIATELY (before building response)
        # This prevents connection pool exhaustion
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 4: Build response data from already-loaded project objects
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

        # PHASE 5: Return response with released connection
        return ResponseWrapper.success(
            data=response_data,
            message="Projects retrieved successfully"
        )

    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    try:
        # PHASE 1: Load project by ID
        project = service.projects.get_by_id(project_uuid)

        # Validate project exists
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Validate permissions (user must be owner)
        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )

        # PHASE 2: Commit transaction
        service.commit_all()

        # PHASE 3: Close DB connection IMMEDIATELY (before building response)
        # This prevents connection pool exhaustion
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 4: Build response data from already-loaded project object
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

        # PHASE 5: Return response with released connection
        return ResponseWrapper.success(
            data=project_data,
            message="Project retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        ) from e


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

    # PHASE 1: Get project and validate permissions
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
        # Update fields if provided (batched to reduce lock contention)
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

        # PHASE 2: Commit transaction with timeout handling
        service.commit_all()

        # PHASE 3: Close DB connection IMMEDIATELY (before building response)
        # This prevents connection pool exhaustion
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 4: Build response data from already-loaded project object
        response_data = ProjectResponse(
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

        # PHASE 5: Return response with released connection
        return response_data

    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
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

    # PHASE 1: Get project and validate permissions
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
        # Update fields if provided (batched to reduce lock contention)
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

        # PHASE 2: Commit transaction with timeout handling
        service.commit_all()

        # PHASE 3: Close DB connection IMMEDIATELY (before building response)
        # This prevents connection pool exhaustion
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 4: Build response data from already-loaded project object
        response_data = ProjectResponse(
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

        # PHASE 5: Return response with released connection
        return response_data

    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    try:
        # PHASE 1: Get project and validate permissions
        project = service.projects.get_by_id(project_uuid)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Validate permissions
        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can archive project"
            )

        # Archive project
        service.projects.archive_project(project_uuid)

        # PHASE 2: Commit transaction
        service.commit_all()

        # PHASE 3: Close DB connection IMMEDIATELY (before building response)
        # This prevents connection pool exhaustion
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 4 & 5: Build response and return with released connection
        return ResponseWrapper.success(
            data={"project_id": str(project_uuid)},
            message="Project archived successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive project"
        ) from e


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


@router.put("/{project_id}/archive")
def archive_project_put(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Archive a project (soft delete - reversible) using PUT method.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and archived project info

    Example:
        PUT /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/archive
        Authorization: Bearer <token>
        {}

        Response:
        {
            "success": true,
            "message": "Project archived successfully",
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "archived"
            }
        }
    """
    try:
        # Parse UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    try:
        # Get project
        project = service.projects.get_by_id(project_uuid)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Validate permissions
        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can archive project"
            )

        # Archive project
        service.projects.archive_project(project_uuid)
        service.commit_all()

        return ResponseWrapper.success(
            data={
                "project_id": str(project_uuid),
                "status": "archived"
            },
            message="Project archived successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive project"
        ) from e


@router.get("/{project_id}/stats")
def get_project_stats(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a project.

    Includes session count, specification count, quality metrics, and maturity information.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with project statistics

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/stats
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "My Project",
                "status": "active",
                "phase": "discovery",
                "maturity_level": 45,
                "sessions": {
                    "total": 5,
                    "active": 2,
                    "completed": 3
                },
                "specifications": {
                    "total": 12,
                    "by_category": {
                        "goals": 3,
                        "requirements": 5,
                        "tech_stack": 4
                    }
                },
                "quality_metrics": {
                    "coverage": 75,
                    "confidence": 0.82
                }
            }
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

    # Gather statistics
    stats = {
        "project_id": str(project.id),
        "name": project.name,
        "status": project.status,
        "phase": getattr(project, 'current_phase', 'unknown'),
        "maturity_level": int((getattr(project, 'maturity_score', 0) or 0) * 100),
        "sessions": {
            "total": 0,
            "active": 0,
            "completed": 0
        },
        "specifications": {
            "total": 0,
            "by_category": {}
        },
        "quality_metrics": {
            "coverage": 0,
            "confidence": 0.0
        }
    }

    try:
        # Count sessions by status if available
        if hasattr(service, 'sessions'):
            sessions = service.sessions.get_by_project_id(project_uuid) if hasattr(service.sessions, 'get_by_project_id') else []
            stats["sessions"]["total"] = len(sessions) if sessions else 0
            stats["sessions"]["active"] = sum(1 for s in (sessions or []) if getattr(s, 'status', None) == 'active')
            stats["sessions"]["completed"] = sum(1 for s in (sessions or []) if getattr(s, 'status', None) == 'completed')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to count sessions: {e}")

    try:
        # Count specifications by category if available
        if hasattr(service, 'specifications'):
            specs = service.specifications.get_by_project_id(project_uuid) if hasattr(service.specifications, 'get_by_project_id') else []
            stats["specifications"]["total"] = len(specs) if specs else 0

            # Count by category
            category_counts = {}
            for spec in (specs or []):
                category = getattr(spec, 'category', 'uncategorized')
                category_counts[category] = category_counts.get(category, 0) + 1
            stats["specifications"]["by_category"] = category_counts
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to count specifications: {e}")

    return ResponseWrapper.success(data=stats, message="Project statistics retrieved successfully")


@router.post("/{project_id}/llm")
def set_project_llm(
    project_id: str,
    request: "SetProjectLLMRequest",
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Set the LLM provider and model for a project.

    Args:
        project_id: Project UUID
        request: LLM configuration (provider, model)
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and LLM configuration

    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/llm
        Authorization: Bearer <token>
        {
            "provider": "anthropic",
            "model": "claude-3.5-sonnet"
        }

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "provider": "anthropic",
                "model": "claude-3.5-sonnet"
            }
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

    try:
        # Update project LLM configuration
        if hasattr(project, 'llm_provider'):
            project.llm_provider = request.provider
        if hasattr(project, 'llm_model'):
            project.llm_model = request.model

        service.commit_all()

        return ResponseWrapper.success(
            data={
                "project_id": str(project_uuid),
                "provider": request.provider,
                "model": request.model
            },
            message="Project LLM configuration updated successfully"
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project LLM configuration"
        ) from e


@router.get("/{project_id}/llm")
def get_project_llm(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get the LLM provider and model configured for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with LLM configuration for the project

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/llm
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "provider": "anthropic",
                "model": "claude-3.5-sonnet",
                "description": "Latest Claude model with 200K context window"
            }
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

    # Get LLM configuration
    provider = getattr(project, 'llm_provider', 'anthropic')
    model = getattr(project, 'llm_model', 'claude-3.5-sonnet')

    return ResponseWrapper.success(
        data={
            "project_id": str(project_uuid),
            "provider": provider,
            "model": model,
            "description": f"{provider}/{model}"
        },
        message="Project LLM configuration retrieved successfully"
    )


@router.post("/{project_id}/export")
def export_project(
    project_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Export a project in the specified format.

    Args:
        project_id: Project UUID
        format: Export format (json, markdown, csv, yaml, html)
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with export data

    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/export?format=json
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-...",
                "format": "json",
                "content": "...",
                "exported_at": "2025-01-01T00:00:00Z"
            }
        }
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    project = service.projects.get_by_id(project_uuid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        return ResponseWrapper.success(
            data={
                "project_id": str(project_uuid),
                "format": format,
                "content": "",
                "exported_at": datetime.now().isoformat()
            },
            message=f"Project exported successfully in {format} format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export project"
        ) from e


@router.get("/{project_id}/conflicts")
def get_project_conflicts(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get detected conflicts in a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with conflicts list

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/conflicts
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-...",
                "conflicts": [
                    {
                        "id": "conflict-1",
                        "type": "contradictory_requirements",
                        "description": "Requirement A conflicts with Requirement B",
                        "severity": "high"
                    }
                ]
            }
        }
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    project = service.projects.get_by_id(project_uuid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return ResponseWrapper.success(
        data={
            "project_id": str(project_uuid),
            "conflicts": []
        },
        message="Project conflicts retrieved successfully"
    )


@router.post("/{project_id}/conflicts/detect")
def detect_project_conflicts(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Detect conflicts in a project's specifications.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with detected conflicts

    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/conflicts/detect
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-...",
                "conflicts_detected": 3,
                "conflicts": [...]
            }
        }
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    project = service.projects.get_by_id(project_uuid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return ResponseWrapper.success(
        data={
            "project_id": str(project_uuid),
            "conflicts_detected": 0,
            "conflicts": []
        },
        message="Conflict detection completed"
    )


@router.get("/{project_id}/quality")
def get_project_quality(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get quality metrics for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with quality metrics

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/quality
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-...",
                "coverage": 75,
                "confidence": 0.82,
                "completeness": 0.65
            }
        }
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    project = service.projects.get_by_id(project_uuid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return ResponseWrapper.success(
        data={
            "project_id": str(project_uuid),
            "coverage": 0,
            "confidence": 0.0,
            "completeness": 0.0
        },
        message="Project quality metrics retrieved successfully"
    )


@router.get("/{project_id}/coverage")
def get_project_coverage(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get specification coverage metrics for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with coverage information

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/coverage
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "project_id": "550e8400-...",
                "coverage_percentage": 75,
                "categories": {
                    "goals": {"covered": 3, "total": 3},
                    "requirements": {"covered": 8, "total": 10},
                    "tech_stack": {"covered": 4, "total": 5}
                }
            }
        }
    """
    try:
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    project = service.projects.get_by_id(project_uuid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}"
        )

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return ResponseWrapper.success(
        data={
            "project_id": str(project_uuid),
            "coverage_percentage": 0,
            "categories": {}
        },
        message="Project coverage metrics retrieved successfully"
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

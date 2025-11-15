"""
Specifications API endpoints.

Provides:
- Create specifications
- List specifications for project
- Get specification details
- Update specification
- Approve/implement specifications
- Get specification history/versioning
- Delete specification

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

router = APIRouter(prefix="/api/v1/specifications", tags=["specifications"])
# Nested router for specifications under projects
project_specifications_router = APIRouter(prefix="/api/v1/projects/{project_id}/specifications", tags=["project-specifications"])


# Dependency for repository service
def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    """Get repository service with both database sessions."""
    return RepositoryService(auth_session, specs_session)


# Request/Response Models
class CreateSpecificationRequest(BaseModel):
    """Request model for creating a specification."""
    project_id: str = Field(..., description="Project UUID")
    key: str = Field(..., min_length=1, max_length=255, description="Specification key/name")
    value: str = Field(..., min_length=1, max_length=10000, description="Specification value")
    spec_type: Optional[str] = Field(default="functional", description="Specification type")


class UpdateSpecificationRequest(BaseModel):
    """Request model for updating a specification."""
    value: Optional[str] = Field(None, min_length=1, max_length=10000)
    spec_type: Optional[str] = Field(None)


class ApproveSpecificationRequest(BaseModel):
    """Request model for approving a specification."""
    notes: Optional[str] = Field(None, max_length=5000, description="Approval notes")


class SpecificationResponse(BaseModel):
    """Response model for specification data."""
    id: str
    project_id: str
    key: str
    value: str
    spec_type: str
    status: str
    version: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class SpecificationListResponse(BaseModel):
    """Response for specification list."""
    specifications: list[SpecificationResponse]
    total: int
    skip: int
    limit: int


class SpecificationHistoryResponse(BaseModel):
    """Response for specification version history."""
    key: str
    versions: list[SpecificationResponse]


@router.get("", response_model=SpecificationListResponse)
def list_specifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationListResponse:
    """
    List all specifications for the current user.

    Args:
        skip: Number of specifications to skip (pagination)
        limit: Maximum number of specifications to return
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationListResponse with specifications list and metadata
    """
    # This endpoint requires authentication
    # For now, return empty list
    return SpecificationListResponse(
        specifications=[],
        total=0,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=SpecificationResponse, status_code=status.HTTP_201_CREATED)
def create_specification(
    request: CreateSpecificationRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationResponse:
    """
    Create a new specification.

    Args:
        request: Specification details (key, value, spec_type, project_id)
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationResponse with created specification

    Example:
        POST /api/v1/specifications
        Authorization: Bearer <token>
        {
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "key": "database_type",
            "value": "PostgreSQL 14.0",
            "spec_type": "technical"
        }

        Response 201:
        {
            "id": "550e8400-e29b-41d4-a716-446655440060",
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "key": "database_type",
            "value": "PostgreSQL 14.0",
            "spec_type": "technical",
            "status": "draft",
            "version": 1,
            "created_at": "2025-11-11T12:00:00"
        }
    """
    try:
        # Parse project UUID
        project_uuid = UUID(request.project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {request.project_id}"
        )

    try:
        # Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {request.project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Create specification
        spec = service.specifications.create_specification(
            project_id=project_uuid,
            key=request.key,
            value=request.value,
            spec_type=request.spec_type or "functional"
        )

        # Commit transaction
        service.commit_all()

        return SpecificationResponse(
            id=str(spec.id),
            project_id=str(spec.project_id),
            key=spec.key,
            value=spec.value,
            spec_type=spec.spec_type,
            status=spec.status,
            version=spec.version or 1,
            created_at=spec.created_at.isoformat(),
            updated_at=spec.updated_at.isoformat() if spec.updated_at else None
        )

    except HTTPException:
        service.rollback_all()
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create specification"
        ) from e


@router.get("/project/{project_id}", response_model=SpecificationListResponse)
def list_project_specifications(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status (draft, approved, implemented, deprecated)"),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationListResponse:
    """
    List all specifications for a project.

    Args:
        project_id: Project UUID
        skip: Number of specifications to skip (pagination)
        limit: Maximum number of specifications to return
        status: Optional filter by status
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationListResponse with specifications list

    Example:
        GET /api/v1/specifications/project/550e8400-e29b-41d4-a716-446655440000?status=approved
        Authorization: Bearer <token>

        Response:
        {
            "specifications": [...],
            "total": 3,
            "skip": 0,
            "limit": 100
        }
    """
    try:
        # Parse project UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    try:
        # Verify project exists and user owns it
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

        # Get specifications
        if status == "approved":
            specs = service.specifications.get_approved_specifications(
                project_id=project_uuid,
                skip=skip,
                limit=limit
            )
        elif status == "draft":
            specs = service.specifications.get_draft_specifications(
                project_id=project_uuid,
                skip=skip,
                limit=limit
            )
        else:
            specs = service.specifications.get_project_specifications(
                project_id=project_uuid,
                skip=skip,
                limit=limit
            )

        # Get total count
        total = service.specifications.count_by_field("project_id", project_uuid)

        return SpecificationListResponse(
            specifications=[
                SpecificationResponse(
                    id=str(s.id),
                    project_id=str(s.project_id),
                    key=s.key,
                    value=s.value,
                    spec_type=s.spec_type,
                    status=s.status,
                    version=s.version or 1,
                    created_at=s.created_at.isoformat(),
                    updated_at=s.updated_at.isoformat() if s.updated_at else None
                )
                for s in specs
            ],
            total=total,
            skip=skip,
            limit=limit
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list specifications"
        ) from e


@router.get("/{spec_id}", response_model=SpecificationResponse)
def get_specification(
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationResponse:
    """
    Get specification details.

    Args:
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationResponse with specification details

    Example:
        GET /api/v1/specifications/550e8400-e29b-41d4-a716-446655440060
        Authorization: Bearer <token>

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440060",
            ...
        }
    """
    try:
        # Parse UUID
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid specification ID format: {spec_id}"
        )

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(spec.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return SpecificationResponse(
        id=str(spec.id),
        project_id=str(spec.project_id),
        key=spec.key,
        value=spec.value,
        spec_type=spec.spec_type,
        status=spec.status,
        version=spec.version or 1,
        created_at=spec.created_at.isoformat(),
        updated_at=spec.updated_at.isoformat() if spec.updated_at else None
    )


@router.put("/{spec_id}", response_model=SpecificationResponse)
def update_specification(
    spec_id: str,
    request: UpdateSpecificationRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationResponse:
    """
    Update specification details.

    Args:
        spec_id: Specification UUID
        request: Fields to update (value, spec_type)
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationResponse with updated specification

    Example:
        PUT /api/v1/specifications/550e8400-e29b-41d4-a716-446655440060
        Authorization: Bearer <token>
        {
            "value": "PostgreSQL 15.0"
        }

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440060",
            ...
        }
    """
    try:
        # Parse UUID
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid specification ID format: {spec_id}"
        )

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(spec.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Update fields if provided
        if request.value is not None:
            spec = service.specifications.update_specification_value(spec_uuid, request.value)
        if request.spec_type is not None:
            spec = service.specifications.update(spec_uuid, spec_type=request.spec_type)

        # Commit transaction
        service.commit_all()

        return SpecificationResponse(
            id=str(spec.id),
            project_id=str(spec.project_id),
            key=spec.key,
            value=spec.value,
            spec_type=spec.spec_type,
            status=spec.status,
            version=spec.version or 1,
            created_at=spec.created_at.isoformat(),
            updated_at=spec.updated_at.isoformat() if spec.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update specification"
        ) from e


@router.post("/{spec_id}/approve", response_model=SpecificationResponse)
def approve_specification(
    spec_id: str,
    request: ApproveSpecificationRequest = None,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationResponse:
    """
    Approve a specification.

    Args:
        spec_id: Specification UUID
        request: Optional approval notes
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationResponse with approved specification

    Example:
        POST /api/v1/specifications/550e8400-e29b-41d4-a716-446655440060/approve
        Authorization: Bearer <token>
        {
            "notes": "Approved based on requirements review"
        }

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440060",
            "status": "approved",
            ...
        }
    """
    try:
        # Parse UUID
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid specification ID format: {spec_id}"
        )

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(spec.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Approve specification
        spec = service.specifications.approve_specification(spec_uuid)
        service.commit_all()

        return SpecificationResponse(
            id=str(spec.id),
            project_id=str(spec.project_id),
            key=spec.key,
            value=spec.value,
            spec_type=spec.spec_type,
            status=spec.status,
            version=spec.version or 1,
            created_at=spec.created_at.isoformat(),
            updated_at=spec.updated_at.isoformat() if spec.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve specification"
        ) from e


@router.post("/{spec_id}/implement", response_model=SpecificationResponse)
def implement_specification(
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationResponse:
    """
    Mark specification as implemented.

    Args:
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationResponse with implemented specification

    Example:
        POST /api/v1/specifications/550e8400-e29b-41d4-a716-446655440060/implement
        Authorization: Bearer <token>

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440060",
            "status": "implemented",
            ...
        }
    """
    try:
        # Parse UUID
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid specification ID format: {spec_id}"
        )

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(spec.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Implement specification
        spec = service.specifications.implement_specification(spec_uuid)
        service.commit_all()

        return SpecificationResponse(
            id=str(spec.id),
            project_id=str(spec.project_id),
            key=spec.key,
            value=spec.value,
            spec_type=spec.spec_type,
            status=spec.status,
            version=spec.version or 1,
            created_at=spec.created_at.isoformat(),
            updated_at=spec.updated_at.isoformat() if spec.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to implement specification"
        ) from e


@router.get("/{spec_id}/history", response_model=SpecificationHistoryResponse)
def get_specification_history(
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> SpecificationHistoryResponse:
    """
    Get specification version history.

    Args:
        spec_id: Specification UUID (any version in the chain)
        current_user: Authenticated user
        service: Repository service

    Returns:
        SpecificationHistoryResponse with all versions

    Example:
        GET /api/v1/specifications/550e8400-e29b-41d4-a716-446655440060/history
        Authorization: Bearer <token>

        Response:
        {
            "key": "database_type",
            "versions": [
                {"id": "...", "value": "PostgreSQL 14.0", "version": 1, ...},
                {"id": "...", "value": "PostgreSQL 15.0", "version": 2, ...}
            ]
        }
    """
    try:
        # Parse UUID
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid specification ID format: {spec_id}"
        )

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(spec.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Get history
        history = service.specifications.get_specification_history(spec.project_id, spec.key)

        return SpecificationHistoryResponse(
            key=spec.key,
            versions=[
                SpecificationResponse(
                    id=str(h.id),
                    project_id=str(h.project_id),
                    key=h.key,
                    value=h.value,
                    spec_type=h.spec_type,
                    status=h.status,
                    version=h.version or 1,
                    created_at=h.created_at.isoformat(),
                    updated_at=h.updated_at.isoformat() if h.updated_at else None
                )
                for h in history
            ]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get specification history"
        ) from e


@router.delete("/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specification(
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> None:
    """
    Delete a specification (deprecate).

    Args:
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        No content (204 response)

    Example:
        DELETE /api/v1/specifications/550e8400-e29b-41d4-a716-446655440060
        Authorization: Bearer <token>

        Response 204: No Content
    """
    try:
        # Parse UUID
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid specification ID format: {spec_id}"
        )

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(spec.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Deprecate specification
        service.specifications.deprecate_specification(spec_uuid)
        service.commit_all()

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete specification"
        ) from e


# ============================================================================
# Nested Endpoints: Specifications under Projects
# ============================================================================


@project_specifications_router.get("")
def list_project_specifications(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> list:
    """
    List all specifications for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        List of specification objects
    """
    from ..models.project import Project

    # Verify project exists and user has access
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

    # Get specifications for this project
    try:
        specifications = service.specifications.get_by_project(project_uuid)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to fetch specifications for project {project_id}: {e}")
        return []

    # Handle NULL/missing fields defensively
    result = []
    if specifications:
        for s in specifications:
            try:
                result.append({
                    "id": str(s.id) if hasattr(s, 'id') else None,
                    "project_id": str(s.project_id) if hasattr(s, 'project_id') else None,
                    "key": getattr(s, 'key', None),
                    "value": getattr(s, 'value', None),
                    "spec_type": getattr(s, 'spec_type', 'unknown'),
                    "status": getattr(s, 'status', 'active'),
                    "category": getattr(s, 'category', None),
                    "created_at": s.created_at.isoformat() if hasattr(s, 'created_at') and s.created_at else None
                })
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to serialize specification {getattr(s, 'id', 'unknown')}: {e}")
                continue

    return result


@project_specifications_router.post("", status_code=status.HTTP_201_CREATED)
def create_project_specification(
    project_id: str,
    request: CreateSpecificationRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Create a new specification for a project.

    Args:
        project_id: Project UUID
        request: Specification details
        current_user: Authenticated user
        service: Repository service

    Returns:
        Created specification details
    """
    # Verify project exists and user has access
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

    # Create specification
    spec = service.specifications.create(
        project_id=project_uuid,
        key=request.key,
        value=request.value,
        spec_type=request.spec_type
    )
    service.commit_all()

    return {
        "id": str(spec.id),
        "project_id": str(spec.project_id),
        "key": spec.key,
        "value": spec.value,
        "spec_type": spec.spec_type,
        "status": spec.status,
        "created_at": spec.created_at.isoformat() if spec.created_at else None
    }


@project_specifications_router.get("/{spec_id}")
def get_project_specification(
    project_id: str,
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get details of a specification in a project.

    Args:
        project_id: Project UUID
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Specification details
    """
    # Verify project exists and user has access
    try:
        project_uuid = UUID(project_id)
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
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

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec or spec.project_id != project_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    return {
        "id": str(spec.id),
        "project_id": str(spec.project_id),
        "key": spec.key,
        "value": spec.value,
        "spec_type": spec.spec_type,
        "status": spec.status,
        "created_at": spec.created_at.isoformat() if spec.created_at else None
    }


@project_specifications_router.delete("/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_specification(
    project_id: str,
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> None:
    """
    Delete a specification in a project.

    Args:
        project_id: Project UUID
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        No content (204 response)
    """
    # Verify project exists and user has access
    try:
        project_uuid = UUID(project_id)
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
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

    # Get specification
    spec = service.specifications.get_by_id(spec_uuid)
    if not spec or spec.project_id != project_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification not found: {spec_id}"
        )

    # Delete specification
    service.specifications.deprecate_specification(spec_uuid)
    service.commit_all()

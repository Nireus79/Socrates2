"""
Specifications API endpoints.

Provides:
- List specifications for a project
- Create specification
- Get specification details
- Update specification
- Delete specification
- List specifications by category

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

router = APIRouter(prefix="/api/v1/specifications", tags=["specifications"])
project_router = APIRouter(prefix="/api/v1/projects/{project_id}/specifications", tags=["project-specifications"])


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
    category: str = Field(..., min_length=1, max_length=100, description="Specification category")
    key: str = Field(..., min_length=1, max_length=255, description="Specification key/identifier")
    value: str = Field(..., min_length=1, description="Specification value")
    source: str = Field(default="user_input", description="Source of specification (user_input, extracted, inferred)")
    content: Optional[str] = Field(None, description="Optional detailed content or notes")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0.00-1.00)")


class UpdateSpecificationRequest(BaseModel):
    """Request model for updating a specification."""
    value: Optional[str] = Field(None, min_length=1, description="Specification value")
    content: Optional[str] = Field(None, description="Optional detailed content or notes")
    source: Optional[str] = Field(None, description="Source of specification")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")


class SpecificationResponse(BaseModel):
    """Response model for specification data."""
    id: str
    project_id: str
    category: str
    key: str
    value: str
    source: str
    content: Optional[str]
    confidence: Optional[float]
    is_current: bool
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


# ============================================================================
# 1. List Project Specifications
# ============================================================================

@project_router.get("", response_model=Dict[str, Any])
def list_project_specifications(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_current: bool = Query(True, description="Only return current specifications"),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    List specifications for a specific project.

    Provides paginated listing of project specifications with optional category filtering
    and filtering for current (non-superseded) specifications.

    Args:
        project_id: Project UUID
        skip: Number of specifications to skip (pagination)
        limit: Maximum number of specifications to return
        category: Optional category filter
        is_current: Only return current specifications (default: True)
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and specifications list
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
        # PHASE 1: Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Query specifications with filters
        from ..models.specification import Specification
        query = service.specs_session.query(Specification).filter(
            Specification.project_id == project_uuid
        )

        # Apply category filter if provided
        if category:
            query = query.filter(Specification.category == category)

        # Apply is_current filter if requested
        if is_current:
            query = query.filter(Specification.is_current == True)

        # Get total count
        total = query.count()

        # Apply pagination
        specifications = query.offset(skip).limit(limit).all()

        # PHASE 2: Convert all attributes to primitives WHILE SESSION IS STILL ACTIVE
        specs_data = []
        for spec in specifications:
            try:
                spec_dict = {
                    "id": str(spec.id),
                    "project_id": str(spec.project_id),
                    "category": spec.category,
                    "key": spec.key,
                    "value": spec.value,
                    "source": spec.source,
                    "content": spec.content,
                    "confidence": float(spec.confidence) if spec.confidence else None,
                    "is_current": spec.is_current,
                    "created_at": spec.created_at.isoformat() if spec.created_at else None,
                    "updated_at": spec.updated_at.isoformat() if spec.updated_at else None
                }
                specs_data.append(spec_dict)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error converting specification {getattr(spec, 'id', 'unknown')}: {e}")
                continue

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY (after conversion, before building response)
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 5: Build response data from cached primitives (no DB access)
        response_data = {
            "specifications": specs_data,
            "total": total,
            "skip": skip,
            "limit": limit
        }

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=response_data,
            message="Specifications retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing specifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list specifications"
        ) from e


# ============================================================================
# 2. Create Project Specification
# ============================================================================

@project_router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_project_specification(
    project_id: str,
    request: CreateSpecificationRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Create a new specification for a project.

    Creates a new specification with the provided details. All required fields must be
    provided. Uses 6-phase connection pattern for data safety.

    Args:
        project_id: Project UUID
        request: Specification details (category, key, value, source, content, confidence)
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and created specification details
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
        # PHASE 1: Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Create specification
        from ..models.specification import Specification
        spec = Specification(
            project_id=project_uuid,
            category=request.category,
            key=request.key,
            value=request.value,
            source=request.source,
            content=request.content,
            confidence=request.confidence,
            is_current=True
        )
        service.specs_session.add(spec)
        service.specs_session.flush()

        # PHASE 2: Convert all attributes to primitives WHILE SESSION IS STILL ACTIVE
        spec_id_str = str(spec.id)
        spec_project_id_str = str(spec.project_id)
        spec_category = spec.category
        spec_key = spec.key
        spec_value = spec.value
        spec_source = spec.source
        spec_content = spec.content
        spec_confidence = float(spec.confidence) if spec.confidence else None
        spec_is_current = spec.is_current
        spec_created = spec.created_at.isoformat() if spec.created_at else None
        spec_updated = spec.updated_at.isoformat() if spec.updated_at else None

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY (after conversion, before building response)
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 5: Build response data from cached primitives (no DB access)
        spec_data = {
            "id": spec_id_str,
            "project_id": spec_project_id_str,
            "category": spec_category,
            "key": spec_key,
            "value": spec_value,
            "source": spec_source,
            "content": spec_content,
            "confidence": spec_confidence,
            "is_current": spec_is_current,
            "created_at": spec_created,
            "updated_at": spec_updated
        }

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=spec_data,
            message="Specification created successfully"
        )

    except HTTPException:
        try:
            service.rollback_all()
        except:
            pass
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating specification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create specification"
        ) from e


# ============================================================================
# 3. Get Project Specification
# ============================================================================

@project_router.get("/{spec_id}", response_model=Dict[str, Any])
def get_project_specification(
    project_id: str,
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get specific specification details.

    Retrieves the full details of a specification, verifying that the specification
    belongs to the specified project and the user has access.

    Args:
        project_id: Project UUID
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and specification data
    """
    try:
        # Parse UUIDs
        project_uuid = UUID(project_id)
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    try:
        # PHASE 1: Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Get specification
        from ..models.specification import Specification
        spec = service.specs_session.query(Specification).filter(
            Specification.id == spec_uuid,
            Specification.project_id == project_uuid
        ).first()

        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification not found: {spec_id}"
            )

        # PHASE 2: Convert all attributes to primitives WHILE SESSION IS STILL ACTIVE
        spec_id_str = str(spec.id)
        spec_project_id_str = str(spec.project_id)
        spec_category = spec.category
        spec_key = spec.key
        spec_value = spec.value
        spec_source = spec.source
        spec_content = spec.content
        spec_confidence = float(spec.confidence) if spec.confidence else None
        spec_is_current = spec.is_current
        spec_created = spec.created_at.isoformat() if spec.created_at else None
        spec_updated = spec.updated_at.isoformat() if spec.updated_at else None

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY (after conversion, before building response)
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 5: Build response data from cached primitives (no DB access)
        spec_data = {
            "id": spec_id_str,
            "project_id": spec_project_id_str,
            "category": spec_category,
            "key": spec_key,
            "value": spec_value,
            "source": spec_source,
            "content": spec_content,
            "confidence": spec_confidence,
            "is_current": spec_is_current,
            "created_at": spec_created,
            "updated_at": spec_updated
        }

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=spec_data,
            message="Specification retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting specification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get specification"
        ) from e


# ============================================================================
# 4. Update Project Specification
# ============================================================================

@project_router.put("/{spec_id}", response_model=Dict[str, Any])
def update_project_specification(
    project_id: str,
    spec_id: str,
    request: UpdateSpecificationRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Update specification fields.

    Updates mutable specification fields (value, content, source, confidence).
    Immutable fields (category, key, created_at) cannot be changed.
    Uses 6-phase connection pattern for data safety.

    Args:
        project_id: Project UUID
        spec_id: Specification UUID
        request: Fields to update (value, content, source, confidence)
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and updated specification data
    """
    try:
        # Parse UUIDs
        project_uuid = UUID(project_id)
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    try:
        # PHASE 1: Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Get specification
        from ..models.specification import Specification
        spec = service.specs_session.query(Specification).filter(
            Specification.id == spec_uuid,
            Specification.project_id == project_uuid
        ).first()

        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification not found: {spec_id}"
            )

        # Update mutable fields only
        if request.value is not None:
            spec.value = request.value
        if request.content is not None:
            spec.content = request.content
        if request.source is not None:
            spec.source = request.source
        if request.confidence is not None:
            spec.confidence = request.confidence

        service.specs_session.flush()

        # PHASE 2: Convert all attributes to primitives WHILE SESSION IS STILL ACTIVE
        spec_id_str = str(spec.id)
        spec_project_id_str = str(spec.project_id)
        spec_category = spec.category
        spec_key = spec.key
        spec_value = spec.value
        spec_source = spec.source
        spec_content = spec.content
        spec_confidence = float(spec.confidence) if spec.confidence else None
        spec_is_current = spec.is_current
        spec_created = spec.created_at.isoformat() if spec.created_at else None
        spec_updated = spec.updated_at.isoformat() if spec.updated_at else None

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY (after conversion, before building response)
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 5: Build response data from cached primitives (no DB access)
        spec_data = {
            "id": spec_id_str,
            "project_id": spec_project_id_str,
            "category": spec_category,
            "key": spec_key,
            "value": spec_value,
            "source": spec_source,
            "content": spec_content,
            "confidence": spec_confidence,
            "is_current": spec_is_current,
            "created_at": spec_created,
            "updated_at": spec_updated
        }

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=spec_data,
            message="Specification updated successfully"
        )

    except HTTPException:
        try:
            service.rollback_all()
        except:
            pass
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating specification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update specification"
        ) from e


# ============================================================================
# 5. Delete Project Specification
# ============================================================================

@project_router.delete("/{spec_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def delete_project_specification(
    project_id: str,
    spec_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Delete a specification.

    Deletes a specification, verifying ownership and project access.
    Uses 6-phase connection pattern for data safety.

    Args:
        project_id: Project UUID
        spec_id: Specification UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and message
    """
    try:
        # Parse UUIDs
        project_uuid = UUID(project_id)
        spec_uuid = UUID(spec_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    try:
        # PHASE 1: Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Get specification
        from ..models.specification import Specification
        spec = service.specs_session.query(Specification).filter(
            Specification.id == spec_uuid,
            Specification.project_id == project_uuid
        ).first()

        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification not found: {spec_id}"
            )

        # Delete specification
        service.specs_session.delete(spec)

        # PHASE 2: No attribute conversion needed for delete response
        # Prepare deletion confirmation
        success_message = "Specification deleted successfully"

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY (after deletion, before building response)
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 5: Build response data (no DB access needed)
        response_data = {
            "success": True,
            "message": success_message
        }

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=response_data,
            message=success_message
        )

    except HTTPException:
        try:
            service.rollback_all()
        except:
            pass
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting specification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete specification"
        ) from e


# ============================================================================
# 6. List Specifications by Category
# ============================================================================

@project_router.get("/category/{category}", response_model=Dict[str, Any])
def list_specifications_by_category(
    project_id: str,
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    List specifications for a specific category.

    Returns only current (not superseded) specifications for the specified category,
    with pagination support.

    Args:
        project_id: Project UUID
        category: Specification category
        skip: Number of specifications to skip (pagination)
        limit: Maximum number of specifications to return
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with success status and specifications list
    """
    try:
        # Parse project UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    # Validate category format
    if not category or len(category) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category format"
        )

    try:
        # PHASE 1: Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Query specifications by category (only current ones)
        from ..models.specification import Specification
        query = service.specs_session.query(Specification).filter(
            Specification.project_id == project_uuid,
            Specification.category == category,
            Specification.is_current == True
        )

        # Get total count
        total = query.count()

        # Apply pagination
        specifications = query.offset(skip).limit(limit).all()

        # PHASE 2: Convert all attributes to primitives WHILE SESSION IS STILL ACTIVE
        specs_data = []
        for spec in specifications:
            try:
                spec_dict = {
                    "id": str(spec.id),
                    "project_id": str(spec.project_id),
                    "category": spec.category,
                    "key": spec.key,
                    "value": spec.value,
                    "source": spec.source,
                    "content": spec.content,
                    "confidence": float(spec.confidence) if spec.confidence else None,
                    "is_current": spec.is_current,
                    "created_at": spec.created_at.isoformat() if spec.created_at else None,
                    "updated_at": spec.updated_at.isoformat() if spec.updated_at else None
                }
                specs_data.append(spec_dict)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error converting specification {getattr(spec, 'id', 'unknown')}: {e}")
                continue

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY (after conversion, before building response)
        try:
            service.specs_session.close()
        except:
            pass

        # PHASE 5: Build response data from cached primitives (no DB access)
        response_data = {
            "specifications": specs_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "category": category
        }

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=response_data,
            message=f"Specifications for category '{category}' retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing specifications by category: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list specifications"
        ) from e

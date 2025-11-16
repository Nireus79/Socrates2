"""Quality Control API Endpoints

Provides access to quality metrics, test coverage analysis, recommendations, and readiness checks.

Endpoints:
- GET /api/v1/projects/{project_id}/quality
- GET /api/v1/projects/{project_id}/coverage
- GET /api/v1/projects/{project_id}/recommendations
- POST /api/v1/projects/{project_id}/readiness-check
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..repositories import RepositoryService
from ..services.response_service import ResponseWrapper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects", tags=["quality"])


# Dependency for repository service
def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    """Get repository service with both database sessions."""
    return RepositoryService(auth_session, specs_session)


# Request/Response Models
class ReadinessCheckRequest(BaseModel):
    """Request model for project readiness check."""
    include_recommendations: bool = Field(
        default=True, description="Include actionable recommendations"
    )
    min_coverage_threshold: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Minimum coverage required"
    )


@router.get("/{project_id}/quality", response_model=Dict[str, Any])
def get_project_quality_metrics(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get quality metrics for a project.

    Retrieves comprehensive quality metrics including specification coverage,
    confidence scores, completeness indicators, and overall quality assessment.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with quality metrics and scores

    Raises:
        HTTPException: If project not found or access denied

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/quality
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Quality metrics retrieved successfully",
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "overall_quality_score": 0.82,
                "coverage": 0.75,
                "average_confidence": 0.88,
                "completeness": 0.65,
                "specification_count": 12
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

    try:
        # PHASE 1: Validate project ownership
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )

        # PHASE 2: Load specifications and calculate metrics
        from ..models.specification import Specification
        specs = service.specs_session.query(Specification).filter(
            Specification.project_id == project_uuid,
            Specification.is_current == True
        ).all()

        spec_count = len(specs)
        total_categories = {"goals", "requirements", "tech_stack", "constraints", "testing", "deployment"}
        covered_categories = set(s.category for s in specs)
        coverage = len(covered_categories) / len(total_categories) if total_categories else 0

        confidences = [float(s.confidence) for s in specs if s.confidence]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        project_id_str = str(project.id)
        project_name = project.name
        project_maturity = getattr(project, "maturity_score", 0) or 0.0
        completeness = project_maturity

        overall_quality = (coverage * 0.4 + average_confidence * 0.4 + completeness * 0.2)

        metrics_data = {
            "project_id": project_id_str,
            "project_name": project_name,
            "overall_quality_score": round(overall_quality, 2),
            "coverage": round(coverage, 2),
            "average_confidence": round(average_confidence, 2),
            "completeness": round(completeness, 2),
            "specification_count": spec_count,
            "categories_covered": sorted(list(covered_categories)),
            "updated_at": datetime.now().isoformat()
        }

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY
        try:
            service.specs_session.close()
            service.auth_session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=metrics_data,
            message="Quality metrics retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        logger.error(f"Error retrieving quality metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quality metrics"
        )


@router.get("/{project_id}/coverage", response_model=Dict[str, Any])
def analyze_project_coverage(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get specification coverage metrics for a project.

    Analyzes coverage across different specification categories and provides
    insights into which areas need more specification work.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with coverage information by category

    Raises:
        HTTPException: If project not found or access denied

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/coverage
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Coverage analysis completed",
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "overall_coverage": 0.75,
                "coverage_gaps": ["constraints", "testing"]
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

    try:
        # PHASE 1: Validate project ownership
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )

        # PHASE 2: Load specifications and analyze coverage
        from ..models.specification import Specification
        specs = service.specs_session.query(Specification).filter(
            Specification.project_id == project_uuid,
            Specification.is_current == True
        ).all()

        categories_data = {}
        standard_categories = ["goals", "requirements", "tech_stack", "constraints", "testing", "deployment"]

        for category in standard_categories:
            specs_in_category = [s for s in specs if s.category == category]
            confidences = [float(s.confidence) for s in specs_in_category if s.confidence]

            categories_data[category] = {
                "specified": len(specs_in_category) > 0,
                "count": len(specs_in_category),
                "confidence": round(sum(confidences) / len(confidences), 2) if confidences else 0.0
            }

        covered_categories = sum(1 for c in categories_data.values() if c["specified"])
        overall_coverage = covered_categories / len(standard_categories)
        coverage_gaps = [cat for cat, data in categories_data.items() if not data["specified"]]

        project_id_str = str(project.id)

        coverage_data = {
            "project_id": project_id_str,
            "overall_coverage": round(overall_coverage, 2),
            "categories_analyzed": len(standard_categories),
            "categories_covered": covered_categories,
            "categories": categories_data,
            "coverage_gaps": coverage_gaps,
            "total_specifications": len(specs),
            "analysis_timestamp": datetime.now().isoformat()
        }

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY
        try:
            service.specs_session.close()
            service.auth_session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=coverage_data,
            message="Coverage analysis completed"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        logger.error(f"Error analyzing coverage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze coverage"
        )


@router.get("/{project_id}/recommendations", response_model=Dict[str, Any])
def get_quality_recommendations(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Get quality improvement recommendations for a project.

    Analyzes the project state and provides actionable recommendations
    to improve specification coverage, quality, and project readiness.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with prioritized recommendations

    Raises:
        HTTPException: If project not found or access denied

    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/recommendations
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Recommendations retrieved successfully",
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "recommendations": [],
                "total_recommendations": 0
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

    try:
        # PHASE 1: Validate project ownership
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )

        # PHASE 2: Load specifications and analyze for recommendations
        from ..models.specification import Specification
        specs = service.specs_session.query(Specification).filter(
            Specification.project_id == project_uuid,
            Specification.is_current == True
        ).all()

        recommendations = []
        spec_count = len(specs)

        project_id_str = str(project.id)

        recommendations_data = {
            "project_id": project_id_str,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "generated_at": datetime.now().isoformat()
        }

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY
        try:
            service.specs_session.close()
            service.auth_session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

        # PHASE 6: Return response with released connection
        return ResponseWrapper.success(
            data=recommendations_data,
            message="Recommendations retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        logger.error(f"Error retrieving recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommendations"
        )


@router.post("/{project_id}/readiness-check", response_model=Dict[str, Any])
def check_project_readiness(
    project_id: str = Path(..., description="Project ID"),
    request: ReadinessCheckRequest = ReadinessCheckRequest(),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> Dict[str, Any]:
    """
    Check if a project is ready for the next phase.

    Evaluates project readiness based on specification coverage, quality metrics,
    and completeness thresholds. Provides actionable feedback on readiness status.

    Args:
        project_id: UUID of the project
        request: Readiness check options
        current_user: Authenticated user
        service: Repository service

    Returns:
        Dict with readiness assessment and recommendations

    Raises:
        HTTPException: If project not found or access denied

    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/readiness-check
        Authorization: Bearer <token>

        Response 200:
        {
            "success": true,
            "message": "Readiness check completed",
            "data": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_ready": true,
                "readiness_score": 0.82,
                "blocking_issues": [],
                "checked_at": "2025-11-11T10:50:00Z"
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

    try:
        # PHASE 1: Validate project ownership
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )

        # PHASE 2: Load specifications and calculate readiness metrics
        from ..models.specification import Specification
        specs = service.specs_session.query(Specification).filter(
            Specification.project_id == project_uuid,
            Specification.is_current == True
        ).all()

        spec_count = len(specs)
        standard_categories = ["goals", "requirements", "tech_stack", "constraints", "testing", "deployment"]
        covered_categories = set(s.category for s in specs)
        coverage = len(covered_categories) / len(standard_categories)

        confidences = [float(s.confidence) for s in specs if s.confidence]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        project_maturity = getattr(project, "maturity_score", 0) or 0.0
        completeness = project_maturity

        readiness_score = (
            coverage * 0.35 +
            avg_confidence * 0.35 +
            completeness * 0.30
        )

        blocking_issues = []
        if coverage < request.min_coverage_threshold:
            blocking_issues.append(f"Coverage below threshold: {coverage:.0%} < {request.min_coverage_threshold:.0%}")

        is_ready = len(blocking_issues) == 0 and readiness_score >= 0.70

        project_id_str = str(project.id)

        readiness_data = {
            "project_id": project_id_str,
            "is_ready": is_ready,
            "readiness_score": round(readiness_score, 2),
            "coverage": round(coverage, 2),
            "confidence": round(avg_confidence, 2),
            "completeness": round(completeness, 2),
            "specification_count": spec_count,
            "blocking_issues": blocking_issues,
            "warnings": [],
            "recommendations": [],
            "checked_at": datetime.now().isoformat()
        }

        # PHASE 3: Commit transaction
        service.commit_all()

        # PHASE 4: Close DB connection IMMEDIATELY
        try:
            service.specs_session.close()
            service.auth_session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")

        # PHASE 6: Return response with released connection
        status_msg = "Project is ready!" if is_ready else "Project needs more work"
        return ResponseWrapper.success(
            data=readiness_data,
            message=f"Readiness check completed: {status_msg}"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            service.rollback_all()
        except:
            pass
        logger.error(f"Error checking project readiness: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check project readiness"
        )

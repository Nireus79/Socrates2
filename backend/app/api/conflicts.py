"""
Conflicts API endpoints.

Provides:
- List conflicts for a project
- Get conflict details
- Resolve conflicts
- Get resolution options
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agents.orchestrator import get_orchestrator
from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/conflicts", tags=["conflicts"])


class ResolveConflictRequest(BaseModel):
    """Request model for resolving a conflict."""
    resolution: str  # 'keep_old', 'replace', 'merge', 'ignore'
    resolution_notes: Optional[str] = None


@router.get("/project/{project_id}")
def list_project_conflicts(
    project_id: str = Path(..., description="Project ID"),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    List all conflicts for a project.

    Args:
        project_id: UUID of the project
        status: Optional filter by status ('open', 'resolved', 'ignored')
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'conflicts': List[dict],
            'count': int
        }

    Example:
        GET /api/v1/conflicts/project/abc-123?status=open
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "conflicts": [
                {
                    "id": "conflict-123",
                    "type": "technology",
                    "description": "...",
                    "severity": "high",
                    "status": "open",
                    ...
                }
            ],
            "count": 1
        }
    """
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Call conflict detector agent
    result = orchestrator.route_request(
        agent_id='conflict',
        action='list_conflicts',
        data={
            'project_id': project_id,
            'status': status
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to list conflicts')
        )

    return result


@router.get("/{conflict_id}")
def get_conflict_details(
    conflict_id: str = Path(..., description="Conflict ID"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific conflict.

    Args:
        conflict_id: UUID of the conflict
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'conflict': dict,
            'specifications': List[dict]
        }

    Example:
        GET /api/v1/conflicts/conflict-123
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "conflict": {
                "id": "conflict-123",
                "type": "technology",
                "description": "Conflicting database choices",
                "severity": "high",
                "spec_ids": ["spec-1", "spec-2"],
                ...
            },
            "specifications": [
                {"id": "spec-1", "content": "Use PostgreSQL", ...},
                {"id": "spec-2", "content": "Use MySQL", ...}
            ]
        }
    """
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Call conflict detector agent
    result = orchestrator.route_request(
        agent_id='conflict',
        action='get_conflict_details',
        data={'conflict_id': conflict_id}
    )

    if not result.get('success'):
        error_code = result.get('error_code')
        if error_code == 'CONFLICT_NOT_FOUND':
            raise HTTPException(status_code=404, detail='Conflict not found')
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to get conflict details')
        )

    return result


@router.get("/{conflict_id}/options")
def get_resolution_options(
    conflict_id: str = Path(..., description="Conflict ID"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get available resolution options for a conflict.

    Args:
        conflict_id: UUID of the conflict
        current_user: Authenticated user

    Returns:
        {
            'conflict_id': str,
            'options': List[dict]
        }

    Example:
        GET /api/v1/conflicts/conflict-123/options
        Authorization: Bearer <token>

        Response:
        {
            "conflict_id": "conflict-123",
            "options": [
                {
                    "value": "keep_old",
                    "label": "Keep existing specification",
                    "description": "Discard the new specification"
                },
                {
                    "value": "replace",
                    "label": "Replace with new",
                    "description": "Replace existing with new specification"
                },
                {
                    "value": "merge",
                    "label": "Merge both",
                    "description": "Keep both specifications"
                },
                {
                    "value": "ignore",
                    "label": "Ignore conflict",
                    "description": "Mark as ignored, no changes"
                }
            ]
        }
    """
    # Resolution options are static for now
    # In Phase 4+, these could be dynamically generated based on conflict type
    options = [
        {
            "value": "keep_old",
            "label": "Keep existing specification",
            "description": "Discard the new specification and keep the existing one"
        },
        {
            "value": "replace",
            "label": "Replace with new",
            "description": "Replace the existing specification with the new one"
        },
        {
            "value": "merge",
            "label": "Merge both",
            "description": "Keep both specifications as separate entries"
        },
        {
            "value": "ignore",
            "label": "Ignore this conflict",
            "description": "Mark the conflict as ignored without making changes"
        }
    ]

    return {
        "conflict_id": conflict_id,
        "options": options
    }


@router.post("/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: str = Path(..., description="Conflict ID"),
    request: ResolveConflictRequest = ...,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Resolve a conflict with user's decision.

    Args:
        conflict_id: UUID of the conflict
        request: Resolution request with resolution type and notes
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'conflict': dict
        }

    Example:
        POST /api/v1/conflicts/conflict-123/resolve
        Authorization: Bearer <token>
        Content-Type: application/json

        {
            "resolution": "replace",
            "resolution_notes": "User prefers the newer database choice"
        }

        Response:
        {
            "success": true,
            "conflict": {
                "id": "conflict-123",
                "status": "resolved",
                "resolution": "replace: User prefers the newer database choice",
                "resolved_at": "2025-11-07T12:34:56Z",
                ...
            }
        }
    """
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Call conflict detector agent
    result = orchestrator.route_request(
        agent_id='conflict',
        action='resolve_conflict',
        data={
            'conflict_id': conflict_id,
            'resolution': request.resolution,
            'resolution_notes': request.resolution_notes
        }
    )

    if not result.get('success'):
        error_code = result.get('error_code')
        if error_code == 'CONFLICT_NOT_FOUND':
            raise HTTPException(status_code=404, detail='Conflict not found')
        elif error_code == 'INVALID_RESOLUTION':
            raise HTTPException(status_code=400, detail=result.get('error'))
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to resolve conflict')
        )

    return result

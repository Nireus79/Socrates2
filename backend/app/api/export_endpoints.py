"""
Export API endpoints.

Provides:
- Export projects to various formats (Markdown, PDF, JSON, Code)
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from sqlalchemy.orm import Session

from ..agents.orchestrator import get_orchestrator
from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/projects", tags=["export"])


@router.get("/{project_id}/export/markdown")
def export_markdown(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Response:
    """
    Export project specifications as Markdown.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Markdown file content

    Example:
        GET /api/v1/projects/abc-123/export/markdown
        Authorization: Bearer <token>

        Response: (Markdown content as text/markdown)
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='export',
        action='export_markdown',
        data={'project_id': project_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 400,
            detail=result.get('error', 'Failed to export project')
        )

    content = result.get('content', '')
    filename = result.get('filename', 'project_specs.md')

    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{project_id}/export/json")
def export_json(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Response:
    """
    Export project data as JSON.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        JSON file content

    Example:
        GET /api/v1/projects/abc-123/export/json
        Authorization: Bearer <token>

        Response: (JSON content as application/json)
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='export',
        action='export_json',
        data={'project_id': project_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 400,
            detail=result.get('error', 'Failed to export project')
        )

    content = result.get('content', '')
    filename = result.get('filename', 'project_export.json')

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{project_id}/export/pdf")
def export_pdf(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Export project as PDF (placeholder).

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Status message

    Example:
        GET /api/v1/projects/abc-123/export/pdf
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "message": "PDF export not yet implemented...",
            ...
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='export',
        action='export_pdf',
        data={'project_id': project_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 400,
            detail=result.get('error', 'Failed to export project')
        )

    return result


@router.get("/{project_id}/export/code")
def export_code(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Export generated code (placeholder).

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Status message

    Example:
        GET /api/v1/projects/abc-123/export/code
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "message": "Code export not yet implemented...",
            ...
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='export',
        action='export_code',
        data={'project_id': project_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 400,
            detail=result.get('error', 'Failed to export code')
        )

    return result

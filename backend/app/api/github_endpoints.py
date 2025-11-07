"""
GitHub Integration API endpoints.

Provides:
- Import GitHub repositories
- Analyze repositories
- List repositories (placeholder)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..agents.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/v1/github", tags=["github"])


class ImportRepoRequest(BaseModel):
    """Request model for importing a GitHub repository."""
    repo_url: str  # e.g., "https://github.com/user/repo"
    project_name: str = None  # Optional custom project name


class AnalyzeRepoRequest(BaseModel):
    """Request model for analyzing a GitHub repository."""
    repo_url: str


@router.post("/import")
def import_repository(
    request: ImportRepoRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Import GitHub repository and create project.

    Args:
        request: Repository details
        current_user: Authenticated user
        db: Database session

    Returns:
        {
            'success': bool,
            'project_id': str,
            'specs_extracted': int,
            'analysis': dict
        }

    Example:
        POST /api/v1/github/import
        Authorization: Bearer <token>
        {
            "repo_url": "https://github.com/user/repo",
            "project_name": "My Project"
        }

        Response:
        {
            "success": true,
            "project_id": "abc-123",
            "specs_extracted": 5,
            "analysis": {...},
            "note": "Full GitHub integration requires GitPython..."
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='github',
        action='import_repository',
        data={
            'user_id': current_user.id,
            'repo_url': request.repo_url,
            'project_name': request.project_name
        }
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to import repository')
        )

    return result


@router.post("/analyze")
def analyze_repository(
    request: AnalyzeRepoRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Analyze GitHub repository structure.

    Args:
        request: Repository URL
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'analysis': dict
        }

    Example:
        POST /api/v1/github/analyze
        Authorization: Bearer <token>
        {
            "repo_url": "https://github.com/user/repo"
        }

        Response:
        {
            "success": true,
            "analysis": {
                "owner": "user",
                "repository": "repo",
                "languages": {...},
                "frameworks": [...],
                ...
            },
            "note": "Full repository analysis requires cloning..."
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='github',
        action='analyze_repository',
        data={'repo_url': request.repo_url}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to analyze repository')
        )

    return result


@router.get("/repos")
def list_repositories(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List user's GitHub repositories (placeholder).

    Args:
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'repositories': List[dict],
            'message': str
        }

    Example:
        GET /api/v1/github/repos
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "repositories": [],
            "message": "GitHub repository listing not yet implemented",
            "note": "Requires GitHub OAuth integration"
        }
    """
    orchestrator = get_orchestrator()

    result = orchestrator.route_request(
        agent_id='github',
        action='list_repositories',
        data={'user_id': current_user.id}
    )

    return result

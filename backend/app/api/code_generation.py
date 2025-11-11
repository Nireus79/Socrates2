"""
Code Generation API endpoints.

Provides:
- Generate code from specifications
- Check generation status
- Download generated code
"""
import io
import zipfile
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agents.orchestrator import get_orchestrator
from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.generated_file import GeneratedFile
from ..models.generated_project import GeneratedProject
from ..models.user import User

router = APIRouter(prefix="/api/v1/code", tags=["code-generation"])


class GenerateCodeRequest(BaseModel):
    """Request model for code generation."""
    project_id: str


@router.post("/generate")
def generate_code(
    request: GenerateCodeRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Generate code from project specifications.

    Requires:
    - Project maturity = 100%
    - No unresolved conflicts

    Args:
        request: GenerateCodeRequest with project_id
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'generation_id': str,
            'total_files': int,
            'total_lines': int,
            'generation_version': int
        }

    Raises:
        HTTPException 400: If maturity < 100% or conflicts exist
        HTTPException 404: If project not found

    Example:
        POST /api/v1/code/generate
        Authorization: Bearer <token>
        Content-Type: application/json

        {
            "project_id": "abc-123"
        }

        Response:
        {
            "success": true,
            "generation_id": "gen-456",
            "total_files": 15,
            "total_lines": 1247,
            "generation_version": 1
        }
    """
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Call code generator agent
    result = orchestrator.route_request(
        agent_id='code_generator',
        action='generate_code',
        data={'project_id': request.project_id}
    )

    if not result.get('success'):
        error_code = result.get('error_code')

        if error_code == 'PROJECT_NOT_FOUND':
            raise HTTPException(status_code=404, detail='Project not found')
        elif error_code == 'MATURITY_NOT_REACHED':
            raise HTTPException(
                status_code=400,
                detail={
                    'error': result.get('error'),
                    'maturity_score': result.get('maturity_score'),
                    'missing_categories': result.get('missing_categories')
                }
            )
        elif error_code == 'UNRESOLVED_CONFLICTS':
            raise HTTPException(
                status_code=400,
                detail={
                    'error': result.get('error'),
                    'unresolved_count': result.get('unresolved_count')
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Code generation failed')
            )

    return result


@router.get("/{generation_id}/status")
def get_generation_status(
    generation_id: str = Path(..., description="Generation ID"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get status of a code generation.

    Args:
        generation_id: UUID of the generation
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'generation': {
                'id': str,
                'project_id': str,
                'generation_version': int,
                'total_files': int,
                'total_lines': int,
                'generation_status': str,
                'generation_started_at': str,
                'generation_completed_at': str,
                'error_message': str (if failed)
            }
        }

    Example:
        GET /api/v1/code/gen-456/status
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "generation": {
                "id": "gen-456",
                "generation_status": "completed",
                "total_files": 15,
                "total_lines": 1247,
                ...
            }
        }
    """
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Call code generator agent
    result = orchestrator.route_request(
        agent_id='code_generator',
        action='get_generation_status',
        data={'generation_id': generation_id}
    )

    if not result.get('success'):
        error_code = result.get('error_code')
        if error_code == 'GENERATION_NOT_FOUND':
            raise HTTPException(status_code=404, detail='Generation not found')
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to get generation status')
        )

    return result


@router.get("/{generation_id}/download")
def download_generated_code(
    generation_id: str = Path(..., description="Generation ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """
    Download generated code as a ZIP file.

    Args:
        generation_id: UUID of the generation
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse with ZIP file containing all generated files

    Example:
        GET /api/v1/code/gen-456/download
        Authorization: Bearer <token>

        Response: application/zip with filename=generated-code-v1.zip
    """
    # Load generation
    generation = db.query(GeneratedProject).filter(
        GeneratedProject.id == generation_id
    ).first()

    if not generation:
        raise HTTPException(status_code=404, detail='Generation not found')

    if generation.generation_status.value != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f'Generation is not completed (status: {generation.generation_status.value})'
        )

    # Load all files
    files = db.query(GeneratedFile).filter(
        GeneratedFile.generated_project_id == generation_id
    ).all()

    if not files:
        raise HTTPException(status_code=404, detail='No files found for this generation')

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            zip_file.writestr(file.file_path, file.file_content or '')

    # Reset buffer position
    zip_buffer.seek(0)

    # Return as streaming response
    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename=generated-code-v{generation.generation_version}.zip'
        }
    )


@router.get("/project/{project_id}/generations")
def list_project_generations(
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List all code generations for a project.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user

    Returns:
        {
            'success': bool,
            'generations': List[dict],
            'count': int
        }

    Example:
        GET /api/v1/code/project/abc-123/generations
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "generations": [
                {
                    "id": "gen-456",
                    "generation_version": 2,
                    "generation_status": "completed",
                    "total_files": 15,
                    ...
                },
                {
                    "id": "gen-123",
                    "generation_version": 1,
                    "generation_status": "completed",
                    "total_files": 12,
                    ...
                }
            ],
            "count": 2
        }
    """
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Call code generator agent
    result = orchestrator.route_request(
        agent_id='code_generator',
        action='list_generations',
        data={'project_id': project_id}
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=400,
            detail=result.get('error', 'Failed to list generations')
        )

    return result

"""Project export API endpoints.

Handles exporting project specifications in multiple formats (JSON, CSV, Markdown, YAML, HTML).
"""
import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.project import Project
from ..models.specification import Specification
from ..models.user import User
from ..services.export_service import ExportService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.get("/projects/{project_id}/specs")
async def export_project_specs(
    project_id: str,
    format: str = Query("json", regex="^(json|csv|markdown|yaml|html)$"),
    include_metadata: bool = Query(True),
    group_by_category: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Export project specifications in specified format.

    Exports all specifications for a project in the requested format.
    Supports JSON, CSV, Markdown, YAML, and HTML.

    Args:
        project_id: Project ID to export
        format: Export format (json, csv, markdown, yaml, html)
        include_metadata: Include metadata in export
        group_by_category: Group specifications by category (for markdown/html)
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Exported specifications in requested format

    Raises:
        HTTPException: If project not found or export fails

    Example:
        GET /api/v1/export/projects/proj_123/specs?format=csv

        Response (CSV):
        "category,key,value,source,confidence
        goals,objective1,Build scalable API,user_input,0.95
        tech_stack,api_framework,FastAPI,extracted,0.92
        ..."

        Or for JSON:
        {
            "format": "json",
            "project_id": "proj_123",
            "project_name": "Example Project",
            "exported_at": "2025-11-11T10:30:00Z",
            "specs_count": 45,
            "specifications": [
                {
                    "category": "goals",
                    "key": "objective1",
                    "value": "Build scalable API",
                    "source": "user_input",
                    "confidence": 0.95
                },
                ...
            ]
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Fetch specifications
        specs_query = db_specs.query(Specification).filter(
            Specification.project_id == project_id,
            Specification.is_current == True
        ).all()

        # Convert to dictionaries for export service
        specs_data = []
        for spec in specs_query:
            specs_data.append({
                "category": spec.category,
                "key": spec.key,
                "value": spec.value,
                "content": spec.content,
                "source": spec.source,
                "confidence": float(spec.confidence) if spec.confidence else None,
                "created_at": spec.created_at.isoformat() if spec.created_at else None,
                "updated_at": spec.updated_at.isoformat() if spec.updated_at else None
            })

        # Export using the export service
        exported_content = ExportService.export(
            format=format,
            project_name=project.name,
            project_id=str(project_id),
            specifications=specs_data,
            include_metadata=include_metadata,
            group_by_category=group_by_category
        )

        logger.info(
            f"Exported {len(specs_data)} specifications from project {project_id} "
            f"in {format} format"
        )

        # Return response based on format
        if format.lower() == "json":
            # JSON is already a dict, parse and return
            import json
            return json.loads(exported_content)
        elif format.lower() == "csv":
            return {
                "format": "csv",
                "project_id": str(project_id),
                "project_name": project.name,
                "specs_count": len(specs_data),
                "content": exported_content,
                "content_type": "text/csv"
            }
        elif format.lower() == "markdown":
            return {
                "format": "markdown",
                "project_id": str(project_id),
                "project_name": project.name,
                "specs_count": len(specs_data),
                "content": exported_content,
                "content_type": "text/markdown"
            }
        elif format.lower() == "yaml":
            return {
                "format": "yaml",
                "project_id": str(project_id),
                "project_name": project.name,
                "specs_count": len(specs_data),
                "content": exported_content,
                "content_type": "application/x-yaml"
            }
        elif format.lower() == "html":
            return {
                "format": "html",
                "project_id": str(project_id),
                "project_name": project.name,
                "specs_count": len(specs_data),
                "content": exported_content,
                "content_type": "text/html"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export project specifications: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.post("/projects/{project_id}/download")
async def download_project_specs(
    project_id: str,
    format: str = Query("json", regex="^(json|csv|markdown|yaml|html)$"),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Download project specifications as a file.

    Returns file metadata with content for download. Frontend should
    handle creating and downloading the file based on format.

    Args:
        project_id: Project ID to download
        format: Download format
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        File metadata with content for download

    Example:
        POST /api/v1/export/projects/proj_123/download?format=csv

        Response:
        {
            "filename": "example-project_specs.csv",
            "format": "csv",
            "content_type": "text/csv",
            "content": "category,key,value,...",
            "size": 1024,
            "created_at": "2025-11-11T10:30:00Z"
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Fetch specifications
        specs_query = db_specs.query(Specification).filter(
            Specification.project_id == project_id,
            Specification.is_current == True
        ).all()

        specs_data = []
        for spec in specs_query:
            specs_data.append({
                "category": spec.category,
                "key": spec.key,
                "value": spec.value,
                "content": spec.content,
                "source": spec.source,
                "confidence": float(spec.confidence) if spec.confidence else None,
            })

        # Generate export
        exported_content = ExportService.export(
            format=format,
            project_name=project.name,
            project_id=str(project_id),
            specifications=specs_data
        )

        # Determine filename and content type
        format_lower = format.lower()
        if format_lower == "json":
            filename = f"{project.name.replace(' ', '-').lower()}_specs.json"
            content_type = "application/json"
        elif format_lower == "csv":
            filename = f"{project.name.replace(' ', '-').lower()}_specs.csv"
            content_type = "text/csv"
        elif format_lower == "markdown":
            filename = f"{project.name.replace(' ', '-').lower()}_specs.md"
            content_type = "text/markdown"
        elif format_lower == "yaml":
            filename = f"{project.name.replace(' ', '-').lower()}_specs.yaml"
            content_type = "application/x-yaml"
        elif format_lower == "html":
            filename = f"{project.name.replace(' ', '-').lower()}_specs.html"
            content_type = "text/html"
        else:
            filename = f"{project.name.replace(' ', '-').lower()}_specs.txt"
            content_type = "text/plain"

        logger.info(f"Downloaded project {project_id} as {format}")

        return {
            "filename": filename,
            "format": format,
            "content_type": content_type,
            "content": exported_content,
            "size": len(exported_content.encode('utf-8')),
            "created_at": project.updated_at.isoformat() if project.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download project specifications: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.get("/formats")
async def get_supported_formats(
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Get list of supported export formats.

    Returns information about each supported format.

    Returns:
        Supported export formats with descriptions

    Example:
        GET /api/v1/export/formats

        Response:
        {
            "formats": [
                {
                    "name": "json",
                    "description": "JSON format",
                    "file_extension": "json",
                    "content_type": "application/json",
                    "best_for": "API integration, data interchange"
                },
                {
                    "name": "csv",
                    "description": "CSV spreadsheet format",
                    "file_extension": "csv",
                    "content_type": "text/csv",
                    "best_for": "Excel, spreadsheet analysis"
                },
                {
                    "name": "markdown",
                    "description": "Markdown document",
                    "file_extension": "md",
                    "content_type": "text/markdown",
                    "best_for": "Documentation, wikis, GitHub"
                },
                {
                    "name": "yaml",
                    "description": "YAML configuration",
                    "file_extension": "yaml",
                    "content_type": "application/x-yaml",
                    "best_for": "Configuration files, Kubernetes"
                },
                {
                    "name": "html",
                    "description": "HTML document",
                    "file_extension": "html",
                    "content_type": "text/html",
                    "best_for": "Web viewing, printing"
                }
            ]
        }
    """
    return {
        "formats": [
            {
                "name": "json",
                "description": "JSON format with full metadata",
                "file_extension": "json",
                "content_type": "application/json",
                "best_for": "API integration, data interchange",
                "features": ["metadata", "structured_data"]
            },
            {
                "name": "csv",
                "description": "CSV spreadsheet format",
                "file_extension": "csv",
                "content_type": "text/csv",
                "best_for": "Excel, spreadsheet analysis",
                "features": ["tabular", "sortable"]
            },
            {
                "name": "markdown",
                "description": "Markdown documentation",
                "file_extension": "md",
                "content_type": "text/markdown",
                "best_for": "Documentation, wikis, GitHub",
                "features": ["human_readable", "categorized", "styled"]
            },
            {
                "name": "yaml",
                "description": "YAML configuration format",
                "file_extension": "yaml",
                "content_type": "application/x-yaml",
                "best_for": "Configuration files, Kubernetes",
                "features": ["human_readable", "nested"]
            },
            {
                "name": "html",
                "description": "Styled HTML document",
                "file_extension": "html",
                "content_type": "text/html",
                "best_for": "Web viewing, printing",
                "features": ["styled", "interactive", "colored_priority"]
            }
        ]
    }

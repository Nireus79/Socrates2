"""
Multi-domain workflow API endpoints for Socrates.

Provides REST API for creating and managing multi-domain specifications
with unified validation and cross-domain conflict detection.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_active_user
from app.domains.workflows import get_workflow_manager
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a workflow."""
    name: str
    description: str
    domains: List[str]
    status: str = "active"


@router.post("", summary="Create a new multi-domain workflow", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new multi-domain workflow.

    Args:
        request: Workflow details (name, description, domains)
        current_user: Authenticated user

    Returns:
        Workflow details

    Raises:
        HTTPException: If workflow already exists
    """
    if not request.domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one domain is required"
        )

    manager = get_workflow_manager()
    workflow_id = f"{request.name.lower().replace(' ', '_')}_{current_user.id}"

    try:
        workflow = manager.create_workflow(workflow_id)
        return {
            "id": workflow_id,
            "name": request.name,
            "description": request.description,
            "status": request.status,
            "domains": request.domains,
            "message": f"Workflow '{request.name}' created successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", summary="List all workflows")
async def list_workflows(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List all multi-domain workflows.

    Args:
        current_user: Authenticated user

    Returns:
        List of workflow IDs
    """
    manager = get_workflow_manager()
    workflows = manager.list_workflows()

    return {
        "total_workflows": len(workflows),
        "workflows": workflows,
    }


@router.get("/{workflow_id}", summary="Get workflow details")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    Get details of a specific workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Workflow details and domain specifications

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        return {
            "workflow_id": workflow_id,
            "domains": workflow.get_involved_domains(),
            "domain_count": len(workflow.domain_specs),
            "domain_specs": {k: v.to_dict() for k, v in workflow.domain_specs.items()},
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workflow_id}/add-domain", summary="Add domain to workflow")
async def add_domain_to_workflow(
    workflow_id: str,
    domain_id: str,
    responses: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Add a domain specification to a workflow.

    Args:
        workflow_id: Workflow identifier
        domain_id: Domain to add
        responses: Answers/responses from domain questions

    Returns:
        Updated workflow details

    Raises:
        HTTPException: If workflow or domain not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        workflow.add_domain_spec(domain_id, responses)

        return {
            "workflow_id": workflow_id,
            "domain_added": domain_id,
            "domains": workflow.get_involved_domains(),
            "message": f"Domain '{domain_id}' added to workflow",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{workflow_id}/remove-domain", summary="Remove domain from workflow")
async def remove_domain_from_workflow(
    workflow_id: str,
    domain_id: str,
) -> Dict[str, Any]:
    """
    Remove a domain specification from a workflow.

    Args:
        workflow_id: Workflow identifier
        domain_id: Domain to remove

    Returns:
        Updated workflow details

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        workflow.remove_domain_spec(domain_id)

        return {
            "workflow_id": workflow_id,
            "domain_removed": domain_id,
            "domains": workflow.get_involved_domains(),
            "message": f"Domain '{domain_id}' removed from workflow",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workflow_id}/validate", summary="Validate multi-domain workflow")
async def validate_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    Validate a complete multi-domain workflow.

    Performs:
    - Individual domain validation
    - Cross-domain conflict detection
    - Specification consistency checking

    Args:
        workflow_id: Workflow identifier

    Returns:
        Validation results with conflicts and summary

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        result = workflow.validate()

        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{workflow_id}/validate-single", summary="Validate single domain")
async def validate_single_domain(
    workflow_id: str,
    domain_id: str,
) -> Dict[str, Any]:
    """
    Validate a single domain within a workflow.

    Args:
        workflow_id: Workflow identifier
        domain_id: Domain to validate

    Returns:
        Validation result for the domain

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        validation = workflow.validate_single_domain(domain_id)

        return validation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{workflow_id}/conflicts", summary="Get cross-domain conflicts")
async def get_cross_domain_conflicts(workflow_id: str) -> Dict[str, Any]:
    """
    Get all cross-domain conflicts for a workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        List of detected conflicts

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        conflicts = workflow.detect_cross_domain_conflicts()

        return {
            "workflow_id": workflow_id,
            "conflict_count": len(conflicts),
            "conflicts": [c.to_dict() for c in conflicts],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{workflow_id}/categories", summary="Get all categories")
async def get_workflow_categories(workflow_id: str) -> Dict[str, Any]:
    """
    Get all specification categories across domains in workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Categories by domain

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        categories = workflow.get_combined_categories()

        return {
            "workflow_id": workflow_id,
            "domains_count": len(categories),
            "categories": {k: list(v) for k, v in categories.items()},
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workflow_id}/export", summary="Export workflow specification")
async def export_workflow(
    workflow_id: str,
    format_id: str = "json",
) -> Dict[str, Any]:
    """
    Export a workflow specification in a specific format.

    Args:
        workflow_id: Workflow identifier
        format_id: Export format (default: "json")

    Returns:
        Exported specification

    Raises:
        HTTPException: If workflow not found or format unsupported
    """
    manager = get_workflow_manager()

    try:
        workflow = manager.get_workflow(workflow_id)
        return workflow.export_specification(format_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workflow_id}", summary="Delete workflow")
async def delete_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    Delete a workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If workflow not found
    """
    manager = get_workflow_manager()

    try:
        manager.delete_workflow(workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": "deleted",
            "message": f"Workflow '{workflow_id}' deleted successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

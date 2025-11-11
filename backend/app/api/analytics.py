"""
Analytics API endpoints for Socrates2.

Provides REST API access to analytics reports and metrics tracking.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.domains.analytics import get_domain_analytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("", summary="Get overall analytics report")
async def get_overall_analytics() -> Dict[str, Any]:
    """
    Get overall analytics report for all domains.

    Returns:
        Comprehensive analytics report including:
        - Total domain accesses
        - Total questions answered
        - Total exports generated
        - Total conflicts detected
        - Unique domains used
        - Domain-specific reports
        - Workflow tracking stats
    """
    analytics = get_domain_analytics()
    return analytics.get_overall_report()


@router.get("/domains/{domain_id}", summary="Get domain-specific analytics")
async def get_domain_analytics_report(domain_id: str) -> Dict[str, Any]:
    """
    Get analytics report for a specific domain.

    Args:
        domain_id: Domain identifier (e.g., "programming", "testing")

    Returns:
        Domain analytics including:
        - Access count
        - Questions answered count
        - Exports generated count
        - Conflicts detected count
    """
    analytics = get_domain_analytics()
    return analytics.get_domain_report(domain_id)


@router.get("/domains/{domain_id}/metrics", summary="Get domain metrics")
async def get_domain_metrics(domain_id: str) -> Dict[str, Any]:
    """
    Get all metrics collected for a specific domain.

    Args:
        domain_id: Domain identifier

    Returns:
        List of all metrics with timestamps and values
    """
    analytics = get_domain_analytics()
    metrics = analytics.get_domain_metrics(domain_id)

    return {
        "domain_id": domain_id,
        "count": len(metrics),
        "metrics": [m.to_dict() for m in metrics]
    }


@router.get("/domains/top/{limit:int}", summary="Get most used domains")
async def get_most_used_domains(limit: int = 10) -> Dict[str, Any]:
    """
    Get ranking of most used domains.

    Args:
        limit: Maximum number of domains to return (default: 10)

    Returns:
        List of (domain_id, access_count) tuples sorted by usage
    """
    analytics = get_domain_analytics()
    most_used = analytics.get_most_used_domains(limit)

    return {
        "limit": limit,
        "count": len(most_used),
        "domains": [
            {"domain_id": d[0], "access_count": d[1]}
            for d in most_used
        ]
    }


@router.get("/workflows/{workflow_id}", summary="Get workflow analytics")
async def get_workflow_analytics(workflow_id: str) -> Dict[str, Any]:
    """
    Get analytics report for a specific workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Workflow analytics including validation duration, conflicts, quality score

    Raises:
        HTTPException: If workflow not found
    """
    analytics = get_domain_analytics()
    report = analytics.get_workflow_report(workflow_id)

    if "error" in report:
        raise HTTPException(
            status_code=404,
            detail=report["error"]
        )

    return report


@router.get("/quality-summary", summary="Get quality summary")
async def get_quality_summary() -> Dict[str, Any]:
    """
    Get quality summary across all workflows.

    Returns:
        Quality metrics summary including:
        - Average quality score
        - Average specification completeness
        - Workflows analyzed count
        - Total conflicts across workflows
    """
    analytics = get_domain_analytics()
    return analytics.get_quality_summary()


@router.post("/export", summary="Export analytics data")
async def export_analytics(format_id: str = "json") -> Dict[str, Any]:
    """
    Export analytics data in a specific format.

    Args:
        format_id: Export format (default: "json", supported: "json")

    Returns:
        Exported analytics data

    Raises:
        HTTPException: If format not supported
    """
    analytics = get_domain_analytics()

    try:
        return analytics.export_analytics(format_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/questions/{domain_id}/top", summary="Get most answered questions")
async def get_most_answered_questions(domain_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get most answered questions in a domain.

    Args:
        domain_id: Domain identifier
        limit: Maximum number of questions to return (default: 10)

    Returns:
        List of most answered question IDs
    """
    analytics = get_domain_analytics()
    questions = analytics.get_most_answered_questions(domain_id, limit)

    return {
        "domain_id": domain_id,
        "limit": limit,
        "count": len(questions),
        "questions": questions
    }


@router.delete("", summary="Clear all analytics data")
async def clear_analytics() -> Dict[str, str]:
    """
    Clear all collected analytics data.

    WARNING: This operation cannot be undone.

    Returns:
        Confirmation message
    """
    analytics = get_domain_analytics()
    analytics.clear_metrics()

    return {
        "status": "success",
        "message": "All analytics data cleared"
    }

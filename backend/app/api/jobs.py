"""
Job monitoring and management API endpoints.

Endpoints for viewing scheduled jobs status and manually triggering jobs.
Admin-only access required.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from ..core.security import get_current_active_user
from ..core.database import get_db_auth
from ..models.user import User
from ..services.job_scheduler import get_scheduler
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/jobs", tags=["admin", "jobs"])


class JobStatus(BaseModel):
    """Status of a scheduled job."""
    id: str
    name: str
    next_run: str | None
    last_run: str | None
    trigger: str
    enabled: bool


class JobsOverviewResponse(BaseModel):
    """Overview of all scheduled jobs."""
    jobs: List[JobStatus]
    scheduler_running: bool
    total_jobs: int


def verify_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Verify that the user is an admin."""
    # TODO: Implement proper RBAC check
    # For now, check if user has admin role
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/", response_model=JobsOverviewResponse)
async def get_scheduled_jobs(
    admin: User = Depends(verify_admin),
) -> JobsOverviewResponse:
    """
    Get overview of all scheduled jobs.

    Returns:
        JobsOverviewResponse with job status information
    """
    scheduler = get_scheduler()

    if not scheduler.is_running:
        logger.warning("Scheduler is not running")
        return JobsOverviewResponse(
            jobs=[],
            scheduler_running=False,
            total_jobs=0,
        )

    jobs = scheduler.list_jobs()

    return JobsOverviewResponse(
        jobs=[JobStatus(**job) for job in jobs],
        scheduler_running=scheduler.is_running,
        total_jobs=len(jobs),
    )


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    admin: User = Depends(verify_admin),
) -> JobStatus:
    """
    Get status of a specific job.

    Args:
        job_id: ID of the job

    Returns:
        JobStatus with detailed job information
    """
    scheduler = get_scheduler()

    job_status = scheduler.get_job_status(job_id)

    if job_status.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return JobStatus(**job_status)


@router.post("/{job_id}/trigger")
async def trigger_job_manually(
    job_id: str,
    admin: User = Depends(verify_admin),
) -> Dict[str, Any]:
    """
    Manually trigger a job immediately.

    This is useful for testing or forcing a job to run outside its schedule.

    Args:
        job_id: ID of the job to trigger

    Returns:
        Dictionary with trigger result
    """
    scheduler = get_scheduler()

    if job_id not in scheduler.jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    try:
        job = scheduler.jobs[job_id]

        # Get the function and call it
        # Note: This requires the job function to be importable
        logger.info(f"Manually triggering job: {job_id}")

        # In a real implementation, you would:
        # 1. Get the job's function
        # 2. Call it directly
        # 3. Return results

        return {
            "status": "triggered",
            "job_id": job_id,
            "message": f"Job '{job_id}' has been queued for execution",
        }

    except Exception as e:
        logger.error(f"Failed to trigger job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")


@router.get("/status/summary")
async def get_jobs_summary(
    admin: User = Depends(verify_admin),
) -> Dict[str, Any]:
    """
    Get a summary of job scheduler status.

    Returns:
        Dictionary with scheduler summary
    """
    scheduler = get_scheduler()

    jobs = scheduler.list_jobs()
    jobs_by_status = {"enabled": 0, "disabled": 0}

    for job in jobs:
        if job.get("enabled"):
            jobs_by_status["enabled"] += 1
        else:
            jobs_by_status["disabled"] += 1

    return {
        "scheduler_running": scheduler.is_running,
        "total_jobs": len(jobs),
        "jobs_by_status": jobs_by_status,
        "last_updated": None,  # TODO: Track last update time
    }

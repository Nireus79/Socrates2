"""
Background job scheduler using APScheduler.

This module manages scheduled tasks like:
- Daily analytics aggregation
- Email queue processing
- Cache cleanup
- Report generation
"""
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import APScheduler, but make it optional
try:
    from apscheduler.job import Job
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    Job = None  # type: ignore
    AsyncIOScheduler = None  # type: ignore
    CronTrigger = None  # type: ignore


class JobScheduler:
    """Manage background jobs with APScheduler."""

    def __init__(self):
        """Initialize the job scheduler."""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not installed. Job scheduling disabled.")
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.jobs: Dict[str, Job] = {}

    def start(self) -> None:
        """Start the scheduler."""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available. Skipping scheduler startup.")
            return

        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler stopped")

    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        name: Optional[str] = None,
        **trigger_args
    ) -> None:
        """
        Add a scheduled job.

        Args:
            func: Async function to execute
            trigger: Type of trigger ("cron" or "interval")
            job_id: Unique job identifier
            name: Human-readable job name
            **trigger_args: Arguments for the trigger (hour, minute, seconds, etc.)

        Examples:
            # Daily job at 2 AM UTC
            scheduler.add_job(
                aggregate_analytics,
                trigger="cron",
                job_id="daily_analytics",
                hour=2,
                minute=0,
                timezone="UTC"
            )

            # Every 5 minutes
            scheduler.add_job(
                process_email_queue,
                trigger="interval",
                job_id="email_queue",
                minutes=5
            )
        """
        if not APSCHEDULER_AVAILABLE:
            logger.warning(f"APScheduler not available. Job '{job_id}' will not be scheduled.")
            return

        if not self.scheduler:
            raise RuntimeError("Scheduler not started. Call start() first.")

        # Remove existing job with same ID
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            logger.debug(f"Removed existing job: {job_id}")

        if trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        elif trigger == "interval":
            trigger_obj = trigger_args
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

        job = self.scheduler.add_job(
            func,
            trigger=trigger_obj,
            id=job_id,
            name=name or f"Job: {job_id}",
            coalesce=True,  # Skip missed runs, only run once if delayed
            max_instances=1,  # Only one instance at a time
            replace_existing=True,
        )

        self.jobs[job_id] = job
        logger.info(f"Added job: {job_id} ({name or 'unnamed'})")

    def remove_job(self, job_id: str) -> None:
        """
        Remove a scheduled job.

        Args:
            job_id: ID of the job to remove
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not started")

        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Removed job: {job_id}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a scheduled job.

        Args:
            job_id: ID of the job

        Returns:
            Dictionary with job status information
        """
        if job_id not in self.jobs:
            return {"status": "not_found"}

        job = self.jobs[job_id]
        return {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "last_run": getattr(job, "last_run_time", None),
            "trigger": str(job.trigger),
            "enabled": not job.pending if hasattr(job, "pending") else True,
        }

    def get_all_jobs_status(self) -> Dict[str, Any]:
        """
        Get status of all scheduled jobs.

        Returns:
            Dictionary with all jobs status
        """
        return {
            job_id: self.get_job_status(job_id) for job_id in self.jobs.keys()
        }

    def list_jobs(self) -> list[Dict[str, Any]]:
        """
        List all scheduled jobs.

        Returns:
            List of job status dictionaries
        """
        return [self.get_job_status(job_id) for job_id in self.jobs.keys()]

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler is not None and self.scheduler.running


# Global scheduler instance
_scheduler: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """
    Get the global scheduler instance.

    Returns:
        JobScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


def reset_scheduler() -> None:
    """Reset the global scheduler (for testing)."""
    global _scheduler
    if _scheduler and _scheduler.is_running:
        _scheduler.stop()
    _scheduler = None

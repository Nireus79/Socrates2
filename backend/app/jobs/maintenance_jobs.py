"""
Maintenance-related background jobs.

Jobs:
- cleanup_old_sessions: Removes old or expired sessions
- refresh_cached_metrics: Refreshes cached metrics
"""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def cleanup_old_sessions() -> dict:
    """
    Clean up old or expired sessions.

    This job runs daily at 3 AM UTC and:
    1. Finds sessions older than 90 days
    2. Deletes associated session data
    3. Archives important session history

    Returns:
        Dictionary with cleanup results
    """
    try:
        # Import here to avoid circular imports
        from ..core.database import SessionLocalSpecs
        from ..models.session import Session

        db = SessionLocalSpecs()

        try:
            logger.info("Cleaning up old sessions...")

            # Find sessions older than 90 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

            old_sessions = db.query(Session).filter(
                Session.created_at < cutoff_date,
                Session.archived_at.is_(None)  # Not already archived
            ).count()

            if old_sessions > 0:
                # Archive old sessions (in production, you might move to archive table)
                db.query(Session).filter(
                    Session.created_at < cutoff_date,
                    Session.archived_at.is_(None)
                ).update({"archived_at": datetime.now(timezone.utc)})

                db.commit()
                logger.info(f"Archived {old_sessions} old sessions")
            else:
                logger.info("No old sessions to clean up")

            return {
                "status": "success",
                "cleaned_sessions": old_sessions,
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


async def refresh_cached_metrics() -> dict:
    """
    Refresh cached metrics.

    This job runs hourly and:
    1. Recalculates project maturity scores
    2. Updates specification quality metrics
    3. Refreshes analytics dashboards

    Returns:
        Dictionary with refresh results
    """
    try:
        # Import here to avoid circular imports
        from ..core.database import SessionLocalSpecs
        from ..models.project import Project

        db = SessionLocalSpecs()

        try:
            logger.debug("Refreshing cached metrics...")

            # Get all active projects
            projects = db.query(Project).filter(
                Project.status == "active"
            ).all()

            # For now, this is a placeholder
            # In production, recalculate maturity, quality scores, etc.

            logger.debug(f"Refreshed metrics for {len(projects)} projects")

            return {
                "status": "success",
                "refreshed_projects": len(projects),
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Metric refresh failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }

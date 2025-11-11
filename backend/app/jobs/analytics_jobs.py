"""
Analytics-related background jobs.

Jobs:
- aggregate_daily_analytics: Aggregates analytics events into daily metrics
- process_analytics_queue: Processes pending analytics events
"""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def aggregate_daily_analytics() -> dict:
    """
    Aggregate analytics events into daily metrics.

    This job runs daily at 2 AM UTC and:
    1. Fetches all analytics events from the previous day
    2. Groups them by project
    3. Calculates metrics (analyses_count, specs_added, conflicts_resolved)
    4. Saves aggregates to project_metrics table

    Returns:
        Dictionary with aggregation results
    """
    try:
        # Import here to avoid circular imports
        from ..core.database import SessionLocalSpecs
        from ..models.analytics_event import AnalyticsEvent
        from ..models.project_metrics import ProjectMetrics

        db = SessionLocalSpecs()

        try:
            yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
            start_time = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc)
            end_time = start_time + timedelta(days=1)

            logger.info(f"Aggregating analytics for {yesterday}")

            # Get events from yesterday
            events = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.timestamp >= start_time,
                AnalyticsEvent.timestamp < end_time
            ).all()

            if not events:
                logger.info("No analytics events to aggregate")
                return {"status": "success", "aggregated_projects": 0, "total_events": 0}

            # Aggregate by project
            project_aggregates = {}
            for event in events:
                try:
                    event_data = event.event_data or {}
                    project_id = event_data.get("project_id")

                    if not project_id:
                        continue

                    if project_id not in project_aggregates:
                        project_aggregates[project_id] = {
                            "analyses_count": 0,
                            "specs_added": 0,
                            "conflicts_resolved": 0,
                            "sessions_created": 0,
                            "user_id": event.user_id,
                        }

                    if event.event_type == "analysis_run":
                        project_aggregates[project_id]["analyses_count"] += 1
                    elif event.event_type == "spec_added":
                        project_aggregates[project_id]["specs_added"] += 1
                    elif event.event_type == "conflict_resolved":
                        project_aggregates[project_id]["conflicts_resolved"] += 1
                    elif event.event_type == "session_created":
                        project_aggregates[project_id]["sessions_created"] += 1

                except Exception as e:
                    logger.warning(f"Error processing analytics event {event.id}: {e}")
                    continue

            # Save aggregates
            saved_count = 0
            for project_id, metrics in project_aggregates.items():
                try:
                    # Check if metric already exists for this date
                    existing = db.query(ProjectMetrics).filter(
                        ProjectMetrics.project_id == project_id,
                        ProjectMetrics.date == yesterday
                    ).first()

                    if existing:
                        # Update existing metric
                        existing.analyses_count = metrics["analyses_count"]
                        existing.specs_added = metrics["specs_added"]
                        existing.conflicts_resolved = metrics["conflicts_resolved"]
                        existing.sessions_created = metrics.get("sessions_created", 0)
                    else:
                        # Create new metric
                        metric = ProjectMetrics(
                            project_id=project_id,
                            user_id=metrics["user_id"],
                            date=yesterday,
                            **{k: v for k, v in metrics.items() if k != "user_id"}
                        )
                        db.add(metric)

                    saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving metric for project {project_id}: {e}")
                    continue

            db.commit()
            logger.info(f"Successfully aggregated {saved_count} projects, {len(events)} total events")

            return {
                "status": "success",
                "aggregated_projects": saved_count,
                "total_events": len(events),
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Analytics aggregation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


async def process_analytics_queue() -> dict:
    """
    Process pending analytics events.

    This job runs every 5 minutes and:
    1. Fetches events from analytics event queue
    2. Validates and deduplicates
    3. Saves to database
    4. Marks as processed

    Returns:
        Dictionary with processing results
    """
    try:
        # Import here to avoid circular imports
        from ..core.database import SessionLocalSpecs
        from ..models.analytics_event import AnalyticsEvent

        db = SessionLocalSpecs()

        try:
            logger.debug("Processing analytics queue...")

            # For now, this is a placeholder
            # In the future, this will process events from a queue system
            # (Redis, Kafka, or database queue table)

            # Example: fetch recent unprocessed events
            recent_events = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.timestamp > datetime.now(timezone.utc) - timedelta(minutes=10)
            ).count()

            logger.debug(f"Found {recent_events} recent events in queue")

            return {
                "status": "success",
                "processed_count": 0,
                "pending_events": recent_events,
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Analytics queue processing failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }

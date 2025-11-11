"""Notification management API endpoints.

Handles user notification preferences, notification delivery, and activity feed.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging

from ..core.security import get_current_active_user
from ..core.database import get_db_auth, get_db_specs
from ..models.user import User
from ..models.notification_preferences import NotificationPreferences
from ..models.activity_log import ActivityLog
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ===== Notification Preferences Endpoints =====

@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth)
) -> Dict:
    """Get user's notification preferences.

    Args:
        current_user: Authenticated user
        db_auth: Auth database session

    Returns:
        User's notification preferences

    Example:
        GET /api/v1/notifications/preferences

        Response:
        {
            "id": "prefs_123...",
            "user_id": "user_456...",
            "email_on_conflict": true,
            "email_on_maturity": true,
            "email_on_mention": true,
            "email_on_activity": false,
            "digest_frequency": "daily",
            "created_at": "2025-11-11T10:30:00Z",
            "updated_at": "2025-11-11T10:30:00Z"
        }
    """
    try:
        prefs = db_auth.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == str(current_user.id)
        ).first()

        if not prefs:
            # Return default preferences if none exist
            return {
                "user_id": str(current_user.id),
                "email_on_conflict": True,
                "email_on_maturity": True,
                "email_on_mention": True,
                "email_on_activity": False,
                "digest_frequency": "daily",
                "message": "Using default preferences"
            }

        return prefs.to_dict()

    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")


@router.post("/preferences")
async def update_notification_preferences(
    email_on_conflict: Optional[bool] = None,
    email_on_maturity: Optional[bool] = None,
    email_on_mention: Optional[bool] = None,
    email_on_activity: Optional[bool] = None,
    digest_frequency: Optional[str] = Query(None, regex="^(real_time|daily|weekly|off)$"),
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth)
) -> Dict:
    """Update user's notification preferences.

    Only provided fields are updated; others remain unchanged.

    Args:
        email_on_conflict: Send email on specification conflicts
        email_on_maturity: Send email on project maturity milestones
        email_on_mention: Send email when mentioned in comments
        email_on_activity: Send email on team activity
        digest_frequency: How often to send digest (real_time, daily, weekly, off)
        current_user: Authenticated user
        db_auth: Auth database session

    Returns:
        Updated notification preferences

    Example:
        POST /api/v1/notifications/preferences
        ?email_on_conflict=true&digest_frequency=weekly

        Response:
        {
            "id": "prefs_123...",
            "user_id": "user_456...",
            "email_on_conflict": true,
            "email_on_maturity": true,
            "email_on_mention": true,
            "email_on_activity": false,
            "digest_frequency": "weekly",
            "created_at": "2025-11-11T10:30:00Z",
            "updated_at": "2025-11-11T15:45:00Z"
        }
    """
    try:
        prefs = db_auth.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == str(current_user.id)
        ).first()

        # Create new preferences if they don't exist
        if not prefs:
            prefs = NotificationPreferences(
                user_id=str(current_user.id)
            )
            db_auth.add(prefs)

        # Update only provided fields
        if email_on_conflict is not None:
            prefs.email_on_conflict = email_on_conflict
        if email_on_maturity is not None:
            prefs.email_on_maturity = email_on_maturity
        if email_on_mention is not None:
            prefs.email_on_mention = email_on_mention
        if email_on_activity is not None:
            prefs.email_on_activity = email_on_activity
        if digest_frequency is not None:
            prefs.digest_frequency = digest_frequency

        db_auth.commit()

        logger.info(f"Updated notification preferences for user {current_user.id}")

        return prefs.to_dict()

    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        db_auth.rollback()
        raise HTTPException(status_code=500, detail="Failed to update preferences")


# ===== Activity Feed Endpoints =====

@router.get("/projects/{project_id}/activity")
async def get_project_activity(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Get activity feed for a project.

    Shows recent user actions on the project with optional filtering.

    Args:
        project_id: Project ID
        limit: Number of activities to return (max 500)
        offset: Number of activities to skip (for pagination)
        action_type: Optional filter by action type
        entity_type: Optional filter by entity type
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        List of activities with total count and pagination info

    Example:
        GET /api/v1/notifications/projects/proj_123/activity?limit=10&action_type=spec_created

        Response:
        {
            "activities": [
                {
                    "id": "activity_123...",
                    "project_id": "proj_123...",
                    "user_id": "user_456...",
                    "action_type": "spec_created",
                    "entity_type": "specification",
                    "entity_id": "spec_789...",
                    "description": "Created specification: API Rate Limit",
                    "metadata": {"category": "performance", "key": "api_rate_limit"},
                    "created_at": "2025-11-11T10:30:00Z"
                },
                ...
            ],
            "total": 150,
            "limit": 10,
            "offset": 0,
            "has_more": true
        }
    """
    try:
        # Verify project access (would typically check project membership)
        # For now, we assume user can view any project's activity

        query = db_specs.query(ActivityLog).filter(
            ActivityLog.project_id == project_id
        )

        # Apply optional filters
        if action_type:
            query = query.filter(ActivityLog.action_type == action_type)
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        activities = query.order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).offset(offset).all()

        return {
            "activities": [activity.to_dict() for activity in activities],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

    except Exception as e:
        logger.error(f"Failed to get project activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get activity feed")


@router.get("/projects/{project_id}/activity/{activity_id}")
async def get_activity_detail(
    project_id: str,
    activity_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Get details of a specific activity.

    Args:
        project_id: Project ID
        activity_id: Activity ID
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Detailed activity information

    Raises:
        HTTPException: If activity not found

    Example:
        GET /api/v1/notifications/projects/proj_123/activity/activity_456

        Response:
        {
            "id": "activity_456...",
            "project_id": "proj_123...",
            "user_id": "user_789...",
            "action_type": "spec_updated",
            "entity_type": "specification",
            "entity_id": "spec_111...",
            "description": "Updated specification: API Rate Limit",
            "metadata": {
                "before": {"value": "1000 requests/minute"},
                "after": {"value": "5000 requests/minute"}
            },
            "created_at": "2025-11-11T10:30:00Z",
            "updated_at": "2025-11-11T10:30:00Z"
        }
    """
    try:
        activity = db_specs.query(ActivityLog).filter(
            ActivityLog.id == activity_id,
            ActivityLog.project_id == project_id
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        return activity.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get activity detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get activity details")


# ===== Notification Test Endpoints =====

@router.post("/test/send-email")
async def test_send_email(
    email: str,
    notification_type: str = Query(
        "conflict_alert",
        regex="^(conflict_alert|trial_expiring|maturity_milestone|mention|digest)$"
    ),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Send a test notification email.

    For testing email service integration. Requires authentication.

    Args:
        email: Recipient email address
        notification_type: Type of test notification
        current_user: Authenticated user

    Returns:
        Success status

    Example:
        POST /api/v1/notifications/test/send-email?email=user@example.com&notification_type=conflict_alert

        Response:
        {
            "success": true,
            "message": "Test email sent to user@example.com",
            "notification_type": "conflict_alert"
        }
    """
    try:
        email_service = EmailService()

        success = False
        message = ""

        if notification_type == "conflict_alert":
            success = email_service.send_conflict_alert(
                to_email=email,
                spec1_title="API Rate Limit",
                spec2_title="API Request Throttling",
                conflict_description="These specifications conflict on API limiting"
            )
            message = "Conflict alert email sent"

        elif notification_type == "trial_expiring":
            success = email_service.send_trial_expiring(
                to_email=email,
                days_left=7
            )
            message = "Trial expiring email sent"

        elif notification_type == "maturity_milestone":
            success = email_service.send_maturity_milestone(
                to_email=email,
                project_name="Example Project",
                percentage=75
            )
            message = "Maturity milestone email sent"

        elif notification_type == "mention":
            success = email_service.send_mention_notification(
                to_email=email,
                mentioned_by="John Doe",
                project_name="Example Project",
                comment_preview="This is a great idea!"
            )
            message = "Mention notification email sent"

        elif notification_type == "digest":
            success = email_service.send_digest(
                to_email=email,
                frequency="daily",
                activities=[
                    {
                        "action": "spec_created",
                        "description": "Created specification: API Rate Limit",
                        "timestamp": "2025-11-11T10:30:00Z"
                    }
                ]
            )
            message = "Digest email sent"

        if not success:
            logger.warning(f"Test email send returned false for {notification_type}")
            return {
                "success": False,
                "message": f"Failed to send {notification_type} email",
                "notification_type": notification_type
            }

        logger.info(f"Sent test {notification_type} email to {email}")

        return {
            "success": True,
            "message": message,
            "notification_type": notification_type,
            "recipient": email
        }

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

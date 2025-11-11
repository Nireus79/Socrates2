"""Activity log service for tracking user actions on projects.

Provides easy interface for logging user activities across the application.
All activities are recorded for audit trails and activity feeds.
"""
import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ActivityLogService:
    """Service for logging and retrieving activity logs.

    Provides a simple interface for recording user actions throughout
    the application. Activities include specification changes, comments,
    document uploads, team member actions, and more.
    """

    # Activity types
    ACTIVITY_TYPES = {
        # Specification activities
        "spec_created": "Created specification",
        "spec_updated": "Updated specification",
        "spec_deleted": "Deleted specification",
        "spec_superseded": "Superseded specification",

        # Comment activities
        "comment_added": "Added comment",
        "comment_updated": "Updated comment",
        "comment_deleted": "Deleted comment",

        # Document activities
        "document_uploaded": "Uploaded document",
        "document_deleted": "Deleted document",

        # Team/Collaboration activities
        "member_invited": "Invited team member",
        "member_added": "Added team member",
        "member_removed": "Removed team member",
        "member_role_changed": "Changed member role",

        # Project activities
        "project_created": "Created project",
        "project_updated": "Updated project",
        "project_renamed": "Renamed project",
        "project_archived": "Archived project",

        # Maturity/Metrics activities
        "maturity_updated": "Updated maturity score",
        "quality_metric_added": "Added quality metric",

        # Conflict/Issue activities
        "conflict_detected": "Detected specification conflict",
        "conflict_resolved": "Resolved specification conflict",
    }

    @staticmethod
    def log_activity(
        db: Session,
        project_id: str,
        user_id: str,
        action_type: str,
        entity_type: str,
        description: str,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a user activity.

        Records an activity log entry for auditing and feed purposes.

        Args:
            db: Database session (socrates_specs)
            project_id: Project ID where activity occurred
            user_id: User ID who performed the action
            action_type: Type of action (spec_created, comment_added, etc.)
            entity_type: Type of entity affected (specification, comment, etc.)
            description: Human-readable description of the action
            entity_id: Optional ID of the affected entity
            metadata: Optional JSON metadata (before/after, reason, etc.)

        Returns:
            True if logged successfully, False otherwise

        Example:
            ActivityLogService.log_activity(
                db=db_specs,
                project_id="proj_123",
                user_id="user_456",
                action_type="spec_created",
                entity_type="specification",
                description="Created specification: API Rate Limit",
                entity_id="spec_789",
                metadata={
                    "category": "performance",
                    "key": "api_rate_limit",
                    "value": "1000 requests/minute"
                }
            )
        """
        try:
            from ..models.activity_log import ActivityLog

            # Create activity log entry
            activity = ActivityLog(
                id=str(uuid.uuid4()),
                project_id=project_id,
                user_id=user_id,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                metadata=metadata
            )

            db.add(activity)
            db.commit()

            logger.debug(
                f"Logged activity: {action_type} on {entity_type} "
                f"in project {project_id} by user {user_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            db.rollback()
            return False

    @staticmethod
    def log_spec_created(
        db: Session,
        project_id: str,
        user_id: str,
        spec_id: str,
        category: str,
        key: str,
        value: str
    ) -> bool:
        """Log specification creation.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            spec_id: Specification ID
            category: Specification category
            key: Specification key
            value: Specification value

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="spec_created",
            entity_type="specification",
            entity_id=spec_id,
            description=f"Created specification: {key}",
            metadata={
                "category": category,
                "key": key,
                "value": value
            }
        )

    @staticmethod
    def log_spec_updated(
        db: Session,
        project_id: str,
        user_id: str,
        spec_id: str,
        key: str,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> bool:
        """Log specification update.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            spec_id: Specification ID
            key: Specification key
            before: Previous values
            after: New values

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="spec_updated",
            entity_type="specification",
            entity_id=spec_id,
            description=f"Updated specification: {key}",
            metadata={
                "before": before,
                "after": after
            }
        )

    @staticmethod
    def log_spec_deleted(
        db: Session,
        project_id: str,
        user_id: str,
        spec_id: str,
        key: str
    ) -> bool:
        """Log specification deletion.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            spec_id: Specification ID
            key: Specification key

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="spec_deleted",
            entity_type="specification",
            entity_id=spec_id,
            description=f"Deleted specification: {key}"
        )

    @staticmethod
    def log_comment_added(
        db: Session,
        project_id: str,
        user_id: str,
        comment_id: str,
        entity_type: str,
        entity_id: str,
        comment_preview: str
    ) -> bool:
        """Log comment addition.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            comment_id: Comment ID
            entity_type: Type of entity commented on (specification, etc.)
            entity_id: ID of entity
            comment_preview: First 100 chars of comment

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="comment_added",
            entity_type="comment",
            entity_id=comment_id,
            description=f"Added comment on {entity_type}",
            metadata={
                "on_entity_type": entity_type,
                "on_entity_id": entity_id,
                "preview": comment_preview[:100]
            }
        )

    @staticmethod
    def log_document_uploaded(
        db: Session,
        project_id: str,
        user_id: str,
        document_id: str,
        filename: str,
        file_size: int
    ) -> bool:
        """Log document upload.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            document_id: Document ID
            filename: Original filename
            file_size: File size in bytes

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="document_uploaded",
            entity_type="document",
            entity_id=document_id,
            description=f"Uploaded document: {filename}",
            metadata={
                "filename": filename,
                "file_size": file_size
            }
        )

    @staticmethod
    def log_member_added(
        db: Session,
        project_id: str,
        user_id: str,
        member_id: str,
        member_email: str,
        role: str
    ) -> bool:
        """Log team member addition.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID who added the member
            member_id: Added member ID
            member_email: Added member email
            role: Role assigned

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="member_added",
            entity_type="project_member",
            entity_id=member_id,
            description=f"Added team member: {member_email}",
            metadata={
                "member_email": member_email,
                "role": role
            }
        )

    @staticmethod
    def log_conflict_detected(
        db: Session,
        project_id: str,
        user_id: str,
        conflict_id: str,
        spec1_key: str,
        spec2_key: str,
        description: str
    ) -> bool:
        """Log conflict detection.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID (system user if automatic)
            conflict_id: Conflict ID
            spec1_key: First specification key
            spec2_key: Second specification key
            description: Conflict description

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="conflict_detected",
            entity_type="conflict",
            entity_id=conflict_id,
            description=f"Detected conflict: {spec1_key} ↔ {spec2_key}",
            metadata={
                "spec1_key": spec1_key,
                "spec2_key": spec2_key,
                "conflict_description": description
            }
        )

    @staticmethod
    def log_maturity_updated(
        db: Session,
        project_id: str,
        user_id: str,
        before_percentage: float,
        after_percentage: float
    ) -> bool:
        """Log maturity score update.

        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            before_percentage: Previous maturity percentage
            after_percentage: New maturity percentage

        Returns:
            True if logged successfully
        """
        return ActivityLogService.log_activity(
            db=db,
            project_id=project_id,
            user_id=user_id,
            action_type="maturity_updated",
            entity_type="project",
            entity_id=project_id,
            description=f"Updated maturity: {before_percentage:.1f}% → {after_percentage:.1f}%",
            metadata={
                "before_percentage": before_percentage,
                "after_percentage": after_percentage,
                "change": after_percentage - before_percentage
            }
        )

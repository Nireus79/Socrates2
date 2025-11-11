"""Collaboration API endpoints for project sharing and team management.

Handles project invitations, access control, and team collaboration features.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.project import Project
from ..models.project_collaborator import ProjectCollaborator
from ..models.project_invitation import InvitationStatus, ProjectInvitation
from ..models.user import User
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/collaboration", tags=["collaboration"])


# ===== Project Invitation Endpoints =====

@router.post("/projects/{project_id}/invite")
async def invite_to_project(
    project_id: str,
    email: str = Query(..., description="Email address to invite"),
    role: str = Query("editor", regex="^(viewer|editor|owner)$", description="Role to assign"),
    message: Optional[str] = Query(None, description="Optional personal message"),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Invite someone to collaborate on a project.

    Sends an invitation email (if email service available) and stores the
    invitation for tracking.

    Args:
        project_id: Project to invite to
        email: Email address of person to invite
        role: Role to assign (viewer, editor, owner)
        message: Optional personal message
        current_user: Authenticated user (must be project owner/editor)
        db_specs: Specs database session

    Returns:
        Invitation details including status

    Raises:
        HTTPException: If project not found, user lacks permission, or invite fails

    Example:
        POST /api/v1/collaboration/projects/proj_123/invite
        ?email=collaborator@example.com&role=editor&message=Welcome to the team!

        Response:
        {
            "success": true,
            "invitation_id": "inv_...",
            "invited_email": "collaborator@example.com",
            "role": "editor",
            "status": "pending",
            "message": "Welcome to the team!",
            "expires_at": "2025-12-11T..."
        }
    """
    try:
        # Verify project exists and user has permission
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id  # Simplified: only owner can invite
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        # Validate email format
        if "@" not in email or "." not in email:
            raise HTTPException(status_code=400, detail="Invalid email address")

        # Check if invitation already exists
        existing = db_specs.query(ProjectInvitation).filter(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.invited_email == email,
            ProjectInvitation.status == InvitationStatus.PENDING
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Pending invitation already exists for this email")

        # Create invitation
        invitation = ProjectInvitation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            invited_by=current_user.id,
            invited_email=email,
            role=role,
            message=message,
            status=InvitationStatus.PENDING,
            expires_at=(datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        )

        db_specs.add(invitation)
        db_specs.commit()

        # Send invitation email
        try:
            email_service = EmailService()
            email_service.send_email(
                to_email=email,
                subject=f"Invited to collaborate on {project.name}",
                body=f"""
You have been invited to collaborate on the project "{project.name}".

Role: {role}

{f'Message from inviter: {message}' if message else ''}

Accept this invitation by logging into Socrates2 and visiting your invitations.

Invitation expires on {invitation.expires_at}
                """.strip()
            )
        except Exception as e:
            logger.warning(f"Failed to send invitation email: {e}")
            # Continue anyway, invitation is still created

        logger.info(f"Sent project invitation to {email} for project {project_id}")

        return invitation.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create invitation: {e}")
        db_specs.rollback()
        raise HTTPException(status_code=500, detail="Failed to create invitation")


@router.get("/invitations")
async def get_my_invitations(
    status: Optional[str] = Query(None, regex="^(pending|accepted|declined|expired|revoked)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Get invitations for current user.

    Lists project invitations that have been sent to the user's email address.

    Args:
        status: Optional filter by invitation status
        limit: Number of results to return
        offset: Number of results to skip
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        List of invitations with pagination info

    Example:
        GET /api/v1/collaboration/invitations?status=pending

        Response:
        {
            "invitations": [
                {
                    "id": "inv_...",
                    "project_id": "proj_123",
                    "invited_email": "user@example.com",
                    "role": "editor",
                    "status": "pending",
                    "message": "...",
                    "expires_at": "2025-12-11T...",
                    "created_at": "2025-11-11T..."
                }
            ],
            "total": 5,
            "limit": 50,
            "offset": 0,
            "has_more": false
        }
    """
    try:
        query = db_specs.query(ProjectInvitation).filter(
            ProjectInvitation.invited_email == current_user.email
        )

        if status:
            query = query.filter(ProjectInvitation.status == InvitationStatus(status))

        total = query.count()

        invitations = query.order_by(
            ProjectInvitation.created_at.desc()
        ).limit(limit).offset(offset).all()

        return {
            "invitations": [inv.to_dict() for inv in invitations],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

    except Exception as e:
        logger.error(f"Failed to get invitations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get invitations")


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Accept a project invitation.

    Adds the user as a collaborator to the project.

    Args:
        invitation_id: Invitation ID to accept
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Updated invitation with accepted status

    Raises:
        HTTPException: If invitation not found, expired, or user doesn't match

    Example:
        POST /api/v1/collaboration/invitations/inv_123/accept

        Response:
        {
            "success": true,
            "message": "Invitation accepted",
            "project_id": "proj_123"
        }
    """
    try:
        invitation = db_specs.query(ProjectInvitation).filter(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.invited_email == current_user.email
        ).first()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Invitation is {invitation.status.value}, cannot accept"
            )

        # Check if expired
        if invitation.expires_at:
            expires = datetime.fromisoformat(invitation.expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires:
                invitation.status = InvitationStatus.EXPIRED
                db_specs.commit()
                raise HTTPException(status_code=400, detail="Invitation has expired")

        # Add as collaborator
        collaborator = ProjectCollaborator(
            id=str(uuid.uuid4()),
            project_id=invitation.project_id,
            user_id=current_user.id,
            role=invitation.role,
            added_by=invitation.invited_by
        )

        db_specs.add(collaborator)

        # Update invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc).isoformat()
        invitation.invited_user_id = current_user.id

        db_specs.commit()

        logger.info(f"User {current_user.id} accepted invitation {invitation_id}")

        return {
            "success": True,
            "message": "Invitation accepted",
            "project_id": str(invitation.project_id),
            "role": invitation.role
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        db_specs.rollback()
        raise HTTPException(status_code=500, detail="Failed to accept invitation")


@router.post("/invitations/{invitation_id}/decline")
async def decline_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Decline a project invitation.

    Marks the invitation as declined.

    Args:
        invitation_id: Invitation ID to decline
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Updated invitation with declined status

    Example:
        POST /api/v1/collaboration/invitations/inv_123/decline

        Response:
        {
            "success": true,
            "message": "Invitation declined"
        }
    """
    try:
        invitation = db_specs.query(ProjectInvitation).filter(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.invited_email == current_user.email
        ).first()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Invitation is {invitation.status.value}, cannot decline"
            )

        invitation.status = InvitationStatus.DECLINED
        db_specs.commit()

        logger.info(f"User {current_user.id} declined invitation {invitation_id}")

        return {
            "success": True,
            "message": "Invitation declined"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to decline invitation: {e}")
        db_specs.rollback()
        raise HTTPException(status_code=500, detail="Failed to decline invitation")


# ===== Project Collaborator Management =====

@router.get("/projects/{project_id}/collaborators")
async def get_project_collaborators(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Get list of project collaborators.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        List of collaborators with their roles

    Example:
        GET /api/v1/collaboration/projects/proj_123/collaborators

        Response:
        {
            "project_id": "proj_123",
            "collaborators": [
                {
                    "id": "collab_...",
                    "user_id": "user_123",
                    "email": "user@example.com",
                    "role": "editor",
                    "added_by": "...",
                    "added_at": "2025-11-11T..."
                }
            ],
            "total": 3
        }
    """
    try:
        # Verify project access
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        collaborators = db_specs.query(ProjectCollaborator).filter(
            ProjectCollaborator.project_id == project_id
        ).all()

        return {
            "project_id": project_id,
            "collaborators": [
                {
                    "id": str(c.id),
                    "user_id": str(c.user_id),
                    "role": c.role,
                    "added_by": str(c.added_by),
                    "added_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in collaborators
            ],
            "total": len(collaborators)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collaborators: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collaborators")


@router.delete("/projects/{project_id}/collaborators/{user_id}")
async def remove_collaborator(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Remove a collaborator from a project.

    Args:
        project_id: Project ID
        user_id: User ID to remove
        current_user: Authenticated user (must be project owner)
        db_specs: Specs database session

    Returns:
        Success status

    Raises:
        HTTPException: If project not found, permission denied, or removal fails

    Example:
        DELETE /api/v1/collaboration/projects/proj_123/collaborators/user_456

        Response:
        {
            "success": true,
            "message": "Collaborator removed"
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        # Find and delete collaborator
        collaborator = db_specs.query(ProjectCollaborator).filter(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == user_id
        ).first()

        if not collaborator:
            raise HTTPException(status_code=404, detail="Collaborator not found")

        db_specs.delete(collaborator)
        db_specs.commit()

        logger.info(f"Removed user {user_id} from project {project_id}")

        return {
            "success": True,
            "message": "Collaborator removed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove collaborator: {e}")
        db_specs.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove collaborator")

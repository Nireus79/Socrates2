"""Teams API endpoints using repository pattern."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..repositories import RepositoryService

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    return RepositoryService(auth_session, specs_session)


class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=2000)


class UpdateTeamRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class TeamResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    description: Optional[str]
    status: str
    member_count: int
    project_count: int
    created_at: str

    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    teams: list[TeamResponse]
    total: int
    skip: int
    limit: int


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> TeamResponse:
    """Create a new team."""
    try:
        team = service.teams.create_team(
            owner_id=current_user.id,
            name=request.name,
            description=request.description or ""
        )
        service.commit_all()
        return TeamResponse(
            id=str(team.id),
            owner_id=str(team.owner_id),
            name=team.name,
            description=team.description,
            status=team.status,
            member_count=team.member_count or 1,
            project_count=team.project_count or 0,
            created_at=team.created_at.isoformat()
        )
    except Exception as e:
        service.rollback_all()
        raise HTTPException(status_code=500, detail="Failed to create team") from e


@router.get("", response_model=TeamListResponse)
def list_user_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> TeamListResponse:
    """List teams owned by current user."""
    try:
        teams = service.teams.get_user_teams(user_id=current_user.id, skip=skip, limit=limit)
        total = service.teams.count_by_field("owner_id", current_user.id)
        return TeamListResponse(
            teams=[
                TeamResponse(
                    id=str(t.id),
                    owner_id=str(t.owner_id),
                    name=t.name,
                    description=t.description,
                    status=t.status,
                    member_count=t.member_count or 1,
                    project_count=t.project_count or 0,
                    created_at=t.created_at.isoformat()
                )
                for t in teams
            ],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list teams") from e


@router.get("/{team_id}")
def get_team(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
):
    """Get team details."""
    try:
        team_uuid = UUID(team_id)
        team = service.teams.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        if str(team.owner_id) != str(current_user.id) and \
           not service.team_members.is_team_member(team_uuid, current_user.id):
            raise HTTPException(status_code=403, detail="Permission denied")
        return {
            "id": str(team.id),
            "owner_id": str(team.owner_id),
            "name": team.name,
            "description": team.description,
            "status": team.status,
            "member_count": team.member_count or 1,
            "project_count": team.project_count or 0,
            "created_at": team.created_at.isoformat()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team ID format")


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: str,
    request: UpdateTeamRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> TeamResponse:
    """Update team details."""
    try:
        team_uuid = UUID(team_id)
        team = service.teams.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        if str(team.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Permission denied")
        if request.name:
            team = service.teams.update_team_name(team_uuid, request.name)
        if request.description is not None:
            team = service.teams.update_team_description(team_uuid, request.description)
        service.commit_all()
        return TeamResponse(
            id=str(team.id),
            owner_id=str(team.owner_id),
            name=team.name,
            description=team.description,
            status=team.status,
            member_count=team.member_count or 1,
            project_count=team.project_count or 0,
            created_at=team.created_at.isoformat()
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team ID format")
    except HTTPException:
        service.rollback_all()
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(status_code=500, detail="Failed to update team") from e


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> None:
    """Delete/archive a team."""
    try:
        team_uuid = UUID(team_id)
        team = service.teams.get_by_id(team_uuid)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        if str(team.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Permission denied")
        service.teams.archive_team(team_uuid)
        service.commit_all()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team ID format")
    except HTTPException:
        service.rollback_all()
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(status_code=500, detail="Failed to delete team") from e

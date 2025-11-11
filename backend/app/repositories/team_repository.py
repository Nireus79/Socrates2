"""
Team Repository for SPECS database operations.

Handles CRUD operations for teams and team members.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Team, TeamMember
from .base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """Repository for Team operations (socrates_specs database)."""

    def __init__(self, session: Session):
        super().__init__(Team, session)

    def get_user_teams(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Team]:
        """Get teams owned by a user."""
        return self.list_by_field('owner_id', user_id, skip=skip, limit=limit)

    def get_active_teams(self, skip: int = 0, limit: int = 100) -> list[Team]:
        """Get all active teams."""
        return self.list_by_field('status', 'active', skip=skip, limit=limit)

    def get_team_by_name(self, name: str) -> Optional[Team]:
        """Get team by name."""
        return self.get_by_field('name', name)

    def create_team(
        self,
        owner_id: UUID,
        name: str,
        description: str = '',
        **kwargs
    ) -> Team:
        """
        Create new team.

        Args:
            owner_id: Team owner user ID
            name: Team name (must be unique)
            description: Team description
            **kwargs: Additional fields

        Returns:
            Created Team instance
        """
        return self.create(
            owner_id=owner_id,
            name=name,
            description=description,
            status='active',
            member_count=1,  # Owner is first member
            project_count=0,
            **kwargs
        )

    def update_team_name(self, team_id: UUID, name: str) -> Optional[Team]:
        """Update team name."""
        return self.update(team_id, name=name)

    def update_team_description(self, team_id: UUID, description: str) -> Optional[Team]:
        """Update team description."""
        return self.update(team_id, description=description)

    def increment_member_count(self, team_id: UUID) -> Optional[Team]:
        """Increment team member count."""
        team = self.get_by_id(team_id)
        if not team:
            return None

        new_count = (team.member_count or 0) + 1
        return self.update(team_id, member_count=new_count)

    def decrement_member_count(self, team_id: UUID) -> Optional[Team]:
        """Decrement team member count."""
        team = self.get_by_id(team_id)
        if not team:
            return None

        new_count = max(0, (team.member_count or 0) - 1)
        return self.update(team_id, member_count=new_count)

    def increment_project_count(self, team_id: UUID) -> Optional[Team]:
        """Increment team project count."""
        team = self.get_by_id(team_id)
        if not team:
            return None

        new_count = (team.project_count or 0) + 1
        return self.update(team_id, project_count=new_count)

    def archive_team(self, team_id: UUID) -> Optional[Team]:
        """Archive a team."""
        return self.update(team_id, status='archived')

    def get_recent_teams(self, limit: int = 10) -> list[Team]:
        """Get most recent teams."""
        return self.list_ordered(
            order_by='created_at',
            ascending=False,
            limit=limit
        )

    def count_active_teams(self) -> int:
        """Count active teams."""
        return self.count_by_field('status', 'active')


class TeamMemberRepository(BaseRepository[TeamMember]):
    """Repository for TeamMember operations."""

    def __init__(self, session: Session):
        super().__init__(TeamMember, session)

    def get_team_members(
        self,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[TeamMember]:
        """Get all members of a team."""
        return self.list_by_field('team_id', team_id, skip=skip, limit=limit)

    def get_user_teams_as_member(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[TeamMember]:
        """Get all teams user is a member of."""
        return self.list_by_field('user_id', user_id, skip=skip, limit=limit)

    def get_active_members(
        self,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[TeamMember]:
        """Get active members of a team."""
        members = self.get_team_members(team_id, skip=skip, limit=limit*2)
        return [m for m in members if m.status == 'active']

    def add_member(
        self,
        team_id: UUID,
        user_id: UUID,
        role: str = 'member',
        permission_level: str = 'write',
        invited_by_id: UUID = None,
        **kwargs
    ) -> TeamMember:
        """
        Add member to team.

        Args:
            team_id: Team ID
            user_id: User ID to add
            role: Member role (owner, admin, lead, member, viewer)
            permission_level: Permission level (read, write, admin)
            invited_by_id: User who invited this member
            **kwargs: Additional fields

        Returns:
            Created TeamMember instance
        """
        return self.create(
            team_id=team_id,
            user_id=user_id,
            role=role,
            permission_level=permission_level,
            invited_by_id=invited_by_id,
            status='active',
            **kwargs
        )

    def update_member_role(
        self,
        member_id: UUID,
        role: str
    ) -> Optional[TeamMember]:
        """Update member role."""
        return self.update(member_id, role=role)

    def update_member_permission(
        self,
        member_id: UUID,
        permission_level: str
    ) -> Optional[TeamMember]:
        """Update member permission level."""
        return self.update(member_id, permission_level=permission_level)

    def remove_member(self, member_id: UUID) -> Optional[TeamMember]:
        """Remove member from team."""
        return self.update(member_id, status='inactive')

    def is_team_member(self, team_id: UUID, user_id: UUID) -> bool:
        """Check if user is member of team."""
        member = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.status == 'active'
        ).first()
        return member is not None

    def get_member_role(self, team_id: UUID, user_id: UUID) -> Optional[str]:
        """Get user's role in team."""
        member = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.status == 'active'
        ).first()
        return member.role if member else None

    def count_team_members(self, team_id: UUID) -> int:
        """Count active members in team."""
        members = self.get_active_members(team_id, limit=10000)
        return len(members)

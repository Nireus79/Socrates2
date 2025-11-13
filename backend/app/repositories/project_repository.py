"""
Project Repository for SPECS database operations.

Handles CRUD operations for projects and related data.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Project
from .base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations (socrates_specs database)."""

    def __init__(self, session: Session):
        super().__init__(Project, session)

    def get_user_projects(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """Get all projects for a user."""
        return self.list_by_field('user_id', user_id, skip=skip, limit=limit)

    def get_active_projects(self, skip: int = 0, limit: int = 100) -> list[Project]:
        """Get all active projects."""
        return self.list_by_field('status', 'active', skip=skip, limit=limit)

    def get_projects_by_phase(
        self,
        phase: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """Get projects in specific phase."""
        return self.list_by_field('phase', phase, skip=skip, limit=limit)

    def get_user_active_projects(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """Get active projects for a user."""
        active_projects = self.get_user_projects(user_id, skip=skip, limit=limit)
        return [p for p in active_projects if p.status == 'active']

    def create_project(
        self,
        user_id: UUID,
        name: str,
        description: str = '',
        **kwargs
    ) -> Project:
        """
        Create new project.

        Args:
            user_id: Creator/owner user ID
            name: Project name
            description: Project description
            **kwargs: Additional fields

        Returns:
            Created Project instance
        """
        # Ensure user_id is a UUID
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        return self.create(
            user_id=user_id,
            creator_id=user_id,  # Creator is the same as initial owner
            owner_id=user_id,    # Initial owner is the creator
            name=name,
            description=description,
            current_phase='discovery',  # Use correct field name
            status='active',
            maturity_score=0,  # Use correct field name
            **kwargs
        )

    def update_project_phase(self, project_id: UUID, phase: str) -> Optional[Project]:
        """Update project to new phase."""
        return self.update(project_id, current_phase=phase)

    def update_project_status(self, project_id: UUID, status: str) -> Optional[Project]:
        """Update project status."""
        return self.update(project_id, status=status)

    def update_maturity_level(
        self,
        project_id: UUID,
        level: int
    ) -> Optional[Project]:
        """Update project maturity score."""
        if level < 0 or level > 100:
            raise ValueError('Maturity level must be between 0 and 100')
        return self.update(project_id, maturity_score=level)

    def archive_project(self, project_id: UUID) -> Optional[Project]:
        """Archive a project (soft delete)."""
        return self.update_project_status(project_id, 'archived')

    def restore_project(self, project_id: UUID) -> Optional[Project]:
        """Restore an archived project back to active status."""
        return self.update_project_status(project_id, 'active')

    def delete_project(self, project_id: UUID) -> bool:
        """
        Hard delete an archived project from the database.

        This is irreversible and only works on archived projects.

        Args:
            project_id: Project UUID to delete

        Returns:
            True if deleted successfully, False if not found or not archived
        """
        project = self.get_by_id(project_id)
        if not project:
            return False

        # Only allow deletion of archived projects
        if project.status != 'archived':
            return False

        # Delete the project (cascade will handle related tables)
        self.session.delete(project)
        return True

    def complete_project(self, project_id: UUID) -> Optional[Project]:
        """Mark project as completed."""
        return self.update_project_status(project_id, 'completed')

    def get_recent_projects(
        self,
        limit: int = 10
    ) -> list[Project]:
        """Get most recently created projects."""
        return self.list_ordered(
            order_by='created_at',
            ascending=False,
            limit=limit
        )

    def get_user_recent_projects(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> list[Project]:
        """Get most recently created projects for a user."""
        projects = self.get_user_projects(user_id, limit=limit * 2)
        return sorted(
            projects,
            key=lambda p: p.created_at,
            reverse=True
        )[:limit]

    def count_user_projects(self, user_id: UUID) -> int:
        """Count total projects for a user."""
        return self.count_by_field('user_id', user_id)

    def count_active_projects(self) -> int:
        """Count total active projects."""
        return self.count_by_field('status', 'active')

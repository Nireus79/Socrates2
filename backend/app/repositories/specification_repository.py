"""
Specification Repository for SPECS database operations.

Handles CRUD operations for specifications.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Specification
from .base_repository import BaseRepository


class SpecificationRepository(BaseRepository[Specification]):
    """Repository for Specification operations (socrates_specs database)."""

    def __init__(self, session: Session):
        super().__init__(Specification, session)

    def get_project_specifications(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Specification]:
        """Get all specifications for a project."""
        return self.list_by_field('project_id', project_id, skip=skip, limit=limit)

    def get_specification_by_key(
        self,
        project_id: UUID,
        key: str
    ) -> Optional[Specification]:
        """Get latest specification by key."""
        specs = self.session.query(Specification).filter(
            Specification.project_id == project_id,
            Specification.key == key
        ).order_by(Specification.version.desc()).first()
        return specs

    def get_approved_specifications(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Specification]:
        """Get approved specifications."""
        all_specs = self.get_project_specifications(project_id, skip=skip, limit=limit*2)
        return [s for s in all_specs if s.status == 'approved']

    def get_draft_specifications(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Specification]:
        """Get draft specifications."""
        all_specs = self.get_project_specifications(project_id, skip=skip, limit=limit*2)
        return [s for s in all_specs if s.status == 'draft']

    def create_specification(
        self,
        project_id: UUID,
        key: str,
        value: str = '',
        spec_type: str = 'functional',
        **kwargs
    ) -> Specification:
        """
        Create new specification.

        Args:
            project_id: Project ID
            key: Specification key
            value: Specification value
            spec_type: Type (functional, non-functional, etc.)
            **kwargs: Additional fields

        Returns:
            Created Specification instance
        """
        return self.create(
            project_id=project_id,
            key=key,
            value=value,
            type=spec_type,
            status='draft',
            version=1,
            **kwargs
        )

    def update_specification_value(
        self,
        spec_id: UUID,
        value: str
    ) -> Optional[Specification]:
        """Update specification value."""
        return self.update(spec_id, value=value)

    def approve_specification(self, spec_id: UUID) -> Optional[Specification]:
        """Approve a specification."""
        return self.update(spec_id, status='approved')

    def implement_specification(self, spec_id: UUID) -> Optional[Specification]:
        """Mark specification as implemented."""
        return self.update(spec_id, status='implemented')

    def deprecate_specification(self, spec_id: UUID) -> Optional[Specification]:
        """Mark specification as deprecated."""
        return self.update(spec_id, status='deprecated')

    def create_specification_version(
        self,
        project_id: UUID,
        key: str,
        value: str,
        **kwargs
    ) -> Specification:
        """
        Create new version of specification.

        Args:
            project_id: Project ID
            key: Specification key
            value: New value
            **kwargs: Additional fields

        Returns:
            Created Specification instance with incremented version
        """
        latest = self.get_specification_by_key(project_id, key)
        new_version = (latest.version + 1) if latest else 1

        return self.create(
            project_id=project_id,
            key=key,
            value=value,
            status='draft',
            version=new_version,
            **kwargs
        )

    def get_specification_history(
        self,
        project_id: UUID,
        key: str
    ) -> list[Specification]:
        """Get all versions of a specification."""
        specs = self.session.query(Specification).filter(
            Specification.project_id == project_id,
            Specification.key == key
        ).order_by(Specification.version.desc()).all()
        return specs

    def count_project_specifications(self, project_id: UUID) -> int:
        """Count specifications in project."""
        return self.count_by_field('project_id', project_id)

    def count_approved_specifications(self, project_id: UUID) -> int:
        """Count approved specifications."""
        approved = self.get_approved_specifications(project_id, limit=10000)
        return len(approved)

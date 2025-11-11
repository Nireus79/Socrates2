"""
Repository Service Container

Provides unified access to all repositories with proper session management.
This is the main entry point for data access operations.

Usage:
    from app.core.database import get_db_auth, get_db_specs
    from app.repositories import RepositoryService

    auth_session = next(get_db_auth())
    specs_session = next(get_db_specs())

    service = RepositoryService(auth_session, specs_session)

    # Access any repository
    user = service.users.get_by_email('test@example.com')
    projects = service.projects.get_user_projects(user.id)

    # Commit changes
    service.commit_all()
"""

from sqlalchemy.orm import Session

from .user_repository import (
    UserRepository,
    RefreshTokenRepository,
    AdminRoleRepository,
    AdminUserRepository,
)
from .project_repository import ProjectRepository
from .session_repository import SessionRepository, ConversationHistoryRepository
from .question_repository import QuestionRepository
from .specification_repository import SpecificationRepository
from .team_repository import TeamRepository, TeamMemberRepository


class RepositoryService:
    """
    Container for all repository instances.

    Manages repositories for both databases and provides unified interface
    for data access operations.
    """

    def __init__(self, auth_session: Session, specs_session: Session):
        """
        Initialize repository service with database sessions.

        Args:
            auth_session: SQLAlchemy session for socrates_auth database
            specs_session: SQLAlchemy session for socrates_specs database
        """
        self.auth_session = auth_session
        self.specs_session = specs_session

        # AUTH Database Repositories
        self.users = UserRepository(auth_session)
        self.refresh_tokens = RefreshTokenRepository(auth_session)
        self.admin_roles = AdminRoleRepository(auth_session)
        self.admin_users = AdminUserRepository(auth_session)

        # SPECS Database Repositories
        self.projects = ProjectRepository(specs_session)
        self.sessions = SessionRepository(specs_session)
        self.conversation_history = ConversationHistoryRepository(specs_session)
        self.questions = QuestionRepository(specs_session)
        self.specifications = SpecificationRepository(specs_session)
        self.teams = TeamRepository(specs_session)
        self.team_members = TeamMemberRepository(specs_session)

    def commit_all(self) -> None:
        """Commit changes to both databases."""
        self.auth_session.commit()
        self.specs_session.commit()

    def rollback_all(self) -> None:
        """Rollback all pending changes."""
        self.auth_session.rollback()
        self.specs_session.rollback()

    def close(self) -> None:
        """Close both database sessions."""
        self.auth_session.close()
        self.specs_session.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        if exc_type:
            self.rollback_all()
        else:
            self.commit_all()
        self.close()


class RepositoryServiceFactory:
    """Factory for creating RepositoryService instances."""

    @staticmethod
    def create(auth_session: Session, specs_session: Session) -> RepositoryService:
        """Create a new RepositoryService instance."""
        return RepositoryService(auth_session, specs_session)

    @staticmethod
    def create_with_context_manager(
        auth_session: Session,
        specs_session: Session
    ) -> RepositoryService:
        """Create a RepositoryService for use with context manager."""
        return RepositoryService(auth_session, specs_session)

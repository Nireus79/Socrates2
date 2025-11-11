"""
Data Access Layer (Repository/DAO Pattern)

This module provides repository classes for data access across both databases:
- socrates_auth: User and admin management
- socrates_specs: Projects, specifications, collaboration

Example usage:
    from app.core.database import get_db_auth, get_db_specs
    from app.repositories import UserRepository, ProjectRepository

    auth_session = next(get_db_auth())
    specs_session = next(get_db_specs())

    user_repo = UserRepository(auth_session)
    project_repo = ProjectRepository(specs_session)

    # Create
    user = user_repo.create_user(
        email='test@example.com',
        username='test',
        hashed_password='...',
        name='Test'
    )

    # Read
    user = user_repo.get_by_email('test@example.com')

    # Update
    user_repo.verify_user(user.id)

    # Commit
    user_repo.commit()
"""

# Base
from .base_repository import BaseRepository
from .repository_service import RepositoryService

# AUTH Database Repositories
from .user_repository import (
    UserRepository,
    RefreshTokenRepository,
    AdminRoleRepository,
    AdminUserRepository,
)

# SPECS Database Repositories
from .project_repository import ProjectRepository
from .session_repository import SessionRepository, ConversationHistoryRepository
from .question_repository import QuestionRepository
from .specification_repository import SpecificationRepository
from .team_repository import TeamRepository, TeamMemberRepository

__all__ = [
    # Base
    'BaseRepository',
    'RepositoryService',

    # AUTH Database
    'UserRepository',
    'RefreshTokenRepository',
    'AdminRoleRepository',
    'AdminUserRepository',

    # SPECS Database
    'ProjectRepository',
    'SessionRepository',
    'ConversationHistoryRepository',
    'QuestionRepository',
    'SpecificationRepository',
    'TeamRepository',
    'TeamMemberRepository',
]

"""
Session Repository for SPECS database operations.

Handles CRUD operations for conversation sessions.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session as SQLSession

from app.models import Session, ConversationHistory
from .base_repository import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository for Session operations (socrates_specs database)."""

    def __init__(self, session: SQLSession):
        super().__init__(Session, session)

    def get_project_sessions(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Session]:
        """Get all sessions for a project."""
        return self.list_by_field('project_id', project_id, skip=skip, limit=limit)

    def get_user_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Session]:
        """Get all sessions for a user."""
        return self.list_by_field('user_id', user_id, skip=skip, limit=limit)

    def get_active_sessions(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Session]:
        """Get active sessions for a project."""
        all_sessions = self.get_project_sessions(project_id, skip=skip, limit=limit*2)
        return [s for s in all_sessions if s.status == 'active']

    def create_session(
        self,
        project_id: UUID,
        user_id: UUID,
        title: str = '',
        **kwargs
    ) -> Session:
        """
        Create new session.

        Args:
            project_id: Project ID
            user_id: User ID
            title: Session title
            **kwargs: Additional fields

        Returns:
            Created Session instance
        """
        return self.create(
            project_id=project_id,
            user_id=user_id,
            title=title,
            status='active',
            message_count=0,
            **kwargs
        )

    def increment_message_count(self, session_id: UUID) -> Optional[Session]:
        """Increment message count."""
        session = self.get_by_id(session_id)
        if not session:
            return None

        new_count = (session.message_count or 0) + 1
        return self.update(session_id, message_count=new_count)

    def close_session(self, session_id: UUID) -> Optional[Session]:
        """Close a session."""
        return self.update(session_id, status='completed')

    def archive_session(self, session_id: UUID) -> Optional[Session]:
        """Archive a session."""
        return self.update(session_id, status='archived')

    def get_recent_sessions(
        self,
        project_id: UUID,
        limit: int = 10
    ) -> list[Session]:
        """Get most recent sessions for a project."""
        sessions = self.get_project_sessions(project_id, limit=limit*2)
        return sorted(
            sessions,
            key=lambda s: s.created_at,
            reverse=True
        )[:limit]

    def count_project_sessions(self, project_id: UUID) -> int:
        """Count sessions in a project."""
        return self.count_by_field('project_id', project_id)


class ConversationHistoryRepository(BaseRepository[ConversationHistory]):
    """Repository for ConversationHistory operations."""

    def __init__(self, session: SQLSession):
        super().__init__(ConversationHistory, session)

    def get_session_messages(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[ConversationHistory]:
        """Get all messages in a session."""
        messages = self.list_by_field(
            'session_id',
            session_id,
            skip=skip,
            limit=limit
        )
        return sorted(messages, key=lambda m: m.created_at)

    def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        message_type: str = 'chat',
        **kwargs
    ) -> ConversationHistory:
        """
        Add message to conversation history.

        Args:
            session_id: Session ID
            role: Message role (user, assistant, system)
            content: Message content
            message_type: Type of message
            **kwargs: Additional fields

        Returns:
            Created ConversationHistory instance
        """
        return self.create(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            **kwargs
        )

    def get_user_messages(self, session_id: UUID) -> list[ConversationHistory]:
        """Get all user messages in a session."""
        messages = self.get_session_messages(session_id, limit=10000)
        return [m for m in messages if m.role == 'user']

    def get_assistant_messages(self, session_id: UUID) -> list[ConversationHistory]:
        """Get all assistant messages in a session."""
        messages = self.get_session_messages(session_id, limit=10000)
        return [m for m in messages if m.role == 'assistant']

    def count_session_messages(self, session_id: UUID) -> int:
        """Count messages in session."""
        return self.count_by_field('session_id', session_id)

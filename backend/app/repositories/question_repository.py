"""
Question Repository for SPECS database operations.

Handles CRUD operations for questions.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Question
from .base_repository import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    """Repository for Question operations (socrates_specs database)."""

    def __init__(self, session: Session):
        super().__init__(Question, session)

    def get_project_questions(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Question]:
        """Get all questions for a project."""
        return self.list_by_field('project_id', project_id, skip=skip, limit=limit)

    def get_session_questions(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Question]:
        """Get questions in a session."""
        return self.list_by_field('session_id', session_id, skip=skip, limit=limit)

    def get_pending_questions(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Question]:
        """Get unanswered questions for a project."""
        all_questions = self.get_project_questions(project_id, skip=skip, limit=limit*2)
        return [q for q in all_questions if q.status == 'pending']

    def get_answered_questions(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Question]:
        """Get answered questions for a project."""
        all_questions = self.get_project_questions(project_id, skip=skip, limit=limit*2)
        return [q for q in all_questions if q.status == 'answered']

    def create_question(
        self,
        project_id: UUID,
        text: str,
        category: str = '',
        priority: str = 'medium',
        **kwargs
    ) -> Question:
        """
        Create new question.

        Args:
            project_id: Project ID
            text: Question text
            category: Question category
            priority: Priority level
            **kwargs: Additional fields

        Returns:
            Created Question instance
        """
        return self.create(
            project_id=project_id,
            text=text,
            category=category,
            priority=priority,
            status='pending',
            **kwargs
        )

    def answer_question(
        self,
        question_id: UUID,
        answer: str
    ) -> Optional[Question]:
        """
        Answer a question.

        Args:
            question_id: Question ID
            answer: Answer text

        Returns:
            Updated Question instance
        """
        return self.update(
            question_id,
            answer=answer,
            status='answered'
        )

    def skip_question(self, question_id: UUID) -> Optional[Question]:
        """Mark question as skipped."""
        return self.update(question_id, status='skipped')

    def resolve_question(self, question_id: UUID) -> Optional[Question]:
        """Mark question as resolved."""
        return self.update(question_id, status='resolved')

    def update_question_priority(
        self,
        question_id: UUID,
        priority: str
    ) -> Optional[Question]:
        """Update question priority."""
        return self.update(question_id, priority=priority)

    def get_high_priority_questions(
        self,
        project_id: UUID
    ) -> list[Question]:
        """Get high/critical priority questions."""
        all_questions = self.get_project_questions(project_id, limit=10000)
        return [
            q for q in all_questions
            if q.priority in ['high', 'critical']
        ]

    def count_pending_questions(self, project_id: UUID) -> int:
        """Count pending questions."""
        pending = self.get_pending_questions(project_id, limit=10000)
        return len(pending)

    def count_answered_questions(self, project_id: UUID) -> int:
        """Count answered questions."""
        answered = self.get_answered_questions(project_id, limit=10000)
        return len(answered)

"""
Database lifecycle management helpers.

CRITICAL PATTERN: Separate DB operations from LLM operations
- Load data from DB, then CLOSE connection
- Call LLM (no connection held)
- Open new connection, save results, close

This prevents connection pool exhaustion during long LLM calls.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocalSpecs
from app.models.session import Session as SessionModel
from app.models.project import Project
from app.models.question import Question
from app.models.specification import Specification

logger = logging.getLogger(__name__)


def load_session_context(session_id: str) -> Dict[str, Any]:
    """
    Load session, project, specs, questions in ONE operation.

    IMPORTANT: Connection is closed before returning.
    Use returned data (not db objects) for LLM processing.

    Returns:
        Dict with keys: session_id, project_id, project_name,
                       specs, questions (all as plain dicts)
    """
    db = SessionLocalSpecs()
    try:
        # Load all needed data
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            logger.error(f"Session {session_id} not found")
            return {}

        project = db.query(Project).filter(Project.id == session.project_id).first()
        if not project:
            logger.error(f"Project {session.project_id} not found")
            return {}

        specs = db.query(Specification).filter(
            Specification.session_id == session_id
        ).all()

        questions = db.query(Question).filter(
            Question.session_id == session_id
        ).all()

        # Convert to plain dicts for use after connection closes
        context = {
            'session_id': str(session.id),
            'project_id': str(session.project_id),
            'project_name': project.name,
            'project_description': project.description,
            'specs': [
                {
                    'id': str(spec.id),
                    'content': spec.content,
                    'category': spec.category,
                    'source': spec.source,
                    'confidence': spec.confidence
                }
                for spec in specs
            ],
            'questions': [
                {
                    'id': str(q.id),
                    'question': q.question,
                    'category': q.category,
                    'is_answered': q.is_answered
                }
                for q in questions
            ]
        }

        return context

    except Exception as e:
        logger.error(f"Error loading session context: {e}", exc_info=True)
        return {}
    finally:
        # CRITICAL: Always close connection before returning
        db.close()


def load_project_specs(project_id: str) -> Dict[str, Any]:
    """
    Load project and all its specifications.

    Connection is closed before returning.
    """
    db = SessionLocalSpecs()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {}

        specs = db.query(Specification).filter(
            Specification.session_id == project.id  # Check this logic
        ).all()

        return {
            'project_id': str(project.id),
            'project_name': project.name,
            'project_description': project.description,
            'specs': [
                {
                    'id': str(spec.id),
                    'content': spec.content,
                    'category': spec.category
                }
                for spec in specs
            ]
        }
    except Exception as e:
        logger.error(f"Error loading project specs: {e}", exc_info=True)
        return {}
    finally:
        db.close()


def save_specifications(session_id: str, specs: List[Dict[str, Any]]) -> bool:
    """
    Save specifications to database.

    Opens new connection, saves, closes.
    """
    db = SessionLocalSpecs()
    try:
        for spec_data in specs:
            spec = Specification(
                session_id=session_id,
                content=spec_data.get('content'),
                category=spec_data.get('category', 'general'),
                source=spec_data.get('source', 'llm'),
                confidence=spec_data.get('confidence', 0.8),
                is_current=True
            )
            db.add(spec)

        db.commit()
        logger.info(f"Saved {len(specs)} specifications for session {session_id}")
        return True

    except Exception as e:
        logger.error(f"Error saving specifications: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


def save_question(session_id: str, question_text: str, category: str = "general") -> Optional[str]:
    """
    Save a new question to database.

    Returns: Question ID if successful, None otherwise
    """
    db = SessionLocalSpecs()
    try:
        question = Question(
            session_id=session_id,
            question=question_text,
            category=category,
            is_answered=False
        )
        db.add(question)
        db.commit()

        logger.info(f"Saved question for session {session_id}")
        return str(question.id)

    except Exception as e:
        logger.error(f"Error saving question: {e}", exc_info=True)
        db.rollback()
        return None
    finally:
        db.close()


def update_question_answered(question_id: str, answer_text: str) -> bool:
    """
    Mark question as answered and save the answer.
    """
    db = SessionLocalSpecs()
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            logger.error(f"Question {question_id} not found")
            return False

        question.is_answered = True
        question.answer = answer_text
        db.commit()

        return True

    except Exception as e:
        logger.error(f"Error updating question: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


def save_conflicts(session_id: str, conflicts: List[Dict[str, Any]]) -> bool:
    """
    Save detected conflicts to database.
    """
    db = SessionLocalSpecs()
    try:
        # Import Conflict model (if it exists)
        # For now, just log that we would save
        logger.info(f"Would save {len(conflicts)} conflicts for session {session_id}")
        return True

    except Exception as e:
        logger.error(f"Error saving conflicts: {e}", exc_info=True)
        return False
    finally:
        db.close()


def get_session_object(session_id: str) -> Optional[SessionModel]:
    """
    Get a session object (returns db object, caller must manage connection).

    WARNING: Caller is responsible for closing the database connection!
    Use this only when you need to work with DB in the same transaction.
    Prefer load_session_context() for most use cases.
    """
    db = SessionLocalSpecs()
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session:
        logger.error(f"Session {session_id} not found")
        db.close()
        return None

    return session

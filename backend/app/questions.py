"""
Questions Domain Module

Re-exports the QuestionTemplateEngine and related utilities from the domains package.
This module provides the question template system that aggregates questions from all
domains and provides filtering, search, and template management capabilities.

Usage:
    from app.questions import QuestionTemplateEngine, get_question_engine

    engine = get_question_engine()
    questions = engine.get_all_questions()
    programming_questions = engine.filter_by_domain("programming")
"""

from app.domains.questions import (
    QuestionTemplateEngine,
    get_question_engine,
)

__all__ = [
    "QuestionTemplateEngine",
    "get_question_engine",
]

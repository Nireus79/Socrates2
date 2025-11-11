"""
Question template and management system for domains.

Handles loading, validating, and serving domain-specific questions
from configuration files (YAML, JSON, etc).
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from .base import Question

logger = logging.getLogger(__name__)


class QuestionTemplateEngine:
    """
    Engine for managing domain questions.

    Loads questions from configuration files and provides filtering,
    validation, and template rendering capabilities.

    Usage:
        engine = QuestionTemplateEngine()
        questions = engine.load_questions("domains/programming/questions.json")
        perf_questions = engine.filter_by_category(questions, "Performance")
    """

    def __init__(self):
        """Initialize the question engine."""
        self.questions_cache: Dict[str, List[Question]] = {}

    def load_questions_from_dict(self, data: List[Dict[str, Any]]) -> List[Question]:
        """
        Load questions from a list of dictionaries.

        Args:
            data: List of question dictionaries

        Returns:
            List of Question objects

        Example:
            data = [
                {
                    "question_id": "q1",
                    "text": "What is your target?",
                    "category": "Performance",
                    "difficulty": "easy"
                },
                ...
            ]
            questions = engine.load_questions_from_dict(data)
        """
        questions = []

        for item in data:
            try:
                question = Question(
                    question_id=item.get("question_id"),
                    text=item.get("text"),
                    category=item.get("category"),
                    difficulty=item.get("difficulty", "medium"),
                    help_text=item.get("help_text"),
                    example_answer=item.get("example_answer"),
                    follow_up_questions=item.get("follow_up_questions", []),
                    dependencies=item.get("dependencies", []),
                )
                questions.append(question)
                logger.debug(f"Loaded question: {question.question_id}")
            except (KeyError, ValueError) as e:
                logger.error(f"Error loading question {item.get('question_id', '?')}: {e}")
                raise ValueError(f"Invalid question configuration: {e}")

        return questions

    def load_questions_from_json(self, json_file: str) -> List[Question]:
        """
        Load questions from a JSON file.

        Args:
            json_file: Path to JSON file

        Returns:
            List of Question objects
        """
        path = Path(json_file)
        if not path.exists():
            raise FileNotFoundError(f"Questions file not found: {json_file}")

        with open(path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Questions file must contain a JSON array")

        return self.load_questions_from_dict(data)

    def filter_by_category(
        self, questions: List[Question], category: str
    ) -> List[Question]:
        """
        Filter questions by category.

        Args:
            questions: List of questions
            category: Category to filter by

        Returns:
            Filtered questions
        """
        return [q for q in questions if q.category == category]

    def filter_by_difficulty(
        self, questions: List[Question], difficulty: str
    ) -> List[Question]:
        """
        Filter questions by difficulty level.

        Args:
            questions: List of questions
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            Filtered questions
        """
        return [q for q in questions if q.difficulty == difficulty]

    def filter_by_dependencies(
        self, questions: List[Question], answered_ids: List[str]
    ) -> List[Question]:
        """
        Filter questions that can be answered given already-answered questions.

        Args:
            questions: List of questions
            answered_ids: IDs of already-answered questions

        Returns:
            Questions whose dependencies are met
        """
        answered_set = set(answered_ids)
        return [
            q for q in questions
            if all(dep_id in answered_set for dep_id in q.dependencies)
        ]

    def validate_questions(self, questions: List[Question]) -> List[str]:
        """
        Validate a set of questions for correctness.

        Checks for:
        - Duplicate IDs
        - Invalid categories
        - Circular dependencies
        - Missing required fields

        Args:
            questions: List of questions to validate

        Returns:
            List of validation error messages (empty if valid)

        Example:
            errors = engine.validate_questions(questions)
            if errors:
                for error in errors:
                    print(f"Validation error: {error}")
        """
        errors = []

        # Check for duplicate IDs
        ids = [q.question_id for q in questions]
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            errors.append(f"Duplicate question IDs: {set(duplicates)}")

        # Check for required fields
        for q in questions:
            if not q.question_id:
                errors.append("Question missing question_id")
            if not q.text:
                errors.append(f"Question {q.question_id} missing text")
            if not q.category:
                errors.append(f"Question {q.question_id} missing category")

        # Check for circular dependencies
        for q in questions:
            if self._has_circular_dependency(q, questions, set()):
                errors.append(f"Question {q.question_id} has circular dependencies")

        return errors

    def _has_circular_dependency(
        self,
        question: Question,
        all_questions: List[Question],
        visited: set
    ) -> bool:
        """Check if a question has circular dependencies."""
        if question.question_id in visited:
            return True

        visited.add(question.question_id)

        for dep_id in question.dependencies:
            dep_question = next(
                (q for q in all_questions if q.question_id == dep_id), None
            )
            if dep_question and self._has_circular_dependency(
                dep_question, all_questions, visited.copy()
            ):
                return True

        return False

    def get_next_questions(
        self,
        all_questions: List[Question],
        answered_ids: List[str],
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[Question]:
        """
        Get the next questions to ask based on answered questions.

        Considers dependencies and optionally filters by category.

        Args:
            all_questions: All available questions
            answered_ids: IDs of already-answered questions
            category: Optional category to filter by
            limit: Maximum number of questions to return

        Returns:
            Next recommended questions
        """
        # Filter by answered questions (dependencies met)
        available = self.filter_by_dependencies(all_questions, answered_ids)

        # Exclude already answered
        available = [q for q in available if q.question_id not in answered_ids]

        # Filter by category if specified
        if category:
            available = self.filter_by_category(available, category)

        # Sort by difficulty (easy first) and return
        sorted_questions = sorted(
            available,
            key=lambda q: {"easy": 0, "medium": 1, "hard": 2}.get(q.difficulty, 1),
        )

        return sorted_questions[:limit]

    def to_dict(self, questions: List[Question]) -> List[Dict[str, Any]]:
        """Convert questions to dictionary representation."""
        return [q.to_dict() for q in questions]

    def to_json(self, questions: List[Question]) -> str:
        """Convert questions to JSON string."""
        return json.dumps(self.to_dict(questions), indent=2)

    def save_to_json(self, questions: List[Question], filepath: str) -> None:
        """
        Save questions to a JSON file.

        Args:
            questions: Questions to save
            filepath: Path to save file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.to_json(questions))

        logger.info(f"Saved {len(questions)} questions to {filepath}")


# Global question engine instance
_global_engine: Optional[QuestionTemplateEngine] = None


def get_question_engine() -> QuestionTemplateEngine:
    """Get the global question template engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = QuestionTemplateEngine()
    return _global_engine

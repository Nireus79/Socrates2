"""Tests for question template engine."""

import json

import pytest

from app.base import Question
from app.questions import QuestionTemplateEngine, get_question_engine


class TestQuestionTemplateEngine:
    """Test QuestionTemplateEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create a fresh question engine."""
        return QuestionTemplateEngine()

    @pytest.fixture
    def sample_questions_data(self):
        """Sample question data for testing."""
        return [
            {
                "question_id": "q1",
                "text": "Question 1?",
                "category": "Category A",
                "difficulty": "easy",
                "help_text": "Help for Q1",
                "dependencies": [],
            },
            {
                "question_id": "q2",
                "text": "Question 2?",
                "category": "Category A",
                "difficulty": "medium",
                "dependencies": ["q1"],
            },
            {
                "question_id": "q3",
                "text": "Question 3?",
                "category": "Category B",
                "difficulty": "hard",
                "dependencies": [],
            },
        ]

    def test_load_questions_from_dict(self, engine, sample_questions_data):
        """Test loading questions from dictionary."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        assert len(questions) == 3
        assert questions[0].question_id == "q1"
        assert questions[1].difficulty == "medium"

    def test_load_questions_invalid_data(self, engine):
        """Test loading question with missing required fields."""
        invalid_data = [{"question_id": "q1"}]  # Missing required fields
        # This will load but with None values, which should be caught by validation
        questions = engine.load_questions_from_dict(invalid_data)
        errors = engine.validate_questions(questions)
        assert len(errors) > 0  # Should have validation errors

    def test_filter_by_category(self, engine, sample_questions_data):
        """Test filtering questions by category."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        cat_a = engine.filter_by_category(questions, "Category A")
        assert len(cat_a) == 2
        assert all(q.category == "Category A" for q in cat_a)

    def test_filter_by_difficulty(self, engine, sample_questions_data):
        """Test filtering questions by difficulty."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        easy = engine.filter_by_difficulty(questions, "easy")
        assert len(easy) == 1
        assert easy[0].question_id == "q1"

    def test_filter_by_dependencies(self, engine, sample_questions_data):
        """Test filtering questions by dependencies."""
        questions = engine.load_questions_from_dict(sample_questions_data)

        # With no answered questions, only q1 and q3 are available (no dependencies)
        available = engine.filter_by_dependencies(questions, [])
        available_ids = {q.question_id for q in available}
        assert "q1" in available_ids
        assert "q3" in available_ids
        assert "q2" not in available_ids  # Requires q1

        # After answering q1, q2 becomes available
        available = engine.filter_by_dependencies(questions, ["q1"])
        available_ids = {q.question_id for q in available}
        assert "q2" in available_ids

    def test_validate_questions_success(self, engine, sample_questions_data):
        """Test validating correct questions."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        errors = engine.validate_questions(questions)
        assert len(errors) == 0

    def test_validate_questions_duplicate_ids(self, engine):
        """Test validation catches duplicate IDs."""
        data = [
            {
                "question_id": "q1",
                "text": "Q1?",
                "category": "C",
                "difficulty": "easy",
                "dependencies": [],
            },
            {
                "question_id": "q1",
                "text": "Q2?",
                "category": "C",
                "difficulty": "easy",
                "dependencies": [],
            },
        ]
        questions = engine.load_questions_from_dict(data)
        errors = engine.validate_questions(questions)
        assert any("Duplicate" in e for e in errors)

    def test_validate_questions_missing_fields(self, engine):
        """Test validation catches missing required fields."""
        data = [
            {
                "question_id": "q1",
                "category": "C",
                "difficulty": "easy",
                "dependencies": [],
            },  # Missing text
        ]
        questions = engine.load_questions_from_dict(data)
        errors = engine.validate_questions(questions)
        assert any("missing text" in e for e in errors)

    def test_validate_questions_circular_dependencies(self, engine):
        """Test validation catches circular dependencies."""
        data = [
            {
                "question_id": "q1",
                "text": "Q1?",
                "category": "C",
                "difficulty": "easy",
                "dependencies": ["q2"],
            },
            {
                "question_id": "q2",
                "text": "Q2?",
                "category": "C",
                "difficulty": "easy",
                "dependencies": ["q1"],
            },
        ]
        questions = engine.load_questions_from_dict(data)
        errors = engine.validate_questions(questions)
        assert any("circular" in e.lower() for e in errors)

    def test_get_next_questions(self, engine, sample_questions_data):
        """Test getting next recommended questions."""
        questions = engine.load_questions_from_dict(sample_questions_data)

        # Initially, should get q1 and q3 (no dependencies)
        next_qs = engine.get_next_questions(questions, [])
        ids = {q.question_id for q in next_qs}
        assert "q1" in ids
        assert "q3" in ids

        # After answering q1, should get q2
        next_qs = engine.get_next_questions(questions, ["q1"])
        ids = {q.question_id for q in next_qs}
        assert "q2" in ids
        assert "q1" not in ids  # Already answered

    def test_get_next_questions_with_category(self, engine, sample_questions_data):
        """Test getting next questions filtered by category."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        next_qs = engine.get_next_questions(questions, [], category="Category A")
        assert all(q.category == "Category A" for q in next_qs)

    def test_get_next_questions_with_limit(self, engine, sample_questions_data):
        """Test limit parameter."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        next_qs = engine.get_next_questions(questions, [], limit=1)
        assert len(next_qs) <= 1

    def test_to_dict(self, engine, sample_questions_data):
        """Test converting questions to dict."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        dict_list = engine.to_dict(questions)
        assert len(dict_list) == 3
        assert dict_list[0]["question_id"] == "q1"

    def test_to_json(self, engine, sample_questions_data):
        """Test converting questions to JSON."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        json_str = engine.to_json(questions)
        parsed = json.loads(json_str)
        assert len(parsed) == 3
        assert parsed[0]["question_id"] == "q1"

    def test_save_and_load_json(self, engine, sample_questions_data, tmp_path):
        """Test saving and loading questions from JSON."""
        questions = engine.load_questions_from_dict(sample_questions_data)
        filepath = tmp_path / "questions.json"

        # Save
        engine.save_to_json(questions, str(filepath))
        assert filepath.exists()

        # Load
        loaded_questions = engine.load_questions_from_json(str(filepath))
        assert len(loaded_questions) == 3
        assert loaded_questions[0].question_id == "q1"


class TestGlobalQuestionEngine:
    """Test global question engine instance."""

    def test_get_question_engine_singleton(self):
        """Test that get_question_engine returns singleton."""
        engine1 = get_question_engine()
        engine2 = get_question_engine()
        assert engine1 is engine2


class TestProgrammingDomainQuestions:
    """Test programming domain question loading."""

    def test_programming_questions_load(self):
        """Test that programming questions load correctly."""
        engine = QuestionTemplateEngine()
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        questions = domain.get_questions()

        assert len(questions) >= 14
        assert all(isinstance(q, Question) for q in questions)

    def test_programming_questions_have_dependencies(self):
        """Test that programming questions have proper dependencies."""
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        questions = domain.get_questions()

        # Check that some questions have dependencies
        with_deps = [q for q in questions if q.dependencies]
        assert len(with_deps) > 0

    def test_programming_questions_categories_match(self):
        """Test that question categories match domain categories."""
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        categories = set(domain.get_categories())
        question_categories = set(q.category for q in domain.get_questions())

        # All question categories should be in domain categories
        assert question_categories.issubset(categories)

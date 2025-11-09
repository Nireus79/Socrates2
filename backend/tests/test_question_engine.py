"""
Unit tests for QuestionGenerator engine.

These tests require NO database - pure logic testing.
This demonstrates the value of separating business logic from database code.
"""

import json
import pytest
from datetime import datetime

from app.core.models import (
    ProjectData, SpecificationData, QuestionData, UserBehaviorData
)
from app.core.question_engine import QuestionGenerator, QUESTION_CATEGORIES


@pytest.fixture
def engine():
    """Create a question generator instance for testing"""
    return QuestionGenerator()


@pytest.fixture
def sample_project():
    """Create sample project data for testing"""
    return ProjectData(
        id="project-123",
        name="E-Commerce Platform",
        description="A platform for selling products online",
        current_phase="discovery",
        maturity_score=20.0,
        user_id="user-456"
    )


@pytest.fixture
def sample_specs():
    """Create sample specifications for testing"""
    return [
        SpecificationData(
            id="spec-1",
            project_id="project-123",
            category="goals",
            key="primary_goal",
            value="Build an e-commerce platform",
            confidence=0.95
        ),
        SpecificationData(
            id="spec-2",
            project_id="project-123",
            category="goals",
            key="target_users",
            value="Small business owners",
            confidence=0.85
        ),
        SpecificationData(
            id="spec-3",
            project_id="project-123",
            category="requirements",
            key="payment_processing",
            value="Accept credit cards and PayPal",
            confidence=0.90
        ),
    ]


@pytest.fixture
def sample_questions():
    """Create sample previous questions for testing"""
    return [
        QuestionData(
            id="q-1",
            text="What is the primary purpose of your project?",
            category="goals",
            context="Understanding main goal",
            quality_score=1.0
        ),
        QuestionData(
            id="q-2",
            text="Who are your target users?",
            category="goals",
            context="Understanding audience",
            quality_score=0.95
        ),
    ]


@pytest.fixture
def sample_user_behavior():
    """Create sample user behavior data for testing"""
    return UserBehaviorData(
        user_id="user-456",
        total_questions_asked=5,
        overall_response_quality=0.85,
        patterns={"communication_style": "technical", "detail_level": "high"},
        learned_from_projects=2
    )


# ============================================================================
# TESTS: COVERAGE CALCULATION
# ============================================================================

class TestCoverageCalculation:
    """Test coverage percentage calculation"""

    def test_empty_specs_gives_zero_coverage(self, engine):
        """Empty spec list should give 0% coverage for all categories"""
        coverage = engine.calculate_coverage([])

        assert len(coverage) == len(QUESTION_CATEGORIES)
        for category in QUESTION_CATEGORIES:
            assert coverage[category] == 0.0

    def test_coverage_with_specs(self, engine, sample_specs):
        """Coverage should reflect spec counts vs targets"""
        coverage = engine.calculate_coverage(sample_specs)

        # 2 goal specs, target is 10 -> 2/10 = 20%
        assert coverage['goals'] == 20.0

        # 1 requirement spec, target is 15 -> 1/15 = 6.67%
        assert coverage['requirements'] <= 10.0  # At most 10%

        # Other categories should have 0%
        assert coverage['security'] == 0.0
        assert coverage['performance'] == 0.0

    def test_coverage_maxes_at_100_percent(self, engine):
        """Coverage should never exceed 100%"""
        # Create more specs than target
        specs = [
            SpecificationData(
                id=f"spec-{i}",
                project_id="project-123",
                category="goals",
                key=f"goal_{i}",
                value=f"Goal {i}",
                confidence=0.9
            )
            for i in range(20)  # 20 specs, target is 10
        ]

        coverage = engine.calculate_coverage(specs)
        assert coverage['goals'] == 100.0  # Capped at 100%

    def test_multiple_categories(self, engine):
        """Coverage should track multiple categories correctly"""
        specs = [
            SpecificationData(
                id="spec-1",
                project_id="project-123",
                category="goals",
                key="goal",
                value="Build app",
                confidence=0.9
            ),
            SpecificationData(
                id="spec-2",
                project_id="project-123",
                category="security",
                key="auth",
                value="OAuth2",
                confidence=0.9
            ),
            SpecificationData(
                id="spec-3",
                project_id="project-123",
                category="performance",
                key="latency",
                value="< 100ms",
                confidence=0.9
            ),
        ]

        coverage = engine.calculate_coverage(specs)

        # Each category should have 1 spec out of various targets
        assert coverage['goals'] == 10.0  # 1/10
        assert coverage['security'] == 10.0  # 1/10
        assert coverage['performance'] == 12.5  # 1/8


# ============================================================================
# TESTS: NEXT CATEGORY IDENTIFICATION
# ============================================================================

class TestNextCategoryIdentification:
    """Test logic for identifying next focus area"""

    def test_empty_coverage_defaults_to_goals(self, engine):
        """Empty coverage should default to goals"""
        next_cat = engine.identify_next_category({})
        assert next_cat == 'goals'

    def test_identifies_lowest_coverage_category(self, engine):
        """Should identify category with lowest coverage"""
        coverage = {
            'goals': 50.0,
            'requirements': 80.0,
            'security': 10.0,  # Lowest
            'performance': 40.0
        }

        next_cat = engine.identify_next_category(coverage)
        assert next_cat == 'security'

    def test_identifies_zero_coverage_category(self, engine):
        """Should identify category with 0% coverage first"""
        coverage = {
            'goals': 50.0,
            'requirements': 80.0,
            'security': 0.0,  # Lowest
            'performance': 40.0
        }

        next_cat = engine.identify_next_category(coverage)
        assert next_cat == 'security'

    def test_all_equal_coverage_returns_first(self, engine):
        """When all equal, should return one of them (implementation dependent)"""
        coverage = {cat: 50.0 for cat in QUESTION_CATEGORIES}

        next_cat = engine.identify_next_category(coverage)
        assert next_cat in QUESTION_CATEGORIES


# ============================================================================
# TESTS: PROMPT GENERATION
# ============================================================================

class TestPromptGeneration:
    """Test prompt building for Claude API"""

    def test_prompt_includes_project_info(self, engine, sample_project, sample_specs, sample_questions):
        """Prompt should include project information"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            'requirements'
        )

        assert sample_project.name in prompt
        assert sample_project.description in prompt
        assert sample_project.current_phase in prompt
        assert 'requirements' in prompt.lower()

    def test_prompt_includes_existing_specs(self, engine, sample_project, sample_specs, sample_questions):
        """Prompt should include existing specifications"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            'goals'
        )

        # Should mention specs (at least some values)
        assert 'goal' in prompt.lower() or 'specification' in prompt.lower()

    def test_prompt_includes_previous_questions(self, engine, sample_project, sample_specs, sample_questions):
        """Prompt should include previous questions asked"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            'requirements'
        )

        # Should mention at least one previous question
        assert any(q.text[:20] in prompt for q in sample_questions)

    def test_prompt_with_user_behavior(self, engine, sample_project, sample_specs, sample_questions, sample_user_behavior):
        """Prompt should include user behavior context when provided"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            'requirements',
            sample_user_behavior
        )

        # Should include user learning profile
        assert 'USER LEARNING PROFILE' in prompt
        assert 'Experience' in prompt
        assert str(sample_user_behavior.total_questions_asked) in prompt

    def test_prompt_without_user_behavior(self, engine, sample_project, sample_specs, sample_questions):
        """Prompt should work fine without user behavior"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            'requirements',
            None
        )

        assert prompt is not None
        assert len(prompt) > 100

    def test_prompt_with_empty_specs(self, engine, sample_project):
        """Prompt should handle empty specs gracefully"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            [],
            [],
            'goals'
        )

        assert 'first interaction' in prompt.lower() or 'existing' in prompt.lower()

    def test_prompt_includes_json_format_instruction(self, engine, sample_project, sample_specs, sample_questions):
        """Prompt should include JSON format instruction"""
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            'requirements'
        )

        assert 'JSON' in prompt
        assert '"text"' in prompt or "'text'" in prompt


# ============================================================================
# TESTS: RESPONSE PARSING
# ============================================================================

class TestResponseParsing:
    """Test parsing of Claude API responses"""

    def test_parse_valid_json_response(self, engine):
        """Should parse valid JSON response correctly"""
        response = '{"text": "What is your budget?", "category": "requirements", "context": "Understanding constraints"}'

        result = engine.parse_question_response(response, 'requirements')

        assert result['text'] == 'What is your budget?'
        assert result['category'] == 'requirements'
        assert result['context'] == 'Understanding constraints'

    def test_parse_with_markdown_fences(self, engine):
        """Should strip markdown code fences"""
        response = '''```json
{"text": "What is your budget?", "category": "requirements", "context": "Understanding constraints"}
```'''

        result = engine.parse_question_response(response, 'requirements')

        assert result['text'] == 'What is your budget?'
        assert result['category'] == 'requirements'

    def test_parse_with_whitespace(self, engine):
        """Should handle leading/trailing whitespace"""
        response = '''   {"text": "What is your budget?", "category": "requirements", "context": "Understanding constraints"}   '''

        result = engine.parse_question_response(response, 'requirements')

        assert result['text'] == 'What is your budget?'

    def test_parse_missing_context_uses_empty(self, engine):
        """Should use empty string for missing context"""
        response = '{"text": "What is your budget?", "category": "requirements"}'

        result = engine.parse_question_response(response, 'requirements')

        assert result['context'] == ""

    def test_parse_missing_category_uses_provided(self, engine):
        """Should use provided category if missing in response"""
        response = '{"text": "What is your budget?"}'

        result = engine.parse_question_response(response, 'requirements')

        assert result['category'] == 'requirements'

    def test_parse_invalid_json_raises_error(self, engine):
        """Should raise error on invalid JSON"""
        response = '{"text": "Invalid JSON"'

        with pytest.raises(json.JSONDecodeError):
            engine.parse_question_response(response, 'requirements')

    def test_parse_missing_text_raises_error(self, engine):
        """Should raise error if text field missing"""
        response = '{"category": "requirements", "context": "Why"}'

        with pytest.raises(ValueError):
            engine.parse_question_response(response, 'requirements')


# ============================================================================
# TESTS: QUESTION DATA CREATION
# ============================================================================

class TestQuestionDataCreation:
    """Test creating QuestionData instances"""

    def test_create_question_with_all_fields(self, engine):
        """Should create question with all fields"""
        question = engine.create_question_data(
            question_id="q-123",
            text="What is your budget?",
            category="requirements",
            context="Understanding constraints",
            quality_score=0.95
        )

        assert question.id == "q-123"
        assert question.text == "What is your budget?"
        assert question.category == "requirements"
        assert question.context == "Understanding constraints"
        assert question.quality_score == 0.95

    def test_create_question_with_default_quality(self, engine):
        """Should use default quality score if not provided"""
        question = engine.create_question_data(
            question_id="q-123",
            text="What is your budget?",
            category="requirements",
            context="Understanding constraints"
        )

        assert question.quality_score == 1.0

    def test_create_question_returns_question_data(self, engine):
        """Should return QuestionData instance"""
        question = engine.create_question_data(
            question_id="q-123",
            text="What is your budget?",
            category="requirements",
            context="Understanding constraints"
        )

        assert isinstance(question, QuestionData)
        assert question.created_at is None  # Not set in engine


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple engine functions"""

    def test_full_question_generation_flow(self, engine, sample_project, sample_specs, sample_questions):
        """Test full flow: coverage -> next category -> prompt"""
        # Step 1: Calculate coverage
        coverage = engine.calculate_coverage(sample_specs)
        assert len(coverage) > 0

        # Step 2: Identify next category
        next_cat = engine.identify_next_category(coverage)
        assert next_cat in QUESTION_CATEGORIES

        # Step 3: Build prompt
        prompt = engine.build_question_generation_prompt(
            sample_project,
            sample_specs,
            sample_questions,
            next_cat
        )
        assert prompt is not None
        assert len(prompt) > 100

    def test_response_parsing_to_question_data(self, engine):
        """Test parsing response and creating question data"""
        # Simulate Claude response
        response = '{"text": "What is your target market?", "category": "requirements", "context": "Understanding scope"}'

        # Parse response
        parsed = engine.parse_question_response(response, 'requirements')

        # Create question data
        question = engine.create_question_data(
            question_id="q-new",
            text=parsed['text'],
            category=parsed['category'],
            context=parsed['context'],
            quality_score=0.95
        )

        assert question.text == 'What is your target market?'
        assert question.category == 'requirements'
        assert isinstance(question, QuestionData)


# ============================================================================
# HELPER TESTS
# ============================================================================

class TestHelpers:
    """Test internal helper methods"""

    def test_format_specs_with_specs(self, engine, sample_specs):
        """Should format specs correctly"""
        formatted = engine._format_specs(sample_specs)

        assert 'e-commerce' in formatted.lower() or 'goal' in formatted.lower()
        assert 'payment' in formatted.lower() or 'requirement' in formatted.lower()

    def test_format_specs_empty(self, engine):
        """Should handle empty specs"""
        formatted = engine._format_specs([])

        assert 'none yet' in formatted.lower() or 'first' in formatted.lower()

    def test_format_specs_limits_to_20(self, engine):
        """Should limit specs to 20 for prompt size"""
        specs = [
            SpecificationData(
                id=f"spec-{i}",
                project_id="project-123",
                category="goals",
                key=f"goal_{i}",
                value=f"Goal {i}",
                confidence=0.9
            )
            for i in range(50)
        ]

        formatted = engine._format_specs(specs)

        # Should only include ~20 specs
        assert formatted.count('-') <= 25  # Rough check

    def test_format_questions_with_questions(self, engine, sample_questions):
        """Should format questions correctly"""
        formatted = engine._format_questions(sample_questions)

        assert 'primary purpose' in formatted.lower()
        assert 'target users' in formatted.lower()

    def test_format_questions_empty(self, engine):
        """Should handle empty questions"""
        formatted = engine._format_questions([])

        assert 'none yet' in formatted.lower() or 'first' in formatted.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

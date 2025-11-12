"""Tests for ProgrammingDomain implementation."""

import pytest

from app.programming import ProgrammingDomain


class TestProgrammingDomain:
    """Test ProgrammingDomain implementation."""

    @pytest.fixture
    def domain(self):
        """Create a fresh programming domain."""
        return ProgrammingDomain()

    def test_domain_metadata(self, domain):
        """Test domain metadata."""
        assert domain.domain_id == "programming"
        assert domain.name == "Software Programming"
        assert domain.version == "1.0.0"
        assert "code generation" in domain.description.lower()

    def test_categories(self, domain):
        """Test that programming domain has expected categories."""
        categories = domain.get_categories()
        assert "Performance" in categories
        assert "Security" in categories
        assert "Scalability" in categories
        assert "Usability" in categories
        assert "Reliability" in categories
        assert "Maintainability" in categories
        assert "Accessibility" in categories

    def test_questions_exist(self, domain):
        """Test that questions are defined."""
        questions = domain.get_questions()
        assert len(questions) > 0
        # Should have questions for each category
        categories = domain.get_categories()
        for cat in categories:
            cat_questions = domain.get_questions_by_category(cat)
            assert len(cat_questions) > 0, f"No questions for category {cat}"

    def test_questions_have_required_fields(self, domain):
        """Test that all questions have required fields."""
        questions = domain.get_questions()
        for q in questions:
            assert q.question_id
            assert q.text
            assert q.category in domain.get_categories()
            assert q.difficulty in ["easy", "medium", "hard"]

    def test_export_formats_exist(self, domain):
        """Test that export formats are defined."""
        formats = domain.get_export_formats()
        assert len(formats) >= 8  # At least 8 languages

        # Check for key languages
        language_ids = {f.format_id for f in formats}
        assert "python" in language_ids
        assert "javascript" in language_ids
        assert "typescript" in language_ids
        assert "go" in language_ids
        assert "java" in language_ids
        assert "rust" in language_ids
        assert "csharp" in language_ids
        assert "kotlin" in language_ids

    def test_export_format_details(self, domain):
        """Test that export formats have correct details."""
        python_format = domain.get_export_format("python")
        assert python_format is not None
        assert python_format.name == "Python"
        assert python_format.file_extension == ".py"
        assert python_format.mime_type == "text/x-python"

    def test_conflict_rules_exist(self, domain):
        """Test that conflict rules are defined."""
        rules = domain.get_conflict_rules()
        assert len(rules) > 0

    def test_conflict_rule_details(self, domain):
        """Test conflict rule structure."""
        rules = domain.get_conflict_rules()
        for rule in rules:
            assert rule.rule_id
            assert rule.name
            assert rule.description
            assert rule.condition
            assert rule.severity in ["error", "warning", "info"]

    def test_quality_analyzers_defined(self, domain):
        """Test that quality analyzers are specified."""
        analyzers = domain.get_quality_analyzers()
        assert len(analyzers) > 0
        # Should include bias detector (universal)
        assert "bias_detector" in analyzers

    def test_domain_serialization(self, domain):
        """Test converting domain to dict."""
        data = domain.to_dict()
        assert data["domain_id"] == "programming"
        assert "categories" in data
        assert "export_formats" in data
        assert "conflict_rules" in data
        assert len(data["export_formats"]) >= 8

    def test_metadata(self, domain):
        """Test domain metadata."""
        metadata = domain.get_metadata()
        assert metadata["domain_id"] == "programming"
        assert metadata["question_count"] > 0
        assert metadata["export_formats"] >= 8
        assert metadata["conflict_rules"] > 0  # conflict_rules is a count, not a list


class TestProgrammingDomainQuestions:
    """Test specific programming domain questions."""

    @pytest.fixture
    def domain(self):
        """Create a fresh programming domain."""
        return ProgrammingDomain()

    def test_performance_questions(self, domain):
        """Test that performance questions exist."""
        perf_questions = domain.get_questions_by_category("Performance")
        assert len(perf_questions) >= 3
        question_ids = {q.question_id for q in perf_questions}
        assert "perf_1" in question_ids
        assert "perf_2" in question_ids
        assert "perf_3" in question_ids

    def test_security_questions(self, domain):
        """Test that security questions exist."""
        sec_questions = domain.get_questions_by_category("Security")
        assert len(sec_questions) >= 3

    def test_scalability_questions(self, domain):
        """Test that scalability questions exist."""
        scale_questions = domain.get_questions_by_category("Scalability")
        assert len(scale_questions) >= 2

    def test_difficulty_distribution(self, domain):
        """Test that questions have varied difficulty."""
        questions = domain.get_questions()
        difficulties = {q.difficulty for q in questions}
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties

    def test_questions_have_help_text(self, domain):
        """Test that questions have helpful guidance."""
        questions = domain.get_questions()
        questions_with_help = [q for q in questions if q.help_text]
        assert len(questions_with_help) > len(questions) * 0.7  # At least 70% have help


class TestProgrammingDomainExports:
    """Test programming domain export formats."""

    @pytest.fixture
    def domain(self):
        """Create a fresh programming domain."""
        return ProgrammingDomain()

    def test_all_formats_have_templates(self, domain):
        """Test that all export formats have template IDs."""
        formats = domain.get_export_formats()
        for fmt in formats:
            assert fmt.template_id
            assert fmt.file_extension
            assert fmt.mime_type

    def test_get_format_by_language(self, domain):
        """Test looking up format by language ID."""
        for lang in ["python", "javascript", "typescript", "go"]:
            fmt = domain.get_export_format(lang)
            assert fmt is not None
            assert fmt.format_id == lang

    def test_nonexistent_format_returns_none(self, domain):
        """Test that nonexistent format returns None."""
        fmt = domain.get_export_format("cobol")
        assert fmt is None


class TestProgrammingDomainRules:
    """Test programming domain conflict rules."""

    @pytest.fixture
    def domain(self):
        """Create a fresh programming domain."""
        return ProgrammingDomain()

    def test_rules_are_named(self, domain):
        """Test that all rules have meaningful names."""
        rules = domain.get_conflict_rules()
        assert len(rules) > 0
        for rule in rules:
            assert rule.name
            assert len(rule.name) > 0

    def test_rules_have_conditions(self, domain):
        """Test that all rules define conditions."""
        rules = domain.get_conflict_rules()
        for rule in rules:
            assert rule.condition
            assert len(rule.condition) > 0

    def test_error_severity_rules(self, domain):
        """Test that critical rules are marked as errors."""
        rules = domain.get_conflict_rules()
        error_rules = [r for r in rules if r.severity == "error"]
        assert len(error_rules) > 0
        # Performance and security conflicts should be errors
        error_names = {r.name for r in error_rules}
        assert any("Performance" in name or "performance" in name for name in error_names)

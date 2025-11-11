"""Tests for BaseDomain abstract class."""

from ..base import BaseDomain, ConflictRule, ExportFormat, Question, SeverityLevel


class TestDomain(BaseDomain):
    """Concrete implementation for testing."""

    domain_id = "test"
    name = "Test Domain"
    version = "1.0.0"
    description = "A test domain"

    def get_categories(self):
        return ["Category1", "Category2"]

    def get_questions(self):
        return [
            Question(
                question_id="q1",
                text="Test question 1?",
                category="Category1",
                difficulty="easy",
            ),
            Question(
                question_id="q2",
                text="Test question 2?",
                category="Category2",
                difficulty="hard",
            ),
        ]

    def get_export_formats(self):
        return [
            ExportFormat(
                format_id="format1",
                name="Format 1",
                description="Test format",
                file_extension=".txt",
                mime_type="text/plain",
                template_id="test_template",
            ),
        ]

    def get_conflict_rules(self):
        return [
            ConflictRule(
                rule_id="rule1",
                name="Test Rule",
                description="A test rule",
                condition="always true",
                severity=SeverityLevel.ERROR,
            ),
        ]

    def get_quality_analyzers(self):
        return ["analyzer1", "analyzer2"]


class TestBaseDomain:
    """Test BaseDomain functionality."""

    def test_domain_initialization(self):
        """Test domain can be initialized."""
        domain = TestDomain()
        assert domain.domain_id == "test"
        assert domain.name == "Test Domain"
        assert domain.version == "1.0.0"

    def test_get_categories(self):
        """Test getting categories."""
        domain = TestDomain()
        categories = domain.get_categories()
        assert len(categories) == 2
        assert "Category1" in categories

    def test_get_questions(self):
        """Test getting all questions."""
        domain = TestDomain()
        questions = domain.get_questions()
        assert len(questions) == 2
        assert questions[0].question_id == "q1"

    def test_get_questions_by_category(self):
        """Test filtering questions by category."""
        domain = TestDomain()
        questions = domain.get_questions_by_category("Category1")
        assert len(questions) == 1
        assert questions[0].category == "Category1"

    def test_get_questions_by_difficulty(self):
        """Test filtering questions by difficulty."""
        domain = TestDomain()
        easy_questions = domain.get_questions_by_difficulty("easy")
        assert len(easy_questions) == 1
        assert easy_questions[0].difficulty == "easy"

    def test_get_export_formats(self):
        """Test getting export formats."""
        domain = TestDomain()
        formats = domain.get_export_formats()
        assert len(formats) == 1
        assert formats[0].format_id == "format1"

    def test_get_export_format(self):
        """Test getting specific export format."""
        domain = TestDomain()
        fmt = domain.get_export_format("format1")
        assert fmt is not None
        assert fmt.name == "Format 1"

    def test_get_export_format_not_found(self):
        """Test getting non-existent export format."""
        domain = TestDomain()
        fmt = domain.get_export_format("nonexistent")
        assert fmt is None

    def test_get_conflict_rules(self):
        """Test getting conflict rules."""
        domain = TestDomain()
        rules = domain.get_conflict_rules()
        assert len(rules) == 1
        assert rules[0].rule_id == "rule1"

    def test_get_quality_analyzers(self):
        """Test getting quality analyzers."""
        domain = TestDomain()
        analyzers = domain.get_quality_analyzers()
        assert len(analyzers) == 2
        assert "analyzer1" in analyzers

    def test_metadata(self):
        """Test getting domain metadata."""
        domain = TestDomain()
        metadata = domain.get_metadata()
        assert metadata["domain_id"] == "test"
        assert metadata["question_count"] == 2
        assert metadata["export_formats"] == 1

    def test_to_dict(self):
        """Test converting domain to dictionary."""
        domain = TestDomain()
        data = domain.to_dict()
        assert data["domain_id"] == "test"
        assert data["name"] == "Test Domain"
        assert len(data["categories"]) == 2
        assert len(data["export_formats"]) == 1


class TestQuestion:
    """Test Question dataclass."""

    def test_question_creation(self):
        """Test creating a question."""
        q = Question(
            question_id="q1",
            text="What is this?",
            category="general",
            difficulty="easy",
        )
        assert q.question_id == "q1"
        assert q.text == "What is this?"
        assert q.difficulty == "easy"

    def test_question_with_dependencies(self):
        """Test question with dependencies."""
        q = Question(
            question_id="q2",
            text="Follow-up?",
            category="general",
            dependencies=["q1"],
        )
        assert q.dependencies == ["q1"]

    def test_question_to_dict(self):
        """Test converting question to dict."""
        q = Question(
            question_id="q1",
            text="What?",
            category="test",
            difficulty="hard",
            help_text="Some help",
        )
        data = q.to_dict()
        assert data["question_id"] == "q1"
        assert data["text"] == "What?"
        assert data["category"] == "test"


class TestSeverityLevel:
    """Test SeverityLevel enum."""

    def test_severity_values(self):
        """Test severity level values."""
        assert SeverityLevel.ERROR.value == "error"
        assert SeverityLevel.WARNING.value == "warning"
        assert SeverityLevel.INFO.value == "info"

    def test_severity_comparison(self):
        """Test severity level comparison."""
        assert SeverityLevel.ERROR == SeverityLevel.ERROR
        assert SeverityLevel.ERROR != SeverityLevel.WARNING

"""
Base domain abstraction for Socrates.

All knowledge domains (programming, book writing, business planning, etc.)
inherit from BaseDomain and implement these extension points.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SeverityLevel(str, Enum):
    """Severity levels for conflicts and quality issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ConflictRule:
    """A rule that can be violated, creating a conflict."""

    rule_id: str
    name: str
    description: str
    condition: str  # Expressed in domain rule language
    severity: SeverityLevel = SeverityLevel.ERROR
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "severity": self.severity.value,
            "message": self.message,
        }


@dataclass
class QualityIssue:
    """A quality issue detected by an analyzer."""

    analyzer_type: str
    issue_type: str
    severity: SeverityLevel
    message: str
    suggestion: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analyzer_type": self.analyzer_type,
            "issue_type": self.issue_type,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "location": self.location,
        }


@dataclass
class QualityAnalyzer:
    """A quality analyzer that can detect issues in a specification."""

    analyzer_id: str
    name: str
    description: str
    analyzer_type: str  # e.g., "bias_detector", "performance_validator"
    enabled: bool = True
    required: bool = False  # If true, must be run
    tags: List[str] = field(default_factory=list)  # e.g., ["universal", "programming", "security"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analyzer_id": self.analyzer_id,
            "name": self.name,
            "description": self.description,
            "analyzer_type": self.analyzer_type,
            "enabled": self.enabled,
            "required": self.required,
            "tags": self.tags,
        }


@dataclass
class ExportFormat:
    """An export format supported by a domain."""

    format_id: str
    name: str
    description: str
    file_extension: str
    mime_type: str
    template_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format_id": self.format_id,
            "name": self.name,
            "description": self.description,
            "file_extension": self.file_extension,
            "mime_type": self.mime_type,
            "template_id": self.template_id,
        }


@dataclass
class Question:
    """A question in the Socratic dialogue."""

    question_id: str
    text: str
    category: str
    difficulty: str = "medium"  # easy, medium, hard
    help_text: Optional[str] = None
    example_answer: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Questions that must be answered first

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_id": self.question_id,
            "text": self.text,
            "category": self.category,
            "difficulty": self.difficulty,
            "help_text": self.help_text,
            "example_answer": self.example_answer,
            "follow_up_questions": self.follow_up_questions,
            "dependencies": self.dependencies,
        }


class BaseDomain(ABC):
    """
    Abstract base class for all knowledge domains in Socrates.

    Each domain represents a knowledge area (programming, books, business, etc.)
    and defines how specifications, questions, exports, and quality checks work.

    Example:
        @dataclass
        class ProgrammingDomain(BaseDomain):
            domain_id = "programming"
            name = "Software Programming"
            version = "1.0.0"

            def get_categories(self) -> List[str]:
                return ["Performance", "Security", "Scalability", "Usability"]

            def get_questions(self) -> List[Question]:
                return [
                    Question(
                        question_id="q1",
                        text="What is your target response time?",
                        category="Performance"
                    ),
                    ...
                ]
    """

    # Domain identity
    domain_id: str
    name: str
    version: str
    description: str = ""

    def __init__(self):
        """Initialize domain."""
        if not hasattr(self, "domain_id") or not self.domain_id:
            raise ValueError("Domain must define domain_id")
        if not hasattr(self, "name") or not self.name:
            raise ValueError("Domain must define name")

    # ========== Categories ==========

    @abstractmethod
    def get_categories(self) -> List[str]:
        """
        Return the specification categories for this domain.

        Examples:
            Programming: ["Performance", "Security", "Scalability", "Usability"]
            Book Writing: ["Plot", "Characters", "Setting", "Themes"]
            Business: ["Market", "Product", "Team", "Revenue"]
        """
        pass

    # ========== Questions ==========

    @abstractmethod
    def get_questions(self) -> List[Question]:
        """
        Return all Socratic questions for this domain.

        Questions guide users through specification gathering.
        """
        pass

    def get_questions_by_category(self, category: str) -> List[Question]:
        """Get questions for a specific category."""
        return [q for q in self.get_questions() if q.category == category]

    def get_questions_by_difficulty(self, difficulty: str) -> List[Question]:
        """Get questions by difficulty level."""
        return [q for q in self.get_questions() if q.difficulty == difficulty]

    # ========== Export Formats ==========

    @abstractmethod
    def get_export_formats(self) -> List[ExportFormat]:
        """
        Return all export formats supported by this domain.

        Examples:
            Programming: ["python", "javascript", "typescript", "go", "java", ...]
            Book Writing: ["outline", "character_profiles", "world_building"]
            Business: ["pitch_deck", "business_plan", "financial_model"]
        """
        pass

    def get_export_format(self, format_id: str) -> Optional[ExportFormat]:
        """Get a specific export format."""
        for fmt in self.get_export_formats():
            if fmt.format_id == format_id:
                return fmt
        return None

    # ========== Conflict Rules ==========

    @abstractmethod
    def get_conflict_rules(self) -> List[ConflictRule]:
        """
        Return all conflict detection rules for this domain.

        Rules define logical contradictions that can occur in specifications.

        Examples:
            Programming:
                - "Can't have conflicting performance requirements"
                - "Security level must be consistent"

            Book Writing:
                - "Character can't be in two places simultaneously"
                - "Can't introduce information before it's revealed"
        """
        pass

    # ========== Quality Analyzers ==========

    @abstractmethod
    def get_quality_analyzers(self) -> List[str]:
        """
        Return IDs of quality analyzers enabled for this domain.

        Analyzers detect quality issues in specifications.

        Examples:
            Programming: ["bias_detector", "performance_validator"]
            Book Writing: ["cliche_detector", "plot_hole_detector", "character_arc_validator"]
            Business: ["market_validator", "budget_checker", "realistic_projections"]
        """
        pass

    # ========== Domain Metadata ==========

    def get_metadata(self) -> Dict[str, Any]:
        """Get comprehensive domain metadata."""
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "categories": self.get_categories(),
            "question_count": len(self.get_questions()),
            "export_formats": len(self.get_export_formats()),
            "conflict_rules": len(self.get_conflict_rules()),
            "analyzers": self.get_quality_analyzers(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert domain to dictionary representation."""
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "categories": self.get_categories(),
            "export_formats": [fmt.to_dict() for fmt in self.get_export_formats()],
            "conflict_rules": [rule.to_dict() for rule in self.get_conflict_rules()],
            "analyzers": self.get_quality_analyzers(),
        }

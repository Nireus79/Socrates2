"""
Abstract base class for knowledge domains in Socrates.

All domain implementations (Programming, Data Engineering, Architecture, etc.)
should inherit from BaseDomain.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .models import ConflictRule, ExportFormat, Question


class BaseDomain(ABC):
    """
    Abstract base class for Socrates knowledge domains.

    Each domain provides:
    - Questions in specific categories
    - Export formats for code generation
    - Conflict detection rules
    - Domain-specific configuration
    """

    domain_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""

    @abstractmethod
    def get_categories(self) -> List[str]:
        """Get all question categories in this domain."""
        pass

    @abstractmethod
    def get_questions(self) -> List[Question]:
        """Get all questions in this domain."""
        pass

    @abstractmethod
    def get_export_formats(self) -> List[ExportFormat]:
        """Get all export formats supported by this domain."""
        pass

    @abstractmethod
    def get_conflict_rules(self) -> List[ConflictRule]:
        """Get all conflict detection rules for this domain."""
        pass

    @abstractmethod
    def get_quality_analyzers(self) -> List[str]:
        """Get IDs of quality analyzers enabled for this domain."""
        pass

    def get_questions_by_category(self, category: str) -> List[Question]:
        """Get questions filtered by category."""
        all_questions = self.get_questions()
        return [q for q in all_questions if q.category == category]

    def get_questions_by_difficulty(self, difficulty: str) -> List[Question]:
        """Get questions filtered by difficulty level."""
        all_questions = self.get_questions()
        return [q for q in all_questions if q.difficulty == difficulty]

    def get_export_format(self, format_id: str) -> ExportFormat | None:
        """Get a specific export format by ID."""
        formats = self.get_export_formats()
        for fmt in formats:
            if fmt.format_id == format_id:
                return fmt
        return None

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

    def to_dict(self) -> dict:
        """Convert domain to dictionary representation."""
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "categories": self.get_categories(),
            "num_questions": len(self.get_questions()),
            "export_formats": [f.model_dump() for f in self.get_export_formats()],
            "conflict_rules": [r.model_dump() for r in self.get_conflict_rules()],
        }

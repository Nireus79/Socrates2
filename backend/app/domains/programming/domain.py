"""
Programming domain implementation for Socrates2.

Defines specifications, questions, exports, and rules for software development projects.
Questions are loaded from questions.json configuration file.
"""

import logging
from pathlib import Path
from typing import List, Optional
import json

from ..base import BaseDomain, Question, ExportFormat, ConflictRule, SeverityLevel
from ..questions import QuestionTemplateEngine

logger = logging.getLogger(__name__)


class ProgrammingDomain(BaseDomain):
    """
    Software Programming domain for Socrates2.

    Handles specification and code generation for software projects.
    Supports 8+ programming languages with specialized patterns.

    Questions are loaded from questions.json configuration file,
    making them easily customizable without code changes.
    """

    domain_id = "programming"
    name = "Software Programming"
    version = "1.0.0"
    description = "Specification and code generation for software development projects"

    def __init__(self):
        """Initialize programming domain and load questions from configuration."""
        super().__init__()
        self._questions: Optional[List[Question]] = None
        self._load_questions()

    def _load_questions(self) -> None:
        """Load questions from questions.json configuration file."""
        try:
            # Get path to questions.json (same directory as this file)
            config_dir = Path(__file__).parent
            questions_file = config_dir / "questions.json"

            if not questions_file.exists():
                logger.error(f"Questions file not found: {questions_file}")
                self._questions = []
                return

            # Load questions using question template engine
            engine = QuestionTemplateEngine()
            self._questions = engine.load_questions_from_json(str(questions_file))
            logger.info(f"Loaded {len(self._questions)} programming questions")

            # Validate questions
            errors = engine.validate_questions(self._questions)
            if errors:
                logger.warning(f"Question validation errors: {errors}")

        except Exception as e:
            logger.error(f"Failed to load programming questions: {e}")
            self._questions = []

    def get_categories(self) -> List[str]:
        """Return specification categories for programming."""
        return [
            "Performance",
            "Security",
            "Scalability",
            "Usability",
            "Reliability",
            "Maintainability",
            "Accessibility",
        ]

    def get_questions(self) -> List[Question]:
        """Return Socratic questions for programming domain from configuration."""
        if self._questions is None:
            self._load_questions()
        return self._questions if self._questions is not None else []

    def get_export_formats(self) -> List[ExportFormat]:
        """Return supported code generation formats."""
        return [
            ExportFormat(
                format_id="python",
                name="Python",
                description="Python class/function generation",
                file_extension=".py",
                mime_type="text/x-python",
                template_id="python_class",
            ),
            ExportFormat(
                format_id="javascript",
                name="JavaScript",
                description="JavaScript class/function generation",
                file_extension=".js",
                mime_type="text/javascript",
                template_id="js_class",
            ),
            ExportFormat(
                format_id="typescript",
                name="TypeScript",
                description="TypeScript class/interface generation",
                file_extension=".ts",
                mime_type="text/typescript",
                template_id="ts_class",
            ),
            ExportFormat(
                format_id="go",
                name="Go",
                description="Go struct/interface generation",
                file_extension=".go",
                mime_type="text/x-go",
                template_id="go_struct",
            ),
            ExportFormat(
                format_id="java",
                name="Java",
                description="Java class generation",
                file_extension=".java",
                mime_type="text/x-java-source",
                template_id="java_class",
            ),
            ExportFormat(
                format_id="rust",
                name="Rust",
                description="Rust struct generation",
                file_extension=".rs",
                mime_type="text/x-rust",
                template_id="rust_struct",
            ),
            ExportFormat(
                format_id="csharp",
                name="C#",
                description="C# class generation",
                file_extension=".cs",
                mime_type="text/x-csharp",
                template_id="csharp_class",
            ),
            ExportFormat(
                format_id="kotlin",
                name="Kotlin",
                description="Kotlin data class generation",
                file_extension=".kt",
                mime_type="text/x-kotlin",
                template_id="kotlin_dataclass",
            ),
        ]

    def get_conflict_rules(self) -> List[ConflictRule]:
        """Return conflict detection rules for programming."""
        return [
            ConflictRule(
                rule_id="perf_conflict",
                name="Performance Consistency",
                description="Response time requirements must be consistent",
                condition="response_time specifications must not contradict",
                severity=SeverityLevel.ERROR,
                message="Conflicting response time specifications",
            ),
            ConflictRule(
                rule_id="sec_conflict",
                name="Security Consistency",
                description="Security standards must align",
                condition="encryption_standard specifications must be compatible",
                severity=SeverityLevel.ERROR,
                message="Conflicting security specifications",
            ),
            ConflictRule(
                rule_id="scale_conflict",
                name="Scalability Planning",
                description="Scalability approach must be feasible",
                condition="throughput and resource constraints must align",
                severity=SeverityLevel.WARNING,
                message="Scalability specifications may be unrealistic",
            ),
            ConflictRule(
                rule_id="arch_consistency",
                name="Architectural Alignment",
                description="Architecture must support requirements",
                condition="performance targets must be achievable with proposed architecture",
                severity=SeverityLevel.ERROR,
                message="Requirements conflict with proposed architecture",
            ),
        ]

    def get_quality_analyzers(self) -> List[str]:
        """Return quality analyzers for programming domain."""
        return [
            "bias_detector",  # Universal analyzer
            "performance_validator",
            "security_validator",
            "scalability_checker",
        ]

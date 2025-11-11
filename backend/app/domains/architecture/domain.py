"""
Architecture domain implementation for Socrates2.

Defines specifications, questions, exports, and rules for system architecture.
Questions are loaded from questions.json configuration file.
"""

import logging
from pathlib import Path
from typing import List, Optional

from ..analyzers import QualityAnalyzerEngine
from ..base import BaseDomain, ConflictRule, ExportFormat, QualityAnalyzer, Question
from ..exporters import ExportTemplateEngine
from ..questions import QuestionTemplateEngine
from ..rules import ConflictRuleEngine

logger = logging.getLogger(__name__)


class ArchitectureDomain(BaseDomain):
    """
    System Architecture domain for Socrates2.

    Handles specification for distributed systems, microservices, and enterprise architectures.
    Supports architecture decision making, design patterns, and deployment strategies.

    All specifications are loaded from configuration files:
    - questions.json: Architecture design questions
    - exporters.json: Architecture documentation formats (diagrams, specs, IaC)
    - rules.json: Architecture pattern rules
    - analyzers.json: Quality analyzers
    Making everything easily customizable without code changes.
    """

    domain_id = "architecture"
    name = "System Architecture"
    version = "1.0.0"
    description = "System architecture design and distributed systems specification"

    def __init__(self):
        """Initialize architecture domain and load all configuration from files."""
        super().__init__()
        self._questions: Optional[List[Question]] = None
        self._exporters: Optional[List[ExportFormat]] = None
        self._rules: Optional[List[ConflictRule]] = None
        self._analyzers: Optional[List[QualityAnalyzer]] = None
        self._load_questions()
        self._load_exporters()
        self._load_rules()
        self._load_analyzers()

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
            logger.info(f"Loaded {len(self._questions)} architecture questions")

            # Validate questions
            errors = engine.validate_questions(self._questions)
            if errors:
                logger.warning(f"Question validation errors: {errors}")

        except Exception as e:
            logger.error(f"Failed to load architecture questions: {e}")
            self._questions = []

    def _load_exporters(self) -> None:
        """Load exporters from exporters.json configuration file."""
        try:
            # Get path to exporters.json (same directory as this file)
            config_dir = Path(__file__).parent
            exporters_file = config_dir / "exporters.json"

            if not exporters_file.exists():
                logger.error(f"Exporters file not found: {exporters_file}")
                self._exporters = []
                return

            # Load exporters using exporter template engine
            engine = ExportTemplateEngine()
            self._exporters = engine.load_exporters_from_json(str(exporters_file))
            logger.info(f"Loaded {len(self._exporters)} architecture exporters")

            # Validate exporters
            errors = engine.validate_exporters(self._exporters)
            if errors:
                logger.warning(f"Exporter validation errors: {errors}")

        except Exception as e:
            logger.error(f"Failed to load architecture exporters: {e}")
            self._exporters = []

    def _load_rules(self) -> None:
        """Load conflict rules from rules.json configuration file."""
        try:
            # Get path to rules.json (same directory as this file)
            config_dir = Path(__file__).parent
            rules_file = config_dir / "rules.json"

            if not rules_file.exists():
                logger.error(f"Rules file not found: {rules_file}")
                self._rules = []
                return

            # Load rules using conflict rule engine
            engine = ConflictRuleEngine()
            self._rules = engine.load_rules_from_json(str(rules_file))
            logger.info(f"Loaded {len(self._rules)} architecture conflict rules")

            # Validate rules
            errors = engine.validate_rules(self._rules)
            if errors:
                logger.warning(f"Rule validation errors: {errors}")

        except Exception as e:
            logger.error(f"Failed to load architecture rules: {e}")
            self._rules = []

    def _load_analyzers(self) -> None:
        """Load quality analyzers from analyzers.json configuration file."""
        try:
            # Get path to analyzers.json (same directory as this file)
            config_dir = Path(__file__).parent
            analyzers_file = config_dir / "analyzers.json"

            if not analyzers_file.exists():
                logger.error(f"Analyzers file not found: {analyzers_file}")
                self._analyzers = []
                return

            # Load analyzers using quality analyzer engine
            engine = QualityAnalyzerEngine()
            self._analyzers = engine.load_analyzers_from_json(str(analyzers_file))
            logger.info(f"Loaded {len(self._analyzers)} architecture quality analyzers")

            # Validate analyzers
            errors = engine.validate_analyzers(self._analyzers)
            if errors:
                logger.warning(f"Analyzer validation errors: {errors}")

        except Exception as e:
            logger.error(f"Failed to load architecture analyzers: {e}")
            self._analyzers = []

    def get_categories(self) -> List[str]:
        """Return specification categories for architecture."""
        return [
            "Architectural Style",
            "Scalability",
            "Reliability",
            "Communication",
            "Data Management",
            "Security",
            "Deployment",
        ]

    def get_questions(self) -> List[Question]:
        """Return architecture questions from configuration."""
        if self._questions is None:
            self._load_questions()
        return self._questions if self._questions is not None else []

    def get_export_formats(self) -> List[ExportFormat]:
        """Return supported code generation formats from configuration."""
        if self._exporters is None:
            self._load_exporters()
        return self._exporters if self._exporters is not None else []

    def get_conflict_rules(self) -> List[ConflictRule]:
        """Return conflict detection rules from configuration."""
        if self._rules is None:
            self._load_rules()
        return self._rules if self._rules is not None else []

    def get_quality_analyzers(self) -> List[str]:
        """Return quality analyzer IDs enabled for architecture domain from configuration."""
        if self._analyzers is None:
            self._load_analyzers()
        # Return analyzer IDs from loaded configuration
        if self._analyzers:
            return [a.analyzer_id for a in self._analyzers if a.enabled]
        return []

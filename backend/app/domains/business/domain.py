"""Business domain for Socrates2.

Covers business strategy, market analysis, financial planning,
go-to-market strategy, and organizational structure.
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


class BusinessDomain(BaseDomain):
    """Business strategy and planning domain."""

    domain_id = "business"
    name = "Business Strategy"
    version = "1.0.0"
    description = (
        "Business planning, market analysis, financial modeling, "
        "GTM strategy, and organizational structure"
    )

    def __init__(self):
        """Initialize Business domain and load all configuration from files."""
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
            config_dir = Path(__file__).parent
            questions_file = config_dir / "questions.json"

            if not questions_file.exists():
                logger.error(f"Questions file not found: {questions_file}")
                self._questions = []
                return

            engine = QuestionTemplateEngine()
            self._questions = engine.load_questions_from_json(str(questions_file))
            logger.info(f"Loaded {len(self._questions)} business questions")

        except Exception as e:
            logger.error(f"Failed to load business questions: {e}")
            self._questions = []

    def _load_exporters(self) -> None:
        """Load exporters from exporters.json configuration file."""
        try:
            config_dir = Path(__file__).parent
            exporters_file = config_dir / "exporters.json"

            if not exporters_file.exists():
                logger.error(f"Exporters file not found: {exporters_file}")
                self._exporters = []
                return

            engine = ExportTemplateEngine()
            self._exporters = engine.load_exporters_from_json(str(exporters_file))
            logger.info(f"Loaded {len(self._exporters)} business exporters")

        except Exception as e:
            logger.error(f"Failed to load business exporters: {e}")
            self._exporters = []

    def _load_rules(self) -> None:
        """Load rules from rules.json configuration file."""
        try:
            config_dir = Path(__file__).parent
            rules_file = config_dir / "rules.json"

            if not rules_file.exists():
                logger.error(f"Rules file not found: {rules_file}")
                self._rules = []
                return

            engine = ConflictRuleEngine()
            self._rules = engine.load_rules_from_json(str(rules_file))
            logger.info(f"Loaded {len(self._rules)} business rules")

        except Exception as e:
            logger.error(f"Failed to load business rules: {e}")
            self._rules = []

    def _load_analyzers(self) -> None:
        """Load analyzers from analyzers.json configuration file."""
        try:
            config_dir = Path(__file__).parent
            analyzers_file = config_dir / "analyzers.json"

            if not analyzers_file.exists():
                logger.error(f"Analyzers file not found: {analyzers_file}")
                self._analyzers = []
                return

            engine = QualityAnalyzerEngine()
            self._analyzers = engine.load_analyzers_from_json(str(analyzers_file))
            logger.info(f"Loaded {len(self._analyzers)} business analyzers")

        except Exception as e:
            logger.error(f"Failed to load business analyzers: {e}")
            self._analyzers = []

    def get_questions(self) -> List[Question]:
        """Get all questions for this domain."""
        return self._questions or []

    def get_export_formats(self) -> List[ExportFormat]:
        """Get all export formats for this domain."""
        return self._exporters or []

    def get_conflict_rules(self) -> List[ConflictRule]:
        """Get all conflict rules for this domain."""
        return self._rules or []

    def get_quality_analyzers(self) -> List[QualityAnalyzer]:
        """Get quality analyzers for this domain."""
        return self._analyzers or []

    def get_categories(self) -> List[str]:
        """Get all question categories in this domain."""
        categories = set()
        for q in self.get_questions():
            if hasattr(q, "category"):
                categories.add(q.category)
        return sorted(list(categories))

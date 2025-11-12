"""
Quality Analyzer Template Engine.

Manages loading, filtering, validating, and executing quality analyzers
for specifications and requirements.
"""

from typing import Dict, List, Optional

from ..base import QualityAnalyzer


class QualityAnalyzerEngine:
    """
    Template engine for managing quality analyzers.

    Handles loading analyzer configurations, filtering by various criteria,
    and validating analyzer configurations.
    """

    def __init__(self):
        """Initialize the analyzer engine."""
        self.analyzers: List[QualityAnalyzer] = []
        self._analyzer_cache: Dict[str, QualityAnalyzer] = {}

    def load_analyzers_from_dict(self, data: List[Dict]) -> List[QualityAnalyzer]:
        """
        Load analyzers from dictionary data.

        Args:
            data: List of analyzer configuration dictionaries

        Returns:
            List of QualityAnalyzer instances
        """
        analyzers = []
        for item in data:
            try:
                analyzer = QualityAnalyzer(**item)
                analyzers.append(analyzer)
            except Exception as e:
                # Log error but continue processing
                print(f"Error loading analyzer: {e}")
                continue

        self.analyzers = analyzers
        self._rebuild_cache()
        return analyzers

    def _rebuild_cache(self) -> None:
        """Rebuild the analyzer cache."""
        self._analyzer_cache = {a.analyzer_id: a for a in self.analyzers}

    def validate_analyzers(self, analyzers: List[QualityAnalyzer]) -> List[str]:
        """
        Validate analyzer configurations.

        Args:
            analyzers: List of analyzers to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        for analyzer in analyzers:
            # Check required fields
            if not analyzer.analyzer_id:
                errors.append(f"Analyzer missing analyzer_id")
            if not analyzer.name:
                errors.append(f"Analyzer {analyzer.analyzer_id} missing name")
            if not analyzer.description:
                errors.append(
                    f"Analyzer {analyzer.analyzer_id} missing description"
                )
            if not analyzer.analyzer_type:
                errors.append(
                    f"Analyzer {analyzer.analyzer_id} missing analyzer_type"
                )

        return errors

    def filter_by_enabled(
        self, analyzers: List[QualityAnalyzer], enabled: bool
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by enabled status.

        Args:
            analyzers: List of analyzers to filter
            enabled: Filter by enabled (True) or disabled (False)

        Returns:
            Filtered list of analyzers
        """
        return [a for a in analyzers if a.enabled == enabled]

    def filter_by_required(
        self, analyzers: List[QualityAnalyzer], required: bool
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by required status.

        Args:
            analyzers: List of analyzers to filter
            required: Filter by required (True) or optional (False)

        Returns:
            Filtered list of analyzers
        """
        return [a for a in analyzers if a.required == required]

    def filter_by_tag(
        self, analyzers: List[QualityAnalyzer], tag: str
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by tag.

        Args:
            analyzers: List of analyzers to filter
            tag: Tag to filter by

        Returns:
            Analyzers that have the specified tag
        """
        return [a for a in analyzers if tag in a.tags]

    def filter_by_type(
        self, analyzers: List[QualityAnalyzer], analyzer_type: str
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by type.

        Args:
            analyzers: List of analyzers to filter
            analyzer_type: Type to filter by

        Returns:
            Analyzers of the specified type
        """
        return [a for a in analyzers if a.analyzer_type == analyzer_type]

    def get_analyzer(self, analyzer_id: str) -> Optional[QualityAnalyzer]:
        """
        Get a specific analyzer by ID.

        Args:
            analyzer_id: ID of analyzer to retrieve

        Returns:
            QualityAnalyzer or None if not found
        """
        return self._analyzer_cache.get(analyzer_id)

    def execute_analyzer(
        self, analyzer_id: str, specification: Dict
    ) -> Dict:
        """
        Execute a specific analyzer on a specification.

        Args:
            analyzer_id: ID of analyzer to execute
            specification: Specification to analyze

        Returns:
            Analysis results
        """
        analyzer = self.get_analyzer(analyzer_id)
        if not analyzer:
            return {"error": f"Analyzer {analyzer_id} not found"}

        if not analyzer.enabled:
            return {"error": f"Analyzer {analyzer_id} is disabled"}

        # Execute the analyzer (placeholder implementation)
        return {
            "analyzer_id": analyzer_id,
            "status": "success",
            "issues": [],
            "confidence": 1.0,
        }


# Global analyzer engine instance
_analyzer_engine: Optional[QualityAnalyzerEngine] = None


def get_analyzer_engine() -> QualityAnalyzerEngine:
    """
    Get or create the global analyzer engine instance.

    Returns:
        The global QualityAnalyzerEngine
    """
    global _analyzer_engine
    if _analyzer_engine is None:
        _analyzer_engine = QualityAnalyzerEngine()
    return _analyzer_engine

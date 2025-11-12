"""
Quality analyzer template and management system for domains.

Handles loading, validating, and serving domain-specific quality analyzers
from configuration files (JSON, etc).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.base import QualityAnalyzer

logger = logging.getLogger(__name__)


class QualityAnalyzerEngine:
    """
    Engine for managing domain quality analyzers.

    Loads analyzers from configuration files and provides filtering,
    validation, and analyzer management capabilities.

    Usage:
        engine = QualityAnalyzerEngine()
        analyzers = engine.load_analyzers("domains/programming/analyzers.json")
        enabled = engine.filter_by_enabled(analyzers, True)
    """

    def __init__(self):
        """Initialize the quality analyzer engine."""
        self.analyzers_cache: Dict[str, List[QualityAnalyzer]] = {}

    def load_analyzers_from_dict(self, data: List[Dict[str, Any]]) -> List[QualityAnalyzer]:
        """
        Load quality analyzers from a list of dictionaries.

        Args:
            data: List of analyzer dictionaries

        Returns:
            List of QualityAnalyzer objects

        Example:
            data = [
                {
                    "analyzer_id": "bias_detector",
                    "name": "Bias Detector",
                    "description": "Detects potential bias in specifications",
                    "analyzer_type": "bias_detector",
                    "enabled": true,
                    "required": false,
                    "tags": ["universal"]
                },
                ...
            ]
            analyzers = engine.load_analyzers_from_dict(data)
        """
        analyzers = []

        for item in data:
            try:
                analyzer = QualityAnalyzer(
                    analyzer_id=item.get("analyzer_id"),
                    name=item.get("name"),
                    description=item.get("description"),
                    analyzer_type=item.get("analyzer_type"),
                    enabled=item.get("enabled", True),
                    required=item.get("required", False),
                    tags=item.get("tags", []),
                )
                analyzers.append(analyzer)
                logger.debug(f"Loaded analyzer: {analyzer.analyzer_id}")
            except (KeyError, ValueError) as e:
                logger.error(f"Error loading analyzer {item.get('analyzer_id', '?')}: {e}")
                raise ValueError(f"Invalid analyzer configuration: {e}")

        return analyzers

    def load_analyzers_from_json(self, json_file: str) -> List[QualityAnalyzer]:
        """
        Load quality analyzers from a JSON file.

        Args:
            json_file: Path to JSON file

        Returns:
            List of QualityAnalyzer objects
        """
        path = Path(json_file)
        if not path.exists():
            raise FileNotFoundError(f"Analyzers file not found: {json_file}")

        with open(path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Analyzers file must contain a JSON array")

        return self.load_analyzers_from_dict(data)

    def filter_by_enabled(
        self, analyzers: List[QualityAnalyzer], enabled: bool = True
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by enabled status.

        Args:
            analyzers: List of analyzers
            enabled: Whether to get enabled or disabled analyzers

        Returns:
            Filtered analyzers
        """
        return [a for a in analyzers if a.enabled == enabled]

    def filter_by_required(
        self, analyzers: List[QualityAnalyzer], required: bool = True
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by required status.

        Args:
            analyzers: List of analyzers
            required: Whether to get required or optional analyzers

        Returns:
            Filtered analyzers
        """
        return [a for a in analyzers if a.required == required]

    def filter_by_tag(self, analyzers: List[QualityAnalyzer], tag: str) -> List[QualityAnalyzer]:
        """
        Filter analyzers by tag.

        Args:
            analyzers: List of analyzers
            tag: Tag to filter by

        Returns:
            Filtered analyzers

        Tags:
        - universal: Applicable to all domains
        - programming: Specific to programming domain
        - security: Checks security aspects
        - performance: Checks performance aspects
        - accessibility: Checks accessibility aspects
        - compliance: Checks compliance with standards
        """
        return [a for a in analyzers if tag in a.tags]

    def filter_by_type(
        self, analyzers: List[QualityAnalyzer], analyzer_type: str
    ) -> List[QualityAnalyzer]:
        """
        Filter analyzers by analyzer type.

        Args:
            analyzers: List of analyzers
            analyzer_type: Type to filter by

        Returns:
            Filtered analyzers
        """
        return [a for a in analyzers if a.analyzer_type == analyzer_type]

    def validate_analyzers(self, analyzers: List[QualityAnalyzer]) -> List[str]:
        """
        Validate a set of analyzers for correctness.

        Checks for:
        - Duplicate analyzer IDs
        - Invalid analyzer types
        - Missing required fields
        - Valid tags

        Args:
            analyzers: List of analyzers to validate

        Returns:
            List of validation error messages (empty if valid)

        Example:
            errors = engine.validate_analyzers(analyzers)
            if errors:
                for error in errors:
                    print(f"Validation error: {error}")
        """
        errors = []

        # Check for duplicate IDs
        analyzer_ids = [a.analyzer_id for a in analyzers]
        duplicates = [id for id in analyzer_ids if analyzer_ids.count(id) > 1]
        if duplicates:
            errors.append(f"Duplicate analyzer IDs: {set(duplicates)}")

        # Check for required fields
        for a in analyzers:
            if not a.analyzer_id:
                errors.append("Analyzer missing analyzer_id")
            if not a.name:
                errors.append(f"Analyzer {a.analyzer_id} missing name")
            if not a.description:
                errors.append(f"Analyzer {a.analyzer_id} missing description")
            if not a.analyzer_type:
                errors.append(f"Analyzer {a.analyzer_id} missing analyzer_type")

        # Check that tags is a list
        for a in analyzers:
            if not isinstance(a.tags, list):
                errors.append(f"Analyzer {a.analyzer_id} tags must be a list")

        return errors

    def get_analyzers_by_tag(
        self, analyzers: List[QualityAnalyzer]
    ) -> Dict[str, List[QualityAnalyzer]]:
        """
        Group analyzers by tag.

        Returns:
            Dictionary mapping tags to analyzers
        """
        tags_map = {}
        for a in analyzers:
            for tag in a.tags:
                if tag not in tags_map:
                    tags_map[tag] = []
                tags_map[tag].append(a)
        return tags_map

    def get_enabled_analyzers(self, analyzers: List[QualityAnalyzer]) -> List[QualityAnalyzer]:
        """Get all enabled analyzers."""
        return self.filter_by_enabled(analyzers, True)

    def get_required_analyzers(self, analyzers: List[QualityAnalyzer]) -> List[QualityAnalyzer]:
        """Get all required analyzers."""
        return self.filter_by_required(analyzers, True)

    def get_optional_analyzers(self, analyzers: List[QualityAnalyzer]) -> List[QualityAnalyzer]:
        """Get all optional analyzers."""
        return self.filter_by_required(analyzers, False)

    def to_dict(self, analyzers: List[QualityAnalyzer]) -> List[Dict[str, Any]]:
        """Convert analyzers to dictionary representation."""
        return [
            {
                "analyzer_id": a.analyzer_id,
                "name": a.name,
                "description": a.description,
                "analyzer_type": a.analyzer_type,
                "enabled": a.enabled,
                "required": a.required,
                "tags": a.tags,
            }
            for a in analyzers
        ]

    def to_json(self, analyzers: List[QualityAnalyzer]) -> str:
        """Convert analyzers to JSON string."""
        return json.dumps(self.to_dict(analyzers), indent=2)

    def save_to_json(self, analyzers: List[QualityAnalyzer], filepath: str) -> None:
        """
        Save analyzers to a JSON file.

        Args:
            analyzers: Analyzers to save
            filepath: Path to save file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.to_json(analyzers))

        logger.info(f"Saved {len(analyzers)} quality analyzers to {filepath}")


# Global quality analyzer engine instance
_global_engine: Optional[QualityAnalyzerEngine] = None


def get_analyzer_engine() -> QualityAnalyzerEngine:
    """Get the global quality analyzer template engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = QualityAnalyzerEngine()
    return _global_engine

"""
Export template and management system for domains.

Handles loading, validating, and serving domain-specific export formats
from configuration files (JSON, etc).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.base import ExportFormat

logger = logging.getLogger(__name__)


class ExportTemplateEngine:
    """
    Engine for managing domain exporters.

    Loads exporters from configuration files and provides filtering,
    validation, and template capabilities.

    Usage:
        engine = ExportTemplateEngine()
        exporters = engine.load_exporters("domains/programming/exporters.json")
        py_exporters = engine.filter_by_format(exporters, "python")
    """

    def __init__(self):
        """Initialize the exporter engine."""
        self.exporters_cache: Dict[str, List[ExportFormat]] = {}

    def load_exporters_from_dict(self, data: List[Dict[str, Any]]) -> List[ExportFormat]:
        """
        Load exporters from a list of dictionaries.

        Args:
            data: List of exporter dictionaries

        Returns:
            List of ExportFormat objects

        Example:
            data = [
                {
                    "format_id": "python",
                    "name": "Python",
                    "description": "Python class/function generation",
                    "file_extension": ".py",
                    "mime_type": "text/x-python",
                    "template_id": "python_class"
                },
                ...
            ]
            exporters = engine.load_exporters_from_dict(data)
        """
        exporters = []

        for item in data:
            try:
                exporter = ExportFormat(
                    format_id=item.get("format_id"),
                    name=item.get("name"),
                    description=item.get("description"),
                    file_extension=item.get("file_extension"),
                    mime_type=item.get("mime_type"),
                    template_id=item.get("template_id"),
                )
                exporters.append(exporter)
                logger.debug(f"Loaded exporter: {exporter.format_id}")
            except (KeyError, ValueError) as e:
                logger.error(f"Error loading exporter {item.get('format_id', '?')}: {e}")
                raise ValueError(f"Invalid exporter configuration: {e}")

        return exporters

    def load_exporters_from_json(self, json_file: str) -> List[ExportFormat]:
        """
        Load exporters from a JSON file.

        Args:
            json_file: Path to JSON file

        Returns:
            List of ExportFormat objects
        """
        path = Path(json_file)
        if not path.exists():
            raise FileNotFoundError(f"Exporters file not found: {json_file}")

        with open(path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Exporters file must contain a JSON array")

        return self.load_exporters_from_dict(data)

    def filter_by_language(
        self, exporters: List[ExportFormat], language: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by language/format name.

        Args:
            exporters: List of exporters
            language: Language name to filter by

        Returns:
            Filtered exporters
        """
        return [e for e in exporters if e.name.lower() == language.lower()]

    def filter_by_extension(
        self, exporters: List[ExportFormat], extension: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by file extension.

        Args:
            exporters: List of exporters
            extension: File extension to filter by

        Returns:
            Filtered exporters
        """
        # Normalize extension (add dot if missing)
        if not extension.startswith("."):
            extension = "." + extension
        return [e for e in exporters if e.file_extension == extension]

    def filter_by_mime_type(
        self, exporters: List[ExportFormat], mime_type: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by MIME type.

        Args:
            exporters: List of exporters
            mime_type: MIME type to filter by

        Returns:
            Filtered exporters
        """
        return [e for e in exporters if e.mime_type == mime_type]

    def filter_by_category(
        self, exporters: List[ExportFormat], category: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by category (grouped by language family).

        Args:
            exporters: List of exporters
            category: Category to filter by (e.g., "compiled", "scripted", "functional")

        Returns:
            Filtered exporters

        Categories:
        - compiled: Java, Go, Rust, C#, Kotlin
        - scripted: Python, JavaScript
        - typed: TypeScript
        - static: Go, Rust, TypeScript, Java, C#, Kotlin
        - dynamic: Python, JavaScript
        """
        categories = {
            "compiled": ["java", "go", "rust", "csharp", "kotlin"],
            "scripted": ["python", "javascript"],
            "typed": ["typescript", "csharp", "kotlin", "java", "rust", "go"],
            "dynamic": ["python", "javascript"],
            "static": ["java", "go", "rust", "csharp", "kotlin", "typescript"],
            "web": ["javascript", "typescript"],
            "systems": ["rust", "go", "csharp"],
            "jvm": ["java", "kotlin"],
        }

        if category not in categories:
            return []

        format_ids = categories[category]
        return [e for e in exporters if e.format_id in format_ids]

    def validate_exporters(self, exporters: List[ExportFormat]) -> List[str]:
        """
        Validate a set of exporters for correctness.

        Checks for:
        - Duplicate format IDs
        - Duplicate template IDs
        - Invalid file extensions
        - Invalid MIME types
        - Missing required fields

        Args:
            exporters: List of exporters to validate

        Returns:
            List of validation error messages (empty if valid)

        Example:
            errors = engine.validate_exporters(exporters)
            if errors:
                for error in errors:
                    print(f"Validation error: {error}")
        """
        errors = []

        # Check for duplicate format IDs
        format_ids = [e.format_id for e in exporters]
        duplicates = [id for id in format_ids if format_ids.count(id) > 1]
        if duplicates:
            errors.append(f"Duplicate exporter format IDs: {set(duplicates)}")

        # Check for duplicate template IDs
        template_ids = [e.template_id for e in exporters]
        template_duplicates = [id for id in template_ids if template_ids.count(id) > 1]
        if template_duplicates:
            errors.append(f"Duplicate template IDs: {set(template_duplicates)}")

        # Check for required fields
        for e in exporters:
            if not e.format_id:
                errors.append("Exporter missing format_id")
            if not e.name:
                errors.append(f"Exporter {e.format_id} missing name")
            if not e.description:
                errors.append(f"Exporter {e.format_id} missing description")
            if not e.file_extension:
                errors.append(f"Exporter {e.format_id} missing file_extension")
            if not e.mime_type:
                errors.append(f"Exporter {e.format_id} missing mime_type")
            if not e.template_id:
                errors.append(f"Exporter {e.format_id} missing template_id")

        # Validate file extensions start with dot
        for e in exporters:
            if e.file_extension and not e.file_extension.startswith("."):
                errors.append(
                    f"Exporter {e.format_id} file_extension must start with dot: {e.file_extension}"
                )

        # Validate MIME types follow standard format
        valid_mime_patterns = ["text/", "application/", "image/", "audio/", "video/"]
        for e in exporters:
            if e.mime_type:
                if not any(e.mime_type.startswith(p) for p in valid_mime_patterns):
                    errors.append(f"Exporter {e.format_id} has invalid MIME type: {e.mime_type}")

        return errors

    def get_exporters_by_language_family(
        self, exporters: List[ExportFormat]
    ) -> Dict[str, List[ExportFormat]]:
        """
        Group exporters by language family.

        Returns:
            Dictionary mapping language families to exporters
        """
        families = {}
        for e in exporters:
            family = e.format_id.split("_")[0] if "_" in e.format_id else e.format_id
            if family not in families:
                families[family] = []
            families[family].append(e)
        return families

    def to_dict(self, exporters: List[ExportFormat]) -> List[Dict[str, Any]]:
        """Convert exporters to dictionary representation."""
        return [
            {
                "format_id": e.format_id,
                "name": e.name,
                "description": e.description,
                "file_extension": e.file_extension,
                "mime_type": e.mime_type,
                "template_id": e.template_id,
            }
            for e in exporters
        ]

    def to_json(self, exporters: List[ExportFormat]) -> str:
        """Convert exporters to JSON string."""
        return json.dumps(self.to_dict(exporters), indent=2)

    def save_to_json(self, exporters: List[ExportFormat], filepath: str) -> None:
        """
        Save exporters to a JSON file.

        Args:
            exporters: Exporters to save
            filepath: Path to save file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.to_json(exporters))

        logger.info(f"Saved {len(exporters)} exporters to {filepath}")


# Global exporter engine instance
_global_engine: Optional[ExportTemplateEngine] = None


def get_exporter_engine() -> ExportTemplateEngine:
    """Get the global exporter template engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = ExportTemplateEngine()
    return _global_engine

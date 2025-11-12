"""
Export Template Engine.

Manages loading, filtering, validating, and executing export templates
for generating code and documentation from specifications.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import ExportFormat


class ExportTemplateEngine:
    """
    Template engine for managing export formats.

    Handles loading export configurations, filtering by various criteria,
    and validating export format configurations.
    """

    def __init__(self):
        """Initialize the export engine."""
        self.exporters: List[ExportFormat] = []
        self._exporter_cache: Dict[str, ExportFormat] = {}

    def load_exporters_from_dict(self, data: List[Dict]) -> List[ExportFormat]:
        """
        Load exporters from dictionary data.

        Args:
            data: List of exporter configuration dictionaries

        Returns:
            List of ExportFormat instances
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
                    is_compiled=item.get("is_compiled", False),
                )
                exporters.append(exporter)
            except Exception as e:
                # Log error but continue processing
                print(f"Error loading exporter: {e}")
                continue

        self.exporters = exporters
        self._rebuild_cache()
        return exporters

    def load_exporters_from_json(self, filepath: str) -> List[ExportFormat]:
        """
        Load exporters from a JSON file.

        Args:
            filepath: Path to the JSON file containing exporter configurations

        Returns:
            List of ExportFormat instances
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Exporters file not found: {filepath}")

        with open(path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Exporters file must contain a JSON array")

        return self.load_exporters_from_dict(data)

    def _rebuild_cache(self) -> None:
        """Rebuild the exporter cache."""
        self._exporter_cache = {e.format_id: e for e in self.exporters}

    def validate_exporters(self, exporters: List[ExportFormat]) -> List[str]:
        """
        Validate exporter configurations.

        Args:
            exporters: List of exporters to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for duplicate format IDs
        format_ids = [e.format_id for e in exporters]
        duplicates = [id for id in format_ids if format_ids.count(id) > 1]
        if duplicates:
            errors.append(f"Duplicate format IDs: {set(duplicates)}")

        # Check for duplicate template IDs
        template_ids = [e.template_id for e in exporters]
        template_duplicates = [id for id in template_ids if template_ids.count(id) > 1]
        if template_duplicates:
            errors.append(f"Duplicate template IDs: {set(template_duplicates)}")

        for exporter in exporters:
            # Check required fields
            if not exporter.format_id:
                errors.append("Exporter missing format_id")
            if not exporter.name:
                errors.append(f"Exporter {exporter.format_id} missing name")
            if not exporter.description:
                errors.append(
                    f"Exporter {exporter.format_id} missing description"
                )
            if not exporter.file_extension:
                errors.append(
                    f"Exporter {exporter.format_id} missing file_extension"
                )
            if not exporter.mime_type:
                errors.append(
                    f"Exporter {exporter.format_id} missing mime_type"
                )
            if not exporter.template_id:
                errors.append(
                    f"Exporter {exporter.format_id} missing template_id"
                )

            # Validate file extensions start with dot
            if exporter.file_extension and not exporter.file_extension.startswith("."):
                errors.append(
                    f"Exporter {exporter.format_id} file_extension must start with dot: {exporter.file_extension}"
                )

            # Validate MIME types follow standard format
            valid_mime_patterns = ["text/", "application/", "image/", "audio/", "video/"]
            if exporter.mime_type:
                if not any(exporter.mime_type.startswith(p) for p in valid_mime_patterns):
                    errors.append(f"Exporter {exporter.format_id} has invalid MIME type: {exporter.mime_type}")

        return errors

    def filter_by_language(
        self, exporters: List[ExportFormat], language: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by language name (case-insensitive).

        Args:
            exporters: List of exporters to filter
            language: Language name to filter by

        Returns:
            Exporters matching the language
        """
        language_lower = language.lower()
        return [e for e in exporters if e.name.lower() == language_lower]

    def filter_by_extension(
        self, exporters: List[ExportFormat], extension: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by file extension.

        Handles extensions with or without leading dot.

        Args:
            exporters: List of exporters to filter
            extension: File extension to filter by (e.g., '.py' or 'py')

        Returns:
            Exporters with the specified extension
        """
        # Normalize extension to include dot
        if not extension.startswith("."):
            extension = f".{extension}"

        return [e for e in exporters if e.file_extension == extension]

    def filter_by_mime_type(
        self, exporters: List[ExportFormat], mime_type: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by MIME type.

        Args:
            exporters: List of exporters to filter
            mime_type: MIME type to filter by

        Returns:
            Exporters with the specified MIME type
        """
        return [e for e in exporters if e.mime_type == mime_type]

    def filter_by_category(
        self, exporters: List[ExportFormat], category: str
    ) -> List[ExportFormat]:
        """
        Filter exporters by language family category.

        Args:
            exporters: List of exporters to filter
            category: Category to filter by (compiled, scripted, static, dynamic, etc.)

        Returns:
            Exporters in the specified category

        Categories:
        - compiled: Java, Go, Rust, C#, Kotlin
        - scripted: Python, JavaScript
        - typed: TypeScript, Java, Go, Rust, C#, Kotlin
        - static: Go, Rust, TypeScript, Java, C#, Kotlin
        - dynamic: Python, JavaScript
        - web: JavaScript, TypeScript
        - systems: Rust, Go, C#
        - jvm: Java, Kotlin
        """
        categories = {
            "compiled": ["java", "go", "rust", "csharp", "kotlin"],
            "scripted": ["python", "javascript"],
            "typed": ["typescript", "csharp", "kotlin", "java", "rust", "go"],
            "static": ["java", "go", "rust", "csharp", "kotlin", "typescript"],
            "dynamic": ["python", "javascript"],
            "web": ["javascript", "typescript"],
            "systems": ["rust", "go", "csharp"],
            "jvm": ["java", "kotlin"],
        }

        if category not in categories:
            return []

        format_ids = categories[category]
        return [e for e in exporters if e.format_id in format_ids]

    def get_exporter(self, format_id: str) -> Optional[ExportFormat]:
        """
        Get a specific exporter by format ID.

        Args:
            format_id: ID of exporter to retrieve

        Returns:
            ExportFormat or None if not found
        """
        return self._exporter_cache.get(format_id)

    def get_by_template_id(self, template_id: str) -> Optional[ExportFormat]:
        """
        Get exporter by template ID.

        Args:
            template_id: Template ID to search for

        Returns:
            ExportFormat or None if not found
        """
        for exporter in self.exporters:
            if exporter.template_id == template_id:
                return exporter
        return None

    def get_exporters_by_language_family(
        self, exporters: List[ExportFormat]
    ) -> Dict[str, List[ExportFormat]]:
        """
        Group exporters by language family.

        Args:
            exporters: List of exporters to group

        Returns:
            Dictionary mapping language family names to lists of exporters
        """
        families = {}
        for exporter in exporters:
            # Extract family from format_id (e.g., "python" from "python_class")
            family = exporter.format_id.split("_")[0] if "_" in exporter.format_id else exporter.format_id
            if family not in families:
                families[family] = []
            families[family].append(exporter)
        return families

    def export_specification(
        self, format_id: str, specification: Dict
    ) -> Dict:
        """
        Export a specification in the specified format.

        Args:
            format_id: Format to export to
            specification: Specification to export

        Returns:
            Export results
        """
        exporter = self.get_exporter(format_id)
        if not exporter:
            return {"error": f"Exporter {format_id} not found"}

        # Execute the export (placeholder implementation)
        return {
            "format_id": format_id,
            "status": "success",
            "file_extension": exporter.file_extension,
            "mime_type": exporter.mime_type,
            "content": "",  # Would contain actual exported content
        }

    def to_dict(self, exporters: List[ExportFormat]) -> List[Dict[str, Any]]:
        """
        Convert exporters to dictionary representation.

        Args:
            exporters: List of exporters to convert

        Returns:
            List of dictionaries representing exporters
        """
        return [exporter.to_dict() for exporter in exporters]

    def to_json(self, exporters: List[ExportFormat]) -> str:
        """
        Convert exporters to JSON string.

        Args:
            exporters: List of exporters to convert

        Returns:
            JSON string representation of exporters
        """
        return json.dumps(self.to_dict(exporters), indent=2)

    def save_to_json(self, exporters: List[ExportFormat], filepath: str) -> None:
        """
        Save exporters to a JSON file.

        Args:
            exporters: List of exporters to save
            filepath: Path to save the JSON file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.to_json(exporters))


# Global exporter engine instance
_exporter_engine: Optional[ExportTemplateEngine] = None


def get_exporter_engine() -> ExportTemplateEngine:
    """
    Get or create the global exporter engine instance.

    Returns:
        The global ExportTemplateEngine
    """
    global _exporter_engine
    if _exporter_engine is None:
        _exporter_engine = ExportTemplateEngine()
    return _exporter_engine

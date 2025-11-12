"""
Export Template Engine.

Manages loading, filtering, validating, and executing export templates
for generating code and documentation from specifications.
"""

from typing import Dict, List, Optional

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
                exporter = ExportFormat(**item)
                exporters.append(exporter)
            except Exception as e:
                # Log error but continue processing
                print(f"Error loading exporter: {e}")
                continue

        self.exporters = exporters
        self._rebuild_cache()
        return exporters

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
        self, exporters: List[ExportFormat], compiled: bool
    ) -> List[ExportFormat]:
        """
        Filter exporters by compiled language category.

        Args:
            exporters: List of exporters to filter
            compiled: True for compiled languages, False for interpreted

        Returns:
            Exporters in the specified category
        """
        return [e for e in exporters if e.is_compiled == compiled]

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

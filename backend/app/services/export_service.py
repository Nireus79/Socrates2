"""Export service for specifications in multiple formats.

Supports JSON, CSV, Markdown, and YAML export formats.
"""
import csv
import json
import logging
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExportService:
    """Export specifications in multiple formats."""

    @staticmethod
    def to_json(
        project_name: str,
        project_id: str,
        specifications: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """Export specifications as JSON.

        Args:
            project_name: Project name
            project_id: Project ID
            specifications: List of specification dictionaries
            include_metadata: Include project metadata

        Returns:
            JSON string

        Example:
            >>> json_str = ExportService.to_json(
            ...     "My Project",
            ...     "proj_123",
            ...     [{"key": "api_limit", "value": "1000 req/min"}]
            ... )
        """
        data = {
            "specifications": specifications
        }

        if include_metadata:
            data = {
                "project": {
                    "name": project_name,
                    "id": project_id,
                    "exported_at": datetime.now(timezone.utc).isoformat()
                },
                **data
            }

        return json.dumps(data, indent=2)

    @staticmethod
    def to_csv(
        specifications: List[Dict[str, Any]],
        fieldnames: Optional[List[str]] = None
    ) -> str:
        """Export specifications as CSV.

        Args:
            specifications: List of specification dictionaries
            fieldnames: CSV column names (auto-detect if not provided)

        Returns:
            CSV string

        Example:
            >>> csv_str = ExportService.to_csv(
            ...     [
            ...         {"key": "api_limit", "value": "1000 req/min", "priority": "high"},
            ...         {"key": "auth", "value": "OAuth 2.0", "priority": "critical"}
            ...     ]
            ... )
        """
        if not specifications:
            return ""

        # Auto-detect fieldnames from first spec if not provided
        if not fieldnames:
            fieldnames = list(specifications[0].keys())

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for spec in specifications:
            # Ensure all fields exist
            row = {field: spec.get(field, "") for field in fieldnames}
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def to_markdown(
        project_name: str,
        specifications: List[Dict[str, Any]],
        group_by_category: bool = True
    ) -> str:
        """Export specifications as Markdown.

        Args:
            project_name: Project name
            specifications: List of specification dictionaries
            group_by_category: Group specs by category if True

        Returns:
            Markdown string

        Example:
            >>> md_str = ExportService.to_markdown(
            ...     "My Project",
            ...     [
            ...         {"key": "api_limit", "value": "1000 req/min", "category": "API"},
            ...         {"key": "auth", "value": "OAuth 2.0", "category": "Security"}
            ...     ]
            ... )
        """
        lines = [
            f"# {project_name}",
            "",
            f"**Exported:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Specifications",
            ""
        ]

        if group_by_category:
            # Group by category
            categories: Dict[str, List[Dict[str, Any]]] = {}
            for spec in specifications:
                category = spec.get("category", "Other")
                if category not in categories:
                    categories[category] = []
                categories[category].append(spec)

            for category in sorted(categories.keys()):
                lines.append(f"### {category}")
                lines.append("")

                for spec in categories[category]:
                    lines.append(ExportService._spec_to_md_item(spec))

                lines.append("")
        else:
            # No grouping
            for spec in specifications:
                lines.append(ExportService._spec_to_md_item(spec))
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _spec_to_md_item(spec: Dict[str, Any]) -> str:
        """Convert a specification to Markdown list item.

        Args:
            spec: Specification dictionary

        Returns:
            Markdown formatted item
        """
        key = spec.get("key", "Unknown")
        value = spec.get("value", "")
        priority = spec.get("priority", "").upper()
        description = spec.get("description", "")

        lines = [f"**{key}**: {value}"]

        if priority:
            lines.append(f"  - Priority: `{priority}`")

        if description:
            lines.append(f"  - Description: {description}")

        return "- " + "\n  ".join(lines)

    @staticmethod
    def to_yaml(
        project_name: str,
        project_id: str,
        specifications: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """Export specifications as YAML.

        Args:
            project_name: Project name
            project_id: Project ID
            specifications: List of specification dictionaries
            include_metadata: Include project metadata

        Returns:
            YAML string

        Example:
            >>> yaml_str = ExportService.to_yaml(
            ...     "My Project",
            ...     "proj_123",
            ...     [{"key": "api_limit", "value": "1000 req/min"}]
            ... )
        """
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed - using JSON fallback")
            return ExportService.to_json(
                project_name, project_id, specifications, include_metadata
            )

        data = {"specifications": specifications}

        if include_metadata:
            data = {
                "project": {
                    "name": project_name,
                    "id": project_id,
                    "exported_at": datetime.now(timezone.utc).isoformat()
                },
                **data
            }

        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @staticmethod
    def to_html(
        project_name: str,
        specifications: List[Dict[str, Any]],
        include_styles: bool = True
    ) -> str:
        """Export specifications as HTML.

        Args:
            project_name: Project name
            specifications: List of specification dictionaries
            include_styles: Include CSS styles

        Returns:
            HTML string

        Example:
            >>> html_str = ExportService.to_html(
            ...     "My Project",
            ...     [{"key": "api_limit", "value": "1000 req/min", "priority": "high"}]
            ... )
        """
        # Build specification rows
        spec_rows = ""
        for spec in specifications:
            priority = spec.get("priority", "medium").upper()
            priority_color = {
                "CRITICAL": "#d9534f",
                "HIGH": "#f0ad4e",
                "MEDIUM": "#5bc0de",
                "LOW": "#5cb85c"
            }.get(priority, "#5bc0de")

            spec_rows += f"""
            <tr>
                <td><strong>{spec.get('key', 'Unknown')}</strong></td>
                <td>{spec.get('value', '')}</td>
                <td><span style="background-color: {priority_color}; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">{priority}</span></td>
                <td>{spec.get('description', '')}</td>
            </tr>
            """

        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Specifications</title>"""

        if include_styles:
            html += """
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #5cb85c;
            padding-bottom: 10px;
        }
        .metadata {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 12px;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background-color: #2c3e50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f9f9f9;
        }
    </style>"""

        html += f"""
</head>
<body>
    <h1>{project_name}</h1>
    <div class="metadata">
        <p><strong>Exported:</strong> {datetime.now(timezone.utc).isoformat()}</p>
        <p><strong>Total Specifications:</strong> {len(specifications)}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Key</th>
                <th>Value</th>
                <th>Priority</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            {spec_rows}
        </tbody>
    </table>
</body>
</html>
"""

        return html

    @staticmethod
    def export(
        format: str,
        project_name: str,
        project_id: str,
        specifications: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Export specifications in specified format.

        Args:
            format: Export format (json, csv, markdown, yaml, html)
            project_name: Project name
            project_id: Project ID
            specifications: List of specification dictionaries
            **kwargs: Format-specific options

        Returns:
            Formatted export string

        Raises:
            ValueError: If format is not supported

        Example:
            >>> content = ExportService.export(
            ...     "json",
            ...     "My Project",
            ...     "proj_123",
            ...     [{"key": "api_limit", "value": "1000 req/min"}]
            ... )
        """
        format_lower = format.lower()

        if format_lower == "json":
            return ExportService.to_json(
                project_name, project_id, specifications,
                kwargs.get("include_metadata", True)
            )
        elif format_lower == "csv":
            return ExportService.to_csv(
                specifications,
                kwargs.get("fieldnames")
            )
        elif format_lower in ["markdown", "md"]:
            return ExportService.to_markdown(
                project_name, specifications,
                kwargs.get("group_by_category", True)
            )
        elif format_lower == "yaml":
            return ExportService.to_yaml(
                project_name, project_id, specifications,
                kwargs.get("include_metadata", True)
            )
        elif format_lower == "html":
            return ExportService.to_html(
                project_name, specifications,
                kwargs.get("include_styles", True)
            )
        else:
            raise ValueError(
                f"Unsupported export format: {format}. "
                f"Supported formats: json, csv, markdown, yaml, html"
            )

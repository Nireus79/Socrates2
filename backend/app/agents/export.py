"""
ExportAgent - Export project specifications and code to various formats.
"""
import base64
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..core.dependencies import ServiceContainer
from ..models.generated_file import GeneratedFile
from ..models.generated_project import GeneratedProject
from ..models.project import Project
from ..models.specification import Specification
from .base import BaseAgent


class ExportAgent(BaseAgent):
    """
    ExportAgent - Export project data to various formats.

    Capabilities:
    - export_markdown: Export specifications as Markdown
    - export_pdf: Export specifications as PDF (placeholder)
    - export_json: Export complete project data as JSON
    - export_code: Export generated code files (placeholder)
    """

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        """Initialize ExportAgent"""
        super().__init__(agent_id, name, services)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'export_markdown',
            'export_pdf',
            'export_json',
            'export_code'
        ]

    def _export_markdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export project specifications as Markdown.

        Args:
            data: {'project_id': UUID}

        Returns:
            {'success': bool, 'content': str, 'filename': str}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get specs database
        db_specs = self.services.get_database_specs()

        # Load project
        project = db_specs.query(Project).filter_by(id=project_id).first()
        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'NOT_FOUND'
            }

        # Load specifications
        specs = db_specs.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Generate Markdown
        markdown = f"""# {project.name}

**Description:** {project.description or 'No description'}
**Current Phase:** {project.current_phase}
**Maturity Score:** {project.maturity_score}%
**Status:** {project.status}

---

## Specifications

"""

        # Group by category
        specs_by_category = {}
        for spec in specs:
            if spec.category not in specs_by_category:
                specs_by_category[spec.category] = []
            specs_by_category[spec.category].append(spec)

        # Format each category
        if specs_by_category:
            for category, category_specs in sorted(specs_by_category.items()):
                markdown += f"### {category.replace('_', ' ').title()}\n\n"
                for spec in category_specs:
                    confidence = f" (confidence: {spec.confidence:.0%})" if spec.confidence else ""
                    markdown += f"- **{spec.key}:** {spec.value}{confidence}\n"
                markdown += "\n"
        else:
            markdown += "*No specifications extracted yet.*\n\n"

        markdown += f"""---

**Created:** {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**Last Updated:** {project.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

        filename = f"{project.name.replace(' ', '_').lower()}_specs.md"

        self.logger.info(f"Exported project {project_id} to Markdown ({len(specs)} specs)")

        return {
            'success': True,
            'content': markdown,
            'filename': filename
        }

    def _export_pdf(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export as PDF (placeholder implementation).

        Args:
            data: {'project_id': UUID}

        Returns:
            {'success': bool, 'message': str}
        """
        # First generate Markdown
        markdown_result = self._export_markdown(data)

        if not markdown_result.get('success'):
            return markdown_result

        # TODO: Convert Markdown to PDF using markdown2pdf or similar
        # For now, return success with placeholder message

        return {
            'success': True,
            'message': 'PDF export not yet implemented. Use Markdown export instead.',
            'markdown_content': markdown_result.get('content'),
            'filename': markdown_result.get('filename', '').replace('.md', '.pdf')
        }

    def _export_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export complete project data as JSON.

        Args:
            data: {'project_id': UUID}

        Returns:
            {'success': bool, 'content': str, 'filename': str}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get specs database
        db_specs = self.services.get_database_specs()

        # Load project
        project = db_specs.query(Project).filter_by(id=project_id).first()
        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'NOT_FOUND'
            }

        # Load specifications
        specs = db_specs.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Build JSON structure
        export_data = {
            'project': project.to_dict(),  # TODO to_dict() Parameter 'self' unfilled
            'specifications': [spec.to_dict() for spec in specs],   # TODO to_dict() Parameter 'self' unfilled
            'export_metadata': {
                'total_specifications': len(specs),
                'categories': list(set(spec.category for spec in specs)),
                'exported_at': datetime.now(timezone.utc).isoformat()
            }
        }

        content = json.dumps(export_data, indent=2)
        filename = f"{project.name.replace(' ', '_').lower()}_export.json"

        self.logger.info(f"Exported project {project_id} to JSON ({len(specs)} specs)")

        return {
            'success': True,
            'content': content,
            'filename': filename
        }

    def _export_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export generated code files as ZIP archive.

        Args:
            data: {'project_id': UUID}

        Returns:
            {'success': bool, 'archive_base64': str, 'filename': str, 'file_count': int}
            OR on failure:
            {'success': False, 'error': str, 'error_code': str}
        """
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        db = None
        try:
            db = self.services.get_database_specs()

            # Load project
            project = db.query(Project).filter_by(id=project_id).first()
            if not project:
                return {
                    'success': False,
                    'error': f'Project not found: {project_id}',
                    'error_code': 'PROJECT_NOT_FOUND'
                }

            # Find latest generation
            generation = db.query(GeneratedProject).filter_by(
                project_id=project_id
            ).order_by(GeneratedProject.generation_version.desc()).first()

            if not generation:
                return {
                    'success': False,
                    'error': 'No generated code found for this project. Generate code first.',
                    'error_code': 'NO_GENERATED_CODE'
                }

            # Load all generated files for this generation
            files = db.query(GeneratedFile).filter_by(
                generation_id=generation.id
            ).all()

            if not files:
                return {
                    'success': False,
                    'error': 'No files found in the latest generation.',
                    'error_code': 'NO_FILES'
                }

            # Create ZIP archive in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    # Use relative path within ZIP
                    arcname = file.file_path.lstrip('/')
                    zip_file.writestr(arcname, file.content)

            # Encode as base64 for transmission
            zip_buffer.seek(0)
            archive_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')

            filename = f"{project.name.replace(' ', '_').lower()}_v{generation.generation_version}.zip"

            self.logger.info(f"Exported {len(files)} files for project {project_id} (generation {generation.generation_version})")

            return {
                'success': True,
                'archive_base64': archive_base64,
                'filename': filename,
                'file_count': len(files),
                'generation_version': generation.generation_version,
                'total_lines': generation.total_lines
            }

        except Exception as e:
            self.logger.error(f"Error exporting code for project {project_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to export code: {str(e)}',
                'error_code': 'EXPORT_ERROR'
            }

        finally:
            if db:
                db.close()

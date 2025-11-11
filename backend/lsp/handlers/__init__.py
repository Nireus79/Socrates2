"""
LSP Request and Notification Handlers

Implements handler classes for LSP protocol methods.
Provides specification-aware IDE features through Language Server Protocol.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from ..api.client import SocratesApiClient, Conflict

logger = logging.getLogger(__name__)


@dataclass
class DocumentState:
    """Track document state for LSP operations"""
    uri: str
    version: int
    text: str
    language_id: str
    project_id: Optional[str] = None
    specification_references: List[str] = None

    def __post_init__(self):
        if self.specification_references is None:
            self.specification_references = []


class InitializationHandler:
    """Handle server initialization"""

    async def initialize(self, params: Dict) -> Dict:
        """Initialize server and return capabilities"""
        logger.info("Initializing Language Server")

        return {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": 1,  # Full document sync
                    "save": {
                        "includeText": True
                    }
                },
                "hoverProvider": True,
                "completionProvider": {
                    "resolveProvider": True,
                    "triggerCharacters": [".", "@", "$"]
                },
                "definitionProvider": True,
                "referencesProvider": True,
                "codeActionProvider": {
                    "codeActionKinds": ["quickfix", "refactor"]
                },
                "documentFormattingProvider": True,
                "documentRangeFormattingProvider": True,
                "diagnosticProvider": {
                    "interFileDependencies": True,
                    "workspaceDiagnostics": False
                },
                "renameProvider": True,
                "documentSymbolProvider": True,
                "workspaceSymbolProvider": True,
                "implementationProvider": True,
                "typeDefinitionProvider": True,
            }
        }


class HoverHandler:
    """Handle hover requests with specification details"""

    def __init__(self, api_client: SocratesApiClient):
        self.api_client = api_client

    async def get_hover(
        self,
        uri: str,
        line: int,
        character: int,
        document_text: str,
        project_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Get hover information for specification reference"""
        try:
            # Extract word at position
            spec_ref = self._extract_specification_reference(document_text, line, character)
            if not spec_ref:
                return None

            # Try to find specification by key
            if project_id:
                specs = await self.api_client.search_specifications(project_id, spec_ref, limit=1)
                if specs:
                    spec = specs[0]
                    return {
                        "contents": {
                            "kind": "markdown",
                            "value": self._format_specification_hover(spec)
                        },
                        "range": {
                            "start": {"line": line, "character": character - len(spec_ref)},
                            "end": {"line": line, "character": character}
                        }
                    }

            return None
        except Exception as e:
            logger.error(f"Failed to get hover information: {e}")
            return None

    def _extract_specification_reference(
        self,
        document_text: str,
        line: int,
        character: int
    ) -> Optional[str]:
        """Extract specification reference at cursor position"""
        lines = document_text.split('\n')
        if line >= len(lines):
            return None

        line_text = lines[line]
        if character > len(line_text):
            return None

        # Match patterns like @spec.key, spec_key, $KEY
        pattern = r'[@$]?[\w.]+'
        match_start = character - 1
        match_end = character

        while match_start >= 0 and re.match(r'[\w.@$]', line_text[match_start]):
            match_start -= 1
        match_start += 1

        while match_end < len(line_text) and re.match(r'[\w.@$]', line_text[match_end]):
            match_end += 1

        if match_start < match_end:
            return line_text[match_start:match_end].lstrip('@$')

        return None

    def _format_specification_hover(self, spec: Any) -> str:
        """Format specification details for hover display"""
        return f"""# {spec.key}

**Category:** {spec.category}

**Value:**
```
{spec.value}
```

**Created:** {spec.created_at}

**Last Updated:** {spec.updated_at}
"""


class CompletionHandler:
    """Handle completion requests with specification-aware suggestions"""

    def __init__(self, api_client: SocratesApiClient):
        self.api_client = api_client

    async def get_completions(
        self,
        uri: str,
        line: int,
        character: int,
        document_text: str,
        project_id: Optional[str] = None,
        max_items: int = 50
    ) -> List[Dict]:
        """Get code completions based on specifications"""
        try:
            if not project_id:
                return []

            # Get word being completed
            word = self._get_word_at_position(document_text, line, character)

            # Fetch matching specifications
            specs = await self.api_client.search_specifications(
                project_id,
                word if word else "",
                limit=max_items
            )

            completions = []
            for spec in specs:
                completions.append({
                    "label": spec.key,
                    "kind": 14,  # Variable completion kind
                    "detail": f"[{spec.category}] {spec.value[:50]}...",
                    "documentation": spec.value,
                    "sortText": spec.key,
                    "filterText": spec.key,
                    "insertText": spec.key,
                    "insertTextFormat": 1  # PlainText
                })

            return completions
        except Exception as e:
            logger.error(f"Failed to get completions: {e}")
            return []

    def _get_word_at_position(self, document_text: str, line: int, character: int) -> str:
        """Extract word being completed"""
        lines = document_text.split('\n')
        if line >= len(lines):
            return ""

        line_text = lines[line]
        if character > len(line_text):
            character = len(line_text)

        start = character - 1
        while start >= 0 and re.match(r'[\w.]', line_text[start]):
            start -= 1
        start += 1

        return line_text[start:character]


class DiagnosticsHandler:
    """Handle diagnostic requests for conflict detection"""

    def __init__(self, api_client: SocratesApiClient):
        self.api_client = api_client

    async def get_diagnostics(self, uri: str, project_id: str) -> List[Dict]:
        """Get diagnostics for document based on conflicts"""
        try:
            conflicts = await self.api_client.get_conflicts(project_id)
            diagnostics = []

            for conflict in conflicts:
                severity = self._map_severity(conflict.severity)
                diagnostics.append({
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 0}
                    },
                    "severity": severity,
                    "source": "Socrates2",
                    "message": conflict.message,
                    "code": conflict.id,
                    "tags": [1] if conflict.type == "deprecated" else []  # DiagnosticTag.Unnecessary
                })

            return diagnostics
        except Exception as e:
            logger.error(f"Failed to get diagnostics: {e}")
            return []

    def _map_severity(self, severity_str: str) -> int:
        """Map conflict severity to LSP diagnostic severity"""
        severity_map = {
            "low": 4,      # Hint
            "medium": 2,   # Warning
            "high": 1,     # Error
            "critical": 1  # Error
        }
        return severity_map.get(severity_str.lower(), 3)  # Default: Information


class DefinitionHandler:
    """Handle definition requests for specifications"""

    def __init__(self, api_client: SocratesApiClient):
        self.api_client = api_client

    async def get_definition(
        self,
        uri: str,
        line: int,
        character: int,
        document_text: str,
        project_id: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """Get definition location for specification"""
        try:
            if not project_id:
                return None

            # Extract specification reference
            spec_ref = self._extract_spec_reference(document_text, line, character)
            if not spec_ref:
                return None

            # Search for specification
            specs = await self.api_client.search_specifications(project_id, spec_ref, limit=1)
            if not specs:
                return None

            # Return location (in this case, just the specification itself)
            return [
                {
                    "uri": f"socrates2://spec/{specs[0].id}",
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": len(spec_ref)}
                    }
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get definition: {e}")
            return None

    def _extract_spec_reference(self, document_text: str, line: int, character: int) -> Optional[str]:
        """Extract specification reference at position"""
        lines = document_text.split('\n')
        if line >= len(lines):
            return None

        line_text = lines[line]
        pattern = r'[@$]?[\w.]+'
        match_start = character - 1
        while match_start >= 0 and re.match(r'[\w.@$]', line_text[match_start]):
            match_start -= 1
        match_start += 1

        match_end = character
        while match_end < len(line_text) and re.match(r'[\w.@$]', line_text[match_end]):
            match_end += 1

        if match_start < match_end:
            return line_text[match_start:match_end].lstrip('@$')

        return None


class ReferencesHandler:
    """Handle references requests to find specification usage"""

    def __init__(self, api_client: SocratesApiClient):
        self.api_client = api_client

    async def find_references(
        self,
        uri: str,
        line: int,
        character: int,
        document_text: str,
        project_id: Optional[str] = None,
        include_declaration: bool = False
    ) -> List[Dict]:
        """Find all references to specification in project"""
        try:
            if not project_id:
                return []

            # Extract specification reference
            spec_ref = self._extract_spec_reference(document_text, line, character)
            if not spec_ref:
                return []

            # Search for specifications
            specs = await self.api_client.search_specifications(project_id, spec_ref)

            references = []
            for spec in specs:
                if include_declaration or spec.key != spec_ref:
                    references.append({
                        "uri": f"socrates2://spec/{spec.id}",
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": len(spec.key)}
                        }
                    })

            return references
        except Exception as e:
            logger.error(f"Failed to find references: {e}")
            return []

    def _extract_spec_reference(self, document_text: str, line: int, character: int) -> Optional[str]:
        """Extract specification reference at position"""
        lines = document_text.split('\n')
        if line >= len(lines):
            return None

        line_text = lines[line]
        match_start = character - 1
        while match_start >= 0 and re.match(r'[\w.@$]', line_text[match_start]):
            match_start -= 1
        match_start += 1

        match_end = character
        while match_end < len(line_text) and re.match(r'[\w.@$]', line_text[match_end]):
            match_end += 1

        if match_start < match_end:
            return line_text[match_start:match_end].lstrip('@$')

        return None


class CodeActionHandler:
    """Handle code action requests for conflict resolution"""

    def __init__(self, api_client: SocratesApiClient):
        self.api_client = api_client

    async def get_code_actions(
        self,
        uri: str,
        range_: Dict,
        diagnostics: List[Dict],
        document_text: str,
        project_id: Optional[str] = None
    ) -> List[Dict]:
        """Get available code actions for diagnostics"""
        actions = []

        try:
            for diagnostic in diagnostics:
                if diagnostic.get("source") != "Socrates2":
                    continue

                conflict_id = diagnostic.get("code")

                # View conflict details action
                actions.append({
                    "title": "View Conflict Details",
                    "kind": "quickfix",
                    "diagnostics": [diagnostic],
                    "command": {
                        "title": "View Conflict",
                        "command": "socrates.viewConflict",
                        "arguments": [conflict_id]
                    }
                })

                # Resolve conflict action
                actions.append({
                    "title": "Resolve Conflict",
                    "kind": "quickfix",
                    "diagnostics": [diagnostic],
                    "command": {
                        "title": "Resolve",
                        "command": "socrates.resolveConflict",
                        "arguments": [conflict_id]
                    }
                })

                # Generate code action
                if project_id:
                    actions.append({
                        "title": "Generate Code",
                        "kind": "refactor",
                        "diagnostics": [diagnostic],
                        "command": {
                            "title": "Generate",
                            "command": "socrates.generateCode",
                            "arguments": [conflict_id, project_id]
                        }
                    })

            return actions
        except Exception as e:
            logger.error(f"Failed to get code actions: {e}")
            return []


class FormattingHandler:
    """Handle code formatting requests"""

    async def format(self, code: str, language: str) -> str:
        """Format code document for specified language"""
        try:
            # Language-specific formatting
            if language == "python":
                return self._format_python(code)
            elif language in ["javascript", "typescript"]:
                return self._format_javascript(code)
            elif language == "go":
                return self._format_go(code)
            elif language == "java":
                return self._format_java(code)
            else:
                return code
        except Exception as e:
            logger.error(f"Failed to format code: {e}")
            return code

    def _format_python(self, code: str) -> str:
        """Apply Python formatting (simplified Black-like)"""
        lines = code.split('\n')
        formatted = []
        for line in lines:
            formatted.append(line.rstrip())
        return '\n'.join(formatted)

    def _format_javascript(self, code: str) -> str:
        """Apply JavaScript formatting (simplified Prettier-like)"""
        lines = code.split('\n')
        formatted = []
        indent_level = 0
        indent_str = "  "

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('}') or stripped.startswith(']') or stripped.startswith(')'):
                indent_level = max(0, indent_level - 1)

            if stripped:
                formatted.append(indent_str * indent_level + stripped)

            if stripped.endswith('{') or stripped.endswith('[') or stripped.endswith('('):
                indent_level += 1

        return '\n'.join(formatted)

    def _format_go(self, code: str) -> str:
        """Apply Go formatting (simplified gofmt-like)"""
        return code.rstrip()

    def _format_java(self, code: str) -> str:
        """Apply Java formatting (simplified)"""
        lines = code.split('\n')
        formatted = []
        indent_level = 0
        indent_str = "    "

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)

            if stripped:
                formatted.append(indent_str * indent_level + stripped)

            if stripped.endswith('{'):
                indent_level += 1

        return '\n'.join(formatted)

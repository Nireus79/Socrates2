"""
Socrates2 Language Server Protocol (LSP) Server

Implements LSP specification for providing IDE features like:
- Hover documentation
- Code completion
- Conflict diagnostics
- Go to definition
- Find references
- Code actions
- Document formatting

Used by both VS Code Extension (6.1) and JetBrains Plugins (6.2) via standard LSP protocol.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

from .handlers import (
    InitializationHandler,
    HoverHandler,
    CompletionHandler,
    DiagnosticsHandler,
    DefinitionHandler,
    ReferencesHandler,
    CodeActionHandler,
    FormattingHandler
)
from .api.client import SocratesApiClient
from .config import LSPConfig
from .utils.uri_handler import URIHandler


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 Request"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str = ""
    params: Optional[Dict] = None


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[Dict] = None


@dataclass
class JSONRPCNotification:
    """JSON-RPC 2.0 Notification"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict] = None


class SocratesLSPServer:
    """
    Main Language Server Protocol server for Socrates2

    Implements LSP 3.17 specification with support for:
    - Multiple clients (VS Code, JetBrains IDEs)
    - Specification-aware code intelligence
    - Conflict detection and resolution
    - Code generation in multiple languages
    """

    def __init__(self, config: Optional[LSPConfig] = None):
        self.config = config or LSPConfig()
        self.logger = self._setup_logging()
        self.api_client = SocratesApiClient(base_url=self.config.api_url)
        self.uri_handler = URIHandler()

        # Initialize handlers
        self.init_handler = InitializationHandler()
        self.hover_handler = HoverHandler(self.api_client)
        self.completion_handler = CompletionHandler(self.api_client)
        self.diagnostics_handler = DiagnosticsHandler(self.api_client)
        self.definition_handler = DefinitionHandler(self.api_client)
        self.references_handler = ReferencesHandler(self.api_client)
        self.code_action_handler = CodeActionHandler(self.api_client)
        self.formatting_handler = FormattingHandler()

        # State management
        self.client_capabilities = {}
        self.open_documents: Dict[str, DocumentState] = {}
        self.project_context: Optional[ProjectContext] = None

        # Message handlers
        self.request_handlers: Dict[str, Callable] = {
            "initialize": self.handle_initialize,
            "shutdown": self.handle_shutdown,
            "textDocument/hover": self.handle_hover,
            "textDocument/completion": self.handle_completion,
            "textDocument/publishDiagnostics": self.handle_publish_diagnostics,
            "textDocument/definition": self.handle_definition,
            "textDocument/references": self.handle_references,
            "textDocument/codeAction": self.handle_code_action,
            "textDocument/formatting": self.handle_formatting,
            "textDocument/didOpen": self.handle_did_open,
            "textDocument/didChange": self.handle_did_change,
            "textDocument/didClose": self.handle_did_close,
        }

        self.notification_handlers: Dict[str, Callable] = {
            "initialized": self.handle_initialized,
            "exit": self.handle_exit,
        }

    async def start(self):
        """Start the LSP server"""
        self.logger.info("Starting Socrates2 LSP Server")
        self.logger.info(f"API URL: {self.config.api_url}")
        self.logger.info(f"Listen address: {self.config.listen_host}:{self.config.listen_port}")

        # Start server loop
        while True:
            try:
                await self._read_and_process_message()
            except EOFError:
                self.logger.info("Client disconnected")
                break
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")

    async def _read_and_process_message(self):
        """Read JSON-RPC message from stdin and process it"""
        # Read header
        headers = {}
        while True:
            line = input().strip()
            if not line:
                break
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

        # Read body
        content_length = int(headers.get("Content-Length", 0))
        body = input(content_length)
        message = json.loads(body)

        # Process message
        response = await self._process_message(message)

        # Send response if applicable
        if response:
            await self._send_response(response)

    async def _process_message(self, message: Dict) -> Optional[JSONRPCResponse]:
        """Process incoming JSON-RPC message"""
        msg_id = message.get("id")
        method = message.get("method", "")
        params = message.get("params")

        self.logger.debug(f"Received: {method}")

        # Handle request
        if msg_id is not None:
            handler = self.request_handlers.get(method)
            if handler:
                try:
                    result = await handler(params or {})
                    return JSONRPCResponse(
                        id=msg_id,
                        result=result
                    )
                except Exception as e:
                    self.logger.error(f"Error handling {method}: {e}")
                    return JSONRPCResponse(
                        id=msg_id,
                        error={
                            "code": -32603,
                            "message": str(e)
                        }
                    )
            else:
                return JSONRPCResponse(
                    id=msg_id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                )

        # Handle notification
        elif method in self.notification_handlers:
            handler = self.notification_handlers[method]
            try:
                await handler(params or {})
            except Exception as e:
                self.logger.error(f"Error handling notification {method}: {e}")

    async def _send_response(self, response: JSONRPCResponse):
        """Send JSON-RPC response to client"""
        body = json.dumps(asdict(response))
        headers = f"Content-Length: {len(body)}\r\n\r\n"
        print(headers + body, end="", flush=True)

    async def _send_notification(self, method: str, params: Optional[Dict] = None):
        """Send JSON-RPC notification to client"""
        notification = JSONRPCNotification(
            method=method,
            params=params
        )
        body = json.dumps(asdict(notification))
        headers = f"Content-Length: {len(body)}\r\n\r\n"
        print(headers + body, end="", flush=True)

    # ============ Request Handlers ============

    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request"""
        self.client_capabilities = params.get("capabilities", {})

        return {
            "capabilities": {
                "textDocumentSync": 1,  # Full sync
                "hoverProvider": True,
                "completionProvider": {
                    "resolveProvider": True,
                    "triggerCharacters": [".", "@"]
                },
                "definitionProvider": True,
                "referencesProvider": True,
                "codeActionProvider": True,
                "documentFormattingProvider": True,
                "diagnosticProvider": {
                    "interFileDependencies": True,
                    "workspaceDiagnostics": False
                }
            },
            "serverInfo": {
                "name": "Socrates2",
                "version": "0.1.0"
            }
        }

    async def handle_shutdown(self, params: Dict) -> Dict:
        """Handle shutdown request"""
        self.logger.info("Server shutting down")
        return {}

    async def handle_initialized(self, params: Dict):
        """Handle initialized notification"""
        self.logger.info("Client initialized")
        # Could send initial diagnostics here

    async def handle_exit(self, params: Dict):
        """Handle exit notification"""
        self.logger.info("Client exiting")

    # ============ Document Operations ============

    async def handle_did_open(self, params: Dict):
        """Handle textDocument/didOpen notification"""
        uri = params["textDocument"]["uri"]
        content = params["textDocument"]["text"]

        self.open_documents[uri] = DocumentState(
            uri=uri,
            content=content,
            language_id=params["textDocument"]["languageId"]
        )

        # Publish diagnostics for new document
        await self._publish_diagnostics(uri)

    async def handle_did_change(self, params: Dict):
        """Handle textDocument/didChange notification"""
        uri = params["textDocument"]["uri"]

        if uri in self.open_documents:
            # Apply changes
            for change in params.get("contentChanges", []):
                if "range" in change:
                    # Incremental change
                    self.open_documents[uri].content = change["text"]
                else:
                    # Full document change
                    self.open_documents[uri].content = change["text"]

            # Publish updated diagnostics
            await self._publish_diagnostics(uri)

    async def handle_did_close(self, params: Dict):
        """Handle textDocument/didClose notification"""
        uri = params["textDocument"]["uri"]
        if uri in self.open_documents:
            del self.open_documents[uri]

    # ============ Intelligence Handlers ============

    async def handle_hover(self, params: Dict) -> Optional[Dict]:
        """Handle textDocument/hover request"""
        uri = params["textDocument"]["uri"]
        line = params["position"]["line"]
        character = params["position"]["character"]

        return await self.hover_handler.get_hover(uri, line, character)

    async def handle_completion(self, params: Dict) -> Dict:
        """Handle textDocument/completion request"""
        uri = params["textDocument"]["uri"]
        line = params["position"]["line"]
        character = params["position"]["character"]

        completions = await self.completion_handler.get_completions(uri, line, character)
        return {
            "isIncomplete": False,
            "items": completions
        }

    async def handle_definition(self, params: Dict) -> Optional[List[Dict]]:
        """Handle textDocument/definition request"""
        uri = params["textDocument"]["uri"]
        line = params["position"]["line"]
        character = params["position"]["character"]

        return await self.definition_handler.get_definition(uri, line, character)

    async def handle_references(self, params: Dict) -> List[Dict]:
        """Handle textDocument/references request"""
        uri = params["textDocument"]["uri"]
        line = params["position"]["line"]
        character = params["position"]["character"]
        include_declaration = params.get("context", {}).get("includeDeclaration", False)

        return await self.references_handler.find_references(
            uri, line, character, include_declaration
        )

    async def handle_code_action(self, params: Dict) -> List[Dict]:
        """Handle textDocument/codeAction request"""
        uri = params["textDocument"]["uri"]
        range_ = params["range"]
        diagnostics = params.get("context", {}).get("diagnostics", [])

        return await self.code_action_handler.get_code_actions(uri, range_, diagnostics)

    async def handle_formatting(self, params: Dict) -> List[Dict]:
        """Handle textDocument/formatting request"""
        uri = params["textDocument"]["uri"]

        if uri in self.open_documents:
            doc = self.open_documents[uri]
            formatted = await self.formatting_handler.format(doc.content, doc.language_id)

            # Return text edits to transform document
            if formatted != doc.content:
                return [{
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": len(doc.content.splitlines()), "character": 0}
                    },
                    "newText": formatted
                }]

        return []

    async def handle_publish_diagnostics(self, params: Dict):
        """Handle textDocument/publishDiagnostics"""
        uri = params.get("textDocument", {}).get("uri")
        if uri:
            await self._publish_diagnostics(uri)

    # ============ Diagnostic Publishing ============

    async def _publish_diagnostics(self, uri: str):
        """Publish diagnostics (conflicts) for document"""
        if uri not in self.open_documents:
            return

        doc = self.open_documents[uri]
        diagnostics = []

        try:
            # Extract project context from URI
            project_id = self._extract_project_id(uri)
            if not project_id:
                return

            # Get conflicts from API
            conflicts = await self.api_client.get_conflicts(project_id)

            # Convert conflicts to diagnostics
            for conflict in conflicts:
                diagnostic = {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 0}
                    },
                    "severity": self._severity_to_lsp(conflict.get("severity", "medium")),
                    "source": "Socrates2",
                    "message": conflict.get("message", "Specification conflict"),
                    "code": conflict.get("id")
                }
                diagnostics.append(diagnostic)

            # Publish diagnostics
            await self._send_notification("textDocument/publishDiagnostics", {
                "uri": uri,
                "diagnostics": diagnostics
            })

        except Exception as e:
            self.logger.error(f"Error publishing diagnostics: {e}")

    # ============ Helper Methods ============

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging"""
        logger = logging.getLogger("socrates2.lsp")
        handler = logging.FileHandler(self.config.log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, self.config.log_level))
        return logger

    def _extract_project_id(self, uri: str) -> Optional[str]:
        """Extract project ID from document URI"""
        # Would parse workspace root or metadata
        return self.project_context.project_id if self.project_context else None

    def _severity_to_lsp(self, severity: str) -> int:
        """Convert conflict severity to LSP diagnostic severity"""
        severity_map = {
            "error": 1,
            "high": 1,
            "medium": 2,
            "warning": 2,
            "low": 3,
            "info": 3
        }
        return severity_map.get(severity.lower(), 3)


@dataclass
class DocumentState:
    """State of an open document"""
    uri: str
    content: str
    language_id: str
    version: int = 1


@dataclass
class ProjectContext:
    """Current project context"""
    project_id: str
    project_name: str
    loaded_at: datetime


async def main():
    """Main entry point"""
    config = LSPConfig()
    server = SocratesLSPServer(config)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())

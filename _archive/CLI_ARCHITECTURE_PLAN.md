# Socrates CLI - Modular Architecture Refactor Plan

## Problem Statement

**Current Status:**
- Socrates.py: 3000+ lines (single monolithic file)
- 150+ backend API endpoints to expose
- Growing number of command handlers (auth, projects, sessions, etc.)
- Difficult to maintain, test, and extend
- Command dispatch logic mixed with implementation

**Challenges:**
- Adding 150+ endpoints would make file 10,000+ lines → unmaintainable
- New features require editing Socrates.py directly
- Hard to locate specific command logic
- Difficult to test individual commands in isolation
- Cannot share command utilities across modules

## Solution: Domain-Aware, Team-First, Modular Plugin Architecture

### Key Principles

1. **Domain-Aware**: Not just code projects - supports business, design, research, etc.
2. **Team-First**: Team collaboration as core feature, not afterthought
3. **Modular**: Each command isolated, easy to test and extend
4. **Flexible**: Same platform for solo users and large teams

### Architecture Overview

Transform from **monolithic** to **plugin-based**, **domain-aware** architecture:

```
Socrates.py (Main entry point, ~200-300 lines)
    ↓
    CommandRegistry (loads and routes commands)
    ↓
    cli/commands/ (modular command implementations)
        ├── auth.py (authentication commands)
        ├── domain.py (domain discovery/info) ← DOMAIN-AWARE
        ├── template.py (template system) ← DOMAIN-AWARE
        ├── projects.py (project management) ← DOMAIN-AWARE
        ├── teams.py (team management) ← TEAM-FIRST
        ├── collaboration.py (team collaboration) ← TEAM-FIRST
        ├── sessions.py (session management) ← DOMAIN-AWARE
        ├── documents.py (knowledge base/RAG)
        ├── specifications.py (spec management) ← DOMAIN-AWARE
        ├── questions.py (question management)
        ├── workflows.py (workflow management) ← DOMAIN-AWARE
        ├── code_generation.py (code gen)
        ├── admin.py (admin functions)
        ├── analytics.py (analytics)
        ├── quality.py (quality gates)
        ├── notifications.py (notifications)
        ├── conflicts.py (conflict resolution)
        ├── export.py (export functionality) ← DOMAIN-SPECIFIC FORMATS
        ├── search.py (search)
        ├── insights.py (insights)
        ├── github.py (GitHub integration)
        ├── config.py (configuration)
        ├── system.py (system commands)
        └── utils.py (shared utilities)
    ↓
    cli/utils/ (shared utilities)
        ├── table_formatter.py (formatting)
        ├── prompts.py (user prompts)
        ├── helpers.py (common utilities)
        └── constants.py (constants, messages)
```

## Implementation Details

### 1. Base CommandHandler Class

**File:** `cli/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from rich.console import Console

class CommandHandler(ABC):
    """Base class for all CLI command handlers."""

    # Command metadata
    command_name: str  # e.g., "auth", "project", "document"
    description: str   # Brief description
    help_text: str     # Detailed help

    def __init__(self, console: Console, api_client, config: Dict[str, Any]):
        self.console = console
        self.api = api_client
        self.config = config

    @abstractmethod
    def handle(self, args: List[str]) -> None:
        """Main command handler. Parse args and execute command."""
        pass

    def show_help(self) -> None:
        """Display help for this command."""
        self.console.print(self.help_text)

    def parse_args(self, args: List[str]) -> Dict[str, Any]:
        """Parse command arguments. Override in subclasses for custom parsing."""
        return {"args": args}
```

### 2. Command Registry

**File:** `cli/registry.py`

```python
from pathlib import Path
from typing import Dict, Type
from importlib import import_module

class CommandRegistry:
    """Registry for loading and routing CLI commands."""

    def __init__(self, console, api_client, config):
        self.console = console
        self.api_client = api_client
        self.config = config
        self.commands: Dict[str, CommandHandler] = {}

    def load_all_commands(self) -> None:
        """Auto-load all commands from cli/commands/ directory."""
        commands_dir = Path(__file__).parent / "commands"

        for module_file in commands_dir.glob("*.py"):
            if module_file.name.startswith("_"):
                continue

            module_name = module_file.stem
            try:
                module = import_module(f"cli.commands.{module_name}")

                # Find CommandHandler subclass in module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, CommandHandler) and
                        attr is not CommandHandler):

                        handler = attr(self.console, self.api_client, self.config)
                        self.commands[handler.command_name] = handler

            except Exception as e:
                self.console.print(f"[red]Warning: Failed to load {module_name}: {e}[/red]")

    def route_command(self, command: str, args: List[str]) -> bool:
        """Route command to appropriate handler. Returns True if handled."""
        if command in self.commands:
            self.commands[command].handle(args)
            return True
        return False

    def list_commands(self) -> Dict[str, str]:
        """Return all available commands with descriptions."""
        return {
            name: handler.description
            for name, handler in self.commands.items()
        }
```

### 3. New File Structure

```
Socrates/
├── Socrates.py (refactored to ~250 lines)
├── cli/
│   ├── __init__.py
│   ├── base.py (CommandHandler abstract base)
│   ├── registry.py (CommandRegistry)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── auth.py (50-100 lines)
│   │   ├── projects.py (100-150 lines)
│   │   ├── sessions.py (100-150 lines)
│   │   ├── documents.py (80-120 lines)
│   │   ├── specifications.py (80-120 lines)
│   │   ├── questions.py (50-80 lines)
│   │   ├── teams.py (60-100 lines)
│   │   ├── code_generation.py (50-80 lines)
│   │   ├── admin.py (40-60 lines)
│   │   ├── analytics.py (40-60 lines)
│   │   ├── quality.py (30-50 lines)
│   │   ├── notifications.py (30-50 lines)
│   │   ├── conflicts.py (40-60 lines)
│   │   ├── workflows.py (40-60 lines)
│   │   ├── domains.py (30-50 lines)
│   │   ├── templates.py (30-50 lines)
│   │   ├── export.py (50-80 lines)
│   │   ├── search.py (30-50 lines)
│   │   ├── insights.py (30-50 lines)
│   │   ├── github.py (40-60 lines)
│   │   ├── config.py (50-80 lines)
│   │   ├── system.py (50-80 lines)
│   │   └── utils.py (shared utilities, 100-150 lines)
│   └── utils/
│       ├── __init__.py
│       ├── table_formatter.py (40-60 lines)
│       ├── prompts.py (60-100 lines)
│       ├── helpers.py (50-100 lines)
│       └── constants.py (50-100 lines)
└── cli_logger.py (existing)
```

## Command Module Examples

### Example 1: Auth Command Module

**File:** `cli/commands/auth.py`

```python
"""Authentication commands (register, login, logout, whoami)."""
from cli.base import CommandHandler
from rich.panel import Panel

class AuthCommandHandler(CommandHandler):
    command_name = "auth"
    description = "Authentication commands: register, login, logout, whoami"
    help_text = """
[bold cyan]Authentication Commands:[/bold cyan]
  /auth register     Register new account
  /auth login        Login to account
  /auth logout       Logout from account
  /auth whoami       Show current user info
"""

    def handle(self, args: list) -> None:
        if not args:
            self.show_help()
            return

        subcommand = args[0]

        if subcommand == "register":
            self.register()
        elif subcommand == "login":
            self.login()
        elif subcommand == "logout":
            self.logout()
        elif subcommand == "whoami":
            self.whoami()
        else:
            self.console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
            self.show_help()

    def register(self) -> None:
        """Registration workflow."""
        # Existing registration code moved here
        pass

    def login(self) -> None:
        """Login workflow."""
        # Existing login code moved here
        pass

    def logout(self) -> None:
        """Logout workflow."""
        # Existing logout code moved here
        pass

    def whoami(self) -> None:
        """Show current user info."""
        # Existing whoami code moved here
        pass
```

### Example 2: Project Command Module (Extended)

**File:** `cli/commands/projects.py`

```python
"""Project management commands."""
from cli.base import CommandHandler
from rich.panel import Panel
from rich.prompt import Prompt

class ProjectCommandHandler(CommandHandler):
    command_name = "project"
    description = "Project management: create, list, select, manage, archive, restore, destroy"
    help_text = """
[bold cyan]Project Commands:[/bold cyan]
  /project create        Create new project
  /project list          List all projects (showing status)
  /project select <id>   Select project to work with
  /project info          Show current project info
  /project manage <id>   Unified management interface (archive/restore/destroy)
  /project archive <id>  Archive project (soft delete - reversible)
  /project restore <id>  Restore archived project
  /project destroy <id>  Permanently delete archived project
  /project share <id>    Share project with team member
  /project unshare <id>  Remove project sharing
  /project collaborate <id> View project collaborators
"""

    def handle(self, args: list) -> None:
        if not args:
            self.show_help()
            return

        subcommand = args[0]

        if subcommand == "create":
            self.create()
        elif subcommand == "list":
            self.list()
        elif subcommand == "select":
            self.select(args[1:])
        elif subcommand == "info":
            self.info()
        elif subcommand == "manage":
            self.manage(args[1:])
        elif subcommand == "archive":
            self.archive(args[1:])
        elif subcommand == "restore":
            self.restore(args[1:])
        elif subcommand == "destroy":
            self.destroy(args[1:])
        elif subcommand == "share":
            self.share(args[1:])
        elif subcommand == "unshare":
            self.unshare(args[1:])
        elif subcommand == "collaborate":
            self.collaborate(args[1:])
        else:
            self.console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
            self.show_help()

    # Command implementations moved from Socrates.py
    def create(self) -> None:
        # ... existing create code
        pass

    def manage(self, args: list) -> None:
        # ... existing manage code (archive/restore/destroy unified interface)
        pass

    # ... other methods
```

### Example 3: New Document Command Module

**File:** `cli/commands/documents.py`

```python
"""Document management (knowledge base/RAG)."""
from cli.base import CommandHandler
from pathlib import Path

class DocumentCommandHandler(CommandHandler):
    command_name = "document"
    description = "Document management: upload, list, search, delete"
    help_text = """
[bold cyan]Document Commands:[/bold cyan]
  /document upload <file>    Upload file to knowledge base
  /document list             List project documents
  /document search <query>   Semantic search documents
  /document info <id>        Show document details
  /document delete <id>      Delete document
  /document rag <query>      Get RAG-augmented context
  /document extract-specs    Extract specifications from documents
"""

    def handle(self, args: list) -> None:
        if not args:
            self.show_help()
            return

        subcommand = args[0]

        if subcommand == "upload":
            self.upload(args[1:])
        elif subcommand == "list":
            self.list()
        elif subcommand == "search":
            self.search(args[1:])
        elif subcommand == "info":
            self.info(args[1:])
        elif subcommand == "delete":
            self.delete(args[1:])
        elif subcommand == "rag":
            self.rag(args[1:])
        elif subcommand == "extract-specs":
            self.extract_specs()
        else:
            self.console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")

    def upload(self, args: list) -> None:
        """Upload document to knowledge base."""
        if not args:
            self.console.print("[yellow]Usage: /document upload <file_path>[/yellow]")
            return

        file_path = Path(args[0])
        if not file_path.exists():
            self.console.print(f"[red]✗ File not found: {file_path}[/red]")
            return

        # Check project selected
        project = self.config.get("current_project")
        if not project:
            self.console.print("[red]✗ No project selected. Use /project select first[/red]")
            return

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            result = self.api.upload_document(project["id"], files)

        if result.get("success"):
            self.console.print(f"[green]✓ Document uploaded successfully[/green]")
            self.console.print(f"  Document ID: {result.get('document_id')}")
            self.console.print(f"  Chunks created: {result.get('chunks')}")
        else:
            error_msg = result.get('message') or 'Unknown error'
            self.console.print(f"[red]✗ Upload failed: {error_msg}[/red]")

    def search(self, args: list) -> None:
        """Semantic search documents."""
        if not args:
            self.console.print("[yellow]Usage: /document search <query>[/yellow]")
            return

        query = " ".join(args)
        project = self.config.get("current_project")
        if not project:
            self.console.print("[red]✗ No project selected[/red]")
            return

        result = self.api.semantic_search(project["id"], query)
        # Display results...
        pass

    # ... other methods
```

## Implementation Roadmap

### Phase 1: Refactor Infrastructure (~2-3 hours)
- [x] Design modular architecture
- [ ] Create `cli/base.py` with CommandHandler base class
- [ ] Create `cli/registry.py` with CommandRegistry
- [ ] Refactor main `Socrates.py` to use registry
- [ ] Create `cli/utils/` shared utilities

### Phase 2: Migrate Existing Commands (~2-3 hours)
- [ ] Migrate auth commands → `cli/commands/auth.py`
- [ ] Migrate project commands → `cli/commands/projects.py` (enhanced)
- [ ] Migrate session commands → `cli/commands/sessions.py`
- [ ] Migrate config commands → `cli/commands/config.py`
- [ ] Migrate system commands → `cli/commands/system.py`

### Phase 3: Implement New Commands (Core Features) (~4-5 hours)
- [ ] `cli/commands/documents.py` - Document upload, search, RAG
- [ ] `cli/commands/specifications.py` - Spec CRUD, approval workflows
- [ ] `cli/commands/questions.py` - Question management
- [ ] `cli/commands/teams.py` - Team management, collaboration
- [ ] `cli/commands/code_generation.py` - Code generation

### Phase 4: Implement New Commands (Advanced Features) (~3-4 hours)
- [ ] `cli/commands/admin.py` - Admin functions, health checks
- [ ] `cli/commands/analytics.py` - Analytics, metrics
- [ ] `cli/commands/quality.py` - Quality gates, recommendations
- [ ] `cli/commands/notifications.py` - Notification management
- [ ] `cli/commands/conflicts.py` - Conflict detection/resolution

### Phase 5: Implement Remaining Commands (~2-3 hours)
- [ ] `cli/commands/workflows.py` - Workflow management
- [ ] `cli/commands/domains.py` - Domain registry
- [ ] `cli/commands/templates.py` - Template management
- [ ] `cli/commands/export.py` - Export functionality
- [ ] `cli/commands/search.py` - Search
- [ ] `cli/commands/insights.py` - Insights
- [ ] `cli/commands/github.py` - GitHub integration
- [ ] `cli/commands/utils.py` - Shared command utilities

### Phase 6: Testing & Polish (~1-2 hours)
- [ ] Test all commands with backend API
- [ ] Verify help text and error messages
- [ ] Add missing error handling
- [ ] Update main help system

**Total Estimated Time:** 14-20 hours of focused development

## Benefits of This Architecture

1. **Scalability:** Add new commands by creating new files in `cli/commands/`
2. **Maintainability:** Each command isolated in its own module (~80-150 lines each)
3. **Testability:** Each CommandHandler can be tested independently
4. **Code Reuse:** Shared utilities in `cli/utils/`
5. **Easy to Locate:** Find command logic by looking at module name
6. **Parallel Development:** Multiple team members can work on different commands
7. **Self-Documenting:** Command name = file name
8. **No Monolithic Files:** Max file size ~200-250 lines

## Transition Strategy

**Step 1:** Create new modular infrastructure alongside existing code
**Step 2:** Migrate existing commands one by one
**Step 3:** Keep both systems working until migration complete
**Step 4:** Once all commands migrated, remove old command methods from Socrates.py
**Step 5:** Add new commands using new modular system

This allows **zero downtime** during refactoring.

## Questions & Decisions

1. **Error Handling:** Consistent error message format across all commands?
   - **Decision:** Use `[red]✗ Error message[/red]` format consistently

2. **Config Management:** How to access current project/session?
   - **Decision:** Pass config dict to each handler, handlers read from config

3. **API Client:** How do handlers call backend?
   - **Decision:** API client instance passed to each handler constructor

4. **Help System:** How to generate unified help?
   - **Decision:** Registry aggregates help_text from all handlers

5. **Command Discovery:** How are new commands auto-discovered?
   - **Decision:** Registry scans `cli/commands/` directory for CommandHandler subclasses

## CLI as Blueprint for Future UI

This architecture isn't just for CLI - it's designed to be a **blueprint for the web UI**.

### How CLI Commands Become UI Components

**Current CLI Command Structure:**
```python
class ProjectCommandHandler(CommandHandler):
    def handle(self, args: list) -> None:
        # Parse CLI arguments
        # Call API methods
        # Format output for terminal
```

**Future UI Component (same logic, different presentation):**
```javascript
// React component using same API client
function ProjectManagementPage() {
    const handleCreateProject = (data) => {
        // Same API call as CLI
        api.createProject(data)
            .then(result => renderResult(result))
    }
    // UI components instead of CLI output
    return <ProjectForm onSubmit={handleCreateProject} />
}
```

### Key Benefits of This Design

1. **API Interaction Logic Reusable:**
   - CLI: Calls `api.create_project()` → formats for terminal
   - UI: Calls `api.create_project()` → renders React component

2. **Feature Parity:**
   - CLI implements 100% of backend features
   - UI can copy the same API interaction patterns
   - No "forgot to implement in UI" problems

3. **Testing Strategy:**
   - CLI commands are fully tested with real backend
   - UI developers can reference CLI for correct API usage
   - Same test cases work for both

4. **Reference Documentation:**
   - CLI commands = interactive documentation
   - Shows exact API sequences for each feature
   - UI developers can trace through CLI to understand workflows

### UI Development Workflow

**Phase 1: CLI is the Testing Interface**
```
Backend API Development
    ↓
CLI Commands (test coverage)
    ↓
Manual CLI Testing by Dev + User
    ↓
Validated Workflows
    ↓
UI Implementation (reference CLI for API patterns)
```

**Phase 2: CLI + UI Parallel Development**
```
New Features
    ↓
Backend API + CLI Commands (developed together)
    ↓
Tested via CLI first
    ↓
UI Implementation (copy patterns from CLI)
```

**Phase 3: CLI Becomes Power User Tool**
```
UI for Regular Users
    ↓
CLI for Power Users / Developers / Testing
    ↓
CLI + IDE Integration (run Socrates.py from IDE)
```

### Specific Examples

**Example: Document Upload**

CLI Command:
```python
def upload(self, args: list) -> None:
    file_path = Path(args[0])
    result = self.api.upload_document(project["id"], files)
    self.console.print(f"✓ Document uploaded: {result['document_id']}")
```

UI Component:
```javascript
function DocumentUpload() {
    const [uploading, setUploading] = useState(false)

    const handleUpload = async (file) => {
        setUploading(true)
        const result = await api.uploadDocument(projectId, file)
        setUploading(false)

        if (result.success) {
            showNotification(`Document uploaded: ${result.document_id}`)
        }
    }

    return <FileUploadWidget onUpload={handleUpload} />
}
```

**Same API sequence, different presentation.**

### API Client as Shared Library

**Current Setup:**
- Socrates.py has inline APIClient
- CLI uses this client

**Future Setup:**
- Extract APIClient → `api_client.py` (shared library)
- CLI imports from shared library
- UI backend imports from shared library
- Both use identical API interaction

```
api_client.py (shared)
    ├── ProjectAPI methods
    ├── DocumentAPI methods
    ├── SessionAPI methods
    ├── ...

cli/commands/ (CLI interface)
    ├── projects.py (uses ProjectAPI)
    ├── documents.py (uses DocumentAPI)
    ├── sessions.py (uses SessionAPI)

ui_backend/ (Future UI backend)
    ├── routes/projects.py (uses ProjectAPI)
    ├── routes/documents.py (uses DocumentAPI)
    ├── routes/sessions.py (uses SessionAPI)
```

### Documentation Generated from CLI

Once CLI has all commands, we can generate UI documentation:

```bash
# Generate command reference
/help > CLI_REFERENCE.md

# This becomes:
API_REFERENCE_FROM_CLI.md
    → Shows all endpoints as CLI commands
    → Shows exact API methods being called
    → Becomes starting point for UI implementation
```

### Testing Strategy: CLI First

```
1. Feature Request
   ↓
2. Backend API Implementation
   ↓
3. CLI Command Implementation
   ↓
4. Manual Testing via CLI (User + Dev)
   ↓
5. Automated CLI Tests
   ↓
6. UI Implementation (reference CLI tests)
   ↓
7. UI Tests (copy patterns from CLI tests)
```

This ensures **CLI is always the most complete, most tested interface**.

## Next Steps

1. ✅ Audit all backend endpoints (DONE)
2. ✅ Design modular architecture (DONE - this document)
3. ✅ Design CLI-as-UI-blueprint strategy (DONE - this section)
4. **→ Review & approve complete architecture**
5. Implement Phase 1: Refactor infrastructure
6. Implement Phases 2-6: Migrate and add commands
7. Test full CLI with all 150+ endpoints
8. Document all commands in help system
9. Extract APIClient to shared library (for future UI)
10. Generate API reference documentation from CLI

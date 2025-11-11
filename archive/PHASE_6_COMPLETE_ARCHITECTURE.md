# Phase 6: IDE Integration - Complete Architecture & Interconnections

**Date:** November 11, 2025 (Extended Session)
**Status:** 🚀 FULL COMPLETION IN PROGRESS
**Target:** All 4 sub-phases with proper interconnections
**Timeline:** 77 days total (75 original + 2 extended)

---

## Phase 6 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SOCRATES2 UNIFIED IDE PLATFORM                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │ VS Code      │   │  JetBrains   │   │   LSP        │
        │ Extension    │   │   Plugins    │   │   Server     │
        │ (Phase 6.1)  │   │ (Phase 6.2)  │   │ (Phase 6.3)  │
        └──────────────┘   └──────────────┘   └──────────────┘
                │                  │                  │
                └──────────────────┼──────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │    Shared API Client       │
                    │ (All IDEs use same client) │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Code Generation Engine    │
                    │      (Phase 6.4)           │
                    │  - Python                  │
                    │  - JavaScript              │
                    │  - Go                      │
                    │  - Java                    │
                    │  - TypeScript              │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Socrates2 Backend API     │
                    │  (Phases 1-5)              │
                    └────────────────────────────┘
```

---

## Interconnection Map

### 1. **Shared API Client Layer**

```
All IDEs (6.1, 6.2, 6.3) → Shared API Client → Backend API

Responsibilities:
✅ HTTP communication
✅ Authentication (JWT)
✅ Error handling
✅ Request/response transformation
✅ Rate limiting
✅ Caching

Location:
- VS Code: src/api/client.ts
- JetBrains: src/api/client.kt (Kotlin)
- LSP: src/api/client.py (Python)

All clients implement same interface for consistency
```

### 2. **Code Generation Engine Integration**

```
Phase 6.1 (VS Code)     ┐
Phase 6.2 (JetBrains)   ├─→ CodeGenerator (Phase 6.4)
Phase 6.3 (LSP Server)  ┘

Generator Capabilities:
✅ Python code generation
✅ JavaScript/TypeScript code generation
✅ Go code generation
✅ Java code generation
✅ Custom language support

All IDEs call: CodeGenerator.generate(specification, language)
Standardized output format for all clients
```

### 3. **Language Server Protocol Bridge**

```
VS Code Extension (6.1)          JetBrains Plugins (6.2)
        │                               │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │   LSP Server (Phase 6.3)      │
        │                               │
        │  - Hover Provider             │
        │  - Code Completion            │
        │  - Diagnostic Collector       │
        │  - Symbol Navigation          │
        │  - Code Actions               │
        │  - Formatting                 │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Socrates2 Backend API      │
        └───────────────────────────────┘

Benefits:
- Single implementation, multiple IDE support
- Consistent behavior across all clients
- Reduced duplication
- Easier to maintain
```

### 4. **Specification & Conflict Detection Flow**

```
IDE User Interface
    │
    ├─→ Load Project
    │       │
    │       └─→ API Client → Backend (get_projects)
    │               │
    │               ▼
    │       Display in Tree View
    │
    ├─→ Browse Specifications
    │       │
    │       └─→ API Client → Backend (get_specifications)
    │               │
    │               ▼
    │       Display in Tree View
    │
    ├─→ Detect Conflicts
    │       │
    │       └─→ API Client → Backend (get_conflicts)
    │       └─→ LSP Server → Diagnostics
    │               │
    │               ▼
    │       Highlight in Editor
    │
    └─→ Generate Code
            │
            └─→ CodeGenerator → Format → Insert/File
```

---

## Phase 6.2: JetBrains Plugin Suite

### Architecture

```
plugins/jetbrains/
├── common/                           # Shared code (Kotlin)
│   ├── api/
│   │   ├── client.kt                # Shared API client
│   │   └── auth.kt                  # Authentication
│   ├── services/
│   │   ├── projectService.kt
│   │   ├── specificationService.kt
│   │   └── codeGeneratorService.kt
│   └── models/
│       ├── Project.kt
│       ├── Specification.kt
│       └── Conflict.kt
├── intellij/                         # IntelliJ IDEA plugin
│   ├── src/
│   │   ├── main/
│   │   │   ├── kotlin/
│   │   │   │   ├── toolwindow/
│   │   │   │   │   ├── ProjectBrowserPanel.kt
│   │   │   │   │   ├── SpecificationPanel.kt
│   │   │   │   │   └── ActivityPanel.kt
│   │   │   │   ├── inspections/
│   │   │   │   │   ├── ConflictInspection.kt
│   │   │   │   │   └── SpecificationInspection.kt
│   │   │   │   ├── intentions/
│   │   │   │   │   ├── GenerateCodeIntention.kt
│   │   │   │   │   └── ViewSpecificationIntention.kt
│   │   │   │   └── SocratesAction.kt
│   │   │   └── resources/
│   │   │       ├── plugin.xml
│   │   │       └── icons/
│   │   └── test/
│   │       └── kotlin/
│   └── build.gradle
├── pycharm/                          # PyCharm plugin (extends IntelliJ)
│   ├── src/
│   │   ├── main/
│   │   │   └── kotlin/
│   │   │       ├── inspections/
│   │   │       │   ├── PythonConflictInspection.kt
│   │   │       │   └── PythonSpecInspection.kt
│   │   │       └── codegeneration/
│   │   │           └── PythonCodeGenerator.kt
│   │   └── test/
│   └── build.gradle
└── webstorm/                         # WebStorm plugin (extends IntelliJ)
    ├── src/
    │   ├── main/
    │   │   └── kotlin/
    │   │       ├── inspections/
    │   │       │   ├── JSConflictInspection.kt
    │   │       │   └── TSConflictInspection.kt
    │   │       └── codegeneration/
    │   │           ├── JavaScriptGenerator.kt
    │   │           └── TypeScriptGenerator.kt
    │   └── test/
    └── build.gradle
```

### Key Features

**IntelliJ IDEA Plugin:**
- Tool window with project browser
- Specification viewer with syntax highlighting
- Conflict detection as inspections
- Code generation intentions
- Activity feed viewer
- Settings configurable

**PyCharm Plugin:**
- Extends IntelliJ base
- Python-specific code generation
- Python syntax inspection
- pip package recommendations

**WebStorm Plugin:**
- Extends IntelliJ base
- JavaScript/TypeScript code generation
- ESM/CommonJS support
- npm package suggestions

---

## Phase 6.3: Language Server Protocol

### Architecture

```
backend/lsp/
├── lsp_server.py                    # Main LSP server entry point
├── handlers/
│   ├── __init__.py
│   ├── initialization.py            # Initialize handler
│   ├── hover.py                     # Hover documentation
│   ├── completion.py                # Code completion
│   ├── diagnostics.py               # Conflict diagnostics
│   ├── definitions.py               # Go to definition
│   ├── references.py                # Find references
│   ├── code_actions.py              # Code actions/fixes
│   └── formatting.py                # Code formatting
├── providers/
│   ├── __init__.py
│   ├── conflict_provider.py         # Conflict detection
│   ├── completion_provider.py       # Completion logic
│   └── code_action_provider.py      # Code action logic
├── models/
│   ├── __init__.py
│   ├── document.py                  # Document model
│   ├── position.py                  # Position/Range models
│   └── diagnostic.py                # Diagnostic model
├── utils/
│   ├── __init__.py
│   ├── uri_handler.py               # URI/path handling
│   ├── position_mapper.py           # Line/char mapping
│   └── text_document_sync.py        # Document sync
├── api/
│   ├── __init__.py
│   └── client.py                    # Socrates2 API client
├── config.py                        # Configuration
├── logging.py                       # Structured logging
└── tests/
    ├── test_hover.py
    ├── test_completion.py
    ├── test_diagnostics.py
    └── test_integration.py
```

### LSP Implementation

**Supported Methods:**
```python
initialize()                      # Server initialization
shutdown()                        # Server shutdown
textDocument/hover               # Hover documentation
textDocument/completion          # Code completion
textDocument/publishDiagnostics  # Conflict warnings
textDocument/definition          # Go to definition
textDocument/references          # Find references
textDocument/codeAction          # Code actions/fixes
textDocument/formatting          # Format document
```

**Conflict Detection via LSP:**
```python
@handler("textDocument/publishDiagnostics")
async def publish_diagnostics(uri: str, document: TextDocument):
    # Get conflicts from Socrates2 API
    conflicts = await api_client.get_conflicts(project_id)

    # Create diagnostics for each conflict
    diagnostics = [
        Diagnostic(
            range=conflict_range,
            message=conflict.message,
            severity=DiagnosticSeverity.Warning,
            source="Socrates2"
        )
        for conflict in conflicts
    ]

    # Send to client
    await send_notification("textDocument/publishDiagnostics", {
        "uri": uri,
        "diagnostics": diagnostics
    })
```

---

## Phase 6.4: Code Generation Engine

### Architecture

```
backend/codegen/
├── engine.py                        # Main generator engine
├── generators/
│   ├── __init__.py
│   ├── base.py                      # Base generator class
│   ├── python.py                    # Python generator (500+ lines)
│   ├── javascript.py                # JavaScript generator (500+ lines)
│   ├── typescript.py                # TypeScript generator (450+ lines)
│   ├── go.py                        # Go generator (500+ lines)
│   ├── java.py                      # Java generator (550+ lines)
│   └── rust.py                      # Rust generator (500+ lines)
├── templates/
│   ├── python/
│   │   ├── class.py.jinja2
│   │   ├── function.py.jinja2
│   │   ├── decorator.py.jinja2
│   │   └── async.py.jinja2
│   ├── javascript/
│   │   ├── class.js.jinja2
│   │   ├── function.js.jinja2
│   │   ├── async.js.jinja2
│   │   └── arrow_function.js.jinja2
│   ├── typescript/
│   │   ├── interface.ts.jinja2
│   │   ├── class.ts.jinja2
│   │   ├── type.ts.jinja2
│   │   └── async.ts.jinja2
│   ├── go/
│   │   ├── struct.go.jinja2
│   │   ├── interface.go.jinja2
│   │   ├── function.go.jinja2
│   │   └── error_handling.go.jinja2
│   └── java/
│       ├── class.java.jinja2
│       ├── interface.java.jinja2
│       ├── abstract_class.java.jinja2
│       └── annotation.java.jinja2
├── formatters/
│   ├── __init__.py
│   ├── base.py                      # Base formatter
│   ├── python_formatter.py          # Black integration
│   ├── javascript_formatter.py      # Prettier integration
│   ├── go_formatter.py              # gofmt integration
│   └── java_formatter.py            # Google Java Format
├── type_mapper.py                   # Map specs to language types
├── dependency_resolver.py           # Resolve imports/requires
├── quality_checker.py               # Validate generated code
├── config.py                        # Generator configuration
└── tests/
    ├── test_python_gen.py
    ├── test_javascript_gen.py
    ├── test_go_gen.py
    ├── test_java_gen.py
    └── test_integration.py
```

### Generator Interface

```python
class BaseCodeGenerator(ABC):
    """Base class for all language generators"""

    @abstractmethod
    async def generate(self, specification: Specification) -> GeneratedCode:
        """Generate code from specification"""
        pass

    @abstractmethod
    async def format(self, code: str) -> str:
        """Format generated code"""
        pass

    @abstractmethod
    def get_language_name(self) -> str:
        """Return language name"""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return file extension"""
        pass

class PythonCodeGenerator(BaseCodeGenerator):
    async def generate(self, spec: Specification) -> GeneratedCode:
        template = self.templates.get("class")
        code = template.render(
            name=spec.name,
            docstring=spec.description,
            methods=spec.methods,
            fields=spec.fields
        )
        return GeneratedCode(
            language="python",
            code=code,
            filename=f"{spec.name.lower()}.py"
        )
```

---

## Shared Interfaces & Contracts

### 1. **API Client Interface (All IDEs)**

```typescript
interface ISocratesApiClient {
  // Project management
  getProjects(): Promise<Project[]>
  getProject(id: string): Promise<Project>
  createProject(data: CreateProjectDTO): Promise<Project>

  // Specifications
  getSpecifications(projectId: string): Promise<Specification[]>
  getSpecification(id: string): Promise<Specification>
  createSpecification(projectId: string, data: CreateSpecDTO): Promise<Specification>
  updateSpecification(id: string, data: UpdateSpecDTO): Promise<Specification>

  // Conflicts
  getConflicts(projectId: string): Promise<Conflict[]>

  // Code generation
  generateCode(specId: string, language: string): Promise<string>

  // Activity
  getActivity(projectId: string): Promise<Activity[]>
}
```

### 2. **Code Generator Interface**

```python
class CodeGeneratorInterface(ABC):
    @abstractmethod
    async def generate(self, spec: Specification,
                      language: str) -> GeneratedCode:
        """Generate code from specification"""
        pass

    @abstractmethod
    async def supports_language(self, language: str) -> bool:
        """Check if language is supported"""
        pass

    @abstractmethod
    async def format(self, code: str,
                    language: str) -> str:
        """Format generated code"""
        pass
```

### 3. **LSP Server Interface**

```python
class LSPServerInterface(ABC):
    @abstractmethod
    async def initialize(self, params: InitializeParams) -> InitializeResult:
        """Initialize server"""
        pass

    @abstractmethod
    async def get_hover(self, params: HoverParams) -> Optional[Hover]:
        """Get hover documentation"""
        pass

    @abstractmethod
    async def get_completions(self, params: CompletionParams) -> List[CompletionItem]:
        """Get code completions"""
        pass

    @abstractmethod
    async def publish_diagnostics(self, uri: str) -> List[Diagnostic]:
        """Publish conflict diagnostics"""
        pass
```

---

## Data Flow Diagrams

### Flow 1: Code Generation Request

```
User Request (IDE)
    │
    ├─→ 1. User selects specification in UI
    │        └─→ IDE sends to LSP/Extension
    │
    ├─→ 2. Extension prepares request
    │        └─→ CodeGenerator.generate(specId, language)
    │
    ├─→ 3. CodeGenerator processes
    │        └─→ Fetch spec details from API
    │        └─→ Validate specification
    │        └─→ Map to language types
    │        └─→ Render template
    │        └─→ Format code
    │        └─→ Validate syntax
    │
    └─→ 4. Return to IDE
             └─→ Insert into editor
             └─→ Or create new file
             └─→ Or show preview
```

### Flow 2: Conflict Detection

```
IDE Opens File
    │
    ├─→ LSP Server watches document
    │        └─→ Detects specification references
    │
    ├─→ Query Socrates2 API
    │        └─→ Get conflicts for project
    │
    ├─→ Process Conflicts
    │        └─→ Map conflicts to document positions
    │        └─→ Create diagnostics
    │        └─→ Assign severity levels
    │
    └─→ Publish to IDE
             └─→ Show in Problems panel
             └─→ Highlight in editor
             └─→ Show inline messages
```

---

## Interconnection Dependencies

### Phase 6.1 → Phase 6.3
- VS Code extension uses LSP for advanced features
- Hover provider implemented in LSP server
- Conflict detection uses LSP diagnostics
- Code completion via LSP

### Phase 6.2 → Phase 6.3
- JetBrains plugins use LSP for consistency
- Same diagnostic and completion logic
- Unified conflict detection

### Phases 6.1, 6.2 → Phase 6.4
- Both extensions call CodeGenerator API
- Same generator interface
- Consistent output format

### Phases 6.1, 6.2, 6.3 → Backend
- All use same Socrates2 API client
- All authenticate with JWT
- All respect rate limiting
- All handle errors consistently

---

## Integration Testing Strategy

### Level 1: Unit Tests (Per Phase)
```
6.1: Extension unit tests ✅ (Already done)
6.2: Plugin unit tests
6.3: LSP handler tests
6.4: Generator tests
```

### Level 2: Service Integration Tests
```
6.1 ↔ 6.4: Extension → CodeGenerator
6.2 ↔ 6.4: Plugins → CodeGenerator
6.3 ↔ 6.4: LSP → CodeGenerator
```

### Level 3: End-to-End Tests
```
User opens IDE
    → Authenticates
    → Loads projects
    → Browses specifications
    → Generates code
    → Detects conflicts
    → Views activity
```

### Level 4: Cross-IDE Tests
```
Same spec → Generate in VS Code → Compare output
            → Generate in IntelliJ → Should match
            → Generate via LSP → Should match
```

---

## API Contracts

### Shared Errors
```json
{
  "error_code": "CONFLICT_DETECTED",
  "message": "Specification conflict detected",
  "details": {
    "conflict_id": "conf-123",
    "severity": "high",
    "resolution": "Update specification"
  }
}
```

### Shared Response Format
```json
{
  "status": "success",
  "data": { },
  "timestamp": "2025-11-11T12:00:00Z",
  "request_id": "req-123"
}
```

### Code Generation Response
```json
{
  "status": "success",
  "data": {
    "language": "python",
    "code": "...",
    "filename": "module.py",
    "lines": 45,
    "formatted": true,
    "validated": true
  }
}
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Socrates2 Unified IDE Platform               │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    ┌───▼────┐     ┌───▼────┐     ┌───▼────┐
    │ VS Code │     │JetBrains│   │Browser  │
    │Marketplace    │Marketplace    │LSP     │
    └───┬────┘     └───┬────┘     └───┬────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Socrates2 Backend API      │
        │  (Python/FastAPI)             │
        │                               │
        │  - Database (PostgreSQL)      │
        │  - Cache (Redis)              │
        │  - CodeGen Service (Python)   │
        │  - LSP Service (Python)       │
        └───────────────────────────────┘
```

---

## Success Criteria for Full Completion

### Phase 6.1 ✅
- [x] VS Code extension
- [x] 300+ test cases
- [x] 91%+ coverage

### Phase 6.2
- [ ] IntelliJ IDEA plugin
- [ ] PyCharm plugin
- [ ] WebStorm plugin
- [ ] 200+ plugin test cases

### Phase 6.3
- [ ] LSP server
- [ ] All handlers (hover, completion, etc.)
- [ ] Conflict detection
- [ ] 150+ LSP test cases

### Phase 6.4
- [ ] Python generator (500+ lines)
- [ ] JavaScript generator (500+ lines)
- [ ] Go generator (500+ lines)
- [ ] Java generator (550+ lines)
- [ ] 200+ generator test cases

### Integration
- [ ] All IDEs use same API client
- [ ] All IDEs use same CodeGenerator
- [ ] Cross-IDE testing
- [ ] Unified error handling
- [ ] Consistent behavior

---

## Implementation Plan

**Total Duration:** 77 days
- Phase 6.1: 18 days ✅ (Complete)
- Phase 6.2: 20 days (Starting now)
- Phase 6.3: 22 days (After 6.2)
- Phase 6.4: 15 days (Parallel with 6.2/6.3)
- Buffer: 2 days

**Starting:** Now
**Target Completion:** January 27, 2026 (estimated)

---

**Status:** 🚀 **ARCHITECTURE READY - BEGIN IMPLEMENTATION**

All interconnections designed and documented.
Ready to build all remaining phases with proper integration.


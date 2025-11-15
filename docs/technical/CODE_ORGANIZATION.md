# Socrates Code Organization Guide

## File Structure

### Main Files (After Refactoring)

```
Socrates.py (4520 lines)
├── Imports & Configuration (lines 1-120)
├── SocratesConfig (lines 67-115)
├── SocratesAPI (lines 121-503)
│   └── 45 methods for backend API communication
└── SocratesCLI (lines 504-4520)
    └── 88 methods organized in command groups

intent_parser.py (346 lines)
└── IntentParser class
    ├── Pattern-based intent matching (20 patterns)
    ├── Claude fallback parsing
    └── Helper methods for model/code/export parsing

Other files:
├── api_client_extension.py - Extended API methods
├── cli_logger.py - CLI logging utilities
├── test_edge_cases.py - Intent parser testing
```

## SocratesCLI Command Organization (51 command methods)

### 1. Authentication Commands (5)
- **Line 1043:** `cmd_register()` - User registration
- **Line ~1275:** `cmd_login()` - User authentication
- **Line ~1360:** `cmd_logout()` - Logout
- **Line ~1375:** `cmd_whoami()` - Show current user
- **Line ~1390:** `cmd_account()` - Account management

### 2. Project Management Commands (2)
- **Line 1522:** `cmd_projects()` - List projects
- **Line ~1565:** `cmd_project()` - Project CRUD operations

### 3. Session Management Commands (4)
- **Line ~1845:** `cmd_session()` - Session operations
- **Line 2054:** `cmd_sessions()` - List sessions
- **Line ~2090:** `cmd_history()` - Show conversation history
- **Line ~2320:** (Account operations - see auth)

### 4. LLM Management Commands (7)
- **Line 2519:** `cmd_llm()` - LLM dispatcher
- **Line 2556:** `cmd_llm_list()` - List available models
- **Line 2617:** `cmd_llm_current()` - Show current model
- **Line 2648:** `cmd_llm_select()` - Select model
- **Line 2682:** `cmd_llm_update()` - Update deprecated models
- **Line 2737:** `cmd_llm_costs()` - Show LLM pricing
- **Line 2775:** `cmd_llm_usage()` - Show usage statistics

### 5. Document Management Commands (5)
- **Line 2807:** `cmd_doc()` - Document dispatcher
- **Line 2851:** `cmd_doc_upload()` - Upload document
- **Line 2885:** `cmd_doc_list()` - List documents
- **Line 2918:** `cmd_doc_search()` - Search documents
- **Line 2948:** `cmd_doc_delete()` - Delete document

### 6. GitHub Integration Commands (4)
- **Line 2968:** `cmd_fetch()` - Fetch dispatcher
- **Line 3008:** `cmd_fetch_github_status()` - GitHub connection status
- **Line 3030:** `cmd_fetch_github_connect()` - Connect GitHub
- **Line ~3057:** `cmd_fetch_github()` - Import from GitHub

### 7. Code Generation Commands (6)
- **Line ~3120:** `cmd_code()` - Code generation dispatcher
- **Line ~3170:** `cmd_code_generate()` - Generate code
- **Line ~3220:** `cmd_code_list()` - List generations
- **Line ~3260:** `cmd_code_status()` - Check generation status
- **Line ~3295:** `cmd_code_preview()` - Preview generated code
- **Line ~3345:** `cmd_code_download()` - Download generated code

### 8. UI/Configuration Commands (4)
- **Line ~3370:** `cmd_theme()` - Theme management
- **Line ~3410:** `cmd_format()` - Format settings
- **Line ~3445:** `cmd_config()` - Configuration management
- **Line ~3510:** `cmd_logging()` - Logging settings

### 9. Data/Session Operations (5)
- **Line ~3600:** `cmd_save()` - Save session
- **Line ~3670:** `cmd_export()` - Export project
- **Line ~3720:** `cmd_session_note()` - Session notes
- **Line ~3750:** `cmd_session_bookmark()` - Bookmarks
- **Line ~3775:** `cmd_session_branch()` - Branching

### 10. Analysis/Utility Commands (8)
- **Line ~3800:** `cmd_stats()` - Statistics
- **Line ~3840:** `cmd_template()` - Templates
- **Line ~3920:** `cmd_search()` - Search
- **Line ~3960:** `cmd_status()` - Status
- **Line ~3995:** `cmd_filter()` - Filtering
- **Line ~4030:** `cmd_insights()` - Insights
- **Line ~4060:** `cmd_resume()` - Resume/Continue
- **Line ~4095:** `cmd_wizard()` - Interactive wizard

### 11. System Commands (2)
- **Line ~1513:** `cmd_back()` - Navigate back
- **Line 2831:** `cmd_escape_to_cli()` - Escape to system CLI

### 12. Core Methods (Not Commands)
- **Line 504:** `__init__()` - Initialization
- **Line ~600:** `run()` - Main event loop
- **Line ~800:** `handle_chat_message()` - Chat message handler
- **Line ~900:** `handle_socratic_message()` - Socratic mode handler
- Various helpers: `ensure_authenticated()`, `prompt_with_back()`, etc.

## Key Implementation Details

### IntentParser (intent_parser.py)

**20 Pattern Matching Rules:**
1. Project creation: "create/make/new project X"
2. Project selection: "open/select/choose/go to project X"
3. Session start: "start/begin/create session"
4. Session end: "end/stop/close session"
5. Mode switching: "switch/change to socratic/direct mode"
6. LLM selection: "use/select model X" (explicit)
7. List commands: "list/show/view projects/sessions/models"
8. Export commands: "save/export as markdown/json/csv/pdf"
9. Document upload: "upload/add/import document X"
10. Document list: "list/show/view documents"
11. Document search: "search/find in documents for X"
12. GitHub import: "import/fetch/download from github X"
13. GitHub connect: "connect/setup github"
14. Code generation: "generate/create [word] code/app/application/project"
15. Code list: "list/show/view generations"
16. Code status: "check/show [pronouns] [code] status [for X]" (FIXED)
17. Code download: "download/get [my/the] code [for X]"
18. Code preview: "show preview for gen_789" (FIXED)
19. List mapping
20. Help command: "help [topic]"

**Confidence Levels:**
- High (0.95): Explicit commands matching fixed patterns
- Medium (0.85): Commands with generation IDs
- Low (0.70): Ambiguous requests

**Claude Fallback:** Used for unmatched complex requests

### Mode-Aware Chat System

**Socratic Mode:**
- User gets pure Q&A interaction
- Intent parsing is SKIPPED to avoid interference
- Natural conversation flow

**Direct Mode:**
- User can mix natural language and commands
- Intent parsing ENABLED
- Pattern matching converts natural language to commands
- Claude fallback handles complex requests

### API Organization (45 methods in SocratesAPI)

**Categories:**
- Authentication (login, register, logout)
- Projects (CRUD operations)
- Sessions (conversation management)
- Specifications (document management)
- Code Generation (generate, list, status)
- Analytics & Metrics (tracking)
- Team/Collaboration (team management)
- Document Management (upload, search)
- GitHub Integration (repos, imports)
- LLM Management (models, configuration)
- More...

## Future Optimization Opportunities

### Phase 1: Code Organization (Current)
- ✓ Extract IntentParser (saved 332 lines)
- [ ] Add section headers to SocratesCLI (readability)
- [ ] Create command handler mixins (grouping by type)

### Phase 2: Modularization (Proposed)
- Extract command handlers to separate modules:
  - `commands/auth.py` - Authentication commands
  - `commands/project.py` - Project commands
  - `commands/llm.py` - LLM commands
  - `commands/doc.py` - Document commands
  - `commands/code.py` - Code generation commands
  - etc.
- Create base command class for shared functionality

### Phase 3: Caching & Performance
- Cache API responses for models, documents
- Implement connection pooling
- Lazy load heavy operations

### Phase 4: Configuration
- Extract hardcoded values to config files
- Support environment-based configuration
- User preferences persistence

## Testing

**Current Tests:**
- `test_edge_cases.py` - IntentParser pattern matching (3 tests, all passing)

**Future Tests Needed:**
- API endpoint tests (45+ endpoints)
- Command integration tests
- Mode-aware chat tests
- Error handling tests
- Performance benchmarks

## File Size Summary

- Before refactoring: Socrates.py = 4852 lines
- After IntentParser extraction: Socrates.py = 4520 lines, intent_parser.py = 346 lines
- Reduction: 332 lines (6.8%)
- Maintainability: Significantly improved (separated concerns)

## Next Steps

1. Add logical section headers to SocratesCLI
2. Create base command mixin for shared functionality
3. Extract related commands to separate modules
4. Comprehensive testing and documentation
5. Performance optimization and caching

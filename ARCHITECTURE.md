# Socrates CLI - Architecture Guide

System design, component interactions, and technical architecture of Socrates CLI.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Socrates CLI (v1.0.0)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐        ┌──────────────────┐              │
│  │  User Input      │        │  Configuration   │              │
│  │  & Commands      │        │  Management      │              │
│  └────────┬─────────┘        └────────┬─────────┘              │
│           │                           │                        │
│           ▼                           ▼                        │
│  ┌───────────────────────────────────────────┐                │
│  │     Intent Parser (intent_parser.py)      │                │
│  │  - Pattern matching (20 patterns)         │                │
│  │  - Claude fallback parsing                │                │
│  │  - Confidence scoring                     │                │
│  └────────────────┬────────────────────────┘                 │
│                   │                                            │
│           ┌───────▼────────┐                                  │
│           │ Command Router │                                  │
│           │                │                                  │
│           └───────┬────────┘                                  │
│                   │                                            │
│  ┌────────────────▼──────────────────────────┐               │
│  │      SocratesCLI (4520 lines)             │               │
│  │  - 51 command handlers (cmd_*)            │               │
│  │  - Chat mode management                   │               │
│  │  - Session management                     │               │
│  │  - Rich UI rendering                      │               │
│  └────────────────┬──────────────────────────┘               │
│                   │                                            │
│  ┌────────────────▼──────────────────────────┐               │
│  │  SocratesAPI (45 extended methods)        │               │
│  │  - HTTP request handling                  │               │
│  │  - Response parsing                       │               │
│  │  - Error handling                         │               │
│  │  - JSON serialization                     │               │
│  └────────────────┬──────────────────────────┘               │
│                   │                                            │
│           ┌───────▼─────────┐                                │
│           │  Backend API    │                                │
│           │ (Remote Server) │                                │
│           └─────────────────┘                                │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. SocratesCLI Class (4520 lines)

**Responsibility:** Main CLI interface, command execution, user interaction

**Methods by Category:**

#### Initialization & Core (10 methods)
- `__init__()` - Setup CLI
- `run()` - Main event loop
- `ensure_authenticated()` - Auth check
- `handle_chat_message()` - Message handler (MODE-AWARE)
- `handle_socratic_message()` - Socratic mode handler
- `_setup_prompt_session()` - Terminal setup

#### Command Handlers (51 methods)
- Authentication: register, login, logout, whoami, account
- Projects: projects, project (create/select/manage)
- Sessions: session, sessions, history
- LLM: llm (list, current, select, update, costs, usage)
- Documents: doc (upload, list, search, delete)
- GitHub: fetch (status, connect, github)
- Code: code (generate, list, status, preview, download)
- Config: config, logging, theme, format, save, export
- Analysis: stats, template, search, status, filter, insights, resume, wizard
- System: back, escape_to_cli

**Key Features:**
- Rich console output (tables, panels, syntax highlighting)
- Command history and autocomplete
- Mode-aware chat (Socratic vs Direct)
- Session persistence (in-memory)

### 2. IntentParser Class (346 lines, separate module)

**Responsibility:** Convert natural language to CLI commands

**Two-Level Approach:**

**Level 1: Pattern Matching**
- 20 regex patterns for common commands
- Fast, no API calls
- High confidence (0.95)

**Patterns:**
```
1. Project creation: "create/make/new project X"
2. Project selection: "open/select/choose project X"
3. Session management: "start/end session"
4. LLM selection: "use/select model X"
5. Document operations: "upload/list/search documents"
6. GitHub operations: "connect/import github"
7. Code generation: "generate code"
8-20. Other operations (status, download, preview, etc.)
```

**Level 2: Claude-Based Parsing**
- Fallback for unmatched requests
- Uses Claude API
- Lower confidence (0.7)
- Flexible handling of complex requests

**Confidence Levels:**
- 0.95 (High): Pattern matched, execute automatically
- 0.85 (Medium): Pattern with ID, execute with confirmation
- 0.70 (Low): Claude parsed, requires user confirmation
- < 0.5 (Very Low): Rejected, user provides command

### 3. SocratesAPI Class (503 lines)

**Responsibility:** Backend API communication, 45 extended methods

**Key Methods:**

```python
# HTTP Communication
_request(method, endpoint, **kwargs)  # Base request handler
_get, _post, _put, _delete()          # HTTP verb helpers

# Authentication (5)
authenticate(), register(), logout()
refresh_token(), validate_token()

# Projects (8)
create_project(), get_project(), list_projects()
update_project(), delete_project(), etc.

# Sessions (5)
create_session(), end_session(), get_session()
list_sessions(), get_session_history()

# Documents (6)
upload_document(), list_documents(), search_documents()
delete_document(), etc.

# Code Generation (8)
generate_code(), list_generations(), get_generation_status()
preview_code(), download_code(), etc.

# LLM Management (7)
list_available_llms(), get_current_llm(), select_llm()
update_llm(), get_llm_costs(), get_llm_usage()

# GitHub Integration (4)
connect_github(), get_github_status()
import_from_github(), analyze_repo()

# Other Methods (2+)
get_health(), get_statistics(), etc.
```

**Features:**
- Automatic token refresh
- Error handling with fallbacks
- JSON request/response handling
- Status code validation

### 4. SocratesConfig Class (49 lines)

**Responsibility:** Configuration management

**Methods:**
- `load()` - Load from file
- `save()` - Save to file
- `get(key, default)` - Retrieve value
- `set(key, value)` - Store value

**Storage:**
- File: `~/.socrates/config.json`
- Format: JSON
- Persistent across sessions

---

## Data Flow

### Command Execution Flow

```
User Input
    │
    ▼
Intent Parser
    │
    ├─→ Pattern Match? ──→ YES ──→ High Confidence
    │       │
    │       NO
    │       │
    └─→ Claude Parse? ──→ YES ──→ Lower Confidence
            │
            NO
            │
        Return None
            │
            ▼
    Command Router
            │
            ▼
    Command Handler
    (cmd_* method)
            │
            ▼
    API Call
    (SocratesAPI)
            │
            ▼
    Backend Server
            │
            ▼
    Response ──→ Parse ──→ Render ──→ Display to User
```

### Chat Mode Flow (Mode-Aware)

```
User Message
    │
    ▼
Check chat_mode
    │
    ├─→ "socratic" ──→ Skip Intent Parsing ──→ Socratic Handler
    │
    ├─→ "direct" ──→ Intent Parsing ──→ Command Router
    │
    └─→ Invalid ──→ Error Message
```

---

## File Structure

```
Socrates/
├── Socrates.py                    # Main CLI (4520 lines)
│   ├── SocratesConfig            # Configuration management
│   ├── SocratesAPI               # Backend API client
│   └── SocratesCLI               # CLI interface (51 commands)
│
├── intent_parser.py               # Intent parsing (346 lines)
│   └── IntentParser               # Natural language parsing
│
├── api_client_extension.py        # Extended API methods
├── cli_logger.py                  # Logging utilities
│
├── Documentation/
│   ├── USER_GUIDE.md             # End-user documentation
│   ├── ARCHITECTURE.md           # This file
│   ├── CODE_ORGANIZATION.md      # Code structure guide
│   ├── DEPLOYMENT_PREP.md        # Release checklist
│   └── README.md                 # Project overview
│
├── Tests/
│   └── test_edge_cases.py        # Intent parser tests
│
├── Configuration/
│   ├── requirements.txt          # Production dependencies
│   ├── requirements-dev.txt      # Dev dependencies
│   └── .env.example             # Environment template
│
└── Runtime/
    └── ~/.socrates/
        ├── config.json          # User configuration
        ├── history.txt          # Command history
        ├── app.log             # Application logs
        └── sessions/           # Saved sessions
```

---

## Technology Stack

### Language & Framework
- **Language:** Python 3.12+
- **CLI Framework:** None (custom implementation)
- **Rich UI:** Rich library (tables, panels, syntax highlighting)
- **Prompting:** prompt_toolkit (history, completion, autocomplete)

### External Dependencies
- **HTTP:** requests, httpx
- **Data Validation:** pydantic
- **Security:** cryptography (JWT)
- **Logging:** Python logging
- **Formatting:** JSON, markdown

### Backend Integration
- **API Communication:** REST HTTP
- **Authentication:** JWT tokens
- **LLM Provider:** Anthropic Claude API

---

## Design Patterns

### 1. Command Pattern
Each CLI command is a method following naming convention:
```python
def cmd_<command_name>(self, args: List[str] = None):
    """Execute <command_name>"""
    # Implementation
```

Benefits:
- Easy to discover commands
- Consistent error handling
- Simple command registry

### 2. Mode Pattern
Chat modes determine behavior:
```python
if self.chat_mode == "socratic":
    # Disable intent parsing, pure Q&A
else:  # direct mode
    # Enable commands and intent parsing
```

Benefits:
- Separation of concerns
- Different user experiences
- Easy mode switching

### 3. Factory Pattern
Intent Parser creates command objects:
```python
result = self.intent_parser.parse(user_input)
if result:
    # Create command from result
    command = result['command']
    args = result['args']
```

### 4. Proxy Pattern
API client acts as proxy to backend:
```python
# Transparent to CLI
response = self.api.create_project(name)
# Handles authentication, errors, parsing
```

---

## Error Handling Strategy

### Error Categories

**1. User Input Errors**
```python
try:
    validate_input(user_input)
except ValueError as e:
    self.console.print(f"Invalid input: {e}")
```

**2. API Errors**
```python
try:
    response = self.api.get_data()
except APIError as e:
    self.console.print(f"API Error: {e.message}")
    # Retry logic
```

**3. Authentication Errors**
```python
if not self.ensure_authenticated():
    self.console.print("Please login first")
    return
```

**4. System Errors**
```python
try:
    operation()
except Exception as e:
    self.console.print(f"System Error: {e}")
    logger.error(e, exc_info=True)
```

### Error Recovery

**Automatic:**
- Token refresh on 401 Unauthorized
- Retry on network timeout
- Fallback to local cache

**Manual:**
- User prompted to retry
- Suggest corrective actions
- Clear error messages

---

## Performance Considerations

### Optimization Opportunities

**1. Caching**
```
Target: 30-50% reduction in API calls
Methods:
- Cache model list (static)
- Cache user data (TTL: 5 min)
- Cache document list (TTL: 1 min)
```

**2. Connection Pooling**
```
Target: 100-200ms per request savings
Implementation:
- requests.Session for HTTP pooling
- Connection reuse
```

**3. Pagination**
```
Target: 80% memory reduction for large lists
Methods:
- Paginate results (50 items/page)
- Lazy load next pages
```

### Bottleneck Analysis

**Current Bottlenecks:**
1. API communication (300-500ms)
2. Intent parser Claude fallback (500-1000ms)
3. Large response parsing (100-200ms)
4. Rich rendering (50-100ms)

**Target Optimizations:**
- Reduce API calls via caching
- Avoid Claude fallback (improve patterns)
- Stream large responses
- Optimize rendering

---

## Security Architecture

### Authentication Flow

```
Login Request
    ↓
Validate Credentials
    ↓
Backend Verification
    ↓
Issue JWT Token
    ↓
Store in Memory (NOT disk)
    ↓
Include in API Requests
    ↓
Token Refresh on 401
    ↓
Clear on Logout
```

### Data Protection

**In Transit:**
- HTTPS encryption
- Certificate validation

**At Rest:**
- Configuration stored unencrypted
- User data on secure backend
- No sensitive data in logs

**In Memory:**
- JWT token in Python variable
- Clear on logout
- No credential persistence

### Input Validation

```python
# Validate all user inputs
validate_project_name(name)     # alphanumeric + underscore
validate_doc_id(id)              # UUID format
validate_query(query)            # XSS prevention
validate_file_size(size)         # Max 50MB
```

---

## Extensibility

### Adding New Commands

1. **Create command method:**
   ```python
   def cmd_mycommand(self, args: List[str] = None):
       """Handle /mycommand"""
       # Implementation
   ```

2. **Register in help:**
   ```python
   # Update help text
   self._setup_help()
   ```

3. **Add to intent parser (optional):**
   ```python
   # Add pattern to patterns list
   (r'pattern_regex', lambda m: ("/mycommand", args))
   ```

### Adding New API Methods

1. **Extend SocratesAPI:**
   ```python
   def my_operation(self, param):
       return self._post("/api/v1/endpoint", json={...})
   ```

2. **Use in command:**
   ```python
   result = self.api.my_operation(value)
   ```

---

## Testing Strategy

### Unit Tests
- Intent parser patterns (20+ patterns)
- API method response parsing
- Configuration management

### Integration Tests
- Command → API flow
- Authentication flow
- Mode switching

### E2E Tests
- Full user workflows
- Multi-command sequences
- Error scenarios

### Performance Tests
- API response time
- Pattern matching performance
- Memory usage
- Rendering performance

---

## Deployment Architecture

### Development
```
Local Machine
    ↓
Python 3.12
    ↓
http://localhost:8000/api
    ↓
Development Backend
```

### Production
```
User Machine
    ↓
Python 3.12 + pip install socrates
    ↓
https://api.socrates.dev
    ↓
Production Backend (Dockerized)
    ↓
Database (PostgreSQL, Two databases)
    ↓
LLM Provider (Anthropic API)
```

---

## Summary

**Socrates CLI Architecture:**
- Modular design with clear separation of concerns
- Natural language intent parsing with two-level approach
- Mode-aware chat system (Socratic vs Direct)
- Extensible command framework (51 current commands)
- Secure authentication and API communication
- Rich terminal UI with real-time feedback

**Key Strengths:**
- Intuitive natural language interface
- Flexible mode system
- Comprehensive command set
- Production-ready error handling

**Areas for Enhancement:**
- Performance optimization (caching, pooling)
- Extended modularization (separate command files)
- Advanced security features
- Comprehensive testing

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
**Architecture Status:** Production Ready

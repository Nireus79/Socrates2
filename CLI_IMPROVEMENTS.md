# CLI Improvements & Enhancement Roadmap

**Date:** November 8, 2025
**Status:** Active Development
**Priority:** High for UX improvements

## Overview

The Socrates CLI (Socrates.py) is a well-structured interactive command-line interface with 940 lines of code. It successfully implements core authentication, project management, session handling, and chat modes. This document outlines identified gaps and recommended improvements.

---

## Current Implementation Status

### ✅ Implemented Features

#### Authentication (100%)
- User registration (/register)
- User login with JWT tokens (/login)
- Logout (/logout)
- User info display (/whoami)
- Token storage and management
- Session persistence

#### Project Management (90%)
- List projects (/projects)
- Create project (/project create)
- Select project (/project select <id>)
- Get project info (/project info)
- Delete project (/project delete)
- Project selection state tracking

#### Session Management (85%)
- Start new session (/session start)
- End session (/session end)
- List sessions (/sessions)
- View history (/history)
- Question/answer flow
- Session state tracking

#### Chat Modes (90%)
- Socratic mode (default) - Structured questioning
- Direct chat mode - Free-form conversation
- Mode switching (/mode)
- Mode detection and prompts

#### User Experience (85%)
- Rich console formatting (colors, panels, tables)
- Command completion with WordCompleter
- Command history with FileHistory
- Interactive prompts (Prompt, Confirm)
- Progress spinners for async operations
- Configuration persistence (~/.socrates/config.json)
- Help system (/help)

#### System Features (80%)
- Configuration management
- Debug mode toggle (/debug)
- Error handling with stack traces
- API client with authentication
- Request/response handling

---

## Identified Gaps & Issues

### Priority 1: Critical (Blocking Workflows)

#### 1. Error Recovery & Handling
**Status:** Partially implemented
**Issue:** Limited error context and recovery options
- API errors show generic messages
- No retry logic for transient failures
- No offline mode or caching
- Connection errors not gracefully handled

**Recommendations:**
```python
# Implement retry decorator
def retry_on_network_error(max_retries=3, backoff=2):
    """Retry with exponential backoff"""

# Implement error context
class APIError(Exception):
    def __init__(self, status_code, message, retry_after=None):
        self.status_code = status_code
        self.message = message
        self.retry_after = retry_after

# Add offline mode capability
class OfflineManager:
    def cache_response(self, endpoint, data)
    def get_cached_response(self, endpoint)
    def sync_when_online(self)
```

**Effort:** Medium | **Impact:** High

#### 2. Output Export Formats
**Status:** Not implemented
**Issue:** Cannot export conversations or specifications
- No export to markdown
- No export to JSON
- No export to CSV
- No save-to-file option

**Recommendations:**
```
/export format <markdown|json|csv|pdf>
/export session <session_id> <format>
/export project <project_id> <format> [--include-history]
/save <filename.md>  # Quick save to markdown
```

**Effort:** Low-Medium | **Impact:** High

#### 3. Batch/Script Mode
**Status:** Not implemented
**Issue:** CLI only works interactively
- No support for piping commands
- No scripting capability
- No batch processing
- No automation support

**Recommendations:**
```bash
# Script mode
python Socrates.py --script commands.txt
python Socrates.py --batch

# Piping support
echo -e "/login\nemail@example.com\npassword" | python Socrates.py

# Shell-style commands
socrates < script.txt
```

**Effort:** Medium | **Impact:** Medium

---

### Priority 2: High (UX Improvements)

#### 4. Configuration Management
**Status:** Basic implementation
**Issue:** Limited config control and visibility
- No config editing UI
- No preset management
- No auto-complete for values
- Hard to reset/clear specific values

**Recommendations:**
```
/config list                      # Show all config
/config set <key> <value>         # Set value
/config get <key>                 # Get specific value
/config reset [--all]             # Reset to defaults
/config export <filename>         # Export config
/config import <filename>         # Import config
/config validate                  # Check config validity

# Config presets
/config preset save <name>
/config preset load <name>
/config preset list
```

**Effort:** Medium | **Impact:** Medium

#### 5. Project Templates
**Status:** Not implemented
**Issue:** All projects start from scratch
- No templates for common project types
- No quick-start workflows
- No example projects

**Recommendations:**
```
/project template list            # Show available templates
/project create --template web-api
/project create --template mobile-app
/project create --template data-processing

Templates:
- web-api: REST API, authentication, database
- mobile-app: Screens, navigation, persistence
- data-processing: ETL, pipelines, analytics
- microservice: Service discovery, messaging
```

**Effort:** Low-Medium | **Impact:** Medium

#### 6. Session Management Enhancements
**Status:** Partially implemented
**Issue:** Limited session control and visibility
- No session notes/bookmarks
- No session branching
- No session duplication
- No progress tracking
- No session recovery

**Recommendations:**
```
/session note "Important discovery"
/session bookmark                 # Mark current point
/session branch <name>            # Create alternative path
/session compare <session1> <session2>
/session resume <session_id>      # Continue paused session
/session stats                    # Show progress metrics
/session export <session_id> <format>
```

**Effort:** Medium | **Impact:** High

#### 7. Display & Formatting Options
**Status:** Limited
**Issue:** No output customization
- Fixed color scheme
- No theme support
- No output verbosity control
- No compact/verbose modes

**Recommendations:**
```
/format list                      # Show available formats
/format theme <light|dark|colorblind>
/format verbosity <quiet|normal|verbose|debug>
/format width <auto|80|120|...>
/format tabular-only              # No colors/styling
/format json                      # Machine-readable output

# Configuration
[display]
theme = dark
verbosity = verbose
use_colors = true
table_width = auto
```

**Effort:** Medium | **Impact:** Low-Medium

#### 8. Plugin System
**Status:** Not implemented
**Issue:** No extensibility
- Cannot add custom commands
- Cannot extend functionality
- No third-party integration

**Recommendations:**
```python
# Plugin interface
class CLIPlugin:
    def register_commands(self) -> Dict[str, Callable]
    def on_session_start(self, session)
    def on_session_end(self, session)
    def on_chat_message(self, message)
    def get_config_schema(self)

# Loading plugins
~/.socrates/plugins/
  my_plugin.py
  my_integration/
```

**Effort:** High | **Impact:** Medium

---

### Priority 3: Nice-to-Have Features

#### 9. Advanced Search & Filtering
**Status:** Not implemented
**Issue:** Limited ability to find data
- No search in projects
- No filter sessions
- No search in history
- No date range filters

**Recommendations:**
```
/search project <query>           # Search project names/descriptions
/search session <query>           # Search session history
/search specifications <query>    # Search extracted specs
/filter sessions --phase discovery --status active
/filter projects --updated-after 2025-11-01
```

**Effort:** Medium | **Impact:** Low-Medium

#### 10. Statistics & Analytics
**Status:** Not implemented
**Issue:** No visibility into usage patterns
- No session metrics
- No specification extraction rate
- No time tracking
- No productivity metrics

**Recommendations:**
```
/stats session [<session_id>]     # Session statistics
/stats project [<project_id>]     # Project statistics
/stats user                        # User statistics
/stats timeline                    # Usage over time
/stats export <format>            # Export analytics

Stats to track:
- Questions asked / answered
- Specifications extracted
- Time per session
- Extraction rate
- Chat mode distribution
```

**Effort:** Medium | **Impact:** Low-Medium

#### 11. Interactive Wizards
**Status:** Partially implemented
**Issue:** Some workflows could be guided
- Project creation is straightforward
- No wizard for complex tasks
- No guided tutorials

**Recommendations:**
```
/wizard project-setup             # Interactive project setup
/wizard first-session             # First session guide
/wizard best-practices            # Best practices tutorial
/wizard config                    # Configuration wizard

Features:
- Step-by-step guidance
- Examples and explanations
- Validation and suggestions
- Save/load wizard state
```

**Effort:** Medium | **Impact:** Low-Medium

#### 12. Team Features (CLI Side)
**Status:** Not implemented
**Issue:** No multi-user collaboration UI
- No shared project awareness
- No real-time collaboration indication
- No shared session features

**Recommendations:**
```
/project share <project_id> <email> <role>
/project unshare <project_id> <email>
/project collaborators [<project_id>]
/project access-level <project_id> [<email>]
/team list
/team members <team_id>
/team add <user_email>
```

**Effort:** Medium | **Impact:** Low-Medium

---

## Technical Debt & Code Quality

### Type Hints
**Status:** 90% complete
**Issue:** Some methods missing return type hints
- See backend TODO notes for SQLAlchemy filter issues
- Some generic typing needed

**Recommendations:**
```python
# Before
def cmd_projects(self):

# After
def cmd_projects(self) -> None:
```

**Effort:** Low | **Impact:** Low

### Documentation
**Status:** Good
**Issue:** Inline documentation could be richer
- Complex logic needs more comments
- API integration could have examples
- Edge cases not documented

**Effort:** Low | **Impact:** Low

### Testing
**Status:** Basic
**Issue:** CLI tests are integration-focused
- Unit tests for helper functions
- Mock API responses
- Test CLI workflows end-to-end

**Effort:** Medium | **Impact:** Medium

---

## Implementation Roadmap

### Phase 1 (Immediate - Sprint 1)
- [ ] Error recovery & retry logic
- [ ] Output export formats (markdown, JSON)
- [ ] Session export/save
- [ ] Configuration UI improvements

**Effort:** 1-2 weeks | **Impact:** 🟢 High

### Phase 2 (Short-term - Sprint 2-3)
- [ ] Batch/script mode
- [ ] Project templates
- [ ] Session management enhancements
- [ ] Display formatting options
- [ ] Advanced search/filtering

**Effort:** 2-3 weeks | **Impact:** 🟡 Medium

### Phase 3 (Medium-term - Sprint 4-5)
- [ ] Statistics & analytics
- [ ] Interactive wizards
- [ ] Plugin system foundation
- [ ] Team features

**Effort:** 3-4 weeks | **Impact:** 🟢 Medium-High

### Phase 4 (Future)
- [ ] Full plugin system
- [ ] Advanced analytics dashboard
- [ ] Desktop app wrapper
- [ ] Mobile companion app

---

## CLI Commands Reference (Current + Proposed)

### Implemented
```
/help                             # Show help
/exit, /quit                       # Exit CLI
/clear                            # Clear screen
/debug                            # Toggle debug mode

Authentication:
/register                         # Register account
/login                           # Login
/logout                          # Logout
/whoami                          # Show current user

Projects:
/projects                        # List projects
/project create                  # Create project
/project select <id>             # Select project
/project info                    # Show project details
/project delete <id>             # Delete project

Sessions:
/session start                   # Start session
/session end                     # End session
/sessions                        # List sessions
/history                         # Show conversation

Chat:
/mode                           # Toggle mode (socratic/direct)
/mode <socratic|direct>         # Set mode
```

### Proposed (Priority 1)
```
/export <format> [<id>]         # Export data
/export session <session_id> <format>
/export project <project_id> <format>
/save <filename>                # Quick save to markdown

/config list                    # Show config
/config set <key> <value>       # Set config
/config get <key>               # Get config value
```

### Proposed (Priority 2)
```
/session note <text>            # Add session note
/session bookmark               # Bookmark current point
/session stats [<id>]           # Show session stats
/search <query>                 # Search across data
/filter <criteria>              # Filter results

/stats <section>                # Show statistics
/project template <name>        # Create from template
```

### Proposed (Priority 3)
```
/wizard <topic>                 # Interactive wizard
/plugin list                    # List plugins
/plugin install <name>          # Install plugin
/theme <name>                   # Set color theme
/format <option>                # Set display format
```

---

## Performance Considerations

### Current Bottlenecks
1. **Large project lists** - Pagination needed for 100+ projects
2. **Long sessions** - History loading could be lazy
3. **Table rendering** - Large tables could be paginated

### Recommendations
```python
# Implement pagination
/projects --page 2 --limit 20
/history --limit 50 --page 1

# Implement lazy loading
class LazyTable:
    def load_more()
    def paginate()

# Implement caching
class ResponseCache:
    ttl = 300  # 5 minutes
```

---

## API Compatibility Issues

### Current Issues
1. **Response format inconsistency** - Some endpoints return `success` field, others don't
2. **Error handling** - Inconsistent error response formats
3. **Pagination** - Not all list endpoints support pagination

### Recommendations
See PROJECT_AUDIT_REPORT.md for backend fixes needed

---

## Testing Strategy

### Unit Tests
- [ ] SocratesConfig load/save
- [ ] SocratesAPI request building
- [ ] Command parsing
- [ ] Error handling

### Integration Tests
- [ ] Full authentication flow
- [ ] Project CRUD operations
- [ ] Session workflow
- [ ] Export functionality

### End-to-End Tests
- [ ] Complete user journey
- [ ] Error recovery
- [ ] Offline mode (once implemented)

---

## Success Criteria

### CLI v1.5 (Current)
- ✅ Authentication working
- ✅ Project management functional
- ✅ Session handling operational
- ✅ Chat modes working
- ⚠️ Error handling basic
- ❌ Export functionality missing
- ❌ Batch mode missing
- ❌ Advanced features missing

### CLI v2.0 (Target)
- ✅ All v1.5 features
- ✅ Robust error handling with retry
- ✅ Export to multiple formats
- ✅ Batch/script mode
- ✅ Project templates
- ✅ Enhanced session management
- ✅ Search/filter functionality
- ✅ Statistics & analytics
- ⚠️ Plugin system (basic)
- ❌ Full plugin system
- ❌ Mobile app

---

## Notes for Next Session

1. **Start with Priority 1 items** - Error recovery and export are most critical
2. **Coordinate with backend** - Some features need API changes (see PROJECT_AUDIT_REPORT.md)
3. **User testing** - Get feedback on new commands before full implementation
4. **Documentation** - Update help and examples for new features
5. **Backwards compatibility** - Ensure existing scripts still work

---

**End of CLI_IMPROVEMENTS.md**

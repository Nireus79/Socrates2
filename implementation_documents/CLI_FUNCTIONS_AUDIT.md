# CLI Functions Audit & Enhancement Plan

**Date:** November 8, 2025
**Current Status:** Master branch analysis
**CLI Completion:** 85% (20/35+ potential commands)

---

## Currently Implemented CLI Commands (20 functions)

### Authentication (4/4 - Complete ✅)
```
✅ /register              - Register new account
✅ /login                 - Login to existing account
✅ /logout                - Logout from current session
✅ /whoami                - Show current user information
```

**Handler Functions:**
- `cmd_register()` - Line 331
- `cmd_login()` - Line 360
- `cmd_logout()` - Line 383
- `cmd_whoami()` - Line 397

---

### Project Management (5/5 - Complete ✅)
```
✅ /projects              - List all projects
✅ /project create        - Create new project
✅ /project select <id>   - Select project
✅ /project info          - Show project details
✅ /project delete <id>   - Delete project
```

**Handler Functions:**
- `cmd_projects()` - Line 412
- `cmd_project(args)` - Line 450

---

### Session Management (4/4 - Core Complete ✅, Enhanced Missing 🔴)
```
✅ /session start         - Start Socratic session
✅ /session end           - End session
✅ /sessions              - List sessions
✅ /history               - Show conversation history

❌ /session note <text>   - Add session note (NOT IMPLEMENTED)
❌ /session bookmark      - Bookmark current point (NOT IMPLEMENTED)
❌ /session resume <id>   - Resume paused session (NOT IMPLEMENTED)
❌ /session stats         - Show session statistics (NOT IMPLEMENTED)
```

**Handler Functions:**
- `cmd_session(args)` - Line 539
- `cmd_sessions()` - Line 595
- `cmd_history()` - Line 634

---

### Chat Modes (1/1 - Complete ✅)
```
✅ /mode                  - Toggle between modes
✅ /mode socratic         - Switch to Socratic mode
✅ /mode direct           - Switch to direct mode
```

**Handler Logic:**
- Lines 829-847 in `handle_command()`

---

### System/Utilities (3/3 - Complete ✅)
```
✅ /help                  - Show help message (Line 784)
✅ /clear                 - Clear screen (Line 794)
✅ /debug                 - Toggle debug mode (Line 798)
✅ /exit, /quit           - Exit CLI (Line 787)
```

---

## Missing CLI Commands (15 functions needed)

### Priority 1: Critical Missing Features (Should add first)

#### 1. Export Functions (3 commands) 🔴
```
❌ /export markdown <project_id>     - Export as Markdown
❌ /export json <project_id>         - Export as JSON
❌ /export csv <project_id>          - Export as CSV
❌ /export pdf <project_id>          - Export as PDF
❌ /save <filename>                  - Quick save to file
```

**Why needed:** Users can't save/export their work
**Effort:** Medium (depends on backend API)
**Status:** Backend partially ready (Phase 2)

---

#### 2. Configuration Functions (3 commands) 🔴
```
❌ /config list                      - Show all configuration
❌ /config set <key> <value>         - Set config value
❌ /config get <key>                 - Get config value
❌ /config reset [--all]             - Reset to defaults
```

**Why needed:** Users need to customize CLI behavior
**Effort:** Low (local config management)
**Status:** Backend infrastructure exists

---

#### 3. Search & Filter Functions (2 commands) 🔴
```
❌ /search <query>                   - Search projects/specs
❌ /filter <criteria>                - Filter projects/sessions
```

**Why needed:** Easy discovery of existing work
**Effort:** Medium (depends on backend search)
**Status:** Backend not implemented

---

### Priority 2: Important Enhancements (Add second)

#### 4. Statistics & Analytics (2 commands) 🟡
```
❌ /stats [project|session|user]     - Show statistics
❌ /insights                         - Show insights/recommendations
```

**Why needed:** Help users understand their progress
**Effort:** Medium
**Status:** Backend partially ready (Phase 3)

---

#### 5. Session Enhancements (3 commands) 🟡
```
❌ /session note <text>              - Add note to session
❌ /session bookmark                 - Mark progress checkpoint
❌ /session branch <name>            - Create alternative path
```

**Why needed:** Better session management
**Effort:** Medium
**Status:** Backend needs enhancement

---

#### 6. Project Templates (1 command) 🟡
```
❌ /template list                    - List available templates
❌ /template info <name>             - Get template details
❌ /project create --template <name> - Create from template
```

**Why needed:** Quick project setup
**Effort:** Low-Medium
**Status:** Backend ready (Phase 2)

---

### Priority 3: Nice-to-Have Features (Add third)

#### 7. Advanced Features (2 commands) 🔵
```
❌ /wizard <topic>                   - Interactive wizard
❌ /format <option>                  - Set display format
❌ /theme <name>                     - Set color theme
```

**Why needed:** Enhanced UX
**Effort:** Low-Medium
**Status:** Backend not needed

---

## Quick Comparison Table

| Command | Status | Priority | Effort | Backend Ready |
|---------|--------|----------|--------|---------------|
| /register | ✅ | - | - | ✅ |
| /login | ✅ | - | - | ✅ |
| /logout | ✅ | - | - | ✅ |
| /whoami | ✅ | - | - | ✅ |
| /projects | ✅ | - | - | ✅ |
| /project | ✅ | - | - | ✅ |
| /session | ✅ | - | - | ✅ |
| /sessions | ✅ | - | - | ✅ |
| /history | ✅ | - | - | ✅ |
| /mode | ✅ | - | - | ✅ |
| /help | ✅ | - | - | N/A |
| /clear | ✅ | - | - | N/A |
| /debug | ✅ | - | - | N/A |
| **Subtotal** | **✅13** | - | - | - |
| | | | | |
| /export | ❌ | 1 | Med | 🟡 |
| /save | ❌ | 1 | Low | 🟡 |
| /config | ❌ | 1 | Low | ✅ |
| /search | ❌ | 1 | Med | ❌ |
| /stats | ❌ | 2 | Med | 🟡 |
| /session note | ❌ | 2 | Low | 🟡 |
| /session bookmark | ❌ | 2 | Low | 🟡 |
| /session branch | ❌ | 2 | Med | 🟡 |
| /template | ❌ | 2 | Low | ✅ |
| /filter | ❌ | 2 | Med | ❌ |
| /insights | ❌ | 3 | Med | 🟡 |
| /wizard | ❌ | 3 | Med | ❌ |
| /format | ❌ | 3 | Low | ❌ |
| /theme | ❌ | 3 | Low | ❌ |
| **Subtotal** | **❌15** | - | - | - |
| | | | | |
| **TOTAL** | **13/28** | | | |

---

## Implementation Roadmap for Missing CLI Functions

### Phase 1: Quick Wins (1-2 weeks)
**No backend dependencies - Pure CLI enhancement**

#### 1.1 Config Management `/config` (3 hours)
```python
def cmd_config(self, args: List[str]):
    """Manage CLI configuration."""
    if not args:
        # List all config
        return

    subcommand = args[0]
    if subcommand == "list":
        # Show all settings
        pass
    elif subcommand == "set":
        # Set key=value
        pass
    elif subcommand == "get":
        # Get specific setting
        pass
```

**Features:**
- Display/set theme
- Display/set verbosity
- Display/set output format
- Save/load presets

---

#### 1.2 Display/Theme Options `/theme`, `/format` (2 hours)
```python
def cmd_theme(self, args: List[str]):
    """Change color theme."""
    themes = ['dark', 'light', 'colorblind', 'monokai']
    # Implementation

def cmd_format(self, args: List[str]):
    """Change output format."""
    formats = ['rich', 'json', 'table', 'minimal']
    # Implementation
```

---

#### 1.3 Quick Save `/save` (2 hours)
```python
def cmd_save(self, args: List[str]):
    """Quick save current session/project to file."""
    if not self.current_session:
        self.console.print("[yellow]No active session to save[/yellow]")
        return

    filename = args[0] if args else f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    # Save to file
```

---

### Phase 2: API-Backed Features (2-3 weeks)
**Requires backend API endpoints**

#### 2.1 Export Functions `/export` (8 hours)
**Depends on:** Backend export API (Phase 2)

```python
def cmd_export(self, args: List[str]):
    """Export session or project."""
    if not args:
        self.console.print("[yellow]Usage: /export <format> [<id>][/yellow]")
        return

    format_type = args[0]  # markdown, json, csv, pdf
    target_id = args[1] if len(args) > 1 else (
        self.current_project["id"] if self.current_project else None
    )

    if format_type == "markdown":
        result = self.api.export_markdown(target_id)
    elif format_type == "json":
        result = self.api.export_json(target_id)
    elif format_type == "csv":
        result = self.api.export_csv(target_id)
    elif format_type == "pdf":
        result = self.api.export_pdf(target_id)
```

---

#### 2.2 Session Enhancements (8 hours)
**Depends on:** Backend session API extensions (Phase 2)

```python
def cmd_session_note(self, args: List[str]):
    """Add note to current session."""
    if not self.current_session:
        self.console.print("[yellow]No active session[/yellow]")
        return

    note_text = " ".join(args)
    result = self.api.add_session_note(
        self.current_session["id"],
        note_text
    )

def cmd_session_bookmark(self):
    """Bookmark current point in session."""
    if not self.current_session:
        self.console.print("[yellow]No active session[/yellow]")
        return

    result = self.api.bookmark_session(self.current_session["id"])

def cmd_session_branch(self, args: List[str]):
    """Create alternative path from current session."""
    if not self.current_session:
        return

    branch_name = args[0] if args else None
    result = self.api.create_session_branch(
        self.current_session["id"],
        branch_name
    )
```

---

#### 2.3 Search & Filter (6 hours)
**Depends on:** Backend search API (Phase 3)

```python
def cmd_search(self, args: List[str]):
    """Search projects, sessions, or specifications."""
    query = " ".join(args)
    result = self.api.search(query)

def cmd_filter(self, args: List[str]):
    """Filter sessions or projects."""
    # Parse filter criteria
    filters = self._parse_filters(args)
    result = self.api.filter_projects(filters)
```

---

#### 2.4 Statistics `/stats` (6 hours)
**Depends on:** Backend analytics API (Phase 3)

```python
def cmd_stats(self, args: List[str]):
    """Show statistics."""
    if not args:
        # User stats
        result = self.api.get_user_stats()
    else:
        target = args[0]  # "session", "project"
        target_id = args[1] if len(args) > 1 else None
        result = self.api.get_stats(target, target_id)
```

---

#### 2.5 Project Templates (4 hours)
**Depends on:** Backend template API (Phase 2)

```python
def cmd_template(self, args: List[str]):
    """Manage project templates."""
    if not args:
        # List templates
        result = self.api.list_templates()
    elif args[0] == "info":
        template_name = args[1]
        result = self.api.get_template_info(template_name)
```

---

### Phase 3: Advanced Features (1-2 weeks)
**No backend dependencies - Pure CLI UX**

#### 3.1 Insights & Recommendations `/insights` (4 hours)
```python
def cmd_insights(self):
    """Show insights based on current project/session."""
    if not self.current_project:
        self.console.print("[yellow]Select a project first[/yellow]")
        return

    insights = [
        "You've extracted 15 specifications (85% of estimated needs)",
        "Current conflict resolution rate: 90%",
        "Recommended next step: Define API authentication requirements"
    ]
```

---

#### 3.2 Interactive Wizard `/wizard` (4 hours)
```python
def cmd_wizard(self, args: List[str]):
    """Interactive guided wizard."""
    wizard_type = args[0] if args else None

    if wizard_type == "project":
        self._wizard_project_setup()
    elif wizard_type == "session":
        self._wizard_first_session()
    elif wizard_type == "config":
        self._wizard_configuration()
```

---

## Code Structure for New Commands

### Pattern for Command Methods
```python
def cmd_<name>(self, args: List[str] = None):
    """Brief description of command."""
    # 1. Check prerequisites
    if not self.ensure_authenticated():
        return

    if not self.ensure_project_selected():
        return

    # 2. Parse arguments
    if not args:
        self.console.print("[yellow]Usage: /<name> <arg1> [<arg2>][/yellow]")
        return

    # 3. Execute
    try:
        with Progress(...) as progress:
            progress.add_task("Processing...", total=None)
            result = self.api.method(args[0])

        if result.get("success"):
            self.console.print("[green]✓ Success[/green]")
            # Display results
        else:
            self.console.print(f"[red]✗ Error: {result.get('message')}[/red]")

    except Exception as e:
        self.console.print(f"[red]Error: {e}[/red]")
        if self.debug:
            import traceback
            self.console.print(traceback.format_exc())
```

### Pattern for Command Handler Registration
```python
def handle_command(self, user_input: str):
    """Parse and handle command."""
    parts = user_input.strip().split()
    command = parts[0].lower()
    args = parts[1:]

    if command == "/<name>":
        self.cmd_<name>(args)
```

---

## API Dependencies Needed

### For Priority 1 (No dependencies)
- ✅ Config management - Local file only
- ✅ Theme/format - Local file only
- ✅ Quick save - Local file only

### For Priority 2 (Needs backend)

#### Export API
```
GET /api/v1/export/markdown/<project_id>
GET /api/v1/export/json/<project_id>
GET /api/v1/export/csv/<project_id>
GET /api/v1/export/pdf/<project_id>
```
**Status:** Phase 2 partial (needs completion)

#### Session Enhancement API
```
POST /api/v1/sessions/<session_id>/notes
POST /api/v1/sessions/<session_id>/bookmark
POST /api/v1/sessions/<session_id>/branch
GET /api/v1/sessions/<session_id>/stats
```
**Status:** Phase 2 (needs implementation)

#### Search API
```
GET /api/v1/search?q=<query>&type=<projects|sessions|specs>
```
**Status:** Phase 3 (needs implementation)

#### Stats API
```
GET /api/v1/stats/user
GET /api/v1/stats/project/<project_id>
GET /api/v1/stats/session/<session_id>
```
**Status:** Phase 3 (needs implementation)

#### Template API
```
GET /api/v1/templates
GET /api/v1/templates/<name>
POST /api/v1/projects?template=<name>
```
**Status:** Phase 2 (needs implementation)

---

## Development Priority Summary

### Recommended Order
1. **Week 1:** `/config`, `/theme`, `/format`, `/save` (quick wins)
2. **Week 2:** `/export`, `/session note`, `/session bookmark` (API-backed)
3. **Week 3:** `/stats`, `/search`, `/filter` (analytics)
4. **Week 4+:** `/wizard`, `/insights`, `/template` (polish)

### Effort & Impact Matrix

| Command | Effort | Impact | Priority |
|---------|--------|--------|----------|
| /config | 🟢 Low | 🟡 Medium | NOW |
| /theme | 🟢 Low | 🟡 Medium | NOW |
| /format | 🟢 Low | 🟡 Medium | NOW |
| /save | 🟢 Low | 🟢 High | NOW |
| /export | 🟡 Med | 🟢 High | NEXT |
| /session note | 🟡 Med | 🟢 High | NEXT |
| /template | 🟡 Med | 🟢 High | NEXT |
| /stats | 🟡 Med | 🟡 Medium | SOON |
| /search | 🔴 High | 🟡 Medium | LATER |
| /wizard | 🟡 Med | 🔵 Low | POLISH |
| /insights | 🟡 Med | 🔵 Low | POLISH |
| /filter | 🟡 Med | 🔵 Low | POLISH |

---

## Next Steps

### For CLI Enhancement:
1. **Implement Priority 1** commands (no backend needed)
   - /config, /theme, /format, /save
   - Effort: ~8 hours
   - Can start immediately

2. **Create backend APIs** (from Phase 2)
   - Export endpoints
   - Session enhancement endpoints
   - Template endpoints
   - Effort: ~30 hours

3. **Implement Priority 2** commands
   - /export, /session note, /session bookmark
   - Effort: ~20 hours

4. **Implement remaining** commands (Priority 3)
   - Based on schedule and need

---

## Files to Update

### Main CLI File
- `Socrates.py` - Add new cmd_* methods and handle_command updates

### New Helper Classes (Optional)
- Create `cli_helpers.py` for config management, themes, formatting
- Create `cli_formatters.py` for different output formats

### Tests
- `backend/tests/test_cli.py` - Add tests for new commands
- Create new test file for each major command group

---

## Success Criteria

- [ ] All Priority 1 commands implemented (4 commands, 8 hours)
- [ ] All Priority 2 commands implemented (6 commands, 20 hours)
- [ ] Tests passing for all new commands
- [ ] Help text updated
- [ ] No regressions in existing commands
- [ ] CLI commands = 27+ (from current 13)

---

**End of CLI_FUNCTIONS_AUDIT.md**

# Priority 3 Implementation - Quick Reference

## Commands at a Glance

| Command | Purpose | Auth | State | API Calls | Complexity |
|---------|---------|------|-------|-----------|------------|
| `/insights` | Gap/risk/opportunity analysis | ✓ | Project | 1 | Medium |
| `/wizard` | Interactive project setup | ✓ | Creates | 3-4 | High |
| `/search <q>` | Full-text search | ✓ | None | 1 | Low |
| `/filter [t] [c]` | Filter specs/questions | ✓ | Project | 0-1 | Low |
| `/resume <id>` | Resume session | ✓ | Session | 1-2 | Medium |
| `/status` | Show current state | ✓ | None | 0 | Low |

**Legend:** Auth=Authentication required, State=State change, Complexity=Implementation difficulty

---

## Critical Dependencies

### Must Have Already
- ✅ `/api/v1/search` - Search endpoint
- ✅ `/api/v1/insights/{project_id}` - Insights endpoint
- ✅ `/api/v1/templates` - Template list
- ✅ `/api/v1/templates/{id}` - Template details
- ✅ `/api/v1/templates/{id}/apply` - Apply template

### May Need to Add
- ⚠️ `/api/v1/sessions/{id}` - Get session details (might exist)
- ⚠️ Session resume endpoint - Status update for session

---

## API Methods to Add to SocratesAPI

```python
# Required methods (in Socrates.py SocratesAPI class)
def search(query, resource_type=None, category=None, skip=0, limit=20)
def get_insights(project_id, insight_type=None)
def list_templates(skip=0, limit=20, industry=None, tags=None)
def get_template(template_id)
def apply_template(template_id, project_id)
def get_session(session_id)
def list_recent_sessions(skip=0, limit=20)
```

**Lines of code:** ~100-150 lines

---

## CLI Command Methods to Add

```python
# Required commands (in Socrates.py SocratesCLI class)
def cmd_insights(args)
def cmd_wizard(args)
def cmd_search(args)
def cmd_filter(args)
def cmd_resume(args)
def cmd_status(args)

# Required helpers
def _display_insights(result)
def _display_search_results(result)
def _display_filtered_results(results, is_spec)
def _display_project_status(project)
def _display_session_status(session)
def _display_next_steps()
def _display_project_created(project, template_id)
def _wizard_select_template()
def _show_recent_sessions()
```

**Lines of code:** ~600-800 lines

---

## Database Models Required

| Model | Key Fields | For Commands |
|-------|-----------|--------------|
| Project | id, name, creator_id, owner_id, current_phase, status, maturity_score | All |
| Session | id, project_id, mode, status, started_at, ended_at | /resume, /status |
| Specification | id, project_id, category, content, confidence, is_current | /insights, /filter, /search |
| Question | id, project_id, session_id, text, category | /search, /filter |

**All models already exist** ✓

---

## Validation Patterns

```python
# Pattern 1: Authentication required
if not self.ensure_authenticated():
    return

# Pattern 2: Project required
if not self.ensure_project_selected():
    return

# Pattern 3: Session required
if not self.ensure_session_active():
    return

# Pattern 4: Argument parsing
project_id = args[0] if args else self.current_project["id"] if self.current_project else None
if not project_id:
    self.console.print("[yellow]Help message[/yellow]")
    return
```

---

## Display Format Templates

### Insights
```
[GAPS] [RISKS] [OPPORTUNITIES]
├─ Items grouped by type
├─ Color coded (red/yellow/green)
└─ Summary statistics at bottom
```

### Search Results
```
[PROJECT] Title
  Description
  └ /project select id

[SPECIFICATION] Title
  Category: ...
  Content: ...
  └ /project select project_id
```

### Filter Results
```
Category: X (N items)
├─ Item 1 | Source | Confidence
├─ Item 2 | Source | Confidence
└─ ...
```

### Status
```
[PROJECT STATUS]
Name, Phase, Maturity, Created, Specs count by category

[SESSION STATUS]
ID, Mode, Duration, Questions asked

[NEXT STEPS]
→ Suggested commands based on state
```

---

## Error Handling Checklist

- [ ] 401 Unauthorized → "Please /login or /register"
- [ ] 403 Forbidden → "Project belongs to different user"
- [ ] 404 Not Found → "Item not found, try /projects to list"
- [ ] 400 Bad Request → "Invalid input, Usage: ..."
- [ ] 500 Server Error → "Server error, please try again"
- [ ] Network Error → "Cannot connect to API, is server running?"

---

## Testing Strategy

### Unit Tests Required
- Each command with valid input
- Each command with missing args
- Each command with invalid args
- Error cases (API errors, network errors)
- Display formatting

**Test file:** `test_cli_priority3_commands.py`

**Estimated tests:** 30-40 test cases

---

## File Modifications Summary

| File | Changes | Lines |
|------|---------|-------|
| Socrates.py | API methods + CLI commands + helpers | +700-900 |
| test_cli_priority3_commands.py | New test file | +500 |
| PRIORITY3_ANALYSIS.md | This comprehensive analysis | Reference |

---

## Implementation Order

### Phase 1: Setup (30 min)
1. Add API wrapper methods to SocratesAPI
2. Update help text
3. Register commands in handle_command()

### Phase 2: Commands (3-4 hours)
1. `/search` - Simplest, no state change
2. `/status` - No API calls, just display
3. `/insights` - Display formatting
4. `/filter` - Similar to insights
5. `/resume` - Session state management
6. `/wizard` - Most complex, interactive

### Phase 3: Testing (2-3 hours)
1. Unit tests for each command
2. Integration tests
3. Error handling tests

### Phase 4: Polish (1 hour)
1. Color schemes
2. Help text refinement
3. Edge cases

---

## Success Criteria

- [ ] All 6 commands implemented
- [ ] API integration tested
- [ ] Error handling for all cases
- [ ] Help text updated
- [ ] Unit tests passing
- [ ] Display formatting matches mockups
- [ ] State management working (wizard, resume)
- [ ] No breaking changes to existing commands

---

## Notes

1. **Backend endpoints already exist** - No backend changes needed
2. **Database models already exist** - All necessary models in place
3. **CLI patterns established** - Follow existing patterns in Socrates.py
4. **Rich library available** - Use Panel, Table, Syntax for formatting
5. **Error handling patterns** - Use existing try/except patterns

---

## Estimated Timeline

- **Development:** 6-8 hours
- **Testing:** 2-3 hours
- **Review:** 1-2 hours
- **Total:** 9-13 hours

**Note:** Assumes backend endpoints are functioning correctly


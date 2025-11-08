# Socrates CLI - Improvements & Enhancement Plan

**Document Status:** Reference Guide for CLI Development
**Created:** November 8, 2025
**Priority:** User Experience & Usability Enhancements

---

## Overview

The Socrates CLI currently functions as a command-line interface for specification gathering and project management. This document outlines required improvements to enhance user experience, navigation, and data management capabilities.

---

## Current State vs. Desired State

### Authentication Flow

**Current:**
- Authentication always starts with email/password input
- No direct chat option from main menu
- No "back" button to previous menu

**Desired:**
- Main menu screen with options to:
  - Register
  - Login
  - Direct Chat (guest/anonymous mode)
  - Exit
- Ability to return to main menu from anywhere
- Remember user preference (registered vs guest)

---

## Priority 1: Navigation System (High Priority)

### 1.1 Main Menu with Arrow Navigation

**Current Behavior:**
- Commands entered as text (e.g., `/register`, `/login`, `/projects`)
- No visual menu system
- User must know commands

**Desired Behavior:**
```
╔════════════════════════════════════════════╗
║          SOCRATES - MAIN MENU              ║
╠════════════════════════════════════════════╣
║                                            ║
║   ➤ Register Account                       ║
║     Login                                  ║
║     Direct Chat (No Account)               ║
║     Exit                                   ║
║                                            ║
║   Use ↑/↓ arrows to navigate, ENTER to select
║   Type 'help' for command list             ║
╚════════════════════════════════════════════╝
```

**Implementation:**
- Use `inquirer` or `prompt_toolkit` selection menus
- Support arrow keys (↑/↓) for navigation
- Highlight current selection
- Display keyboard shortcuts

---

### 1.2 Context-Aware Navigation (Back Button)

**Current Behavior:**
- User stuck in submenus
- No way to return to previous menu level
- Awkward command-based navigation

**Desired Behavior:**
- Every menu should have:
  - Previous option at bottom (`↑ Back to Previous Menu`)
  - Main Menu shortcut (e.g., `Home` or `0`)
  - Current context displayed (breadcrumb)

**Example Breadcrumb:**
```
Home > Projects > My Project > Sessions > Session 1
```

**Implementation:**
- Maintain navigation stack
- Show breadcrumb at top of every screen
- Add `[0] Main Menu`, `[b] Back` shortcuts
- Confirm destructive actions before returning

---

### 1.3 Menu Structure

**Proposed Hierarchy:**

```
MAIN MENU
├── Register Account
├── Login
│   └── Project Dashboard
│       ├── List Projects
│       ├── Create Project
│       ├── View Project
│       │   ├── View Details
│       │   ├── Start Session
│       │   ├── View Sessions
│       │   ├── Edit Project
│       │   └── Delete Project
│       └── Manage Account
│           ├── View Profile
│           ├── Change Password
│           └── Logout
├── Direct Chat (Anonymous)
│   ├── Create Temporary Session
│   ├── Chat Interface
│   └── Export Chat
└── Exit
```

---

## Priority 2: Input Validation & Security (High Priority)

### 2.1 Password Masking with Visual Feedback

**Current Behavior:**
- Password input appears as plain text OR no feedback
- User cannot see if they're actually typing
- No character count indicator

**Desired Behavior:**
- Show `*` or `•` for each character typed in real-time
- Show character count: `Password (12/64 characters)`
- Password strength indicator:
  ```
  Password Strength: ████░░░░░░ (Medium)
  ✓ 8+ characters
  ✓ Contains uppercase
  ✗ Contains numbers
  ✗ Contains special chars
  ```

**Implementation:**
```python
def get_password_input(prompt: str = "Password", min_length: int = 8) -> str:
    """Get password input with masking and feedback"""
    # Use getpass with custom handling
    # Show • for each character
    # Display strength meter
    # Validate length and complexity
```

---

### 2.2 Email Validation

**Current Behavior:**
- Basic email validation (if any)
- No feedback on invalid format

**Desired Behavior:**
- Real-time email validation as user types
- Helpful error messages:
  ```
  ✗ Invalid email format
  Expected: username@domain.com
  ```
- Suggest common domain corrections:
  ```
  Did you mean: user@gmail.com?  [Y/n]
  ```

---

### 2.3 Input Confirmation for Important Actions

**Current Behavior:**
- No confirmation for delete operations
- Data loss possible

**Desired Behavior:**
```
Are you sure you want to DELETE this project?
This action cannot be undone.

Name: My Project
Sessions: 5
Specifications: 23

Type the project name to confirm: ___________
Or press CTRL+C to cancel
```

---

## Priority 3: Data Management Operations (High Priority)

### 3.1 Project Deletion

**Current State:** NOT IMPLEMENTED in CLI
**API Available:** ✓ DELETE `/api/v1/projects/{project_id}`

**Desired Implementation:**
```
1. List projects with selection
2. Show project summary (sessions, specs, creation date)
3. Double-confirm deletion (show name/ID)
4. Archive option: "Archive project instead of delete? [Y/n]"
5. Confirmation message with backup info
```

---

### 3.2 Session Deletion/Cleanup

**Current State:** NOT IMPLEMENTED in CLI
**API Available:** ✗ DELETE endpoint for sessions (needs backend implementation)

**Desired Implementation:**
```
1. List sessions for a project
2. Show session stats (duration, questions asked, specs extracted)
3. Option to:
   - Delete session completely
   - Archive session (for records)
   - Export session (JSON/PDF)
4. Bulk delete old sessions: "Delete sessions older than 30 days? [Y/n]"
```

**Backend Work Required:**
- Add DELETE endpoint: `/api/v1/sessions/{session_id}`
- Implement soft delete (archive) vs hard delete
- Add cascade rules for associated questions/specs

---

### 3.3 User Account Deletion

**Current State:** NOT IMPLEMENTED in CLI
**API Available:** ✗ DELETE endpoint for users (needs backend implementation)

**Desired Implementation:**
```
1. Confirm current user via password
2. Show impact:
   - Projects: 5
   - Sessions: 23
   - Specifications: 156
3. Export options:
   - "Export all data before deletion? [Y/n]"
4. Delete or keep data:
   - [1] Delete account & all data
   - [2] Delete account, keep projects as "legacy"
   - [3] Cancel deletion
5. Final warning with 10-second countdown
```

**Backend Work Required:**
- Add DELETE endpoint: `/api/v1/users/{user_id}`
- Implement account deletion policies
- Add data export capability
- Implement cascade deletion rules

---

## Priority 4: Direct Chat / Guest Mode (Medium Priority)

### 4.1 Anonymous Chat Option

**Current State:** API endpoint exists, CLI doesn't expose it

**Desired Implementation:**
```
MAIN MENU
├── ...
├── Direct Chat (No Account Required)
│   ├── Create temporary chat session
│   ├── Chat interface with auto-save
│   ├── Export chat to file
│   └── Copy chat to clipboard
└── ...
```

**User Flow:**
```
[Select] Direct Chat
  └─→ Start session (auto-create temporary project)
      └─→ Chat interface:
          - Left: Chat history
          - Right: Send message / Options
          - Bottom: Mode toggle (Socratic ↔ Direct)
          - Options: [Export] [Copy] [Save] [Exit]
```

---

### 4.2 Chat Interface Improvements

**Current State:** Basic text input/output

**Desired State:**
```
╔═══════════════════════════════════════════════════════╗
║ Project: My AI App | Session: 001 | Questions: 12    ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║ Assistant: What problem are you solving?             ║
║ [13:45] → Goals category (88% coverage)             ║
║                                                       ║
║ You: I want to build a task management app           ║
║                                                       ║
║ Assistant: Great! Are your users teams or...?        ║
║ [13:46] → Requirements category (45% coverage)       ║
║                                                       ║
║                                                       ║
║ Type message (or /help for commands)                 ║
║ >>> [________________________________] [Send] [Menu] ║
║                                                       ║
║ [M] Menu [H] History [E] Export [S] Save [Q] Quit   ║
╚═══════════════════════════════════════════════════════╝
```

**Features:**
- Timestamps for each message
- Category tags showing coverage
- Rich formatting (bold, italics, code blocks)
- Inline quick actions

---

## Priority 5: Session & Project Management (Medium Priority)

### 5.1 Enhanced Session View

**Current State:** Basic list

**Desired State:**
```
╔════════════════════════════════════════════════════════╗
║ Session Management - My Project                       ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Session ID    │ Start Time  │ Questions │ Status     ║
║ ──────────────┼─────────────┼───────────┼────────    ║
║ sess_001      │ 2025-11-08  │ 12        │ Active     ║
║ sess_002      │ 2025-11-07  │ 15        │ Completed  ║
║ sess_003      │ 2025-11-06  │ 8         │ Abandoned  ║
║                                                        ║
║ Selected: sess_001 (Active)                          ║
║ ➤ Continue Session                                    ║
║   View History                                        ║
║   Export Session                                      ║
║   Archive Session                                     ║
║   Delete Session                                      ║
║   Back to Project                                     ║
╚════════════════════════════════════════════════════════╝
```

---

### 5.2 Project Overview Dashboard

**Current State:** Basic list of projects

**Desired State:**
```
╔═══════════════════════════════════════════════════════════╗
║ Projects Dashboard                                        ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║ My AI App [████████░░ 80% complete]                      ║
║   Created: 2025-11-01  |  Sessions: 5  |  Specs: 23     ║
║   Status: Active                                         ║
║   ➤ Continue  [A]rchive  [E]xport  [E]dit  [D]elete    ║
║                                                           ║
║ Legacy Project [██░░░░░░░░ 20% complete]                ║
║   Created: 2025-10-01  |  Sessions: 2  |  Specs: 4      ║
║   Status: Archived                                       ║
║   [R]estore  [E]xport  [D]elete                         ║
║                                                           ║
║ ✚ Create New Project                                     ║
║                                                           ║
║ [H] Home  [F] Filter  [S] Sort  [Q] Quit              ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Priority 6: Data Export & Import (Low Priority)

### 6.1 Export Options

**Desired Implementation:**

From any context (session, project), user should be able to:
- Export as JSON (raw data)
- Export as Markdown (formatted notes)
- Export as PDF (formatted document)
- Export as CSV (spreadsheet)
- Copy to clipboard

---

### 6.2 Import Options

**Desired Implementation:**

- Import previous session data
- Import project template
- Bulk create projects from CSV

---

## Technical Implementation Notes

### Libraries to Consider

```python
# Navigation & Menus
inquirer              # Interactive CLI menus (↑/↓ arrows, selections)
rich.prompt           # Enhanced prompts with validation
prompt_toolkit        # Advanced input handling (history, completion)

# Input Handling
getpass              # Secure password input (built-in)
wcwidth              # Terminal width handling
windows_curses       # Windows terminal support (if needed)

# Data Handling
tabulate             # Pretty table formatting
json                 # JSON export (built-in)
csv                  # CSV export (built-in)
markdown             # Markdown generation

# Optional UI
textual              # Full TUI framework (advanced)
curses               # Terminal control (complex)
```

---

## Implementation Phases

### Phase 1: Foundation (Priority 1)
1. Navigation menu system
2. Back button / context awareness
3. Breadcrumb navigation
4. Password masking

**Estimated:** 2-3 days
**Impact:** Huge UX improvement

---

### Phase 2: Data Management (Priority 2-3)
1. Project deletion
2. Session deletion
3. User account deletion (backend + CLI)
4. Confirmation dialogs

**Estimated:** 2-3 days
**Impact:** Critical for data management

---

### Phase 3: Features (Priority 4-5)
1. Direct chat / anonymous mode
2. Enhanced session/project views
3. Export functionality

**Estimated:** 2-3 days
**Impact:** Feature parity with other tools

---

### Phase 4: Polish (Priority 6)
1. Data import
2. Template system
3. Advanced analytics

**Estimated:** TBD
**Impact:** Nice-to-have features

---

## Acceptance Criteria

### Navigation (Phase 1)
- [ ] Main menu displays with arrow key navigation
- [ ] User can navigate back from any submenu
- [ ] Breadcrumb shows current location
- [ ] All commands accessible via menu
- [ ] Password input shows asterisks in real-time

### Data Management (Phase 2)
- [ ] User can delete projects with confirmation
- [ ] User can delete sessions with confirmation
- [ ] User can delete account with confirmation
- [ ] Deleted data shows clear confirmation message
- [ ] Archive option available for projects/sessions

### Direct Chat (Phase 3)
- [ ] Anonymous users can start chat without account
- [ ] Chat interface works without registration
- [ ] Chat can be exported to file
- [ ] Session mode can toggle (Socratic ↔ Direct)

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Test navigation in all menus
- [ ] Test back button at each level
- [ ] Test password masking with different inputs
- [ ] Test deletion confirmations
- [ ] Test with and without auth
- [ ] Test on Windows, macOS, Linux terminals

### Automated Testing
- [ ] Unit tests for menu navigation logic
- [ ] Unit tests for input validation
- [ ] Integration tests for API calls
- [ ] E2E tests for complete workflows

---

## Backward Compatibility

**Current Command-Based Interface:**
- Keep all existing `/command` support
- Add menu as alternative interface
- User choice: interactive menu OR command mode
- Default to interactive menu, allow opt-out

---

## Future Considerations

1. **Themes:** Dark/light mode for CLI
2. **Accessibility:** Screen reader support
3. **Internationalization:** Multi-language support
4. **Session Recovery:** Resume interrupted sessions
5. **Offline Mode:** Cache and sync when reconnected

---

## Questions & Decisions Needed

1. Should deleted projects/sessions be recoverable (soft delete)?
2. Should there be an admin mode for managing all users?
3. Should chat history be preserved across sessions?
4. What's the retention policy for archived data?
5. Should we implement rate limiting in CLI?

---

## Related Issues & Dependencies

- **Backend:** Need DELETE endpoints for sessions and users
- **API:** Need soft delete / archive capability
- **Database:** Need to handle cascading deletes
- **Config:** Need to add CLI preferences/settings

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-08 | 1.0 | Initial comprehensive CLI improvement plan |


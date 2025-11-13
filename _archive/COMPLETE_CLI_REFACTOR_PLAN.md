# Complete CLI Refactor Plan: Modular, Domain-Aware, Team-First

## Executive Summary

Transform Socrates CLI from **3000-line monolith** into **modular, domain-aware, team-first system** that equally supports:
- ✅ Solo developers building software
- ✅ Teams designing products
- ✅ Business teams planning strategy
- ✅ Researchers analyzing markets
- ✅ Anyone doing structured thinking

## The Vision

### Before: Code-Centric, Monolithic
```
Socrates.py (3000+ lines)
  └─ Designed for: Developers generating code
  └─ Usage: Solo projects mostly
  └─ Usability: Hard to add features
  └─ Team support: Afterthought
```

### After: Domain-Aware, Modular, Team-Friendly
```
Socrates.py (250 lines entry point)
  ↓
cli/commands/ (modular by feature)
  ├─ Supports: Developers, Teams, Designers, Business, Researchers
  ├─ Usage: Solo AND team projects equally
  ├─ Usability: Add new feature in minutes
  ├─ Team support: Built-in from start
```

---

## Three Key Architectures Working Together

### 1. MODULAR ARCHITECTURE (How CLI is Organized)

**Problem Solved:** Monolithic code is unmaintainable

**Solution:**
```
cli/commands/
├── auth.py (50 lines)
├── projects.py (120 lines) ← domain-aware project creation
├── teams.py (80 lines) ← team management
├── collaboration.py (80 lines) ← team features
├── sessions.py (120 lines) ← domain-specific sessions
├── domain.py (80 lines) ← domain discovery
├── template.py (80 lines) ← template browsing/applying
├── documents.py (100 lines)
├── specifications.py (100 lines)
├── code_generation.py (80 lines)
├── export.py (80 lines) ← domain-specific export formats
└── ...20+ more modules, each ~80-150 lines
```

**Benefits:**
- Each command easy to understand
- Easy to add new features
- Can test in isolation
- Parallel development possible

**Implementation:**
- CommandHandler base class
- CommandRegistry for auto-discovery
- Shared utils in cli/utils/

### 2. DOMAIN-AWARE ARCHITECTURE (Supporting Non-Coding Projects)

**Problem Solved:** Platform only worked for code projects

**Solution:**
```
Available Domains:
├── Programming (code generation, technical specs)
├── Business (business plans, strategies)
├── Design (product specs, design guidelines)
├── Research (analyses, reports)
└── Marketing (campaigns, positioning)
```

**Where Domain Awareness Lives:**

**1. Project Creation** (domain-aware from start)
```
/project create
→ Pick domain or template
→ Socrates customizes experience for that domain
```

**2. Session Workflows** (domain-specific questions)
```
/session start
→ Ask which domain
→ Load domain-specific question sets
→ Questions match domain context
```

**3. Output Formats** (domain-specific exports)
```
Business domain exports: markdown (plan), PDF (presentation), JSON
Design domain exports: markdown (spec), Figma (future), PDF
Research domain exports: markdown (report), PDF, HTML
Programming domain exports: code (.zip), markdown (specs), PDF
```

**4. Templates** (pre-built for domains)
```
/template list
→ Group by domain
→ Business: startup plan, product launch, market analysis
→ Design: product redesign, UX research
→ Research: competitive analysis, market research
```

**5. Workflows** (domain-specific processes)
```
/workflow list [domain]
→ Business domain workflows: strategy planning, market entry
→ Design domain workflows: product design thinking, UX research
→ Programming domain workflows: code generation, technical specs
```

**Benefits:**
- Equally good for business and coding projects
- Customized experience per project type
- Appropriate questions and outputs
- Same platform, different contexts

### 3. TEAM-FIRST ARCHITECTURE (Supporting Collaboration)

**Problem Solved:** Team collaboration was secondary feature

**Solution:** Team commands as core feature alongside solo workflows

**Team Features Built Into Every Workflow:**

**1. Team Management** (Core feature)
```
/team create "Product Team"
/team invite email@company.com
/team member list
/team info <team_id>
```

**2. Project Sharing** (Automatic with teams)
```
/project create
→ "Working solo or with team? [solo/team]"
→ If team: auto-share with team members
→ Everyone has access, can collaborate
```

**3. Collaborative Sessions** (Real-time teamwork)
```
/session start
→ If project is team-owned
→ Show active team members
→ Contributions visible to all
→ Can see who answered which question
```

**4. Activity/Collaboration Status**
```
/collaboration status [project_id]
→ Who's online right now?
→ What are they working on?
→ Recent contributions
→ Shared updates
```

**5. Role-Based Access**
```
Roles: Owner, Contributor, Reviewer
→ Each has appropriate permissions
→ Configured at team creation
→ Can change per project
```

**Benefits:**
- Teams can use Socrates from day 1
- No separate "team mode"
- Solo and team seamlessly mixed
- Easy to grow from solo to team

---

## Complete User Journey Examples

### Solo User: Business Planning
```
1. /domain list
   → "Let me explore available domains"
   → Sees Business domain option

2. /template list business
   → "Let me see business templates"
   → Finds "Startup Business Plan"

3. /project create
   → Uses template: "Startup Business Plan"
   → Domain: Business (auto-selected)
   → Name: "My SaaS Idea"
   → Solo project created

4. /session start
   → Domain: Business (auto-set)
   → Workflow: Startup Planning (from template)
   → Socratic mode: AI asks business questions

5. AI: "What problem does your product solve?"
   User: "Small businesses struggle with scheduling"

6. AI: "Who would pay to solve this?"
   User: "Restaurant owners"

7. ...continues with business-specific questions...

8. /specification list
   → Shows building business plan specification

9. /export markdown my-saas-idea
   → Generates: Business_Plan_SaaS.md
   → Contains: Market analysis, business model, go-to-market
```

### Team: Product Design Collaboration
```
1. User A: /team create "Design Team"
   → Team created with ID team_xyz
   → Generates invite code

2. User A: /team invite alice@company.com team_xyz
   User A: /team invite bob@company.com team_xyz
   → Invitations sent

3. All three users accept and join team

4. User A: /project create
   → Select template: "Product Design"
   → Team: Design Team
   → Project auto-shared with Alice & Bob

5. All three users: /session start
   → Same project, collaborative session
   → See each other online
   → Contribute answers to same questions

6. AI: "What user problem are we solving?"
   → All can answer, see each other's thoughts
   → Build shared understanding

7. /collaboration status
   → Shows all three online
   → Shows Alice answered q1, q2
   → Shows Bob answered q3, q5
   → Shows User A answered q4, q6

8. /specification list
   → Design spec building in real-time
   → Sections assigned to team members

9. /project export pdf product-design
   → Final design spec
   → Shows all contributors
   → Professional format ready to present
```

### Developer: Code Generation
```
1. /domain list
   → Sees Programming domain

2. /template list programming
   → Sees code generation templates
   → Selects "REST API"

3. /project create
   → Uses template
   → Domain: Programming
   → Name: "User Management API"

4. /session start
   → Domain: Programming
   → Workflow: Code Generation
   → Socratic mode

5. AI: "What entities do you need?"
   User: "Users, Teams, Permissions"

6. AI: "What are the CRUD operations?"
   User: "Create, Read, Update, Delete teams"

7. ...continues with technical questions...

8. /export code my-api
   → Generates complete API codebase
   → Download: api.zip
   → Fully functional, ready to use
```

---

## Implementation Strategy

### Phase 1: Modular Infrastructure (2-3 hours)
- [ ] Create `cli/base.py` (CommandHandler)
- [ ] Create `cli/registry.py` (CommandRegistry)
- [ ] Create `cli/utils/` shared utilities
- [ ] Refactor Socrates.py to ~250 lines

### Phase 2: Migrate Existing + Add Core (2-3 hours)
- [ ] Migrate auth → `cli/commands/auth.py`
- [ ] Migrate projects → `cli/commands/projects.py` + domain-awareness
- [ ] Migrate sessions → `cli/commands/sessions.py` + domain-awareness
- [ ] Add domain → `cli/commands/domain.py`
- [ ] Add template → `cli/commands/template.py`
- [ ] Add teams → `cli/commands/teams.py`
- [ ] Add collaboration → `cli/commands/collaboration.py`

### Phase 3: Core Features (3-4 hours)
- [ ] Enhanced documents → `cli/commands/documents.py`
- [ ] Enhanced specifications → `cli/commands/specifications.py`
- [ ] Enhanced workflows → `cli/commands/workflows.py`
- [ ] Enhanced export → `cli/commands/export.py` (domain-specific formats)
- [ ] Add questions → `cli/commands/questions.py`
- [ ] Add code generation → `cli/commands/code_generation.py`

### Phase 4: Advanced (2-3 hours)
- [ ] Admin → `cli/commands/admin.py`
- [ ] Analytics → `cli/commands/analytics.py`
- [ ] Quality → `cli/commands/quality.py`
- [ ] Notifications → `cli/commands/notifications.py`
- [ ] Conflicts → `cli/commands/conflicts.py`

### Phase 5: Polish (1-2 hours)
- [ ] Test all 150+ endpoints
- [ ] Comprehensive help system
- [ ] Error handling across all commands
- [ ] End-to-end workflows for each domain

**Total: 14-20 hours**

---

## Context Management for Domain & Team

CLI state needs to track:

```python
{
    "user": {...},
    "current_project": {
        "id": "...",
        "domain": "business",      # ← DOMAIN
        "team_id": "...",          # ← TEAM
        "template": "startup_plan"
    },
    "current_team": {...},         # ← TEAM CONTEXT
    "current_session": {
        "id": "...",
        "domain": "business",      # ← DOMAIN FOR THIS SESSION
        "workflow": "startup_planning",
        "mode": "socratic"
    }
}
```

**How handlers access context:**
```python
class SessionCommandHandler(CommandHandler):
    def handle(self, args):
        # Access domain from config
        project = self.config.get("current_project")
        domain = project.get("domain")

        # Load domain-specific questions
        questions = self.api.get_questions_for_domain(domain)

        # Start domain-specific session
        session = self.api.start_session(
            project_id=project["id"],
            domain=domain,
            questions=questions
        )
```

---

## File Structure

```
Socrates/
├── Socrates.py (250 lines - entry point only)
├── cli/
│   ├── __init__.py
│   ├── base.py (CommandHandler, ~100 lines)
│   ├── registry.py (CommandRegistry, ~150 lines)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── auth.py (~50 lines)
│   │   ├── projects.py (~120 lines) [domain-aware]
│   │   ├── teams.py (~80 lines)
│   │   ├── collaboration.py (~80 lines)
│   │   ├── domain.py (~80 lines)
│   │   ├── template.py (~80 lines)
│   │   ├── sessions.py (~120 lines) [domain-aware]
│   │   ├── documents.py (~100 lines)
│   │   ├── specifications.py (~100 lines)
│   │   ├── questions.py (~80 lines)
│   │   ├── workflows.py (~80 lines)
│   │   ├── code_generation.py (~80 lines)
│   │   ├── export.py (~100 lines) [domain-specific formats]
│   │   ├── admin.py (~60 lines)
│   │   ├── analytics.py (~70 lines)
│   │   ├── quality.py (~50 lines)
│   │   ├── notifications.py (~50 lines)
│   │   ├── conflicts.py (~60 lines)
│   │   ├── search.py (~50 lines)
│   │   ├── insights.py (~50 lines)
│   │   ├── github.py (~60 lines)
│   │   ├── config.py (~70 lines)
│   │   ├── system.py (~80 lines)
│   │   └── utils.py (~120 lines)
│   └── utils/
│       ├── __init__.py
│       ├── table_formatter.py (~50 lines)
│       ├── prompts.py (~80 lines)
│       ├── helpers.py (~80 lines)
│       └── constants.py (~80 lines)
├── cli_logger.py (existing)
└── API_ENDPOINT_MAP.md
   CLI_ARCHITECTURE_PLAN.md
   CLI_NON_CODING_PROJECTS.md
   COMPLETE_CLI_REFACTOR_PLAN.md (this file)
```

---

## Key Features by Command Module

### Domain-Aware Commands
- **domain.py**: List domains, show domain info, guide domain selection
- **template.py**: Browse templates by domain, apply templates
- **projects.py**: Create with domain selection, auto-share with teams
- **sessions.py**: Start domain-specific sessions, load domain questions
- **specifications.py**: Domain-specific spec types and formats
- **workflows.py**: Domain-specific workflow selection
- **export.py**: Domain-specific export formats

### Team-First Commands
- **teams.py**: Create, list, invite members, manage roles
- **collaboration.py**: Show team status, activity feed, contributions
- **projects.py**: Share projects with teams, manage access
- **sessions.py**: Show collaborative session participants

### Fully Modular & Testable
Each module:
- ~80-120 lines of code
- Single responsibility (one domain/feature)
- Can be tested independently
- Can be modified without affecting others
- Clear entry point via `handle()`

---

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **File Size** | 3000+ lines | 250 lines (main) + modular |
| **New Endpoint Time** | Edit main file | Create new command file |
| **Testing** | Hard (integrated) | Easy (isolated) |
| **Code Location** | Search 3000 lines | File name = command |
| **Team Support** | Secondary feature | First-class feature |
| **Non-Coding Projects** | Not supported | Equally supported |
| **Domain Awareness** | None | Full support |
| **Maintainability** | Poor (monolith) | Excellent (modular) |
| **Extensibility** | Difficult | Simple |

---

## Success Criteria

After complete implementation:
- ✅ All 150+ backend endpoints exposed in CLI
- ✅ Solo developers can generate code
- ✅ Solo users can plan business, design products
- ✅ Teams can collaborate seamlessly
- ✅ Domain selection easy from project creation
- ✅ Each command module < 120 lines
- ✅ Main Socrates.py < 300 lines
- ✅ Can add new command in < 10 minutes
- ✅ Same platform for all project types
- ✅ Ready to use as UI blueprint

---

## Next Steps

### For Approval
Please review:
1. ✅ CLI_IMPLEMENTATION_SUMMARY.md (quick overview)
2. ✅ CLI_ARCHITECTURE_PLAN.md (detailed design)
3. ✅ CLI_NON_CODING_PROJECTS.md (domain awareness)
4. ✅ COMPLETE_CLI_REFACTOR_PLAN.md (this document)

### Then Implementation
**Phase 1: Infrastructure** - Create modular system foundation
→ Will take 2-3 hours
→ Makes remaining work much faster
→ Everything else builds on this

Ready to proceed with Phase 1?

---

**Status:** Architecture complete, awaiting approval to implement
**Timeline:** 14-20 hours total development time
**Goal:** Socrates CLI as complete, testable, extensible interface for all project types

# SOCRATES - PROJECT VISION

**Version:** 2.0.0
**Status:** Vision Document (Core Document - Immutable)
**Last Updated:** November 3, 2025

---

## THE CORE PROBLEM SOCRATES SOLVES

Modern AI has three fundamental failures:

### Problem 1: Context Loss
Modern AI systems cannot keep context. They process forward and never look back. They cannot recall previous sessions or maintain comprehensive project specifications across time.

**Socrates Solution:** All context and specifications are persisted in a database. The system never forgets. A user can return to a project months later and the complete context is there—what was asked, what was answered, what conflicts were found, what decisions were made.

### Problem 2: Greedy Algorithmic Decisions
AI systems optimize locally (immediate step) without considering global costs (cascading effects). A "quick" decision that seems good now becomes expensive later when it requires rework.

**Socrates Solution:** The Quality Control system prevents greedy decisions by:
- Analyzing all possible solution paths
- Calculating TOTAL cost (direct cost + rework cost)
- Showing users ALL options before they choose
- Preventing obviously bad decisions from happening

### Problem 3: Incomplete Specifications
Specifications gathered through chat are often incomplete, vague, and conflicted. Missing requirements are discovered expensively during implementation.

**Socrates Solution:** The Socratic questioning engine gathers complete, specific specifications by:
- Asking questions from 7 different professional roles
- Making questions dynamic (more answers = more detailed questions)
- Detecting contradictions in real-time
- Identifying missing areas systematically
- Building solid context upfront

---

## WHAT IS SOCRATES?

**Socrates is a multi-agent AI system that solves the three problems above through:**

### 1. Persistent Context Management
- All questions, answers, context, and conflicts stored in database
- Cross-session access: return to project anytime and context is complete
- Never loses project knowledge

### 2. Dynamic Socratic Questioning Engine
- Asks questions from 7 professional roles (PM, BA, UX, Frontend, Backend, DBA, DevOps)
- Questions adapt based on user answers (broader answers = more detailed follow-ups)
- User can toggle between Socratic mode (guided questioning) and Direct Chat (tell us)
- System extracts specifications and context from every interaction

### 3. Conflict Detection & Resolution
- Automatically detects 4 types of conflicts:
  1. **Technology conflicts** (database/framework incompatibilities)
  2. **Requirement conflicts** (contradictory requirements)
  3. **Timeline conflicts** (oversubscribed schedule)
  4. **Resource conflicts** (insufficient team capacity)
- When conflict found: user is informed, shown resolution options, asked which spec/context to keep
- Database stays consistent (no contradictions)

### 4. Quality Control System
- Prevents greedy algorithmic decisions
- Before major action: analyzes all possible paths
- Shows users total cost (direct + rework) for each path
- Maturity threshold (60%): below = suggestions, above = mandatory choice
- Detects specific bad patterns (e.g., "tunnel vision": modifying tests to hide bugs instead of fixing them)

### 5. User Learning & Adaptation
- Tracks which questions work best for each user
- Learns communication preferences (technical vs business, detailed vs brief)
- Learns expertise level and focuses areas
- Adapts future interactions based on patterns
- Different users get different questions based on learned profile

### 6. Team Collaboration
- Different roles get different questions (PM gets timeline/business questions, Dev gets technical questions)
- Detects conflicts between team member answers
- Asks conflicting members to decide, database reflects agreed specs
- Role-based access control (Owner, Lead, Developer, Viewer)

### 7. Project Generation Foundation
- All specifications and context feed into project generation
- Backend generates architecture, file structure, code
- Quality of generated project depends on quality of specs
- Better specs = better generated code

### 8. IDE & GitHub Integration
- Like Claude Code: can integrate with user's IDE
- Can access GitHub repositories (clone, analyze, reference)
- Can debug projects (identify issues, suggest fixes)
- Extends Socratic method into actual development

### 9. Knowledge Base Per Project
- Users can upload documents as reference materials
- System has context of uploaded documents
- Socratic questions can reference these materials
- Team can share knowledge base

### 10. Multi-LLM Support
- Connect to different LLM providers (Claude, OpenAI, Gemini, Ollama)
- User can choose preferred provider
- Can use local models (Ollama)
- System doesn't depend on single LLM

---

## WHAT SOCRATES IS NOT

❌ A simple chatbot
❌ A code generator that doesn't understand context
❌ A tool that loses information between sessions
❌ A system that makes greedy decisions
❌ A one-size-fits-all approach
❌ A substitute for thinking (enables better thinking)
❌ A system that ignores conflicts

---

## CORE WORKFLOW: 4 PHASES

### Phase 1: Discovery
- User describes what they want to build (high-level)
- System asks clarifying questions (Socratic mode or Direct Chat)
- User answers, providing details
- System extracts context, specifications, assumptions
- Quality system identifies coverage gaps

### Phase 2: Conflict Resolution
- As specs accumulate, system detects conflicts
- When conflict found: user informed, shown options, asked to decide
- Database updated with agreed specs (no contradictions)
- User can proceed to next phase or continue gathering specs

### Phase 3: Quality Review
- User sees summary: what specs are gathered, what maturity level achieved
- Quality system shows: coverage across 10 critical areas, detected conflicts, open assumptions
- If maturity < 60%: system SUGGESTS next steps
- If maturity ≥ 60%: system ASKS user to choose between paths
- User decides: continue gathering specs, or proceed to generation

### Phase 4: Project Generation
- User confirms they want to generate project
- All specs and context used to generate:
  - Architectural structure
  - Technology choices justified
  - File structure
  - Code implementation
  - Configuration files
- Generated project reflects all decisions captured during phases 1-3

---

## HOW IT WORKS: THE SOCRATIC METHOD

**Socratic questioning is systematic and dynamic:**

1. System asks question based on role and project type
2. User answers (brief or detailed)
3. System analyzes answer:
   - Extract specification/context
   - Measure completeness (0-1 scale)
   - Detect vague language
   - Identify gaps
4. System adapts:
   - Broad answer = ask more specific follow-ups
   - Vague answer = ask for examples/clarification
   - Contradictions detected = flag for user
5. Context accumulates: every question and answer stored in database
6. Learning happens: system learns what questions work for this user
7. Repeat until specifications are complete and solid

---

## KEY NON-NEGOTIABLE FEATURES

These features MUST exist or Socrates is not Socrates:

1. ✅ **Persistent Context** - Nothing is forgotten, all specs stored in database
2. ✅ **Conflict Detection** - 4 types detected automatically on every spec change
3. ✅ **Quality Control** - Prevents greedy decisions, shows all paths with costs
4. ✅ **Socratic Questioning** - Dynamic, role-based, user-adaptive
5. ✅ **Toggle Modes** - Can switch between Socratic (guided) and Direct Chat (flexible)
6. ✅ **4 Phases** - Discovery → Conflict Resolution → Quality Review → Generation
7. ✅ **User Learning** - System adapts to individual user patterns
8. ✅ **Team Collaboration** - Different roles, conflict resolution between team members
9. ✅ **Project Generation** - All specs feed into project code generation
10. ✅ **Multi-LLM Support** - Not tied to single LLM provider

---

## FUNDAMENTAL PRINCIPLES

### Principle 1: Never Lose Information
Once a specification is captured, it stays in the database. Users can reference it, update it, but it's never lost.

### Principle 2: Prevent Expensive Mistakes Early
Conflicts and gaps detected in the specification phase (cheap to fix) not the implementation phase (expensive to fix).

### Principle 3: User Controls Decisions
Quality system SHOWS users ALL options and costs. Users make informed decisions, not blind guesses.

### Principle 4: Context is King
Better context = better specifications = better generated code. Every interaction builds context.

### Principle 5: Team Alignment
Different perspectives (7 roles) ensure requirements are viewed from all angles. Team conflicts discovered early.

---

## WHAT WAS LEARNED FROM PREVIOUS FAILURES

**Socrates 8.0 was production-ready but didn't solve the core problems.** It was:
- ✓ A good chatbot interface
- ✗ Missing context persistence (couldn't recall across sessions)
- ✗ Missing conflict detection
- ✗ Missing quality control system
- ✗ Missing the Socratic method (was just chat)

**Socrates v2.0 must be different:**
- Solves context loss problem (persistent database)
- Solves greedy decision problem (quality control + path comparison)
- Solves incomplete specs problem (dynamic Socratic questioning)
- Integrates all features to support the core mission

---

## SUCCESS METRICS

Socrates is successful when:

1. **Context Persistence**: Users can return to project months later, all context is there
2. **Conflict Prevention**: Conflicts detected before implementation (not during)
3. **Cost Savings**: Projects cost less to develop (better specs = less rework)
4. **Quality Improvement**: Generated projects are higher quality (based on better specs)
5. **Team Alignment**: Team members agree on requirements (conflicts resolved early)
6. **User Adaptation**: System learns and gets better for each user over time
7. **Knowledge Preservation**: Team never loses project decisions/rationale

---

## SCOPE GUARDS

### What MUST be built first (MVP foundation):
- Authentication & user management
- Project & session management
- Socratic questioning engine (role-based, dynamic)
- Context/specification storage in database
- Basic conflict detection (4 types)
- Quality control system (path comparison, tunnel vision detection)
- Toggle between Socratic and Direct Chat modes

### What comes after MVP is solid:
- Advanced team collaboration features
- Project generation (architecture → code)
- IDE integration
- GitHub integration
- Knowledge base uploads
- Advanced user behavior learning

### What is explicitly NOT in scope initially:
- Beautiful UI (backend operational first)
- Advanced analytics
- Custom integrations
- Mobile apps
- Enterprise features (until later phases)

---

## IMPLEMENTATION PRINCIPLES

1. **Never Assume** - Verify assumptions by reading code and documentation
2. **Always Check** - Before making changes, verify against VISION.md
3. **Build One Feature Completely** - Don't start Phase 2 until Phase 1 is end-to-end working
4. **Test as You Build** - Integration tests between phases
5. **Document Decisions** - Why each architectural choice was made
6. **Reference This Document** - Every commit should reference what part of vision it implements

---

## THIS DOCUMENT IS IMMUTABLE

**This VISION.md defines what Socrates IS.** It should not change unless:
- Core problems change
- Fundamental approach changes
- You (the user) explicitly update it

If I propose changes that deviate from this document, you can stop me immediately by referencing the specific line.

---

**Last approved by:** User
**Date:** November 3, 2025
**Status:** LOCKED - This is the source of truth for all development decisions

---

## SESSION PROGRESS - NOVEMBER 4, 2025

### Discovery Session: Architecture Design & Technology Decisions

**Objective:** Design a solid, extensible architecture that solves the 3 core problems and supports all 10 non-negotiable features

**Major Findings & Decisions:**

#### 1. REAL-TIME COMPATIBILITY TESTING (New Feature)

**What:** Before implementation phase, during Design phase, the system validates that proposed technologies actually work together.

**When:** User proposes architecture → System tests compatibility → Reports issues → User decides → Specs updated → Re-test → Repeat until compatibility confirmed

**Why This Was Missing:** Previous design didn't account for practical incompatibilities (e.g., "React 18 + Django requires ASGI not WSGI" or "Library A v2.0 incompatible with Library B v1.5 by version")

**How It Works:**
1. User proposes: "React 18 + Django 4.2 + PostgreSQL 15"
2. System tests: Attempts actual imports, checks version compatibility, analyzes library interactions
3. System reports: "Compatible, but WebSockets need ASGI upgrade"
4. User decides: Accept or choose alternative
5. If alternative: Re-test
6. Results stored in database (prevents re-testing same combo)

**Deep Not Shallow:** Uses actual import testing, not just lookup table. Catches real version-specific issues.

**Database:** test_results table tracks all compatibility tests, decisions, proposed solutions

#### 2. MATURITY SYSTEM (Clarified & Enhanced)

**Dynamic Calculation:** Maturity = (categories with coverage / total categories) * 100

**Coverage Categories (10):**
- Goals, Requirements, Tech Stack, Constraints, Team Structure, Timeline, Deployment Target, Success Criteria, Testing Strategy, Monitoring & Ops

**Maturity Per Category:** Each tracked independently (0-100%)

**How It Gates Phase Transitions:**

- **Discovery → Analysis:** Requires maturity ≥ 60%, all conflicts resolved
  - Message: "You're at 45%. Missing: Tech Stack (0%), Scalability (10%), Testing (5%). Complete these areas to advance."

- **Analysis → Design:** Requires maturity 100%, architecture tested for compatibility
  - Message: "All specs must be finalized and tech compatibility confirmed"

- **Design → Implementation:** Requires maturity 100%, all conflicts resolved, compatibility testing passed
  - Message: "Architecture approved and compatibility confirmed"

**User Can Delete Specs:** "Forget feature X" → spec soft-deleted → maturity recalculated (may drop) → must re-cover gaps

**User Can View Anytime:** "Show me progress" → displays maturity per category, what's missing, time estimate

**Why Dynamic:** As user adds specs, maturity changes. As user deletes specs, maturity recalculates. System always reflects true coverage.

#### 3. RULES/INSTRUCTIONS SYSTEM (For Quality Control)

**What:** User-defined rules encoded per user, passed to Quality Control system

**Stored:** user_rules table as JSONB (flexible, queryable)

**Examples:**
```json
{
  "never_assume": true,
  "always_check": true,
  "prefer_postgres": true,
  "prefer_async": true,
  "min_test_coverage": 0.8,
  "communication_style": "technical",
  "no_microservices": true,
  "require_api_documentation": true
}
```

**How Used:** Quality Control checks rules against proposals
- If proposed "SQLite" but rule says "prefer_postgres" → QC flags it
- If proposed "monolith" but rule says "no_microservices" → QC allows it
- If proposed test coverage "50%" but rule requires "80%" → QC flags gap

**Note:** Can be deferred to Phase 2 if complex for MVP

#### 4. ARCHITECTURE DECISION: 2 POSTGRESQL DATABASES (Not 1, Not 3)

**Database 1: `socrates_auth`** (Small, locked down, slow changes)
- users, user_rules, teams (later), permissions (later)
- ~10MB typical
- Authentication, user management, authorization

**Database 2: `socrates_specs`** (Large, optimized for writes, fast reads)
- projects, sessions, specifications, conversation_history, conflicts, quality_metrics, maturity_tracking, knowledge_base, test_results
- ~1GB+ over time
- All project data, specs, conversation, testing results

**Why 2 and Not 1:**
- ✅ Security isolation (auth breach ≠ specs breach)
- ✅ Independent scaling (auth stays small, specs scales)
- ✅ Different backup strategies
- ✅ Different optimization needs
- ✅ Compliance separation (user auth separate from project data)
- ✅ Future-proof for team collaboration (team ops don't affect auth)

**Why Not 3+:**
- Too operationally complex
- 2 is the right balance: separation + simplicity

**Why PostgreSQL Not SQLite:**
- SQLite single-user only
- PostgreSQL: concurrent access, ACID transactions, JSON support, extensible (pgvector later)
- Battle-tested, production-ready

**Why NO ChromaDB in MVP:**
- Full-text search (PostgreSQL native) sufficient
- Vectors (semantic search) not needed until Phase 5+ when multiple projects exist
- Adding vectors later is NON-BREAKING (ALTER TABLE, no data loss, existing queries still work)

**Why NO pgvector in MVP:**
- Discovery phase: no semantic search
- Analysis phase: not searching similar specs
- Design phase: real-time compatibility testing (no semantic search)
- Knowledge base: full-text search sufficient

#### 5. CLI FIRST, UI LATER

**Why:**
- Fast to MVP (no UI framework overhead)
- Easy to test and debug
- Focused on core logic not UI polish
- UI can be added/replaced later without breaking backend

**Design:** Like Claude Code - simple, direct, functional

**Structure:**
- Commands for project management (create, load, list)
- Commands for chat (run conversation, toggle modes, show status)
- Commands for phase transitions (advance, show phase)
- Admin commands for testing/debugging

**Why Not Click/Typer:** Keep MVP focused, reduce dependencies

#### 6. TECHNOLOGY STACK FINALIZED

**Python 3.12**
- ✅ Stable (Sept 2023 release)
- ✅ Works with all dependencies
- ✅ Not too new (3.14 has unknown edge cases)

**FastAPI 0.121.0+**
- ✅ Async-native (needed for multi-LLM later)
- ✅ Pydantic validation built-in
- ✅ Perfect for React UI integration
- ✅ Lightweight, modern

**SQLAlchemy ORM 2.0.44+**
- ✅ Works perfectly with Python 3.12
- ✅ Mature, proven, tested
- ✅ Type-safe, flexible
- ✅ NOT the problem from last session (last session was confused about non-existent incompatibilities)

**PostgreSQL (2 instances)**
- ✅ ACID compliance, JSON support, extensions, battle-tested
- ✅ NOT SQLite (limited to single user, concurrent access issues)

**Pydantic 2.12.3+**
- ✅ FastAPI integration
- ✅ Strong validation
- ✅ Type safety

**Alembic**
- ✅ Database migrations
- ✅ Version control for schema changes

**Note:** NO vectors, NO ChromaDB for MVP (added later Phase 5+ as needed)

#### 7. IMPLEMENTATION APPROACH: PHASES

**Phase 0: Foundation (Week 1)**
- Requirements.txt, database setup, SQLAlchemy models, FastAPI structure, CLI structure

**Phase 1: MVP Core (Weeks 2-4)**
- Authentication, project management, Socratic engine, Direct chat, conflict detection, maturity system, Quality Control basics, CLI, testing

**Phase 2: Polish MVP (Week 5)**
- Error handling, validation, edge cases, documentation, real-world testing

**Phase 3+: Future Modules**
- Code generation, IDE integration, GitHub integration, team collaboration, user learning, vectors, analytics

---

## REFINED NON-NEGOTIABLE FEATURES (Clarified Nov 4)

**From original 10, clarified with new discoveries:**

1. ✅ **Persistent Context** - Database stores all specs, decisions, conflict resolutions, conversation history
2. ✅ **Conflict Detection** - 4 types detected on every spec change, user resolves immediately
3. ✅ **Quality Control** - Prevents greedy decisions, shows paths with costs, detects bad patterns
4. ✅ **Socratic Questioning** - Dynamic, role-based (7 roles), adapts to vagueness
5. ✅ **Toggle Modes** - Socratic ↔ Direct Chat in same session, real-time switch
6. ✅ **4 Phases** - Discovery → Analysis → Design → Implementation (each with maturity gates)
7. ✅ **User Learning** - Adapts to user patterns (Phase 5, infrastructure ready now)
8. ✅ **Team Collaboration** - Multiple roles, conflict resolution (Phase 6, infrastructure ready now)
9. ✅ **Project Generation** - Specs → Architecture → Code (Phase 4, infrastructure ready now)
10. ✅ **Multi-LLM Support** - Not tied to single LLM (Phase 3+, infrastructure ready now)

**NEW FEATURES (Clarified This Session):**

11. ✅ **Real-Time Compatibility Testing** - Deep testing of proposed tech before implementation
12. ✅ **Maturity System** - Dynamic coverage tracking, gates phase transitions
13. ✅ **Rules/Instructions** - User-defined rules passed to Quality Control
14. ✅ **CLI First** - Testing interface before UI
15. ✅ **2-Database Architecture** - Auth separate from specs for scalability and security

---

## EXTENSIBILITY GUARANTEES

**These features can be added later WITHOUT refactoring:**

- **Code Generation** (Phase 4): Add generated_projects table, no schema changes
- **IDE Integration** (Phase 3): Add IDE endpoints, existing API unchanged
- **GitHub Integration** (Phase 4): Add github_integrations table, no schema changes
- **Team Collaboration** (Phase 6): Add team_members, team_conflicts tables, no existing table changes
- **Vector Embeddings** (Phase 5): ALTER TABLE knowledge_base ADD COLUMN embedding vector(384) - non-breaking
- **Advanced User Learning** (Phase 5): Add user_learning_profile, question_effectiveness tables
- **Analytics** (Phase 8): Add analytics tables, no existing changes

**Why:** Architecture designed to add new features as new tables/services, not modify existing ones.

---

## DECISION RATIONALE SUMMARY

| Decision | Chosen | Why Not Alternatives |
|----------|--------|----------------------|
| Databases | 2 PostgreSQL | 1 DB: can't scale independently. 3+ DB: too complex |
| Python | 3.12 | 3.14: too new, edge cases unknown |
| ORM | SQLAlchemy | Raw SQL: harder to maintain. Others: less proven |
| Compatibility Testing | Deep | Shallow: 70% accurate, misses version issues |
| Vectors | Phase 5+ | Not needed now, safe to defer, non-breaking to add |
| CLI | Custom | Click/Typer: extra dependency, complicates testing |
| UI | Phase 3+ | CLI first: faster MVP, focused on core logic |

---

**Session Completed:** November 4, 2025
**Approved By:** User
**Status:** Ready for Phase 0: Foundation Implementation
**Next:** See ARCHITECTURE.md for full technical specification

# SOCRATES v2.0 - ARCHITECTURE DOCUMENT

**Version:** 2.0.0
**Date:** November 4, 2025
**Status:** APPROVED - Ready for Implementation
**Approved By:** User
**Source of Truth:** VISION.md (immutable requirements)

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Core Problems & Solutions](#core-problems--solutions)
3. [System Overview](#system-overview)
4. [Technology Stack](#technology-stack)
5. [Database Architecture](#database-architecture)
6. [Data Models](#data-models)
7. [System Phases](#system-phases)
8. [Core Modules (MVP)](#core-modules-mvp)
9. [Real-Time Compatibility Testing](#real-time-compatibility-testing)
10. [Quality Control System](#quality-control-system)
11. [Maturity System](#maturity-system)
12. [Rules/Instructions System](#rulesinstituctions-system)
13. [CLI Architecture](#cli-architecture)
14. [API Architecture](#api-architecture)
15. [Future Modules (Post-MVP)](#future-modules-post-mvp)
16. [Extensibility & Scalability](#extensibility--scalability)
17. [Implementation Roadmap](#implementation-roadmap)
18. [Design Decisions & Rationale](#design-decisions--rationale)

---

## EXECUTIVE SUMMARY

Socrates v2.0 is a multi-agent AI system that solves three fundamental problems in software development:

1. **Context Loss** - Persistent database stores all specs, decisions, context (never forgotten)
2. **Greedy Algorithmic Decisions** - Quality Control prevents locally-optimal choices that cost globally
3. **Incomplete Specifications** - Dynamic Socratic questioning gathers complete specs from multiple perspectives

**Key Innovation:** Real-time compatibility testing during design phase detects practical incompatibilities BEFORE code generation, preventing expensive rework.

---

## CORE PROBLEMS & SOLUTIONS

### Problem 1: Modern AI Systems Lose Context

**The Issue:** AI processes information and forgets. Return to a project 3 months later = lost context.

**Solution (VISION.md:13-16):** All context and specifications persisted in database. Complete project context available anytime, anywhere.

**Implementation:** PostgreSQL `socrates_specs` database stores:
- conversation_history (every chat turn)
- specifications (versioned)
- interactions (audit trail)
- All decisions and resolutions

### Problem 2: Greedy Algorithmic Decisions

**The Issue (VISION.md:18-25):** AI optimizes locally (immediate step) without seeing global costs (rework, cascading effects).

**Example:** "Skip security requirements to save time" saves 10 tokens now but costs 200 tokens in rework later.

**Solution:** Quality Control system:
- Analyzes all possible paths before user chooses
- Shows total cost (direct + rework risk) for each path
- Prevents obviously bad decisions
- Maturity threshold (60%) determines when forcing decisions vs suggesting

**Implementation:** QualityControlService checks:
- Coverage gaps (10 requirement areas)
- Bias in questions (solution bias, technology bias, leading questions)
- Bad patterns (tunnel vision: modifying tests instead of fixing bugs)
- Path optimization (direct cost + rework probability)

### Problem 3: Incomplete Specifications

**The Issue (VISION.md:27-35):** Chat-based requirements gathering is vague, incomplete, conflicted.

**Solution:** Dynamic Socratic questioning from 7 professional roles:
- PM (goals, timelines, business value)
- BA (requirements, use cases, workflows)
- UX (users, flows, accessibility)
- Frontend (UI, framework, browser support)
- Backend (API, database, scalability)
- DBA (data modeling, performance)
- DevOps (deployment, infrastructure, monitoring)

**Implementation:** SocraticCounselorService generates questions dynamically, adapts based on answer vagueness and coverage gaps.

---

## SYSTEM OVERVIEW

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI / UI (Future)                      │
│            (Claude Code style CLI for MVP)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                           │
│         (async, Pydantic validation, REST API)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
   │ Services  │  │ Agents   │  │Validators│
   └────┬─────┘  └────┬─────┘  └────┬─────┘
        │              │              │
   ┌────▼─────────────▼──────────────▼─────┐
   │    SQLAlchemy ORM Layer                │
   └────┬──────────────────────────────────┘
        │
        ├─────────────────┬──────────────────┐
        │                 │                  │
    ┌───▼──────┐      ┌──▼────────┐     ┌──▼────────┐
    │PostgreSQL│      │PostgreSQL │     │PostgreSQL │
    │socrates_ │      │socrates_  │     │(Future)   │
    │  auth    │      │  specs    │     │Team/Org DB│
    └──────────┘      └───────────┘     └───────────┘

[MVP Phase]          [MVP + Future]      [Phase N]
```

---

## TECHNOLOGY STACK

### Why These Choices?

#### **Python 3.12**
- ✅ Stable, battle-tested (released Sept 2023)
- ✅ Compatible with all dependencies (FastAPI, SQLAlchemy, Pydantic)
- ✅ Modern async/await features
- ✅ Good performance
- **Why not 3.14?** Too new, edge cases unknown for production MVP

#### **FastAPI 0.121.0+**
- ✅ Async-native (required for multi-LLM support later)
- ✅ Pydantic validation built-in
- ✅ Automatic OpenAPI documentation
- ✅ Lightweight, modern
- ✅ Perfect for React UI integration later
- **Why?** Supports current needs + future multi-LLM concurrency

#### **PostgreSQL (2 instances)**
- ✅ ACID compliance (data integrity for specs)
- ✅ JSON support (rules, metadata stored as JSONB)
- ✅ Full-text search (knowledge base search, MVP phase)
- ✅ Extensible (pgvector added later for semantic search if needed)
- ✅ Battle-tested, robust
- **Why not SQLite?** Single-user, limited concurrency, can't support future team collaboration
- **Why not MySQL?** Less extensible, no pgvector support

#### **SQLAlchemy ORM 2.0.44+**
- ✅ Proven, mature
- ✅ Works perfectly with Python 3.12
- ✅ Flexible: can use ORM or Core SQL as needed
- ✅ Type hints support (Pydantic integration)
- ✅ Easy to test (can swap database for testing)
- **Why ORM not raw SQL?** Maintainability, type safety, migrations

#### **Pydantic 2.12.3+**
- ✅ FastAPI integration
- ✅ Strong validation
- ✅ Serialization/deserialization
- ✅ Type safety
- **Why?** Core to FastAPI, ensures data quality

#### **CLI Framework: Custom (No Click/Typer)**
- ✅ Like Claude Code - simple, direct
- ✅ No extra dependencies
- ✅ Easy to debug and extend
- ✅ Can be replaced by UI later
- **Why not Click/Typer?** Keep MVP focused on core logic, CLI is testing tool

#### **Alembic**
- ✅ Database migrations
- ✅ Version control for schema
- ✅ Works with SQLAlchemy
- **Why?** Essential for managing 2 databases safely

---

## DATABASE ARCHITECTURE

### Design Decision: 2 PostgreSQL Instances

#### **Why 2 and not 1?**

**One Database Problems:**
- ❌ Auth data mixed with project data (security concern)
- ❌ Can't back up/archive projects without affecting auth
- ❌ Specs table grows exponentially (millions of rows), auth stays small
- ❌ Different scaling needs: auth = slow writes, specs = fast concurrent writes
- ❌ Can't isolate specs DB for performance tuning or scaling
- ❌ Compliance: harder to separate user authentication from project data

**Two Database Benefits:**
- ✅ Auth data locked down strictly, separate backup strategy
- ✅ Specs DB optimized for high-volume writes and concurrent access
- ✅ Can scale independently (auth stays small, specs scales horizontally)
- ✅ Security isolation: specs breach ≠ auth breach
- ✅ Maintenance: can reset/archive specs without affecting auth
- ✅ Compliance: clean separation of auth from project data
- ✅ Future proof: team collaboration multiplies specs writes, auth unaffected
- ✅ Future modules (IDE integration, GitHub integration) benefit from separate specs DB

**Operational Cost:**
- Both are PostgreSQL (same tools, knowledge)
- Initial setup: ~30 minutes more than single DB
- Long-term benefit: huge (scalability, maintenance, security)

#### **Why PostgreSQL + 2 instances (not SQLite, not NoSQL)?**

**SQLite Problems:**
- ❌ Single user only (MVP needs concurrent access for testing)
- ❌ Limited to one machine
- ❌ Can't scale for future team collaboration
- ❌ Not suitable for production multi-user systems

**NoSQL Problems:**
- ❌ Socrates needs ACID transactions (specs must be consistent)
- ❌ Relationships complex (projects → specs → conflicts → quality metrics)
- ❌ SQL easier to analyze specs data

**PostgreSQL Advantages:**
- ✅ ACID transactions (data integrity for specs)
- ✅ JSON support (JSONB) for rules, metadata, flexibility
- ✅ Full-text search built-in (knowledge base)
- ✅ pgvector extension ready for Phase 5+ (semantic search)
- ✅ Battle-tested, proven, enterprise-grade
- ✅ Excellent concurrency handling
- ✅ Rich ecosystem (Alembic migrations, SQLAlchemy, etc.)

#### **Why NO ChromaDB or pgvector in MVP?**

**Vectoring Not Needed for MVP:**
- Discovery phase: No semantic search needed
- Analysis phase: Not searching similar specs
- Design phase: Real-time compatibility testing (no semantic search)
- Knowledge base: Full-text search (PostgreSQL native) sufficient

**When to Add Vectors (Phase 5+):**
- Many historical projects (50+) exist
- Want to find "similar" specs across projects
- Semantic understanding needed beyond keywords
- User asks for it (evidence of value)

**Why Adding Vectors Later is Safe:**
```sql
-- MVP (no vectors)
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY,
    content TEXT,
    metadata JSONB
);

-- Phase 5+ (adding vectors) - non-breaking
ALTER TABLE knowledge_base ADD COLUMN embedding vector(384);
-- Old queries work, new queries use vectors
```

No refactoring needed. No data loss. Safe to defer.

---

## DATA MODELS

### Database 1: `socrates_auth` (Authentication & User Management)

**Purpose:** Authentication, user profiles, rules/instructions, team management (future)

**Tables:**

#### `users`
```python
id: UUID (PK)
username: str (unique)
email: str (unique)
password_hash: str
created_at: DateTime
updated_at: DateTime
is_active: bool
is_archived: bool
archived_at: DateTime (nullable)
```

**Purpose:** User identity and authentication
**Why these fields?**
- username/email: login identity
- password_hash: security (never store plain text)
- is_active: disable without deleting
- is_archived: soft delete (audit trail)
- created_at/updated_at: tracking

#### `user_rules`
```python
id: UUID (PK)
user_id: UUID (FK → users)
rule_json: JSONB
created_at: DateTime
updated_at: DateTime
```

**Purpose:** User-defined rules/instructions passed to Quality Control

**Example rules_json:**
```json
{
  "never_assume": true,
  "always_check": true,
  "prefer_postgres": true,
  "prefer_async": true,
  "min_test_coverage": 0.8,
  "communication_style": "technical",
  "detail_level": "comprehensive"
}
```

**Why JSONB?**
- Flexible: rules change per user, project
- Queryable: PostgreSQL can search JSONB
- Extensible: add new rules without schema change

#### (Future) `teams`
```python
id: UUID (PK)
name: str
owner_id: UUID (FK → users)
created_at: DateTime
updated_at: DateTime
```

#### (Future) `team_members`
```python
id: UUID (PK)
team_id: UUID (FK → teams)
user_id: UUID (FK → users)
role: str (owner | lead | developer | viewer)
joined_at: DateTime
```

---

### Database 2: `socrates_specs` (Projects, Specifications, Context)

**Purpose:** Project data, specifications, conversation, conflict detection, quality metrics

**Tables:**

#### `projects`
```python
id: UUID (PK)
owner_id: UUID (FK → socrates_auth.users)
name: str
description: str (nullable)
phase: str (discovery | analysis | design | implementation)
status: str (active | archived | completed)
maturity_percent: float (0-100)
created_at: DateTime
updated_at: DateTime
is_archived: bool
archived_at: DateTime (nullable)
```

**Purpose:** Project metadata and phase tracking

**Why these fields?**
- owner_id: who owns project
- phase: current workflow phase
- maturity_percent: dynamic maturity score (calculated, not static)
- status: project lifecycle
- is_archived: soft delete

#### `sessions`
```python
id: UUID (PK)
project_id: UUID (FK → projects)
mode: str (socratic | direct)
started_at: DateTime
ended_at: DateTime (nullable)
is_active: bool
```

**Purpose:** Conversation session management (can span multiple chat turns)

**Why these fields?**
- mode: user can toggle Socratic ↔ Direct Chat in real-time (same session)
- is_active: can pause/resume session
- Spans multiple turns, persists

#### `specifications`
```python
id: UUID (PK)
project_id: UUID (FK → projects)
spec_type: str (goal | requirement | constraint | tech_choice | team_structure | deployment_target)
name: str (human readable: "User Authentication", "Database Choice", etc.)
content: str (the actual spec: "Users can login with email/password using OAuth2")
version: int (tracks changes)
is_current: bool (latest version?)
created_at: DateTime
updated_at: DateTime
created_by: str (user who added this)
deleted_at: DateTime (nullable) (soft delete for "forget that feature")
```

**Purpose:** Store all specifications mentioned by user, versioned

**Why these fields?**
- version: can see spec evolution over time
- is_current: know which is active
- deleted_at: "forget feature X" - soft delete, can undo
- created_by: who said it (future: for team collaboration)
- spec_type: categorize for Quality Control analysis

#### `conversation_history`
```python
id: UUID (PK)
session_id: UUID (FK → sessions)
author: str (user | system)
type: str (question | answer | suggestion | conflict_alert | phase_transition)
content: str (the actual text)
phase: str (discovery | analysis | design)
timestamp: DateTime
metadata_json: JSONB (extra data: question_id, conflict_id, etc.)
```

**Purpose:** Complete audit trail of every conversation

**Why complete history?**
- Understand how specs emerged
- Replay session logic for debugging
- Quality Control learns from patterns
- Future: user learning system analyzes patterns

#### `conflicts`
```python
id: UUID (PK)
project_id: UUID (FK → projects)
type: str (technology | requirement | timeline | resource | compatibility)
severity: str (low | medium | high | blocking)
description: str (what conflicts?)
involved_spec_ids: JSONB (array of spec IDs)
detected_at: DateTime
status: str (unresolved | resolved | overridden)
resolution: str (user's decision: keep_old | use_new | manual_edit | both_valid)
resolved_at: DateTime (nullable)
resolution_notes: str (why did user choose this?)
```

**Purpose:** Track all detected conflicts and resolutions

**Why these fields?**
- type includes "compatibility" (new for real-time testing phase)
- status: unresolved conflicts BLOCK phase transitions
- resolution: audit what user chose
- involved_spec_ids: can see which specs caused it

#### `quality_metrics`
```python
id: UUID (PK)
project_id: UUID (FK → projects)
phase: str (discovery | analysis | design)
bias_score: float (0-1, 0=unbiased, 1=highly biased)
coverage_gaps: JSONB (which areas missing coverage)
recommendations: JSONB (what questions to ask)
path_analysis: JSONB (paths available with costs)
detected_patterns: JSONB (tunnel vision, scope creep, etc.)
calculated_at: DateTime
```

**Purpose:** Quality Control analysis results

**Why JSONB for complex data?**
- Flexible structure for different phase analyses
- Can query individual recommendations
- Extensible as Quality Control improves

#### `maturity_tracking`
```python
id: UUID (PK)
project_id: UUID (FK → projects)
category: str (goals | requirements | tech_stack | constraints | team | timeline | deployment | success_criteria | testing | monitoring)
completeness_percent: float (0-100)
required_minimum: float (what % needed to block advancement)
satisfied: bool (has minimum been met?)
last_updated: DateTime
```

**Purpose:** Track maturity per category, identify gaps

**Why per-category?**
- User can see exactly what's missing: "Security: 0%, Scalability: 10%, Testing: 5%"
- Quality system can recommend: "Ask security questions next"
- Blocks phase transitions: "Can't move to Analysis - coverage < 60%"

#### `knowledge_base`
```python
id: UUID (PK)
project_id: UUID (FK → projects)
source: str (user_uploaded | github_imported | documentation_added)
content: str (actual document text)
metadata_json: JSONB (original filename, size, import_date)
created_at: DateTime
updated_at: DateTime
```

**Purpose:** Store user-provided reference documents, uploaded code, etc.

**Why no embedding in MVP?**
- Full-text search (PostgreSQL native) sufficient
- Vectors added Phase 5+ when needed

#### `test_results` (Compatibility Testing)
```python
id: UUID (PK)
project_id: UUID (FK → projects)
session_id: UUID (FK → sessions)
test_scenario: str (description: "React 18 + Django 4.2 + PostgreSQL 15")
tech_combinations: JSONB ({"frontend": "React 18", "backend": "Django 4.2", "database": "PostgreSQL 15"})
compatibility_status: str (compatible | incompatible | warning)
issues_found: JSONB (array of issues discovered)
tested_at: DateTime
proposed_solutions: JSONB (suggestions to fix issues)
```

**Purpose:** Track compatibility testing during Design phase

**Why separate table?**
- Each test = validation work, results stored
- User can see test history
- Quality Control learns: "This combo failed before"
- Prevents user testing same thing twice

---

## SYSTEM PHASES

### Phase Definitions & Maturity Gates

#### **Phase 1: DISCOVERY**
**Goal:** Gather complete specifications via Socratic questions or direct chat

**What Happens:**
1. User creates project, provides high-level description
2. System toggles between Socratic mode (asks questions) or Direct Chat (user tells)
3. User can toggle mid-session (no need to exit/re-enter)
4. Every answer adds specification to database
5. Real-time conflict detection runs on every new spec
6. If conflicts found: user resolves them immediately
7. Maturity % tracked and visible

**Maturity Requirements:**
- Minimum 60% maturity to advance
- All major features/functions described
- Conflicts resolved
- User can ask "summary" anytime to see progress

**Exit Criteria:**
- User explicitly requests: "Move to Analysis phase"
- System checks: maturity >= 60% AND conflicts resolved
- If not met: System explains what's missing
- User can continue gathering specs or override

**Database Activity:**
- specifications table grows (every answer = new spec)
- conversation_history captures every turn
- conflicts detected and stored
- maturity_tracking updated continuously

#### **Phase 2: ANALYSIS**
**Goal:** System analyzes specs and proposes architecture + technologies

**What Happens:**
1. System reads all specifications collected in Phase 1
2. System proposes:
   - Architecture structure (monolith vs microservices, etc.)
   - Technology stack (programming languages, frameworks, databases, deployment)
   - Implementation approach
3. Quality Control checks proposals for:
   - Coverage gaps (missing considerations)
   - Bias (solution bias, technology bias)
   - Feasibility (can this work with these specs?)
4. System presents analysis to user: "Here's what I recommend, here's why"
5. User can:
   - Approve proposed architecture
   - Ask questions about choices
   - Request alternative approaches
   - Modify specifications if they want

**Real-Time Compatibility Testing:**
- When user approves tech choices, system tests compatibility
- Try to import libraries, check version compatibility
- Detect conflicts: "Library A v2.0 incompatible with Library B v1.5"
- If issues found: inform user, propose solutions
- User decides: accept risk, choose alternative, or modify specs

**Maturity Requirements:**
- Architecture proposed and tested
- All tech compatibility confirmed (no blocking issues)
- Maturity reaches 100% (all specs covered, all conflicts resolved)
- User approves architecture

**Exit Criteria:**
- User explicitly requests: "Move to Design phase"
- System checks: tech compatibility OK AND maturity 100%
- If not met: System explains what needs resolution

**Database Activity:**
- test_results table populated (compatibility testing)
- quality_metrics updated with analysis
- If user modifies specs: specifications table updated, test_results re-run
- conflicts table updated if new tech conflicts found

#### **Phase 3: DESIGN**
**Goal:** Finalize architecture, prepare for implementation

**What Happens:**
1. System shows final approved architecture
2. User can review, ask questions
3. If modifications needed: return to Analysis phase
4. Real-Time Compatibility Testing runs again after any changes
5. Final validation: all specs matched to architecture components
6. Quality Control final review: no greedy decisions, no gaps

**Maturity Requirements:**
- Maturity 100% (all specs finalized)
- All tech compatibility confirmed
- All conflicts resolved
- Architecture approved by user

**Exit Criteria:**
- User explicitly requests: "Move to Implementation phase"
- System checks: all criteria met
- If not: System explains blockers

**Database Activity:**
- No new specifications (locked for generation)
- test_results finalized
- quality_metrics final review stored

#### **Phase 4: IMPLEMENTATION** (Future Module)
**Goal:** Generate code from specifications

**What Happens:**
1. Code generation service takes all specs + architecture
2. Generates:
   - File structure
   - Architecture diagrams
   - Code implementation
   - Configuration files
   - Deployment scripts
3. Quality Control validates generated code:
   - Matches specs?
   - Follows architecture?
   - No anti-patterns?
4. User receives complete project

**Database Activity:**
- generated_projects table (new, Phase 4+)
- generation_history tracked
- Code can be regenerated if specs change

---

## CORE MODULES (MVP)

### 1. Socratic Questioning Engine

**Purpose:** Ask role-based questions, adapt based on answers

**Services:**
- `SocraticQuestioningService` - Question generation, adaptation
- `SpecificationExtractionService` - Parse answers into structured specs
- `VaguenessDetectionService` - Detect vague answers, request clarification

**7 Professional Roles:**
1. PM - Goals, timelines, business value, success metrics
2. BA - Requirements, use cases, workflows, constraints
3. UX - Users, flows, accessibility, design requirements
4. Frontend - UI framework, browser support, state management, performance
5. Backend - API design, database, scalability, business logic
6. DBA - Data modeling, query patterns, performance requirements, data volume
7. DevOps - Deployment target, infrastructure, monitoring, scaling, CI/CD

**Question Categories:**
- Requirements gathering
- Technical discovery
- Design exploration
- Validation
- Risk assessment
- Clarification

**How It Works:**
```
1. System determines missing coverage (which categories not filled)
2. Selects question from weakest category
3. Picks role that would ask that question
4. Chooses question most effective for THIS user (learning)
5. User answers
6. System extracts specification from answer
7. System measures vagueness:
   IF vague → ask follow-up clarifying questions
   ELSE → move to next category
8. Repeat until maturity >= 60%
```

### 2. Direct Chat Mode

**Purpose:** User can tell system directly instead of answering questions

**Services:**
- `DirectChatService` - Parse user messages
- `SpecificationExtractionService` - Extract specs from freeform text
- `IntentDetectionService` - Understand what user is saying

**How It Works:**
```
1. User: "We need a REST API for user management"
2. System: "Got it. Extracted spec: requirements → REST API for user management"
3. System: "Any other details about this?"
4. User can continue or ask system to ask Socratic questions
```

**User Can Toggle:**
- In same session (no need to exit/re-enter)
- Real-time: "Switch to Socratic mode" → System asks next question
- Real-time: "Switch to Direct Chat" → User types freeform

### 3. Real-Time Conflict Detection

**Purpose:** Detect conflicts immediately as specs are added, allow user to resolve

**Services:**
- `ConflictDetectionService` - Detect 4 types
- `ConflictResolutionService` - Show user options, record decisions

**4 Conflict Types:**

1. **Technology Conflicts**
   - Example: "SQLite + 1000 concurrent users"
   - Rule: Detects tech stack incompatibilities
   - Action: Inform user, propose alternatives

2. **Requirement Conflicts**
   - Example: "No data persistence" + "Remember user preferences"
   - Rule: Detect semantic contradictions
   - Action: Ask user which to keep

3. **Timeline Conflicts**
   - Example: "100 hours of work, 2 devs, 1 week"
   - Rule: Detect impossible schedules
   - Action: Warn user, propose extensions

4. **Resource Conflicts**
   - Example: "ML expertise needed, team is 2 junior devs"
   - Rule: Detect insufficient capabilities
   - Action: Warn user, propose hiring/training

**How Resolution Works:**
```
CONFLICT DETECTED: Tech Stack Conflict
Old: "Django as backend"
New: "FastAPI as backend"
User sees 4 options:
1. Keep existing (Django)
2. Replace with new (FastAPI)
3. Skip this specification
4. Manual resolution (edit both)
User chooses → Database updates → No contradiction remains
```

### 4. Quality Control System

**Purpose:** Prevent greedy decisions, ensure coverage, detect bad patterns

**Services:**
- `QualityAnalysisService` - Analyze questions and suggestions for bias/gaps
- `CoverageAnalysisService` - Track coverage across 10 requirement areas
- `BadPatternDetectionService` - Detect tunnel vision, scope creep, premature optimization

**Bias Detection:**
- Solution bias: "Should we use Django?" → suggests specific solution
- Technology bias: "Kubernetes is best" → pushes specific tech
- Leading questions: "You need security, right?" → directs answer
- Narrow scope: Misses alternatives

**Coverage Areas (10):**
1. Scalability (concurrent users, data growth, performance targets)
2. Security (authentication, authorization, encryption, compliance)
3. Performance (response time, throughput, resource usage)
4. Testing (unit, integration, performance, security testing)
5. Monitoring (logging, metrics, alerting, dashboards)
6. Error Handling (validation, recovery, rollback)
7. Data Retention (backup, archival, retention policies)
8. Disaster Recovery (failure scenarios, recovery time, backups)
9. Maintenance (updates, patching, deprecation, technical debt)
10. User Feedback (support channels, feedback collection, improvements)

**Bad Pattern Detection:**
- Tunnel Vision: Tests modified to pass instead of fixing bugs
- Scope Creep: Features added beyond MVP
- Over-optimization: Premature optimization before profiling

### 5. Maturity System

**Purpose:** Track spec completeness, block phase transitions if incomplete

**How It Works:**

```
Dynamic Maturity Calculation:
- For each specification mentioned: mark as covered
- For each category (scalability, security, etc.): calculate % coverage
- Maturity = (covered categories / total categories) * 100

Discovery Phase:
- Maturity 0-60%: SUGGEST next questions (optional)
- Maturity 60-99%: ASK user to choose between alternatives (path analysis)
- Maturity 100%: User can advance to Analysis

Analysis Phase:
- System proposes architecture
- Real-time compatibility testing
- Maturity reaches 100% when all tests pass
- User can advance to Design

User Can Delete Specs:
- "Forget feature X"
- specifications table: set deleted_at = now
- Maturity recalculated (may drop below 100%)
- New specs must cover gaps again
```

**Blocking Phase Transitions:**
```
User: "Move to Analysis phase"
System checks:
  - maturity >= 60%? NO → "60% required, you're at 45%. Missing: Security, Scalability"
  - conflicts resolved? YES
  - System recommends: "Ask about security requirements next"

User: "Move to Design phase"
System checks:
  - architecture proposed? YES
  - tech compatibility OK? YES
  - maturity 100%? NO → "Design phase requires 100% maturity"
  - System shows: "All specs must be finalized"
```

---

## REAL-TIME COMPATIBILITY TESTING

### Deep Testing (Option B)

**Purpose:** During Analysis/Design phase, validate that proposed technologies actually work together

**When It Runs:**
- User proposes: "React 18 + Django 4.2 + PostgreSQL 15"
- System runs compatibility test
- Reports issues BEFORE implementation

**How Deep Testing Works:**

```
Step 1: Gather Technology Specifications
- Frontend: React 18
- Backend: Django 4.2
- Database: PostgreSQL 15
- Library A: Django REST Framework v3.14
- Library B: Celery v5.3

Step 2: Attempt Actual Imports
- Try: import react
- Try: import django
- Try: import psycopg2
- Try: pip check (dependency conflicts)

Step 3: Check Version Compatibility
- React 18 requires Node.js 16+
- Django 4.2 requires Python 3.8+
- Celery 5.3 conflicts with Django 3.x but compatible with 4.2
- DRF 3.14 compatible with Django 4.2

Step 4: Analyze Library Interactions
- "Django middleware X" + "Celery task queue Y" = compatible
- "React state management Z" + "Django API endpoint" = compatible
- Database connection pooling: "pgbouncer" compatible with "psycopg2 + Django"

Step 5: Check Known Issue Patterns
- SQLite + concurrent users > 100 = WARNING
- Microservices + SQLite database per service = ERROR
- WebSockets + Django WSGI server = INCOMPATIBLE (needs ASGI)

Step 6: Report Results
{
  "scenario": "React 18 + Django 4.2 + PostgreSQL 15",
  "status": "COMPATIBLE",
  "warnings": [
    "Django running on WSGI - WebSockets won't work without ASGI upgrade"
  ],
  "issues": [],
  "recommendations": [
    "Use Daphne or Uvicorn for ASGI if real-time features needed",
    "Configure pgbouncer for connection pooling"
  ]
}

Step 7: User Decision
- User accepts compatibility or chooses alternative
- If alternative chosen: re-run tests
- Results stored in test_results table
- System learns: "User rejected microservices, prefers monolith"
```

**Why Deep (not Shallow)?**

- **Shallow (DB lookup):** "I know React + Django is bad" → but misses version-specific issues
- **Deep (actual testing):** Finds real problems: "React 18 compatible with Django 4.2 but needs ASGI for WebSockets"

**Deep is needed for MVP** because real-time testing prevents the expensive "we thought it would work" mistakes.

---

## QUALITY CONTROL SYSTEM

### Preventing Greedy Decisions

**Maturity Threshold Model:**

```
Maturity < 60%:
  System: SUGGESTS paths and next steps (optional guidance)
  User: Can ignore, can override
  Message: "Consider these options, but you can proceed as-is"
  Example:
    - "You haven't specified security requirements"
    - "Here's why it matters: 80 hours saved if we get it right"
    - "Want to take 10 minutes to answer security questions?"

Maturity >= 60%:
  System: ASKS user to choose between paths (mandatory decision)
  User: MUST choose before proceeding
  Message: "Multiple paths available with different costs. Which?"
  Example:
    - Path A (fast): 10h + 60% failure risk = 120h expected
    - Path B (balanced): 30h + 15% failure risk = 33h expected ← RECOMMENDED
    - Path C (thorough): 50h + 5% failure risk = 55h expected
```

### How It Prevents Greedy Behavior

**Example: Skipping Security Requirements**

```
Discovery Phase:
Greedy approach (without QC):
  1. User: "We need a web app"
  2. System: "Ok, let's build it" (no security questions)
  3. Cost: 5h implementation
  4. Later: Security breach discovered
  5. Total cost: 5h + 200h emergency fixes = 205h

With Quality Control (MVP):
  1. User: "We need a web app"
  2. QC detects: "Security coverage: 0%" (critical gap)
  3. QC calculates paths:
     - Path A (skip security): 5h + (80% × 200h) = 165h expected
     - Path B (include security): 25h + (5% × 50h) = 27.5h expected
  4. Maturity >= 60%: System ASKS: "Which path?"
  5. User sees numbers, chooses Path B
  6. Security requirements gathered
  7. Total cost: 25h (cheaper than skipping)
```

---

## MATURITY SYSTEM

### Dynamic Maturity Calculation

**Categories Tracked (10):**
1. Goals
2. Requirements
3. Tech Stack
4. Constraints
5. Team Structure
6. Timeline
7. Deployment Target
8. Success Criteria
9. Testing Strategy
10. Monitoring & Ops

**How Maturity % Calculated:**

```
maturity_percent = (categories_with_coverage / total_categories) * 100

Example:
Covered: Goals (100%), Requirements (80%), Tech Stack (0%), Constraints (50%)
Uncovered: Team Structure, Timeline, Deployment, Success Criteria, Testing, Monitoring

Maturity = (3 categories with some coverage / 10 total) * 100 = 30%

User sees: "30% complete. Missing: Tech Stack (critical), Deployment, Testing, Monitoring"
```

**Maturity Per Category:**

```
Each category has a completeness_percent (0-100%):
- Goals: 100% (user described goals clearly)
- Requirements: 80% (most requirements clear, some missing detail)
- Tech Stack: 0% (user hasn't chosen technologies)
- Constraints: 50% (budget known, timeline unknown)

For advancement, system can require:
- Overall maturity >= 60%
- Each critical category >= 50% (no zero-coverage areas allowed)
```

**User Can View Anytime:**

```
User: "Show me progress"
System:
  ✓ Goals: 100% (clear)
  ✓ Requirements: 85% (mostly clear)
  ⚠ Tech Stack: 0% (critical - not started)
  ⚠ Deployment Target: 0% (critical - not started)
  ✓ Constraints: 70% (budget defined, timeline partial)
  - Team Structure: 50% (owner known, team size unknown)
  - Testing Strategy: 40% (some ideas, incomplete)
  - Monitoring: 30% (basic ideas only)

  OVERALL: 45% (can't advance yet, needs 60%)
  MISSING: Tech Stack, Deployment Target (both critical)
  RECOMMENDATION: Ask about technology choices next
```

---

## RULES/INSTRUCTIONS SYSTEM

### User-Defined Rules Passed to Quality Control

**Purpose:** Encode how this user works, apply across all projects

**Stored In:** `user_rules` table (JSONB)

**Example Rules:**

```json
{
  "never_assume": true,
  "always_check": true,
  "prefer_postgres": true,
  "prefer_async": true,
  "min_test_coverage": 0.8,
  "communication_style": "technical",
  "detail_level": "comprehensive",
  "no_microservices": true,
  "require_api_documentation": true,
  "ci_cd_mandatory": true
}
```

**How Quality Control Uses Rules:**

```
During Analysis phase:

System proposes: "Use SQLite for database"
User rule: "prefer_postgres": true

QC checks:
  - Proposed: SQLite
  - User rule: prefer PostgreSQL
  - Conflict detected

QC informs user:
  "Your rule prefers PostgreSQL.
   I proposed SQLite (simpler for MVP).
   Recommendation: Use PostgreSQL (per your preference).
   Is this OK?"

User decides: Accept recommendation or override
```

**Rules Applied By Quality Control:**

1. **never_assume** → QC checks all assumptions are explicit
2. **always_check** → QC verifies every assertion
3. **prefer_*technology*** → QC suggests preferred tech when options available
4. **min_test_coverage** → QC ensures testing specs meet minimum
5. **communication_style** → Affects question selection (technical vs business)
6. **detail_level** → Affects depth of questions and follow-ups
7. **no_*architecture_pattern*** → QC blocks incompatible patterns
8. **require_*documentation*** → QC ensures certain docs specified
9. **ci_cd_mandatory** → QC ensures CI/CD specified

**Can Be Skipped for MVP** (Phase 2 addition)

If complex to implement initially, can be added in Phase 2 after core works.

---

## CLI ARCHITECTURE

### Design Philosophy: Like Claude Code

**Purpose:** Testing interface, IDE integration later

**NOT like Click/Typer:**
- Simple, direct
- Easy to debug
- Easy to replace with UI later
- Focused on core logic, not CLI bells

**Structure:**

```
socrates/
├── cli/
│   ├── __init__.py
│   ├── main.py (entry point)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── project.py (create, list, load)
│   │   ├── chat.py (run conversation)
│   │   ├── status.py (show progress, maturity)
│   │   └── admin.py (database, testing)
│   └── formatters.py (colored output)
├── backend/
│   ├── __init__.py
│   ├── app.py (FastAPI app)
│   ├── config.py (settings)
│   └── ... (services, models, routes)
└── tests/
```

**Basic Commands:**

```bash
# Project management
socrates project create "My Project" "Description"
socrates project list
socrates project load <project_id>

# Conversation
socrates chat <project_id>        # Start conversation
socrates chat --status            # Show maturity, progress
socrates chat --summary           # Show full summary

# Phase transitions
socrates phase show                # Current phase
socrates phase advance             # Try to advance (checks maturity)

# Admin/testing
socrates db init                   # Initialize databases
socrates db reset                  # Reset for testing
```

**Example Chat Flow:**

```
$ socrates chat project_id

SOCRATES v2.0
Project: E-commerce Platform
Phase: DISCOVERY (45% maturity)

[Socratic Mode]
System: What is your primary business goal?
User: We want to build an e-commerce platform for selling digital products

System: Got it. Any other goals?
User: Or ask me something else
> switch to direct chat

[Direct Chat Mode]
System: Mode switched. Tell me about your project.
User: REST API, 50,000 users, React frontend, PostgreSQL

System: Extracted specs:
  - API Type: REST
  - Scale: 50,000 concurrent users
  - Frontend: React
  - Database: PostgreSQL

Detected conflicts: None
Maturity now: 65%

Continue? (ask more questions / show summary / advance phase)
>
```

---

## API ARCHITECTURE

### FastAPI Structure

**Purpose:** Backend API for CLI, UI (later), IDE integration (later)

**Design:**

```
/api/v1/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   └── POST /logout
│
├── /projects
│   ├── POST / (create)
│   ├── GET / (list)
│   ├── GET /{id} (load)
│   ├── GET /{id}/status (maturity, progress)
│   └── DELETE /{id}
│
├── /sessions
│   ├── POST / (start session)
│   ├── GET /{id} (get session)
│   ├── POST /{id}/message (send message)
│   ├── POST /{id}/next-question (Socratic mode)
│   └── POST /{id}/toggle-mode (switch Socratic/Direct)
│
├── /specifications
│   ├── GET /project/{project_id} (list all specs for project)
│   ├── POST / (add spec)
│   ├── DELETE /{id} (delete/forget spec)
│   └── PUT /{id} (update spec)
│
├── /conflicts
│   ├── GET /project/{project_id} (list conflicts)
│   ├── POST /{id}/resolve (resolve conflict)
│   └── GET /{id}/options (show resolution options)
│
├── /quality
│   ├── GET /project/{project_id}/metrics (quality metrics)
│   ├── GET /project/{project_id}/analysis (full analysis)
│   └── GET /project/{project_id}/recommendations (suggestions)
│
└── /admin (testing/debugging)
    ├── GET /health
    ├── POST /db-reset
    └── GET /stats
```

**Why REST (not GraphQL or other)?**
- Simpler for CLI
- Standard, well-understood
- Perfect for React UI later
- Easy to test
- KISS principle

---

## FUTURE MODULES (POST-MVP)

### Phase 2: Project Generation

**When:** After MVP proven, specs/architecture working

**What:** Generate code from specifications

**Adds:**
- CodeGenerationService
- generated_projects table
- Implementation-specific conflict detection
- Code quality validation

### Phase 3: IDE Integration

**When:** After project generation working

**What:** Like Claude Code - IDE extension

**Adds:**
- IDE protocol handlers
- Real-time spec access from IDE
- Code analysis in context
- Debugging integration

### Phase 4: GitHub Integration

**When:** After IDE integration

**What:** Import from GitHub, analyze code

**Adds:**
- GitHub API integration
- Repository analysis service
- Auto-spec generation from code
- Code review integration

### Phase 5: User Learning & Adaptation

**When:** After MVP has user data

**What:** Learn which questions work best, adapt to each user

**Adds:**
- question_effectiveness tracking
- user_learning_profile table
- Behavioral adaptation engine
- Personalized question selection

### Phase 6: Team Collaboration

**When:** After single-user MVP stable

**What:** Multiple users per project, role-based access

**Adds:**
- teams, team_members tables
- team_conflicts detection
- Role-based question assignment
- Consensus-based specification resolution

### Phase 7: Advanced Knowledge Base

**When:** Many projects accumulated

**What:** Semantic search via vectors

**Adds:**
- pgvector extension to specs DB
- embedding generation for documents
- Semantic similarity search
- Learning from similar past projects

### Phase 8: Analytics & Insights

**When:** Multiple projects + data available

**What:** Metrics, patterns, ROI tracking

**Adds:**
- analytics tables
- Dashboard views
- Cost/ROI calculations
- Team productivity metrics

---

## EXTENSIBILITY & SCALABILITY

### How Architecture Supports Future Features

#### **Rule 1: New Features = New Tables (No Refactoring)**

Example: Adding team collaboration

```python
# Before (MVP)
projects table:
  - owner_id
  - name

# After (Phase 6) - just add new tables, no changes to existing
team_members table:
  - team_id
  - user_id
  - role

# OLD queries still work, NEW queries use teams
```

#### **Rule 2: API Endpoints Versioned (/api/v1/)**

```
MVP: /api/v1/projects
Phase 3: /api/v2/projects (if needed)
  - Backward compatible with v1
  - Or v1 still works, v2 is new
  - No breaking changes
```

#### **Rule 3: Services Are Modular**

```
SocraticQuestioningService (MVP) - works standalone
+ QualityControlService (MVP) - works standalone
+ ConflictDetectionService (MVP) - works standalone
+ CodeGenerationService (Phase 2) - doesn't break existing
+ UserLearningService (Phase 5) - doesn't break existing
```

#### **Rule 4: Database Migrations Non-Breaking**

```
-- MVP
CREATE TABLE projects (id, name, owner_id);

-- Phase 2: Add columns (non-breaking)
ALTER TABLE projects ADD COLUMN is_generated BOOLEAN DEFAULT false;

-- Phase 6: Add relationships (non-breaking if done right)
ALTER TABLE projects ADD COLUMN team_id UUID REFERENCES teams(id);
```

#### **Rule 5: Config-Driven Features**

```python
FEATURE_FLAGS = {
    'socratic_questioning': True,
    'direct_chat': True,
    'conflict_detection': True,
    'quality_control': True,
    'code_generation': False,  # Phase 2
    'ide_integration': False,  # Phase 3
    'github_integration': False,  # Phase 4
    'user_learning': False,  # Phase 5
    'team_collaboration': False,  # Phase 6
}

# Can enable features gradually for testing
```

### Scalability Path

**MVP Scale:** 1-10 projects, 1-2 concurrent users

```
1 server (CLI on user's machine)
PostgreSQL auth DB (local or cloud)
PostgreSQL specs DB (local or cloud)
```

**Phase 3 Scale:** 100-1000 projects, 10-50 concurrent users

```
Same setup, possibly cloud-hosted
May shard specs DB by project if needed
Caching layer added if needed
```

**Phase 6+ Scale:** 10,000+ projects, 1000+ concurrent users

```
Multiple API servers (load balanced)
Auth DB: separate, optimized for reads
Specs DB: sharded by project or user
Cache layer (Redis)
CDN for static content
Async job queue (Celery) for heavy work
```

---

## IMPLEMENTATION ROADMAP

### Phase 0: Foundation (Week 1)

- [ ] Create requirements.txt
- [ ] Create database setup scripts
- [ ] Create SQLAlchemy models for both databases
- [ ] Create FastAPI project structure
- [ ] Create initial CLI structure

### Phase 1: MVP Core (Weeks 2-4)

- [ ] Authentication API (register, login)
- [ ] Project management (create, load, list)
- [ ] Session management
- [ ] Socratic questioning service
- [ ] Direct chat service
- [ ] Specification extraction
- [ ] Basic conflict detection (4 types)
- [ ] Maturity calculation
- [ ] Quality Control basic checks
- [ ] CLI commands
- [ ] Testing (unit + integration)

### Phase 2: Polish MVP (Week 5)

- [ ] Error handling
- [ ] Validation
- [ ] Edge cases
- [ ] Documentation
- [ ] Performance optimization
- [ ] User testing with real users

### Phase 3-8: Future Modules (Post-MVP)

See "Future Modules" section above.

---

## DESIGN DECISIONS & RATIONALE

### Decision 1: 2 PostgreSQL Instances (Not 1, Not 3)

| Aspect | 1 DB | 2 DBs | 3+ DBs |
|--------|------|-------|--------|
| Simplicity | ✅ Best | ✓ OK | ❌ Complex |
| Separation | ❌ Poor | ✅ Best | ✓ OK |
| Scaling | ❌ Coupled | ✅ Independent | ✓ Independent |
| Security | ❌ Mixed | ✅ Isolated | ✓ Isolated |
| Operations | ✅ Simple | ✓ OK | ❌ Complex |

**Chosen: 2 DBs**
- Addresses real scalability needs
- Maintains operational simplicity (both PostgreSQL)
- Future-proofs for team collaboration, IDE integration
- Security benefit (auth isolated)

### Decision 2: SQLAlchemy ORM (Not Raw SQL)

| Aspect | Raw SQL | SQLAlchemy | Tortoise |
|--------|---------|-----------|----------|
| Type Safety | ❌ Manual | ✅ Automatic | ✓ OK |
| Maintainability | ❌ Hard | ✅ Easy | ✓ OK |
| Performance | ✅ Best | ✓ OK | ✓ OK |
| Learning | ❌ High | ✓ OK | ✓ OK |
| Flexibility | ✓ OK | ✅ High | ✓ OK |

**Chosen: SQLAlchemy**
- Proven, mature, stable
- Works perfectly with Python 3.12
- Pydantic integration
- Flexible (can use ORM or Core SQL as needed)

### Decision 3: No Vectors in MVP

| Feature | Needed Now? | MVP Value? | Complexity | Decision |
|---------|------------|-----------|-----------|----------|
| Semantic search | No | 0% | High | ❌ Skip |
| Full-text search | No | 0% | Low | ✓ PostgreSQL built-in |
| Embeddings | No | 0% | Medium | ❌ Skip |

**Chosen: PostgreSQL full-text search for MVP, vectors Phase 5+**
- MVP doesn't need semantic search
- PostgreSQL native search sufficient
- Adding vectors later is non-breaking
- Saves implementation time, reduces complexity

### Decision 4: Deep Compatibility Testing (Not Shallow)

| Approach | Speed | Accuracy | MVP Fit | Cost |
|----------|-------|----------|---------|------|
| Shallow (DB lookup) | ✅ Fast | ❌ 70% accurate | ✓ OK | Low |
| Deep (actual imports) | ⚠️ Medium | ✅ 99% accurate | ✅ Best | Medium |

**Chosen: Deep Testing**
- Catches real version conflicts
- Prevents "thought it would work" failures
- Supports real-time testing in Design phase
- Worth the complexity

### Decision 5: CLI First, UI Later

| Aspect | CLI First | UI First | Both |
|--------|-----------|----------|------|
| Speed to MVP | ✅ Fast | ❌ Slow | ❌ Very slow |
| Testability | ✅ Easy | ⚠️ Hard | ⚠️ Hard |
| Flexibility | ✅ High | ❌ Low | ✓ OK |
| User Experience | ⚠️ OK | ✅ Best | ✅ Best |

**Chosen: CLI First**
- Allows rapid iteration on core logic
- Easy to test and debug
- Can replace with UI later
- Real users can test core logic early

---

## SUMMARY

### MVP (This Phase)

**What's Included:**
- 2 PostgreSQL databases (auth + specs)
- FastAPI backend
- SQLAlchemy ORM
- Socratic questioning engine
- Direct chat mode
- Real-time conflict detection
- Maturity system (dynamic)
- Quality Control (bias, coverage, bad patterns)
- Deep real-time compatibility testing
- CLI interface
- User rules system (stored, ready for QC to use)

**What's NOT Included:**
- Code generation
- IDE integration
- GitHub integration
- User learning algorithms
- Team collaboration
- Vector embeddings/semantic search
- UI
- Analytics/billing

### Why This Architecture Works

1. **Solves Core Problems** (VISION.md requirements)
   - ✅ Persistent context (database stores everything)
   - ✅ Prevents greedy decisions (Quality Control + maturity threshold)
   - ✅ Gathers complete specs (Socratic + Direct + real-time testing)

2. **Foundation for Future**
   - ✅ Can add code generation without refactoring
   - ✅ Can add IDE integration without breaking API
   - ✅ Can add vectors later (non-breaking ALTER TABLE)
   - ✅ Can add team collab without restructuring auth

3. **Maintainable**
   - ✅ Clear separation (auth DB vs specs DB)
   - ✅ Modular services (each feature = separate service)
   - ✅ Type safe (SQLAlchemy + Pydantic)
   - ✅ Testable (can mock, can use test DB)

4. **Practical**
   - ✅ Python 3.12 stable, all deps work
   - ✅ PostgreSQL battle-tested
   - ✅ FastAPI proven with React
   - ✅ Can be built in reasonable time

---

## NEXT STEPS

1. **Get Approval** on this architecture
2. **Create requirements.txt** with all dependencies
3. **Initialize PostgreSQL databases** (auth + specs schemas)
4. **Implement Phase 0: Foundation**
5. **Implement Phase 1: MVP Core**
6. **Test with real users**

---

**Status:** READY FOR IMPLEMENTATION

**Approved:** [Your signature here]
**Date:** November 4, 2025


# Interconnections Map - Complete System Data Flow

**Purpose:** This document shows EVERY interconnection between components, phases, and files. This was the #1 missing piece in previous attempts.

**Critical Rule:** No file/component should be created without understanding:
1. What it depends on (inputs)
2. What depends on it (outputs)
3. How data flows through it

---

## 📊 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│                  (Question Answer / Chat Message)                │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI ENDPOINT                            │
│  - Validates JWT token                                           │
│  - Extracts user_id, session_id                                  │
│  - Passes to AgentOrchestrator                                   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATOR                             │
│  1. Determine which agent to use (capability-based routing)      │
│  2. Load user context (preferences, behavior profile)            │
│  3. Check if major operation → Quality Control                   │
│  4. Route to agent                                               │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ├──────────────┬────────────────┬───────
                            ▼              ▼                ▼
┌──────────────────────┐   ┌──────────────────┐   ┌───────────────┐
│  SOCRATIC COUNSELOR  │   │ CONTEXT ANALYZER │   │ CODE GENERATOR│
│  - Generate question │   │ - Extract specs  │   │ - Generate    │
│  - Load project ctx  │   │ - Detect conflicts│   │   code        │
│  - Call Claude API   │   │ - Save to DB     │   │               │
└──────────┬───────────┘   └────────┬─────────┘   └───────┬───────┘
           │                        │                      │
           │                        │                      │
           └────────────────────────┼──────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                         │
│  - socrates_auth: users, auth_tokens                             │
│  - socrates_specs: projects, sessions, specs, conflicts          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Component Interconnection Matrix

| Component | Depends On | Provides To | Data Format |
|-----------|-----------|-------------|-------------|
| **FastAPI Endpoints** | - | AgentOrchestrator | `{'action': str, 'data': dict, 'user_id': str}` |
| **AgentOrchestrator** | ServiceContainer, All Agents | FastAPI Endpoints | `{'success': bool, 'data': dict}` |
| **ServiceContainer** | Config, Database, Logger | All Agents | Service instances |
| **BaseAgent** | ServiceContainer | AgentOrchestrator | Standardized responses |
| **ProjectManagerAgent** | Database (projects, users) | All other agents | Project context |
| **SocraticCounselorAgent** | Claude API, Project context | ContextAnalyzerAgent | Questions |
| **ContextAnalyzerAgent** | Claude API, Existing specs | ConflictDetectorAgent | Extracted specs |
| **ConflictDetectorAgent** | Existing specs, New specs | User (via API) | Conflict records |
| **CodeGeneratorAgent** | All specifications | User (via API) | Generated code |
| **Database Models** | - | All Agents | SQLAlchemy ORM objects |
| **Quality Control** | Agent requests, Project state | AgentOrchestrator | Verification metadata |
| **Claude API Client** | API key, Prompts | All agent

s | LLM responses |

---

## 📦 Phase-to-Phase Interconnections

### Phase 0 → Phase 1
**What Phase 0 Provides:**
- Complete documentation
- Architecture decisions
- Database schema design
- Clear success criteria

**What Phase 1 Expects:**
- `DATABASE_SCHEMA.md` → Create migration files
- `ARCHITECTURE.md` → Implement BaseAgent
- `PROJECT_STRUCTURE.md` → Create directory structure

**Verification Gate:**
- ✅ Can connect to PostgreSQL
- ✅ Can create users
- ✅ Can authenticate
- ✅ BaseAgent can be instantiated
- ✅ Tests pass: `test_phase_1_infrastructure.py`

### Phase 1 → Phase 2
**What Phase 1 Provides:**
```python
# From Phase 1:
class BaseAgent:
    def __init__(self, agent_id, name, services):
        self.agent_id = agent_id
        self.services = services
        self.db = services.get_database()
        self.logger = services.get_logger()

    def process_request(self, action, data):
        # Standardized request processing
        pass

class AgentOrchestrator:
    def route_request(self, agent_id, action, data):
        # Route to appropriate agent
        pass

# Database Models:
- User (id, email, hashed_password)
- Project (id, user_id, name, phase, maturity)
- Session (id, project_id, mode, status)
```

**What Phase 2 Expects:**
- `BaseAgent` class available for inheritance
- `AgentOrchestrator` can register new agents
- Database has `projects`, `sessions` tables

**Verification Gate:**
- ✅ Can create ProjectManagerAgent(BaseAgent)
- ✅ Can register agent with orchestrator
- ✅ Can route request to agent
- ✅ Agent can access database via services
- ✅ Tests pass: `test_phase_2_core_agents.py`

### Phase 2 → Phase 3
**What Phase 2 Provides:**
```python
# 3 Working Agents:
class ProjectManagerAgent(BaseAgent):
    def _create_project(self, data):
        # Creates project in database
        return project_id

class SocraticCounselorAgent(BaseAgent):
    def _generate_question(self, data):
        # Calls Claude API, returns question
        return {'question_id': str, 'text': str}

class ContextAnalyzerAgent(BaseAgent):
    def _extract_specifications(self, data):
        # Extracts specs from user answer
        return {'specs': [...], 'extracted_count': int}

# Database Tables:
- specifications (id, project_id, category, key, value, confidence)
- questions (id, project_id, session_id, text, category)
```

**What Phase 3 Expects:**
- `ContextAnalyzerAgent._extract_specifications()` returns structured specs
- Database has `specifications` table
- Can query existing specs by project_id + category + key

**Phase 3 Implementation:**
```python
class ConflictDetectorAgent(BaseAgent):
    def _detect_conflicts(self, data):
        # Get new specs from ContextAnalyzerAgent result
        new_specs = data['new_specs']
        project_id = data['project_id']

        # Query EXISTING specs (depends on specifications table from Phase 2)
        existing_specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Compare
        conflicts = []
        for new_spec in new_specs:
            for existing in existing_specs:
                if self._is_conflict(new_spec, existing):
                    conflicts.append(...)

        return {'conflicts': conflicts}
```

**Verification Gate:**
- ✅ Can detect contradicting specs
- ✅ Creates conflict records in database
- ✅ Returns conflicts to user for resolution
- ✅ Tests pass: `test_phase_3_conflict_detection.py`

### Phase 3 → Phase 4
**What Phase 3 Provides:**
```python
# Conflict Detection:
class ConflictDetectorAgent(BaseAgent):
    def _detect_conflicts(self, data):
        return {'conflicts': [...], 'has_conflicts': bool}

# Database Tables:
- conflicts (id, project_id, old_spec_id, new_spec_value, resolution)

# Modified ContextAnalyzerAgent flow:
def _extract_specifications(self, data):
    specs = self._extract_from_answer(...)

    # CHECK FOR CONFLICTS (new in Phase 3)
    conflicts = self.orchestrator.route_request(
        'conflict_detector', 'detect_conflicts',
        {'new_specs': specs, 'project_id': data['project_id']}
    )

    if conflicts['has_conflicts']:
        return {'success': False, 'conflicts': conflicts}
    else:
        self._save_specs(specs)
        return {'success': True, 'specs_saved': len(specs)}
```

**What Phase 4 Expects:**
- Specs saved only if no conflicts
- Project maturity calculated based on specs
- Can query all specs for a project

**Phase 4 Implementation:**
```python
class CodeGeneratorAgent(BaseAgent):
    def _generate_code(self, data):
        project_id = data['project_id']

        # Check maturity (depends on specifications from Phase 2+3)
        project = self.db.query(Project).get(project_id)
        if project.maturity_score < 100.0:
            return {'success': False, 'error': 'Maturity not reached'}

        # Load ALL specifications
        specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Group by category
        grouped_specs = self._group_specs_by_category(specs)

        # Build comprehensive prompt
        prompt = self._build_code_generation_prompt(grouped_specs)

        # Call Claude API
        code = self.claude_client.call(prompt, max_tokens=15000)

        return {'success': True, 'code': code}
```

**Verification Gate:**
- ✅ Can calculate maturity from specs
- ✅ Blocks code generation if maturity < 100%
- ✅ Generates valid code when maturity = 100%
- ✅ Tests pass: `test_phase_4_code_generation.py`

### Phase 4 → Phase 5
**What Phase 4 Provides:**
- Working code generation pipeline
- Maturity calculation logic

**What Phase 5 Adds:**
**Quality Control BEFORE code generation**

```python
class AgentOrchestrator:
    def route_request(self, agent_id, action, data):
        # Existing code...

        # NEW in Phase 5: Quality Control Gate
        if self._is_major_operation(agent_id, action):
            quality_result = self.quality_controller.verify(
                agent_id, action, data
            )

            if quality_result['is_blocking']:
                return {
                    'success': False,
                    'blocked_by': 'quality_control',
                    'reason': quality_result['reason'],
                    'suggestions': quality_result['suggestions']
                }

        # Route to agent
        result = agent.process_request(action, data)
        return result
```

**Quality Control Checks:**
1. **Before generate_question:** Check for bias patterns
2. **Before extract_specs:** Check coverage gaps
3. **Before generate_code:** Check maturity + missing categories

**Verification Gate:**
- ✅ Quality control blocks biased questions
- ✅ Quality control blocks premature code generation
- ✅ Quality control suggests gap-filling actions
- ✅ Tests pass: `test_phase_5_quality_control.py`

---

## 🗄️ Database Table Dependencies

### Creation Order (Due to Foreign Keys):

```
**Database 1: socrates_auth**
Phase 1:
1. users (no dependencies)
2. refresh_tokens (→ users)
3. password_reset_requests (→ users)
4. audit_logs (→ users)
5. user_rules (→ users)

**Database 2: socrates_specs**
Phase 1-2:
6. projects (→ socrates_auth.users)
7. sessions (→ projects)
8. conversation_history (→ sessions)
9. questions (→ projects, → sessions)
10. specifications (→ projects)

Phase 3:
11. conflicts (→ projects, → specifications)
12. quality_metrics (→ projects)
13. maturity_tracking (→ projects)
14. test_results (→ projects, → sessions)

Phase 4:
15. generated_projects (→ projects)
16. generated_files (→ generated_projects)

Phase 5:
17. user_behavior_patterns (→ socrates_auth.users)
18. question_effectiveness (→ socrates_auth.users)
19. knowledge_base_documents (→ projects)

Phase 6:
20. teams (→ socrates_auth.users)
21. team_members (→ teams, → socrates_auth.users)
22. team_invitations (→ teams, → socrates_auth.users)
23. project_shares (→ projects, → teams)
24. api_keys (→ socrates_auth.users)
25. llm_usage_tracking (→ projects)
```

### Query Dependencies (What Queries Need What Tables):

| Operation | Tables Queried | Order |
|-----------|---------------|-------|
| Create project | users, projects | users first (FK check) |
| Generate question | projects, questions, specifications | projects → specs → generate |
| Extract specs | sessions, specifications | session exists check → save specs |
| Detect conflicts | specifications (existing), conflicts | query existing → compare → save conflict |
| Calculate maturity | specifications | group by category → calculate |
| Generate code | projects, specifications | verify maturity → load all specs |

---

## 📁 File Interconnection Map

### Directory Structure with Dependencies:

```
backend/
├── app/
│   ├── core/                    # PHASE 1 - Foundation (no dependencies)
│   │   ├── config.py           # Loads env vars
│   │   ├── database.py         # Depends on: config.py
│   │   ├── security.py         # JWT handling
│   │   └── dependencies.py     # ServiceContainer - Depends on: database.py, config.py
│   │
│   ├── models/                  # PHASE 1-4 - Data models
│   │   ├── base.py             # Depends on: core/database.py
│   │   ├── user.py             # Depends on: base.py (Phase 1)
│   │   ├── project.py          # Depends on: base.py, user.py (Phase 2)
│   │   ├── session.py          # Depends on: base.py, project.py, user.py (Phase 2)
│   │   ├── specification.py    # Depends on: base.py, project.py (Phase 3)
│   │   └── conflict.py         # Depends on: base.py, project.py, specification.py (Phase 3)
│   │
│   ├── agents/                  # PHASE 1-6 - Agent system
│   │   ├── base.py             # Depends on: core/dependencies.py (Phase 1)
│   │   ├── orchestrator.py     # Depends on: base.py (Phase 1)
│   │   ├── project.py          # Depends on: base.py, models/project.py (Phase 2)
│   │   ├── socratic.py         # Depends on: base.py, models/question.py (Phase 2)
│   │   ├── context.py          # Depends on: base.py, models/specification.py (Phase 2)
│   │   ├── conflict.py         # Depends on: base.py, models/conflict.py, agents/context.py (Phase 3)
│   │   ├── code.py             # Depends on: base.py, models/specification.py (Phase 4)
│   │   └── quality.py          # Depends on: base.py, orchestrator.py (Phase 5)
│   │
│   ├── api/                     # PHASE 2-4 - API Routes
│   │   ├── deps.py             # Auth dependencies
│   │   ├── projects.py         # Depends on: agents/project.py (Phase 2)
│   │   ├── sessions.py         # Depends on: agents/socratic.py, agents/context.py (Phase 2)
│   │   └── code.py             # Depends on: agents/code.py (Phase 4)
│   │
│   └── main.py                 # Depends on: core/*, api/*, agents/orchestrator.py
│
├── tests/                       # Tests mirror app/ structure
│   ├── test_phase_1_infrastructure.py    # Tests: core/, models/base, models/user
│   ├── test_phase_2_core_agents.py       # Tests: agents/project, socratic, context
│   ├── test_phase_3_conflict_detection.py # Tests: agents/conflict
│   ├── test_phase_4_code_generation.py    # Tests: agents/code
│   └── test_phase_5_quality_control.py    # Tests: agents/quality
│
├── alembic/                     # Database migrations (Phase 1+)
│   └── versions/
│       ├── 001_create_users.py          # Phase 1
│       ├── 002_create_projects.py       # Phase 2
│       ├── 003_create_specifications.py # Phase 3
│       └── ...
│
└── requirements.txt             # All dependencies listed
```

### Import Rules (STRICT):

**✅ ALLOWED:**
```python
# Lower layer → Higher layer (OK)
from app.core.database import get_db
from app.models.user import User
from app.agents.base import BaseAgent

# Same layer (OK if no circular dependency)
from app.agents.socratic import SocraticCounselorAgent  # in orchestrator.py
```

**❌ FORBIDDEN:**
```python
# Higher layer → Lower layer (CIRCULAR!)
from app.agents.orchestrator import orchestrator  # in models/project.py - NO!

# Fallback imports (MASKED FAILURES!)
try:
    from app.core import ServiceContainer
except ImportError:
    from fallback_helpers import ServiceContainer  # ABSOLUTELY NOT!
```

---

## 🔄 Request Flow: User Answer → Spec Storage

**Detailed Data Flow with All Interconnections:**

```python
# 1. USER SUBMITS ANSWER
POST /api/sessions/{session_id}/answer
Body: {"question_id": "q_123", "answer": "I want to use Python with FastAPI"}

# 2. FASTAPI ENDPOINT (api/sessions.py)
@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    answer_data: AnswerRequest,
    current_user: User = Depends(get_current_user),  # Depends on: core/security.py
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)  # Depends on: agents/orchestrator.py
):
    result = orchestrator.route_request(
        agent_id='context',
        action='extract_specifications',
        data={
            'session_id': session_id,
            'question_id': answer_data.question_id,
            'answer': answer_data.answer,
            'user_id': current_user.id  # From authentication
        }
    )
    return result

# 3. AGENT ORCHESTRATOR (agents/orchestrator.py)
class AgentOrchestrator:
    def route_request(self, agent_id='context', action='extract_specifications', data={}):
        # Load agent
        agent = self.agents['context']  # ContextAnalyzerAgent instance

        # Check if major operation
        if self._is_major_operation('context', 'extract_specifications'):
            # Phase 5: Quality Control (not yet implemented in Phase 2)
            pass

        # Route to agent
        result = agent.process_request(action, data)
        return result

# 4. CONTEXT ANALYZER AGENT (agents/context.py)
class ContextAnalyzerAgent(BaseAgent):
    def process_request(self, action='extract_specifications', data={}):
        # BaseAgent handles standard processing
        method = f"_{action}"  # _extract_specifications
        return getattr(self, method)(data)

    def _extract_specifications(self, data):
        session_id = data['session_id']
        question_id = data['question_id']
        answer = data['answer']

        # Load context (DEPENDS ON: models/session, models/project, models/question)
        session = self.db.query(Session).get(session_id)
        project = self.db.query(Project).get(session.project_id)
        question = self.db.query(Question).get(question_id)
        existing_specs = self.db.query(Specification).filter_by(
            project_id=project.id
        ).all()

        # Build extraction prompt
        prompt = self._build_extraction_prompt(question, answer, existing_specs)

        # Call Claude API (DEPENDS ON: core/dependencies.py → claude_client)
        response = self.claude_client.call(prompt)
        extracted_specs = self._parse_response(response)

        # PHASE 3 INTEGRATION: Check for conflicts
        conflicts = self.orchestrator.route_request(
            'conflict',
            'detect_conflicts',
            {
                'new_specs': extracted_specs,
                'existing_specs': existing_specs,
                'project_id': project.id
            }
        )

        # If conflicts, STOP and return
        if conflicts['has_conflicts']:
            return {
                'success': False,
                'conflicts_detected': True,
                'conflicts': conflicts['conflicts']
            }

        # No conflicts → Save specs (DEPENDS ON: models/specification)
        saved_specs = []
        for spec in extracted_specs:
            spec_obj = Specification(
                project_id=project.id,
                category=spec['category'],
                key=spec['key'],
                value=spec['value'],
                source='socratic_question',
                source_id=question_id,
                confidence=spec['confidence']
            )
            self.db.add(spec_obj)
            saved_specs.append(spec_obj)

        self.db.commit()

        # Update maturity (DEPENDS ON: models/project, maturity calculation logic)
        new_maturity = self._calculate_maturity(project.id)
        project.maturity_score = new_maturity
        self.db.commit()

        return {
            'success': True,
            'specs_extracted': len(saved_specs),
            'maturity_score': new_maturity,
            'conflicts_detected': False
        }

# 5. RESPONSE BACK TO USER
{
  "success": true,
  "specs_extracted": 2,
  "maturity_score": 23.5,
  "specifications": [
    {"category": "tech_stack", "key": "backend_language", "value": "Python"},
    {"category": "tech_stack", "key": "api_framework", "value": "FastAPI"}
  ]
}
```

**Interconnections in This Flow:**
1. **FastAPI** → **Auth Middleware** (get_current_user)
2. **FastAPI** → **AgentOrchestrator** (get_orchestrator)
3. **AgentOrchestrator** → **ContextAnalyzerAgent**
4. **ContextAnalyzerAgent** → **Database** (Session, Project, Question models)
5. **ContextAnalyzerAgent** → **Claude API** (via ServiceContainer)
6. **ContextAnalyzerAgent** → **ConflictDetectorAgent** (via Orchestrator)
7. **ContextAnalyzerAgent** → **Database** (Save Specification models)
8. **ContextAnalyzerAgent** → **Maturity Calculator** (updates Project.maturity_score)

---

## ✅ Verification Checklist for Each Phase

### Phase 1 Verification:
Before proceeding to Phase 2, verify ALL of these:

- [ ] Can create database connection
- [ ] Can create `users` table
- [ ] Can create user with hashed password
- [ ] Can authenticate user and get JWT token
- [ ] Can create `projects` table
- [ ] `BaseAgent` class can be imported
- [ ] `AgentOrchestrator` class can be imported
- [ ] `ServiceContainer` provides: config, database, logger
- [ ] Tests pass: `pytest tests/test_phase_1_infrastructure.py`
- [ ] No import errors when running `python -c "from app.core import *"`

### Phase 2 Verification:
Before proceeding to Phase 3, verify ALL of these:

- [ ] Can create ProjectManagerAgent instance
- [ ] Can register agent with orchestrator
- [ ] Can route request to agent via orchestrator
- [ ] ProjectManagerAgent can create project in database
- [ ] SocraticCounselorAgent can generate question via Claude API
- [ ] ContextAnalyzerAgent can extract specs from answer
- [ ] Extracted specs are saved to `specifications` table
- [ ] Can query specifications by project_id
- [ ] Tests pass: `pytest tests/test_phase_2_core_agents.py`
- [ ] Integration test: Create project → Ask question → Submit answer → Specs saved

### Phase 3 Verification:
Before proceeding to Phase 4, verify ALL of these:

- [ ] ConflictDetectorAgent can compare new vs existing specs
- [ ] Conflicting specs are detected (test with contradicting answers)
- [ ] Conflicts are saved to `conflicts` table
- [ ] User receives conflict resolution options
- [ ] Resolved conflicts update database correctly
- [ ] Non-conflicting specs are saved immediately
- [ ] Tests pass: `pytest tests/test_phase_3_conflict_detection.py`
- [ ] Integration test: Answer question → Change answer (conflict) → Resolve → Updated

### Phase 4 Verification:
Before proceeding to Phase 5, verify ALL of these:

- [ ] Maturity calculation works (based on specs coverage)
- [ ] Code generation is blocked when maturity < 100%
- [ ] Code generation succeeds when maturity = 100%
- [ ] Generated code includes ALL specifications from database
- [ ] Generated code is valid (syntax check)
- [ ] Tests pass: `pytest tests/test_phase_4_code_generation.py`
- [ ] Integration test: Complete project specs → Generate code → Code validates

---

## 🔴 Critical Failure Points (From Previous Attempts)

### 1. **Fallback Helpers** (The #1 Killer)
**Problem:** Archive had `fallback_helpers.py` that provided dummy implementations when dependencies were missing.

**Why It Failed:**
```python
# In agents/base.py
try:
    from ..core import ServiceContainer
except ImportError:
    from .fallback_helpers import ServiceContainer  # Returns empty objects!

# Result:
services.get_config() → {}  # Empty dict, no error
services.get_database() → None  # None, no error
# Code appears to work but silently fails!
```

**Solution for Socrates2:**
```python
# STRICT IMPORTS - No fallbacks!
from app.core import ServiceContainer  # If this fails, LET IT FAIL LOUD

# If import fails:
# ImportError: cannot import name 'ServiceContainer' from 'app.core'
# → GOOD! We know immediately what's wrong.
```

### 2. **Circular Dependencies**
**Problem:** Agent imports Model, Model imports Agent

**Solution:**
- Strict layered architecture
- Models NEVER import Agents
- Agents import Models (one direction only)

### 3. **Missing Verification Gates**
**Problem:** Phase 2 implemented before Phase 1 was verified

**Solution:**
- Mandatory test suite for each phase
- Cannot merge Phase N+1 until Phase N tests pass
- Checklist above must be completed

---

## 📋 Summary: Interconnection Principles

1. **Every component MUST declare:**
   - What it depends on (imports)
   - What it provides (exports)
   - What data it expects (input schema)
   - What data it returns (output schema)

2. **Phase transitions MUST verify:**
   - Previous phase fully working
   - All dependencies available
   - Tests passing
   - Integration test successful

3. **NO silent failures:**
   - No fallback imports
   - No try/except ImportError
   - Fail fast with clear errors

4. **Data flow MUST be explicit:**
   - No magic globals
   - No singletons (except database engine)
   - Dependency injection everywhere

---

**Next Document:** [PHASES.md](./PHASES.md) - Detailed implementation plan for each phase

**Reference:** [Old Repo Archive Analysis](https://github.com/Nireus79/Socrates/blob/main/SOCRATES_ARCHIVE_ANALYSIS.md)

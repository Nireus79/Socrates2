# Library API Implementation Plan

## Phase 1: Create Core Public API (socrates/__init__.py)

### Step 1: Create Package Structure

File location: `socrates/__init__.py`

Main sections to include:
1. Configuration (Settings, get_settings)
2. Dependency Injection (ServiceContainer)
3. Database connections
4. Security & JWT functions
5. Pure business logic engines
6. Data models
7. Subscription management
8. Logging utilities
9. Domain framework exports
10. Agent framework exports
11. Database models

### Step 2: Verify Imports

Test that all imports work and there are no circular dependencies.

---

## Phase 2: Documentation

Create 3 key docs:
1. API_REFERENCE.md - What each export does
2. ARCHITECTURE.md - How components work together
3. EXAMPLES.md - How to use them

---

## Phase 3: Examples

Create `examples/basic_usage.py` showing:
- Question generation
- Conflict detection
- Bias detection
- User learning profiles
- Pure engine usage (no database)

---

## Phase 4: Testing

Test suite for:
- Pure engines (no database needed)
- Database integration (optional)
- Data model conversions
- Security functions

Key: Pure engines should pass tests WITHOUT any database setup

---

## Phase 5: PyPI Publishing

Setup:
- pyproject.toml or setup.py
- Version management
- README.md
- LICENSE

---

## Priority - What MUST Export

CRITICAL (Foundation):
- ServiceContainer
- Settings, get_settings
- Database sessions (SessionLocalAuth, SessionLocalSpecs, get_db_auth, get_db_specs)
- JWT functions (create_access_token, decode_access_token)
- All dataclasses (ProjectData, SpecificationData, etc.)
- All conversions (*_db_to_data functions)

HIGH (Core Features):
- QuestionGenerator
- ConflictDetectionEngine
- BiasDetectionEngine
- LearningEngine
- NLUService

MEDIUM (Nice to have):
- Action logging
- Rate limiting
- Subscription management
- Validators

ALREADY AVAILABLE:
- All 29+ SQLAlchemy models
- All 7 domains
- All 9 agents
- AgentOrchestrator


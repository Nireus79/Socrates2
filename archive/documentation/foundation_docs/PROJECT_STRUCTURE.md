# Socrates - Project Structure

**Last Updated:** 2025-11-05
**Status:** Foundation - To be implemented in Phase 1

---

## Directory Structure

```
socrates/
├── README.md
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore
│
├── docs/                      # All documentation (this folder's contents)
│   ├── VISION.md
│   ├── ARCHITECTURE.md
│   ├── TECHNOLOGY_STACK.md
│   ├── USER_WORKFLOW.md
│   ├── SYSTEM_WORKFLOW.md
│   ├── PROJECT_STRUCTURE.md (this file)
│   ├── INTERCONNECTIONS_MAP.md
│   ├── PHASES_SUMMARY.md
│   ├── PHASE_0.md through PHASE_5.md
│   ├── ARCHIVE_PATTERNS.md
│   ├── ARCHIVE_ANTIPATTERNS.md
│   ├── WHY_PREVIOUS_ATTEMPTS_FAILED.md
│   └── SQLALCHEMY_BEST_PRACTICES.md
│
├── backend/                   # FastAPI backend application
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Configuration management
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   │
│   │   ├── core/             # Core infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── database.py   # Database connection management
│   │   │   ├── dependencies.py  # FastAPI dependencies (ServiceContainer)
│   │   │   ├── config.py     # Configuration classes
│   │   │   ├── security.py   # Authentication & authorization
│   │   │   └── logging.py    # Logging configuration
│   │   │
│   │   ├── models/           # SQLAlchemy models (database schema)
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # BaseModel class
│   │   │   ├── user.py       # User model (socrates_auth)
│   │   │   ├── project.py    # Project model (socrates_specs)
│   │   │   ├── session.py    # Session model
│   │   │   ├── specification.py  # Specification model
│   │   │   ├── conflict.py   # Conflict model
│   │   │   ├── conversation_history.py
│   │   │   ├── quality_metrics.py
│   │   │   ├── maturity_tracking.py
│   │   │   ├── knowledge_base.py
│   │   │   └── test_results.py
│   │   │
│   │   ├── schemas/          # Pydantic models (API request/response)
│   │   │   ├── __init__.py
│   │   │   ├── user.py       # UserCreate, UserResponse, UserLogin
│   │   │   ├── project.py    # ProjectCreate, ProjectResponse
│   │   │   ├── session.py    # SessionCreate, SessionResponse
│   │   │   ├── specification.py
│   │   │   ├── conflict.py
│   │   │   └── common.py     # Shared schemas (pagination, etc.)
│   │   │
│   │   ├── agents/           # Agent-based architecture
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # BaseAgent class
│   │   │   ├── orchestrator.py  # AgentOrchestrator
│   │   │   ├── project_manager.py  # ProjectManagerAgent
│   │   │   ├── socratic_counselor.py  # SocraticCounselorAgent
│   │   │   ├── context_analyzer.py  # ContextAnalyzerAgent
│   │   │   ├── conflict_detector.py  # ConflictDetectorAgent
│   │   │   ├── code_generator.py  # CodeGeneratorAgent (Phase 4+)
│   │   │   ├── chat.py       # ChatAgent
│   │   │   ├── user_manager.py  # UserManagerAgent
│   │   │   ├── document_processor.py  # DocumentProcessorAgent (Phase 4+)
│   │   │   ├── system_monitor.py  # SystemMonitorAgent (Phase 3+)
│   │   │   └── architecture_optimizer.py  # ArchitectureOptimizerAgent (Phase 5+)
│   │   │
│   │   ├── services/         # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py  # Authentication logic
│   │   │   ├── project_service.py
│   │   │   ├── session_service.py
│   │   │   ├── socratic_service.py  # Socratic questioning engine
│   │   │   ├── context_service.py
│   │   │   ├── conflict_detection_service.py
│   │   │   ├── quality_control_service.py
│   │   │   ├── maturity_service.py
│   │   │   ├── compatibility_testing_service.py
│   │   │   └── llm/          # LLM provider abstraction
│   │   │       ├── __init__.py
│   │   │       ├── base_provider.py  # BaseLLMProvider
│   │   │       ├── claude_provider.py  # Primary (MVP)
│   │   │       ├── openai_provider.py  # Phase 3+
│   │   │       ├── gemini_provider.py  # Phase 3+
│   │   │       └── ollama_provider.py  # Phase 3+
│   │   │
│   │   ├── repositories/     # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py  # BaseRepository class
│   │   │   ├── user_repository.py
│   │   │   ├── project_repository.py
│   │   │   ├── session_repository.py
│   │   │   ├── specification_repository.py
│   │   │   ├── conflict_repository.py
│   │   │   └── conversation_repository.py
│   │   │
│   │   ├── api/              # FastAPI routes
│   │   │   ├── __init__.py
│   │   │   ├── routes.py     # Main router
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── projects.py   # Project management endpoints
│   │   │   ├── sessions.py   # Session endpoints
│   │   │   ├── specifications.py
│   │   │   ├── conflicts.py
│   │   │   ├── quality.py    # Quality metrics endpoints
│   │   │   └── health.py     # Health check endpoints
│   │   │
│   │   └── utils/            # Utility functions
│   │       ├── __init__.py
│   │       ├── datetime_helpers.py
│   │       ├── validation.py
│   │       └── text_processing.py
│   │
│   ├── tests/                # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py       # Pytest fixtures
│   │   ├── test_database_persistence.py  # CRITICAL: Archive killer test
│   │   ├── test_models/
│   │   ├── test_agents/
│   │   ├── test_services/
│   │   ├── test_repositories/
│   │   └── test_api/
│   │
│   └── alembic/              # Database migrations
│       ├── versions/
│       ├── env.py
│       ├── script.py.mako
│       └── alembic.ini
│
├── cli/                      # Command-line interface (MVP)
│   ├── __init__.py
│   ├── main.py               # CLI entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── auth.py           # /login, /register
│   │   ├── projects.py       # /create, /load, /list
│   │   ├── chat.py           # /chat, /socratic, /toggle
│   │   └── admin.py          # /status, /debug
│   └── utils/
│       ├── __init__.py
│       └── display.py        # Output formatting
│
├── scripts/                  # Utility scripts
│   ├── setup_databases.py    # Initialize both PostgreSQL databases
│   ├── seed_data.py          # Seed test data
│   └── run_migrations.py     # Run Alembic migrations
│
└── data/                     # Local data (development only)
    └── .gitignore            # Ignore all files in data/
```

---

## Two-Database Setup

### Database 1: `socrates_auth`

**Connection:** `postgresql://localhost:5432/socrates_auth`

**Managed by:**
- `backend/app/models/user.py`
- `backend/app/repositories/user_repository.py`
- `backend/alembic/env.py` (auth migrations)

**Tables:**
- users
- user_rules (JSONB)

### Database 2: `socrates_specs`

**Connection:** `postgresql://localhost:5433/socrates_specs`

**Managed by:**
- All other models in `backend/app/models/`
- All other repositories
- `backend/alembic/env.py` (specs migrations)

**Tables:**
- projects
- sessions
- specifications
- conversation_history
- conflicts
- quality_metrics
- maturity_tracking
- knowledge_base
- test_results

---

## Key Files Explained

### `backend/main.py`
- FastAPI application factory
- Registers all routers
- Configures middleware (CORS, logging, error handling)
- Startup/shutdown events (database connections)

### `backend/app/core/dependencies.py`
- ServiceContainer class (dependency injection)
- FastAPI dependencies (get_db, get_current_user, get_orchestrator)
- NO fallback helpers (fail-fast principle)

### `backend/app/agents/base.py`
- BaseAgent abstract class
- Dependency injection pattern
- Capability declaration system
- Auto-context loading (user preferences)
- Request processing framework

### `backend/app/agents/orchestrator.py`
- AgentOrchestrator class
- Routes requests by agent_id or capability
- Quality control integration
- Agent lifecycle management

### `backend/app/services/socratic_service.py`
- Socratic questioning engine
- Dynamic question generation (7 roles)
- Answer analysis and spec extraction
- Vagueness detection
- Follow-up question generation

### `backend/app/services/quality_control_service.py`
- QualityControlService class
- Bias detection (6 types)
- Coverage tracking (10 areas)
- Path optimization
- Tunnel vision detection

### `backend/app/services/maturity_service.py`
- MaturityService class
- Dynamic maturity calculation (10 categories)
- Phase transition gating
- Coverage gap identification

### `backend/tests/test_database_persistence.py`
- **CRITICAL TEST:** Ensures data persists after session closes
- Tests the exact bug that killed previous attempt
- MUST PASS before Phase 2

---

## Import Rules (CRITICAL)

**From ARCHIVE_ANTIPATTERNS.md:**

### ✅ DO: Absolute imports from app root

```python
from app.core.dependencies import ServiceContainer, get_orchestrator
from app.agents.base import BaseAgent
from app.models.user import User
from app.services.socratic_service import SocraticService
```

### ❌ DON'T: Relative imports or fallback helpers

```python
# ❌ NEVER THIS (killed 80% of archive features)
try:
    from ..core import ServiceContainer
except ImportError:
    from .fallback_helpers import ServiceContainer  # Silent failure!

# ❌ NEVER THIS (confusing, breaks refactoring)
from ..models import User

# ✅ DO THIS
from app.models.user import User
```

---

## Configuration Files

### `requirements.txt`
```
fastapi>=0.121.0
uvicorn[standard]>=0.34.0
sqlalchemy>=2.0.44
psycopg2-binary>=2.9.10  # PostgreSQL driver
alembic>=1.14.0
pydantic>=2.12.3
python-jose[cryptography]  # JWT authentication
passlib[bcrypt]  # Password hashing
anthropic  # Claude API client
python-dotenv  # Environment variable management
pytest>=8.3.0
pytest-asyncio
httpx  # Testing HTTP requests
```

### `.env.example`
```bash
# Database connections
DATABASE_AUTH_URL=postgresql://user:password@localhost:5432/socrates_auth
DATABASE_SPECS_URL=postgresql://user:password@localhost:5433/socrates_specs

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Claude API
ANTHROPIC_API_KEY=your-anthropic-api-key

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### `pyproject.toml`
```toml
[project]
name = "socrates"
version = "0.1.0"
description = "Agentic RAG system for vibe coding"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"

[tool.black]
line-length = 100
target-version = ['py312']

[tool.ruff]
line-length = 100
```

---

## Development Workflow

### 1. Setup Databases
```bash
# Create databases
createdb socrates_auth
createdb socrates_specs

# Run migrations
python scripts/setup_databases.py
python scripts/run_migrations.py
```

### 2. Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Run CLI
```bash
cd cli
python main.py
```

### 4. Run Tests
```bash
cd backend
pytest
pytest tests/test_database_persistence.py -v  # CRITICAL TEST
```

---

## Phase Implementation Order

### Phase 0: Foundation (Week 1)
- Create directory structure
- Setup requirements.txt
- Initialize Git repository
- Create database initialization scripts
- Setup Alembic migrations

### Phase 1: MVP Core (Weeks 2-4)
- Implement all models
- Implement BaseAgent + AgentOrchestrator
- Implement 5 core agents (ProjectManager, SocraticCounselor, ContextAnalyzer, ConflictDetector, UserManager)
- Implement core services (auth, socratic, quality_control, maturity)
- Implement repositories
- Implement FastAPI routes
- Implement CLI
- Write tests (90% coverage minimum)
- **MUST PASS:** test_database_persistence.py

### Phase 2: Polish MVP (Week 5)
- Error handling
- Validation
- Edge cases
- Documentation
- Real-world testing

### Phase 3+: Future Modules
- Code generation (Phase 4)
- IDE integration (Phase 4)
- Team collaboration (Phase 6)
- UI (Phase 6)

---

## File Naming Conventions

### Python Files
- snake_case for all files: `socratic_service.py`
- Class names: PascalCase: `SocraticService`
- Function names: snake_case: `generate_question()`
- Constants: UPPER_SNAKE_CASE: `MAX_QUESTIONS = 10`

### Documentation Files
- UPPER_SNAKE_CASE for root docs: `VISION.md`, `ARCHITECTURE.md`
- Phase files: `PHASE_0.md`, `PHASE_1.md`

### Database Tables
- snake_case: `users`, `conversation_history`, `quality_metrics`

---

## Testing Structure

### Test Organization
```
backend/tests/
├── conftest.py           # Shared fixtures (db session, test client)
├── test_models/          # SQLAlchemy model tests
│   └── test_user.py
├── test_agents/          # Agent tests
│   ├── test_base_agent.py
│   └── test_socratic_counselor.py
├── test_services/        # Service layer tests
│   ├── test_auth_service.py
│   └── test_socratic_service.py
├── test_repositories/    # Repository tests
│   └── test_user_repository.py
├── test_api/             # API endpoint tests
│   ├── test_auth_endpoints.py
│   └── test_projects_endpoints.py
└── test_database_persistence.py  # CRITICAL: Archive killer test
```

### Test Coverage Requirements
- Minimum 90% coverage before Phase 2
- 100% coverage for:
  - BaseAgent
  - AgentOrchestrator
  - All repositories
  - Quality control system
  - Maturity system

---

## References

- [VISION.md](VISION.md) - Project goals
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md) - Technology decisions
- [INTERCONNECTIONS_MAP.md](./INTERCONNECTIONS_MAP.md) - Component dependencies
- [ARCHIVE_ANTIPATTERNS.md](./ARCHIVE_ANTIPATTERNS.md) - What NOT to do
- [SQLALCHEMY_BEST_PRACTICES.md](./SQLALCHEMY_BEST_PRACTICES.md) - Database implementation

---

**Last Updated:** 2025-11-05
**Status:** Ready for Phase 1 implementation

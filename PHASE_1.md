# Phase 1: Infrastructure Foundation

**Status:** ⏳ PENDING (Awaiting Phase 0 completion)
**Duration:** Estimated 2-3 days
**Goal:** Build solid, testable infrastructure foundation

---

## 📋 Objectives

1. Set up PostgreSQL databases (auth + specs)
2. Implement FastAPI skeleton
3. Create authentication system
4. Implement BaseAgent pattern
5. Implement AgentOrchestrator
6. Create ServiceContainer with dependency injection
7. Write comprehensive tests

---

## 🔗 Dependencies

### Depends On (From Phase 0):
- **DATABASE_SCHEMA.md** → Implement database models
- **ARCHITECTURE.md** → BaseAgent and Orchestrator design
- **PROJECT_STRUCTURE.md** → Directory structure
- **TESTING_STRATEGY.md** → Test requirements

### Provides To (For Phase 2):
```python
# Classes Phase 2 will use:
from app.core.dependencies import ServiceContainer, get_orchestrator
from app.agents.base import BaseAgent
from app.agents.orchestrator import AgentOrchestrator
from app.models.base import BaseModel
from app.models.user import User
from app.models.project import Project
from app.models.session import Session
```

---

## 📦 Deliverables

### 1. Database Setup

**Files Created:**
```
backend/app/core/database.py
backend/alembic/versions/001_create_users_table.py
backend/alembic/versions/002_create_auth_tokens_table.py
backend/alembic/versions/003_create_projects_table.py
backend/alembic/versions/004_create_sessions_table.py
```

**Tables Created:**
1. `users` (id, email, hashed_password, status, role, created_at, updated_at)
2. `auth_tokens` (id, user_id, token, expires_at, created_at)
3. `projects` (id, user_id, name, description, phase, maturity_score, status, created_at, updated_at)
4. `sessions` (id, project_id, user_id, mode, status, started_at, ended_at)

**Interconnection:**
- Phase 2 agents will query these tables
- Foreign keys: auth_tokens → users, projects → users, sessions → projects + users

---

### 2. BaseModel Class

**File:** `backend/app/models/base.py`

**Provides:**
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, func
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base class for all models"""
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

**Why This Design:**
- UUID primary keys (not auto-increment) → Distributed system friendly
- Automatic timestamps → Audit trail
- `to_dict()` method → Easy API serialization
- Abstract base → All models inherit common behavior

**Used By:**
- All model classes in Phase 1, 2, 3, etc.

---

### 3. User Model

**File:** `backend/app/models/user.py`

**Provides:**
```python
from app.models.base import BaseModel
from sqlalchemy import Column, String, Enum
from passlib.context import CryptContext
import enum

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    @staticmethod
    def hash_password(password: str) -> str:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.hashed_password)
```

**Interconnection:**
- Used by: Authentication endpoints, all agents (user_id in requests)
- References: None (base table)

---

### 4. Authentication System

**File:** `backend/app/core/security.py`

**Provides:**
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User

SECRET_KEY = "your-secret-key-here"  # Load from .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
```

**Used By:**
- All API endpoints requiring authentication
- Agents needing user context

---

### 5. ServiceContainer (Dependency Injection)

**File:** `backend/app/core/dependencies.py`

**Provides:**
```python
from typing import Optional
import logging
from sqlalchemy.orm import Session
from anthropic import Anthropic
from app.core.database import SessionLocal, engine
from app.core.config import settings

class ServiceContainer:
    """
    Central service container for dependency injection.
    NO FALLBACKS - All dependencies are required.
    """

    def __init__(self):
        self._db_session: Optional[Session] = None
        self._claude_client: Optional[Anthropic] = None
        self._logger_cache: dict = {}

    def get_database(self) -> Session:
        """Get database session - REQUIRED"""
        if self._db_session is None:
            self._db_session = SessionLocal()
        return self._db_session

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance - REQUIRED"""
        if name not in self._logger_cache:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            self._logger_cache[name] = logger
        return self._logger_cache[name]

    def get_config(self) -> dict:
        """Get configuration - REQUIRED"""
        return settings.dict()

    def get_claude_client(self) -> Anthropic:
        """Get Claude API client - REQUIRED"""
        if self._claude_client is None:
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self._claude_client = Anthropic(api_key=api_key)
        return self._claude_client

    def close(self):
        """Clean up resources"""
        if self._db_session:
            self._db_session.close()

# Global instance
_service_container = None

def get_service_container() -> ServiceContainer:
    """Get global service container instance"""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container
```

**Key Design Decisions:**
- ❌ NO fallback returns (no `{}` or `None`)
- ✅ Raises exceptions if dependencies missing
- ✅ Lazy loading (create on first use)
- ✅ Singleton pattern (one instance)

**Used By:**
- All agents via `BaseAgent.__init__()`

---

### 6. BaseAgent Class

**File:** `backend/app/agents/base.py`

**Provides:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.dependencies import ServiceContainer

class BaseAgent(ABC):
    """
    Base class for all agents.
    Provides:
    - Dependency injection via ServiceContainer
    - Standardized request processing
    - Common utilities
    """

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        # REQUIRED dependencies - no fallbacks
        if services is None:
            raise ValueError("ServiceContainer is required")

        self.agent_id = agent_id
        self.name = name
        self.services = services

        # Get dependencies (will raise if not available)
        self.db = services.get_database()
        self.logger = services.get_logger(f"agent.{agent_id}")
        self.config = services.get_config()
        self.claude_client = services.get_claude_client()

        # Statistics
        self.stats = {
            'requests_processed': 0,
            'errors_encountered': 0,
            'last_activity': None
        }

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides.
        Must be implemented by subclass.
        """
        pass

    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request. Routes to appropriate method based on action.

        Args:
            action: Action to perform (e.g., 'create_project', 'generate_question')
            data: Request data

        Returns:
            Response dictionary with 'success' and 'data' or 'error'
        """
        from datetime import datetime

        self.stats['requests_processed'] += 1
        self.stats['last_activity'] = datetime.utcnow().isoformat()

        # Route to method
        method_name = f"_{action}"  # e.g., _create_project
        if not hasattr(self, method_name):
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'error_code': 'UNKNOWN_ACTION'
            }

        try:
            method = getattr(self, method_name)
            result = method(data)
            return result
        except Exception as e:
            self.stats['errors_encountered'] += 1
            self.logger.error(f"Error in {self.agent_id}.{action}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_code': 'AGENT_ERROR'
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'stats': self.stats
        }
```

**Why This Design:**
- ✅ ABC enforces subclass implementation
- ✅ Required ServiceContainer (no fallbacks)
- ✅ Standardized request routing
- ✅ Built-in error handling
- ✅ Statistics tracking

**Used By:**
- All agent implementations (Phase 2+)

---

### 7. AgentOrchestrator

**File:** `backend/app/agents/orchestrator.py`

**Provides:**
```python
from typing import Dict, Any, Optional, List
from app.core.dependencies import ServiceContainer
from app.agents.base import BaseAgent

class AgentOrchestrator:
    """
    Central orchestrator for all agents.
    Responsibilities:
    - Agent registration
    - Request routing
    - Quality control integration (Phase 5)
    """

    def __init__(self, services: ServiceContainer):
        self.services = services
        self.logger = services.get_logger("orchestrator")
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        if not isinstance(agent, BaseAgent):
            raise TypeError("Agent must inherit from BaseAgent")

        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")
        self.logger.info(f"  Capabilities: {', '.join(agent.get_capabilities())}")

    def route_request(
        self,
        agent_id: str,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to appropriate agent.

        Args:
            agent_id: ID of agent to route to
            action: Action to perform
            data: Request data

        Returns:
            Response from agent
        """
        # Validate agent exists
        if agent_id not in self.agents:
            return {
                'success': False,
                'error': f'Unknown agent: {agent_id}',
                'error_code': 'UNKNOWN_AGENT'
            }

        agent = self.agents[agent_id]

        # Validate capability
        capabilities = agent.get_capabilities()
        if action not in capabilities:
            return {
                'success': False,
                'error': f'Agent {agent_id} does not support action: {action}',
                'error_code': 'UNSUPPORTED_ACTION',
                'available_capabilities': capabilities
            }

        # Route to agent
        self.logger.info(f"Routing to {agent_id}.{action}")
        result = agent.process_request(action, data)

        return result

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get information about all registered agents"""
        return [
            {
                'agent_id': agent.agent_id,
                'name': agent.name,
                'capabilities': agent.get_capabilities(),
                'stats': agent.get_stats()
            }
            for agent in self.agents.values()
        ]

# Global instance
_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        from app.core.dependencies import get_service_container
        services = get_service_container()
        _orchestrator = AgentOrchestrator(services)
    return _orchestrator
```

**Interconnection:**
- Phase 2: Agents register with orchestrator
- Phase 5: Quality control integrated here
- All API endpoints call orchestrator

---

## 🧪 Testing Requirements

### Test File: `backend/tests/test_phase_1_infrastructure.py`

**Must Test:**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base, BaseModel
from app.models.user import User, UserStatus, UserRole
from app.core.security import create_access_token, get_current_user
from app.core.dependencies import ServiceContainer
from app.agents.base import BaseAgent
from app.agents.orchestrator import AgentOrchestrator

# Test Database Connection
def test_database_connection():
    """Test can connect to PostgreSQL"""
    engine = create_engine("postgresql://user:pass@localhost/socrates_test")
    connection = engine.connect()
    assert connection is not None
    connection.close()

# Test Models
def test_create_user():
    """Test can create user with hashed password"""
    user = User(
        email="test@example.com",
        hashed_password=User.hash_password("password123"),
        status=UserStatus.ACTIVE,
        role=UserRole.USER
    )
    assert user.email == "test@example.com"
    assert user.verify_password("password123") == True
    assert user.verify_password("wrong") == False

# Test Authentication
def test_create_jwt_token():
    """Test JWT token creation"""
    token = create_access_token({"sub": "user_123"})
    assert token is not None
    assert isinstance(token, str)

# Test ServiceContainer
def test_service_container():
    """Test ServiceContainer provides all required services"""
    services = ServiceContainer()

    # Must provide database
    db = services.get_database()
    assert db is not None

    # Must provide logger
    logger = services.get_logger("test")
    assert logger is not None

    # Must provide config
    config = services.get_config()
    assert config is not None
    assert isinstance(config, dict)

    # Must provide Claude client
    claude = services.get_claude_client()
    assert claude is not None

# Test BaseAgent
def test_base_agent_requires_services():
    """Test BaseAgent fails without ServiceContainer"""
    with pytest.raises(ValueError):
        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["test"]

        TestAgent("test", "Test Agent", None)  # Should raise

def test_base_agent_with_services():
    """Test BaseAgent works with ServiceContainer"""
    services = ServiceContainer()

    class TestAgent(BaseAgent):
        def get_capabilities(self):
            return ["test_action"]

        def _test_action(self, data):
            return {'success': True, 'result': 'test'}

    agent = TestAgent("test", "Test Agent", services)
    assert agent.agent_id == "test"
    assert "test_action" in agent.get_capabilities()

    # Test request processing
    result = agent.process_request("test_action", {})
    assert result['success'] == True

# Test AgentOrchestrator
def test_orchestrator_registration():
    """Test agent registration"""
    services = ServiceContainer()
    orchestrator = AgentOrchestrator(services)

    class TestAgent(BaseAgent):
        def get_capabilities(self):
            return ["test"]

    agent = TestAgent("test", "Test", services)
    orchestrator.register_agent(agent)

    assert "test" in orchestrator.agents
    assert orchestrator.agents["test"] == agent

def test_orchestrator_routing():
    """Test request routing"""
    services = ServiceContainer()
    orchestrator = AgentOrchestrator(services)

    class TestAgent(BaseAgent):
        def get_capabilities(self):
            return ["test_action"]

        def _test_action(self, data):
            return {'success': True, 'data': data}

    agent = TestAgent("test", "Test", services)
    orchestrator.register_agent(agent)

    # Valid request
    result = orchestrator.route_request("test", "test_action", {'key': 'value'})
    assert result['success'] == True
    assert result['data']['key'] == 'value'

    # Invalid agent
    result = orchestrator.route_request("nonexistent", "test_action", {})
    assert result['success'] == False
    assert 'Unknown agent' in result['error']

    # Invalid action
    result = orchestrator.route_request("test", "nonexistent_action", {})
    assert result['success'] == False
    assert 'does not support action' in result['error']
```

**Test Coverage Required:** Minimum 90%

---

## ✅ Verification Checklist

Phase 1 is complete when ALL of these pass:

### Database
- [ ] Can connect to PostgreSQL (`socrates_auth` and `socrates_specs` databases)
- [ ] All migrations run successfully
- [ ] `users` table created with correct schema
- [ ] `auth_tokens` table created with correct schema
- [ ] `projects` table created with correct schema
- [ ] `sessions` table created with correct schema
- [ ] Foreign keys working (can't create project without user)

### Models
- [ ] Can import `BaseModel` without errors
- [ ] Can create `User` instance
- [ ] Can hash and verify passwords
- [ ] Can save user to database
- [ ] User timestamps auto-populate

### Authentication
- [ ] Can create JWT token
- [ ] Can decode JWT token
- [ ] `get_current_user()` returns correct user
- [ ] Invalid token raises 401 error

### ServiceContainer
- [ ] Can create ServiceContainer instance
- [ ] `get_database()` returns Session (not None)
- [ ] `get_logger()` returns Logger (not None)
- [ ] `get_config()` returns dict (not empty {})
- [ ] `get_claude_client()` returns Anthropic client (not None)
- [ ] Missing API key raises clear error (not silent failure)

### BaseAgent
- [ ] Can create BaseAgent subclass
- [ ] BaseAgent requires ServiceContainer (raises if None)
- [ ] `process_request()` routes to correct method
- [ ] Unknown action returns error (not crash)
- [ ] Statistics tracking works

### AgentOrchestrator
- [ ] Can create orchestrator instance
- [ ] Can register agent
- [ ] Can route request to agent
- [ ] Invalid agent returns error
- [ ] Invalid action returns error
- [ ] `get_all_agents()` returns registered agents

### Tests
- [ ] All tests in `test_phase_1_infrastructure.py` pass
- [ ] Test coverage ≥ 90%
- [ ] No import errors when running tests
- [ ] Can run tests with: `pytest backend/tests/test_phase_1_infrastructure.py -v`

### Integration Test
- [ ] Can start FastAPI server: `uvicorn app.main:app --reload`
- [ ] Can create user via API: `POST /api/auth/register`
- [ ] Can login and get JWT: `POST /api/auth/login`
- [ ] Can access protected endpoint with JWT
- [ ] Invalid JWT returns 401

---

## 🎯 Success Criteria

Phase 1 is complete and verified when:

1. ✅ All verification checklist items pass
2. ✅ All tests pass with ≥90% coverage
3. ✅ Integration test successful
4. ✅ No fallback mechanisms exist
5. ✅ All imports work (no ImportError)
6. ✅ Documentation updated with actual implementation
7. ✅ User reviewed and approved

---

## 🔴 Common Pitfalls (From Previous Attempts)

### ❌ Don't Do This:
```python
# NO FALLBACKS!
try:
    from app.core import ServiceContainer
except ImportError:
    from fallback_helpers import ServiceContainer  # NO!

# NO SILENT FAILURES!
def get_database(self):
    try:
        return SessionLocal()
    except:
        return None  # NO! Raise the error!

# NO OPTIONAL DEPENDENCIES!
def get_claude_client(self):
    if ANTHROPIC_API_KEY:
        return Anthropic(api_key=ANTHROPIC_API_KEY)
    return None  # NO! Raise error if missing!
```

### ✅ Do This Instead:
```python
# EXPLICIT IMPORTS - Fail fast if missing
from app.core import ServiceContainer  # If fails, we want to know!

# RAISE ERRORS - Don't hide problems
def get_database(self):
    """Get database session - REQUIRED"""
    try:
        return SessionLocal()
    except Exception as e:
        raise DatabaseError(f"Failed to create database session: {e}")

# REQUIRED DEPENDENCIES - Fail if not configured
def get_claude_client(self):
    """Get Claude client - REQUIRED"""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY must be set in environment")
    return Anthropic(api_key=ANTHROPIC_API_KEY)
```

---

## 📊 Data Flow (Phase 1)

```
User Request
     ↓
FastAPI Endpoint
     ↓
get_current_user() → Validates JWT → Queries User from database
     ↓
get_orchestrator() → Returns AgentOrchestrator instance
     ↓
orchestrator.route_request() → (Phase 2 will register agents here)
     ↓
Response
```

---

## 🔄 Handoff to Phase 2

**What Phase 1 Provides:**
- Working database with users, projects, sessions tables
- Authentication system (JWT)
- BaseAgent class ready for inheritance
- AgentOrchestrator ready for agent registration
- ServiceContainer providing all dependencies

**What Phase 2 Will Do:**
- Create 3 agents inheriting from BaseAgent
- Register agents with orchestrator
- Implement agent-specific actions
- Add more database tables (questions, specifications)

**Verification Gate:**
Cannot proceed to Phase 2 until Phase 1 verification checklist is 100% complete.

---

**Previous Phase:** [PHASE_0.md](./PHASE_0.md) - Documentation
**Next Phase:** [PHASE_2.md](./PHASE_2.md) - Core Agents (ProjectManager, Socratic, Context)

**Reference:**
- [INTERCONNECTIONS_MAP.md](./INTERCONNECTIONS_MAP.md) - See Phase 1 → Phase 2 interconnections
- [Old Repo: backend_for_audit/src/agents/base.py](https://github.com/Nireus79/Socrates/blob/main/ARCHIVE/backend_for_audit/src/agents/base.py) - Reference (DO NOT copy-paste)

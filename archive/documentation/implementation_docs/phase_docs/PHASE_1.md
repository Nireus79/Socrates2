# Phase 1: Infrastructure Foundation

**Status:** ✅ COMPLETE
**Completed:** November 6, 2025
**Duration:** 2 days
**Goal:** Build solid, testable infrastructure foundation

---

## ⚠️ CRITICAL: Read Before Starting

**🔴 MUST READ:** [SQLALCHEMY_BEST_PRACTICES.md](SQLALCHEMY_BEST_PRACTICES.md) - Contains critical issues that **KILLED PREVIOUS ATTEMPTS**

### Session Lifecycle Warning (Archive Killer Bug)

**Previous attempt had ZERO data persistence** due to SQLAlchemy session closing before commit synced to disk. This caused:
- API returned 201 Created
- But database had 0 records in ALL tables
- Users lost ALL messages, sessions, and data

**Verification Test (MUST PASS):**
```python
def test_persistence_after_session_close():
    """This test FAILED in archive - caused complete data loss."""
    with get_db_session() as db:
        user = User(username="test")
        db.add(user)
        db.commit()
        user_id = user.id

    # Session closed - data MUST still be in database
    with get_db_session() as db:
        found = db.query(User).filter_by(id=user_id).first()
        assert found is not None  # ⚠️ This FAILED in archive!
```

**Solution:** See SQLALCHEMY_BEST_PRACTICES.md sections:
- Issue #1: Session Lifecycle (80% of previous failures)
- Issue #2: Detached Instance Errors (15% of previous failures)
- Complete configuration examples

**DO NOT proceed with database implementation until you've read and understood the SQLAlchemy best practices document.**

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

## 🌐 API Endpoints

This phase implements authentication and admin endpoints. See [API_ENDPOINTS.md](../foundation_docs/API_ENDPOINTS.md) for complete API documentation.

**Implemented in Phase 1:**
- POST /api/v1/auth/register - Lines 23-50 in API_ENDPOINTS.md
- POST /api/v1/auth/login - Lines 52-80 in API_ENDPOINTS.md
- POST /api/v1/auth/logout - Lines 82-95 in API_ENDPOINTS.md
- GET /api/v1/admin/health - Lines 650-670 in API_ENDPOINTS.md
- GET /api/v1/admin/stats - Lines 720-745 in API_ENDPOINTS.md

**Testing Endpoints:**
```bash
# Health check
curl http://localhost:8000/api/v1/admin/health

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!"}'
```

---

## 📦 Deliverables

### 1. Database Setup

**⚠️ BEFORE implementing:**
- Read [SQLALCHEMY_BEST_PRACTICES.md](SQLALCHEMY_BEST_PRACTICES.md)
- Read [DATABASE_SCHEMA_COMPLETE.md](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md) for complete table definitions

**Files Created:**
```
backend/app/core/database.py
backend/alembic/versions/001_create_users_table.py
backend/alembic/versions/002_create_refresh_tokens_table.py
backend/alembic/versions/003_create_projects_table.py
backend/alembic/versions/004_create_sessions_table.py
```

**Tables Created:**

**socrates_auth database:**
1. `users` - See [DATABASE_SCHEMA_COMPLETE.md#users](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#users)
2. `refresh_tokens` - See [DATABASE_SCHEMA_COMPLETE.md#refresh_tokens](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#refresh_tokens)
3. `password_reset_requests` - See [DATABASE_SCHEMA_COMPLETE.md#password_reset_requests](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#password_reset_requests)
4. `audit_logs` - See [DATABASE_SCHEMA_COMPLETE.md#audit_logs](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#audit_logs)
5. `user_rules` - See [DATABASE_SCHEMA_COMPLETE.md#user_rules](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#user_rules)

**socrates_specs database:**
6. `projects` - See [DATABASE_SCHEMA_COMPLETE.md#projects](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#projects)
7. `sessions` - See [DATABASE_SCHEMA_COMPLETE.md#sessions](../foundation_docs/DATABASE_SCHEMA_COMPLETE.md#sessions)

**Interconnection:**
- Phase 2 agents will query these tables
- Phase 2 adds: conversation_history, questions, specifications tables
- Foreign keys: refresh_tokens → users, projects → users, sessions → projects

#### Complete Migration Files

**File: backend/alembic/versions/001_create_users_table.py**

```python
"""Create users table

Revision ID: 001
Revises:
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_status', 'users', ['status'])

def downgrade():
    op.drop_index('idx_users_status')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

**File: backend/alembic/versions/002_create_refresh_tokens_table.py**

```python
"""Create refresh_tokens table

Revision ID: 002
Revises: 001
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key to users in socrates_auth database
    op.create_foreign_key(
        'fk_refresh_tokens_user_id',
        'refresh_tokens', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_token', 'refresh_tokens', ['token'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])

def downgrade():
    op.drop_index('idx_refresh_tokens_expires_at')
    op.drop_index('idx_refresh_tokens_token')
    op.drop_index('idx_refresh_tokens_user_id')
    op.drop_constraint('fk_refresh_tokens_user_id', 'refresh_tokens', type_='foreignkey')
    op.drop_table('refresh_tokens')
```

**File: backend/alembic/versions/003_create_projects_table.py**

```python
"""Create projects table

Revision ID: 003
Revises: 002
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('current_phase', sa.String(50), nullable=False, server_default='discovery'),
        sa.Column('maturity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('idx_projects_user_id', 'projects', ['user_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_current_phase', 'projects', ['current_phase'])
    op.create_index('idx_projects_maturity_score', 'projects', ['maturity_score'])

    # Add check constraint for maturity_score
    op.create_check_constraint(
        'check_projects_maturity_score',
        'projects',
        'maturity_score >= 0 AND maturity_score <= 100'
    )

def downgrade():
    op.drop_constraint('check_projects_maturity_score', 'projects', type_='check')
    op.drop_index('idx_projects_maturity_score')
    op.drop_index('idx_projects_current_phase')
    op.drop_index('idx_projects_status')
    op.drop_index('idx_projects_user_id')
    op.drop_table('projects')
```

**File: backend/alembic/versions/004_create_sessions_table.py**

```python
"""Create sessions table

Revision ID: 004
Revises: 003
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(20), nullable=False, server_default='socratic'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Foreign key to projects
    op.create_foreign_key(
        'fk_sessions_project_id',
        'sessions', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index('idx_sessions_project_id', 'sessions', ['project_id'])
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_mode', 'sessions', ['mode'])

def downgrade():
    op.drop_index('idx_sessions_mode')
    op.drop_index('idx_sessions_status')
    op.drop_index('idx_sessions_project_id')
    op.drop_constraint('fk_sessions_project_id', 'sessions', type_='foreignkey')
    op.drop_table('sessions')
```

**Running Migrations:**
```bash
# Initialize Alembic (first time only)
cd backend
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url
# For socrates_auth:
sqlalchemy.url = postgresql://user:password@localhost/socrates_auth

# Create migration files (use the code above)

# Run migrations
alembic upgrade head

# Verify tables created
psql socrates_auth -c "\dt"
psql socrates_specs -c "\dt"
```

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

## 🔧 Troubleshooting

### Issue 1: Database Connection Failed

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Causes:**
1. PostgreSQL not running
2. Wrong connection string in `.env`
3. Database doesn't exist
4. Wrong credentials

**Solution:**
```bash
# 1. Check if PostgreSQL is running
sudo systemctl status postgresql
# or
ps aux | grep postgres

# 2. Check if databases exist
psql -l | grep socrates

# 3. Create databases if missing
createdb socrates_auth
createdb socrates_specs

# 4. Test connection manually
psql socrates_auth -c "SELECT 1"

# 5. Verify .env file
cat backend/.env | grep DATABASE_URL
```

---

### Issue 2: Migration Fails - "relation already exists"

**Symptom:**
```
alembic.util.exc.CommandError: relation "users" already exists
```

**Causes:**
- Tables manually created
- Previous migration partially completed
- Alembic version table out of sync

**Solution:**
```bash
# Check current migration state
alembic current

# Check what migrations exist
alembic history

# If table exists but migration not recorded:
alembic stamp head

# If need to start fresh (DANGEROUS - deletes data):
# DROP all tables
psql socrates_auth -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# Then run migrations again
alembic upgrade head
```

---

### Issue 3: Import Error - "No module named 'app'"

**Symptom:**
```
ModuleNotFoundError: No module named 'app'
```

**Causes:**
- Not running from correct directory
- PYTHONPATH not set
- Virtual environment not activated

**Solution:**
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Check you're in backend/ directory
pwd
# Should show: /path/to/Socrates/backend

# 3. Add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Socrates/backend"

# 4. Or run with Python module syntax
python -m app.main
```

---

### Issue 4: "bcrypt" or "passlib" Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'passlib'
```

**Causes:**
- Dependencies not installed
- Wrong virtual environment

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify passlib installed
pip list | grep passlib

# If still missing, install directly
pip install passlib[bcrypt]
```

---

### Issue 5: JWT Token Not Working - "Invalid token"

**Symptom:**
```
fastapi.HTTPException: Could not validate credentials
```

**Causes:**
- SECRET_KEY not set or changed
- Token expired
- Algorithm mismatch

**Solution:**
```bash
# 1. Check SECRET_KEY in .env
cat backend/.env | grep SECRET_KEY

# 2. Generate new SECRET_KEY if missing
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Add to .env
echo "SECRET_KEY=<generated_key>" >> backend/.env

# 4. Restart FastAPI server
# Tokens issued before restart will be invalid
```

---

### Issue 6: Tests Pass Locally But Data Not Persisting

**Symptom:**
- Tests show SUCCESS
- Database queries return 0 rows
- API returns 201 Created but data doesn't exist

**Causes:**
- **ARCHIVE KILLER BUG**: Session closes before commit syncs to disk
- Using `db.commit()` but session closes immediately
- Transaction isolation issues

**Solution:**
```python
# ❌ WRONG - Session closes before commit syncs
def create_user(db):
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    # Session closes here - data might not be on disk yet!

# ✅ CORRECT - Ensure session stays open until data persisted
def create_user(db):
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)  # Forces data to be read back from database
    return user

# ✅ CORRECT - Use context manager
with get_db() as db:
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id  # Get ID before session closes

# Verify data persisted
with get_db() as db:
    found = db.query(User).filter(User.id == user_id).first()
    assert found is not None  # THIS MUST PASS
```

**See:** SQLALCHEMY_BEST_PRACTICES.md Issue #1 for complete explanation

---

### Issue 7: FastAPI Server Won't Start - Port Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# 1. Find process using port 8000
lsof -i :8000

# 2. Kill the process
kill -9 <PID>

# 3. Or use different port
uvicorn app.main:app --port 8001
```

---

### Issue 8: Alembic Can't Find Config

**Symptom:**
```
alembic.util.exc.CommandError: Can't locate revision identified by '001'
```

**Causes:**
- Running from wrong directory
- alembic.ini missing
- Wrong database URL in alembic.ini

**Solution:**
```bash
# 1. Must run from backend/ directory
cd backend

# 2. Check alembic.ini exists
ls alembic.ini

# 3. Check database URL in alembic.ini
grep sqlalchemy.url alembic.ini

# 4. Verify migration files exist
ls alembic/versions/
```

---

## ✅ Verification Checklist

Phase 1 is complete when ALL of these pass:

### Database
- [x] Can connect to PostgreSQL (`socrates_auth` and `socrates_specs` databases)
- [x] All migrations run successfully (revision 004 on both databases)
- [x] `users` table created with correct schema
- [x] `refresh_tokens` table created with correct schema
- [x] `projects` table created with correct schema
- [x] `sessions` table created with correct schema
- [x] Foreign keys working (can't create project without user)

### Models
- [x] Can import `BaseModel` without errors
- [x] Can create `User` instance
- [x] Can hash and verify passwords
- [x] Can save user to database
- [x] User timestamps auto-populate

### Authentication
- [x] Can create JWT token
- [x] Can decode JWT token
- [x] `get_current_user()` returns correct user
- [x] Invalid token raises 401 error

### ServiceContainer
- [x] Can create ServiceContainer instance
- [x] `get_database()` returns Session (not None)
- [x] `get_logger()` returns Logger (not None)
- [x] `get_config()` returns dict (not empty {})
- [x] `get_claude_client()` returns Anthropic client (not None)
- [x] Missing API key raises clear error (not silent failure)

### BaseAgent
- [x] Can create BaseAgent subclass
- [x] BaseAgent requires ServiceContainer (raises if None)
- [x] `process_request()` routes to correct method
- [x] Unknown action returns error (not crash)
- [x] Statistics tracking works

### AgentOrchestrator
- [x] Can create orchestrator instance
- [x] Can register agent
- [x] Can route request to agent
- [x] Invalid agent returns error
- [x] Invalid action returns error
- [x] `get_all_agents()` returns registered agents

### Tests
- [x] All tests in `test_phase_1_infrastructure.py` pass (52/52 tests passing)
- [x] Test coverage ≥ 90%
- [x] No import errors when running tests
- [x] Can run tests with: `pytest backend/tests/test_phase_1_infrastructure.py -v`

### Integration Test
- [x] Can start FastAPI server: `uvicorn app.main:app --reload`
- [x] Can create user via API: `POST /api/auth/register`
- [x] Can login and get JWT: `POST /api/auth/login`
- [x] Can access protected endpoint with JWT
- [x] Invalid JWT returns 401

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

**PHASE 1 COMPLETE:** All success criteria met on November 6, 2025

---

## 📊 Phase 1 Completion Summary

**Implementation Complete:**
- ✅ Database setup (PostgreSQL 17, 2 databases)
- ✅ 4 migrations executed (revision 004 on both databases)
- ✅ BaseModel and User models implemented
- ✅ JWT authentication system implemented
- ✅ ServiceContainer with dependency injection
- ✅ BaseAgent abstract class
- ✅ AgentOrchestrator for routing
- ✅ 52 tests passing (100% pass rate)
- ✅ Archive killer bug fixed (session lifecycle)

**Dependencies Installed:**
- All Phase 0-1 dependencies installed
- Phase 6-10 dependencies pre-installed
- 0 critical conflicts detected
- OpenTelemetry Jaeger → OTLP (version fix)

**Ready for Phase 2:** All interconnections verified, database ready for questions and specifications tables

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

**Previous Phase:** [PHASE_0.md](PHASE_0.md) - Documentation
**Next Phase:** [PHASE_2.md](PHASE_2.md) - Core Agents (ProjectManager, Socratic, Context)

**Reference:**
- [INTERCONNECTIONS_MAP.md](INTERCONNECTIONS_MAP.md) - See Phase 1 → Phase 2 interconnections
- [Old Repo: backend_for_audit/src/agents/base.py](https://github.com/Nireus79/Socrates/blob/main/ARCHIVE/backend_for_audit/src/agents/base.py) - Reference (DO NOT copy-paste)

# Socrates2 Architecture Guide

**Level:** Intermediate to Advanced
**Time to read:** 45 minutes
**Goal:** Understand system design and components

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  Web UI / CLI / API Client / SDKs                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Web Server                        │
│  Routes → Handlers → Business Logic → Response              │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴─────────┬──────────────┐
        ↓                  ↓              ↓
┌──────────────┐  ┌──────────────┐  ┌──────────┐
│   Services   │  │   Agents     │  │ Domains  │
│   Layer      │  │   Layer      │  │  System  │
└──────────────┘  └──────────────┘  └──────────┘
        │                  │              │
        └────────┬─────────┴──────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────┐
│           Repository & Database Access Layer                │
│      SQLAlchemy ORM → Database Queries                      │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴──────────┐
        ↓                   ↓
    PostgreSQL          PostgreSQL
   (socrates_auth)   (socrates_specs)
```

---

## Layer Architecture

### 1. Presentation Layer (FastAPI)

**Purpose:** Handle HTTP requests/responses

**Components:**
- `app/api/` - API endpoints
- `app/main.py` - Application factory
- Routers for each feature

**Responsibilities:**
- Validate incoming requests
- Transform to domain objects
- Call services
- Format responses
- Handle errors

**Example Endpoint:**
```python
@router.post("/api/v1/projects")
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """Create new project."""
    service = ProjectService(db)
    project = service.create(project, current_user.id)
    return ProjectResponse.from_orm(project)
```

### 2. Service Layer (Business Logic)

**Purpose:** Implement business rules

**Components:**
- `app/services/` - Service classes
- Each service handles one domain (ProjectService, etc.)
- Orchestrate repositories and external services

**Responsibilities:**
- Business logic
- Data validation
- Transaction management
- Service coordination

**Example Service:**
```python
class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectRepository(db)

    def create(self, data: ProjectCreate, user_id: UUID) -> Project:
        """Create project with validation."""
        # Validate business rules
        if not self._is_valid_project(data):
            raise ValidationError()

        # Create via repository
        project = self.repo.create(data, user_id)

        # Additional processing
        self._initialize_project(project)

        return project
```

### 3. Repository Layer (Data Access)

**Purpose:** Abstract database access

**Components:**
- `app/repositories/` - Repository classes
- Each repository handles one model
- SQLAlchemy ORM queries

**Responsibilities:**
- Database queries
- Transaction handling
- Query optimization
- Connection management

**Example Repository:**
```python
class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ProjectCreate, user_id: UUID) -> Project:
        """Create project in database."""
        project = Project(
            name=data.name,
            owner_id=user_id,
            **data.dict()
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, id: UUID) -> Optional[Project]:
        """Get project by ID."""
        return self.db.query(Project).filter(
            Project.id == id
        ).first()
```

### 4. Domain Layer (Knowledge Domains)

**Purpose:** Handle domain-specific logic

**Components:**
- `app/domains/` - Domain classes
- 7 pre-configured domains
- Question templates, analyzers, exporters

**Domains:**
1. **Architecture** - System design
2. **Programming** - Implementation
3. **Testing** - Quality assurance
4. **DataEngineering** - Data management
5. **Security** - Security and compliance
6. **Business** - Business requirements
7. **DevOps** - Operations

**Example Domain:**
```python
class ArchitectureDomain(BaseDomain):
    """Architecture domain for system design specifications."""

    name = "architecture"
    questions = [
        Question(text="What is your system architecture pattern?"),
        Question(text="How do services communicate?"),
        # ... more questions
    ]

    def analyze(self, specs: List[Spec]) -> Analysis:
        """Analyze architecture specs."""
        # Domain-specific analysis
        return Analysis(...)
```

### 5. Agent Layer (AI Coordination)

**Purpose:** Coordinate with Claude AI

**Components:**
- `app/agents/` - Agent classes
- BaseAgent - Abstract agent
- SocraticCounselorAgent - Conversation agent
- ContextAnalyzerAgent - Analysis agent

**Responsibilities:**
- Call Claude API
- Parse responses
- Manage conversation context
- Generate specifications

**Example Agent:**
```python
class SocraticCounselorAgent(BaseAgent):
    """Guides users through Socratic questioning."""

    async def generate_question(self, context: Context) -> Question:
        """Generate next question based on context."""
        prompt = self._build_prompt(context)
        response = await self.client.messages.create(
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(response)
```

### 6. Model Layer (Data Models)

**Purpose:** Define data structures

**Components:**
- `app/models/` - SQLAlchemy models
- Core models (User, Project, Specification, etc.)
- Relationships and constraints

**Core Models:**
```
User
├── Projects (one-to-many)
├── Sessions (one-to-many)
└── TeamMemberships (one-to-many)

Project
├── Specifications (one-to-many)
├── Sessions (one-to-many)
├── TeamMembers (many-to-many)
└── Workflows (one-to-many)

Session
├── Messages (one-to-many)
├── Specifications (many-to-many)
└── Domain (foreign key)

Specification
├── Project (foreign key)
├── Session (foreign key)
└── Category (many-to-many)
```

---

## Database Architecture

### Two-Database Design

**Why Two Databases?**
- **Separation of concerns**
- **Independent scaling**
- **Different backup schedules**
- **Security isolation**

### Database 1: socrates_auth

**Purpose:** User and authentication data
**Size:** Small (10-50 MB)
**Backup:** Daily
**Tables:**
- users
- refresh_tokens
- user_roles

### Database 2: socrates_specs

**Purpose:** Specifications and projects
**Size:** Large (100 MB - 10 GB+)
**Backup:** Hourly
**Tables:**
- projects
- sessions
- specifications
- domains
- workflows
- team_members
- analytics_metrics

### Migrations

**Location:** `backend/alembic/versions/`
**Tool:** Alembic for schema versioning
**Approach:** Sequential migrations (001, 002, 003, ...)

**Run Migrations:**
```bash
# Set database URL
export DATABASE_URL_SPECS="postgresql://user:pass@host/socrates_specs"

# Run migrations
alembic upgrade head
```

---

## Authentication & Security

### JWT Token Flow

```
1. User Registration
   POST /auth/register
   ↓
2. Create User
   Hash password with bcrypt
   Store in database
   ↓
3. Create JWT Token
   Create access token (30 min)
   Create refresh token (7 days)
   ↓
4. Return Tokens
   Send to client
   Client stores securely
   ↓
5. Make Requests
   Include Bearer token
   API validates token
   ↓
6. Token Expiry
   Access token expires
   Use refresh token to get new one
```

### Security Features

- ✅ Bcrypt password hashing (10 rounds)
- ✅ JWT with HS256 algorithm
- ✅ Refresh token rotation
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (ORM)
- ✅ Rate limiting (future)
- ✅ API key authentication (future)

---

## Key Components

### ProjectService

**Responsibilities:**
- Create projects
- Update projects
- Delete projects
- List projects
- Check permissions

**Methods:**
```python
create(data: ProjectCreate, user_id: UUID) -> Project
get_by_id(id: UUID, user_id: UUID) -> Project
list_user_projects(user_id: UUID) -> List[Project]
update(id: UUID, data: ProjectUpdate) -> Project
delete(id: UUID) -> None
```

### SessionService

**Responsibilities:**
- Create sessions
- Manage conversation state
- Generate questions
- Store answers
- Build specifications

**Methods:**
```python
create_session(data: SessionCreate) -> Session
get_current_question(session_id: UUID) -> Question
store_answer(session_id: UUID, answer: str) -> None
complete_session(session_id: UUID) -> List[Specification]
```

### SpecificationService

**Responsibilities:**
- Store specifications
- Analyze specifications
- Detect conflicts
- Generate recommendations

**Methods:**
```python
create_spec(data: SpecCreate) -> Specification
list_by_project(project_id: UUID) -> List[Specification]
analyze_specs(specs: List[Specification]) -> Analysis
detect_conflicts(specs: List[Specification]) -> List[Conflict]
```

### WorkflowService

**Responsibilities:**
- Execute multi-domain workflows
- Coordinate across domains
- Aggregate results
- Cross-domain analysis

**Methods:**
```python
create_workflow(data: WorkflowCreate) -> Workflow
execute(workflow_id: UUID) -> WorkflowResult
get_results(workflow_id: UUID) -> WorkflowResult
```

---

## API Endpoint Structure

### Authentication Endpoints
```
POST   /api/v1/auth/register       - Register new user
POST   /api/v1/auth/login          - Login user
POST   /api/v1/auth/refresh        - Refresh token
POST   /api/v1/auth/logout         - Logout user
```

### Project Endpoints
```
POST   /api/v1/projects            - Create project
GET    /api/v1/projects            - List user projects
GET    /api/v1/projects/{id}       - Get project
PATCH  /api/v1/projects/{id}       - Update project
DELETE /api/v1/projects/{id}       - Delete project
```

### Specification Endpoints
```
POST   /api/v1/projects/{id}/specs     - Create spec
GET    /api/v1/projects/{id}/specs     - List specs
GET    /api/v1/projects/{id}/specs/{id} - Get spec
PATCH  /api/v1/projects/{id}/specs/{id} - Update spec
DELETE /api/v1/projects/{id}/specs/{id} - Delete spec
```

### Session Endpoints
```
POST   /api/v1/projects/{id}/sessions      - Start session
GET    /api/v1/projects/{id}/sessions      - List sessions
GET    /api/v1/projects/{id}/sessions/{id} - Get session
POST   /api/v1/projects/{id}/sessions/{id}/answer - Answer question
```

### Workflow Endpoints
```
POST   /api/v1/workflows           - Create workflow
GET    /api/v1/workflows           - List workflows
GET    /api/v1/workflows/{id}      - Get workflow
POST   /api/v1/workflows/{id}/execute - Execute workflow
```

---

## Data Flow Example

**User Flow: Creating a Project and Starting a Session**

```
1. Client: POST /api/v1/projects
   {
     "name": "My Project",
     "description": "...",
     "maturity_score": 0.0
   }

2. API Handler (app/api/projects.py)
   - Validates request
   - Gets current user
   - Calls ProjectService

3. ProjectService
   - Validates business rules
   - Calls ProjectRepository

4. ProjectRepository
   - Creates Project in database
   - Returns Project object

5. ProjectService
   - Initializes analytics
   - Returns Project

6. API Handler
   - Formats response
   - Returns HTTP 201

7. Client: POST /api/v1/projects/{id}/sessions
   {
     "name": "Session 1",
     "domains": ["architecture"]
   }

8. API Handler
   - Validates request
   - Gets project
   - Calls SessionService

9. SessionService
   - Creates Session
   - Gets domain questions
   - Returns first question

10. API Handler
    - Returns question in response

11. Client: POST /api/v1/projects/{id}/sessions/{id}/answer
    {
      "answer": "User's answer to question"
    }

12. SessionService
    - Stores answer
    - Generates next question
    - Returns next question

13. Client: Repeat until session complete

14. SessionService
    - Analyzes answers
    - Creates Specifications
    - Returns results
```

---

## Extension Points

### Add Custom Domain

1. Create domain class in `app/domains/`
2. Define questions
3. Implement analyzers
4. Add to domain registry
5. Questions available to users

### Add New Analyzer

1. Create analyzer class
2. Implement `analyze()` method
3. Register with domain
4. Results included in analysis

### Add Integration

1. Create service in `app/integrations/`
2. Implement API calls
3. Add endpoints to trigger integration
4. Store results in database

---

## Performance Considerations

### Optimization

- ✅ Database indexing on foreign keys
- ✅ Pagination for list endpoints
- ✅ Query optimization with eager loading
- ✅ Caching for domains and questions
- ✅ Async/await for I/O operations

### Scaling

- Horizontal scaling via load balancer
- Database replication for reads
- Cache layer (Redis) for hot data
- Async job queue for long operations
- CDN for static assets

---

**[← Back to Documentation Index](../INDEX.md)**

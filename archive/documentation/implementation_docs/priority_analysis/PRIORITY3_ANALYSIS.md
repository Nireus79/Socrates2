# Priority 3 CLI Commands - Comprehensive Pre-Implementation Analysis

**Date:** November 8, 2025
**Focus:** Detailed requirements and integration analysis for Priority 3 commands
**Status:** Analysis Complete - Ready for Implementation

---

## Table of Contents

1. [Part 1: CLI Command Requirements](#part-1-cli-command-requirements)
2. [Part 2: API Endpoint Analysis](#part-2-api-endpoint-analysis)
3. [Part 3: Database Schema Review](#part-3-database-schema-review)
4. [Part 4: Integration Points](#part-4-integration-points)
5. [Part 5: Priority 3 Command Definitions](#part-5-priority-3-command-definitions)
6. [Implementation Strategy](#implementation-strategy)
7. [Testing Approach](#testing-approach)

---

## Part 1: CLI Command Requirements

### Priority 3 Commands Overview

| Command | Purpose | Status | Dependencies |
|---------|---------|--------|--------------|
| `/insights` | Show project analysis gaps/risks/opportunities | New | `/project` selected |
| `/wizard` | Interactive Q&A for new project setup | New | None (creates project) |
| `/search <query>` | Find projects/specs/questions | New | Authentication required |
| `/filter [type] [category]` | Filter specifications | New | `/project` selected |
| `/resume <session_id>` | Resume a previous session | New | `/project` selected |
| `/status` | Show current project/session status | New | Optional `/project` |

---

### 1. `/insights [project_id]` Command

#### Requirements Analysis

**Purpose:** Display project analysis including specification gaps, risks, and opportunities.

**Input Parameters:**
- `project_id` (optional): UUID of project to analyze
  - If not provided, use `current_project.id`
  - If not available, show error

**Data Requirements:**
- Project object (name, id, maturity_score, current_phase, status)
- All specifications for the project (with category, confidence, content)
- Count of specs by category
- Expected categories (goals, requirements, tech_stack, scalability, security, performance, testing, monitoring, data_retention, disaster_recovery)

**Processing:**
- Identify missing categories (gaps)
- Find low-confidence specs (<0.7) = risks
- Identify well-covered categories (≥5 specs) = opportunities
- Calculate coverage percentage

**Output Format:**
```
╔══════════════════════════════════════════════════════════╗
║          PROJECT INSIGHTS: [Project Name]                ║
╚══════════════════════════════════════════════════════════╝

[GAPS - Missing Categories]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HIGH:  Security Requirements
       → Define security requirements
       → Review best practices
       → Document assumptions

MEDIUM: Testing Strategy
        → Document test plans
        ...

[RISKS - Low Confidence Items]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 specs with confidence < 70%
→ Review and validate these items
→ Update specifications with more detail
→ Conduct additional research

[OPPORTUNITIES - Well Covered Areas]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Goals (8 specs)
→ Requirements (12 specs)
→ Tech Stack (6 specs)

[SUMMARY]
━━━━━━━
Coverage: 70% (7/10 categories)
Total Insights: 8 (3 gaps, 2 risks, 3 opportunities)
```

**Error Cases:**
- Project not found: `[red]Project not found: {id}[/red]`
- No project selected: Show help message
- API error: `[red]Error fetching insights: {error}[/red]`

**API Dependency:**
- Backend endpoint: `GET /api/v1/insights/{project_id}`
- Authentication: Bearer token required
- Returns: `InsightsResponse` with insights list and summary

---

### 2. `/wizard` Command

#### Requirements Analysis

**Purpose:** Interactive step-by-step guide to create and set up a new project with optional template.

**Input Parameters:**
- None (interactive prompts)

**Data Flow:**
1. Ask project name
2. Ask project description
3. Show available templates
4. Ask if user wants to use template
5. If yes: Show template details, apply template to project
6. Set current_project to new project
7. Show next steps

**Processing:**
- Create project via API
- If template selected, apply it
- Store project in `current_project`
- Auto-select the project

**Output Format:**
```
╔════════════════════════════════════════════╗
║      NEW PROJECT SETUP WIZARD              ║
╚════════════════════════════════════════════╝

[1/5] Project Name:
> [user input]

[2/5] Project Description:
> [user input]

[3/5] Choose Template (or skip with Enter):
 1. Web Application      - Full-stack web app template
 2. REST API            - Microservice/backend API
 3. Mobile Application  - iOS/Android mobile app
 4. (Skip - no template)
> [user input]

[4/5] Template Selected: Web Application
     Would apply 35 specifications covering:
     • Goals & Requirements
     • Tech Stack
     • Security
     • Performance
     Confirm? (y/n): [user input]

[5/5] Creating project...

[green]✓ Project created successfully[/green]
ID:   [project-uuid]
Name: [Project Name]
Templates: 35 specs loaded from "Web Application"

Ready to start? Type /session start to begin!
```

**Error Cases:**
- Network error during creation: Show retry prompt
- Invalid inputs: Validate and re-prompt
- Template apply fails: Warn but complete project creation

**API Dependencies:**
- `POST /api/v1/projects` - Create project
- `GET /api/v1/templates` - List templates
- `GET /api/v1/templates/{template_id}` - Get template details
- `POST /api/v1/templates/{template_id}/apply` - Apply template

---

### 3. `/search <query>` Command

#### Requirements Analysis

**Purpose:** Full-text search across all user projects, specifications, and questions.

**Input Parameters:**
- `query` (required): Search text (1-500 characters)
- Optional filter flags:
  - `--type <projects|specifications|questions|all>` (default: all)
  - `--category <category_name>` (e.g., security, requirements)
  - `--limit <number>` (default: 20, max: 100)

**Data Requirements:**
- User's projects (name, description, id)
- Specifications with category and content
- Questions with category and text
- Relevance scoring (simple text matching)

**Processing:**
- Search across all three resource types
- Apply type/category filters
- Score by relevance (keyword matching)
- Paginate results
- Return resource counts by type

**Output Format:**
```
SEARCH RESULTS FOR "fastapi"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 8 results | Projects: 1 | Specs: 5 | Questions: 2

[PROJECT] My API Backend (Score: 1.0)
         Description: Building RESTful APIs with FastAPI...
         └ /project select proj-123

[SPECIFICATION] Tech Stack Requirements (Score: 1.0)
                Category: tech_stack
                Content: Use FastAPI for API framework...
                Project: My API Backend
                └ /project select proj-123

[QUESTION] API Framework Choice (Score: 0.95)
           Category: tech_stack
           Context: Determining which framework to use
           Project: My API Backend
           └ /project select proj-123

[Page 1 of 2] Next: /search fastapi --limit 20 --offset 8
```

**Error Cases:**
- Query too short: `[yellow]Query must be at least 1 character[/yellow]`
- No results: `[yellow]No results found for "{query}"[/yellow]`
- API error: `[red]Search failed: {error}[/red]`

**API Dependency:**
- Backend endpoint: `GET /api/v1/search?query=...&resource_type=...&category=...`
- Authentication: Bearer token required
- Returns: `SearchResponse` with results, totals, and counts

---

### 4. `/filter [type] [category]` Command

#### Requirements Analysis

**Purpose:** Filter and display specifications for current project by type and category.

**Input Parameters:**
- `type` (optional): Filter type - "spec" or "question" (default: spec)
- `category` (optional): Category name (goals, requirements, security, etc.)

**Data Requirements:**
- All specifications/questions for current_project
- Categories and their content
- Confidence scores for specs
- Source information (user_input, extracted, inferred)

**Processing:**
- Query specs/questions for current project
- Apply category filter if specified
- Group by category
- Count items per category
- Display in sortable table

**Output Format:**
```
SPECIFICATIONS FOR: [Project Name] [Filters Applied]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Category: security (3 specs)
────────────────────────
□ Implement OAuth2 for user authentication
  Source: extracted | Confidence: 95% | Created: 2 hours ago

□ Enable HTTPS/TLS for all connections
  Source: user_input | Confidence: 100% | Created: 1 hour ago

□ Regular security audits quarterly
  Source: inferred | Confidence: 70% | Created: 30 min ago

Category: performance (2 specs)
───────────────────────────────
□ API response time < 200ms
  Source: user_input | Confidence: 100% | Created: 45 min ago

□ Support 10,000 concurrent users
  Source: extracted | Confidence: 80% | Created: 10 min ago

Total: 5 specifications
Use /insights for gap analysis
```

**Error Cases:**
- No project selected: Show error
- Invalid category: List available categories
- No specs in category: `[yellow]No {category} specifications found[/yellow]`

**Database Requirements:**
- Query Specification model with filters
- Access current_project.id
- Group results by category

---

### 5. `/resume <session_id>` Command

#### Requirements Analysis

**Purpose:** Resume a previous paused/ended session and continue with Socratic questioning.

**Input Parameters:**
- `session_id` (required): UUID of session to resume
- Or show list of recent sessions if not provided

**Data Requirements:**
- Session object (id, project_id, status, mode, started_at, ended_at)
- Associated project (name, id)
- Session conversation history (if needed)
- Last question context

**Processing:**
1. Validate session exists and belongs to user
2. Verify session status (paused/completed OK, active shows warning)
3. Load session into memory
4. Load associated project
5. Resume session (change status to active if was paused)
6. Display session summary
7. Prepare for next question

**Output Format:**
```
RESUMING SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project: [Project Name]
Session ID: [session-uuid]
Mode: Socratic Questioning
Originally started: [date/time]
Previous duration: 45 minutes

Conversation summary:
• 12 questions asked
• 5 specification topics covered
• Last topic: Security requirements

[green]✓ Session resumed[/green]

Ready for the next question? Type your response or /quit

Q1: What are your authentication requirements?
→
```

**Error Cases:**
- Session not found: `[red]Session not found: {id}[/red]`
- Session belongs to different project: Error
- Already active session: Warn and ask to end first
- No session_id provided: Show recent sessions list

**API Dependencies:**
- `GET /api/v1/sessions/{session_id}` - Get session details
- `GET /api/v1/sessions/{session_id}/history` - Get conversation
- `PUT /api/v1/sessions/{session_id}` - Update session status
- Possibly endpoint to fetch recent sessions

---

### 6. `/status` Command

#### Requirements Analysis

**Purpose:** Display current project and session status, with quick stats and next actions.

**Input Parameters:**
- None (shows current state)

**Data Requirements:**
- Current project details (if selected)
- Current session details (if active)
- Project stats:
  - Total specs count
  - Specs by category
  - Maturity score
  - Current phase
- Session stats:
  - Questions asked
  - Time elapsed
  - Mode (socratic/direct)

**Processing:**
- Display current_project status if available
- Display current_session status if available
- Show quick stats
- Suggest next actions based on state

**Output Format:**
```
═══════════════════════════════════════════════════
                  CURRENT STATUS
═══════════════════════════════════════════════════

[PROJECT STATUS]
Name:           My Web Application
ID:             proj-12345678
Phase:          discovery
Maturity:       35%
Status:         active
Created:        5 days ago
Specs:          18 total (5 categories covered)
                └ goals: 4 | requirements: 7 | security: 3 | performance: 2 | tech_stack: 2

Last updated:   10 minutes ago

[SESSION STATUS]
ID:             sess-87654321
Mode:           Socratic Questioning 🤔
Status:         active
Started:        2 hours 15 min ago
Questions:      12
Coverage:       50% (5 categories touched)

[NEXT STEPS]
→ Continue Socratic session: Just type your response
→ View insights: /insights
→ Filter specs: /filter security
→ Search: /search performance requirements
→ End session: /session end

═══════════════════════════════════════════════════
```

If no project selected:
```
[yellow]No project selected[/yellow]
Create new: /project create
Or list existing: /projects
```

If no session active:
```
[green]Project selected[/green]
Start session: /session start
```

---

## Part 2: API Endpoint Analysis

### Already Implemented Endpoints (3 new)

#### 2.1 Search Endpoint

**File:** `/backend/app/api/search.py`

**Endpoint:** `GET /api/v1/search`

**Request Parameters:**
```python
query: str          # Required, min 1, max 500 chars
resource_type: str  # Optional: 'projects', 'specifications', 'questions'
category: str       # Optional: Filter by category
skip: int           # Default 0, pagination offset
limit: int          # Default 20, max 100
```

**Response Model: SearchResponse**
```python
{
    "success": bool,
    "query": str,
    "results": [
        {
            "resource_type": "project|specification|question",
            "id": str,
            "title": str,
            "preview": str,
            "category": str|null,
            "project_id": str|null,
            "relevance_score": float
        }
    ],
    "total": int,
    "skip": int,
    "limit": int,
    "resource_counts": {
        "projects": int,
        "specifications": int,
        "questions": int
    }
}
```

**Authentication:** Bearer token required (get_current_active_user)

**Error Handling:**
- 401: Not authenticated
- 400: Invalid query length
- Database errors: 500

**Data Validation:**
- Query length: 1-500 characters
- Skip: >= 0
- Limit: 1-100
- resource_type: Must be valid type or None
- category: Case-sensitive match

**CLI Data Mapping:**
```
API result.resource_type → Display as "PROJECT" | "SPECIFICATION" | "QUESTION"
API result.title → Display as primary text
API result.preview → Show description
API result.project_id → Use for /project select
API result_counts → Show "Page 1 of X"
```

---

#### 2.2 Insights Endpoint

**File:** `/backend/app/api/insights.py`

**Endpoint:** `GET /api/v1/insights/{project_id}`

**Request Parameters:**
```python
project_id: str     # URL parameter, required
insight_type: str   # Query param optional: 'gaps', 'risks', 'opportunities', 'all'
```

**Response Model: InsightsResponse**
```python
{
    "success": bool,
    "project_id": str,
    "project_name": str,
    "insights": [
        {
            "type": "gap|risk|opportunity",
            "title": str,
            "description": str,
            "severity": "low|medium|high",
            "category": str|null,
            "recommendations": [str, str, ...]
        }
    ],
    "summary": {
        "total_insights": int,
        "gaps_count": int,
        "risks_count": int,
        "opportunities_count": int,
        "coverage_percentage": float,
        "most_covered_category": str|null,
        "least_covered_category": str|null
    }
}
```

**Authentication:** Bearer token + Project ownership check

**Error Handling:**
- 401: Not authenticated
- 403: Project belongs to different user
- 404: Project not found
- 500: Database errors

**Expected Categories (for gap detection):**
- goals, requirements, tech_stack, scalability, security, performance
- testing, monitoring, data_retention, disaster_recovery

**Gap Logic:**
- Gap = category with 0 specs
- Severity: high for security/testing, medium for others

**Risk Logic:**
- Risk = specs with confidence < 0.7
- Aggregates all low-confidence items

**Opportunity Logic:**
- Opportunity = category with >= 5 specs
- Shows areas ready for implementation

**CLI Data Mapping:**
```
insight.type → Display color (gap=yellow, risk=red, opportunity=green)
insight.severity → Use for header emphasis
insight.recommendations → Show as bullet points
summary.coverage_percentage → Display as progress
```

---

#### 2.3 Templates Endpoint

**File:** `/backend/app/api/templates.py`

**Endpoint 1: List Templates**
`GET /api/v1/templates`

**Request Parameters:**
```python
skip: int           # Default 0
limit: int          # Default 20, max 100
industry: str       # Optional: 'SaaS', 'Consumer', 'Any'
tags: str           # Optional: comma-separated
```

**Response Model: TemplatesListResponse**
```python
{
    "success": bool,
    "templates": [
        {
            "id": str,
            "name": str,
            "description": str,
            "use_case": str,
            "industry": str|null,
            "categories": [
                {
                    "name": str,
                    "description": str,
                    "examples": [str, str, ...]
                }
            ],
            "estimated_specs": int,
            "difficulty": "beginner|intermediate|advanced",
            "tags": [str, str, ...]
        }
    ],
    "total": int,
    "skip": int,
    "limit": int
}
```

**Built-in Templates:**
1. **Web Application** (35 specs)
   - Categories: Goals, Tech Stack, Security, Performance
   - Tags: [web, saas, full-stack, popular]
   - Difficulty: intermediate

2. **REST API** (25 specs)
   - Categories: Goals, Requirements, Performance
   - Tags: [api, backend, microservices]
   - Difficulty: intermediate

3. **Mobile Application** (30 specs)
   - Categories: Goals, Platform Requirements
   - Tags: [mobile, ios, android, cross-platform]
   - Difficulty: advanced

**Endpoint 2: Get Template Details**
`GET /api/v1/templates/{template_id}`

**Response Model: TemplateDetailResponse**
```python
{
    "success": bool,
    "template": {/* Template object */},
    "preview_specs": [
        {
            "category": str,
            "content": str
        }
    ]
}
```

**Endpoint 3: Apply Template**
`POST /api/v1/templates/{template_id}/apply?project_id={project_id}`

**Response Model: ApplyTemplateResponse**
```python
{
    "success": bool,
    "project_id": str,
    "specs_created": int,
    "message": str
}
```

**Authentication:** All endpoints require Bearer token + Project ownership for apply

**Error Handling:**
- 401: Not authenticated
- 403: Project ownership check on apply
- 404: Template/Project not found
- 500: Database errors

**CLI Data Mapping:**
```
template.estimated_specs → Show as "35 specs"
template.difficulty → Color code (beginner=green, intermediate=yellow, advanced=red)
template.tags → Show as pill badges
```

---

## Part 3: Database Schema Review

### Key Models for Priority 3

#### 3.1 Project Model

**File:** `/backend/app/models/project.py`

**Key Fields:**
```python
class Project(BaseModel):
    # UUID Fields
    id: UUID                    # Primary key
    creator_id: UUID            # Immutable
    owner_id: UUID              # Transferable
    user_id: UUID               # Deprecated (use owner_id)
    
    # Content
    name: String(255)           # Project name
    description: Text|null      # Optional description
    
    # Status & Phase
    current_phase: String(50)   # discovery|analysis|design|implementation
    status: String(20)          # active|archived|completed
    maturity_score: Integer     # 0-100
    
    # Relationships
    sessions: [Session]
    questions: [Question]
    specifications: [Specification]
    quality_metrics: [QualityMetric]
    
    # Timestamps
    created_at: DateTime
    updated_at: DateTime
```

**Indexes:**
- idx_projects_creator_id, owner_id, user_id
- idx_projects_status
- idx_projects_current_phase
- idx_projects_maturity_score

**For Priority 3:**
- `/insights` needs: id, name, user_id (for auth check)
- `/wizard` creates project with defaults: phase='discovery', status='active', maturity_score=0
- `/status` needs: id, name, phase, status, maturity_score, created_at

---

#### 3.2 Session Model

**File:** `/backend/app/models/session.py`

**Key Fields:**
```python
class Session(BaseModel):
    # UUID Fields
    id: UUID                        # Primary key
    project_id: UUID (FK)           # Foreign key to projects
    
    # Mode & Status
    mode: String(20)                # socratic|direct_chat
    status: String(20)              # active|paused|completed
    
    # Timestamps
    started_at: DateTime(timezone=True)
    ended_at: DateTime|null         # NULL if active
    created_at: DateTime
    updated_at: DateTime
    
    # Relationships
    project: Project
    questions: [Question]
    specifications: [Specification]
    conversation_history: [ConversationHistory]
```

**Indexes:**
- idx_sessions_project_id
- idx_sessions_status
- idx_sessions_mode

**For Priority 3:**
- `/resume` needs: id, project_id, status, mode, started_at, ended_at
- `/status` needs: id, mode, status, started_at, question count
- `/filter` queries specs by session_id (optional)

**State Tracking:**
- Status values: 'active' (in progress), 'paused' (can resume), 'completed' (ended)
- Resume logic: Change status from 'paused'/'completed' to 'active'

---

#### 3.3 Specification Model

**File:** `/backend/app/models/specification.py`

**Key Fields:**
```python
class Specification(BaseModel):
    # UUID Fields
    id: UUID                        # Primary key
    project_id: UUID (FK)           # Foreign key to projects
    session_id: UUID|null (FK)      # Foreign key to sessions
    
    # Content
    category: String(100)           # goals|requirements|tech_stack|...
    content: Text                   # The specification text
    
    # Metadata
    source: String(50)              # user_input|extracted|inferred
    confidence: Numeric(3,2)|null   # 0.00-1.00
    is_current: Boolean             # true if not superseded
    
    # Versioning
    superseded_at: DateTime|null
    superseded_by: UUID|null (FK)   # Self-referencing FK
    spec_metadata: JSONB|null       # Additional data
    
    # Timestamps
    created_at: DateTime
    updated_at: DateTime
    
    # Relationships
    project: Project
    session: Session
```

**Indexes:**
- idx_specifications_project_id
- idx_specifications_category
- idx_specifications_is_current (partial, where is_current=true)
- idx_specifications_created_at

**For Priority 3:**
- `/insights` queries: project_id, category, confidence, is_current=true
- `/filter` queries: project_id, category, confidence, source, is_current=true
- `/search` matches: content, category against query
- Count by category for coverage calculation

**Expected Categories:**
- goals, requirements, tech_stack, scalability, security
- performance, testing, monitoring, data_retention, disaster_recovery

**Confidence Scores:**
- 0.00-0.69: Low (risky)
- 0.70-0.89: Medium
- 0.90-1.00: High (trusted)

---

#### 3.4 Question Model

**File:** `/backend/app/models/question.py`

**Key Fields:**
```python
class Question(BaseModel):
    # UUID Fields
    id: UUID                    # Primary key
    project_id: UUID (FK)       # Foreign key to projects
    session_id: UUID (FK)       # Foreign key to sessions
    
    # Content
    text: Text                  # Question text
    category: String(50)        # Same categories as specs
    context: Text|null          # Why this question matters
    
    # Scoring
    quality_score: Numeric(3,2) # 0.00-1.00, default 1.0
    
    # Timestamps
    created_at: DateTime
    updated_at: DateTime
    
    # Relationships
    project: Project
    session: Session
```

**Indexes:**
- idx_questions_project_id
- idx_questions_session_id
- idx_questions_category
- idx_questions_created_at

**For Priority 3:**
- `/search` matches: text, category against query
- `/filter` displays questions by category
- `/resume` loads questions for context

---

### Data Model Relationships

```
User (in socrates_auth)
  ├── owns Projects
  └─ Projects
      ├── has Sessions
      ├── has Questions
      ├── has Specifications
      └── has QualityMetrics
         └── Session
            ├── has Questions
            ├── has Specifications (references)
            └── has ConversationHistory

Search indexes:
  - Full-text on: Project.name, Project.description
  - Full-text on: Specification.content, Specification.category
  - Full-text on: Question.text, Question.category
```

---

## Part 4: Integration Points

### 4.1 CLI to API Communication Pattern

**Current Pattern in Socrates.py:**

```python
class SocratesAPI:
    def _request(self, method: str, endpoint: str, **kwargs) -> Response:
        """Make HTTP request with headers and error handling"""
        headers = self._headers()  # Includes Bearer token
        response = requests.request(method, url, **kwargs)
        return response
    
    def method_name(self, param: str) -> Dict[str, Any]:
        """Wrapper method for specific endpoint"""
        response = self._request("GET", f"/api/v1/endpoint/{param}")
        return response.json()
```

**Error Handling Pattern:**
```python
def api_method(self, param: str) -> Dict[str, Any]:
    try:
        response = self._request("GET", f"/api/v1/endpoint/{param}")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e), "error_code": "CODE"}
```

### 4.2 API Methods to Add to SocratesAPI Class

```python
# Priority 3 API methods needed
def search(self, query: str, resource_type: str = None, 
           category: str = None, skip: int = 0, limit: int = 20) -> Dict:
    """Search endpoint"""
    
def get_insights(self, project_id: str, insight_type: str = None) -> Dict:
    """Get project insights"""
    
def list_templates(self, skip: int = 0, limit: int = 20,
                   industry: str = None, tags: str = None) -> Dict:
    """List templates"""
    
def get_template(self, template_id: str) -> Dict:
    """Get template details"""
    
def apply_template(self, template_id: str, project_id: str) -> Dict:
    """Apply template to project"""
    
def get_session(self, session_id: str) -> Dict:
    """Get session details"""
    
def resume_session(self, session_id: str) -> Dict:
    """Resume a session"""
    
def list_user_sessions(self, skip: int = 0, limit: int = 20) -> Dict:
    """List user's recent sessions"""
```

### 4.3 CLI State Management

**Current State Variables:**
```python
self.current_project: Dict[str, Any]  # Selected project
self.current_session: Dict[str, Any]  # Active session
self.current_question: Dict[str, Any] # Current question
self.chat_mode: str                   # "socratic" or "direct"
```

**State Changes Needed:**
- `/wizard`: Creates project → sets `current_project`
- `/resume`: Loads session → sets `current_session`
- `/filter`: Query current_project → needs `ensure_project_selected()`
- `/insights`: Query current_project → needs `ensure_project_selected()`
- `/search`: No state change (shows results)
- `/status`: Reads state (no change)

**State Persistence:**
- Use `SocratesConfig` to save:
  - current_project_id
  - current_session_id
- Load on CLI startup

### 4.4 Error Handling Patterns

**Validation Checks (in CLI commands):**
```python
def cmd_insights(self, args: List[str]):
    if not self.ensure_authenticated():
        return
    
    project_id = args[0] if args else (
        self.current_project["id"] if self.current_project else None
    )
    
    if not project_id:
        self.console.print("[yellow]No project selected[/yellow]")
        return
    
    try:
        result = self.api.get_insights(project_id)
        if not result.get("success"):
            self.console.print(f"[red]Error: {result.get('error')}[/red]")
            return
        # Display results
    except Exception as e:
        self.console.print(f"[red]Unexpected error: {e}[/red]")
```

**Common Error Codes:**
- `401`: Not authenticated → suggest /login
- `403`: Permission denied → suggest /project select
- `404`: Not found → list available items
- `400`: Bad request → show usage
- `500`: Server error → suggest retry

### 4.5 Pagination & Display

**Current Pattern:**
```python
# List operations show page info
table = Table(title="Items", show_header=True)
table.add_column("ID")
# ... add rows ...
self.console.print(table)

# Show pagination info
total = result.get("total", 0)
skip = result.get("skip", 0)
limit = result.get("limit", 20)
page = (skip // limit) + 1
total_pages = (total + limit - 1) // limit
self.console.print(f"[dim]Page {page} of {total_pages}[/dim]")
```

**Needed for Priority 3:**
- Search results → paginated table
- Filter results → grouped by category table
- Insights → grouped by type (gaps, risks, opportunities)
- Templates → paginated list

---

## Part 5: Priority 3 Command Definitions

### Implementation Checklist

#### Command 1: `/insights`

```python
def cmd_insights(self, args: List[str]):
    """
    Usage: /insights [project_id]
    
    Shows gaps, risks, and opportunities for a project.
    If no project_id provided, uses current_project.
    """
    
    # Validation
    if not self.ensure_authenticated():
        return
    
    # Get project ID
    project_id = args[0] if args else (
        self.current_project["id"] if self.current_project else None
    )
    
    if not project_id:
        self.console.print("[yellow]No project selected. Use /project select <id>[/yellow]")
        return
    
    # API call with progress indicator
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      console=self.console, transient=True) as progress:
            progress.add_task("Analyzing project...", total=None)
            result = self.api.get_insights(project_id)
        
        if not result.get("success"):
            self.console.print(f"[red]Error: {result.get('error')}[/red]")
            return
        
        # Display insights
        self._display_insights(result)
        
    except Exception as e:
        self.console.print(f"[red]Error: {e}[/red]")
        if self.debug:
            import traceback
            self.console.print(traceback.format_exc())

def _display_insights(self, result: Dict):
    """Helper to display insights in formatted output"""
    # Parse response and format for console display
    # Group by type (gaps, risks, opportunities)
    # Use colors: red for risks, yellow for gaps, green for opportunities
    # Show recommendations as bullet points
    # Display summary statistics at bottom
```

---

#### Command 2: `/wizard`

```python
def cmd_wizard(self, args: List[str]):
    """
    Interactive wizard for creating new project with optional template.
    
    Flow:
    1. Ask project name
    2. Ask project description
    3. Show templates
    4. Ask to apply template
    5. Create project and apply template
    6. Set as current project
    """
    
    self.console.print("\n[bold cyan]New Project Setup Wizard[/bold cyan]\n")
    
    # Step 1: Project name
    name = Prompt.ask("[1/5] Project Name")
    if not name:
        self.console.print("[yellow]Project name required[/yellow]")
        return
    
    # Step 2: Description
    description = Prompt.ask(
        "[2/5] Project Description (optional)",
        default=""
    )
    
    # Step 3-4: Templates
    use_template = self._wizard_select_template()
    template_id = None
    if use_template:
        template_id = use_template["id"]
    
    # Step 5: Create project
    try:
        with Progress(...) as progress:
            progress.add_task("Creating project...", total=None)
            create_result = self.api.create_project(name, description)
        
        if not create_result.get("success"):
            self.console.print(f"[red]Failed to create project: {create_result.get('error')}[/red]")
            return
        
        project = create_result["project"]
        
        # Apply template if selected
        if template_id:
            apply_result = self.api.apply_template(template_id, project["id"])
            if apply_result.get("success"):
                specs_created = apply_result.get("specs_created", 0)
                self.console.print(f"[green]✓ Applied template ({specs_created} specs)[/green]")
        
        # Set as current project
        self.current_project = project
        self.config.set("current_project_id", project["id"])
        
        # Display success
        self._display_project_created(project, template_id)
        
    except Exception as e:
        self.console.print(f"[red]Error: {e}[/red]")

def _wizard_select_template(self) -> Optional[Dict]:
    """Helper to show templates and let user select one"""
    # Fetch template list
    # Display in numbered list with descriptions
    # Let user select or skip
    # Return selected template or None
```

---

#### Command 3: `/search <query>`

```python
def cmd_search(self, args: List[str]):
    """
    Usage: /search <query> [--type TYPE] [--category CAT] [--limit NUM]
    
    Search across projects, specifications, and questions.
    """
    
    if not self.ensure_authenticated():
        return
    
    if not args:
        self.console.print("[yellow]Usage: /search <query> [--type TYPE] [--category CAT] [--limit NUM][/yellow]")
        return
    
    # Parse arguments
    query = args[0]
    resource_type = None
    category = None
    limit = 20
    
    # Parse optional flags
    i = 1
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            resource_type = args[i + 1]
            i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            i += 1
    
    # Validate query
    if len(query) < 1 or len(query) > 500:
        self.console.print("[yellow]Query must be 1-500 characters[/yellow]")
        return
    
    # API call
    try:
        with Progress(...) as progress:
            progress.add_task("Searching...", total=None)
            result = self.api.search(query, resource_type, category, 0, limit)
        
        if not result.get("success"):
            self.console.print(f"[red]Error: {result.get('error')}[/red]")
            return
        
        # Display results
        if not result.get("results"):
            self.console.print(f"[yellow]No results found for \"{query}\"[/yellow]")
            return
        
        self._display_search_results(result)
        
    except Exception as e:
        self.console.print(f"[red]Error: {e}[/red]")

def _display_search_results(self, result: Dict):
    """Format and display search results"""
    # Show header with search stats
    # Group results by resource_type
    # Use different colors for each type
    # Show preview text
    # Include navigation to select items
```

---

#### Command 4: `/filter [type] [category]`

```python
def cmd_filter(self, args: List[str]):
    """
    Usage: /filter [spec|question] [category]
    
    Filter and display specifications or questions for current project.
    """
    
    if not self.ensure_authenticated():
        return
    
    if not self.ensure_project_selected():
        return
    
    filter_type = args[0].lower() if args else "spec"
    category = args[1].lower() if len(args) > 1 else None
    
    if filter_type not in ["spec", "specification", "question", "q"]:
        self.console.print("[yellow]Type: spec or question[/yellow]")
        return
    
    # Normalize type
    is_spec = filter_type in ["spec", "specification"]
    
    try:
        with Progress(...) as progress:
            progress.add_task("Loading...", total=None)
            # Query from backend or load from current_project state
            # Could add endpoint to filter, or do client-side filtering
            results = self._filter_project_items(
                self.current_project["id"],
                is_spec,
                category
            )
        
        if not results:
            item_type = "specifications" if is_spec else "questions"
            self.console.print(f"[yellow]No {item_type} found[/yellow]")
            return
        
        self._display_filtered_results(results, is_spec)
        
    except Exception as e:
        self.console.print(f"[red]Error: {e}[/red]")

def _filter_project_items(self, project_id: str, is_spec: bool, category: str) -> List[Dict]:
    """Get filtered items for project"""
    # Query appropriate endpoint or use cached data
    # For now, could be client-side filtering of specs
```

---

#### Command 5: `/resume <session_id>`

```python
def cmd_resume(self, args: List[str]):
    """
    Usage: /resume [session_id]
    
    Resume a previous session.
    If no session_id provided, show list of recent sessions.
    """
    
    if not self.ensure_authenticated():
        return
    
    session_id = args[0] if args else None
    
    if not session_id:
        # Show recent sessions
        self._show_recent_sessions()
        return
    
    # Get session details
    try:
        with Progress(...) as progress:
            progress.add_task("Loading session...", total=None)
            result = self.api.get_session(session_id)
        
        if not result.get("success"):
            self.console.print(f"[red]Error: {result.get('error')}[/red]")
            return
        
        session = result["session"]
        
        # Update current state
        self.current_session = session
        self.current_project = {"id": session["project_id"]}  # Load full project
        
        # Display session info
        self._display_session_resumed(session)
        
        # Ready for chat
        
    except Exception as e:
        self.console.print(f"[red]Error: {e}[/red]")

def _show_recent_sessions(self):
    """Display list of recent sessions to resume"""
    # Query API for recent sessions
    # Show in table with project name, date, duration
    # Allow user to select or type session ID
```

---

#### Command 6: `/status`

```python
def cmd_status(self, args: List[str]):
    """
    Show current project and session status.
    """
    
    if not self.ensure_authenticated():
        return
    
    # Display project status if available
    if self.current_project:
        self._display_project_status(self.current_project)
    else:
        self.console.print("[yellow]No project selected[/yellow]")
        self.console.print("[dim]Create: /project create | List: /projects[/dim]")
        return
    
    # Display session status if available
    if self.current_session:
        self._display_session_status(self.current_session)
    else:
        self.console.print("[dim]No active session[/dim]")
        self.console.print("[dim]Start: /session start[/dim]")
    
    # Show next steps
    self._display_next_steps()

def _display_project_status(self, project: Dict):
    """Format project status display"""
    # Show project info in formatted panel
    # Include stats (specs, phase, maturity)
    # Color code based on maturity

def _display_session_status(self, session: Dict):
    """Format session status display"""
    # Show session info
    # Calculate duration
    # Show question count if available

def _display_next_steps(self):
    """Show suggested next actions"""
    # Based on current state, suggest relevant commands
```

---

## Implementation Strategy

### Phase 1: API Method Additions (CLI Layer)

**File:** `Socrates.py` - Add to SocratesAPI class

```python
# Add 6 API wrapper methods:
1. search(query, resource_type, category, skip, limit)
2. get_insights(project_id, insight_type)
3. list_templates(skip, limit, industry, tags)
4. get_template(template_id)
5. apply_template(template_id, project_id)
6. get_session(session_id) - already exists
7. list_recent_sessions(skip, limit) - new
```

### Phase 2: Command Implementation (CLI Layer)

**File:** `Socrates.py` - Add to SocratesCLI class

```python
# Add 6 command methods:
1. cmd_insights(args)
2. cmd_wizard(args)
3. cmd_search(args)
4. cmd_filter(args)
5. cmd_resume(args)
6. cmd_status(args)

# Add helper methods for display:
1. _display_insights(result)
2. _display_search_results(result)
3. _display_filtered_results(results, is_spec)
4. _display_project_status(project)
5. _display_session_status(session)
6. _display_next_steps()
7. _display_project_created(project, template_id)
8. _wizard_select_template()
9. _show_recent_sessions()
10. _filter_project_items(project_id, is_spec, category)
```

### Phase 3: Command Registration

**File:** `Socrates.py` - Update in `__init__`

```python
# Add to self.commands list:
self.commands = [
    # ... existing ...
    "/insights", "/wizard", "/search", "/filter", "/resume", "/status"
]

# Add to handle_command method:
elif command == "/insights":
    self.cmd_insights(args)
elif command == "/wizard":
    self.cmd_wizard(args)
elif command == "/search":
    self.cmd_search(args)
elif command == "/filter":
    self.cmd_filter(args)
elif command == "/resume":
    self.cmd_resume(args)
elif command == "/status":
    self.cmd_status(args)
```

### Phase 4: Help Text Updates

**File:** `Socrates.py` - Update in `print_help()`

```python
# Add Priority 3 commands to help text
# Update /help output to include new commands
# Add usage examples
```

### Phase 5: Testing & Integration

```python
# Test files:
1. test_cli_priority3_commands.py - Unit tests
2. Integration with existing commands
3. Error handling validation
4. API error response handling
```

---

## Testing Approach

### Unit Test Strategy

**Test File:** `test_cli_priority3_commands.py`

#### Test Cases per Command

**For `/insights`:**
```python
def test_insights_with_project_selected()
def test_insights_with_project_id_arg()
def test_insights_no_project()
def test_insights_api_error()
def test_insights_display_format()
```

**For `/wizard`:**
```python
def test_wizard_create_project()
def test_wizard_with_template()
def test_wizard_without_template()
def test_wizard_cancel()
def test_wizard_api_error()
```

**For `/search`:**
```python
def test_search_basic()
def test_search_with_filters()
def test_search_by_type()
def test_search_by_category()
def test_search_invalid_query()
def test_search_no_results()
def test_search_pagination()
```

**For `/filter`:**
```python
def test_filter_specifications()
def test_filter_questions()
def test_filter_by_category()
def test_filter_no_project()
def test_filter_no_results()
```

**For `/resume`:**
```python
def test_resume_existing_session()
def test_resume_invalid_session()
def test_resume_no_session_id()
def test_resume_session_list()
```

**For `/status`:**
```python
def test_status_with_project()
def test_status_with_session()
def test_status_no_project()
def test_status_display_format()
```

### Integration Tests

```python
def test_wizard_then_insights()
    # Create project with wizard
    # Check insights works on new project

def test_search_finds_created_project()
    # Create project
    # Search for project
    # Verify it appears in results

def test_resume_after_pause()
    # Start session
    # Pause it
    # Resume and verify state
```

### Error Handling Tests

```python
def test_api_401_error_handling()
def test_api_403_error_handling()
def test_api_404_error_handling()
def test_api_500_error_handling()
def test_network_error_handling()
```

### Display Format Tests

```python
def test_insights_table_display()
def test_search_results_formatting()
def test_filter_results_grouping()
def test_status_panel_display()
```

---

## Summary & Next Steps

### Completed Analysis
- ✅ 6 Priority 3 CLI commands fully specified
- ✅ 3 backend API endpoints reviewed and documented
- ✅ Database schema requirements identified
- ✅ Integration points and patterns established
- ✅ Error handling strategy defined
- ✅ Testing approach documented

### Ready for Implementation
1. **SocratesAPI additions** - 7 new wrapper methods (~50 lines)
2. **SocratesCLI commands** - 6 new command methods (~400 lines)
3. **Helper methods** - 10 display/utility methods (~300 lines)
4. **Help text updates** - Updated usage documentation
5. **Tests** - Comprehensive test coverage (~500 lines)

### Key Implementation Notes

**Critical Dependencies:**
- All commands require Authentication (Bearer token)
- `/insights`, `/filter`, `/resume` require Project selection
- `/wizard` can create new project without selection
- `/search` works at user level (any project)

**API Dependencies Ready:**
- ✅ `/api/v1/search` - Implemented in backend
- ✅ `/api/v1/insights/{project_id}` - Implemented in backend
- ✅ `/api/v1/templates` - Implemented in backend
- ✅ `/api/v1/templates/{id}` - Implemented in backend
- ✅ `/api/v1/templates/{id}/apply` - Implemented in backend
- ⚠️ `/api/v1/sessions/{id}/resume` - May need backend endpoint

**Optional Backend Enhancement:**
- List recent sessions endpoint - for `/resume` without args
- Could alternatively use client-side caching

### Estimated Implementation Time
- API methods: 1-2 hours
- CLI commands: 3-4 hours
- Tests: 2-3 hours
- Total: 6-9 hours for complete implementation

---

## Appendix: File Locations Reference

**CLI Implementation:**
- `/home/user/Socrates2/Socrates.py` (lines 1-1528)

**API Endpoints:**
- `/home/user/Socrates2/backend/app/api/search.py`
- `/home/user/Socrates2/backend/app/api/insights.py`
- `/home/user/Socrates2/backend/app/api/templates.py`

**Database Models:**
- `/home/user/Socrates2/backend/app/models/project.py`
- `/home/user/Socrates2/backend/app/models/session.py`
- `/home/user/Socrates2/backend/app/models/specification.py`
- `/home/user/Socrates2/backend/app/models/question.py`

**Main Application:**
- `/home/user/Socrates2/backend/app/main.py` (includes all routers)

**Configuration:**
- `/home/user/Socrates2/cli-requirements.txt` (CLI dependencies)
- `/home/user/Socrates2/backend/requirements.txt` (Backend dependencies)

---

**Analysis Complete** ✓

This document provides comprehensive specifications for implementing all 6 Priority 3 CLI commands with full integration to existing backend endpoints and database models.

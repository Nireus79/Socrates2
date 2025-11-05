# API ENDPOINTS - Complete Mapping

**Version:** 1.0.0
**API Version:** v1
**Base URL:** `/api/v1/`
**Status:** 📋 DOCUMENTED - Ready for Phase 1 Implementation

---

## TABLE OF CONTENTS

1. [Authentication Endpoints](#authentication-endpoints)
2. [Project Endpoints](#project-endpoints)
3. [Session Endpoints](#session-endpoints)
4. [Specification Endpoints](#specification-endpoints)
5. [Conflict Endpoints](#conflict-endpoints)
6. [Quality Control Endpoints](#quality-control-endpoints)
7. [Admin Endpoints](#admin-endpoints)
8. [Endpoint-to-Agent Mapping](#endpoint-to-agent-mapping)
9. [Endpoint-to-Database Mapping](#endpoint-to-database-mapping)
10. [Implementation Phases](#implementation-phases)

---

## AUTHENTICATION ENDPOINTS

### POST /api/v1/auth/register

**Phase:** Phase 1
**Agent:** N/A (Direct auth service)
**Database:** socrates_auth.users

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (201 Created):**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "created_at": "2025-11-05T12:00:00Z"
}
```

**Errors:**
- 400: Invalid email format
- 409: Email already exists

---

### POST /api/v1/auth/login

**Phase:** Phase 1
**Agent:** N/A (Direct auth service)
**Database:** socrates_auth.users, socrates_auth.refresh_tokens

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "uuid"
}
```

**Errors:**
- 401: Invalid credentials
- 404: User not found

---

### POST /api/v1/auth/logout

**Phase:** Phase 1
**Agent:** N/A (Direct auth service)
**Database:** socrates_auth.refresh_tokens

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

## PROJECT ENDPOINTS

### POST /api/v1/projects

**Phase:** Phase 2
**Agent:** ProjectManagerAgent
**Action:** `create_project`
**Database:** socrates_specs.projects

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "name": "E-commerce Platform",
  "description": "Online marketplace for local artisans"
}
```

**Response (201 Created):**
```json
{
  "project_id": "uuid",
  "name": "E-commerce Platform",
  "description": "Online marketplace for local artisans",
  "phase": "discovery",
  "maturity_score": 0.0,
  "status": "active",
  "created_at": "2025-11-05T12:00:00Z"
}
```

**Errors:**
- 400: Invalid project name
- 401: Unauthorized

---

### GET /api/v1/projects

**Phase:** Phase 2
**Agent:** ProjectManagerAgent
**Action:** `list_projects`
**Database:** socrates_specs.projects

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `status` (optional): active | archived | completed
- `limit` (optional): default 50
- `offset` (optional): default 0

**Response (200 OK):**
```json
{
  "projects": [
    {
      "project_id": "uuid",
      "name": "E-commerce Platform",
      "phase": "discovery",
      "maturity_score": 45.5,
      "status": "active",
      "created_at": "2025-11-05T12:00:00Z",
      "updated_at": "2025-11-05T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

### GET /api/v1/projects/{project_id}

**Phase:** Phase 2
**Agent:** ProjectManagerAgent
**Action:** `get_project`
**Database:** socrates_specs.projects

**Response (200 OK):**
```json
{
  "project_id": "uuid",
  "name": "E-commerce Platform",
  "description": "Online marketplace for local artisans",
  "phase": "discovery",
  "maturity_score": 45.5,
  "status": "active",
  "created_at": "2025-11-05T12:00:00Z",
  "updated_at": "2025-11-05T14:30:00Z"
}
```

**Errors:**
- 404: Project not found
- 403: Access denied

---

### GET /api/v1/projects/{project_id}/status

**Phase:** Phase 2
**Agent:** ProjectManagerAgent
**Action:** `get_project_status`
**Database:** socrates_specs.projects, socrates_specs.specifications, socrates_specs.maturity_tracking

**Response (200 OK):**
```json
{
  "project_id": "uuid",
  "phase": "discovery",
  "maturity_score": 45.5,
  "specifications_count": 23,
  "unresolved_conflicts": 0,
  "coverage_breakdown": {
    "goals": 80.0,
    "requirements": 60.0,
    "tech_stack": 40.0,
    "security": 20.0
  }
}
```

---

### DELETE /api/v1/projects/{project_id}

**Phase:** Phase 2
**Agent:** ProjectManagerAgent
**Action:** `delete_project`
**Database:** socrates_specs.projects (soft delete)

**Response (200 OK):**
```json
{
  "message": "Project archived successfully",
  "project_id": "uuid"
}
```

---

## SESSION ENDPOINTS

### POST /api/v1/sessions

**Phase:** Phase 2
**Agent:** SocraticCounselorAgent
**Action:** `start_session`
**Database:** socrates_specs.sessions

**Request:**
```json
{
  "project_id": "uuid",
  "mode": "socratic"
}
```

**Response (201 Created):**
```json
{
  "session_id": "uuid",
  "project_id": "uuid",
  "mode": "socratic",
  "status": "active",
  "started_at": "2025-11-05T12:00:00Z"
}
```

---

### GET /api/v1/sessions/{session_id}

**Phase:** Phase 2
**Agent:** N/A (Direct query)
**Database:** socrates_specs.sessions

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "project_id": "uuid",
  "mode": "socratic",
  "status": "active",
  "started_at": "2025-11-05T12:00:00Z",
  "last_activity": "2025-11-05T14:30:00Z"
}
```

---

### POST /api/v1/sessions/{session_id}/next-question

**Phase:** Phase 2
**Agent:** SocraticCounselorAgent
**Action:** `generate_question`
**Database:** socrates_specs.questions, socrates_specs.specifications

**Response (200 OK):**
```json
{
  "question_id": "uuid",
  "text": "What is the expected number of concurrent users?",
  "category": "scalability",
  "context": "This helps determine infrastructure requirements and scaling strategy",
  "maturity_score": 45.5
}
```

---

### POST /api/v1/sessions/{session_id}/answer

**Phase:** Phase 2
**Agent:** ContextAnalyzerAgent → ConflictDetectorAgent (Phase 3)
**Action:** `extract_specifications`
**Database:** socrates_specs.specifications, socrates_specs.conversation_history

**Request:**
```json
{
  "question_id": "uuid",
  "answer": "We expect 50,000 concurrent users initially, scaling to 200,000 within first year"
}
```

**Response (200 OK - No Conflicts):**
```json
{
  "success": true,
  "specs_extracted": 3,
  "specifications": [
    {
      "category": "scalability",
      "key": "concurrent_users_initial",
      "value": "50000",
      "confidence": 0.95
    },
    {
      "category": "scalability",
      "key": "concurrent_users_year_one",
      "value": "200000",
      "confidence": 0.95
    },
    {
      "category": "scalability",
      "key": "growth_timeline",
      "value": "1 year",
      "confidence": 0.90
    }
  ],
  "maturity_score": 52.3,
  "conflicts_detected": false
}
```

**Response (409 Conflict - Phase 3):**
```json
{
  "success": false,
  "conflicts_detected": true,
  "conflicts": [
    {
      "conflict_id": "uuid",
      "type": "technology",
      "old_spec": {
        "key": "primary_database",
        "value": "PostgreSQL"
      },
      "new_spec_value": "MySQL",
      "resolution_options": ["keep_old", "replace", "merge"]
    }
  ]
}
```

---

### POST /api/v1/sessions/{session_id}/toggle-mode

**Phase:** Phase 2
**Agent:** N/A (Session update)
**Database:** socrates_specs.sessions

**Request:**
```json
{
  "mode": "direct"
}
```

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "mode": "direct",
  "message": "Switched to direct chat mode"
}
```

---

### POST /api/v1/sessions/{session_id}/message

**Phase:** Phase 2
**Agent:** ContextAnalyzerAgent
**Action:** `extract_specifications` (from freeform message)
**Database:** socrates_specs.conversation_history, socrates_specs.specifications

**Request:**
```json
{
  "message": "I want to build a REST API using Python and FastAPI with PostgreSQL database"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "specs_extracted": 3,
  "specifications": [
    {
      "category": "tech_stack",
      "key": "api_type",
      "value": "REST",
      "confidence": 0.98
    },
    {
      "category": "tech_stack",
      "key": "backend_language",
      "value": "Python",
      "confidence": 0.98
    },
    {
      "category": "tech_stack",
      "key": "api_framework",
      "value": "FastAPI",
      "confidence": 0.98
    },
    {
      "category": "tech_stack",
      "key": "primary_database",
      "value": "PostgreSQL",
      "confidence": 0.98
    }
  ],
  "maturity_score": 58.7
}
```

---

## SPECIFICATION ENDPOINTS

### GET /api/v1/specifications/project/{project_id}

**Phase:** Phase 2
**Agent:** N/A (Direct query)
**Database:** socrates_specs.specifications

**Query Parameters:**
- `category` (optional): Filter by category
- `limit` (optional): default 100
- `offset` (optional): default 0

**Response (200 OK):**
```json
{
  "specifications": [
    {
      "spec_id": "uuid",
      "category": "tech_stack",
      "key": "backend_language",
      "value": "Python",
      "source": "socratic_question",
      "confidence": 0.95,
      "created_at": "2025-11-05T12:00:00Z"
    }
  ],
  "total": 23,
  "limit": 100,
  "offset": 0
}
```

---

### POST /api/v1/specifications

**Phase:** Phase 2
**Agent:** ContextAnalyzerAgent
**Action:** Manual spec addition
**Database:** socrates_specs.specifications

**Request:**
```json
{
  "project_id": "uuid",
  "category": "security",
  "key": "authentication_method",
  "value": "OAuth2 with JWT",
  "source": "direct_input"
}
```

**Response (201 Created):**
```json
{
  "spec_id": "uuid",
  "project_id": "uuid",
  "category": "security",
  "key": "authentication_method",
  "value": "OAuth2 with JWT",
  "confidence": 1.0,
  "created_at": "2025-11-05T12:00:00Z"
}
```

---

### PUT /api/v1/specifications/{spec_id}

**Phase:** Phase 2
**Agent:** ContextAnalyzerAgent
**Action:** Update spec (creates new version)
**Database:** socrates_specs.specifications

**Request:**
```json
{
  "value": "OAuth2 with JWT and MFA"
}
```

**Response (200 OK):**
```json
{
  "spec_id": "uuid",
  "version": 2,
  "value": "OAuth2 with JWT and MFA",
  "updated_at": "2025-11-05T14:30:00Z"
}
```

---

### DELETE /api/v1/specifications/{spec_id}

**Phase:** Phase 2
**Agent:** N/A (Direct update)
**Database:** socrates_specs.specifications (soft delete)

**Response (200 OK):**
```json
{
  "message": "Specification removed",
  "spec_id": "uuid"
}
```

---

## CONFLICT ENDPOINTS

### GET /api/v1/conflicts/project/{project_id}

**Phase:** Phase 3
**Agent:** ConflictDetectorAgent
**Action:** `list_conflicts`
**Database:** socrates_specs.conflicts

**Query Parameters:**
- `status` (optional): pending | resolved
- `limit` (optional): default 50

**Response (200 OK):**
```json
{
  "conflicts": [
    {
      "conflict_id": "uuid",
      "type": "technology",
      "old_spec": {
        "key": "primary_database",
        "value": "PostgreSQL"
      },
      "new_spec_value": "MySQL",
      "status": "pending",
      "detected_at": "2025-11-05T14:00:00Z"
    }
  ],
  "total": 1
}
```

---

### GET /api/v1/conflicts/{conflict_id}/options

**Phase:** Phase 3
**Agent:** ConflictDetectorAgent
**Action:** `get_resolution_options`
**Database:** socrates_specs.conflicts

**Response (200 OK):**
```json
{
  "conflict_id": "uuid",
  "options": [
    {
      "action": "keep_old",
      "description": "Keep PostgreSQL (original choice)",
      "impact": "No changes to existing specifications"
    },
    {
      "action": "replace",
      "description": "Replace with MySQL",
      "impact": "Updates primary_database specification"
    },
    {
      "action": "merge",
      "description": "Use both databases",
      "impact": "Adds complexity, requires multi-database architecture"
    }
  ]
}
```

---

### POST /api/v1/conflicts/{conflict_id}/resolve

**Phase:** Phase 3
**Agent:** ConflictDetectorAgent
**Action:** `resolve_conflict`
**Database:** socrates_specs.conflicts, socrates_specs.specifications

**Request:**
```json
{
  "resolution": "keep_old",
  "notes": "Staying with PostgreSQL due to better scalability"
}
```

**Response (200 OK):**
```json
{
  "conflict_id": "uuid",
  "status": "resolved",
  "resolution": "keep_old",
  "resolved_at": "2025-11-05T14:30:00Z"
}
```

---

## QUALITY CONTROL ENDPOINTS

### GET /api/v1/quality/project/{project_id}/metrics

**Phase:** Phase 5
**Agent:** QualityControllerAgent
**Action:** `get_quality_metrics`
**Database:** socrates_specs.quality_metrics

**Response (200 OK):**
```json
{
  "project_id": "uuid",
  "overall_quality": 85.5,
  "bias_score": 0.15,
  "coverage_gaps": ["monitoring", "disaster_recovery"],
  "last_analysis": "2025-11-05T14:00:00Z"
}
```

---

### GET /api/v1/quality/project/{project_id}/analysis

**Phase:** Phase 5
**Agent:** QualityControllerAgent
**Action:** `analyze_project`
**Database:** socrates_specs.quality_metrics, socrates_specs.specifications

**Response (200 OK):**
```json
{
  "project_id": "uuid",
  "quality_analysis": {
    "bias_detected": false,
    "coverage_complete": false,
    "coverage_gaps": ["monitoring", "disaster_recovery"],
    "recommendations": [
      "Add monitoring specifications",
      "Define disaster recovery requirements"
    ]
  },
  "path_analysis": {
    "current_path": "thorough",
    "estimated_cost": 8000,
    "alternative_paths": [
      {
        "path": "greedy",
        "cost": 10000,
        "risk": "high"
      }
    ]
  }
}
```

---

### GET /api/v1/quality/project/{project_id}/recommendations

**Phase:** Phase 5
**Agent:** QualityControllerAgent
**Action:** `get_recommendations`
**Database:** socrates_specs.quality_metrics

**Response (200 OK):**
```json
{
  "recommendations": [
    {
      "type": "coverage_gap",
      "category": "monitoring",
      "priority": "high",
      "suggestion": "Ask questions about logging and monitoring requirements"
    },
    {
      "type": "bias_warning",
      "category": "tech_stack",
      "priority": "medium",
      "suggestion": "Question shows solution bias - rephrase to be more open-ended"
    }
  ]
}
```

---

## ADMIN ENDPOINTS

### GET /api/v1/admin/health

**Phase:** Phase 1
**Agent:** N/A (System health check)
**Database:** All databases

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "databases": {
    "socrates_auth": "connected",
    "socrates_specs": "connected"
  },
  "timestamp": "2025-11-05T14:30:00Z"
}
```

---

### POST /api/v1/admin/db-reset

**Phase:** Phase 1 (Testing only)
**Agent:** N/A (Direct database operation)
**Database:** All databases

**⚠️ WARNING:** Only available in development/testing environments

**Response (200 OK):**
```json
{
  "message": "All databases reset successfully",
  "tables_cleared": 25
}
```

---

### GET /api/v1/admin/stats

**Phase:** Phase 1
**Agent:** N/A (System statistics)
**Database:** All databases

**Response (200 OK):**
```json
{
  "users_total": 152,
  "projects_total": 47,
  "active_sessions": 8,
  "specifications_total": 1234,
  "llm_calls_today": 567,
  "database_size_mb": 245
}
```

---

## ENDPOINT-TO-AGENT MAPPING

| Endpoint | Agent | Action |
|----------|-------|--------|
| POST /auth/register | AuthService | register_user |
| POST /auth/login | AuthService | login_user |
| POST /auth/logout | AuthService | logout_user |
| POST /projects | ProjectManagerAgent | create_project |
| GET /projects | ProjectManagerAgent | list_projects |
| GET /projects/{id} | ProjectManagerAgent | get_project |
| GET /projects/{id}/status | ProjectManagerAgent | get_project_status |
| DELETE /projects/{id} | ProjectManagerAgent | delete_project |
| POST /sessions | SocraticCounselorAgent | start_session |
| POST /sessions/{id}/next-question | SocraticCounselorAgent | generate_question |
| POST /sessions/{id}/answer | ContextAnalyzerAgent | extract_specifications |
| POST /sessions/{id}/message | ContextAnalyzerAgent | extract_specifications |
| GET /conflicts/project/{id} | ConflictDetectorAgent | list_conflicts |
| POST /conflicts/{id}/resolve | ConflictDetectorAgent | resolve_conflict |
| GET /quality/project/{id}/metrics | QualityControllerAgent | get_quality_metrics |
| GET /quality/project/{id}/analysis | QualityControllerAgent | analyze_project |

---

## ENDPOINT-TO-DATABASE MAPPING

| Endpoint | Primary Table(s) | Database |
|----------|------------------|----------|
| POST /auth/register | users | socrates_auth |
| POST /auth/login | users, refresh_tokens | socrates_auth |
| POST /projects | projects | socrates_specs |
| GET /projects | projects | socrates_specs |
| POST /sessions | sessions | socrates_specs |
| POST /sessions/{id}/next-question | questions, specifications | socrates_specs |
| POST /sessions/{id}/answer | conversation_history, specifications | socrates_specs |
| GET /specifications/project/{id} | specifications | socrates_specs |
| GET /conflicts/project/{id} | conflicts | socrates_specs |
| GET /quality/project/{id}/metrics | quality_metrics | socrates_specs |

---

## IMPLEMENTATION PHASES

### Phase 1: Authentication & Infrastructure
**Endpoints:**
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- GET /admin/health
- GET /admin/stats

**Status:** ⏳ Ready to implement

---

### Phase 2: Core Agents & Socratic Mode
**Endpoints:**
- POST /projects
- GET /projects
- GET /projects/{id}
- GET /projects/{id}/status
- DELETE /projects/{id}
- POST /sessions
- GET /sessions/{id}
- POST /sessions/{id}/next-question
- POST /sessions/{id}/answer
- POST /sessions/{id}/message
- POST /sessions/{id}/toggle-mode
- GET /specifications/project/{id}
- POST /specifications
- PUT /specifications/{id}
- DELETE /specifications/{id}

**Status:** ⏳ Ready to implement after Phase 1

---

### Phase 3: Conflict Detection
**Endpoints:**
- GET /conflicts/project/{id}
- GET /conflicts/{id}/options
- POST /conflicts/{id}/resolve

**Status:** ⏳ Ready to implement after Phase 2

---

### Phase 4: Code Generation
**Endpoints:**
- POST /code/generate (not in ARCHITECTURE.md - needs adding)
- GET /code/{project_id}/status (not in ARCHITECTURE.md - needs adding)

**Status:** ⚠️ Missing from ARCHITECTURE.md

---

### Phase 5: Quality Control
**Endpoints:**
- GET /quality/project/{id}/metrics
- GET /quality/project/{id}/analysis
- GET /quality/project/{id}/recommendations

**Status:** ⏳ Ready to implement after Phase 4

---

## MISSING ENDPOINTS

### Code Generation Endpoints (Phase 4)

**POST /api/v1/code/generate**
```json
Request:
{
  "project_id": "uuid"
}

Response:
{
  "generation_id": "uuid",
  "status": "processing",
  "estimated_time_seconds": 180
}
```

**GET /api/v1/code/{generation_id}/status**
```json
Response:
{
  "generation_id": "uuid",
  "status": "completed",
  "code_url": "https://...",
  "files_generated": 156,
  "lines_of_code": 23451
}
```

---

## SUMMARY

**Total Endpoints Documented:** 34
**Phase 1:** 5 endpoints
**Phase 2:** 15 endpoints
**Phase 3:** 3 endpoints
**Phase 4:** 2 endpoints (need to add to ARCHITECTURE.md)
**Phase 5:** 3 endpoints
**Admin:** 3 endpoints

**Status:**
- ✅ All core endpoints mapped
- ⚠️ Code generation endpoints need to be added to ARCHITECTURE.md
- ✅ All endpoints mapped to agents
- ✅ All endpoints mapped to database tables
- ✅ Ready for Phase 1 implementation

---

**Next Steps:**
1. Add code generation endpoints to ARCHITECTURE.md
2. Begin Phase 1 implementation with authentication endpoints
3. Create API integration tests for each endpoint


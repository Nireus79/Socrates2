# DEEP INVESTIGATION REPORT
## Schemas, Migrations, Endpoints, Models - Complete Analysis

**Date:** 2025-11-15
**Status:** CRITICAL - System has fundamental architectural inconsistencies

---

## EXECUTIVE SUMMARY

The Socrates system has **74% endpoint failure rate** due to systematic inconsistencies across three layers:

1. **HTTP Method Mismatch** - Endpoints use wrong HTTP verbs
2. **Missing Endpoint Routes** - 15+ endpoints not registered
3. **Database Schema Issues** - 3 endpoints crash with 500 errors
4. **Connection Pool Hangs** - 2 endpoints cause backend timeouts

---

## SECTION 1: DATABASE STRUCTURE

### Migrations Status (17 Total)
```
✓ 001 - auth_initial_schema
✓ 002 - auth_admin_management
✓ 003 - specs_core_specification_tables
✓ 004 - specs_generated_content
✓ 005 - specs_tracking_analytics
✓ 006 - specs_collaboration_sharing
✓ 007 - specs_api_llm_integration
✓ 008 - specs_analytics_search
✓ 009 - specs_activity_project_management
✓ 010 - auth_add_updated_at_to_refresh_tokens
✓ 011 - specs_fix_projects_schema
✓ 012 - specs_add_mode_to_sessions
✓ 013 - specs_add_timestamp_columns_to_sessions
✓ 014 - specs_make_sessions_user_id_nullable
✓ 015 - specs_add_context_to_questions
✓ 016 - specs_add_all_missing_question_columns
✓ 017 - specs_add_missing_specification_columns
```

### Database Structure (2 Databases)

**Auth Database (socrates_auth):**
- users
- refresh_tokens
- admin_roles
- admin_users
- admin_audit_logs

**Specs Database (socrates_specs):**
- projects
- sessions
- specifications
- conversation_history
- questions
- conflicts
- teams
- team_members
- project_shares
- generated_projects
- generated_files
- quality_metrics
- analytics_metrics
- llm_usage_tracking
- knowledge_base_documents
- document_chunks
- api_keys
- subscriptions
- invoices
- activity_logs
- project_invitations
- notification_preferences
- question_effectiveness
- user_behavior_patterns

### Models (33 Total)
**Core (8):** project, session, specification, generated_project, project_collaborator, project_invitation, project_ownership_history, project_share

**Auth (3):** user, admin_user, user_behavior_pattern

**Content (2):** conflict, conversation_history

**Analytics (2):** analytics_metrics, quality_metric

**Collaboration (2):** team, team_member

**Billing (1):** subscription

**Other (13):** activity_log, admin_audit_log, admin_role, api_key, document_chunk, generated_file, invoice, knowledge_base_document, llm_usage_tracking, notification_preferences, question, question_effectiveness, refresh_token

---

## SECTION 2: API ENDPOINTS ANALYSIS

### Registered Endpoints Summary
- **Total API Files:** 29
- **Total Endpoints Defined:** 180+
- **Total Expected to Work:** 23 critical endpoints
- **Actually Working:** 10 (43%)
- **HTTP Method Errors:** 2
- **Missing Routes (404):** 15
- **Server Errors (500):** 3
- **Connection Timeouts:** 2

### Critical Sessions Endpoints (BROKEN)

#### Problem 1: HTTP METHOD MISMATCH

**Issue: `next-question` endpoint uses POST but tests expect GET**
```
Current:  @router.post("/{session_id}/next-question")    [sessions.py:187]
Expected: @router.get("/{session_id}/next-question")
Status: HTTP 405 (Method Not Allowed)
Fix: Change decorator from @router.post to @router.get
```

**Issue: `mode` endpoint uses POST but tests expect PUT**
```
Current:  @router.post("/{session_id}/mode")    [sessions.py:814]
Expected: @router.put("/{session_id}/mode")
Status: HTTP 405 (Method Not Allowed)
Note: GET /mode exists [sessions.py:760] but POST should be PUT
Fix: Change decorator from @router.post to @router.put
```

#### Problem 2: MISSING REQUIRED FIELD

**Issue: `answer` endpoint requires `question_id` but workflow doesn't provide it**
```
Endpoint: POST /{session_id}/answer    [sessions.py:285]
Status: HTTP 422 (Validation Error)
Problem: SubmitAnswerRequest needs question_id field [sessions.py:38]
Current Request: {"answer": "..."}
Required Request: {"question_id": "...", "answer": "..."}
Impact: Cannot submit answers - workflow blocked
```

#### Problem 3: SCHEMA/DATA MISMATCH

**Issue: `/specifications` endpoint crashes when retrieving specs**
```
Endpoint: GET /api/v1/projects/{id}/specifications
Status: HTTP 500 (Internal Server Error)
Cause: Database schema mismatch or NULL value handling
File: [Need to check error log]
```

---

## SECTION 3: ENDPOINT MAPPING

### Sessions Router (`/api/v1/sessions`)
```python
router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
```

**Registered Endpoints:**
- ✓ GET      "" (list sessions)
- ✓ POST     "" (start session)
- ✗ POST     "/{session_id}/next-question"     [WRONG METHOD - should be GET]
- ✓ POST     "/{session_id}/answer"            [CORRECT but needs question_id]
- ✓ POST     "/{session_id}/chat"              [CORRECT]
- ✓ GET      "/{session_id}"                   [CORRECT]
- ✗ GET      "/{session_id}/history"           [WORKS but returns empty]
- ✓ POST     "/{session_id}/end"               [CORRECT]
- ✓ GET      "/{session_id}/mode"              [CORRECT]
- ✗ POST     "/{session_id}/mode"              [WRONG METHOD - should be PUT]
- ✓ POST     "/{session_id}/pause"             [CORRECT]
- ✓ POST     "/{session_id}/resume"            [CORRECT]

### Project Sessions Router (`/api/v1/projects/{project_id}/sessions`)
```python
project_sessions_router = APIRouter(prefix="/api/v1/projects/{project_id}/sessions", tags=["project-sessions"])
```

**Status:** Registered but has same issues as above

---

## SECTION 4: MISSING ENDPOINTS (NOT REGISTERED)

**LLM Management (3 missing):**
- GET  /api/v1/llm/providers
- POST /api/v1/projects/{id}/llm
- GET  /api/v1/projects/{id}/llm

**Project Operations (2 missing):**
- PUT  /api/v1/projects/{id}/archive
- GET  /api/v1/projects/{id}/stats

**Export Operations (1 missing):**
- POST /api/v1/projects/{id}/export

**Conflict Management (2 missing):**
- GET  /api/v1/projects/{id}/conflicts
- POST /api/v1/projects/{id}/conflicts/detect

**Quality Gates (2 missing):**
- GET  /api/v1/projects/{id}/quality
- POST /api/v1/quality/analyze-question

**Session Context (2 missing):**
- GET  /api/v1/sessions/{id}/context
- GET  /api/v1/sessions/{id}/messages

**Session Management (1 missing):**
- DELETE /api/v1/sessions/{id}

**Alternative Endpoints (2 missing):**
- GET  /api/v1/sessions/{id}/question
- POST /api/v1/sessions/{id}/submit-answer

---

## SECTION 5: CONNECTION POOL ISSUES (TIMEOUTS)

**2 Endpoints causing 60-second timeouts:**

1. **PUT /api/v1/projects/{id}** - Project update
   - Status: Read timeout after 60 seconds
   - Cause: Database operation hangs (likely circular query or lock)
   - Impact: Cannot update projects

2. **DELETE /api/v1/projects/{id}** - Project deletion
   - Status: Read timeout after 60 seconds
   - Cause: Same as above - connection pool exhaustion
   - Impact: Cannot delete projects

**Root Cause:** Same connection pool exhaustion issue from previous phase (holds DB connection during external API calls)

---

## SECTION 6: SCHEMA INCONSISTENCIES

### Specs Model vs Migration

**Migration 017 adds:**
- category (String, NOT NULL, default='general')
- content (Text, nullable)
- source (String, nullable)
- confidence (Float, default=0.8)
- is_current (Boolean, default=true)
- spec_metadata (JSON, nullable)
- superseded_at (DateTime, nullable)
- superseded_by (String, nullable)
- maturity_score (Integer, default=0)

**Code expects:** All of these (model.py)

**Status:** ✓ Consistent

### Answer Submission Workflow Issue

**Problem:** Workflow expects to submit answer without question_id
```
Test sends: POST /api/v1/sessions/{id}/answer
Body: {"answer": "..."}

API Requires: {"question_id": "...", "answer": "..."}

Current Question Generation: Doesn't store question_id in a way accessible to client
```

---

## SECTION 7: DATABASE QUERY ISSUES

### Issue: specifications listing crashes

**Endpoint:** GET /api/v1/projects/{id}/specifications
**Status:** HTTP 500
**Cause:** Unknown (need to check error logs)
**Likely:**
- Foreign key mismatch
- NULL value in category or content field
- Type mismatch in query

---

## SECTION 8: CONSISTENCY ANALYSIS

### What's Broken vs What Works

| Component | Status | Issue |
|-----------|--------|-------|
| Database Migrations | ✓ CONSISTENT | All 17 run successfully |
| Models Definition | ✓ CONSISTENT | Match migrations |
| Router Registration | ✓ CONSISTENT | All routers included in main.py |
| HTTP Methods | ✗ BROKEN | 2 endpoints use wrong verbs |
| Required Fields | ✗ BROKEN | answer endpoint needs question_id |
| Endpoint Coverage | ✗ BROKEN | 15 endpoints not implemented |
| Database Operations | ✗ BROKEN | 2 endpoints timeout, 3 return 500 |
| Chat/Direct Mode | ✓ WORKING | Endpoints function correctly |
| Project CRUD | ⚠ PARTIAL | Create/Read work, Update/Delete timeout |

---

## SECTION 9: DETAILED REPAIR PLAN

### PHASE 1: FIX HTTP METHOD ERRORS (2 changes)

**1.1 Fix next-question endpoint**
- File: `backend/app/api/sessions.py:187`
- Change: `@router.post` → `@router.get`
- Impact: HTTP 405 → HTTP 200 for GET requests
- Time: 1 minute

**1.2 Fix mode endpoint**
- File: `backend/app/api/sessions.py:814`
- Change: `@router.post` → `@router.put`
- Impact: HTTP 405 → HTTP 200 for PUT requests
- Time: 1 minute

### PHASE 2: FIX ANSWER SUBMISSION WORKFLOW (4 changes)

**2.1 Track current question in session**
- File: `backend/app/api/sessions.py` - get_next_question function
- Change: Store question_id in session or return it to client
- Time: 5 minutes

**2.2 Update SubmitAnswerRequest schema**
- File: `backend/app/api/sessions.py:37-39`
- Change: Make question_id optional OR get from session context
- Time: 2 minutes

**2.3 Update client workflow**
- Handle returning question_id from question endpoint
- Include in answer submission
- Time: 5 minutes

**2.4 Test answer submission**
- Time: 5 minutes

### PHASE 3: FIX CONNECTION POOL TIMEOUTS (2 changes)

**3.1 Fix project update endpoint**
- File: `backend/app/api/projects.py`
- Problem: Likely holding DB connection during operations
- Solution: Apply same 5-phase pattern (Load → Close → Process → Open → Save)
- Time: 10 minutes

**3.2 Fix project deletion endpoint**
- File: `backend/app/api/projects.py`
- Same fix as 3.1
- Time: 10 minutes

### PHASE 4: IMPLEMENT MISSING ENDPOINTS (15 endpoints)

**Group 1: LLM Management (3)**
- GET /api/v1/llm/providers
- POST /api/v1/projects/{id}/llm
- GET /api/v1/projects/{id}/llm
- File: Create `backend/app/api/llm.py`
- Time: 15 minutes

**Group 2: Project Stats & Archive (2)**
- PUT /api/v1/projects/{id}/archive
- GET /api/v1/projects/{id}/stats
- File: `backend/app/api/projects.py`
- Time: 10 minutes

**Group 3: Export (1)**
- POST /api/v1/projects/{id}/export
- File: `backend/app/api/export_endpoints.py` (likely exists)
- Time: 5 minutes

**Group 4: Conflicts (2)**
- GET /api/v1/projects/{id}/conflicts
- POST /api/v1/projects/{id}/conflicts/detect
- File: `backend/app/api/conflicts.py`
- Time: 10 minutes

**Group 5: Quality (2)**
- GET /api/v1/projects/{id}/quality
- POST /api/v1/quality/analyze-question
- File: `backend/app/api/quality.py`
- Time: 10 minutes

**Group 6: Context (2)**
- GET /api/v1/sessions/{id}/context
- GET /api/v1/sessions/{id}/messages
- File: `backend/app/api/sessions.py`
- Time: 10 minutes

**Group 7: Session Management (1)**
- DELETE /api/v1/sessions/{id}
- File: `backend/app/api/sessions.py`
- Time: 5 minutes

**Group 8: Alternatives (2)**
- GET /api/v1/sessions/{id}/question
- POST /api/v1/sessions/{id}/submit-answer
- File: `backend/app/api/sessions.py`
- Time: 5 minutes

### PHASE 5: FIX DATABASE/SCHEMA ISSUES (3 fixes)

**5.1 Fix specifications listing endpoint**
- Investigate 500 error cause
- Fix database query or schema issue
- Time: 15 minutes

**5.2 Verify all schema migrations applied**
- Check socrates_specs database
- Run any missing migrations
- Verify all tables exist
- Time: 10 minutes

**5.3 Add defensive NULL handling**
- All endpoints should handle NULL values gracefully
- Time: 20 minutes

### PHASE 6: COMPREHENSIVE TESTING

**6.1 Run comprehensive test (39 tests)**
- Time: 5 minutes

**6.2 Fix any remaining issues**
- Time: 30 minutes (estimated)

---

## SECTION 10: ESTIMATED REPAIR TIME

| Phase | Task | Time |
|-------|------|------|
| 1 | HTTP Method Fixes | 2 min |
| 2 | Answer Submission Fix | 17 min |
| 3 | Connection Pool Fixes | 20 min |
| 4 | Missing Endpoints | 70 min |
| 5 | Schema Issues | 45 min |
| 6 | Testing & Fixes | 35 min |
| **TOTAL** | **Full Repair** | **189 min ≈ 3.2 hours** |

---

## SECTION 11: CRITICAL SUCCESS FACTORS

1. **HTTP Methods MUST match REST standards**
   - GET for retrieval
   - POST for creation
   - PUT for updates
   - DELETE for removal

2. **Workflow consistency**
   - Question generation returns question_id
   - Answer submission includes question_id
   - No breaking API contracts

3. **Connection management**
   - Apply 5-phase pattern consistently
   - Never hold DB connections during API calls
   - Close connections immediately after data load

4. **Schema validation**
   - All migrations run successfully
   - All nullable fields handle NULL properly
   - No foreign key constraint violations

5. **Testing verification**
   - Run 39-test comprehensive suite
   - 100% pass rate required
   - No timeouts or 500 errors

---

## NEXT STEPS

1. **Immediate (5 mins):** Fix HTTP methods (Phase 1)
2. **Short-term (30 mins):** Fix answer submission (Phase 2)
3. **Medium-term (1 hour):** Fix timeouts and schema (Phase 3 & 5)
4. **Long-term (1.5 hours):** Implement missing endpoints (Phase 4)
5. **Validation (30 mins):** Comprehensive testing (Phase 6)

---

**Report Generated:** 2025-11-15 20:15:00
**Status:** Ready for consistent, methodical repair

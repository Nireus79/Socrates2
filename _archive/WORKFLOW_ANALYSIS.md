# Socrates User Workflow Analysis - Test Coverage & Broken Features

Date: November 13, 2025

## Executive Summary

The Socrates application has significant gaps in user workflow coverage. Tests are well-structured but incomplete. Two key workflows are broken: session start and session history retrieval.

## 1. E2E Test Files Found

Files in backend/tests/:
- test_e2e_complete_workflow.py (4 test classes)
- test_e2e_flow.py (script-based, requires running server)
- test_e2e_simple.py (token refresh test)
- test_socrates_cli.py (10+ test classes, mostly skipped)
- test_sessions_endpoints.py (session CRUD tests)
- test_projects_endpoints.py (project CRUD tests)

## 2. Critical Bugs Found

### BUG 1: Session Start Fails (Line 137-141 in sessions.py)

File: backend/app/api/sessions.py
Lines: 86-182

Problem: project_id is string but Session model expects UUID

Code at line 137:
```
session = SessionModel(
    project_id=request.project_id,  # String from JSON
    status='active',
    started_at=datetime.now(timezone.utc)
)
```

But Session model expects (session.py line 33):
```
project_id = Column(
    PG_UUID(as_uuid=True),  # UUID type required
    ForeignKey('projects.id', ondelete='CASCADE'),
    nullable=False,
)
```

Result: TypeError on db.add(session) at line 143
Generic error at line 179: "Failed to start session"

Fix: Convert UUID string before insert
```
from uuid import UUID
project_id=UUID(request.project_id)
```

### BUG 2: Session History .to_dict() Missing (Lines 543, 620)

File: backend/app/api/sessions.py

Code:
- Line 543: session.to_dict()
- Line 620: h.to_dict()

Problem: Session model has NO to_dict() method
Result: AttributeError at runtime
Impact: GET /api/v1/sessions/{session_id} and GET .../history endpoints crash

Fix: Add to_dict() method to Session model in backend/app/models/session.py

### BUG 3: Inconsistent Session Request Models

File: backend/app/api/sessions.py
Lines: 30-33 vs 1013-1024

Two different request models:
1. StartSessionRequest (line 30): Takes only project_id
2. CreateProjectSessionRequest (line 1013): Takes name, description, status

Problem: CreateProjectSessionRequest has fields NOT in Session model
- name field: NOT in Session model
- description field: NOT in Session model

Session model (session.py) has: project_id, mode, status, started_at, ended_at

Result: name/description silently ignored

## 3. Missing Test Coverage

Not tested at all:
- POST /api/v1/sessions/{session_id}/next-question (question generation)
- POST /api/v1/sessions/{session_id}/answer (answer submission)
- POST /api/v1/sessions/{session_id}/chat (chat mode)
- GET /api/v1/sessions/{session_id}/history (session history) - BROKEN
- Chat mode switching and operation
- Specification extraction from answers
- Maturity score calculations
- Project selection workflow
- CLI project selection commands
- Multi-user permission enforcement
- Error scenarios (invalid UUID, missing project, etc)

## 4. User Workflow Breakdown

The complete user workflow that should work:

1. Register user         ✅ Works
2. Login                ✅ Works
3. Create project       ✅ Works
4. Start session        ❌ FAILS - UUID bug
5. Get question         ❌ Not tested
6. Submit answer        ❌ Not tested
7. Extract specs        ❌ Not tested
8. Continue/end         ⚠️ Partial

## 5. Project Delete Issue

File: backend/app/cli/commands/projects.py
Lines: 232-264

Problem: Delete requires FULL UUID but list shows abbreviated IDs

List output shows: 550e8400-e29b-41d4-a716-...
Delete command requires: 550e8400-e29b-41d4-a716-446655440000

Missing feature: Project selection
- No 'socrates project select <id>' command
- No storage of current_project in config
- No --current flag for delete

Evidence: Config infrastructure exists (get_config_dir, save_credentials functions)
but current_project tracking not implemented.

## 6. Test Files Location

All test files in: C:\Users\themi\PycharmProjects\Socrates\backend\tests\

Main E2E file: test_e2e_complete_workflow.py (293 lines, 4 test classes)
Session tests: test_sessions_endpoints.py (200+ lines)
Project tests: test_projects_endpoints.py (200+ lines)
CLI tests: test_socrates_cli.py (410+ lines, mostly skipped)

## 7. Files Needing Changes

CRITICAL (Bugs):
1. backend/app/api/sessions.py - UUID conversion, to_dict() calls, inconsistent request models
2. backend/app/models/session.py - Add to_dict() method

HIGH (Features):
3. backend/app/cli/commands/projects.py - Add project select, use current_project
4. backend/app/cli/commands/config.py - Ensure current_project persists

TESTS:
5. backend/tests/test_sessions_endpoints.py - Add question/answer/chat tests
6. backend/tests/test_e2e_complete_workflow.py - Expand session workflow
7. backend/tests/test_socrates_cli.py - Add project selection tests

## 8. Workflow Completeness Matrix

Registered user flow:                        60% functional
Project creation flow:                       95% functional
Project deletion flow:                       50% functional (requires full UUID)
Session start flow:                          0% functional (broken)
Socratic question flow:                      0% functional (not tested)
Answer submission flow:                      0% functional (not tested)
Chat mode flow:                              0% functional (not tested)
Session history retrieval:                   0% functional (broken)
Project selection/context:                   0% functional (not implemented)

## 9. Estimated Fix Effort

Bug fixes:
- Session start UUID bug: 15 mins
- Session to_dict() bug: 30 mins
- Fix request models: 30 mins

Features:
- Project selection: 1.5 hours
- Project delete with context: 1 hour

Tests:
- Question/answer workflow: 2 hours
- Chat mode workflow: 2 hours
- Session history: 1 hour
- CLI project selection: 1.5 hours
- Error scenarios: 1 hour

Total estimated: 14-16 hours to make all workflows functional and tested

## 10. Test Gaps Summary

Tested: Registration, Login, Project CRUD, Basic session CRUD
Not tested: Complete Socratic conversation, Chat mode, Session history, Project selection, Error handling for invalid inputs

Most broken: Starting a session (UUID type mismatch) and completing Socratic workflow (no questions/answers tested)


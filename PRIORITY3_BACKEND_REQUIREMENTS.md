# Priority 3 - Backend Requirements & Gaps

**Date:** November 8, 2025
**Status:** Analysis of backend readiness for Priority 3 CLI commands

---

## Backend Endpoints: Status Check

### Implemented Endpoints ✓

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/api/v1/search` | GET | ✓ Implemented | search.py |
| `/api/v1/insights/{project_id}` | GET | ✓ Implemented | insights.py |
| `/api/v1/templates` | GET | ✓ Implemented | templates.py |
| `/api/v1/templates/{template_id}` | GET | ✓ Implemented | templates.py |
| `/api/v1/templates/{template_id}/apply` | POST | ✓ Implemented | templates.py |
| `/api/v1/sessions/{session_id}` | GET | ✓ Implemented | sessions.py |
| `/api/v1/sessions/{session_id}/history` | GET | ✓ Implemented | sessions.py |
| `/api/v1/sessions/{session_id}/next-question` | POST | ✓ Implemented | sessions.py |
| `/api/v1/sessions/{session_id}/answer` | POST | ✓ Implemented | sessions.py |
| `/api/v1/sessions/{session_id}/end` | POST | ✓ Implemented | sessions.py |

---

## Potential Gaps

### Gap 1: Session Resume Endpoint

**Current Status:** Missing

**Required For:** `/resume <session_id>` command

**What's Missing:**
- Endpoint to change session status from 'paused'/'completed' back to 'active'
- Currently no endpoint to update session status

**Session Model Supports:**
- status: active, paused, completed ✓
- started_at, ended_at timestamps ✓

**Solutions:**

**Option A (Recommended): Add Resume Endpoint**
```python
@router.post("/{session_id}/resume")
def resume_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """Resume a paused or completed session"""
    # Get session
    session = db.query(Session).where(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404)
    
    # Verify ownership via project
    project = db.query(Project).where(Project.id == session.project_id).first()
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403)
    
    # Update status
    session.status = "active"
    db.commit()
    
    return {
        "success": True,
        "session_id": str(session.id),
        "message": "Session resumed"
    }
```

**Implementation:** ~20 lines in `/backend/app/api/sessions.py`

**Option B (Alternative): Update via existing endpoint**
- Could add PUT endpoint to update session fields
- More generic but less semantic

---

### Gap 2: List Recent Sessions for User

**Current Status:** Partially implemented

**Required For:** `/resume` (when no session_id provided)

**What Exists:**
- `GET /api/v1/projects/{project_id}/sessions` - Lists sessions for a project
- No endpoint to list all user's recent sessions across projects

**Potential Solution:**
```python
@router.get("")
def list_user_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """List all sessions for current user across all projects"""
    # Query sessions for projects owned by user
    query = db.query(Session).join(Project).where(
        Project.user_id == current_user.id
    )
    
    if status:
        query = query.where(Session.status == status)
    
    total = query.count()
    sessions = query.order_by(Session.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "sessions": [...],
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

**Alternative for CLI:** Client-side implementation
- Store recent session IDs in config
- Show user's 5 most recent sessions from memory
- No backend endpoint needed

---

## Recommendations

### Must Implement (Blocking)
None - All required endpoints exist

### Should Implement (Nice to Have)
1. `POST /api/v1/sessions/{session_id}/resume` - 20 lines
   - Makes `/resume <id>` command more robust
   - Atomic operation on backend

2. `GET /api/v1/sessions` (user sessions) - 30 lines
   - Makes `/resume` (no args) better UX
   - Shows recent sessions across projects

### Could Implement (Optional)
- Filter specifications by project/category
  - Could add dedicated endpoint or use client-side filtering
  - Current `/search` works, can filter client-side with `/filter`

---

## CLI Implementation Without New Endpoints

### `/resume` Can Work Without Resume Endpoint
```python
# Option 1: No status update needed
# Just load session and continue with next-question

# Option 2: Update config to track session state
# CLI manages "paused" vs "active" separately

# Option 3: Always treat as resumable
# Don't change status, just continue with next question
```

### Client-Side Session Resume Logic
```python
def cmd_resume(self, args: List[str]):
    if not args:
        # Show recent sessions from config
        recent = self.config.get("recent_sessions", [])
        # Display and let user select
    
    session_id = args[0]
    result = self.api.get_session(session_id)
    
    # Load session into memory
    self.current_session = result["session"]
    self.current_project = {"id": result["session"]["project_id"]}
    
    # Don't update status - just resume naturally
    # Next /session message will get next-question
```

---

## Impact on Priority 3 Implementation

### Can Implement All 6 Commands Without Backend Changes
- ✓ `/insights` - Endpoint ready
- ✓ `/wizard` - Endpoints ready
- ✓ `/search` - Endpoint ready
- ✓ `/filter` - Can use search or client-side
- ✓ `/resume` - Endpoint ready (get_session)
- ✓ `/status` - No endpoint needed

### Recommended Backend Enhancements (Post Priority 3)
1. Add `POST /api/v1/sessions/{session_id}/resume` for robustness
2. Add `GET /api/v1/sessions` for better UX

---

## Implementation Timeline

### Phase 1: CLI Commands (No Backend Changes)
**Time:** 6-8 hours
- Implement all 6 commands
- Use existing backend endpoints
- Client-side filtering where needed

### Phase 2: Backend Enhancement (Optional)
**Time:** 1-2 hours
- Add resume endpoint (20 lines)
- Add list sessions endpoint (30 lines)

---

## Database Model Verification

### Models Required - All Present ✓

```
Project
├─ id, name, creator_id, owner_id
├─ current_phase (discovery|analysis|design|implementation)
├─ status (active|archived|completed)
├─ maturity_score (0-100)
└─ Indexes: creator_id, owner_id, user_id, status, phase, maturity

Session
├─ id, project_id
├─ mode (socratic|direct_chat)
├─ status (active|paused|completed) ✓ Supports pause/resume
├─ started_at, ended_at
└─ Indexes: project_id, status, mode

Specification
├─ id, project_id, session_id
├─ category (goals|requirements|...)
├─ content (text)
├─ confidence (0.00-1.00)
├─ source (user_input|extracted|inferred)
├─ is_current (boolean)
└─ Indexes: project_id, category, is_current, created_at

Question
├─ id, project_id, session_id
├─ text (content)
├─ category (goals|requirements|...)
├─ quality_score (0.00-1.00)
└─ Indexes: project_id, session_id, category, created_at
```

**All required fields and indexes present** ✓

---

## Summary

**Backend Status:** Ready for Priority 3 implementation

**No blocking issues** - All required endpoints are implemented

**Optional enhancements** - Could improve UX but not required

**Recommendation:** Proceed with CLI implementation as planned

---

## Verification Commands

```bash
# Check if endpoints are registered in main.py
grep -n "search\|insights\|templates" /home/user/Socrates2/backend/app/main.py

# Verify models have required fields
python -c "from backend.app.models import Project, Session, Specification, Question; print('OK')"

# List all session endpoints
grep "@router" /home/user/Socrates2/backend/app/api/sessions.py
```


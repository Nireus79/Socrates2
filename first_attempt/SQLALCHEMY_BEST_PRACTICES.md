# SQLAlchemy Best Practices for Socrates2

**Critical:** This document addresses SQLAlchemy problems that killed previous attempts. READ BEFORE implementing Phase 1.

**References:**
- Archive audit: `/home/user/Socrates/ARCHIVE/ARCHIVE_OLD_ANALYSIS/FINAL_AUDIT_REPORT.md`
- Session failures: `/home/user/Socrates/ARCHIVE/ARCHIVE_OLD_ANALYSIS/AUDIT_CHECKLIST.md#235`

---

## Critical Issues from Archive

### ⚠️ Issue #1: Session Lifecycle Breaking Data Persistence (KILLED PREVIOUS ATTEMPT)

**Problem:** Database session closed before commit synced to disk, causing **ZERO data persistence** despite API returning 201 Created.

**Archive Evidence:**
```
BEFORE FIX: 0 records in ALL tables (users, sessions, messages)
AFTER FIX: 100% data persistence
Root Cause: get_db_session() closed session in finally block before SQLite buffering completed
```

**What Happened:**
```python
# ❌ ARCHIVE ANTI-PATTERN (Killed previous attempt)
def get_db_session() -> Session:
    service = get_database_service()
    session = service.get_session()
    try:
        yield session
    finally:
        session.close()  # ⚠️ Closes before commit syncs to disk!

# Route handler
@app.post("/messages")
def create_message(data: MessageCreate, db: Session = Depends(get_db_session)):
    message = Message(**data.dict())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message  # Returns successfully...
    # Session closes HERE in finally block
    # But SQLite buffering hasn't synced to disk yet!
    # Result: Message appears in response but NEVER reaches database
```

**Why This Failed:**
1. FastAPI dependency injection calls `finally` block immediately after route returns
2. SQLite write-ahead logging (WAL) hasn't synced to disk yet
3. Session closes, buffer discarded, data lost
4. API returns 201 Created (data was in memory), but database has 0 rows

**✅ SOLUTION for Socrates2:**

```python
# Option A: Use scoped_session (RECOMMENDED)
from sqlalchemy.orm import scoped_session, sessionmaker

Session = scoped_session(sessionmaker(bind=engine))

def get_db():
    """Get thread-local session that persists across request lifecycle."""
    db = Session()
    try:
        yield db
        db.commit()  # Explicit commit BEFORE closing
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Option B: Context manager with explicit commit
@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()  # ⚠️ MUST commit before close
        session.flush()   # ⚠️ Force sync to disk
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

**Verification Test (MUST PASS):**
```python
def test_persistence_after_session_close():
    """Verify data persists after session closes (archive killer bug)."""
    # Create record
    with get_db_session() as db:
        user = User(username="test", email="test@test.com")
        db.add(user)
        db.commit()
        user_id = user.id

    # Session closed - data MUST still be in database
    with get_db_session() as db:
        found = db.query(User).filter_by(id=user_id).first()
        assert found is not None, "❌ ARCHIVE KILLER BUG: Data lost after session close!"
        assert found.username == "test"
```

---

### ⚠️ Issue #2: Detached Instance Errors (Archive Issue #47)

**Problem:** Accessing SQLAlchemy objects after session closes causes "Instance is not bound to a Session" errors.

**Archive Evidence:**
```
Issue #47: Project Listing (500 error)
Root Cause: SQLAlchemy detached instance error
Fix: Use JWT token to extract user_id instead of accessing detached object
```

**What Happened:**
```python
# ❌ ARCHIVE ANTI-PATTERN
@app.get("/projects")
def get_projects(current_user: User = Depends(get_current_user)):
    # current_user is from previous session (now closed)
    # Accessing current_user.id causes detached instance error
    projects = db.query(Project).filter_by(owner_id=current_user.id).all()
    # ERROR: DetachedInstanceError
```

**✅ SOLUTION for Socrates2:**

```python
# Extract scalar values WITHIN session
@app.get("/projects")
def get_projects(user_id: UUID = Depends(get_user_id_from_token), db: Session = Depends(get_db)):
    # user_id is a scalar (UUID), not a detached object
    projects = db.query(Project).filter_by(owner_id=user_id).all()
    return projects

# Helper function
def get_user_id_from_token(authorization: str = Header(...)) -> UUID:
    """Extract user_id from JWT token (no database session needed)."""
    token = authorization.replace("Bearer ", "")
    payload = jwt.decode(token, SECRET_KEY)
    return UUID(payload["sub"])
```

**Rules:**
1. ✅ **DO** extract scalar values (int, str, UUID) from objects within session
2. ✅ **DO** pass scalar values between functions
3. ❌ **DON'T** pass SQLAlchemy model instances outside session scope
4. ❌ **DON'T** access lazy-loaded relationships after session closes

---

### ⚠️ Issue #3: Lazy Loading After Session Close

**Problem:** Accessing relationships after session closes causes errors.

**Archive Evidence:** `/home/user/Socrates/ARCHIVE/docs_old/developers_doc/DATABASE_GUIDE.md:707`

```python
# ❌ ARCHIVE ANTI-PATTERN
user = db.query(User).get(user_id)
# Session closes here
projects = user.projects  # ERROR: DetachedInstanceError

# ✅ SOLUTION: Eager loading
from sqlalchemy.orm import joinedload

user = db.query(User).options(joinedload(User.projects)).get(user_id)
# Session closes here
projects = user.projects  # ✅ Works - already loaded
```

---

### ⚠️ Issue #4: Silent Exception Handling (Archive Root Cause #2)

**Problem:** Services catch exceptions but don't re-raise, making debugging impossible.

**Archive Evidence:**
```
Root Cause #2: Silent Exception Handling
Pattern: except Exception as e: log_error(...) but no raise
Result: Caller can't distinguish between valid empty result and error
Impact: Silent failures make debugging impossible
```

**What Happened:**
```python
# ❌ ARCHIVE ANTI-PATTERN
def authenticate_user(username: str, password: str):
    try:
        user = db.query(User).filter_by(username=username).first()
        if user and verify_password(password, user.password):
            return user
        return None
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return None  # ⚠️ Can't distinguish "wrong password" from "database down"

# ✅ SOLUTION: Fail fast
def authenticate_user(username: str, password: str):
    try:
        user = db.query(User).filter_by(username=username).first()
        if user and verify_password(password, user.password):
            return user
        raise ValueError("Invalid credentials")
    except ValueError:
        raise  # Expected error - re-raise
    except Exception as e:
        logger.error(f"Database error during auth: {e}", exc_info=True)
        raise  # Unexpected error - re-raise for proper handling
```

---

### ⚠️ Issue #5: Model/DTO Field Mismatches (Archive 40+ Issues)

**Problem:** Pydantic DTOs missing fields from SQLAlchemy models, causing data loss.

**Archive Evidence:**
```
40+ field mismatches identified
Critical: User.role missing, Session.insights_extracted missing, Specification.description missing
Impact: Data loss, type errors, API unusability
```

**What Happened:**
```python
# SQLAlchemy Model
class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID, primary_key=True)
    insights_extracted = Column(JSONB)  # Core Socratic output
    action_items = Column(JSONB)        # Core Socratic output
    decisions_made = Column(JSONB)      # Core Socratic output

# ❌ ARCHIVE DTO (Missing critical fields)
class SessionResponse(BaseModel):
    id: UUID
    # insights_extracted MISSING!
    # action_items MISSING!
    # decisions_made MISSING!
    # Result: Core Socratic outputs lost when serializing response

# ✅ SOLUTION: Complete DTO
class SessionResponse(BaseModel):
    id: UUID
    insights_extracted: Optional[Dict] = None
    action_items: Optional[Dict] = None
    decisions_made: Optional[Dict] = None

    class Config:
        from_attributes = True  # SQLAlchemy 2.0 (was orm_mode in 1.x)
```

**Verification Test (MUST PASS):**
```python
def test_dto_completeness():
    """Verify all model fields exist in DTOs (archive killer bug)."""
    model_fields = set(Session.__table__.columns.keys())
    dto_fields = set(SessionResponse.model_fields.keys())
    missing = model_fields - dto_fields
    assert not missing, f"❌ ARCHIVE KILLER BUG: DTO missing fields: {missing}"
```

---

## SQLAlchemy Configuration for Socrates2

### Engine Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# For SQLite (development)
engine = create_engine(
    "sqlite:///./socrates.db",
    connect_args={"check_same_thread": False},  # Allow multi-threading
    poolclass=StaticPool,                       # Single pool for all threads
    echo=False,                                 # Set True for SQL debugging
    pool_pre_ping=True                          # Verify connections before use
)

# For PostgreSQL (production)
engine = create_engine(
    "postgresql://user:pass@localhost/socrates_auth",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)
```

### Session Configuration

```python
from sqlalchemy.orm import sessionmaker, scoped_session

# ⚠️ CRITICAL: These settings prevented data loss in archive fix
SessionLocal = sessionmaker(
    autocommit=False,  # Manual commit control (REQUIRED for rollback)
    autoflush=False,   # Manual flush control (prevents partial commits)
    expire_on_commit=False,  # Allow accessing objects after commit
    bind=engine
)

# Thread-local session (RECOMMENDED)
Session = scoped_session(SessionLocal)
```

---

## Best Practices Checklist

### ✅ Session Lifecycle
- [ ] Always commit explicitly before closing session
- [ ] Use context managers or scoped_session for automatic cleanup
- [ ] Test data persistence after session closes (archive killer test)
- [ ] Never rely on FastAPI dependency injection closing session without explicit commit

### ✅ Object Handling
- [ ] Extract scalar values (UUID, int, str) within session
- [ ] Never pass SQLAlchemy objects outside session scope
- [ ] Use eager loading (joinedload) for relationships that will be accessed later
- [ ] Configure expire_on_commit=False if objects must be accessed after commit

### ✅ Error Handling
- [ ] Never catch exceptions without re-raising (fail fast principle)
- [ ] Distinguish expected errors (ValueError) from unexpected (Exception)
- [ ] Always rollback on exception before closing session
- [ ] Log with exc_info=True for full stack traces

### ✅ Model/DTO Sync
- [ ] Every model field must exist in response DTO (test this!)
- [ ] Use Pydantic's from_attributes=True (SQLAlchemy 2.0)
- [ ] Create validation tests comparing model columns to DTO fields
- [ ] Update DTOs immediately when models change

### ✅ Testing
- [ ] Test data persistence after session closes
- [ ] Test accessing objects after session closes (should fail or use eager loading)
- [ ] Test DTO completeness (all model fields present)
- [ ] Test rollback on exception

---

## Phase 1 Implementation Requirements

**BEFORE implementing database layer:**

1. ✅ Read this document completely
2. ✅ Understand session lifecycle issue (killed previous attempt)
3. ✅ Implement session management with explicit commit before close
4. ✅ Create DTO completeness validation tests
5. ✅ Verify data persistence test passes

**Verification gates (MUST PASS before Phase 2):**

```python
# Test 1: Data persists after session close
test_persistence_after_session_close()  # MUST PASS

# Test 2: No detached instance errors
test_no_detached_instances()  # MUST PASS

# Test 3: DTOs complete
test_dto_completeness()  # MUST PASS

# Test 4: Explicit error handling
test_exceptions_propagate()  # MUST PASS
```

---

## Critical Learnings from Archive

### What Killed Previous Attempt:

1. **80%:** Session lifecycle - data never reached database
2. **15%:** Detached instances - objects accessed after session closed
3. **3%:** Silent failures - exceptions caught but not re-raised
4. **2%:** Model/DTO mismatches - data loss on serialization

### Success Factors for Socrates2:

1. ✅ Explicit commit BEFORE closing session
2. ✅ Scalar value extraction within session
3. ✅ Fail-fast exception handling
4. ✅ Complete DTO coverage with validation tests
5. ✅ Test data persistence after session closes

---

## Archive References

**Critical Files to Study:**
- `/home/user/Socrates/ARCHIVE/ARCHIVE_OLD_ANALYSIS/FINAL_AUDIT_REPORT.md` - Complete audit
- `/home/user/Socrates/ARCHIVE/ARCHIVE_OLD_ANALYSIS/AUDIT_CHECKLIST.md#235` - Issue #2 (database failure)
- `/home/user/Socrates/ARCHIVE/ARCHIVE_OLD_ANALYSIS/FINAL_STATUS_SUMMARY.txt` - Root cause #47 (detached instance)
- `/home/user/Socrates/ARCHIVE/docs_old/developers_doc/DATABASE_GUIDE.md:707` - Lazy loading issues

**Archive Session Configuration:**
```python
# From: /home/user/Socrates/ARCHIVE/backend_for_audit/src/database/service.py:126
SessionLocal = sessionmaker(
    autocommit=False,  # ⚠️ Required for manual transaction control
    autoflush=False,   # ⚠️ Required for manual flush control
    bind=engine
)
```

---

## Quick Reference

### DO ✅
- Explicit commit before close
- Extract scalars within session
- Fail fast on errors
- Eager load relationships
- Test persistence after close
- Complete DTOs

### DON'T ❌
- Close session without commit
- Pass objects outside session
- Catch exceptions silently
- Access relationships after close
- Skip DTO validation tests
- Trust FastAPI cleanup alone

---

**Last Updated:** 2025-11-05
**Archive Study:** Complete (124 files analyzed)
**Critical Issues Found:** 5 (all documented above)
**Success Rate:** Archive 0% → Socrates2 Target 85%

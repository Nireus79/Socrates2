# CRITICAL LESSONS LEARNED - Phases 1-4

**Document Purpose:** Record all mistakes made in Phases 1-4 to prevent repetition in Phases 5-10.

---

## ⚠️ CRITICAL MISTAKE #1: Missing Database-Specific Checks in Migrations

**What Happened:**
- Created migrations 005, 006, 007 for `socrates_specs` database tables
- Did NOT add checks to ensure they only run on the correct database
- Alembic tried to run these migrations on BOTH `socrates_auth` and `socrates_specs`
- This caused errors when running migrations

**The Fix:**
```python
import os

def _should_run():
    """Only run this migration for socrates_specs database"""
    db_url = os.getenv("DATABASE_URL", "")
    return "socrates_specs" in db_url

def upgrade():
    if not _should_run():
        return
    # ... rest of migration

def downgrade():
    if not _should_run():
        return
    # ... rest of downgrade
```

**Root Cause:**
- Two-database architecture requires explicit database routing
- Migrations 001-002 go to `socrates_auth` (users, refresh_tokens)
- Migrations 003+ go to `socrates_specs` (everything else)
- Without checks, Alembic doesn't know which database each migration belongs to

**For Phases 5-10:**
```
✅ ALWAYS add _should_run() check to migrations
✅ Check if "socrates_auth" or "socrates_specs" is in DATABASE_URL
✅ Return early if migration shouldn't run on current database
✅ Add check to BOTH upgrade() and downgrade()
```

---

## ⚠️ CRITICAL MISTAKE #2: Missing `updated_at` Column in Migrations

**What Happened:**
- `Specification` model inherits from `BaseModel`
- `BaseModel` has `created_at` and `updated_at` columns
- Migration 006 created `created_at` but forgot `updated_at`
- SQLAlchemy expected `updated_at` to exist → Runtime error

**The Fix:**
Added to migration:
```python
sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
```

**Root Cause:**
- When model inherits from BaseModel, ALL BaseModel columns must be in migration
- I added `created_at` but forgot `updated_at`

**For Phases 5-10:**
```
✅ ALWAYS check BaseModel columns: id, created_at, updated_at
✅ ALL three must be in migration if model inherits from BaseModel
✅ Double-check migration matches model exactly
✅ Use server_default=sa.text('NOW()') for timestamp columns
```

---

## ⚠️ CRITICAL MISTAKE #3: SQLAlchemy Reserved Word `metadata`

**What Happened:**
- Named columns `metadata` in Specification and ConversationHistory models
- SQLAlchemy reserves `metadata` for table metadata
- Error: `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved`

**The Fix:**
```python
# ❌ WRONG
metadata = Column(JSONB, nullable=True)

# ✅ CORRECT
spec_metadata = Column(JSONB, nullable=True)  # For Specification
message_metadata = Column(JSONB, nullable=True)  # For ConversationHistory
```

**Root Cause:**
- SQLAlchemy uses `metadata` internally for table definitions
- Cannot use it as a column name

**SQLAlchemy Reserved Words to AVOID:**
```
❌ metadata
❌ query
❌ session  (for column names - OK for model/table names)
❌ registry
❌ mapper
```

**For Phases 5-10:**
```
✅ NEVER name a column 'metadata'
✅ Use specific names: spec_metadata, message_metadata, config_metadata, etc.
✅ Check SQLAlchemy reserved words list before naming columns
```

---

## ⚠️ CRITICAL MISTAKE #4: Wrong Pytest Fixture Names

**What Happened:**
- Used `db_auth` and `db_specs` in test functions
- Actual fixtures in `conftest.py` are named `auth_session` and `specs_session`
- Error: `fixture 'db_auth' not found`

**The Fix:**
```python
# ❌ WRONG
def test_something(db_auth, db_specs):
    user = db_auth.query(User).first()

# ✅ CORRECT
def test_something(auth_session, specs_session):
    user = auth_session.query(User).first()
```

**Root Cause:**
- Didn't check conftest.py to see actual fixture names
- Assumed fixture names instead of verifying

**For Phases 5-10:**
```
✅ ALWAYS check conftest.py for exact fixture names
✅ Use auth_session for socrates_auth database tests
✅ Use specs_session for socrates_specs database tests
✅ Use db_auth_session and db_specs_session for ServiceContainer tests
```

---

## ⚠️ CRITICAL MISTAKE #5: Incorrect Mock Decorators

**What Happened:**
- Added `@patch` decorators to patch agent's `services` attribute
- `services` is an instance attribute (set in `__init__`), not class attribute
- Mock didn't work, and was unnecessary anyway

**The Fix:**
```python
# ❌ WRONG
@patch('app.agents.socratic.SocraticCounselorAgent.services')
def test_something(mock_services, socratic_agent):
    # services is instance attribute, not class attribute!
    pass

# ✅ CORRECT
def test_something(socratic_agent, mock_claude_client):
    # Mock Claude client directly via ServiceContainer fixture
    # No need to patch services
    pass
```

**Root Cause:**
- `services` is passed to `__init__` and stored as instance variable
- Cannot patch instance variables with `@patch` decorator
- Claude client is already mocked in ServiceContainer fixture

**For Phases 5-10:**
```
✅ DO NOT patch agent.services
✅ DO use mock_claude_client fixture which mocks Claude API
✅ DO NOT use @patch for instance attributes
✅ Use fixtures for mocking, not decorators
```

---

## ⚠️ MISTAKE #6: Two-Database Migration Running Order

**What Happened:**
- Ran `alembic upgrade head` without specifying which database
- Some migrations need socrates_auth, others need socrates_specs
- Without database checks, migrations fail

**Best Practice:**
```powershell
# Run auth migrations
$env:DATABASE_URL = "postgresql://postgres@localhost:5432/socrates_auth"
alembic upgrade head

# Run specs migrations
$env:DATABASE_URL = "postgresql://postgres@localhost:5432/socrates_specs"
alembic upgrade head
```

**Or use automated script:**
```powershell
.\scripts\run_migrations.ps1
```

**For Phases 5-10:**
```
✅ Document which database each migration targets
✅ Provide clear migration instructions in phase docs
✅ Always include _should_run() checks
```

---

## 📋 Pre-Implementation Checklist for Phases 5-10

Before creating ANY model or migration:

### Models:
- [ ] Check if model inherits from BaseModel
- [ ] If yes, ensure id, created_at, updated_at are in migration
- [ ] Avoid SQLAlchemy reserved words (metadata, query, session as columns)
- [ ] Use descriptive names for JSONB columns (not just "metadata")

### Migrations:
- [ ] Add `import os` at top
- [ ] Add `_should_run()` function checking DATABASE_URL
- [ ] Add database check in both `upgrade()` and `downgrade()`
- [ ] Verify which database: "socrates_auth" or "socrates_specs"
- [ ] Include ALL columns from BaseModel if inherited
- [ ] Use UUID(as_uuid=True) for UUID columns
- [ ] Use server_default for timestamp columns

### Tests:
- [ ] Use `auth_session` NOT `db_auth`
- [ ] Use `specs_session` NOT `db_specs`
- [ ] Use `mock_claude_client` fixture, NOT @patch decorators
- [ ] DO NOT patch instance attributes (services, db, etc.)
- [ ] Verify fixture names in conftest.py before writing tests

### Agents:
- [ ] Accept ServiceContainer in `__init__`
- [ ] Store as `self.services` (instance attribute)
- [ ] Get database via `self.services.get_database_auth()` or `get_database_specs()`
- [ ] Get Claude client via `self.services.get_claude_client()`
- [ ] DO NOT access services as class attribute

---

## 🎯 Key Takeaways

**The Pattern That Works:**

1. **Models**: Check BaseModel inheritance, avoid reserved words
2. **Migrations**: Add database checks, include all BaseModel columns
3. **Tests**: Use correct fixture names, mock via fixtures not decorators
4. **Agents**: Use ServiceContainer, access as instance attributes

**The Golden Rule:**
> "When in doubt, check existing code first (conftest.py, BaseModel, other migrations)"

---

**This document MUST be consulted before implementing Phases 5-10.**

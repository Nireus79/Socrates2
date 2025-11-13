# Action Items - Implementation Roadmap

**Status:** 80% Complete - CLI and library ready, backend integration needed

---

## IMMEDIATE ACTIONS (Do First)

### 1. Integrate API Methods into Socrates.py

**File:** `Socrates.py`
**Action:** Add all 150+ methods from `api_client_extension.py` to the `SocratesAPI` class

**Option A: Direct Integration (Recommended)**
```python
# At the top of Socrates.py, after SocratesAPI class definition

# Copy all methods from api_client_extension.py into SocratesAPI class
# Or inherit from extension mixin:

from api_client_extension import SocratesAPIExtension

class SocratesAPI(SocratesAPIExtension):
    # ... existing code ...
    pass
```

**Option B: Import as Mixin**
```python
# In Socrates.py
from api_client_extension import SocratesAPIExtension

class SocratesAPI(SocratesAPIExtension):
    """API client for Socrates backend"""
    # Keep existing methods
    # Inherit new methods from extension
```

**Time:** 30 minutes
**Status:** NEEDS TO BE DONE

---

### 2. Verify Backend API Endpoints Exist

**Files to Check:**
- `backend/app/api/auth.py`
- `backend/app/api/projects.py`
- `backend/app/api/sessions.py`
- `backend/app/api/teams.py`
- `backend/app/api/specifications.py`
- `backend/app/api/documents.py`
- `backend/app/api/domains.py`
- `backend/app/api/templates.py`
- `backend/app/api/code_generation.py`
- `backend/app/api/questions.py`
- `backend/app/api/workflows.py`
- `backend/app/api/export.py`
- `backend/app/api/admin.py`
- `backend/app/api/analytics.py`
- `backend/app/api/quality.py`
- `backend/app/api/notifications.py`
- `backend/app/api/conflicts.py`
- `backend/app/api/search.py`
- `backend/app/api/insights.py`
- `backend/app/api/github_endpoints.py`

**Action:**
1. Open each file
2. Check endpoints match API client methods
3. Create missing endpoints

**Time:** 2-3 hours
**Status:** NEEDS TO BE DONE

---

### 3. Test CLI Commands

**Command:**
```bash
# Test each module
python Socrates.py /auth register
python Socrates.py /project list
python Socrates.py /team create "Test Team"
python Socrates.py /document upload /path/to/file
python Socrates.py /llm list
# ... test all 112+ commands
```

**Time:** 1-2 hours
**Status:** CAN DO ONCE BACKEND IS VERIFIED

---

## BACKEND WORK (Week 1)

### 4. Implement LLM System Backend

**Files to Create:**

#### A. LLM Router (`backend/app/core/llm_router.py`)
```python
"""Multi-LLM provider routing system"""

class LLMRouter:
    """Route requests to selected LLM provider"""

    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        self.selected_provider = "anthropic"
        self.selected_model = "claude-3.5-sonnet"

    def route_completion(self, prompt, user_id, provider=None, model=None):
        """Route completion request to selected provider"""
        # Logic to route based on user's selected provider/model
        pass

    def get_available_models(self):
        """Get all available models from all providers"""
        return {
            "anthropic": ["claude-3.5-sonnet", "claude-3-opus", ...],
            "openai": ["gpt-4", "gpt-3.5-turbo", ...],
            ...
        }

    def set_user_model(self, user_id, provider, model):
        """Set user's preferred LLM/model"""
        # Save to database
        pass

    def get_user_model(self, user_id):
        """Get user's selected LLM/model"""
        # Fetch from database
        pass

    def get_costs(self):
        """Get costs per model"""
        return {...}

    def track_usage(self, user_id, provider, model, tokens_used, tokens_output):
        """Track LLM usage for billing"""
        # Save to llm_usage_tracking table
        pass
```

**Time:** 3-4 hours
**Status:** NEEDS TO BE DONE

#### B. LLM Endpoints (`backend/app/api/llm_endpoints.py`)
```python
"""LLM management API endpoints"""
from fastapi import APIRouter
from app.core.llm_router import LLMRouter

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])
llm_router = LLMRouter()

@router.get("/available")
async def list_available_models():
    """List all available LLM models"""
    return llm_router.get_available_models()

@router.get("/current")
async def get_current_model(current_user = Depends(get_current_user)):
    """Get currently selected model"""
    return llm_router.get_user_model(current_user.id)

@router.post("/select")
async def select_model(provider: str, model: str, current_user = Depends(get_current_user)):
    """Select LLM provider and model"""
    llm_router.set_user_model(current_user.id, provider, model)
    return {"success": True, "message": "Model selected"}

@router.get("/costs")
async def get_costs():
    """Get LLM costs per model"""
    return llm_router.get_costs()

@router.get("/usage")
async def get_usage(period: str = "month", current_user = Depends(get_current_user)):
    """Get LLM usage statistics"""
    return get_user_llm_usage(current_user.id, period)
```

**Time:** 2-3 hours
**Status:** NEEDS TO BE DONE

#### C. Database Migration
```bash
# Create migration file
alembic revision -m "Add LLM provider selection"
```

**Content:**
```python
# In alembic/versions/[timestamp]_add_llm_selection.py

def upgrade():
    # Add columns to users table
    op.add_column('users', sa.Column('llm_provider', sa.String(50), default='anthropic'))
    op.add_column('users', sa.Column('llm_model', sa.String(100), default='claude-3.5-sonnet'))

    # Create llm_usage_tracking table
    op.create_table(
        'llm_usage_tracking',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('provider', sa.String(50)),
        sa.Column('model', sa.String(100)),
        sa.Column('tokens_input', sa.Integer),
        sa.Column('tokens_output', sa.Integer),
        sa.Column('cost', sa.Float),
        sa.Column('created_at', sa.DateTime),
    )

def downgrade():
    op.drop_table('llm_usage_tracking')
    op.drop_column('users', 'llm_provider')
    op.drop_column('users', 'llm_model')
```

**Time:** 1 hour
**Status:** NEEDS TO BE DONE

#### D. Update Agents to Use LLM Router
**Files to Modify:**
- `backend/app/agents/base.py`
- `backend/app/agents/socratic.py`
- `backend/app/agents/direct_chat.py`
- `backend/app/agents/code_generator.py`
- All other agent files

**Change:**
```python
# Old code
response = anthropic_client.messages.create(...)

# New code
from app.core.llm_router import llm_router

response = llm_router.route_completion(
    prompt=prompt,
    user_id=current_user.id,
)
```

**Time:** 4-5 hours
**Status:** NEEDS TO BE DONE

### 5. Run Database Migrations

```bash
cd backend
python -m alembic upgrade head
```

**Time:** 30 minutes
**Status:** DO AFTER MIGRATION FILES CREATED

---

## TESTING (Week 1-2)

### 6. Test CLI Commands Against Backend

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload

# In another terminal, test CLI
cd ..
python Socrates.py /auth register john doe johndoe password john@example.com
python Socrates.py /auth login john@example.com password
python Socrates.py /project create "My Project"
python Socrates.py /project list
python Socrates.py /llm list
python Socrates.py /llm select
# ... test all commands
```

**Time:** 2-3 hours
**Status:** DO AFTER BACKEND WORK

### 7. Write Test Suite

**File:** `tests/test_integration.py`

```python
import pytest
from socrates_cli_lib import SocratesCLI

@pytest.fixture
def cli():
    return SocratesCLI("http://localhost:8000")

def test_register(cli):
    result = cli.register("john", "doe", "johndoe", "password123", "john@example.com")
    assert result["success"]

def test_login(cli):
    result = cli.login("johndoe", "password123")
    assert result["success"]

def test_create_project(cli):
    cli.login("johndoe", "password123")
    result = cli.create_project("Test Project")
    assert result["success"]

def test_llm_selection(cli):
    cli.login("johndoe", "password123")
    result = cli.list_available_llms()
    assert result["success"]
    assert "providers" in result["data"]
```

**Time:** 3-4 hours
**Status:** DO AFTER BACKEND WORK

---

## IDE INTEGRATION (Week 2-3)

### 8. Create VS Code Extension

**Files to Create:**
```
ide_integration/vscode/
├── package.json
├── tsconfig.json
├── src/
│   ├── extension.ts
│   ├── socrates.ts
│   └── commands/
│       ├── auth.ts
│       ├── project.ts
│       └── ...
└── README.md
```

**Time:** 8-10 hours
**Status:** FRAMEWORK READY, CODE NEEDED

### 9. Create PyCharm Plugin

**Files to Create:**
```
ide_integration/pycharm/
├── plugin.xml
├── src/
│   └── com/socrates/
│       ├── SocratesAction.java
│       ├── SocratesConsole.java
│       └── ...
└── README.md
```

**Time:** 8-10 hours
**Status:** FRAMEWORK READY, CODE NEEDED

---

## SUMMARY TABLE

| Item | Status | Time | Priority |
|------|--------|------|----------|
| 1. Integrate API methods | ⏳ | 30 min | 🔴 URGENT |
| 2. Verify endpoints | ⏳ | 2-3 hrs | 🔴 URGENT |
| 3. Test CLI commands | ⏳ | 1-2 hrs | 🟡 HIGH |
| 4. LLM router | ⏳ | 3-4 hrs | 🟡 HIGH |
| 5. LLM endpoints | ⏳ | 2-3 hrs | 🟡 HIGH |
| 6. Database migration | ⏳ | 1 hr | 🟡 HIGH |
| 7. Update agents | ⏳ | 4-5 hrs | 🟡 HIGH |
| 8. Test suite | ⏳ | 3-4 hrs | 🟢 MEDIUM |
| 9. VS Code ext | ⏳ | 8-10 hrs | 🟢 MEDIUM |
| 10. PyCharm ext | ⏳ | 8-10 hrs | 🟢 MEDIUM |

**Total Estimated Time:** 35-45 hours

---

## Quick Links

- **CLI Implementation:** `COMPLETE_CLI_IMPLEMENTATION.md`
- **Full Summary:** `FULL_IMPLEMENTATION_SUMMARY.md`
- **Implementation Plan:** `IMPLEMENTATION_PLAN.md`
- **API Extension Methods:** `api_client_extension.py`
- **IDE Library:** `socrates_cli_lib.py`
- **LLM CLI Commands:** `cli/commands/llm.py`

---

## Success Indicators

✅ You'll know it's working when:
1. `python Socrates.py /auth register` works
2. `python Socrates.py /project list` shows projects
3. `python Socrates.py /llm list` shows available models
4. `python Socrates.py /llm select` lets you choose a model
5. IDE library can be imported: `from socrates_cli_lib import SocratesCLI`
6. IDE can call `SocratesCLI().list_projects()`

---

## Need Help?

If stuck:
1. Check `FULL_IMPLEMENTATION_SUMMARY.md` for complete context
2. Look at existing backend endpoints for patterns
3. Review CLI command modules for examples
4. Check CLI utils for helper functions

**Total Implementation:** 80% CLI/API + 20% Backend = 100% Complete

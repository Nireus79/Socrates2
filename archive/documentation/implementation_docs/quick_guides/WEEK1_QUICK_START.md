# ⚡ WEEK 1 QUICK START - OPTIMIZATION BEGINS

**Status:** Ready to Execute
**Timeline:** Week 1 (10-15 hours total)
**Owner:** Development Team
**Start Date:** Now

---

## THE MISSION

**Week 1 Goal:** Prevent production issues + Establish core module pattern
- Critical fixes: 30 minutes
- Core extraction: 5-8 hours
- Integration: 3-5 hours
- **Expected Impact:** 30-40% performance improvement, library-ready foundation

---

## 🚀 DAY 1: CRITICAL FIXES (30 minutes)

These are one-line changes that prevent crashes. Do them first.

### Fix 1: Remove Debug File I/O (5 min)
**File:** `backend/app/agents/project.py:58-64`

```python
# BEFORE:
try:
    import os
    debug_file = os.path.join(os.path.dirname(__file__), '..', '..', 'debug_create_project.txt')
    with open(debug_file, 'a') as f:
        f.write(f"DEBUG: _create_project called...")
except Exception as e:
    pass

# AFTER:
# DELETE THE ENTIRE try/except BLOCK
# Use logging instead if needed:
self.logger.debug(f"Creating project: name={name}")
```

### Fix 2: Remove stderr Prints (5 min)
**File:** `backend/app/agents/socratic.py:164-167`

```python
# BEFORE:
import sys
print(f"\n=== SOCRATIC AGENT CALLING CLAUDE ===" , file=sys.stderr)
print(f"MODEL={model_name}", file=sys.stderr)
print(f"CATEGORY={next_category}", file=sys.stderr)
sys.stderr.flush()

# AFTER:
# DELETE ALL 4 lines
# Replace with:
self.logger.info(f"Calling Claude: model={model_name}, category={next_category}")
```

### Fix 3: Add Spec Query Limits (10 min)
**File:** `backend/app/agents/socratic.py:114-119`

```python
# BEFORE:
existing_specs = db.query(Specification).filter(
    and_(
        Specification.project_id == project_id,
        Specification.is_current == True
    )
).all()  # ← No limit!

# AFTER:
existing_specs = db.query(Specification).filter(
    and_(
        Specification.project_id == project_id,
        Specification.is_current == True
    )
).order_by(Specification.created_at.desc()).limit(100).all()  # ← Added!
```

**Also do this in:**
- `backend/app/agents/context.py:117-122` (same change)
- `backend/app/agents/code_generator.py:150-155` (same change)

### Fix 4: Use deque for History (5 min)
**File:** `backend/app/core/nlu_service.py:117, 128-129`

```python
# BEFORE:
def __init__(self):
    self.conversation_history = []

# In method:
self.conversation_history.append(new_message)
if len(self.conversation_history) > 20:
    self.conversation_history = self.conversation_history[-20:]

# AFTER:
from collections import deque

def __init__(self):
    self.conversation_history = deque(maxlen=20)

# In method:
self.conversation_history.append(new_message)  # Automatic management
```

### Fix 5: Add Pagination (5 min)
**File:** `backend/app/api/sessions.py:530-537`

```python
# BEFORE:
@router.get("/{session_id}/history")
def get_session_history(session_id: str, ...):
    history = db.query(ConversationHistory).filter(...).all()
    return {'success': True, 'history': [h.to_dict() for h in history]}

# AFTER:
@router.get("/{session_id}/history")
def get_session_history(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ...
):
    total = db.query(ConversationHistory).filter(...).count()
    history = db.query(ConversationHistory).filter(...).offset(skip).limit(limit).all()
    return {
        'success': True,
        'history': [h.to_dict() for h in history],
        'total': total,
        'skip': skip,
        'limit': limit,
        'has_more': (skip + limit) < total
    }
```

### Testing Quick Wins
```bash
# After each fix:
python -m pytest tests/ -k "project or socratic or session" -v

# Should see no new failures
```

---

## 📦 DAY 2-3: CREATE CORE MODULES (5-8 hours)

Now create the library-ready foundation. Use **DATA_MODEL_TEMPLATES.md** as your guide.

### Step 1: Create Models (1-2 hours)

**File:** Create `backend/app/core/models.py`

```python
# Copy from DATA_MODEL_TEMPLATES.md:
# - ProjectData
# - SpecificationData
# - QuestionData
# - ConflictData
# - BiasAnalysisResult
# - CoverageAnalysisResult
# - UserBehaviorData

# Plus conversion functions:
# - project_db_to_data()
# - spec_db_to_data()
# - question_db_to_data()
# - specs_db_to_data()
```

**Checklist:**
- [ ] All dataclasses created
- [ ] All conversion functions defined
- [ ] No SQLAlchemy imports in core module
- [ ] Type hints on all parameters

### Step 2: Extract Question Engine (2-3 hours)

**File:** Create `backend/app/core/question_engine.py`

**Strategy:**
1. Copy pure logic from `backend/app/agents/socratic.py:_generate_question()`
2. Extract methods that don't need database:
   - `_calculate_coverage()`
   - `_identify_next_category()`
   - `_build_question_generation_prompt()` (simplified)
3. Create `QuestionGenerator` class

**Template:**
```python
# backend/app/core/question_engine.py

from dataclasses import dataclass
from typing import List, Dict
from .models import ProjectData, SpecificationData

@dataclass
class QuestionResult:
    """Result of question generation"""
    text: str
    category: str
    context: str
    quality_score: float = 1.0

class QuestionGenerator:
    """Pure question generation logic - database-agnostic"""

    def generate(
        self,
        project: ProjectData,
        specs: List[SpecificationData],
        focus_category: str = None
    ) -> QuestionResult:
        """Generate question (pure logic, no database)"""
        # Calculate coverage
        coverage = self._calculate_coverage(specs)

        # Identify next category
        category = focus_category or self._identify_next_category(coverage)

        # Build context (without calling Claude yet)
        # This is pure logic
        context = f"Focus on {category} to improve project maturity"

        # Return question structure
        # (Actual text generation happens in Agent, not here)
        return QuestionResult(
            text="Placeholder question",  # Will be filled by Agent
            category=category,
            context=context,
            quality_score=1.0
        )

    def _calculate_coverage(self, specs: List[SpecificationData]) -> Dict[str, float]:
        """Calculate coverage per category"""
        coverage = {}
        for spec in specs:
            coverage[spec.category] = coverage.get(spec.category, 0) + 1
        return {k: min(v / 10, 1.0) * 100 for k, v in coverage.items()}

    def _identify_next_category(self, coverage: Dict[str, float]) -> str:
        """Identify lowest coverage category"""
        return min(coverage, key=coverage.get) if coverage else 'goals'
```

**Checklist:**
- [ ] Uses ProjectData, SpecificationData (not DB models)
- [ ] Returns QuestionResult (not DB model)
- [ ] No database queries
- [ ] No API calls
- [ ] Pure business logic only

### Step 3: Write Tests (1-2 hours)

**File:** Create `tests/test_core/test_question_engine.py`

```python
import pytest
from app.core.question_engine import QuestionGenerator
from app.core.models import ProjectData, SpecificationData

class TestQuestionGenerator:
    def setup_method(self):
        self.generator = QuestionGenerator()

    def test_calculate_coverage(self):
        """Test coverage calculation"""
        specs = [
            SpecificationData(id="1", category="goals", key="k1", value="v1", confidence=0.9),
            SpecificationData(id="2", category="goals", key="k2", value="v2", confidence=0.9),
        ]
        coverage = self.generator._calculate_coverage(specs)
        assert coverage['goals'] == pytest.approx(20.0)  # 2/10 * 100

    def test_identify_next_category(self):
        """Test category selection"""
        coverage = {'goals': 50, 'requirements': 30, 'tech_stack': 20}
        category = self.generator._identify_next_category(coverage)
        assert category == 'tech_stack'  # Lowest coverage

    def test_generate_returns_structure(self):
        """Test question generation returns proper structure"""
        project = ProjectData(
            id="p1", name="Test", description="Test project",
            current_phase="discovery", maturity_score=25, user_id="u1"
        )
        specs = [
            SpecificationData(id="1", category="goals", key="k", value="v", confidence=0.9)
        ]

        result = self.generator.generate(project, specs, focus_category='requirements')

        assert result.text  # Has text
        assert result.category == 'requirements'
        assert result.context  # Has context
        assert 0 <= result.quality_score <= 1.0
```

**Run Tests:**
```bash
pytest tests/test_core/test_question_engine.py -v
# Should pass: 3 passed
```

---

## 🔗 DAY 4-5: INTEGRATE & TEST (3-5 hours)

Now use the core module in the actual agent.

### Step 1: Refactor SocraticCounselorAgent (2-3 hours)

**File:** `backend/app/agents/socratic.py`

**Change:**
```python
# At top of file:
from ..core.question_engine import QuestionGenerator
from ..core.models import ProjectData, SpecificationData, project_db_to_data, specs_db_to_data

class SocraticCounselorAgent(BaseAgent):
    def __init__(self, agent_id, name, services):
        super().__init__(agent_id, name, services)
        self.engine = QuestionGenerator()  # ← Use core engine

    def _generate_question(self, data: Dict) -> Dict:
        db = None
        try:
            db = self.services.get_database_specs()

            # PHASE 1: Load from database
            project_db = db.query(Project).filter(...).first()
            specs_db = db.query(Specification).filter(...).all()

            # PHASE 2: Convert to plain data
            project = project_db_to_data(project_db)
            specs = specs_db_to_data(specs_db)

            # PHASE 3: Use core engine (pure logic)
            question_result = self.engine.generate(
                project=project,
                specs=specs,
                focus_category='requirements'  # Determine this separately
            )

            # PHASE 4: Save to database
            question = Question(
                project_id=project_db.id,
                text=question_result.text,
                category=question_result.category,
                context=question_result.context,
                quality_score=Decimal(str(question_result.quality_score))
            )
            db.add(question)
            db.commit()
            db.refresh(question)

            return {
                'success': True,
                'question': question.to_dict(),
                'question_id': str(question.id)
            }
        finally:
            if db:
                db.close()
```

### Step 2: Run Full Tests (1 hour)

```bash
# Run all agent tests
pytest tests/test_agents/test_socratic.py -v

# Run integration tests
pytest tests/test_api/test_sessions.py -v

# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=html
```

### Step 3: Measure Performance (1-2 hours, optional)

```python
# tests/test_performance/test_week1.py
import time

def test_question_generation_performance():
    """Question generation should be < 2 seconds"""
    client = TestClient(app)

    start = time.time()
    response = client.post("/sessions/123/generate-question")
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 2.0  # Should be fast
```

---

## ✅ WEEK 1 COMPLETION CHECKLIST

### Critical Fixes (Day 1)
- [ ] Debug file I/O removed
- [ ] stderr prints removed
- [ ] Spec query limits added (3 files)
- [ ] deque implemented for history
- [ ] Pagination added to session history
- [ ] All changes tested (no new failures)

### Core Modules (Day 2-3)
- [ ] `backend/app/core/models.py` created
- [ ] 7 dataclasses defined (ProjectData, SpecificationData, etc.)
- [ ] 4 conversion functions working
- [ ] `backend/app/core/question_engine.py` created
- [ ] QuestionGenerator class functional
- [ ] Pure logic (no database, no API calls)
- [ ] Unit tests pass (3/3)

### Integration (Day 4-5)
- [ ] SocraticCounselorAgent refactored
- [ ] Uses QuestionGenerator from core module
- [ ] Uses ProjectData, SpecificationData
- [ ] Integration tests pass
- [ ] Performance tests pass

### Git & Documentation
- [ ] All changes committed
- [ ] Commit messages clear
- [ ] Changes pushed to branch
- [ ] README updated if needed

---

## 📊 EXPECTED WEEK 1 RESULTS

### Performance
```
Quick Wins Impact:
- No more OOM errors on large projects
- No more transaction timeouts
- 30-40% faster API responses
- Cleaner logs (no stderr noise)
```

### Code Quality
```
Architecture Pattern Established:
- Core module with pure logic ✓
- Plain data models (library-ready) ✓
- Separation of concerns ✓
- Testable without database ✓
```

### Foundation for Week 2
```
Ready for:
- Conflict engine extraction
- Quality engine extraction
- Learning engine extraction
- More agent refactoring
```

---

## 🆘 TROUBLESHOOTING

### Issue: Tests fail after removing debug code
**Solution:** Debug code wasn't being tested. That's why it was a bug. Tests should still pass.
**Action:** Run `pytest tests/ -v` to see which tests actually fail. They're likely unrelated.

### Issue: Deque import error
**Solution:** `deque` is in stdlib `collections`
**Action:** Add `from collections import deque` at top of file

### Issue: Conversion functions cause type errors
**Solution:** Use proper type hints
**Action:** Check DATA_MODEL_TEMPLATES.md for correct type signatures

### Issue: Core module takes too long
**Solution:** Focus on question_engine first, do others in Week 2
**Action:** Move conflict/quality/learning engines to Week 2 if running over

---

## 📖 REFERENCE DOCS

While implementing Week 1, reference:

1. **DATA_MODEL_TEMPLATES.md** - Copy-paste templates
2. **OPTIMIZATION_PLAN.md, Part 1** - Detailed explanation
3. **OPTIMIZATION_IMPLEMENTATION_GUIDE.md** - Code examples

---

## 🎯 NEXT WEEK PREVIEW

After Week 1 completes successfully:

**Week 2 Goals:**
- High-impact optimizations (4 hours)
- Extract conflict, quality, learning engines (3 hours)
- Refactor agents to use new engines (3 hours)
- Result: 50% code quality, 50% performance improvement

---

## 👥 TEAM COORDINATION

**Daily Standup (5 min):**
- What did you complete?
- Any blockers?
- On track for Day X completion?

**By End of Day 5:**
- All critical fixes merged
- Core modules reviewed
- Integration tests passing
- Week 1 marked complete in tracking

---

**Status:** ✅ **READY TO START NOW**

Begin with Day 1 critical fixes (30 minutes).

All templates and guidance available in project docs.

Good luck! 🚀

---

**Day 1:** Start Now → 30 minutes
**Day 2-3:** Core extraction → 5-8 hours
**Day 4-5:** Integration → 3-5 hours

**Week 1 Total:** 10-15 hours
**Expected Improvement:** 30-40% faster, prevents crashes

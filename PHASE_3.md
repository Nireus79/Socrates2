# Phase 3: Real-Time Conflict Detection

**Status:** ⏳ PENDING
**Duration:** 2-3 days
**Goal:** Add conflict detection before saving specifications

---

## 📋 Objectives

1. Create ConflictDetectorAgent
2. Create Conflict model
3. Integrate conflict detection into spec extraction workflow
4. Implement conflict resolution UI flow
5. Test with contradicting answers

---

## 🔗 Dependencies

**From Phase 2:**
- `ContextAnalyzerAgent._extract_specifications()` - Insert conflict check before saving
- `Specification` model - Query existing specs
- `AgentOrchestrator` - Route to conflict detector

**Provides To Phase 4:**
- Conflict-free specifications (only saved if no conflicts)
- Conflict resolution history

---

## 📦 Key Deliverable: Conflict Model

```python
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey
from app.models.base import BaseModel
import enum

class ConflictType(enum.Enum):
    TECHNOLOGY = "technology"
    REQUIREMENTS = "requirements"
    TIMELINE = "timeline"
    RESOURCES = "resources"

class ConflictResolution(enum.Enum):
    PENDING = "pending"
    KEEP_OLD = "keep_old"
    REPLACE = "replace"
    MERGE = "merge"

class Conflict(BaseModel):
    __tablename__ = "conflicts"

    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False)
    conflict_type = Column(Enum(ConflictType), nullable=False)
    old_spec_id = Column(String(36), ForeignKey('specifications.id'), nullable=False)
    new_spec_value = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    resolution = Column(Enum(ConflictResolution), default=ConflictResolution.PENDING)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), ForeignKey('users.id'), nullable=True)
```

---

## 🔄 Modified Data Flow

**Before Phase 3:**
```
Extract specs → Save to DB → Update maturity
```

**After Phase 3:**
```
Extract specs → Check conflicts → If conflict: STOP, ask user
                                → If no conflict: Save to DB → Update maturity
```

---

## 🧪 Critical Tests

```python
def test_conflict_detection():
    """Test detects contradicting specs"""
    # First answer: "Use PostgreSQL"
    result1 = context_agent.process_request('extract_specifications', {
        'answer': 'I want to use PostgreSQL for the database'
    })
    assert result1['success'] == True

    # Second answer: "Use MySQL" (CONFLICT!)
    result2 = context_agent.process_request('extract_specifications', {
        'answer': 'Actually, let's use MySQL instead'
    })
    assert result2['success'] == False
    assert result2['conflicts_detected'] == True
    assert len(result2['conflicts']) > 0

def test_conflict_resolution():
    """Test can resolve conflict"""
    # Resolve: Replace old with new
    result = conflict_agent.process_request('resolve_conflict', {
        'conflict_id': conflict.id,
        'resolution': 'replace'
    })
    assert result['success'] == True

    # Verify spec updated
    spec = db.query(Specification).filter_by(key='primary_database').first()
    assert spec.value == 'MySQL'
```

---

## ✅ Verification

- [ ] ConflictDetectorAgent created and registered
- [ ] Detects contradicting specs
- [ ] Creates conflict records
- [ ] Blocks saving if conflicts exist
- [ ] User can resolve conflicts
- [ ] Tests pass with contradicting answers

---

**Previous:** [PHASE_2.md](./PHASE_2.md)
**Next:** [PHASE_4.md](./PHASE_4.md)

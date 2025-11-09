# Week 2 Complete: Agent Integration Guide

## Current Status

✅ **Complete (Days 1-4 + 5a):**
- 3 Core engines created (1,120 lines of pure logic)
- QualityControllerAgent refactored (95 lines removed)
- Pattern established and verified

📋 **Pending (Days 5b-5c):**
- ConflictDetectorAgent → use ConflictDetectionEngine
- UserLearningAgent → use LearningEngine

---

## Part 1: ConflictDetectorAgent Refactoring

### Pattern
```
Before: Agent has embedded prompt building, Claude API call, JSON parsing
After: Engine has prompt building + response parsing, Agent has database I/O + orchestration
```

### Files to Modify
- `backend/app/agents/conflict_detector.py` (450 lines → ~320 lines)

### Integration Steps

#### Step 1: Update Imports
```python
# ADD these imports:
from ..core.conflict_engine import ConflictDetectionEngine
from ..core.models import specs_db_to_data, conflict_db_to_data

# REMOVE these (no longer needed):
# - No changes to other imports needed, keep existing ones
```

#### Step 2: Update __init__()
```python
def __init__(self, agent_id: str = 'conflict', name: str = 'Conflict Detector', services=None):
    """Initialize with ConflictDetectionEngine"""
    super().__init__(agent_id, name, services)
    # ADD THIS:
    self.conflict_engine = ConflictDetectionEngine(self.logger)
```

#### Step 3: Refactor _detect_conflicts()

**Before:**
```python
# Build prompt
prompt = self._build_conflict_detection_prompt(new_specs, existing_specs)

# Call Claude
response = claude_client.messages.create(...)
response_text = response.content[0].text

# Parse JSON
conflict_analysis = json.loads(response_text)
```

**After:**
```python
# Convert to plain data
new_specs_data = specs_db_to_data([...])
existing_specs_data = specs_db_to_data([...])

# Build prompt using engine
prompt = self.conflict_engine.build_conflict_detection_prompt(
    new_specs_data,
    existing_specs_data
)

# Call Claude (same as before)
response = claude_client.messages.create(...)
response_text = response.content[0].text

# Parse response using engine
analysis = self.conflict_engine.parse_conflict_analysis(
    response_text,
    new_specs_data,
    existing_specs_data
)
```

#### Step 4: Remove Helper Methods
**Delete these methods (moved to engine):**
- `_build_conflict_detection_prompt()` (90 lines)
- `_format_specs_for_conflict_analysis()` (30 lines)

**Keep these methods:**
- `_resolve_conflict()` (database I/O)
- `_list_conflicts()` (database query)
- `_get_conflict_details()` (database query)

### Expected Results
- **Code removed:** ~120 lines
- **Lines saved:** Prompt building, JSON parsing logic
- **Testing:** Engine logic fully testable without database
- **Reusability:** Conflict analysis usable by other agents

---

## Part 2: UserLearningAgent Refactoring

### Pattern
```
Before: Agent has embedded behavior tracking and metrics calculation
After: Engine has all calculation logic, Agent has database I/O + orchestration
```

### Files to Modify
- `backend/app/agents/user_learning.py` (357 lines → ~240 lines)

### Integration Steps

#### Step 1: Update Imports
```python
# ADD these imports:
from ..core.learning_engine import LearningEngine
from ..core.models import UserBehaviorData
```

#### Step 2: Update __init__()
```python
def __init__(self, agent_id: str = 'learning', name: str = 'User Learning', services=None):
    """Initialize with LearningEngine"""
    super().__init__(agent_id, name, services)
    # ADD THIS:
    self.learning_engine = LearningEngine(self.logger)
```

#### Step 3: Refactor _get_user_profile()

**Before:**
```python
# Manual metrics calculation
engagement_score = ...
learning_velocity = ...
communication_style = ...
topics_explored = ...
```

**After:**
```python
# Use engine to build profile
user_behavior = UserBehaviorData(...)
metrics = self.learning_engine.calculate_learning_metrics(user_behavior)
hints = self.learning_engine.get_personalization_hints(user_behavior)

# Return structured response
return {
    'success': True,
    'behavior_patterns': user_behavior.patterns,
    'engagement_score': metrics['engagement_score'],
    'learning_velocity': metrics['learning_velocity'],
    'personalization_hints': hints
}
```

#### Step 4: Refactor _track_user_interaction()

**Before:**
```python
# Manual quality scoring
if quality > 0.8: style = 'technical'
elif quality > 0.6: style = 'professional'
else: style = 'casual'
```

**After:**
```python
# Use engine to track
interaction = self.learning_engine.track_response_quality(
    question_text=question,
    response_text=response,
    quality_score=quality_score
)
# Interaction now has: detail_level, coherence, quality_score
```

#### Step 5: Remove Helper Methods
**Delete these methods (moved to engine):**
- `_calculate_engagement_score()` (~20 lines)
- `_calculate_learning_velocity()` (~15 lines)
- `_determine_communication_style()` (~20 lines)
- `_infer_topic_interests()` (~25 lines)

**Keep these methods:**
- `_get_user_from_database()` (database query)
- `_record_interaction()` (database persistence)
- `_update_quality_metrics()` (database update)

### Expected Results
- **Code removed:** ~80 lines
- **Lines saved:** Metrics calculation, style inference
- **Testing:** Engine logic fully testable without database
- **Reusability:** Learning analysis usable by other agents

---

## Verification Checklist

After refactoring each agent, verify:

### Code Quality
- [ ] All imports updated correctly
- [ ] No duplicate logic remains
- [ ] Engine instance created in __init__
- [ ] All engine methods called with correct parameters
- [ ] Helper methods removed (moved to engine)

### Functionality
- [ ] Agent imports without errors
- [ ] Agent methods callable
- [ ] Database operations preserved
- [ ] Error handling maintained
- [ ] Logging statements updated

### Architecture
- [ ] Agent focuses on I/O and orchestration
- [ ] Engine focuses on pure logic
- [ ] Clear separation of concerns
- [ ] No circular dependencies

### Testing
```bash
# Quick import test
cd backend && source .venv/bin/activate
python -c "from app.agents.conflict_detector import ConflictDetectorAgent; print('✓')"
python -c "from app.agents.user_learning import UserLearningAgent; print('✓')"
```

---

## Summary of Changes

| Agent | Original | After | Removed | Status |
|-------|----------|-------|---------|--------|
| QualityController | 535 | 440 | 95 | ✅ Complete |
| ConflictDetector | 450 | 330 | 120 | 📋 Pending |
| UserLearning | 357 | 277 | 80 | 📋 Pending |
| **TOTAL** | **1,342** | **1,047** | **295** | **~78% done** |

---

## Timeline

**Estimated Time per Agent:**
- QualityControllerAgent: 30 minutes (DONE)
- ConflictDetectorAgent: 40 minutes (remaining)
- UserLearningAgent: 30 minutes (remaining)
- Testing & Verification: 20 minutes

**Total Remaining: ~90 minutes**

---

## Next Steps After Integration

1. **Test all three agents:**
   ```bash
   pytest tests/test_agent_integration.py -v
   ```

2. **Commit final refactoring:**
   ```bash
   git add -A
   git commit -m "feat: Week 2 Days 5b-5c - Agent integration complete"
   ```

3. **Proceed to Week 3:**
   - Response model optimization
   - Eager loading for relationships
   - Query result caching
   - Continue pattern with remaining agents

---

## Key Principles

1. **Separation of Concerns**
   - Agents: Database I/O, API orchestration, validation
   - Engines: Pure business logic, no database access

2. **No Duplicate Logic**
   - Logic extracted once in engine
   - Reused by multiple agents
   - Single source of truth

3. **Testability**
   - Engine methods testable without database
   - Agent methods testable with mocked database
   - Pure function testing possible

4. **Library-Ready**
   - Engines can move to separate package
   - Agents remain in main application
   - Core logic becomes reusable library

---

## Questions?

Refer to:
- `backend/app/core/conflict_engine.py` - Full ConflictDetectionEngine API
- `backend/app/core/learning_engine.py` - Full LearningEngine API
- `backend/app/agents/quality_controller.py` - Completed refactoring pattern

All three follow the same pattern established in QualityControllerAgent refactoring.

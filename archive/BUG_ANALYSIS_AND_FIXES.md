# Critical Bugs Found - Analysis and Fixes

**Date:** November 10, 2025
**Status:** BUGS IDENTIFIED & DOCUMENTED WITH TESTS
**Test File:** `backend/tests_new/test_question_gen_bugs_simple.py` (8 tests, all passing)

---

## Executive Summary

Two critical bugs prevent the CLI from functioning:
1. **Bug #1**: Question generation crashes (Specification schema mismatch)
2. **Bug #2**: Direct chat fails (Invalid message format for Anthropic API)

Both bugs are now documented with comprehensive test cases and reproduction steps.

---

## BUG #1: Specification Model Schema Mismatch

### ❌ Error Symptom
```
> /session start
✓ Session started: 0f8751c4-7f97-4c59-9c3f-395733198699
Failed to get question: Failed to generate question: 'Specification' object has no attribute 'key'
```

### 📍 Location
- **File:** `/backend/app/core/models.py`
- **Lines:** 171-172
- **Function:** `spec_db_to_data()`

### 🔍 Root Cause

**Database Model** (`app/models/specification.py`):
```python
class Specification(BaseModel):
    category = Column(String(100))      # e.g., "goals"
    content = Column(Text)              # e.g., "Handle 1000 concurrent users"
    source = Column(String(50))
    confidence = Column(Numeric(3, 2))
    is_current = Column(Boolean)
```

**Expected by Conversion Function** (`app/core/models.py:171-172`):
```python
def spec_db_to_data(db_spec) -> SpecificationData:
    return SpecificationData(
        ...
        key=db_spec.key,      # ← DOESN'T EXIST!
        value=db_spec.value,  # ← DOESN'T EXIST!
        ...
    )
```

**Expected by Library** (`SpecificationData` class):
```python
@dataclass
class SpecificationData:
    category: str      # "goals"
    key: str           # "response_time"
    value: str         # "< 200ms"
    confidence: float
```

### 📊 Call Chain
1. User: `/session start`
2. SocraticCounselorAgent._generate_question() - line 127
3. specs_db_to_data(existing_specs)
4. For each spec: spec_db_to_data(spec)
5. **CRASH:** AttributeError: 'Specification' object has no attribute 'key'

### 🔧 Fix Options

#### Option A: Map `content` to both `key` and `value` (Quick Fix)
```python
def spec_db_to_data(db_spec) -> SpecificationData:
    return SpecificationData(
        id=str(db_spec.id),
        project_id=str(db_spec.project_id),
        category=db_spec.category,
        key=db_spec.content[:50] if db_spec.content else "spec",  # Use first 50 chars as key
        value=db_spec.content,  # Use full content as value
        confidence=float(db_spec.confidence),
        source=db_spec.source,
        is_current=db_spec.is_current,
        created_at=db_spec.created_at.isoformat() if db_spec.created_at else None
    )
```

**Pros:**
- No database migration needed
- Works immediately
- Simple implementation

**Cons:**
- Doesn't preserve structured key/value pairs
- Library may expect separated values

#### Option B: Database Migration (Proper Fix)
Add new columns to Specification model:
```python
key = Column(String(255))      # "response_time"
value = Column(Text)           # "< 200ms"
content = Column(Text)         # Keep for backward compatibility
```

**Pros:**
- Proper schema design
- Supports structured data
- Aligns with library expectations

**Cons:**
- Requires database migration
- More complex implementation

### 💡 Recommendation
**Use Option A for immediate fix** to get tests passing, then consider Option B for proper long-term design.

---

## BUG #2: Invalid Timestamp Field in Anthropic Messages

### ❌ Error Symptom
```
> hello
Failed: Server error: {"detail":"Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0.timestamp: Extra inputs are not permitted'}, 'request_id': 'req_...'}"}
```

### 📍 Location
- **File:** `/backend/app/agents/direct_chat.py`
- **Line:** 302
- **Function:** `DirectChatAgent._load_conversation_context()`

### 🔍 Root Cause

**Code at line 298-305** (`direct_chat.py`):
```python
recent_messages = [
    {
        'role': msg.role,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()  # ← LINE 302: INVALID!
    }
    for msg in messages
]
```

**What Anthropic API Accepts:**
```python
{
    'role': 'user',      # ✓ REQUIRED
    'content': 'Hello'   # ✓ REQUIRED
}
```

**What Our Code Sends:**
```python
{
    'role': 'user',
    'content': 'Hello',
    'timestamp': '2025-11-10T12:34:56.789Z'  # ✗ INVALID!
}
```

### 📊 Call Chain
1. User: types message in direct chat mode
2. DirectChatAgent._load_conversation_context() - line 290
3. Builds messages list with 'timestamp' - line 302
4. NLUService.chat() sends to Anthropic API
5. **CRASH:** ValueError: Extra inputs are not permitted

### 🔧 Fix

**Remove 'timestamp' field from message dict:**

```python
# BEFORE (BROKEN):
recent_messages = [
    {
        'role': msg.role,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()  # ← DELETE THIS LINE
    }
    for msg in messages
]

# AFTER (FIXED):
recent_messages = [
    {
        'role': msg.role,
        'content': msg.content
    }
    for msg in messages
]
```

**Effort:** 2 minutes
**Impact:** Fixes direct chat mode completely

---

## Test Coverage

### Bug #1 Tests (3 tests)
1. ✅ `test_spec_db_to_data_schema_mismatch` - Shows schema mismatch
2. ✅ `test_specs_db_to_data_chain_effect` - Shows call chain to error
3. ✅ `test_show_field_mapping_issue` - Documents field mapping

### Bug #2 Tests (2 tests)
1. ✅ `test_anthropic_api_rejects_timestamp` - Shows invalid format
2. ✅ `test_valid_anthropic_message_format` - Shows correct format

### Integration Tests (3 tests)
1. ✅ `test_socratic_mode_error_message` - User-facing error
2. ✅ `test_direct_mode_error_message` - User-facing error
3. ✅ `test_summary_of_both_bugs` - Summary documentation

**All 8 tests PASS** ✓

---

## Implementation Plan

### Immediate Actions (30 minutes)

1. **Fix Bug #2 (2 minutes)**
   - Remove 'timestamp' field from direct_chat.py line 302
   - Test in direct chat mode

2. **Fix Bug #1 (5 minutes)**
   - Update spec_db_to_data() to map content → key/value
   - Test in socratic mode

3. **Run Full Test Suite (10 minutes)**
   - Run pytest on test_question_gen_bugs_simple.py
   - Run pytest on test_api_endpoints.py
   - Run pytest on test_agents_core.py

4. **Manual CLI Testing (10 minutes)**
   - Test `/session start` → generates question
   - Test direct chat mode → receives response
   - Test multiple questions

### Next Phase (Post-Bugs-Fixed)

1. Update LIBRARY_AND_PROJECT_ROADMAP.md with timeline for proper schema fix (Option B)
2. Add database migration for key/value columns (if going with Option B)
3. Update documentation
4. Run full test suite

---

## Summary Table

| Bug | Location | Lines | Issue | Fix | Impact |
|-----|----------|-------|-------|-----|--------|
| #1 | models.py | 171-172 | Missing key/value fields | Map content field | Question generation |
| #2 | direct_chat.py | 302 | Invalid timestamp in messages | Remove timestamp | Direct chat |

---

## Files to Modify

```
/home/user/Socrates2/backend/
├── app/core/models.py           [BUG #1: Fix spec_db_to_data]
└── app/agents/direct_chat.py    [BUG #2: Remove timestamp]
```

---

## Verification Steps

After fixes are applied:

1. **CLI Test - Socratic Mode:**
   ```
   > /project select
   > /session start
   Ready to begin Socratic questioning!
   Question: [Should show a question, no error]
   ```

2. **CLI Test - Direct Chat Mode:**
   ```
   > /mode
   ✓ Switched to direct mode 💬
   > hello
   Socrates: [Should receive response, no error]
   ```

3. **Test Suite:**
   ```bash
   pytest tests_new/test_question_gen_bugs_simple.py -v
   # Expected: 8 passed ✓
   ```

---

**Status:** Ready for implementation
**Estimated Fix Time:** 30 minutes
**Risk Level:** LOW (both are simple fixes)


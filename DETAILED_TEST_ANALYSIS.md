# Socrates2 Test Analysis: Failing Tests and Missing Modules

**Analysis Date:** November 12, 2025
**Total Test Methods:** 117 across 5 test files
**Root Cause:** Missing top-level module wrappers for re-exporting from `app.domains` subdirectory

---

## Executive Summary

The test suite contains **117 test methods** organized in 5 test files testing the Phase 7 "pluggification" system. All tests fail at import time because they expect to import from:

- `app.programming`
- `app.questions`
- `app.registry`
- `app.rules`

However, these modules are located in `app.domains/` subdirectory. The modules and classes exist and are functional, but the imports are wrong. **No code needs to be written—only 4 import wrapper modules need to be created** to make modules accessible at the package root level.

---

## Test Files and Their Purposes

### 1. test_integration.py (25 tests)
**Purpose:** Integration tests for complete Phase 7.0 pluggification system

**Location:** `/home/user/Socrates2/backend/tests/test_integration.py`

**Test Classes:**
- `TestPhase7Integration` (16 tests) - Complete system integration across all subsystems
- `TestPhase7Performance` (5 tests) - Performance benchmarking
- `TestPhase7Compatibility` (2 tests) - Backward compatibility tests

**What It Tests:**
- Domain initialization loads all 4 subsystems (questions, exporters, rules, analyzers)
- All subsystems return correct types (Question, ExportFormat, ConflictRule, str for analyzers)
- Subsystem counts match configuration (questions ≥14, exporters=8, rules ≥4, analyzers ≥4)
- Questions and exporters integration workflow
- Conflict rules detect specification conflicts
- Quality analyzers validate specification quality
- Complete workflow: questions → specs → rules → analyzers → export
- Multiple domain instances independence
- Error handling and recovery
- Performance (loading < 100ms, filtering < 50ms)
- Singleton engines work correctly
- Scalability with multiple domain instances
- Data consistency across subsystems
- All objects have required metadata

**Imports Required:**
```python
from app.analyzers import QualityAnalyzerEngine
from app.base import (
    ConflictRule,
    ExportFormat,
    Question,
)
from app.exporters import ExportTemplateEngine
from app.programming import ProgrammingDomain  # ❌ MISSING
from app.questions import QuestionTemplateEngine  # ❌ MISSING
from app.rules import ConflictRuleEngine  # ❌ MISSING
```

---

### 2. test_programming_domain.py (22 tests)
**Purpose:** Validate ProgrammingDomain implementation

**Location:** `/home/user/Socrates2/backend/tests/test_programming_domain.py`

**Test Classes:**
- `TestProgrammingDomain` (6 tests) - Basic domain functionality
- `TestProgrammingDomainQuestions` (6 tests) - Question set validation
- `TestProgrammingDomainExports` (5 tests) - Export format functionality
- `TestProgrammingDomainRules` (5 tests) - Conflict rule functionality

**What It Tests:**
- Domain metadata (id, name, version, description)
- Categories exist (Performance, Security, Scalability, Usability, etc.)
- Questions exist for each category
- Questions have required fields (id, text, category, difficulty)
- Export formats exist (8+ languages: Python, JavaScript, TypeScript, Go, Java, Rust, C#, Kotlin)
- Export format details correct (extension, mime type)
- Conflict rules exist with details
- Domain serialization to dict
- Metadata completeness
- Performance questions (≥3: perf_1, perf_2, perf_3)
- Difficulty distribution (easy, medium, hard)
- Questions have help text (≥70%)
- All formats have templates
- Format lookup by language
- Rules have meaningful names
- Rules have conditions
- Critical rules marked as errors

**Imports Required:**
```python
from app.programming import ProgrammingDomain  # ❌ MISSING
```

---

### 3. test_questions.py (19 tests)
**Purpose:** Validate QuestionTemplateEngine

**Location:** `/home/user/Socrates2/backend/tests/test_questions.py`

**Test Classes:**
- `TestQuestionTemplateEngine` (17 tests) - Engine functionality
- `TestGlobalQuestionEngine` (1 test) - Singleton pattern
- `TestProgrammingDomainQuestions` (1 test) - Integration with ProgrammingDomain

**What It Tests:**
- Load questions from dictionary
- Validate questions with missing fields
- Filter by category
- Filter by difficulty
- Filter by dependencies
- Validate questions (success cases)
- Detect duplicate IDs
- Detect missing required fields
- Detect circular dependencies
- Get next recommended questions
- Filter next questions by category
- Limit parameter
- Convert to dict
- Convert to JSON
- Save/load JSON files
- Singleton pattern (get_question_engine returns same instance)
- Programming domain questions load correctly (≥14)
- Questions have proper dependencies
- Question categories match domain categories

**Imports Required:**
```python
from app.base import Question
from app.questions import QuestionTemplateEngine, get_question_engine  # ❌ MISSING
from app.programming import ProgrammingDomain  # ❌ MISSING
```

---

### 4. test_registry.py (17 tests)
**Purpose:** Validate DomainRegistry system

**Location:** `/home/user/Socrates2/backend/tests/test_registry.py`

**Test Classes:**
- `TestDomainRegistry` (13 tests) - Registry functionality
- `TestGlobalFunctions` (4 tests) - Global registry functions

**What It Tests:**
- Registry is singleton
- Register domain
- Register duplicate raises error
- Register non-BaseDomain raises error
- Get domain
- Get nonexistent domain raises error
- Lazy instantiation of domains
- Check if domain exists (has_domain)
- List all domain IDs
- List all domains
- Get domain count
- Unregister domain
- Unregister nonexistent raises error
- Clear all domains
- Convert registry to dict
- Global registry functions
- Register domain globally
- Verify test domain inheritance from BaseDomain

**Imports Required:**
```python
from app.base import BaseDomain
from app.registry import DomainRegistry, get_domain_registry, register_domain  # ❌ MISSING
```

---

### 5. test_rules.py (34 tests)
**Purpose:** Validate ConflictRuleEngine

**Location:** `/home/user/Socrates2/backend/tests/test_rules.py`

**Test Classes:**
- `TestConflictRuleEngine` (32 tests) - Engine functionality
- `TestGlobalRuleEngine` (1 test) - Singleton pattern
- `TestProgrammingDomainRules` (9 tests) - Integration with ProgrammingDomain

**What It Tests:**
- Load rules from dictionary
- Validate rules with missing fields
- Filter by severity (error, warning)
- Filter by severity (case insensitive)
- Filter by category
- Filter by category (multiple matches)
- Filter by pattern matching
- Pattern matching case insensitive
- Pattern matching in description
- Validate rules success
- Detect duplicate rule IDs
- Detect missing required fields
- Detect all missing required fields
- Group rules by category
- Group rules by severity
- Severity grouping with only errors
- Convert to dict
- Convert to JSON
- Save/load JSON files
- Load from non-existent file raises error
- Load from JSON that isn't array raises error
- ConflictRule field validation
- All severity levels handled
- Filter chaining (severity then category)
- Large rule set (50 rules)
- Multiple rules same category
- Singleton pattern
- Programming domain rules load (≥4)
- Rules have required fields
- Rule IDs unique
- Rules validate correctly
- Rules have severity levels
- Rules span multiple categories

**Imports Required:**
```python
from app.base import ConflictRule, SeverityLevel
from app.rules import ConflictRuleEngine, get_rule_engine  # ❌ MISSING
from app.programming import ProgrammingDomain  # ❌ MISSING
```

---

## Root Cause Analysis

### The Problem

Tests import from top-level `app` module:
```python
from app.programming import ProgrammingDomain
from app.questions import QuestionTemplateEngine
from app.registry import DomainRegistry
from app.rules import ConflictRuleEngine
```

**But these files don't exist at the app root.**

### Why It Happens

The actual modules are in `app/domains/`:
- `/home/user/Socrates2/backend/app/domains/questions.py` ✓ exists
- `/home/user/Socrates2/backend/app/domains/rules.py` ✓ exists
- `/home/user/Socrates2/backend/app/domains/registry.py` ✓ exists
- `/home/user/Socrates2/backend/app/domains/programming/__init__.py` ✓ exists

### The Solution

Create 4 simple **import wrapper modules** at the `app/` level that re-export from `app/domains/`. This is a common Python pattern for API organization.

---

## What Each Test File Expects to Import

### test_integration.py Import Map

| Import | Current Location | Needed Location | Status |
|--------|-----------------|-----------------|--------|
| `from app.analyzers import QualityAnalyzerEngine` | `app.analyzers.engine` | `app.analyzers` | ✓ Works |
| `from app.base import ConflictRule, ExportFormat, Question` | `app.base.models` | `app.base` | ✓ Works |
| `from app.exporters import ExportTemplateEngine` | `app.exporters.engine` | `app.exporters` | ✓ Works |
| `from app.programming import ProgrammingDomain` | `app.domains.programming` | **`app.programming`** | ❌ Missing |
| `from app.questions import QuestionTemplateEngine` | `app.domains.questions` | **`app.questions`** | ❌ Missing |
| `from app.rules import ConflictRuleEngine` | `app.domains.rules` | **`app.rules`** | ❌ Missing |

### test_programming_domain.py Import Map

| Import | Current Location | Needed Location | Status |
|--------|-----------------|-----------------|--------|
| `from app.programming import ProgrammingDomain` | `app.domains.programming` | **`app.programming`** | ❌ Missing |

### test_questions.py Import Map

| Import | Current Location | Needed Location | Status |
|--------|-----------------|-----------------|--------|
| `from app.base import Question` | `app.base.models` | `app.base` | ✓ Works |
| `from app.questions import QuestionTemplateEngine, get_question_engine` | `app.domains.questions` | **`app.questions`** | ❌ Missing |
| `from app.programming import ProgrammingDomain` | `app.domains.programming` | **`app.programming`** | ❌ Missing |

### test_registry.py Import Map

| Import | Current Location | Needed Location | Status |
|--------|-----------------|-----------------|--------|
| `from app.base import BaseDomain` | `app.base.base_domain` | `app.base` | ✓ Works |
| `from app.registry import DomainRegistry, get_domain_registry, register_domain` | `app.domains.registry` | **`app.registry`** | ❌ Missing |

### test_rules.py Import Map

| Import | Current Location | Needed Location | Status |
|--------|-----------------|-----------------|--------|
| `from app.base import ConflictRule, SeverityLevel` | `app.base.models` | `app.base` | ✓ Works |
| `from app.rules import ConflictRuleEngine, get_rule_engine` | `app.domains.rules` | **`app.rules`** | ❌ Missing |
| `from app.programming import ProgrammingDomain` | `app.domains.programming` | **`app.programming`** | ❌ Missing |

---

## Modules to Create

### 1. `/home/user/Socrates2/backend/app/programming.py`

**Purpose:** Re-export ProgrammingDomain for API convenience

**Required Exports:**
- `ProgrammingDomain` from `app.domains.programming`

**Content:**
```python
"""
Programming domain for Socrates.

Re-exports from app.domains.programming for convenient top-level access.
"""

from app.domains.programming import ProgrammingDomain

__all__ = [
    "ProgrammingDomain",
]
```

**Note:** Check if other domain classes (BusinessDomain, ArchitectureDomain, etc.) should also be exported

---

### 2. `/home/user/Socrates2/backend/app/questions.py`

**Purpose:** Re-export question template engine for API convenience

**Required Exports:**
- `QuestionTemplateEngine` from `app.domains.questions`
- `get_question_engine()` from `app.domains.questions` (function, not class)

**Content:**
```python
"""
Question template engine for Socrates.

Re-exports from app.domains.questions for convenient top-level access.
"""

from app.domains.questions import (
    QuestionTemplateEngine,
    get_question_engine,
)

__all__ = [
    "QuestionTemplateEngine",
    "get_question_engine",
]
```

---

### 3. `/home/user/Socrates2/backend/app/rules.py`

**Purpose:** Re-export conflict rule engine for API convenience

**Required Exports:**
- `ConflictRuleEngine` from `app.domains.rules`
- `get_rule_engine()` from `app.domains.rules` (function, not class)

**Content:**
```python
"""
Conflict rule engine for Socrates.

Re-exports from app.domains.rules for convenient top-level access.
"""

from app.domains.rules import (
    ConflictRuleEngine,
    get_rule_engine,
)

__all__ = [
    "ConflictRuleEngine",
    "get_rule_engine",
]
```

---

### 4. `/home/user/Socrates2/backend/app/registry.py`

**Purpose:** Re-export domain registry for API convenience

**Required Exports:**
- `DomainRegistry` from `app.domains.registry`
- `get_domain_registry()` from `app.domains.registry` (function)
- `register_domain()` from `app.domains.registry` (function)

**Content:**
```python
"""
Domain registry for Socrates.

Re-exports from app.domains.registry for convenient top-level access.
"""

from app.domains.registry import (
    DomainRegistry,
    get_domain_registry,
    register_domain,
)

__all__ = [
    "DomainRegistry",
    "get_domain_registry",
    "register_domain",
]
```

---

## Verification Checklist

After creating the 4 modules above, verify:

1. **Import Test 1: Programming**
   ```bash
   cd /home/user/Socrates2/backend
   python -c "from app.programming import ProgrammingDomain; print(ProgrammingDomain)"
   ```
   Expected: No error, prints `<class 'app.domains.programming.ProgrammingDomain'>`

2. **Import Test 2: Questions**
   ```bash
   python -c "from app.questions import QuestionTemplateEngine, get_question_engine; print(QuestionTemplateEngine, get_question_engine)"
   ```
   Expected: No error, prints both

3. **Import Test 3: Rules**
   ```bash
   python -c "from app.rules import ConflictRuleEngine, get_rule_engine; print(ConflictRuleEngine, get_rule_engine)"
   ```
   Expected: No error, prints both

4. **Import Test 4: Registry**
   ```bash
   python -c "from app.registry import DomainRegistry, get_domain_registry, register_domain; print(DomainRegistry, get_domain_registry, register_domain)"
   ```
   Expected: No error, prints all three

5. **Run Single Test:**
   ```bash
   python -m pytest tests/test_programming_domain.py::TestProgrammingDomain::test_domain_metadata -xvs
   ```
   Expected: Test passes (after conftest dependencies are installed)

---

## Summary

| Aspect | Details |
|--------|---------|
| **Total Test Methods** | 117 (25 + 22 + 19 + 17 + 34) |
| **Files with Import Issues** | 5 test files |
| **Root Cause** | Missing wrapper modules at app/ level |
| **Modules to Create** | 4 simple re-export modules |
| **Code to Write** | ~70 lines total (mostly docstrings) |
| **Complexity** | Very Low - just Python imports |
| **Impact** | Fixes all 117 test import errors |

---

## Next Steps

1. Create `/home/user/Socrates2/backend/app/programming.py`
2. Create `/home/user/Socrates2/backend/app/questions.py`
3. Create `/home/user/Socrates2/backend/app/rules.py`
4. Create `/home/user/Socrates2/backend/app/registry.py`
5. Run import verification commands (above)
6. Install missing test dependencies (sqlalchemy, etc.)
7. Run tests: `pytest tests/test_integration.py tests/test_programming_domain.py tests/test_questions.py tests/test_registry.py tests/test_rules.py -v`


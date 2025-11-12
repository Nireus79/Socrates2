# Import Issues - Detailed Findings

## Overview
This document provides detailed file-by-file findings of all import issues in the codebase.

---

## Category 1: Agent Files Importing from Non-Existent 'socrates' Package

### 1. `/home/user/Socrates2/backend/app/agents/socratic.py`
**Line:** 19
**Current Import:**
```python
from socrates import (
    QuestionGenerator,
    UserBehaviorData,
    project_db_to_data,
    questions_db_to_data,
    specs_db_to_data,
)
```

**What Actually Exists:**
- `QuestionGenerator` - in `/home/user/Socrates2/backend/app/core/question_engine.py`
- `UserBehaviorData` - in `/home/user/Socrates2/backend/app/core/models.py`
- `project_db_to_data` - in `/home/user/Socrates2/backend/app/core/models.py`
- `questions_db_to_data` - in `/home/user/Socrates2/backend/app/core/models.py`
- `specs_db_to_data` - in `/home/user/Socrates2/backend/app/core/models.py`

**How Used:**
- Line 54: `self.question_generator = QuestionGenerator(self.logger)`
- Line 127: `project_data = project_db_to_data(project)`
- Line 128: `specs_data = specs_db_to_data(existing_specs)`
- Line 129: `questions_data = questions_db_to_data(previous_questions)`
- Line 149: `user_behavior = UserBehaviorData(...)`
- Line 162-163: Using question_generator methods

---

### 2. `/home/user/Socrates2/backend/app/agents/conflict_detector.py`
**Line:** 20
**Current Import:**
```python
from socrates import ConflictDetectionEngine, SpecificationData, specs_db_to_data
```

**What Actually Exists:**
- `ConflictDetectionEngine` - in `/home/user/Socrates2/backend/app/core/conflict_engine.py`
- `SpecificationData` - in `/home/user/Socrates2/backend/app/core/models.py`
- `specs_db_to_data` - in `/home/user/Socrates2/backend/app/core/models.py`

**How Used:**
- Line 51 (approx): `self.conflict_engine = ConflictDetectionEngine(self.logger)`
- Throughout: Using ConflictDetectionEngine methods and SpecificationData

---

### 3. `/home/user/Socrates2/backend/app/agents/quality_controller.py`
**Line:** 20
**Current Import:**
```python
from socrates import BiasDetectionEngine, specs_db_to_data
```

**What Actually Exists:**
- `BiasDetectionEngine` - in `/home/user/Socrates2/backend/app/core/quality_engine.py`
- `specs_db_to_data` - in `/home/user/Socrates2/backend/app/core/models.py`

**How Used:**
- Line 49 (approx): `self.quality_engine = BiasDetectionEngine(self.logger)`
- Throughout: Using BiasDetectionEngine methods

---

### 4. `/home/user/Socrates2/backend/app/agents/user_learning.py`
**Line:** 19
**Current Import:**
```python
from socrates import LearningEngine
```

**What Actually Exists:**
- `LearningEngine` - in `/home/user/Socrates2/backend/app/core/learning_engine.py`

**How Used:**
- Line 45 (approx): `self.learning_engine = LearningEngine(self.logger)`
- Throughout: Using LearningEngine methods

---

## Category 2: Test File Expecting 'socrates' Package

### 5. `/home/user/Socrates2/backend/tests/test_library_integration.py`

**Total Test Cases:** 28

**All Tests Expect:** `import socrates` to succeed with following exports:

**Engines Expected:**
```python
from socrates import QuestionGenerator        # Line 25
from socrates import ConflictDetectionEngine  # Line 30
from socrates import BiasDetectionEngine      # Line 35
from socrates import LearningEngine           # Line 40
```

**Data Models Expected:**
```python
from socrates import ProjectData              # Line 50
from socrates import SpecificationData        # Line 55
from socrates import QuestionData             # Line 60
from socrates import ConflictData             # Line 65
```

**Conversion Functions Expected:**
```python
from socrates import project_db_to_data       # Line 75
from socrates import spec_db_to_data          # Line 80
from socrates import question_db_to_data      # Line 85
from socrates import conflict_db_to_data      # Line 90
```

**Version Expected:**
```python
import socrates
socrates.__version__  # Line 101-102
```

**Test Classes:**
1. `TestSocratesLibraryImports` - 5 tests
2. `TestSocratesDataModels` - 4 tests
3. `TestSocratesConversionFunctions` - 4 tests
4. `TestSocratesLibraryVersion` - 2 tests
5. `TestQuestionGeneratorUsage` - 6 tests
6. `TestConflictDetectionEngineUsage` - 2 tests
7. `TestBiasDetectionEngineUsage` - 2 tests
8. `TestLearningEngineUsage` - 2 tests
9. `TestSocratesLibraryIntegration` - 2 tests

---

## Category 3: Working Domain Imports (Reference)

### These Imports Work Correctly:

#### A. Direct Domain Imports (from app.domains submodules)
**Working Pattern:**
```python
from app.programming import ProgrammingDomain
from app.architecture import ArchitectureDomain
from app.testing import TestingDomain
from app.business import BusinessDomain
from app.security import SecurityDomain
from app.devops import DevOpsDomain
from app.data_engineering import DataEngineeringDomain
```

**Files Using This Pattern:** 19 test files
- `/home/user/Socrates2/backend/tests/test_programming_domain.py` (line 5)
- `/home/user/Socrates2/backend/tests/test_integration.py` (line 14)
- `/home/user/Socrates2/backend/tests/test_questions.py` (line 230, 240, 251)
- `/home/user/Socrates2/backend/tests/test_rules.py` (line 394, 404, 419, 429, 439, 450)
- `/home/user/Socrates2/backend/tests/test_exporters.py` (line 370, 380, 391, 402, 419, 434, 447)
- `/home/user/Socrates2/backend/tests/test_analyzers.py` (line 322, 332)

#### B. Registry Pattern (from app.domains)
**Working Pattern:**
```python
from app.domains import (
    ArchitectureDomain,
    TestingDomain,
    ProgrammingDomain,
    get_domain_registry
)
from app.domains.registry import register_all_domains
```

**File:** `/home/user/Socrates2/backend/app/domains/__init__.py`
- Properly exports all 7 domains
- Properly exports registry functions

---

## Category 4: Domain Module Structure Status

### All 7 Domain Modules are Fully Implemented:

| Domain | Status | Key Files |
|--------|--------|-----------|
| Programming | ✅ Complete | `/app/domains/programming/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |
| Architecture | ✅ Complete | `/app/domains/architecture/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |
| Testing | ✅ Complete | `/app/domains/testing/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |
| Business | ✅ Complete | `/app/domains/business/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |
| Data Engineering | ✅ Complete | `/app/domains/data_engineering/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |
| Security | ✅ Complete | `/app/domains/security/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |
| DevOps | ✅ Complete | `/app/domains/devops/{__init__.py, domain.py, questions.json, exporters.json, rules.json, analyzers.json}` |

### Domain Module Exports Status:

| File | Has `__all__` | Content |
|------|:-------:|---------|
| `app/domains/__init__.py` | ✅ Yes | Exports: BaseDomain, DomainRegistry, get_domain_registry, 7x Domain classes |
| `app/domains/programming/__init__.py` | ✅ Yes | `__all__ = ["ProgrammingDomain"]` |
| `app/domains/architecture/__init__.py` | ✅ Yes | `__all__ = ["ArchitectureDomain"]` |
| `app/domains/testing/__init__.py` | ✅ Yes | `__all__ = ["TestingDomain"]` |
| `app/domains/business/__init__.py` | ❌ No | Missing `__all__` (imports defined but no explicit export) |
| `app/domains/security/__init__.py` | ❓ Unknown | Need verification |
| `app/domains/devops/__init__.py` | ❓ Unknown | Need verification |
| `app/domains/data_engineering/__init__.py` | ❓ Unknown | Need verification |

---

## Category 5: Core Engine Implementation Details

### QuestionGenerator
**File:** `/home/user/Socrates2/backend/app/core/question_engine.py`
**Status:** ✅ Fully implemented

**Available Methods:**
- `__init__(logger=None)`
- `calculate_coverage(specs: List[SpecificationData]) -> Dict[str, float]`
- `identify_next_category(coverage: Dict[str, float]) -> str`
- `build_question_generation_prompt(...) -> str`
- `parse_question_response(response_text: str, category: str) -> Dict`

**Dependencies:**
- Uses: `SpecificationData`, `ProjectData`, `QuestionData`, `UserBehaviorData` from models.py

---

### ConflictDetectionEngine
**File:** `/home/user/Socrates2/backend/app/core/conflict_engine.py`
**Status:** ✅ Fully implemented

**Available Methods:**
- `__init__(logger=None)`
- `build_conflict_detection_prompt(new_specs, existing_specs, project_context) -> str`
- `detect_conflicts(...) -> List[ConflictData]`

**Enums Provided:**
- `ConflictType` (CONTRADICTION, INCONSISTENCY, DEPENDENCY, REDUNDANCY)
- `ConflictSeverity` (LOW, MEDIUM, HIGH)

**Dependencies:**
- Uses: `SpecificationData`, `ConflictData` from models.py

---

### BiasDetectionEngine
**File:** `/home/user/Socrates2/backend/app/core/quality_engine.py`
**Status:** ✅ Fully implemented

**Available Methods:**
- `__init__(logger=None)`
- `detect_bias_in_question(question_text: str) -> BiasAnalysisResult`
- `analyze_coverage(specs: List[SpecificationData]) -> CoverageAnalysisResult`

**Bias Pattern Detection:**
- Solution bias patterns (6 patterns)
- Technology bias patterns (7 patterns)
- Leading question patterns (9 patterns)
- Custom weight scoring system

**Dependencies:**
- Uses: `BiasAnalysisResult`, `CoverageAnalysisResult`, `SpecificationData` from models.py

---

### LearningEngine
**File:** `/home/user/Socrates2/backend/app/core/learning_engine.py`
**Status:** ✅ Fully implemented

**Available Methods:**
- `__init__(logger=None)`
- `build_user_profile(user_id, questions_asked, responses_quality, topic_interactions, projects_completed) -> UserBehaviorData`
- `calculate_learning_metrics(user_behavior: UserBehaviorData) -> Dict[str, Any]`

**Dependencies:**
- Uses: `UserBehaviorData` from models.py

---

## Summary: Files Affected by Import Issues

### Must Be Fixed (Breaking Imports):
1. ❌ `/home/user/Socrates2/backend/app/agents/socratic.py`
2. ❌ `/home/user/Socrates2/backend/app/agents/conflict_detector.py`
3. ❌ `/home/user/Socrates2/backend/app/agents/quality_controller.py`
4. ❌ `/home/user/Socrates2/backend/app/agents/user_learning.py`
5. ❌ `/home/user/Socrates2/backend/tests/test_library_integration.py`

### Should Be Enhanced (Missing Exports):
6. ⚠️ `/home/user/Socrates2/backend/app/domains/business/__init__.py`
7. ⚠️ `/home/user/Socrates2/backend/app/domains/security/__init__.py`
8. ⚠️ `/home/user/Socrates2/backend/app/domains/devops/__init__.py`
9. ⚠️ `/home/user/Socrates2/backend/app/domains/data_engineering/__init__.py`

### Should Create (Recommended):
10. 🆕 `/home/user/Socrates2/socrates/__init__.py` (public API package)

---

## Solution Approaches

### Approach 1: Create Public `socrates` Package (RECOMMENDED)

**Steps:**
1. Create `/home/user/Socrates2/socrates/` directory
2. Create `/home/user/Socrates2/socrates/__init__.py` with:
   ```python
   """
   Socrates Library - Public API
   
   Re-exports core engines and data models from app.core for external use.
   """
   
   __version__ = "0.1.0"
   
   # Core Engines
   from app.core.question_engine import QuestionGenerator
   from app.core.conflict_engine import ConflictDetectionEngine
   from app.core.quality_engine import BiasDetectionEngine
   from app.core.learning_engine import LearningEngine
   
   # Data Models
   from app.core.models import (
       ProjectData,
       SpecificationData,
       QuestionData,
       ConflictData,
       UserBehaviorData,
       BiasAnalysisResult,
       CoverageAnalysisResult,
       MaturityScore,
   )
   
   # Conversion Functions
   from app.core.models import (
       project_db_to_data,
       spec_db_to_data,
       question_db_to_data,
       conflict_db_to_data,
       specs_db_to_data,
       questions_db_to_data,
       conflicts_db_to_data,
   )
   
   __all__ = [
       "QuestionGenerator",
       "ConflictDetectionEngine",
       "BiasDetectionEngine",
       "LearningEngine",
       "ProjectData",
       "SpecificationData",
       "QuestionData",
       "ConflictData",
       "UserBehaviorData",
       "BiasAnalysisResult",
       "CoverageAnalysisResult",
       "MaturityScore",
       "project_db_to_data",
       "spec_db_to_data",
       "question_db_to_data",
       "conflict_db_to_data",
       "specs_db_to_data",
       "questions_db_to_data",
       "conflicts_db_to_data",
   ]
   ```

3. Update `/home/user/Socrates2/backend/app/__init__.py`:
   ```python
   """
   Socrates Application Package
   Phase 1: Infrastructure Foundation
   """
   
   __version__ = "0.1.0"
   
   # Make socrates library available as app.socrates
   try:
       from ... import socrates
   except ImportError:
       pass  # Development mode without top-level socrates package
   ```

**Advantages:**
- ✅ Fixes all 5 failing import files
- ✅ Supports all 28 tests
- ✅ Creates clean public API boundary
- ✅ Follows library extraction pattern
- ✅ Prepares for future separate `socrates-ai` package

---

### Approach 2: Update Imports in Agent Files (ALTERNATIVE)

**Replace all imports:**
- `from socrates import X` → `from app.core.question_engine import X`
- `from socrates import Y` → `from app.core.models import Y`

**Files to Update:**
1. `app/agents/socratic.py` - 4 imports to fix
2. `app/agents/conflict_detector.py` - 2 imports to fix
3. `app/agents/quality_controller.py` - 2 imports to fix
4. `app/agents/user_learning.py` - 1 import to fix
5. `tests/test_library_integration.py` - 28 test assertions to fix

**Disadvantages:**
- ❌ More scattered imports (less centralized)
- ❌ Harder to future library extraction
- ❌ Requires updating test file (28 tests)

---

### Approach 3: Hybrid (BEST PRACTICE)

1. Create public `socrates` package (Approach 1)
2. Keep internal `app.core.*` implementations as-is
3. Agents import from public `socrates` package
4. This maintains clean architecture:
   - Internal: `app.core.*` (implementation)
   - Public: `socrates.*` (API)
   - Tests: Can import from both

**Result:**
- ✅ Works with current code (needs no agent fixes)
- ✅ Works with test library integration (passes all 28 tests)
- ✅ Prepares for extraction to separate `socrates-ai` PyPI package
- ✅ Maintains clean internal/public separation


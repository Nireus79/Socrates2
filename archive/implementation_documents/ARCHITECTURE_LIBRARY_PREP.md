# 🏗️ ARCHITECTURE PREPARATION FOR LIBRARY EXTRACTION

**Strategy:** Prepare for library extraction during optimization work (not afterward)
**Status:** Phase planning document
**Timeline:** Parallel with optimization work (no additional effort)

---

## EXECUTIVE SUMMARY

By making **3 key architectural changes during optimization**, we achieve:
- ✅ Better performing code (optimization goal)
- ✅ Cleaner separation of concerns (library-ready goal)
- ✅ Easier to extract core logic later (no rework needed)
- ✅ No additional work beyond optimization plan

**Key Insight:** The optimization work and library-extraction work **align perfectly**. We're already removing coupling and dependencies during optimization.

---

## THE ALIGNMENT

### What Optimization Wants
- Remove API calls from DB transactions
- Reduce code duplication
- Separate concerns (API layer vs. business logic)
- Better error handling
- Clear interfaces

### What Library Extraction Wants
- Remove database dependencies from core logic
- Remove API/FastAPI dependencies from core logic
- Separate concerns (core engine vs. app orchestration)
- Better error handling
- Clear interfaces

### Realization
**These are the same things!**

Architecture preparation adds almost zero extra effort—just do optimization with library extraction in mind.

---

## 3 KEY ARCHITECTURAL CHANGES

### CHANGE 1: Extract Core Logic into Pure Modules

**Current Problem:**
```python
# backend/app/agents/socratic.py (monolithic)
class SocraticCounselorAgent(BaseAgent):
    def _generate_question(self, data):
        # Query database
        db = self.services.get_database_specs()
        project = db.query(Project)...  # ← DB dependency

        # Call Claude
        response = self.services.get_claude_client().messages.create(...)  # ← API dependency

        # Parse response
        # Save to database
        # Call other agents
```

**Library-Ready Solution:**
```python
# backend/app/core/question_engine.py (PURE LOGIC - NO DEPENDENCIES)
class QuestionGenerator:
    """Core question generation logic - database/API agnostic"""

    def __init__(self, config: QuestioningConfig = None):
        self.config = config or QuestioningConfig()

    def select_category(
        self,
        coverage: Dict[str, float]
    ) -> str:
        """Select next category (pure logic, no I/O)"""
        return min(coverage, key=coverage.get)

    def build_context(
        self,
        project: ProjectData,  # ← Plain dataclass, not DB model
        specs: List[SpecificationData],
        learning_profile: Dict
    ) -> QuestionContext:
        """Build context for question generation (pure logic)"""
        return QuestionContext(
            project=project,
            specs=specs,
            learning_profile=learning_profile
        )

# backend/app/agents/socratic.py (ORCHESTRATION - HANDLES I/O)
class SocraticCounselorAgent(BaseAgent):
    def __init__(self, ...):
        self.engine = QuestionGenerator()  # ← Core engine

    def _generate_question(self, data: Dict) -> Dict:
        # PHASE 1: Load data from database
        db = self.services.get_database_specs()
        project_db = db.query(Project).filter(...).first()
        specs_db = db.query(Specification).filter(...).all()

        # Convert to plain data objects (for library)
        project_data = ProjectData(
            id=str(project_db.id),
            name=project_db.name,
            ...
        )
        specs_data = [SpecificationData(...) for s in specs_db]

        # PHASE 2: Use core engine (pure logic)
        context = self.engine.build_context(project_data, specs_data, learning_profile)
        category = self.engine.select_category(coverage)

        # PHASE 3: Call Claude API
        response = self.services.get_claude_client().messages.create(...)

        # PHASE 4: Save to database
        question = Question(...)
        db.add(question)
        db.commit()
```

**File Structure Created:**
```
backend/
├── app/
│   ├── core/                           ← NEW: Pure logic modules
│   │   ├── question_engine.py          ← Extracted from socratic.py
│   │   ├── conflict_engine.py          ← Extracted from conflict_detector.py
│   │   ├── quality_engine.py           ← Extracted from quality_controller.py
│   │   ├── learning_engine.py          ← Extracted from user_learning.py
│   │   ├── nlu_engine.py               ← Extracted from nlu_service.py
│   │   └── models.py                   ← Plain dataclasses (library-agnostic)
│   │
│   ├── agents/                         ← MODIFIED: Now thin orchestration layer
│   │   ├── socratic.py                 ← Uses question_engine.py
│   │   ├── conflict_detector.py        ← Uses conflict_engine.py
│   │   ├── quality_controller.py       ← Uses quality_engine.py
│   │   └── ...
│   │
│   └── ...
```

**Benefits:**
- ✅ Core logic reusable without database
- ✅ Easier to test (pure functions)
- ✅ Easier to optimize (no I/O side effects)
- ✅ Clear library extraction path
- ✅ Agents become thin orchestration layer

---

### CHANGE 2: Standardize Data Models (Library-Agnostic)

**Current Problem:**
```python
# Core logic uses SQLAlchemy models
from ..models.specification import Specification  # ← DB model

def analyze_specs(specs: List[Specification]):  # ← Tied to DB
    ...
```

**Library-Ready Solution:**

Create `backend/app/core/models.py` with plain dataclasses:
```python
# backend/app/core/models.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

# ===== LIBRARY-AGNOSTIC DATA MODELS =====
# These can be copied directly into socrates-core library

@dataclass
class ProjectData:
    """Plain project data (not a database model)"""
    id: str
    name: str
    description: str
    current_phase: str
    maturity_score: float
    user_id: str

@dataclass
class SpecificationData:
    """Plain specification data"""
    id: str
    category: str
    key: str
    value: str
    confidence: float
    source: str = 'user_input'

@dataclass
class QuestionData:
    """Plain question data"""
    id: str
    text: str
    category: str
    context: str
    quality_score: float

@dataclass
class ConflictData:
    """Plain conflict data"""
    id: str
    type: str
    severity: str
    description: str
    spec1_id: str
    spec2_id: str

@dataclass
class UserBehaviorData:
    """Plain user behavior data"""
    user_id: str
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence: float

# ===== CONVERSION FUNCTIONS =====
# Bridge between DB models and plain data

def db_project_to_data(project: 'Project') -> ProjectData:
    """Convert SQLAlchemy Project to plain ProjectData"""
    return ProjectData(
        id=str(project.id),
        name=project.name,
        description=project.description,
        current_phase=project.current_phase,
        maturity_score=float(project.maturity_score),
        user_id=str(project.user_id)
    )

def db_specification_to_data(spec: 'Specification') -> SpecificationData:
    """Convert SQLAlchemy Specification to plain SpecificationData"""
    return SpecificationData(
        id=str(spec.id),
        category=spec.category,
        key=spec.key,
        value=spec.value,
        confidence=float(spec.confidence),
        source=spec.source
    )
```

**Usage in Agents:**
```python
# backend/app/agents/socratic.py
from ..core.models import ProjectData, SpecificationData, db_project_to_data, db_specification_to_data
from ..core.question_engine import QuestionGenerator

class SocraticCounselorAgent(BaseAgent):
    def _generate_question(self, data: Dict) -> Dict:
        db = self.services.get_database_specs()

        # Load from database
        project_db = db.query(Project).filter(...).first()
        specs_db = db.query(Specification).filter(...).all()

        # Convert to plain data (agnostic of database)
        project = db_project_to_data(project_db)
        specs = [db_specification_to_data(s) for s in specs_db]

        # Use core engine (works with plain data)
        engine = QuestionGenerator()
        question = engine.generate(
            project=project,
            specs=specs,
            focus_category='requirements'
        )

        # Save to database (app-specific)
        db.add(Question(...))
```

**Library Path (Later):**
```python
# When library is extracted, it includes:
# - Core business logic
# - Plain dataclasses (ProjectData, SpecificationData, etc.)
# - No database models
# - No SQLAlchemy dependency

# Users of library:
from socrates_core.models import ProjectData, SpecificationData
from socrates_core.questioning import QuestionGenerator

# Can work with ANY data source (database, API, file, etc.)
engine = QuestionGenerator()
question = engine.generate(
    project=my_project_data,
    specs=my_specs_data
)
```

**Benefits:**
- ✅ Core logic doesn't depend on SQLAlchemy
- ✅ Easy to extract (just copy models.py and core/)
- ✅ Works with any data source
- ✅ Better decoupling in Socrates
- ✅ Easier to test

---

### CHANGE 3: Create Clear Service Interfaces

**Current Problem:**
```python
# Agents directly import and call other agents
from .quality_controller import QualityControllerAgent
from .conflict_detector import ConflictDetectorAgent
from .user_learning import UserLearningAgent

# No clear interface - high coupling
```

**Library-Ready Solution:**

Create explicit interfaces for services:

```python
# backend/app/core/services.py
"""Service interfaces for core functionality"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..core.models import QuestionData, ConflictData, BiasResult

# ===== SERVICE INTERFACES =====
# Clear contracts for library integration

class IQualityService(ABC):
    """Interface for quality control services"""

    @abstractmethod
    def analyze_question_bias(self, question: str) -> BiasResult:
        """Analyze question for bias"""
        pass

    @abstractmethod
    def analyze_coverage(self, specs: List) -> CoverageResult:
        """Analyze specification coverage"""
        pass

class IConflictService(ABC):
    """Interface for conflict detection"""

    @abstractmethod
    def detect_conflicts(self, specs: List) -> List[ConflictData]:
        """Detect conflicts between specifications"""
        pass

class ILearningService(ABC):
    """Interface for user learning tracking"""

    @abstractmethod
    def track_question_effectiveness(self, effectiveness_data: Dict) -> Dict:
        """Track how effective a question was"""
        pass

class INLUService(ABC):
    """Interface for natural language understanding"""

    @abstractmethod
    def parse_intent(self, text: str) -> Dict:
        """Parse user intent from text"""
        pass

# ===== IMPLEMENTATION (In Socrates) =====

from .orchestrator import get_orchestrator

class OrchestrationQualityService(IQualityService):
    """Quality service using agent orchestration"""

    def analyze_question_bias(self, question: str) -> BiasResult:
        orchestrator = get_orchestrator()
        result = orchestrator.route_request(
            'quality',
            'analyze_question',
            {'question_text': question}
        )
        return BiasResult(**result)

    def analyze_coverage(self, specs: List) -> CoverageResult:
        # ...
        pass
```

**Usage with Dependency Injection:**
```python
# backend/app/core/dependencies.py

class ServiceContainer:
    def __init__(self, ...):
        self.quality_service: IQualityService = OrchestrationQualityService()
        self.conflict_service: IConflictService = OrchestrationConflictService()
        self.learning_service: ILearningService = OrchestrationLearningService()
        self.nlu_service: INLUService = OrchestrationNLUService()

    def get_quality_service(self) -> IQualityService:
        return self.quality_service

# In agents:
class SocraticCounselorAgent(BaseAgent):
    def __init__(self, agent_id, name, services: ServiceContainer):
        self.quality_service = services.get_quality_service()

    def _generate_question(self, data):
        # Use service (no direct agent coupling)
        bias_result = self.quality_service.analyze_question_bias(question_text)
```

**Library Path (Later):**
```python
# Library can implement these interfaces differently
from socrates_core.services import IQualityService, IConflictService

class LocalQualityService(IQualityService):
    """Quality service using local analysis (no API calls)"""
    def analyze_question_bias(self, question: str):
        # Pure local analysis
        pass

# Users inject their own implementation
services = ServiceContainer(
    quality_service=LocalQualityService(),
    conflict_service=LocalConflictService()
)
```

**Benefits:**
- ✅ Clear service contracts
- ✅ Easy to mock for testing
- ✅ Easy to swap implementations
- ✅ Decouples agents from each other
- ✅ Perfect for library integration

---

## IMPLEMENTATION DURING OPTIMIZATION

### Timeline Integration

**Week 1: Critical Fixes + Architecture Prep**
- Do optimization critical fixes
- Create `backend/app/core/question_engine.py` (extracted from socratic.py)
- Create `backend/app/core/models.py` (plain dataclasses)
- Create `backend/app/core/services.py` (service interfaces)

**Week 2: High-Impact Optimizations + More Extraction**
- Refactor socratic.py to use question_engine
- Refactor conflict_detector.py similarly
- Refactor quality_controller.py similarly
- Create conversion functions (db model → plain data)

**Week 3-4: Medium-Impact + Full Integration**
- Refactor remaining agents
- Implement dependency injection
- Test all agent interactions

**Result:** By end of optimization, architecture is **library-ready**.

---

## SPECIFIC FILES TO CREATE/MODIFY

### NEW FILES (Library-Ready Components)

```
backend/app/core/
├── question_engine.py          ← NEW: Pure question logic
├── conflict_engine.py          ← NEW: Pure conflict logic
├── quality_engine.py           ← NEW: Pure quality logic
├── learning_engine.py          ← NEW: Pure learning logic
├── nlu_engine.py               ← NEW: Pure NLU logic
├── models.py                   ← NEW: Plain dataclasses
└── services.py                 ← NEW: Service interfaces
```

### MODIFIED FILES (Remove Dependencies)

```
backend/app/agents/
├── socratic.py                 ← REFACTOR: Use question_engine
├── conflict_detector.py        ← REFACTOR: Use conflict_engine
├── quality_controller.py       ← REFACTOR: Use quality_engine
├── user_learning.py            ← REFACTOR: Use learning_engine
└── nlu_service.py              ← Already extracted
```

---

## QUICK WIN: Preparation Checklist

During optimization, for each optimization you do:

- [ ] **Separate I/O from Logic:** Extract pure logic to `core/` module
- [ ] **Use Plain Data:** Convert DB models to dataclasses before passing to logic
- [ ] **Define Interface:** Create service interface for the component
- [ ] **Test Independently:** Add tests for pure logic (no database)

### Example: Optimize Maturity Calculation

```python
# STEP 1: Extract pure logic
# backend/app/core/quality_engine.py
class MaturityCalculator:
    def calculate_delta(self, new_specs: List[SpecificationData], current_score: float) -> float:
        # Pure logic - no database access
        ...

# STEP 2: Use in agent
# backend/app/agents/context.py
calculator = MaturityCalculator()
delta = calculator.calculate_delta(new_specs_data, current_score)

# STEP 3: Write tests (no database needed)
def test_maturity_calculation():
    calc = MaturityCalculator()
    result = calc.calculate_delta([spec1, spec2], 25.0)
    assert result == expected_delta
```

---

## ESTIMATING EFFORT

**Extra Work Beyond Optimization:** ~0 hours
**Why:** You're refactoring the same code

**Breakdown:**
- Creating service interfaces: (included in code cleanup)
- Extracting pure logic: (included in optimization)
- Creating dataclasses: (included in refactoring)
- Writing tests: (part of quality gates)

**Actual Extra Work:** Just being mindful during optimization (no code duplication)

---

## RESULTING ARCHITECTURE

After optimization WITH library-readiness preparation:

```
┌─────────────────────────────────────────┐
│   Socrates Application Layer (FastAPI) │
│  ┌──────────────────────────────────┐  │
│  │  API Endpoints (sessions, etc.)  │  │
│  └────────────────┬─────────────────┘  │
└───────────────────┼──────────────────────┘
                    │
┌───────────────────▼──────────────────────┐
│   Agent Orchestration Layer (Agents)     │
│  ┌──────────────────────────────────┐   │
│  │  Socratic Agent                  │   │
│  │  Conflict Agent                  │   │
│  │  Quality Agent                   │   │
│  │  Learning Agent                  │   │
│  └────────────────┬─────────────────┘   │
└───────────────────┼──────────────────────┘
                    │
┌───────────────────▼──────────────────────┐
│   Service Layer (Pure Logic)             │
│  ┌──────────────────────────────────┐   │
│  │  IQuestionService                │   │
│  │  IConflictService                │   │
│  │  IQualityService                 │   │
│  │  ILearningService                │   │
│  │  INLUService                     │   │
│  └────────────────┬─────────────────┘   │
└───────────────────┼──────────────────────┘
                    │
┌───────────────────▼──────────────────────┐
│   Core Engine Layer (LIBRARY READY!)     │
│  ┌──────────────────────────────────┐   │
│  │  QuestionGenerator               │   │
│  │  ConflictDetector                │   │
│  │  QualityAnalyzer                 │   │
│  │  LearningEngine                  │   │
│  │  NLUEngine                       │   │
│  │                                  │   │
│  │  Plain Data Models               │   │
│  │  (ProjectData, SpecData, etc.)   │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

**What Can Be Extracted into Library:**
- Core Engine Layer (100%)
- Data Models (100%)
- Service Interfaces (100%)

**What Stays in Socrates:**
- API endpoints
- Agent orchestration
- Database layer
- Authentication

---

## BENEFITS SUMMARY

### Immediate (During Optimization)
✅ Better code organization
✅ Easier to test
✅ Cleaner separation of concerns
✅ No additional complexity

### Medium-term (Library Extraction)
✅ Zero rework needed
✅ Clean library boundaries already defined
✅ Just copy-paste core/ to socrates-core/
✅ Tested code ready to ship

### Long-term (Ecosystem)
✅ Multiple implementations (local, cloud, hybrid)
✅ Language bindings easier (clear API boundary)
✅ Third-party integrations simpler
✅ Product differentiation (strategic value, not just code)

---

## DECISION POINT

### Option A: Do Optimization + Prepare for Library (RECOMMENDED)
- Same effort as just optimization
- Ends with library-ready code
- Zero rework needed later
- Cleaner architecture

### Option B: Do Optimization Only
- Slightly less refactoring
- Will need rework for library extraction
- More technical debt later
- Miss the alignment opportunity

**Recommendation:** **Option A - Prepare for library during optimization**

The alignment is too perfect to pass up. You're doing the refactoring anyway—just structure it for library extraction.

---

## NEXT STEPS

1. **Review this guide** with your architecture lead
2. **Decide:** Do full prep (Option A) or light optimization (Option B)
3. **If Option A:** Add this architectural work to optimization plan
4. **If Option B:** Keep this guide for future reference when extracting library

**Estimated Timeline Shift:**
- Option A: +0 hours (same work, better structured)
- Option B: +20-30 hours (when library extraction happens later)

---

**Document Type:** Strategy & Architecture Guide
**Status:** Ready for Decision
**Confidence:** High (Optimization + Library prep are aligned)
**Next Action:** Team review and decision on approach

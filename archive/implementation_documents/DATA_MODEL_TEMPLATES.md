# 📋 DATA MODEL TEMPLATES

**Quick Reference for Library-Ready Development**
**Use these templates when creating core modules during optimization**

---

## Overview

When creating `backend/app/core/` modules (question_engine, conflict_engine, etc.):
- Use **dataclass models** instead of SQLAlchemy models
- Models should be **database-agnostic**
- This enables library extraction with zero rework
- **Zero performance overhead** - just a different data structure

---

## Core Data Models

### ProjectData
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectData:
    """Plain project data - used by core engines"""
    id: str
    name: str
    description: str
    current_phase: str  # 'discovery', 'design', 'implementation', etc.
    maturity_score: float  # 0-100
    user_id: str
    created_at: Optional[str] = None  # ISO format if needed
    updated_at: Optional[str] = None
```

**Used By:**
- QuestionGenerator
- MaturityCalculator
- QualityAnalyzer

---

### SpecificationData
```python
from dataclasses import dataclass

@dataclass
class SpecificationData:
    """Plain specification data"""
    id: str
    project_id: str
    category: str  # 'goals', 'requirements', 'tech_stack', etc.
    key: str  # e.g., 'framework'
    value: str  # e.g., 'FastAPI'
    confidence: float  # 0.0-1.0
    source: str = 'user_input'  # 'user_input', 'extracted', 'imported'
    is_current: bool = True
```

**Used By:**
- ConflictDetector
- CoverageAnalyzer
- MaturityCalculator
- QuestionGenerator (for context)

---

### QuestionData
```python
from dataclasses import dataclass

@dataclass
class QuestionData:
    """Plain question data"""
    id: str
    text: str
    category: str  # 'goals', 'requirements', etc.
    context: str  # Why this question matters
    quality_score: float  # 0.0-1.0 (1.0 = no bias)
```

**Used By:**
- QuestionGenerator
- BiasDetector
- EffectivenessTracker

---

### ConflictData
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConflictData:
    """Plain conflict data"""
    id: str
    type: str  # 'contradiction', 'inconsistency', 'dependency'
    severity: str  # 'low', 'medium', 'high'
    description: str
    spec1_id: str
    spec2_id: str
    resolution_suggestion: Optional[str] = None
```

**Used By:**
- ConflictDetector
- ConflictResolver

---

### BiasAnalysisResult
```python
from dataclasses import dataclass
from typing import List

@dataclass
class BiasAnalysisResult:
    """Result of bias analysis"""
    bias_score: float  # 0.0 (no bias) to 1.0 (extreme bias)
    bias_types: List[str]  # ['solution_bias', 'leading_question', etc.]
    is_blocking: bool  # True if score > 0.5
    reason: Optional[str] = None  # Why it's blocked
    suggested_alternatives: List[str] = None  # Better question alternatives
```

**Used By:**
- BiasDetector
- QuestionValidator

---

### CoverageAnalysisResult
```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class CoverageAnalysisResult:
    """Result of coverage analysis"""
    coverage_score: float  # 0.0-1.0 (percentage)
    coverage_by_category: Dict[str, int]  # {'goals': 5, 'requirements': 8, ...}
    gaps: List[str]  # Categories with insufficient specs
    is_sufficient: bool  # True if score >= 0.7
    suggested_actions: List[str] = None  # What to ask next
```

**Used By:**
- CoverageAnalyzer
- MaturityCalculator

---

### UserBehaviorData
```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class UserBehaviorData:
    """User learning profile data"""
    user_id: str
    total_questions_asked: int
    overall_response_quality: float  # 0.0-1.0
    patterns: Dict[str, Any]  # {'communication_style': 'detailed', ...}
    learned_from_projects: int  # Number of projects analyzed
```

**Used By:**
- QuestionGenerator (for personalization)
- BehaviorAnalyzer
- EffectivenessTracker

---

## Conversion Functions

These convert between database models and plain data.
Keep these at the API/Agent layer, NOT in core engines.

```python
# backend/app/core/models.py

from ..models.project import Project  # SQLAlchemy model
from ..models.specification import Specification
from ..models.question import Question

def project_db_to_data(db_project: Project) -> ProjectData:
    """Convert SQLAlchemy Project to ProjectData"""
    return ProjectData(
        id=str(db_project.id),
        name=db_project.name,
        description=db_project.description,
        current_phase=db_project.current_phase,
        maturity_score=float(db_project.maturity_score),
        user_id=str(db_project.user_id),
        created_at=db_project.created_at.isoformat() if db_project.created_at else None,
        updated_at=db_project.updated_at.isoformat() if db_project.updated_at else None
    )

def spec_db_to_data(db_spec: Specification) -> SpecificationData:
    """Convert SQLAlchemy Specification to SpecificationData"""
    return SpecificationData(
        id=str(db_spec.id),
        project_id=str(db_spec.project_id),
        category=db_spec.category,
        key=db_spec.key,
        value=db_spec.value,
        confidence=float(db_spec.confidence),
        source=db_spec.source,
        is_current=db_spec.is_current
    )

def question_db_to_data(db_question: Question) -> QuestionData:
    """Convert SQLAlchemy Question to QuestionData"""
    return QuestionData(
        id=str(db_question.id),
        text=db_question.text,
        category=db_question.category,
        context=db_question.context,
        quality_score=float(db_question.quality_score)
    )

def specs_db_to_data(db_specs: list) -> list:
    """Batch convert specifications"""
    return [spec_db_to_data(s) for s in db_specs]
```

---

## Usage Pattern in Agents

### Example: SocraticCounselorAgent

```python
# backend/app/agents/socratic.py

from ..core.question_engine import QuestionGenerator
from ..core.models import ProjectData, SpecificationData, project_db_to_data, specs_db_to_data

class SocraticCounselorAgent(BaseAgent):
    def __init__(self, ...):
        self.engine = QuestionGenerator()

    def _generate_question(self, data: Dict) -> Dict:
        # PHASE 1: Load from database
        db = self.services.get_database_specs()
        project_db = db.query(Project).filter(...).first()
        specs_db = db.query(Specification).filter(...).all()

        # PHASE 2: Convert to plain data
        project = project_db_to_data(project_db)
        specs = specs_db_to_data(specs_db)

        # PHASE 3: Use core engine (pure logic, no DB)
        question = self.engine.generate(
            project=project,
            specs=specs,
            focus_category='requirements'
        )

        # PHASE 4: Save to database (app-specific)
        db_question = Question(
            project_id=project_db.id,
            text=question.text,
            category=question.category,
            context=question.context,
            quality_score=Decimal(str(question.quality_score))
        )
        db.add(db_question)
        db.commit()

        return {
            'success': True,
            'question': {
                'id': str(db_question.id),
                'text': db_question.text,
                'category': db_question.category
            }
        }
```

**Pattern:**
1. Load DB models
2. Convert to plain data
3. Pass to core engine
4. Get plain data back
5. Convert back to DB models (if needed)
6. Save to database

---

## Checklist for Core Module Creation

When creating a new `backend/app/core/` module:

- [ ] Use dataclasses for all data objects
- [ ] No SQLAlchemy imports in core module
- [ ] Accept plain data (ProjectData, SpecificationData, etc.)
- [ ] Return plain data
- [ ] Pure logic only (no I/O, no API calls)
- [ ] Document assumptions in docstrings
- [ ] Write unit tests (no database needed)
- [ ] Keep conversion functions at agent/API layer

---

## Library Extraction Reference

When extracting to library later:
1. Copy `backend/app/core/models.py` → `socrates-core/socrates_core/models.py`
2. Copy `backend/app/core/question_engine.py` → `socrates-core/socrates_core/question_engine.py`
3. Copy other core modules similarly
4. Remove conversion functions (they stay in app)
5. Done! No rework needed.

---

## Examples

### Creating a New Core Module

```python
# backend/app/core/maturity_engine.py

from dataclasses import dataclass
from typing import List
from .models import SpecificationData

@dataclass
class MaturityScore:
    """Maturity score calculation result"""
    current_score: float
    delta: float
    new_score: float
    next_category: str

class MaturityCalculator:
    """Calculate project maturity - pure logic, database-agnostic"""

    def calculate_delta(
        self,
        new_specs: List[SpecificationData],
        current_score: float
    ) -> MaturityScore:
        """Calculate maturity score delta from new specs"""
        # Pure logic - no database access
        delta = len(new_specs) * 2.5  # Simplified
        new_score = min(100.0, current_score + delta)

        # Determine next focus area
        if new_score >= 30:
            next_category = 'design'
        else:
            next_category = 'requirements'

        return MaturityScore(
            current_score=current_score,
            delta=delta,
            new_score=new_score,
            next_category=next_category
        )
```

---

## Summary

**Using These Templates:**
- ✅ Zero additional complexity
- ✅ Same code as SQLAlchemy models (just dataclasses)
- ✅ Better separation of concerns
- ✅ Enables library extraction later
- ✅ Easier to test (pure functions)
- ✅ Database-agnostic core logic

**Implementation Time:**
- No extra time during optimization
- Save 20-30 hours during library extraction
- Make code cleaner and more testable

**Recommendation:**
Use these templates whenever creating `backend/app/core/` modules during optimization work.
It's the right architecture anyway, and enables library extraction as a bonus.

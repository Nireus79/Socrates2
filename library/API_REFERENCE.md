# Socrates Library - API Reference

**Version:** 0.2.0
**Status:** Phase 1a - Pure Logic Engines (No configuration required)

## Overview

The Socrates library provides pure business logic engines for Socratic learning systems. Phase 1a exports are production-ready and require no database or environment configuration.

## Table of Contents

- [Pure Business Logic Engines](#pure-business-logic-engines)
- [Data Models](#data-models)
- [Enums & Constants](#enums--constants)
- [Conversion Functions](#conversion-functions)
- [Quick Start](#quick-start)

---

## Pure Business Logic Engines

### QuestionGenerator

Generate Socratic questions to guide users through requirements gathering.

```python
from socrates import QuestionGenerator, QUESTION_CATEGORIES

# Create generator
qgen = QuestionGenerator()

# Available question categories
print(QUESTION_CATEGORIES)  # ['functional', 'performance', 'security', ...]

# Generate questions
gaps = ['authentication', 'data_persistence']
questions = qgen.generate(gaps, category='security')
```

**Methods:**

- `generate(gaps: List[str], category: str = None) -> List[str]`
  - Generates questions for identified specification gaps
  - Args:
    - `gaps`: List of gap areas (e.g., 'authentication', 'performance')
    - `category`: Optional specific category ('functional', 'security', 'performance', etc.)
  - Returns: List of generated Socratic questions

- `calculate_coverage(answers: List[str]) -> float`
  - Calculates coverage percentage (0-100) of gathered requirements

- `identify_gaps(spec_text: str) -> List[str]`
  - Identifies what areas are missing from current specification

**Constants:**

- `QUESTION_CATEGORIES`: List of available question categories
- `CATEGORY_TARGETS`: Dict mapping categories to target question counts

---

### ConflictDetectionEngine

Identify and classify conflicts in specifications and requirements.

```python
from socrates import ConflictDetectionEngine, ConflictType, ConflictSeverity

# Create engine (claude_client is optional)
engine = ConflictDetectionEngine(claude_client=None)

# Detect conflicts
specs = ["requirement1", "requirement2", ...]
conflicts = engine.detect_conflicts(specs)

# Check conflict types
for conflict in conflicts:
    print(f"Type: {conflict['type']}")  # ConflictType enum value
    print(f"Severity: {conflict['severity']}")  # ConflictSeverity enum value
```

**Enums:**

- `ConflictType`: CONTRADICTION, INCONSISTENCY, DEPENDENCY, REDUNDANCY
- `ConflictSeverity`: LOW, MEDIUM, HIGH

**Methods:**

- `detect_conflicts(specifications: List[str]) -> List[Dict]`
  - Detects conflicts between specifications
  - Returns: List of conflict dictionaries with type, severity, and details

- `build_conflict_detection_prompt(specs: List[str]) -> str`
  - Builds prompt for Claude to detect conflicts (useful for debugging)

**Factory:**

- `create_conflict_detection_engine(logger=None) -> ConflictDetectionEngine`
  - Creates engine with optional logging

---

### BiasDetectionEngine

Detect biases in questions and specifications.

```python
from socrates import BiasDetectionEngine

# Create engine
bias_engine = BiasDetectionEngine()

# Detect bias in questions
question = "You'll obviously need to use React for the frontend, right?"
bias_result = bias_engine.detect_bias_in_question(question)

# Analyze coverage for bias
specs = ["requirement1", "requirement2", ...]
coverage = bias_engine.analyze_coverage(specs)
```

**Bias Types:**

- `solution_bias`: Suggests specific technology/solution
- `technology_bias`: Assumes specific tech stack
- `leading_question`: Question assumes answer

**Methods:**

- `detect_bias_in_question(question: str) -> BiasAnalysisResult`
  - Analyzes question for biases
  - Returns: BiasAnalysisResult with detected biases and confidence scores

- `analyze_coverage(specifications: List[str]) -> CoverageAnalysisResult`
  - Analyzes specification coverage for balanced requirements

---

### LearningEngine

Analyze user learning patterns and predict difficulty levels.

```python
from socrates import LearningEngine, create_learning_engine

# Create engine
learning_engine = LearningEngine()

# Build user profile from answers
user_profile = learning_engine.build_user_profile(
    user_answers=["answer1", "answer2", ...],
    question_history=["q1", "q2", ...]
)

# Predict difficulty of next question
difficulty = learning_engine.predict_difficulty(
    user_profile=user_profile,
    question="new question"
)

# Calculate learning metrics
metrics = learning_engine.calculate_learning_metrics(user_profile)

# Factory method
engine = create_learning_engine(logger=None)
```

**Methods:**

- `build_user_profile(user_answers: List[str], question_history: List[str]) -> UserBehaviorData`
  - Creates user learning profile from history

- `predict_difficulty(user_profile: UserBehaviorData, question: str) -> float`
  - Predicts difficulty (0-1 scale) for a question

- `calculate_learning_metrics(user_profile: UserBehaviorData) -> Dict`
  - Returns metrics: comprehension level, learning pace, domain expertise, etc.

---

## Data Models

All data models are plain Python dataclasses with no database dependencies.

### ProjectData

```python
from socrates import ProjectData

project = ProjectData(
    id="proj-123",
    name="Mobile App",
    description="A mobile app for iOS and Android",
    user_id="user-456",
    current_phase=1,
    maturity_score=0.45,
    created_at="2025-01-01T00:00:00",
    updated_at="2025-01-02T00:00:00"
)

print(project.name)  # "Mobile App"
print(project.maturity_score)  # 0.45
```

**Fields:**
- `id: str` - Unique identifier
- `name: str` - Project name
- `description: str` - Project description
- `user_id: str` - Owner user ID
- `current_phase: int` - Current project phase (1-5)
- `maturity_score: float` - Overall maturity (0-1)
- `created_at: str` - ISO format timestamp
- `updated_at: str` - ISO format timestamp

---

### SpecificationData

```python
from socrates import SpecificationData

spec = SpecificationData(
    id="spec-123",
    project_id="proj-123",
    content="Security must use OAuth 2.0",
    version=1,
    category="security",
    created_at="2025-01-01T00:00:00"
)
```

**Fields:**
- `id: str` - Unique identifier
- `project_id: str` - Parent project ID
- `content: str` - Specification content
- `version: int` - Version number
- `category: str` - Category (e.g., 'security', 'performance')
- `created_at: str` - ISO format timestamp

---

### QuestionData

```python
from socrates import QuestionData

question = QuestionData(
    id="q-123",
    project_id="proj-123",
    content="What are your authentication requirements?",
    category="security",
    created_at="2025-01-01T00:00:00"
)
```

**Fields:**
- `id: str` - Unique identifier
- `project_id: str` - Parent project ID
- `content: str` - Question text
- `category: str` - Question category
- `created_at: str` - ISO format timestamp

---

### ConflictData

```python
from socrates import ConflictData, ConflictType, ConflictSeverity

conflict = ConflictData(
    id="cf-123",
    project_id="proj-123",
    type=ConflictType.CONTRADICTION,
    severity=ConflictSeverity.HIGH,
    description="Specs contradict each other",
    created_at="2025-01-01T00:00:00"
)
```

**Fields:**
- `id: str` - Unique identifier
- `project_id: str` - Parent project ID
- `type: ConflictType` - Type of conflict
- `severity: ConflictSeverity` - Conflict severity
- `description: str` - Detailed description
- `created_at: str` - ISO format timestamp

---

### BiasAnalysisResult

```python
from socrates import BiasAnalysisResult

result = BiasAnalysisResult(
    question_id="q-123",
    has_bias=True,
    bias_types=["solution_bias", "technology_bias"],
    confidence=0.85,
    suggestion="Rephrase to avoid assuming React.js"
)
```

**Fields:**
- `question_id: str` - ID of analyzed question
- `has_bias: bool` - Whether bias detected
- `bias_types: List[str]` - Types of detected biases
- `confidence: float` - Confidence score (0-1)
- `suggestion: str` - Suggested improvement

---

### CoverageAnalysisResult

```python
from socrates import CoverageAnalysisResult

coverage = CoverageAnalysisResult(
    coverage_percentage=75.0,
    missing_areas=["security", "compliance"],
    recommendations=["Add security requirements", "Define compliance needs"]
)
```

**Fields:**
- `coverage_percentage: float` - Coverage % (0-100)
- `missing_areas: List[str]` - Identified gaps
- `recommendations: List[str]` - Suggestions for improvement

---

### MaturityScore

```python
from socrates import MaturityScore

score = MaturityScore(
    overall=0.65,
    functional=0.80,
    performance=0.55,
    security=0.70,
    usability=0.60
)

print(f"Overall maturity: {score.overall}")  # 0.65
```

**Fields:**
- `overall: float` - Overall maturity (0-1)
- `functional: float` - Functional requirements maturity
- `performance: float` - Performance requirements maturity
- `security: float` - Security requirements maturity
- `usability: float` - Usability requirements maturity

---

### UserBehaviorData

```python
from socrates import UserBehaviorData

profile = UserBehaviorData(
    user_id="user-123",
    comprehension_level=0.72,
    learning_pace="moderate",
    domain_expertise="intermediate",
    question_response_time_avg=45.5
)
```

**Fields:**
- `user_id: str` - User identifier
- `comprehension_level: float` - Understanding level (0-1)
- `learning_pace: str` - Pace: 'slow', 'moderate', 'fast'
- `domain_expertise: str` - Level: 'beginner', 'intermediate', 'expert'
- `question_response_time_avg: float` - Average response time (seconds)

---

## Enums & Constants

### QUESTION_CATEGORIES

```python
from socrates import QUESTION_CATEGORIES, CATEGORY_TARGETS

# Available categories
print(QUESTION_CATEGORIES)
# ['functional', 'performance', 'security', 'usability', 'accessibility', 'compliance', 'scalability', 'maintenance']

# Target questions per category
print(CATEGORY_TARGETS)
# {'functional': 5, 'performance': 3, 'security': 4, ...}
```

---

### ConflictType

```python
from socrates import ConflictType

# Conflict types
ConflictType.CONTRADICTION    # Requirements contradict each other
ConflictType.INCONSISTENCY    # Inconsistent specification details
ConflictType.DEPENDENCY       # Unmet dependencies between requirements
ConflictType.REDUNDANCY       # Duplicate or redundant requirements
```

---

### ConflictSeverity

```python
from socrates import ConflictSeverity

# Severity levels
ConflictSeverity.LOW           # Minor issue, can be ignored
ConflictSeverity.MEDIUM        # Should be addressed
ConflictSeverity.HIGH          # Must be resolved before proceeding
```

---

## Conversion Functions

Convert between database models and plain dataclasses.

### project_db_to_data()

```python
from socrates import project_db_to_data

# Convert SQLAlchemy Project model to ProjectData
project_data = project_db_to_data(db_project)

print(project_data.name)
print(type(project_data))  # <class 'socrates.ProjectData'>
```

---

### spec_db_to_data()

```python
from socrates import spec_db_to_data

spec_data = spec_db_to_data(db_specification)
```

---

### question_db_to_data()

```python
from socrates import question_db_to_data

question_data = question_db_to_data(db_question)
```

---

### conflict_db_to_data()

```python
from socrates import conflict_db_to_data

conflict_data = conflict_db_to_data(db_conflict)
```

---

### Batch Conversion Functions

```python
from socrates import specs_db_to_data, questions_db_to_data, conflicts_db_to_data

# Convert lists of DB models
spec_list = specs_db_to_data(db_specs)
question_list = questions_db_to_data(db_questions)
conflict_list = conflicts_db_to_data(db_conflicts)
```

---

## Quick Start

### Installation

```bash
pip install socrates-ai
```

### Basic Usage

```python
from socrates import (
    QuestionGenerator,
    ConflictDetectionEngine,
    BiasDetectionEngine,
    LearningEngine,
    QUESTION_CATEGORIES
)

# 1. Generate questions for requirements gathering
qgen = QuestionGenerator()
questions = qgen.generate(['authentication', 'performance'])

# 2. Detect conflicts in requirements
conflict_engine = ConflictDetectionEngine()
conflicts = conflict_engine.detect_conflicts(requirements)

# 3. Analyze bias in questions
bias_engine = BiasDetectionEngine()
for q in questions:
    bias_result = bias_engine.detect_bias_in_question(q)
    if bias_result.has_bias:
        print(f"Bias detected: {bias_result.suggestion}")

# 4. Track user learning
learning_engine = LearningEngine()
user_profile = learning_engine.build_user_profile(answers, question_history)
difficulty = learning_engine.predict_difficulty(user_profile, next_question)
```

---

## Phase 1b+ Features (Requires Configuration)

Future phases will include:

- **Phase 1b:** Configuration, Database, Security, JWT
- **Phase 2:** NLU Service, Subscription Management, Rate Limiting
- **Phase 3:** Agents, Domains, Full Framework

To enable Phase 1b+, configure environment variables:
- `DATABASE_URL_AUTH`: PostgreSQL connection string for auth DB
- `DATABASE_URL_SPECS`: PostgreSQL connection string for specs DB
- `SECRET_KEY`: JWT signing key
- `ANTHROPIC_API_KEY`: Claude API key

See `LIBRARY_GUIDE.md` for setup instructions.

---

## Error Handling

```python
from socrates import ConflictDetectionEngine

try:
    engine = ConflictDetectionEngine()
    conflicts = engine.detect_conflicts(specs)
except ValueError as e:
    print(f"Invalid specifications: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Performance Notes

All Phase 1a engines are pure Python with no I/O:
- No database access
- No network calls (unless using Claude for enhanced analysis)
- Fast in-memory operations
- Suitable for CLI, desktop, and server applications

---

## Contributing

Contributions welcome! See the main repository for details.

---

## License

MIT License - See LICENSE file for details

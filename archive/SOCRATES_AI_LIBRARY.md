# Socrates AI Library Extraction & Architecture Guide

**Status:** Planning (Implementation in Phases 3-6)
**Library Name:** `socrates-ai`
**Target:** PyPI package (reusable across projects)
**Timeline:** 6 months (incremental extraction)

---

## Overview

Extract core algorithms from Socrates into a standalone Python library:

```
┌─────────────────────────────────────────┐
│  socrates-ai (PyPI Library)             │
├─────────────────────────────────────────┤
│ - Specification validation              │
│ - Conflict detection & resolution       │
│ - Maturity calculation                  │
│ - Quality metrics                       │
│ - Question generation                   │
│ - Text preprocessing                    │
└─────────────────────────────────────────┘
         ↑
   Used by...
         ↓
┌─────────────────────────────────────────┐
│  Socrates (FastAPI Application)        │
├─────────────────────────────────────────┤
│ - Web server (FastAPI)                  │
│ - Authentication & billing              │
│ - Database models & migrations          │
│ - Admin panel                           │
│ - IDE extensions                        │
│ - Knowledge base & RAG                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Other Applications (future users)      │
├─────────────────────────────────────────┤
│ - CLI tools                             │
│ - Third-party integrations              │
│ - Academic research                     │
│ - Enterprise deployments                │
└─────────────────────────────────────────┘
```

---

## Module Structure

### 1. `socrates_ai.specifications` (Core)

**Purpose:** Specification validation, merging, normalization

```python
from socrates_ai.specifications import (
    Specification,
    SpecificationValidator,
    SpecificationMerger,
    SpecificationDiff,
    SpecificationNormalizer
)

# Validate spec format
validator = SpecificationValidator()
is_valid, errors = validator.validate({
    "key": "authentication",
    "value": "OAuth 2.0",
    "category": "security",
    "content": "Uses OAuth 2.0 for authentication"
})

# Detect conflicts
merger = SpecificationMerger()
merged, conflicts = merger.merge(
    specs_1=[spec1, spec2],
    specs_2=[spec3, spec4]
)

# Calculate diff
differ = SpecificationDiff()
changes = differ.compute_diff(old_spec, new_spec)
# Returns: [{"field": "value", "old": "...", "new": "..."}]
```

**Files to Extract:**
- `backend/app/agents/context.py` → Specification class + extraction logic
- `backend/app/agents/conflict_detector.py` → Conflict detection
- `backend/app/agents/quality_analyzer.py` → Quality checks

---

### 2. `socrates_ai.conflicts` (Algorithms)

**Purpose:** Detect and resolve specification conflicts

```python
from socrates_ai.conflicts import (
    ConflictDetector,
    ConflictResolver,
    ConflictSeverity
)

# Detect conflicts
detector = ConflictDetector()
conflicts = detector.find_conflicts(
    specifications=[spec1, spec2, spec3]
)
# Returns: [
#   {
#       "id": "conflict_1",
#       "type": "contradiction",
#       "specs": [spec1_id, spec2_id],
#       "severity": ConflictSeverity.HIGH,
#       "message": "Authentication method conflicts"
#   }
# ]

# Resolve conflicts
resolver = ConflictResolver()
resolution = resolver.resolve(
    conflict=conflict,
    resolution_strategy="latest"  # or "merge", "manual"
)
```

**Export From:**
- `backend/app/agents/conflict_detector.py` → Full module

---

### 3. `socrates_ai.maturity` (Scoring)

**Purpose:** Calculate project and specification maturity

```python
from socrates_ai.maturity import (
    MaturityCalculator,
    MaturityCategory,
    MaturityLevel
)

# Calculate project maturity
calculator = MaturityCalculator()
maturity_score = calculator.calculate_project(
    specifications=specs,
    weights={
        "completeness": 0.3,
        "consistency": 0.3,
        "clarity": 0.2,
        "accuracy": 0.2
    }
)
# Returns: 73

# Calculate spec maturity
spec_score = calculator.calculate_specification(spec)
# Returns: {
#     "score": 85,
#     "level": MaturityLevel.HIGH,
#     "factors": {
#         "completeness": 90,
#         "clarity": 85,
#         "accuracy": 75
#     }
# }
```

**Export From:**
- `backend/app/agents/maturity_agent.py` → Full module

---

### 4. `socrates_ai.quality` (Analysis)

**Purpose:** Analyze specification quality

```python
from socrates_ai.quality import (
    QualityAnalyzer,
    QualityIssue,
    QualitySuggestion
)

# Analyze quality
analyzer = QualityAnalyzer()
report = analyzer.analyze(specifications=specs)
# Returns: {
#     "overall_score": 78,
#     "issues": [
#         QualityIssue(
#             spec_key="database_schema",
#             issue_type="incomplete",
#             message="Missing schema details",
#             severity="warning"
#         )
#     ],
#     "suggestions": [
#         QualitySuggestion(
#             suggestion="Add performance requirements",
#             spec_key="database_schema"
#         )
#     ]
# }
```

**Export From:**
- `backend/app/agents/quality_analyzer.py` → Quality checking logic

---

### 5. `socrates_ai.questions` (Generation)

**Purpose:** Generate context questions for spec extraction

```python
from socrates_ai.questions import (
    QuestionGenerator,
    Question,
    QuestionType
)

# Generate questions
generator = QuestionGenerator()
questions = generator.generate(
    project_context="Building an e-commerce platform",
    category="database",
    num_questions=5
)
# Returns: [
#     Question(
#         text="What are the key entities in your data model?",
#         type=QuestionType.OPEN_ENDED,
#         priority=1,
#         category="database"
#     ),
#     ...
# ]

# Prioritize questions
prioritized = generator.prioritize_questions(
    existing_specs=specs,
    all_questions=questions
)
# Returns: Sorted by relevance to gaps
```

**Export From:**
- `backend/app/agents/question_generator.py` → Full module

---

### 6. `socrates_ai.utils` (Helpers)

**Purpose:** Common utilities

```python
from socrates_ai.utils import (
    TextNormalizer,
    CategoryClassifier,
    KeyValueExtractor
)

# Normalize text
normalizer = TextNormalizer()
clean_text = normalizer.normalize(text)

# Classify category
classifier = CategoryClassifier()
category = classifier.classify("This is about database schema...")
# Returns: "database"

# Extract key-value pairs
extractor = KeyValueExtractor()
pairs = extractor.extract("Authentication: OAuth 2.0")
# Returns: [{"key": "authentication", "value": "OAuth 2.0"}]
```

**Export From:**
- Various utility functions across codebase

---

## Implementation Timeline

### Phase 3: Initial Structure
- Create `socrates-ai` package skeleton
- Export conflict detection module
- Write comprehensive tests

### Phase 4: Expand Core
- Extract maturity calculation
- Extract specifications validation
- Add documentation examples

### Phase 5: Complete Coverage
- Extract question generation
- Extract quality analysis
- Add integration tests

### Phase 6: Polish & Release
- Optimize performance
- Complete API documentation
- Release v1.0.0 to PyPI

---

## API Design

### 1. Installation
```bash
pip install socrates-ai
```

### 2. Basic Usage
```python
from socrates_ai import (
    SpecificationValidator,
    ConflictDetector,
    MaturityCalculator
)

# Validate specs
validator = SpecificationValidator()
assert validator.validate(spec)

# Detect conflicts
detector = ConflictDetector()
conflicts = detector.find_conflicts(specs)

# Calculate maturity
calculator = MaturityCalculator()
score = calculator.calculate_project(specs)
```

### 3. Advanced Usage
```python
from socrates_ai.specifications import SpecificationMerger
from socrates_ai.conflicts import ConflictResolver

# Merge specs with auto-resolution
merger = SpecificationMerger()
merged, _ = merger.merge(specs1, specs2)

# Resolve conflicts
resolver = ConflictResolver()
resolution = resolver.resolve(
    conflict,
    strategy="intelligent"  # Uses ML if available
)
```

---

## Code Organization

### Library Structure
```
socrates_ai/
├── __init__.py               # Public API exports
├── specifications/
│   ├── __init__.py
│   ├── models.py            # Specification dataclass
│   ├── validator.py         # SpecificationValidator
│   ├── merger.py            # SpecificationMerger
│   ├── differ.py            # SpecificationDiff
│   └── normalizer.py        # SpecificationNormalizer
├── conflicts/
│   ├── __init__.py
│   ├── detector.py          # ConflictDetector
│   ├── resolver.py          # ConflictResolver
│   ├── types.py             # ConflictType, Severity enums
│   └── strategies.py        # Resolution strategies
├── maturity/
│   ├── __init__.py
│   ├── calculator.py        # MaturityCalculator
│   ├── rules.py             # Domain-specific rules
│   └── scoring.py           # Score aggregation
├── quality/
│   ├── __init__.py
│   ├── analyzer.py          # QualityAnalyzer
│   ├── issues.py            # QualityIssue models
│   └── checkers.py          # Individual checkers
├── questions/
│   ├── __init__.py
│   ├── generator.py         # QuestionGenerator
│   ├── prioritizer.py       # QuestionPrioritizer
│   └── templates.py         # Question templates
├── utils/
│   ├── __init__.py
│   ├── text.py              # TextNormalizer
│   ├── classifier.py        # CategoryClassifier
│   └── extraction.py        # KeyValueExtractor
└── tests/
    ├── test_specifications.py
    ├── test_conflicts.py
    ├── test_maturity.py
    ├── test_quality.py
    ├── test_questions.py
    └── test_utils.py
```

### Socrates Usage
```python
from socrates_ai import (
    SpecificationValidator,
    ConflictDetector,
    MaturityCalculator
)

# In backend/app/agents/context.py:
validator = SpecificationValidator()
detector = ConflictDetector()
calculator = MaturityCalculator()

# Use library functions in agent logic
is_valid, errors = validator.validate(spec)
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_specifications.py
def test_validate_valid_spec():
    spec = {
        "key": "auth",
        "value": "OAuth",
        "category": "security"
    }
    validator = SpecificationValidator()
    assert validator.validate(spec)[0] == True

def test_detect_conflict():
    specs = [
        {"key": "db", "value": "PostgreSQL"},
        {"key": "db", "value": "MongoDB"}
    ]
    detector = ConflictDetector()
    conflicts = detector.find_conflicts(specs)
    assert len(conflicts) == 1
```

### Integration Tests
```python
def test_full_workflow():
    # Generate questions
    generator = QuestionGenerator()
    questions = generator.generate(context)

    # Extract specs from answers
    specs = extract_from_answers(questions, answers)

    # Validate specs
    validator = SpecificationValidator()
    assert all(validator.validate(s)[0] for s in specs)

    # Detect conflicts
    detector = ConflictDetector()
    assert len(detector.find_conflicts(specs)) == 0

    # Calculate maturity
    calculator = MaturityCalculator()
    score = calculator.calculate_project(specs)
    assert 0 <= score <= 100
```

### Performance Tests
```python
def test_large_spec_set():
    # Generate 10,000 specs
    specs = generate_random_specs(10000)

    # Measure conflict detection
    detector = ConflictDetector()
    start = time.time()
    conflicts = detector.find_conflicts(specs)
    elapsed = time.time() - start

    # Should complete <5 seconds
    assert elapsed < 5.0
```

---

## Documentation

### README
```markdown
# socrates-ai

Reusable Python library for specification validation, conflict detection,
and quality analysis.

## Installation

pip install socrates-ai

## Quick Start

from socrates_ai import SpecificationValidator

validator = SpecificationValidator()
is_valid, errors = validator.validate(spec)

## Full Documentation

See [docs/](docs/) for comprehensive guides.
```

### API Reference
- Each module has docstrings
- Generated with Sphinx
- Hosted on ReadTheDocs

### Examples
```
examples/
├── basic_validation.py
├── conflict_detection.py
├── maturity_calculation.py
├── question_generation.py
└── integration_example.py
```

---

## Release Strategy

### Version 0.1.0 (Phase 3)
- Conflict detection only
- Basic documentation
- Beta release on PyPI

### Version 0.5.0 (Phase 4-5)
- Add maturity, quality, questions modules
- Comprehensive tests
- Stable API

### Version 1.0.0 (Phase 6)
- Full library functionality
- Production-ready
- Semantic versioning

### Post-1.0
- Community contributions
- Plugin ecosystem
- Alternative implementations (Rust, JavaScript)

---

## Community & Adoption

### Expected Adoption
1. **Socrates internal use** - All agents use library
2. **Open-source users** - CLI tools, research projects
3. **Enterprise customers** - Custom implementations
4. **Competitors** - Better than reimplementing

### Growth Plan
1. **Month 1-3:** Internal use, v0.1 beta
2. **Month 4-6:** Community feedback, v1.0
3. **Month 7-12:** 500+ GitHub stars, 100+ PyPI downloads/day
4. **Year 2:** 1000+ stars, npm/Maven ports

---

## Benefits of Library Extraction

### For Socrates
- ✅ Cleaner codebase (separation of concerns)
- ✅ Faster testing (test algorithms independently)
- ✅ Easier maintenance (bug fixes in one place)
- ✅ Revenue opportunities (paid enterprise plugins)

### For Users
- ✅ Reusable in their own projects
- ✅ No dependency on Socrates web app
- ✅ Community contributions
- ✅ Competitive advantage for AI projects

### For Community
- ✅ Open-source AI toolkit
- ✅ Academic research tool
- ✅ Benchmark for other systems
- ✅ Building block for AI pipelines

---

## Migration Checklist

### Phase 3
- [ ] Create socrates-ai package structure
- [ ] Extract conflict detection module
- [ ] Add unit tests (>80% coverage)
- [ ] Write API documentation
- [ ] Publish v0.1.0 to PyPI (beta)

### Phase 4
- [ ] Extract maturity module
- [ ] Extract specifications module
- [ ] Add integration tests
- [ ] Update documentation with examples
- [ ] Publish v0.5.0 to PyPI

### Phase 5
- [ ] Extract quality module
- [ ] Extract questions module
- [ ] Add performance tests
- [ ] Create examples and tutorials
- [ ] Prepare v1.0.0

### Phase 6
- [ ] Final API review
- [ ] Complete test coverage (>90%)
- [ ] Publish v1.0.0 to PyPI (stable)
- [ ] Create GitHub organization
- [ ] Setup CI/CD for continuous releases

---

## Long-Term Vision

**Year 1:** Stable v1.0 with core modules, 500+ GitHub stars

**Year 2:** Expand to other languages (JavaScript, Go, Rust)

**Year 3:** Socrates ecosystem with plugins and integrations

**Future:** Industry standard for specification analysis and quality metrics

---

## Success Metrics

- [ ] **Adoption:** 100+ external projects using socrates-ai
- [ ] **Community:** 20+ GitHub contributors
- [ ] **Quality:** >90% test coverage
- [ ] **Performance:** Handles 100k specs in <1 second
- [ ] **Documentation:** 100% API coverage
- [ ] **Releases:** Monthly updates in Year 1

# Socrates Library - Usage Examples

Complete examples of using Socrates pure logic engines for Socratic learning systems.

## Table of Contents

1. [Installation](#installation)
2. [Question Generation](#question-generation)
3. [Conflict Detection](#conflict-detection)
4. [Bias Detection](#bias-detection)
5. [Learning Analytics](#learning-analytics)
6. [Full Workflow](#full-workflow)
7. [CLI Example](#cli-example)

---

## Installation

```bash
# Install from PyPI
pip install socrates-ai

# Or install from source
git clone https://github.com/Socrates/socrates-ai.git
cd socrates-ai/backend
pip install -e .
```

### Verify Installation

```python
import socrates
print(f"Socrates version: {socrates.__version__}")
print(f"Available engines: {len(socrates.__all__)} exports")
```

---

## Question Generation

Generate Socratic questions to guide users through requirements gathering.

### Example 1: Generate Questions for Specification Gaps

```python
from socrates import QuestionGenerator, QUESTION_CATEGORIES

# Initialize
qgen = QuestionGenerator()

# Print available categories
print("Question categories:", QUESTION_CATEGORIES)
# Output: ['functional', 'performance', 'security', 'usability', ...]

# Generate questions for identified gaps
gaps = ['authentication', 'data_storage', 'api_security']
questions = qgen.generate(gaps)

for i, q in enumerate(questions, 1):
    print(f"{i}. {q}")

# Output:
# 1. How will users authenticate to your system?
# 2. What data needs to be persisted long-term?
# 3. How will you secure API endpoints from unauthorized access?
# ...
```

### Example 2: Category-Specific Questions

```python
from socrates import QuestionGenerator

qgen = QuestionGenerator()

# Generate only security-focused questions
security_questions = qgen.generate(
    gaps=['authentication', 'data_privacy'],
    category='security'
)

# Generate only performance-related questions
perf_questions = qgen.generate(
    gaps=['response_time', 'concurrent_users'],
    category='performance'
)

print(f"Security questions: {len(security_questions)}")
print(f"Performance questions: {len(perf_questions)}")
```

### Example 3: Coverage Analysis

```python
from socrates import QuestionGenerator

qgen = QuestionGenerator()

# Gather user answers
user_responses = [
    "OAuth 2.0 for authentication",
    "PostgreSQL database",
    "Redis for caching",
    "Need sub-second response times"
]

# Calculate coverage percentage
coverage = qgen.calculate_coverage(user_responses)
print(f"Specification coverage: {coverage}%")

# Identify missing areas
gaps = qgen.identify_gaps("Only have auth and db specs")
print(f"Missing specifications: {gaps}")
# Output: ['performance', 'security', 'scalability', ...]
```

---

## Conflict Detection

Identify and categorize conflicts in requirements and specifications.

### Example 1: Detect Specification Conflicts

```python
from socrates import ConflictDetectionEngine, ConflictType, ConflictSeverity

# Initialize engine
engine = ConflictDetectionEngine(claude_client=None)

# Specifications with conflicts
specs = [
    "System must support unlimited concurrent users",
    "System must run on a single shared server",
    "Response time must be under 100ms for all operations",
    "We'll use a simple SQLite database"
]

# Detect conflicts
conflicts = engine.detect_conflicts(specs)

# Display results
for conflict in conflicts:
    print(f"\nConflict: {conflict['description']}")
    print(f"  Type: {conflict['type']}")
    print(f"  Severity: {conflict['severity']}")
    print(f"  Involved specs: {conflict.get('specs_involved', [])}")

# Output example:
# Conflict: Scalability contradiction
#   Type: ConflictType.CONTRADICTION
#   Severity: ConflictSeverity.HIGH
#   Involved specs: [0, 1]  (unlimited users + single server)
```

### Example 2: Analyze Conflict Types

```python
from socrates import ConflictDetectionEngine, ConflictType, ConflictSeverity

engine = ConflictDetectionEngine()
specs = [...]  # your specifications

conflicts = engine.detect_conflicts(specs)

# Group by severity
high_severity = [c for c in conflicts if c['severity'] == ConflictSeverity.HIGH]
medium_severity = [c for c in conflicts if c['severity'] == ConflictSeverity.MEDIUM]
low_severity = [c for c in conflicts if c['severity'] == ConflictSeverity.LOW]

print(f"High severity conflicts: {len(high_severity)}")
print(f"Medium severity conflicts: {len(medium_severity)}")
print(f"Low severity conflicts: {len(low_severity)}")

# Address high-severity first
for conflict in high_severity:
    print(f"MUST FIX: {conflict['description']}")
```

### Example 3: Use Conflict Detection in Workflow

```python
from socrates import ConflictDetectionEngine

def validate_specifications(specs_list):
    """Validate specifications for conflicts"""
    engine = ConflictDetectionEngine()
    conflicts = engine.detect_conflicts(specs_list)

    if not conflicts:
        print("No conflicts found - specifications are consistent!")
        return True

    print(f"Found {len(conflicts)} conflicts:")
    for c in conflicts:
        print(f"  - {c['description']} (Severity: {c['severity']})")

    return False  # Specifications need review

# Usage
my_specs = [
    "API must be REST",
    "API must use GraphQL",
]

if validate_specifications(my_specs):
    print("Ready to implement!")
else:
    print("Please resolve conflicts first.")
```

---

## Bias Detection

Identify biases in questions and ensure neutral, comprehensive requirements gathering.

### Example 1: Detect Bias in Questions

```python
from socrates import BiasDetectionEngine

bias_engine = BiasDetectionEngine()

# Questions with potential biases
questions = [
    "You'll use React.js for the frontend, right?",  # Technology bias
    "Obviously, you need microservices architecture.",  # Solution bias
    "What are your requirements?",  # Neutral
    "Should we use Kubernetes or Docker Compose?"  # Leading question
]

# Analyze each question
for q in questions:
    result = bias_engine.detect_bias_in_question(q)

    print(f"\nQuestion: {q}")
    print(f"  Has bias: {result.has_bias}")

    if result.has_bias:
        print(f"  Types: {result.bias_types}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Suggestion: {result.suggestion}")
    else:
        print(f"  Neutral question")

# Output example:
# Question: You'll use React.js for the frontend, right?
#   Has bias: True
#   Types: ['technology_bias', 'leading_question']
#   Confidence: 0.95
#   Suggestion: Rephrase to "What are your frontend technology requirements?"
```

### Example 2: Analyze Specification Coverage for Bias

```python
from socrates import BiasDetectionEngine

bias_engine = BiasDetectionEngine()

# Gathered specifications
specifications = [
    "Frontend will use React and TypeScript",
    "Backend will use Python with FastAPI",
    "Database will be PostgreSQL",
    "Will deploy to AWS using Kubernetes"
]

# Analyze coverage
coverage = bias_engine.analyze_coverage(specifications)

print(f"Coverage: {coverage.coverage_percentage}%")
print(f"Missing areas: {coverage.missing_areas}")
print(f"Recommendations:")
for rec in coverage.recommendations:
    print(f"  - {rec}")

# Output example:
# Coverage: 45%
# Missing areas: ['testing_strategy', 'monitoring', 'disaster_recovery', 'security_approach']
# Recommendations:
#   - Define testing strategy (unit, integration, e2e)
#   - Specify monitoring and logging approach
#   - Plan disaster recovery procedures
```

### Example 3: Question Quality Improvement Workflow

```python
from socrates import BiasDetectionEngine, QuestionGenerator

def improve_questions(raw_questions):
    """Remove biases from questions"""
    bias_engine = BiasDetectionEngine()
    improved = []

    for q in raw_questions:
        result = bias_engine.detect_bias_in_question(q)

        if result.has_bias:
            improved.append({
                'original': q,
                'suggestion': result.suggestion,
                'bias_types': result.bias_types
            })
        else:
            improved.append({
                'original': q,
                'suggestion': None,
                'bias_types': []
            })

    return improved

# Usage
raw_qs = [
    "Will you use microservices like everyone else?",
    "What are your performance requirements?",
    "Should we just use MongoDB instead of SQL?"
]

improved_qs = improve_questions(raw_qs)

for item in improved_qs:
    print(f"\nOriginal: {item['original']}")
    if item['suggestion']:
        print(f"Improved: {item['suggestion']}")
    else:
        print(f"Already neutral!")
```

---

## Learning Analytics

Track user learning patterns and personalize question difficulty.

### Example 1: Build User Profile

```python
from socrates import LearningEngine

learning_engine = LearningEngine()

# User's answer history
user_answers = [
    "OAuth 2.0",
    "PostgreSQL with ACID transactions",
    "We need sub-second response times",
    "RESTful API with proper versioning",
    "End-to-end encryption for sensitive data"
]

# Questions asked
questions_asked = [
    "How will users authenticate?",
    "What database will you use?",
    "What are your performance requirements?",
    "API design approach?",
    "Security approach?"
]

# Build profile
profile = learning_engine.build_user_profile(user_answers, questions_asked)

print(f"User comprehension level: {profile.comprehension_level:.2%}")
print(f"Learning pace: {profile.learning_pace}")
print(f"Domain expertise: {profile.domain_expertise}")
print(f"Avg response time: {profile.question_response_time_avg:.1f}s")

# Output example:
# User comprehension level: 78%
# Learning pace: moderate
# Domain expertise: intermediate
# Avg response time: 32.5s
```

### Example 2: Predict Question Difficulty

```python
from socrates import LearningEngine

learning_engine = LearningEngine()

# Assume we have a user profile from previous interaction
profile = learning_engine.build_user_profile(
    user_answers=["OAuth", "PostgreSQL", "REST API"],
    questions_asked=["Auth?", "Database?", "API?"]
)

# Predict difficulty for different questions
questions = [
    "How will you handle distributed transactions?",  # Hard
    "What's your database backup strategy?",  # Medium
    "Will you use a web framework?"  # Easy
]

for q in questions:
    difficulty = learning_engine.predict_difficulty(profile, q)
    level = (
        "Easy" if difficulty < 0.33 else
        "Medium" if difficulty < 0.67 else
        "Hard"
    )
    print(f"'{q[:40]}...' - {level} (difficulty: {difficulty:.2f})")

# Output:
# 'How will you handle distributed transact...' - Hard (difficulty: 0.85)
# 'What's your database backup strategy?...' - Medium (difficulty: 0.52)
# 'Will you use a web framework?...' - Easy (difficulty: 0.18)
```

### Example 3: Calculate Learning Metrics

```python
from socrates import LearningEngine

learning_engine = LearningEngine()

profile = learning_engine.build_user_profile(
    user_answers=["OAuth", "PostgreSQL", "REST", "Docker", "Kubernetes"],
    questions_asked=["Auth?", "DB?", "API?", "Containers?", "Orchestration?"]
)

# Get comprehensive metrics
metrics = learning_engine.calculate_learning_metrics(profile)

print("Learning Metrics:")
for key, value in metrics.items():
    print(f"  {key}: {value}")

# Suggest next questions based on expertise gaps
print("\nSuggested next topics:")
print("  - Security compliance and audit trails")
print("  - Monitoring and observability")
print("  - Disaster recovery planning")
```

---

## Full Workflow

Complete end-to-end workflow using all engines together.

```python
from socrates import (
    QuestionGenerator,
    ConflictDetectionEngine,
    BiasDetectionEngine,
    LearningEngine,
    ProjectData,
    SpecificationData
)

def socratic_requirements_gathering(user_input_function):
    """
    Full workflow for gathering project requirements using Socratic method.

    Handles:
    1. Initial questions generation
    2. Bias detection in user responses
    3. Conflict detection in specifications
    4. Learning analytics tracking
    5. Coverage analysis
    """

    # Initialize engines
    qgen = QuestionGenerator()
    conflict_engine = ConflictDetectionEngine()
    bias_engine = BiasDetectionEngine()
    learning_engine = LearningEngine()

    # Create project
    project = ProjectData(
        id="proj-001",
        name="E-Commerce Platform",
        description="Online shopping system",
        user_id="user-001",
        current_phase=1,
        maturity_score=0.0,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00"
    )

    specifications = []
    question_history = []
    answers = []

    # Identify initial gaps
    print("=== Requirements Gathering Workflow ===\n")
    gaps = qgen.identify_gaps("We need to build an e-commerce site")
    print(f"Identified gaps: {gaps}\n")

    # Generate and ask questions
    questions = qgen.generate(gaps[:3], category=None)  # First 3 gaps

    for i, question in enumerate(questions, 1):
        print(f"Q{i}: {question}")

        # Get user response
        answer = user_input_function(f"Your answer: ")

        question_history.append(question)
        answers.append(answer)

        # Check for bias in the answer
        bias_result = bias_engine.detect_bias_in_question(answer)
        if bias_result.has_bias:
            print(f"  [Note: Answer shows some assumptions. Consider: {bias_result.suggestion}]\n")

        # Create specification from answer
        spec = SpecificationData(
            id=f"spec-{i}",
            project_id=project.id,
            content=answer,
            version=1,
            category=gaps[i-1] if i <= len(gaps) else 'general',
            created_at="2025-01-01T00:00:00"
        )
        specifications.append(spec)

    print("\n=== Analyzing Specifications ===")

    # Check for conflicts
    spec_contents = [s.content for s in specifications]
    conflicts = conflict_engine.detect_conflicts(spec_contents)

    if conflicts:
        print(f"\nFound {len(conflicts)} potential conflicts:")
        for c in conflicts:
            print(f"  - {c['description']} (Severity: {c['severity']})")
    else:
        print("No conflicts detected - specifications are consistent!")

    # Calculate coverage
    coverage_pct = qgen.calculate_coverage(answers)
    print(f"\nSpecification coverage: {coverage_pct}%")

    # Build learning profile
    profile = learning_engine.build_user_profile(answers, question_history)
    print(f"\nUser expertise level: {profile.domain_expertise}")
    print(f"Comprehension: {profile.comprehension_level:.1%}")

    # Update project maturity
    project.maturity_score = coverage_pct / 100.0
    print(f"\nProject maturity score: {project.maturity_score:.2f}")

    return {
        'project': project,
        'specifications': specifications,
        'conflicts': conflicts,
        'coverage': coverage_pct,
        'user_profile': profile
    }


# Usage
def mock_input(prompt):
    """Mock input for demonstration"""
    responses = [
        "OAuth 2.0 with social login integration",
        "PostgreSQL with proper backups",
        "50ms response time target"
    ]
    return responses[mock_input.counter := (mock_input.counter + 1) % len(responses)]

mock_input.counter = 0

if __name__ == "__main__":
    result = socratic_requirements_gathering(mock_input)
    print("\n=== Results ===")
    print(f"Project: {result['project'].name}")
    print(f"Specifications: {len(result['specifications'])} gathered")
    print(f"Conflicts: {len(result['conflicts'])} found")
    print(f"Coverage: {result['coverage']:.1f}%")
```

---

## CLI Example

Create a simple CLI tool using Socrates engines.

```python
#!/usr/bin/env python3
"""
Simple CLI for requirements gathering using Socratic method.
Usage: python cli_example.py
"""

from socrates import (
    QuestionGenerator,
    ConflictDetectionEngine,
    BiasDetectionEngine
)

def main():
    print("=== Socratic Requirements Gathering CLI ===\n")

    # Initialize engines
    qgen = QuestionGenerator()
    conflict_engine = ConflictDetectionEngine()
    bias_engine = BiasDetectionEngine()

    specs = []

    while True:
        print("\nOptions:")
        print("  1. Add specification")
        print("  2. Generate questions")
        print("  3. Check for conflicts")
        print("  4. Check specification coverage")
        print("  5. Exit")

        choice = input("\nChoose option (1-5): ").strip()

        if choice == "1":
            spec = input("Enter specification: ").strip()
            if spec:
                specs.append(spec)
                print(f"Added: {spec}")

                # Check for bias
                bias = bias_engine.detect_bias_in_question(spec)
                if bias.has_bias:
                    print(f"Tip: {bias.suggestion}")

        elif choice == "2":
            gaps = input("Enter gaps (comma-separated): ").strip().split(",")
            gaps = [g.strip() for g in gaps]
            questions = qgen.generate(gaps)

            print("\nGenerated questions:")
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q}")

        elif choice == "3":
            if len(specs) < 2:
                print("Need at least 2 specifications to detect conflicts")
            else:
                conflicts = conflict_engine.detect_conflicts(specs)

                if conflicts:
                    print(f"\nFound {len(conflicts)} conflicts:")
                    for c in conflicts:
                        print(f"  - {c['description']}")
                else:
                    print("No conflicts found!")

        elif choice == "4":
            if specs:
                coverage = qgen.calculate_coverage(specs)
                print(f"\nCoverage: {coverage}%")
            else:
                print("Add specifications first!")

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
```

---

## More Examples

For more examples, see:
- `examples/` directory in repository
- GitHub discussions and issues
- API_REFERENCE.md for detailed documentation

## Troubleshooting

### Import Errors

```python
# If you get import errors:
import socrates
print(socrates.__all__)  # See what's available

# Verify installation
python -m pip show socrates-ai
```

### Missing Questions

```python
from socrates import QuestionGenerator, CATEGORY_TARGETS

qgen = QuestionGenerator()

# Check if you have enough questions per category
print(CATEGORY_TARGETS)  # See targets
# Adjust gaps based on targets
```

### Performance

All Phase 1a engines are fast (pure Python):
- QuestionGenerator: <10ms for most operations
- ConflictDetectionEngine: <50ms per spec batch
- BiasDetectionEngine: <5ms per question
- LearningEngine: <20ms per calculation

For better performance:
- Cache engine instances (reuse objects)
- Batch similar operations
- Use multiprocessing for large spec batches

---

## Contributing Examples

Have a cool example? Submit a PR to the repository!

---

## License

MIT License - See LICENSE file

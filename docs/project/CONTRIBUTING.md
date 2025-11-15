# Contributing to Socrates

Thank you for your interest in contributing to Socrates! We welcome contributions from the community. This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 17+
- Git

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nireus79/Socrates.git
   cd Socrates
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   cd backend
   pip install -e ".[dev]"
   ```

4. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL and API credentials
   ```

5. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions
- `refactor/` - Code refactoring

### 2. Make Changes

- Write clear, descriptive commit messages
- Follow the code style (see Code Style section below)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_workflows.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

### 4. Code Quality Checks

```bash
# Format code with Black
black app/ tests/

# Lint with Ruff
ruff check app/ tests/

# Type check with mypy
mypy app/ --explicit-package-bases
```

### 5. Commit and Push

```bash
git add .
git commit -m "Clear, descriptive commit message"
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Push to your fork and submit a pull request
- Provide clear description of changes
- Reference any related issues (#123)
- Ensure all tests pass
- Wait for review and address feedback

## Code Style

### Python Code Style

We follow [PEP 8](https://pep8.org/) with Black formatting and Ruff linting.

**Key rules:**
- Line length: 100 characters (Black default)
- Use type hints where possible
- Import ordering: stdlib → third-party → local
- Docstrings for all public functions/classes

**Example:**
```python
from typing import Optional

def generate_questions(
    category: str,
    count: int = 5,
    difficulty: Optional[str] = None
) -> list[str]:
    """
    Generate Socratic questions for a category.

    Args:
        category: Question category
        count: Number of questions to generate
        difficulty: Optional difficulty level (basic, intermediate, advanced)

    Returns:
        List of generated questions

    Raises:
        ValueError: If count is negative
    """
    if count < 0:
        raise ValueError("count must be non-negative")

    # Implementation...
    return []
```

### File Organization

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core services (database, config, security)
│   ├── domains/       # Domain implementations
│   ├── agents/        # Agent implementations
│   ├── models/        # Database models
│   └── main.py        # FastAPI app factory
├── tests/             # Test suite
├── alembic/           # Database migrations
└── socrates/          # Public API package
```

## Testing

### Adding Tests

Tests should be placed in `tests/` directory following the structure of `app/`:

```python
import pytest
from socrates import QuestionGenerator

class TestQuestionGenerator:
    """Test QuestionGenerator engine."""

    def test_generate_questions_returns_list(self):
        """Test that generate_questions returns a list."""
        qgen = QuestionGenerator()
        result = qgen.generate_questions("authentication", count=3)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_generate_questions_invalid_count(self):
        """Test that invalid count raises ValueError."""
        qgen = QuestionGenerator()
        with pytest.raises(ValueError):
            qgen.generate_questions("auth", count=-1)
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_engines.py::TestQuestionGenerator -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run tests matching pattern
pytest tests/ -k "question" -v
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def process_specification(spec: dict, validate: bool = True) -> dict:
    """
    Process a specification with optional validation.

    Args:
        spec: Specification dictionary
        validate: Whether to validate the specification

    Returns:
        Processed specification dictionary

    Raises:
        ValueError: If specification is invalid and validate=True
        KeyError: If required fields are missing

    Example:
        >>> spec = {"name": "auth", "type": "security"}
        >>> result = process_specification(spec)
        >>> print(result["processed"])
        True
    """
    pass
```

### README Updates

If adding new features, update relevant README sections:
- Features
- Installation instructions
- API examples
- Architecture diagrams

## Commit Message Guidelines

Write clear, descriptive commit messages:

```
feat: Add subscription tier management

- Implement SubscriptionTier enum with 4 tiers
- Add TIER_LIMITS configuration
- Create subscription API endpoints
- Add comprehensive tests

Fixes #123
```

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions
- `chore:` - Build/dependency updates

## Pull Request Process

1. **Before submitting:**
   - Run all tests: `pytest tests/ -v`
   - Format code: `black app/ tests/`
   - Lint code: `ruff check app/ tests/`
   - Type check: `mypy app/`

2. **PR description should include:**
   - Clear summary of changes
   - Motivation and context
   - Testing approach
   - Any breaking changes
   - Related issues

3. **Expect:**
   - Code review
   - Requests for changes
   - Feedback on design/approach
   - Merging by maintainers

## Reporting Issues

### Bug Reports

Please include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Python version, OS, dependencies
- Relevant error messages/logs

### Feature Requests

Please include:
- Clear description of the feature
- Motivation (why is this needed?)
- Proposed API/interface
- Any related issues

## Project Structure

**Phase-based development:**
- Phase 1a: Pure Logic (database-independent)
- Phase 1b: Infrastructure (database, config, security)
- Phase 2: Advanced Features (subscriptions, rate limiting)
- Phase 3: Framework & Agents (agents, domains, orchestration)
- Phase 4+: Future enhancements

Each phase maintains backward compatibility with previous phases.

## Questions?

- **GitHub Issues:** Report bugs and feature requests
- **GitHub Discussions:** Ask questions
- **Documentation:** Check README and docs in `/backend/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Socrates!**

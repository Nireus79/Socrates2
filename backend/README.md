# Socrates2 Backend

AI-Powered Specification Assistant using Socratic Method

**Current Version:** 0.1.0
**Status:** Phase 7.4 - Advanced Analytics & Multi-Domain Workflows
**Build Status:** 274 tests passing ✅

## Overview

Socrates2 is a comprehensive AI system for building and validating specifications across multiple knowledge domains using the Socratic method. It provides:

- **Multi-Domain System:** 7 pre-configured domains (Programming, Data Engineering, Architecture, Testing, Business, Security, DevOps)
- **Workflow Management:** Orchestrate specifications across multiple domains with unified validation
- **Analytics Engine:** Track domain usage, workflow quality, and system health
- **REST API:** Complete API for programmatic access to all features
- **CLI Interface:** Command-line tools for domain and workflow management
- **Template Engine:** Customizable question, export, rule, and analyzer engines

## Quick Start

### Installation

```bash
cd backend

# Install in editable mode (recommended for development)
pip install -e ".[dev]"

# Or production installation
pip install -e .
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
export ANTHROPIC_API_KEY="your-key-here"
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Setup Database

```bash
# Run migrations
alembic upgrade head

# Verify setup
pytest tests/ -v --tb=short
```

### Run Server

```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload

# Access API docs: http://localhost:8000/docs
# Access ReDoc: http://localhost:8000/redoc
```

## Key Features

### 1. Multi-Domain System

Seven pre-configured domains with complete question sets, exporters, conflict rules, and quality analyzers:

- **Programming** - Language design, patterns, frameworks
- **Data Engineering** - Data pipelines, databases, ETL
- **Architecture** - System design, scalability, performance
- **Testing** - Test strategy, coverage, automation
- **Business** - Market analysis, GTM, financials
- **Security** - Compliance, encryption, threats
- **DevOps** - Infrastructure, automation, monitoring

```bash
# List all available domains
socrates domains list

# Get details about a domain
socrates domains info programming

# Get all questions in a domain
socrates domains questions data_engineering

# Get exporters for a domain
socrates domains exporters architecture
```

### 2. REST API

Complete API with 40+ endpoints organized by resource:

#### Domains
```bash
# List all domains
curl http://localhost:8000/api/v1/domains

# Get domain details
curl http://localhost:8000/api/v1/domains/programming

# Get domain questions
curl http://localhost:8000/api/v1/domains/programming/questions

# Get export formats
curl http://localhost:8000/api/v1/domains/programming/exporters

# Get validation rules
curl http://localhost:8000/api/v1/domains/programming/rules

# Validate specification
curl -X POST http://localhost:8000/api/v1/domains/programming/validate-specification \
  -H "Content-Type: application/json" \
  -d '{"field1": "value1", "field2": "value2"}'
```

#### Workflows
```bash
# Create workflow combining multiple domains
curl -X POST http://localhost:8000/api/v1/workflows?workflow_id=my_project

# Add domain to workflow
curl -X POST http://localhost:8000/api/v1/workflows/my_project/add-domain \
  -d '{"domain_id": "programming"}'

# Validate workflow specifications
curl http://localhost:8000/api/v1/workflows/my_project/validate

# Get cross-domain conflicts
curl http://localhost:8000/api/v1/workflows/my_project/conflicts

# Export workflow
curl -X POST http://localhost:8000/api/v1/workflows/my_project/export \
  -d '{"format_id": "json"}'
```

#### Analytics
```bash
# Get overall analytics report
curl http://localhost:8000/api/v1/analytics

# Get domain-specific analytics
curl http://localhost:8000/api/v1/analytics/domains/programming

# Get workflow quality metrics
curl http://localhost:8000/api/v1/analytics/quality-summary

# Get most used domains
curl http://localhost:8000/api/v1/analytics/domains/top/10

# Export analytics data
curl -X POST http://localhost:8000/api/v1/analytics/export?format_id=json
```

### 3. CLI Interface

Command-line tools for all features:

```bash
# Domain commands
socrates domains list                           # List all domains
socrates domains info <domain_id>              # Domain details
socrates domains questions <domain_id>         # Get questions
socrates domains exporters <domain_id>         # Get exporters

# Workflow commands
socrates workflows create <workflow_id>        # Create workflow
socrates workflows list                        # List workflows
socrates workflows show <workflow_id>          # Workflow details
socrates workflows add <workflow_id> <domain>  # Add domain
socrates workflows validate <workflow_id>      # Validate specs
socrates workflows export <workflow_id>        # Export workflow
socrates workflows delete <workflow_id>        # Delete workflow

# Analytics commands
socrates analytics report                      # Overall report
socrates analytics quality                     # Quality summary
socrates analytics domains                     # Domain ranking
socrates analytics export <format>             # Export data

# Auth commands
socrates auth login                            # User login
socrates auth logout                           # User logout
socrates auth token --generate                 # Generate API token
```

## Project Structure

```
backend/
├── app/                          # Main application package
│   ├── api/                      # FastAPI endpoints (40+ routes)
│   │   ├── domains.py           # Domain management (11 endpoints)
│   │   ├── workflows.py         # Workflow management (11 endpoints)
│   │   ├── analytics.py         # Analytics reporting (8 endpoints)
│   │   ├── auth.py              # Authentication
│   │   ├── admin.py             # Admin endpoints
│   │   └── ...                  # Other endpoints
│   │
│   ├── domains/                  # Multi-domain system
│   │   ├── base.py              # BaseDomain abstract class
│   │   ├── registry.py          # DomainRegistry singleton
│   │   ├── programming/         # Programming domain (14 Q's, 8 exports)
│   │   ├── data_engineering/    # Data Engineering domain
│   │   ├── architecture/        # Architecture domain
│   │   ├── testing/             # Testing domain
│   │   ├── business/            # Business domain
│   │   ├── security/            # Security domain
│   │   ├── devops/              # DevOps domain
│   │   ├── questions.py         # Question template engine
│   │   ├── exporters.py         # Export format engine
│   │   ├── rules.py             # Conflict rule engine
│   │   ├── analyzers.py         # Quality analyzer engine
│   │   ├── workflows.py         # Multi-domain workflow orchestration
│   │   ├── analytics.py         # Domain analytics tracking
│   │   └── tests/               # Domain tests (80+ tests)
│   │
│   ├── cli/                      # CLI interface
│   │   ├── main.py              # CLI entry point
│   │   ├── commands/
│   │   │   ├── domains.py       # Domain commands
│   │   │   ├── workflows.py     # Workflow commands
│   │   │   ├── analytics.py     # Analytics commands
│   │   │   └── auth.py          # Auth commands
│   │   └── tests.py             # CLI tests (21 tests)
│   │
│   ├── core/                     # Core functionality
│   │   ├── database.py          # SQLAlchemy setup (2 databases)
│   │   ├── config.py            # Settings management
│   │   ├── security.py          # JWT auth
│   │   ├── dependencies.py      # Dependency injection
│   │   └── ...                  # Other utilities
│   │
│   ├── models/                   # SQLAlchemy models
│   │   ├── base.py              # BaseModel with UUID, timestamps
│   │   ├── user.py              # User model
│   │   ├── project.py           # Project model
│   │   ├── specification.py     # Specification model
│   │   └── ...                  # Other models
│   │
│   ├── agents/                   # Agent system
│   │   ├── base.py              # BaseAgent abstract class
│   │   ├── orchestrator.py      # AgentOrchestrator
│   │   └── ...                  # Specialized agents
│   │
│   ├── services/                 # Business logic services
│   │   └── ...
│   │
│   └── main.py                   # FastAPI application factory
│
├── tests/                        # Test suite (274+ tests)
│   ├── test_domains/            # Domain tests
│   ├── test_workflows.py        # Workflow tests (29 tests)
│   ├── test_analytics.py        # Analytics tests (27 tests)
│   ├── test_cli.py              # CLI tests (21 tests)
│   └── ...                       # Other test files
│
├── alembic/                      # Database migrations
│   └── versions/                 # Migration scripts
│
├── pyproject.toml               # Package configuration
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
└── README.md                    # This file
```

## Testing

### Run All Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html

# Run specific test module
pytest tests/test_workflows.py -v

# Run tests matching pattern
pytest tests/ -k "workflow" -v
```

### Test Coverage

- **Domain System:** 80+ tests
  - 14 domain tests (per-domain functionality)
  - Question engine tests
  - Export engine tests
  - Rule engine tests
  - Analyzer engine tests

- **Workflows:** 29 tests
  - Multi-domain workflow creation and validation
  - Cross-domain conflict detection
  - Specification export

- **Analytics:** 27 tests
  - Metrics tracking
  - Domain analytics
  - Workflow analytics
  - Quality summary

- **CLI:** 21 tests
  - Domain commands
  - Workflow commands
  - Analytics commands
  - Help text

- **Infrastructure:** 100+ tests
  - Database persistence
  - Authentication
  - API endpoints
  - Agent system
  - Service integration

**Total: 274+ tests, all passing ✅**

## Development

### Code Quality

```bash
# Format code with black (100 char line length)
black app/ tests/

# Lint with ruff
ruff check app/ tests/

# Type check with mypy
mypy app/ --explicit-package-bases

# Run all checks
black app/ && ruff check app/ && mypy app/
```

### Common Development Tasks

```bash
# Start development server with auto-reload
python -m uvicorn app.main:app --reload --port 8000

# Run tests continuously while editing
pytest-watch tests/

# Create new database migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

### Environment Variables

Create `.env` file with:

```env
# Database URLs (PostgreSQL)
DATABASE_URL_AUTH=postgresql://postgres:password@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://postgres:password@localhost:5432/socrates_specs

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API
ANTHROPIC_API_KEY=your-api-key-here

# Application
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## API Documentation

Once the server is running:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

All endpoints are documented with:
- Request/response examples
- Parameter descriptions
- Error codes and messages
- Authentication requirements

## Architecture

### Multi-Database Design

**socrates_auth database:**
- Users table (authentication)
- Refresh tokens table (JWT management)

**socrates_specs database:**
- Projects table (specification metadata)
- Sessions table (conversation history)
- And future: specifications, questions, conflicts, metrics

### Domain System Architecture

```
DomainRegistry (singleton)
    ├── ProgrammingDomain
    ├── DataEngineeringDomain
    ├── ArchitectureDomain
    ├── TestingDomain
    ├── BusinessDomain
    ├── SecurityDomain
    └── DevOpsDomain

Each Domain contains:
    ├── Questions (via QuestionTemplateEngine)
    ├── Export Formats (via ExportTemplateEngine)
    ├── Conflict Rules (via ConflictRuleEngine)
    └── Quality Analyzers (via QualityAnalyzerEngine)
```

### Workflow System

```
WorkflowManager (singleton)
    └── MultiDomainWorkflow
        ├── DomainSpec (per domain)
        ├── CrossDomainConflict detection
        │   ├── Architecture ↔ Testing
        │   ├── Performance ↔ Testing
        │   └── Data ↔ Architecture
        └── Unified validation & export
```

### Analytics System

```
DomainAnalytics (singleton)
    ├── Domain access tracking
    ├── Question answer tracking
    ├── Export generation tracking
    ├── Conflict detection tracking
    ├── Workflow analytics
    ├── Quality metrics
    └── Custom reporting
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

```bash
cd backend
pip install -e .
```

### "Connection refused" on PostgreSQL

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
# or Services app on Windows

# Start PostgreSQL if stopped
sudo systemctl start postgresql   # Linux

# Verify databases exist
psql -U postgres -l | grep socrates
```

### API returns 404 for domains

```bash
# Ensure domains are registered
python -c "from app.domains import get_domain_registry; r = get_domain_registry(); print([d for d in r.list_domain_ids()])"

# Check that domain JSON files exist
ls -la app/domains/*/domain.json
```

### Tests fail with "domain not found"

```bash
# Domain registration might not have happened
# Delete any .pyc files and restart
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true

# Run tests again
pytest tests/ -v
```

## Contributing

1. Install in editable mode: `pip install -e ".[dev]"`
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes
4. Run tests: `pytest tests/ -v`
5. Format code: `black app/ tests/`
6. Commit with descriptive message
7. Push and create pull request

## Phase Status

- ✅ **Phase 0:** Documentation - Complete
- ✅ **Phase 1:** Infrastructure - Complete (user/project/session models)
- ✅ **Phase 2:** Authentication - Complete (JWT, roles)
- ✅ **Phase 3:** Agents - Complete (BaseAgent, Orchestrator)
- ✅ **Phase 4:** Core APIs - Complete (domain/project endpoints)
- ✅ **Phase 5:** Questions & Exporters - Complete (7 domains, 100+ questions)
- ✅ **Phase 6:** Specification Validation - Complete (conflict rules, quality analyzers)
- ✅ **Phase 7:** Advanced Features - Complete
  - ✅ Phase 7.1: Advanced Domains (Business, Security, DevOps)
  - ✅ Phase 7.2: Template Engines
  - ✅ Phase 7.3: Multi-Domain Workflows
  - ✅ Phase 7.4: Analytics System & CLI
- ⏳ **Phase 8:** Production Hardening

## License

MIT

## Support

For issues, questions, or contributions:
1. Check existing documentation in `/docs`
2. Review test files for usage examples
3. Check API docs at `/docs` endpoint
4. Create issue with detailed description

---

**Last Updated:** November 11, 2025
**Maintained by:** Socrates2 Team

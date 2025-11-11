# Socrates2 Backend

AI-Powered Specification Assistant using Socratic Method

## Quick Start

```bash
cd backend

# Install in editable mode (recommended)
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Setup database
createdb socrates_auth
createdb socrates_specs
alembic upgrade head

# Run tests
pytest tests/test_data_persistence.py -v  # CRITICAL tests
pytest tests/ -v                           # All tests

# Start server
python -m uvicorn app.main:app --reload

# Open browser: http://localhost:8000/docs
```

## Documentation

- **[INSTALL.md](../archive/INSTALL.md)** - Complete installation guide
- **[PYCHARM_SETUP.md](../PYCHARM_SETUP.md)** - PyCharm configuration
- **[PHASE_1_IMPLEMENTATION_COMPLETE.md](../PHASE_1_IMPLEMENTATION_COMPLETE.md)** - Implementation details

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── core/              # Core functionality (config, database, security)
│   ├── models/            # SQLAlchemy models
│   ├── api/               # FastAPI endpoints
│   ├── agents/            # Agent system (BaseAgent, Orchestrator)
│   └── main.py            # FastAPI application
├── tests/                 # Test suite
│   ├── test_data_persistence.py        # CRITICAL: Archive killer bug prevention
│   └── test_phase_1_infrastructure.py  # Comprehensive infrastructure tests
├── alembic/              # Database migrations
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml        # Package configuration
└── .env                  # Environment variables (create from .env.example)
```

## Key Features (Phase 1)

### Infrastructure
- ✅ **Safe session management** - Prevents data loss bug from archive
- ✅ Two-database architecture (auth + specs)
- ✅ Proper error handling (no silent failures)
- ✅ No fallback mechanisms (fail-fast approach)

### Authentication
- ✅ JWT token-based authentication
- ✅ User registration and login
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (user/admin)

### Agent System
- ✅ BaseAgent abstract class
- ✅ AgentOrchestrator for routing
- ✅ ServiceContainer for dependency injection
- ✅ Built-in error handling and statistics

### API Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - Login (JWT)
- `GET /api/v1/auth/me` - Current user info
- `GET /api/v1/admin/health` - Health check
- `GET /api/v1/admin/stats` - System statistics (admin only)

## Installation Methods

### Recommended: Editable Install

**Benefits:** Works everywhere, portable, professional standard

```bash
cd backend
pip install -e ".[dev]"
```

### Alternative: Working Directory

**Use for:** Docker, CI/CD, production

```bash
cd backend
export PYTHONPATH=.
pip install -r requirements.txt
```

See [INSTALL.md](../archive/INSTALL.md) for complete instructions.

## Testing

### Critical Persistence Tests (MUST PASS)

These tests verify the data loss bug from archive is fixed:

```bash
pytest tests/test_data_persistence.py -v -s
```

**Expected:** All 4 tests pass ✅

If ANY test fails, DO NOT proceed to Phase 2.

### All Infrastructure Tests

```bash
pytest tests/test_phase_1_infrastructure.py -v
```

### Run All Tests with Coverage

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Development

### Start Development Server

```bash
python -m uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000

API documentation: http://localhost:8000/docs

### Verify Environment

```bash
python test_imports.py
# Should show: ✅ ALL IMPORTS SUCCESSFUL!

python setup_dev.py
# Comprehensive environment check
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

## Database

### Two-Database Architecture

- **socrates_auth** - User authentication, tokens
- **socrates_specs** - Projects, sessions, specifications

### Migrations

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback
alembic downgrade -1
```

## Configuration

All configuration in `.env` file:

```bash
# Copy example
cp .env.example .env

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env
DATABASE_URL_AUTH=postgresql://user:pass@localhost/socrates_auth
DATABASE_URL_SPECS=postgresql://user:pass@localhost/socrates_specs
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-api-key-here
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

```bash
cd backend
pip install -e .
```

### "Unresolved reference 'app'" in PyCharm

After `pip install -e .`, PyCharm auto-detects. If not:
- File → Invalidate Caches → Restart

### Database Connection Errors

```bash
# Check PostgreSQL running
sudo systemctl status postgresql  # Linux
# or check Services on Windows

# Verify databases exist
psql -l | grep socrates

# Create if missing
createdb socrates_auth
createdb socrates_specs
```

### Tests Fail

```bash
# Ensure dependencies installed
pip install -e ".[dev]"

# Check database setup
alembic upgrade head

# Run with verbose output
pytest tests/ -v -s
```

## Architecture Highlights

### Safe Session Management

**Archive had critical bug:** Sessions closed before commit synced to disk → Zero data persistence

**Socrates2 solution:**

```python
def get_db_auth():
    db = SessionLocalAuth()
    try:
        yield db
        db.commit()  # ✅ CRITICAL: Commit BEFORE close
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### No Fallbacks

Archive returned `None` or `{}` on errors → Silent failures

Socrates2 raises exceptions → Fail-fast approach

```python
def get_claude_client(self):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY required")  # ✅ Fail fast
    return Anthropic(api_key=ANTHROPIC_API_KEY)
```

## Phase Status

- ✅ **Phase 0:** Documentation - Complete
- ✅ **Phase 1:** Infrastructure - Implementation complete, testing required
- ⏳ **Phase 2:** Core Agents - Awaiting Phase 1 verification
- ⏳ **Phase 3-10:** Future phases

## Contributing

1. Install in editable mode: `pip install -e ".[dev]"`
2. Create feature branch: `git checkout -b feature/name`
3. Make changes
4. Run tests: `pytest tests/ -v`
5. Format code: `black app/ tests/`
6. Commit and push

## License

MIT

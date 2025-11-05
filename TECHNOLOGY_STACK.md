# Socrates2 - Technology Stack

**Last Updated:** 2025-11-05
**Source:** [ARCHITECTURE.md](./ARCHITECTURE.md) and [VISION.md](./VISION.md)

---

## Technology Decisions

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.12 | Core application language |
| **Web Framework** | FastAPI | 0.121.0+ | REST API backend |
| **ORM** | SQLAlchemy | 2.0.44+ | Database abstraction |
| **Database** | PostgreSQL | 15+ | Data persistence (2 instances) |
| **Validation** | Pydantic | 2.12.3+ | Data validation & serialization |
| **Migrations** | Alembic | latest | Database schema versioning |
| **LLM Client** | Anthropic SDK | latest | Claude API integration |
| **CLI** | Custom | - | Command-line interface (MVP) |

---

## Detailed Rationale

### Python 3.12

**Why:**
- ✅ Stable, battle-tested (released Sept 2023)
- ✅ Compatible with all dependencies (FastAPI, SQLAlchemy, Pydantic)
- ✅ Modern async/await features for concurrent operations
- ✅ Type hints support (crucial for large codebase)
- ✅ Good performance balance

**Why not 3.14?**
- Too new, edge cases unknown for production MVP
- Limited library support
- Unknown compatibility issues

**Why not 3.11 or earlier?**
- Missing modern features
- Slower performance
- Less modern async support

---

### FastAPI 0.121.0+

**Why:**
- ✅ Async-native (required for multi-LLM support in future phases)
- ✅ Pydantic validation built-in (data integrity)
- ✅ Automatic OpenAPI documentation (easier testing & future UI integration)
- ✅ Lightweight, modern, fast
- ✅ Perfect for React UI integration later
- ✅ Dependency injection system (clean architecture)

**Why not Django?**
- Too heavy for MVP
- Sync-by-default (async requires ASGI conversion)
- Template engine not needed (CLI first, REST API only)

**Why not Flask?**
- No async support natively
- No built-in validation
- More boilerplate required

---

### PostgreSQL (2 Instances)

#### Database 1: `socrates_auth` (Authentication & User Data)

**Contains:**
- users
- user_rules
- auth_tokens (later)
- teams (future Phase 6+)
- permissions (future Phase 6+)

**Characteristics:**
- Small (~10MB typical)
- Locked down security
- Slow-changing data
- Independent backup strategy

#### Database 2: `socrates_specs` (Projects & Specifications)

**Contains:**
- projects
- sessions
- specifications
- conversation_history
- conflicts
- quality_metrics
- maturity_tracking
- knowledge_base
- test_results

**Characteristics:**
- Large (~1GB+ over time)
- Optimized for high-volume writes
- Fast concurrent access
- Frequent queries and updates

**Why 2 databases (not 1, not 3)?**

**One Database Problems:**
- ❌ Auth data mixed with project data (security concern)
- ❌ Can't back up/archive projects without affecting auth
- ❌ Specs table grows exponentially, auth stays small
- ❌ Different scaling needs
- ❌ Can't isolate for performance tuning
- ❌ Compliance issues (harder to separate concerns)

**Two Database Benefits:**
- ✅ Security isolation (specs breach ≠ auth breach)
- ✅ Independent scaling (auth stays small, specs scales)
- ✅ Different backup strategies
- ✅ Different optimization needs
- ✅ Clean compliance separation
- ✅ Future-proof for team collaboration
- ✅ Can reset/archive specs without affecting auth

**Why not 3+?**
- Too operationally complex
- 2 is right balance: separation + simplicity

**Why PostgreSQL (not SQLite, not MySQL, not NoSQL)?**

**vs SQLite:**
- ❌ SQLite: Single-user only (no concurrency)
- ❌ SQLite: Limited to one machine
- ❌ SQLite: Can't scale for team collaboration
- ✅ PostgreSQL: Multi-user, concurrent access

**vs MySQL:**
- ❌ MySQL: Less extensible
- ❌ MySQL: No pgvector support (future semantic search)
- ✅ PostgreSQL: More extensible, better JSON support

**vs NoSQL (MongoDB, etc.):**
- ❌ NoSQL: No ACID transactions (specs must be consistent)
- ❌ NoSQL: No foreign keys (data integrity)
- ✅ PostgreSQL: ACID compliance, referential integrity

**PostgreSQL Advantages:**
- ✅ ACID compliance (data integrity for specs)
- ✅ JSONB support (flexible rules, metadata storage)
- ✅ Full-text search (knowledge base search in MVP)
- ✅ Extensible (pgvector added later for semantic search if needed)
- ✅ Battle-tested, robust, production-ready
- ✅ Concurrent access (multiple agents querying simultaneously)

---

### SQLAlchemy ORM 2.0.44+

**Why:**
- ✅ Proven, mature (10+ years production use)
- ✅ Works perfectly with Python 3.12
- ✅ Flexible: can use ORM or Core SQL as needed
- ✅ Type hints support (Pydantic integration)
- ✅ Easy to test (can swap database for testing)
- ✅ Handles relationships cleanly
- ✅ Migration support via Alembic

**Why not raw SQL?**
- Harder to maintain
- Type safety harder
- More boilerplate
- Migration management manual

**Why not Django ORM?**
- Tied to Django framework
- Can't use without full Django stack

**Critical Note:** See [SQLALCHEMY_BEST_PRACTICES.md](./SQLALCHEMY_BEST_PRACTICES.md) for issues that killed previous attempts.

---

### Pydantic 2.12.3+

**Why:**
- ✅ FastAPI integration (native support)
- ✅ Strong validation (prevents invalid data)
- ✅ Serialization/deserialization (JSON ↔ Python objects)
- ✅ Type safety (catches errors at development time)
- ✅ Clear error messages (debugging easier)
- ✅ from_attributes (SQLAlchemy model → Pydantic model conversion)

**Why not attrs or dataclasses?**
- No validation
- No serialization
- Less FastAPI integration

---

### CLI Framework: Custom (No Click/Typer)

**Why Custom:**
- ✅ Like Claude Code - simple, direct, functional
- ✅ No extra dependencies (reduces complexity)
- ✅ Easy to debug and extend
- ✅ Can be replaced by UI later without backend changes
- ✅ Focused on core logic, not CLI polish

**Why not Click?**
- Extra dependency
- Adds complexity to testing
- CLI is temporary (UI comes later)

**Why not Typer?**
- Same as Click (Typer is built on Click)
- MVP focus: core logic, not CLI features

**CLI Design:**
- Commands for project management (create, load, list)
- Commands for chat (run conversation, toggle modes, show status)
- Commands for phase transitions (advance, show phase)
- Admin commands for testing/debugging

---

### Alembic (Database Migrations)

**Why:**
- ✅ Database schema version control
- ✅ Works seamlessly with SQLAlchemy
- ✅ Essential for managing 2 databases safely
- ✅ Can migrate forward/backward
- ✅ Team collaboration (shared schema changes)

**Why not Django migrations?**
- Tied to Django
- Can't use standalone

**Why not raw SQL migrations?**
- Manual tracking
- Error-prone
- No rollback support

---

## Future Technologies (Not in MVP)

### Phase 3+: Multi-LLM Support

| Provider | SDK | Purpose |
|----------|-----|---------|
| Claude | Anthropic SDK | Primary LLM (MVP) |
| OpenAI | OpenAI SDK | Alternative provider |
| Gemini | Google Generative AI SDK | Alternative provider |
| Ollama | Ollama SDK | Local models |

**Why deferred:** MVP uses Claude only, multi-LLM adds complexity without immediate benefit.

---

### Phase 4+: Code Generation

| Technology | Purpose |
|-----------|---------|
| AST parsing | Code analysis |
| Jinja2 | Template generation |
| Black/Ruff | Code formatting |

**Why deferred:** Foundation must be solid before code generation.

---

### Phase 5+: Semantic Search (Optional)

| Technology | Purpose |
|-----------|---------|
| pgvector | Vector storage in PostgreSQL |
| Sentence-Transformers | Embedding generation |

**Why deferred:** Full-text search sufficient for MVP, vectors add complexity.

**Non-Breaking Addition:** ALTER TABLE knowledge_base ADD COLUMN embedding vector(384) - existing queries still work.

---

### Phase 6+: UI

| Technology | Purpose |
|-----------|---------|
| React | Frontend framework |
| TailwindCSS | Styling |
| Vite | Build tool |

**Why deferred:** CLI first (faster MVP), UI later (no backend changes needed).

---

## Explicitly NOT Used (And Why)

### ❌ ChromaDB
- **Why not:** Full-text search sufficient for MVP
- **Future:** Vectors added only if semantic search proves necessary (Phase 5+)
- **Decision:** PostgreSQL with pgvector is non-breaking upgrade later

### ❌ Redis
- **Why not:** Not needed for MVP (PostgreSQL handles caching via queries)
- **Future:** May add for session management in Phase 6+ (team collaboration)

### ❌ Celery (Task Queue)
- **Why not:** No background jobs in MVP
- **Future:** May add for long-running operations (code generation Phase 4+)

### ❌ Docker (Development)
- **Why not:** Adds complexity to local development
- **Future:** Docker for production deployment (Phase 2)

### ❌ Microservices
- **Why not:** MVP is monolithic (simpler, faster development)
- **Future:** Can split later if needed (agents are already modular)

---

## Technology Decision Summary

| Category | Chosen | Alternatives Considered | Why Chosen |
|----------|--------|------------------------|------------|
| Language | Python 3.12 | 3.14, 3.11 | Stable, compatible |
| Web Framework | FastAPI | Django, Flask | Async, lightweight |
| Database | PostgreSQL (2 instances) | SQLite, MySQL, NoSQL | ACID, scalability |
| ORM | SQLAlchemy 2.0 | Django ORM, raw SQL | Mature, flexible |
| Validation | Pydantic | attrs, dataclasses | FastAPI integration |
| CLI | Custom | Click, Typer | Simple, focused |
| LLM | Claude (Anthropic) | GPT-4, Gemini | Best for reasoning |

---

## Compatibility Testing (Real-Time)

**Feature:** Before implementation, system validates that proposed technologies work together.

**How:**
- Attempts actual imports
- Checks version compatibility
- Analyzes library interactions
- Tests database connections

**Benefits:**
- Catches incompatibilities BEFORE coding
- Prevents expensive rework
- Stores results in database (no re-testing)

**Implementation:** Phase 1 (compatibility_testing service)

---

## Extensibility Guarantees

**These features can be added later WITHOUT refactoring:**

- **Vectors (Phase 5):** ALTER TABLE knowledge_base ADD COLUMN embedding - non-breaking
- **Multi-LLM (Phase 3):** Add provider classes, existing code unchanged
- **UI (Phase 6):** React consumes same REST API, no backend changes
- **Team Collaboration (Phase 6):** Add team tables, existing tables unchanged
- **IDE Integration (Phase 4):** Add IDE endpoints, existing API unchanged

**Architecture Rule:** New features = new tables/services, NOT modifying existing ones.

---

**References:**
- [VISION.md](./VISION.md) - Project goals and requirements
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Complete system architecture
- [SQLALCHEMY_BEST_PRACTICES.md](./SQLALCHEMY_BEST_PRACTICES.md) - Database implementation guide

---

**Last Reviewed:** 2025-11-05
**Status:** APPROVED

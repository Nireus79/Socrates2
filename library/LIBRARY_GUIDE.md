# Socrates Library - Implementation Guide

Complete guide to understanding and using the Socrates library across all phases.

## Table of Contents

- [Library Architecture](#library-architecture)
- [Phase 1a - Pure Logic](#phase-1a---pure-logic)
- [Phase 1b - Infrastructure](#phase-1b---infrastructure)
- [Phase 2 - Advanced Features](#phase-2---advanced-features)
- [Phase 3 - Full Framework](#phase-3---full-framework)
- [Migration Path](#migration-path)
- [FAQ](#faq)

---

## Library Architecture

### Overview

The Socrates library is organized into phases, allowing you to start simple and scale:

```
Phase 1a: Pure Logic Engines
  ├─ QuestionGenerator (no dependencies)
  ├─ ConflictDetectionEngine (no dependencies)
  ├─ BiasDetectionEngine (no dependencies)
  └─ LearningEngine (no dependencies)

Phase 1b: Infrastructure (requires .env configuration)
  ├─ Database (PostgreSQL)
  ├─ Security (JWT)
  ├─ Config Management
  └─ Dependency Injection

Phase 2: Services (requires Phase 1b)
  ├─ NLU Service (conversational AI)
  ├─ Subscription Management
  ├─ Rate Limiting
  └─ Action Logging

Phase 3: Full Framework (requires Phase 2)
  ├─ Agents (9 implementations)
  ├─ Domains (7 implementations)
  ├─ Database Models (33+ models)
  └─ Agent Orchestrator
```

### Design Principles

1. **Progressive Enhancement**: Start simple, add features as needed
2. **No Forced Dependencies**: Use only what you need
3. **Pure Logic First**: Core engines work without configuration
4. **Database Optional**: Combine with your own database or use ours
5. **Library-Friendly**: Can be embedded in other applications

---

## Phase 1a - Pure Logic

### What's Available

✅ Available now with `pip install socrates-ai`

- 4 pure business logic engines
- 8 dataclasses for data modeling
- 7 conversion functions
- Constants and enums
- ~27 exports (see `API_REFERENCE.md`)

### What You Need

- Python 3.10+
- `pip` package manager
- That's it!

### Quick Start

```bash
# Install
pip install socrates-ai

# Use
python << 'EOF'
from socrates import QuestionGenerator

qgen = QuestionGenerator()
questions = qgen.generate(['authentication', 'performance'])
for q in questions:
    print(f"- {q}")
EOF
```

### Use Cases

1. **CLI Tools**: Build Socratic CLI without database
2. **Web Frontends**: Embed in React, Vue, Angular (via API)
3. **Plugins**: Add to existing tools
4. **Research**: Academic projects needing pure logic
5. **Desktop Apps**: Electron, PyQt applications

### Example: Standalone CLI Tool

```python
from socrates import QuestionGenerator, ConflictDetectionEngine

def main():
    qgen = QuestionGenerator()
    conflict_engine = ConflictDetectionEngine()

    # Get specs from user
    print("Enter specifications (one per line, blank to finish):")
    specs = []
    while True:
        s = input()
        if not s:
            break
        specs.append(s)

    # Generate questions
    print("\nGenerated questions:")
    questions = qgen.generate(['general'])
    for q in questions:
        print(f"- {q}")

    # Detect conflicts
    if len(specs) >= 2:
        conflicts = conflict_engine.detect_conflicts(specs)
        print(f"\nConflicts found: {len(conflicts)}")

if __name__ == "__main__":
    main()
```

### Limitations

Phase 1a cannot:
- ❌ Persist data (no database)
- ❌ Authenticate users (no security)
- ❌ Scale across machines (single process)
- ❌ Use advanced NLU (no Claude integration)
- ❌ Run agents (needs configuration)

---

## Phase 1b - Infrastructure

### What Becomes Available

After configuring environment:

- Configuration management (Settings, get_settings)
- Database connections (PostgreSQL)
- Security & JWT authentication
- Dependency injection (ServiceContainer)
- Service initialization

### Prerequisites

1. **PostgreSQL 12+**
   ```bash
   # macOS with Homebrew
   brew install postgresql

   # Ubuntu/Debian
   sudo apt-get install postgresql

   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Environment Variables**
   ```bash
   # .env file or system environment
   DATABASE_URL_AUTH=postgresql://user:pass@localhost:5432/socrates_auth
   DATABASE_URL_SPECS=postgresql://user:pass@localhost:5432/socrates_specs
   SECRET_KEY=your-secret-key-32-chars-minimum
   ANTHROPIC_API_KEY=sk-...  # Claude API key
   ```

3. **Databases Created**
   ```bash
   psql -U postgres

   CREATE DATABASE socrates_auth;
   CREATE DATABASE socrates_specs;

   \q
   ```

### Setup Steps

1. **Install with Database Support**
   ```bash
   pip install socrates-ai[db]
   ```

2. **Create .env File**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Initialize Databases**
   ```bash
   socrates-init-db  # Command-line tool
   ```

4. **Use in Your Application**
   ```python
   from socrates import get_settings, Settings
   from socrates import get_db_auth, get_db_specs

   # Load configuration
   settings = get_settings()

   # Get database sessions
   db = get_db_auth()
   try:
       # Use database
       pass
   finally:
       db.close()
   ```

### Uncomment Imports

After Phase 1b setup, uncomment in `socrates/__init__.py`:

```python
# Uncomment these imports
from app.core.config import Settings, get_settings
from app.core.dependencies import ServiceContainer
from app.core.database import (
    engine_auth, engine_specs,
    SessionLocalAuth, SessionLocalSpecs,
    # ... etc
)
from app.core.security import (
    create_access_token, decode_access_token,
    # ... etc
)
```

### Example: With Database

```python
from socrates import get_db_auth, get_settings, ServiceContainer
from app.models import Project

def create_project(name: str, description: str):
    settings = get_settings()
    db = get_db_auth()

    try:
        project = Project(
            name=name,
            description=description,
            user_id="user-001"
        )
        db.add(project)
        db.commit()
        return project
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
```

---

## Phase 2 - Advanced Features

### What Becomes Available

- **NLU Service**: Natural language intent parsing
- **Subscription Management**: Tier limits and quota enforcement
- **Rate Limiting**: API rate limiting for scaling
- **Action Logging**: Comprehensive workflow logging
- **Validators**: Email, domain validation

### Prerequisites

- Phase 1b setup (database, config)
- Claude API key (for NLU)

### Setup

```python
from socrates import NLUService, Intent, create_nlu_service
from anthropic import Anthropic

# Initialize NLU
client = Anthropic()
nlu = NLUService(client)

# Parse user intent
user_input = "Create a new project called Mobile App"
intent = nlu.parse_intent(user_input)

if intent.is_operation:
    print(f"Operation: {intent.operation}")
    print(f"Params: {intent.params}")
else:
    print(f"Response: {intent.response}")
```

### Rate Limiting Example

```python
from socrates import RateLimiter, get_rate_limiter

limiter = get_rate_limiter()

# Check if user can perform action
user_id = "user-123"
if limiter.is_rate_limited(user_id, "question_generation", limit=100):
    print("Rate limit exceeded!")
else:
    # Process question generation
    pass
```

### Subscription Tiers

```python
from socrates import SubscriptionTier, TIER_LIMITS, UsageLimiter

# Check user quota
user_tier = SubscriptionTier.PRO
limiter = UsageLimiter()

if limiter.check_limit(user_id, "agent_runs", user_tier):
    # User can run more agents
    pass
else:
    # User has exceeded quota
    print("Agent runs limit reached for your tier")

# View tier limits
print(TIER_LIMITS)
# {
#   'FREE': {'agent_runs': 10, 'questions_per_month': 100, ...},
#   'PRO': {'agent_runs': unlimited, 'questions_per_month': 1000, ...},
#   ...
# }
```

---

## Phase 3 - Full Framework

### What Becomes Available

- **Agents**: 9 agent implementations
- **Domains**: 7 domain-specific implementations
- **Agent Orchestrator**: Central coordinator
- **Full Database Support**: 33+ models
- **Team Features**: Collaboration, sharing, permissions

### Architecture

```python
from socrates import (
    AgentOrchestrator,
    ProjectManagerAgent,
    SocraticCounselorAgent,
    ProgrammingDomain,
    DataEngineeringDomain
)

# Initialize orchestrator
orchestrator = get_orchestrator()

# Register domains
orchestrator.register_domain(ProgrammingDomain())
orchestrator.register_domain(DataEngineeringDomain())

# Execute agent workflow
result = orchestrator.execute(
    agent_type='ProjectManagerAgent',
    domain='Programming',
    context={
        'project_id': 'proj-123',
        'user_id': 'user-123'
    }
)

print(result)
```

### Agents Overview

| Agent | Purpose | Use Case |
|-------|---------|----------|
| ProjectManagerAgent | Manage projects and phases | Track project progress |
| SocraticCounselorAgent | Guide users through spec gathering | Requirements elicitation |
| ContextAnalyzerAgent | Analyze project context | Understand project intent |
| ConflictDetectorAgent | Find spec conflicts | Validate requirements |
| CodeGeneratorAgent | Generate code from specs | Bootstrap implementation |
| QualityControllerAgent | Ensure spec quality | Validate completeness |
| ExportAgent | Export to multiple formats | Document specifications |
| TeamCollaborationAgent | Manage team interactions | Enable team workflows |
| UserLearningAgent | Track user learning | Personalize experience |

### Domains Overview

| Domain | Focus | Questions |
|--------|-------|-----------|
| Programming | Software development | Architecture, patterns, testing |
| DataEngineering | Data systems | Pipelines, warehousing, governance |
| Architecture | System design | Scalability, reliability, performance |
| Testing | Quality assurance | Coverage, strategy, automation |
| Business | Business logic | Requirements, workflows, metrics |
| Security | Security & compliance | Threats, controls, compliance |
| DevOps | Operations & deployment | Deployment, monitoring, disaster recovery |

### Example: Full Workflow

```python
from socrates import (
    AgentOrchestrator,
    get_orchestrator,
    ProgrammingDomain,
    ProjectData
)

def full_workflow(project_id: str, user_id: str):
    # Get orchestrator
    orchestrator = get_orchestrator()

    # Register domains
    orchestrator.register_domain(ProgrammingDomain())

    # Step 1: Analyze project context
    context_result = orchestrator.execute(
        agent_type='ContextAnalyzerAgent',
        domain='Programming',
        context={'project_id': project_id, 'user_id': user_id}
    )

    # Step 2: Run Socratic counselor
    socratic_result = orchestrator.execute(
        agent_type='SocraticCounselorAgent',
        domain='Programming',
        context={
            'project_id': project_id,
            'user_id': user_id,
            'conversation_history': context_result['questions']
        }
    )

    # Step 3: Check for conflicts
    conflict_result = orchestrator.execute(
        agent_type='ConflictDetectorAgent',
        domain='Programming',
        context={
            'project_id': project_id,
            'specifications': socratic_result['gathered_specs']
        }
    )

    # Step 4: Ensure quality
    quality_result = orchestrator.execute(
        agent_type='QualityControllerAgent',
        domain='Programming',
        context={
            'project_id': project_id,
            'specifications': socratic_result['gathered_specs'],
            'conflicts': conflict_result['conflicts']
        }
    )

    return {
        'context': context_result,
        'socratic': socratic_result,
        'conflicts': conflict_result,
        'quality': quality_result
    }
```

---

## Migration Path

### Recommended Progression

```
Week 1: Phase 1a (Pure Logic)
  ├─ Install library
  ├─ Try QuestionGenerator
  ├─ Explore ConflictDetectionEngine
  └─ Build simple CLI tool

Week 2: Phase 1b (Infrastructure)
  ├─ Set up PostgreSQL
  ├─ Configure .env
  ├─ Initialize databases
  └─ Use database sessions in your code

Week 3: Phase 2 (Services)
  ├─ Add NLU for intent parsing
  ├─ Implement subscription tiers
  ├─ Add rate limiting
  └─ Enable action logging

Week 4+: Phase 3 (Framework)
  ├─ Use agents for complex workflows
  ├─ Register domains
  ├─ Build full application
  └─ Deploy to production
```

### Example: Gradual Migration

```python
# Week 1: Just pure engines
from socrates import QuestionGenerator
qgen = QuestionGenerator()

# Week 2: Add database
from socrates import get_db_auth, ProjectData
db = get_db_auth()

# Week 3: Add NLU
from socrates import NLUService
nlu = NLUService()

# Week 4: Use agents
from socrates import AgentOrchestrator
orchestrator = get_orchestrator()
```

---

## FAQ

### Q: Can I use Phase 1a without configuration?

**A:** Yes! Phase 1a is completely self-contained. No database, no .env needed.

### Q: Do I have to use all phases?

**A:** No. Use only what you need:
- Just want question generation? Use Phase 1a only
- Need persistence? Add Phase 1b
- Want NLU? Add Phase 2
- Need full framework? Add Phase 3

### Q: Can I mix with my own database?

**A:** Yes. Use Phase 1a engines with your own database. The conversion functions help bridge between your models and Socrates dataclasses.

### Q: How do I deploy Phase 1a?

**A:** Anywhere Python runs:
- PyPI package (`pip install socrates-ai`)
- Docker container
- Serverless (AWS Lambda, Google Cloud Functions)
- Desktop app (PyQt, Electron with Python backend)

### Q: Can I deploy Phase 1b+?

**A:** Yes, but requires:
- Python 3.10+
- PostgreSQL 12+
- Environment variables configured
- Claude API access (for NLU)

### Q: What about the agents - can I run just one?

**A:** Yes, or all together. Each agent is independent but they coordinate via AgentOrchestrator.

### Q: Is the database required?

**A:** Only for Phases 1b+. Phase 1a is pure logic, no database needed.

### Q: Can I extend the engines?

**A:** Yes! All engines have documented interfaces. Create your own subclasses or wrap them.

### Q: What about performance?

**A:** Phase 1a is fast (pure Python):
- QuestionGenerator: ~10ms
- ConflictDetectionEngine: ~50ms per batch
- BiasDetectionEngine: ~5ms per question

Phase 1b+ adds database latency (~50-100ms).

### Q: Can I use this in production?

**A:** Yes! All phases are production-ready. Start with Phase 1a, scale to phases as needed.

### Q: Support for other databases?

**A:** Currently PostgreSQL for Phase 1b+. Phase 1a works with any database via conversion functions.

### Q: Commercial use allowed?

**A:** Yes, MIT License allows commercial use. See LICENSE file.

---

## Next Steps

1. **Start with Phase 1a**: `pip install socrates-ai`
2. **Run examples**: See `EXAMPLES.md`
3. **Read API Reference**: See `API_REFERENCE.md`
4. **Check out the repository**: https://github.com/Socrates/socrates-ai
5. **Join the community**: Discussions and issues on GitHub

---

## Support

- **Documentation**: See `API_REFERENCE.md` and `EXAMPLES.md`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@socrates-ai.dev (when available)

---

## Contributing

Contributions welcome! See CONTRIBUTING.md in the repository.

## License

MIT License - See LICENSE file for details

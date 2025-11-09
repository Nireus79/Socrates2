# ARCHITECTURE EXTENSIBILITY GUIDE

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟡 MEDIUM - Design for future, implement in phases

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Extensibility Principles](#extensibility-principles)
3. [How to Add New Agents](#how-to-add-new-agents)
4. [How to Add New LLM Providers](#how-to-add-new-llm-providers)
5. [How to Extend Database Schema](#how-to-extend-database-schema)
6. [Hook System (Future)](#hook-system-future)
7. [Plugin Architecture (Future)](#plugin-architecture-future)
8. [Extension Examples](#extension-examples)

---

## OVERVIEW

**Goal:** Add new features without refactoring existing code.

### Current Extensibility Score: 85%

✅ **What's Extensible (85%):**
- Agent system (BaseAgent pattern)
- Service layer (add new services)
- Database schema (add new tables)
- API endpoints (add new routes)
- LLM providers (abstract interface)

❌ **What Needs Improvement (15%):**
- Hook system for non-invasive extensions
- Plugin architecture for third-party extensions
- Event-driven communication between agents

---

## EXTENSIBILITY PRINCIPLES

### Principle 1: Open/Closed Principle

**"Open for extension, closed for modification"**

✅ **Good Example:**

```python
# Adding new agent doesn't modify AgentOrchestrator
class NewFeatureAgent(BaseAgent):
    def execute(self, **kwargs):
        # New functionality
        pass

# Register with orchestrator
orchestrator.register_agent("new_feature", NewFeatureAgent)
```

❌ **Bad Example:**

```python
# Modifying AgentOrchestrator to add new agent
class AgentOrchestrator:
    def run_agent(self, agent_name):
        if agent_name == "socratic":
            # ... existing code
        elif agent_name == "new_feature":  # ❌ Modified existing class
            # ... new code
```

### Principle 2: Add Tables, Don't Modify Them

```sql
-- ✅ GOOD: Add new table for Phase 3 feature
CREATE TABLE llm_usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,  -- References existing users table
    provider VARCHAR(50),
    -- ... new columns
);

-- ❌ BAD: Modify existing table
ALTER TABLE users ADD COLUMN llm_preference VARCHAR(50);  -- ❌ Breaking change
```

### Principle 3: Use Metadata Fields

```python
# Flexible metadata using JSONB
class Specification(Base):
    __tablename__ = "specifications"

    id = Column(UUID(as_uuid=True), primary_key=True)
    content = Column(Text, nullable=False)
    metadata = Column(JSONB)  # ✅ Extensible without schema changes

# Phase 0: Basic metadata
spec.metadata = {"source": "user_input"}

# Phase 5: Add semantic embedding (no schema change!)
spec.metadata = {
    "source": "user_input",
    "embedding_vector": [0.1, 0.2, ...],  # ✅ Non-breaking
    "semantic_cluster": "authentication"
}
```

---

## HOW TO ADD NEW AGENTS

### Step 1: Create Agent Class

```python
# agents/my_new_agent.py
from agents.base_agent import BaseAgent
from llm.llm_service import LLMService

class MyNewAgent(BaseAgent):
    """
    New agent for [specific functionality].

    Phase: [Phase number when this agent is added]
    Dependencies: [List of dependencies]
    """

    def __init__(self, db, llm_service: LLMService):
        super().__init__(db, llm_service)
        self.name = "my_new_agent"

    def execute(self, **kwargs):
        """
        Execute agent logic.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            Agent-specific result
        """
        # Agent logic here
        pass

    def validate(self, **kwargs) -> dict:
        """Validate agent can execute with given parameters."""
        return {"is_valid": True, "errors": []}
```

### Step 2: Register Agent

```python
# services/agent_orchestrator.py
from agents.my_new_agent import MyNewAgent

class AgentOrchestrator:
    def __init__(self, db, llm_service):
        self.db = db
        self.llm_service = llm_service
        self.agents = {}

        # Register agents
        self._register_agents()

    def _register_agents(self):
        """Register all agents."""
        # Phase 0 agents
        self.register_agent("socratic", SocraticAgent)
        self.register_agent("spec_extractor", SpecificationExtractorAgent)

        # Phase X: New agent
        self.register_agent("my_new_agent", MyNewAgent)  # ✅ Just add here

    def register_agent(self, name: str, agent_class):
        """Register agent by name."""
        self.agents[name] = agent_class(self.db, self.llm_service)
```

### Step 3: Use Agent

```python
# Anywhere in code
orchestrator = AgentOrchestrator(db, llm_service)
result = orchestrator.run_agent("my_new_agent", param1="value1")
```

**No modifications to existing agents required!**

---

## HOW TO ADD NEW LLM PROVIDERS

### Step 1: Implement LLMProvider Interface

```python
# llm/providers/my_provider.py
from llm.base_provider import LLMProvider, LLMResponse

class MyProvider(LLMProvider):
    """Implementation for MyLLM API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.MY_PROVIDER_API_KEY
        self.client = MyLLMClient(api_key=self.api_key)

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using MyLLM."""
        response = self.client.complete(prompt=prompt, **kwargs)

        return LLMResponse(
            content=response.text,
            model=response.model,
            tokens_used=response.tokens,
            finish_reason=response.finish_reason,
            metadata={}
        )

    # Implement other required methods...
```

### Step 2: Register Provider

```python
# llm/llm_service.py
from llm.providers.my_provider import MyProvider

class LLMService:
    def _create_provider(self, provider_name: str):
        providers = {
            "claude": ClaudeProvider,
            "openai": OpenAIProvider,
            "my_provider": MyProvider,  # ✅ Just add here
        }

        provider_class = providers.get(provider_name)
        return provider_class()
```

### Step 3: Configure

```bash
# .env
DEFAULT_LLM_PROVIDER=my_provider
MY_PROVIDER_API_KEY=your-api-key
```

**No modifications to existing services required!**

---

## HOW TO EXTEND DATABASE SCHEMA

### Non-Breaking Extensions

```sql
-- ✅ Add new table (safe)
CREATE TABLE new_feature_data (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),  -- Link to existing
    feature_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ✅ Add new column with default (safe)
ALTER TABLE projects
ADD COLUMN new_feature_enabled BOOLEAN DEFAULT false;

-- ✅ Add new index (safe)
CREATE INDEX idx_projects_new_column ON projects(new_feature_enabled)
WHERE new_feature_enabled = true;

-- ✅ Add new ENUM value (PostgreSQL specific, safe)
ALTER TYPE phase_type ADD VALUE 'new_phase';
```

### Breaking Changes (Avoid!)

```sql
-- ❌ Rename column (breaks existing code)
ALTER TABLE projects RENAME COLUMN name TO project_name;

-- ❌ Drop column (data loss)
ALTER TABLE projects DROP COLUMN description;

-- ❌ Change column type (risky)
ALTER TABLE projects ALTER COLUMN maturity_score TYPE BIGINT;

-- ❌ Add NOT NULL column without default (fails on existing rows)
ALTER TABLE projects ADD COLUMN required_field VARCHAR(100) NOT NULL;
```

### Safe Migration Pattern

```python
# Phase N migration: Add new table
def upgrade():
    op.create_table(
        'new_feature_data',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id')),
        sa.Column('data', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('new_feature_data')
```

---

## HOOK SYSTEM (FUTURE)

### Concept

Allow non-invasive extensions via hooks.

```python
# Phase X: Hook system
class HookManager:
    """Manage extension hooks."""

    def __init__(self):
        self.hooks = defaultdict(list)

    def register_hook(self, hook_name: str, callback):
        """Register callback for hook."""
        self.hooks[hook_name].append(callback)

    def trigger_hook(self, hook_name: str, **context):
        """Trigger all callbacks for hook."""
        for callback in self.hooks[hook_name]:
            callback(**context)

# Usage in code
hook_manager = HookManager()

# Extension point: Before specification saved
@hook_manager.register_hook("before_spec_save")
def validate_custom_rules(spec, project, **kwargs):
    # Custom validation logic
    if not custom_validation(spec):
        raise ValueError("Custom validation failed")

# In service
class SpecificationService:
    def save_specification(self, spec):
        # Trigger hook
        hook_manager.trigger_hook("before_spec_save", spec=spec, project=project)

        # Save
        db.add(spec)
        db.commit()
```

### Standard Hooks

```python
# Proposed hooks for future
STANDARD_HOOKS = [
    # Specification hooks
    "before_spec_save",
    "after_spec_save",
    "before_spec_delete",
    "after_spec_delete",

    # Project hooks
    "before_project_create",
    "after_project_create",
    "before_phase_advance",
    "after_phase_advance",

    # Generation hooks
    "before_generation_start",
    "after_generation_complete",
    "before_file_generate",
    "after_file_generate",

    # LLM hooks
    "before_llm_call",
    "after_llm_call",
]
```

---

## PLUGIN ARCHITECTURE (FUTURE)

### Plugin Structure

```python
# plugins/my_plugin/plugin.py
from core.plugin_base import PluginBase

class MyPlugin(PluginBase):
    """
    My custom plugin.

    Extends Socrates2 with custom functionality.
    """

    name = "my_plugin"
    version = "1.0.0"
    author = "Your Name"

    def initialize(self):
        """Initialize plugin (called once on load)."""
        # Register hooks
        self.hook_manager.register_hook("before_spec_save", self.validate_spec)

        # Register custom agent
        self.agent_orchestrator.register_agent("my_agent", MyCustomAgent)

    def validate_spec(self, spec, **kwargs):
        """Custom specification validation."""
        # Plugin logic
        pass

# Plugin manifest
# plugins/my_plugin/manifest.json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "Custom plugin for XYZ",
    "author": "Your Name",
    "entry_point": "plugin.MyPlugin",
    "dependencies": [],
    "permissions": ["read_specs", "write_specs"]
}
```

---

## EXTENSION EXAMPLES

### Example 1: Add Semantic Search (Phase 5)

```python
# 1. Add vector column to existing table (non-breaking)
# Migration
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        'specifications',
        sa.Column('embedding', Vector(384), nullable=True)  # ✅ Nullable
    )

# 2. Create new service (doesn't modify existing)
class SemanticSearchService:
    def __init__(self, db):
        self.db = db
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def embed_specification(self, spec: Specification):
        """Add embedding to specification."""
        embedding = self.embedder.encode(spec.content)
        spec.embedding = embedding  # ✅ Use new column
        self.db.commit()

    def search_similar(self, query: str, limit: int = 10):
        """Search similar specifications."""
        query_embedding = self.embedder.encode(query)

        results = self.db.execute(
            """
            SELECT id, content,
                   embedding <-> :query_embedding as distance
            FROM specifications
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT :limit
            """,
            {"query_embedding": query_embedding, "limit": limit}
        )

        return results.fetchall()

# 3. Use in existing code (optional)
# Existing code continues to work without embeddings
# New code can use semantic search
```

### Example 2: Add Custom Question Templates (Phase 5)

```python
# 1. Add new table (doesn't modify existing)
CREATE TABLE custom_question_templates (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    role VARCHAR(50),
    template TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

# 2. Extend SocraticAgent (doesn't modify base)
class SocraticAgent(BaseAgent):
    def get_question(self, role: str, user_id: str):
        # Try custom templates first
        custom = self._get_custom_template(role, user_id)
        if custom:
            return custom

        # Fall back to default templates
        return self._get_default_template(role)

    def _get_custom_template(self, role: str, user_id: str):
        """Get user's custom template (Phase 5 feature)."""
        result = self.db.query(CustomQuestionTemplate).filter_by(
            user_id=user_id,
            role=role
        ).first()

        return result.template if result else None
```

---

## VERIFICATION CHECKLIST

Before implementing extensions:

- [ ] Extension uses BaseAgent pattern (for agents)
- [ ] Extension uses LLMProvider interface (for LLMs)
- [ ] Extension adds new tables, doesn't modify existing
- [ ] Extension uses nullable columns if adding to existing tables
- [ ] Extension doesn't break existing tests
- [ ] Extension has own tests
- [ ] Extension documented
- [ ] Migration strategy clear (upgrade + downgrade)

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This guide ensures Socrates2 remains extensible through Phase 0-6 without refactoring.*

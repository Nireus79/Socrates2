# Archive Good Patterns: What To Keep From Old Repo

**Reference:** [Old Repo Archive](https://github.com/Nireus79/Socrates)

---

## ✅ PATTERN #1: BaseAgent with Dependency Injection

**File:** `backend_for_audit/src/agents/base.py:874`

```python
class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        self.agent_id = agent_id
        self.name = name
        self.services = services
        self.db = services.get_database()
        self.logger = services.get_logger(f"agent.{agent_id}")
        self.claude_client = services.get_claude_client()

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        pass

    def process_request(self, action: str, data: Dict) -> Dict:
        method_name = f"_{action}"
        return getattr(self, method_name)(data)
```

**Why It's Good:**
- ✅ Standardized interface for all agents
- ✅ Dependency injection (testable)
- ✅ Capability declaration (discoverable)
- ✅ Consistent request routing

**Use In Socrates:** Keep this exact pattern

---

## ✅ PATTERN #2: AgentOrchestrator with Capability Routing

**File:** `backend_for_audit/src/agents/orchestrator.py`

```python
class AgentOrchestrator:
    def __init__(self, services):
        self.agents = {}

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_id] = agent

    def route_request(self, agent_id, action, data):
        agent = self.agents[agent_id]

        # Validate capability
        if action not in agent.get_capabilities():
            return error('Unsupported action')

        return agent.process_request(action, data)
```

**Why It's Good:**
- ✅ Central routing (single entry point)
- ✅ Capability validation
- ✅ Easy to add quality control gates

**Use In Socrates:** Keep, enhance with mandatory quality control

---

## ✅ PATTERN #3: Database Models with BaseModel

**File:** `backend_for_audit/src/models/base.py`

```python
class BaseModel(Base):
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

**Why It's Good:**
- ✅ UUID primary keys (distributed-friendly)
- ✅ Automatic timestamps
- ✅ Easy serialization

**Use In Socrates:** Keep exactly as is

---

## ✅ PATTERN #4: Quality Control Integration Points

**File:** `backend_for_audit/src/agents/quality_analyzer.py:1,116 lines`

```python
class QualityAnalyzer:
    def analyze_question(self, question):
        # Detect bias patterns
        bias_score = self._calculate_bias(question)
        return QuestionAnalysis(bias_score=bias_score)

    def analyze_session(self, session_id):
        # Identify coverage gaps
        gaps = self._identify_gaps(session_id)
        return SessionAnalysis(gaps=gaps)
```

**Why It's Good:**
- ✅ Separates quality checking from agent logic
- ✅ Can be enhanced without changing agents
- ✅ Clear success/failure criteria

**Use In Socrates:** Keep concept, integrate into orchestrator as mandatory

---

## ✅ PATTERN #5: Specification Storage Design

**File:** `backend_for_audit/src/models/specification.py`

```python
class Specification:
    project_id = Column(String(36), ForeignKey('projects.id'))
    category = Column(Enum(SpecCategory))
    key = Column(String(255))
    value = Column(Text)
    confidence = Column(Float)
    source = Column(String(50))  # 'socratic_question', 'direct_chat'
    version = Column(Integer)  # For conflict tracking
```

**Why It's Good:**
- ✅ Flexible key-value storage
- ✅ Category grouping for maturity
- ✅ Confidence scoring
- ✅ Version tracking for conflicts

**Use In Socrates:** Keep this schema

---

## ✅ PATTERN #6: Socratic7.py Monolithic Simplicity

**File:** `ARCHIVE/Socratic7.py:3,778 lines`

```python
# Everything in one file:
# - Agent classes
# - Database setup
# - API routes
# - Main loop
```

**Why It's Good:**
- ✅ No circular imports possible
- ✅ Easy to understand data flow
- ✅ Proof that concept works
- ✅ Easy to debug (search one file)

**Use In Socrates:**
- Don't make monolithic
- But keep simplicity principle
- Clear data flow like Socratic7
- Structured files like backend_for_audit

---

## 📋 Summary: Patterns To Keep

| Pattern | From | Keep? | Notes |
|---------|------|-------|-------|
| BaseAgent | backend_for_audit | ✅ Yes | Exact pattern |
| AgentOrchestrator | backend_for_audit | ✅ Yes | Add mandatory QC |
| ServiceContainer | backend_for_audit | ✅ Yes | Remove fallbacks |
| BaseModel | backend_for_audit | ✅ Yes | Exact pattern |
| Specification schema | backend_for_audit | ✅ Yes | Exact schema |
| Quality Analyzer | backend_for_audit | ✅ Yes | Integrate mandatory |
| Monolithic simplicity | Socratic7.py | ⚠️ Principle only | Use in structure decisions |

---

**See Also:**
- [ARCHIVE_ANTIPATTERNS.md](ARCHIVE_ANTIPATTERNS.md) - What NOT to do
- [INTERCONNECTIONS_MAP.md](INTERCONNECTIONS_MAP.md) - How components connect

# Phase 2: Core Agents (Minimum Viable Socratic Mode)

**Status:** ⏳ PENDING (Awaiting Phase 1 completion)
**Duration:** Estimated 3-4 days
**Goal:** Implement 3 core agents for basic Socratic questioning workflow

---

## 📋 Objectives

1. Implement ProjectManagerAgent (project CRUD)
2. Implement SocraticCounselorAgent (question generation)
3. Implement ContextAnalyzerAgent (spec extraction)
4. Create database models for questions and specifications
5. Implement full Socratic questioning workflow
6. Write comprehensive tests

---

## 🔗 Dependencies

### Depends On (From Phase 1):
```python
from app.core.dependencies import ServiceContainer, get_orchestrator
from app.agents.base import BaseAgent
from app.agents.orchestrator import AgentOrchestrator
from app.models.base import BaseModel
from app.models.user import User
from app.models.project import Project
from app.models.session import Session
```

### Provides To (For Phase 3):
```python
# Agents:
from app.agents.project import ProjectManagerAgent
from app.agents.socratic import SocraticCounselorAgent
from app.agents.context import ContextAnalyzerAgent

# Models:
from app.models.question import Question
from app.models.specification import Specification

# Workflow:
# 1. Create project (ProjectManagerAgent)
# 2. Generate question (SocraticCounselorAgent)
# 3. Extract specs from answer (ContextAnalyzerAgent)
# Phase 3 will add conflict detection between steps 3 and saving specs
```

---

## 📦 Deliverables

### 1. Question Model

**File:** `backend/app/models/question.py`

```python
from sqlalchemy import Column, String, Text, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class QuestionCategory(enum.Enum):
    GOALS = "goals"
    REQUIREMENTS = "requirements"
    TECH_STACK = "tech_stack"
    SCALABILITY = "scalability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    MONITORING = "monitoring"
    DATA_RETENTION = "data_retention"
    DISASTER_RECOVERY = "disaster_recovery"

class Question(BaseModel):
    __tablename__ = "questions"

    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False, index=True)
    text = Column(Text, nullable=False)
    category = Column(Enum(QuestionCategory), nullable=False, index=True)
    context = Column(Text, nullable=True)  # Why this question matters
    quality_score = Column(Float, default=1.0)  # From quality analyzer (Phase 5)

    # Relationships
    project = relationship("Project", back_populates="questions")
    session = relationship("Session", back_populates="questions")
```

**Used By:**
- SocraticCounselorAgent (creates questions)
- ContextAnalyzerAgent (loads question for context)

---

### 2. Specification Model

**File:** `backend/app/models/specification.py`

```python
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.question import QuestionCategory

class Specification(BaseModel):
    __tablename__ = "specifications"

    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False, index=True)
    category = Column(Enum(QuestionCategory), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)  # e.g., "primary_database"
    value = Column(Text, nullable=False)  # e.g., "PostgreSQL 15"
    source = Column(String(50), nullable=False)  # "socratic_question", "direct_chat", "document"
    source_id = Column(String(36), nullable=True)  # question_id or message_id
    confidence = Column(Float, default=0.9)  # 0.0-1.0
    reasoning = Column(Text, nullable=True)  # Why this spec was extracted
    version = Column(Integer, default=1)  # For conflict tracking

    # Relationships
    project = relationship("Project", back_populates="specifications")

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_spec_project_category_key', 'project_id', 'category', 'key'),
    )
```

**Interconnection:**
- Phase 3: ConflictDetectorAgent will query by (project_id, category, key)
- Phase 4: CodeGeneratorAgent will query all specs for project
- Phase 4: Maturity calculation based on specs count per category

---

### 3. ProjectManagerAgent

**File:** `backend/app/agents/project.py`

```python
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.project import Project, ProjectPhase, ProjectStatus
from app.models.user import User

class ProjectManagerAgent(BaseAgent):
    """Manages project lifecycle"""

    def get_capabilities(self) -> List[str]:
        return [
            'create_project',
            'get_project',
            'update_project',
            'delete_project',
            'list_projects'
        ]

    def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new project.

        Args:
            data: {
                'user_id': str,
                'name': str,
                'description': str
            }

        Returns:
            {'success': bool, 'project_id': str, 'project': dict}
        """
        user_id = data.get('user_id')
        name = data.get('name')
        description = data.get('description', '')

        # Validate
        if not user_id or not name:
            return {
                'success': False,
                'error': 'user_id and name are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Check user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                'success': False,
                'error': f'User not found: {user_id}',
                'error_code': 'USER_NOT_FOUND'
            }

        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            phase=ProjectPhase.DISCOVERY,
            maturity_score=0.0,
            status=ProjectStatus.ACTIVE
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        self.logger.info(f"Created project: {project.id} for user: {user_id}")

        return {
            'success': True,
            'project_id': project.id,
            'project': project.to_dict()
        }

    def _get_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get project by ID"""
        project_id = data.get('project_id')

        if not project_id:
            return {
                'success': False,
                'error': 'project_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'PROJECT_NOT_FOUND'
            }

        return {
            'success': True,
            'project': project.to_dict()
        }

    def _list_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List all projects for user"""
        user_id = data.get('user_id')

        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        projects = self.db.query(Project).filter(
            Project.user_id == user_id
        ).order_by(Project.created_at.desc()).all()

        return {
            'success': True,
            'projects': [p.to_dict() for p in projects],
            'count': len(projects)
        }
```

**Data Flow:**
```
API: POST /api/projects → orchestrator.route_request('project', 'create_project', {…})
                       → ProjectManagerAgent._create_project()
                       → Saves to database
                       → Returns project_id
Phase 2+: Create Session → Ask Question → Extract Specs (all need project_id)
```

---

### 4. SocraticCounselorAgent

**File:** `backend/app/agents/socratic.py`

```python
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.project import Project
from app.models.session import Session
from app.models.question import Question, QuestionCategory
from app.models.specification import Specification

class SocraticCounselorAgent(BaseAgent):
    """Generates Socratic questions to gather requirements"""

    def get_capabilities(self) -> List[str]:
        return [
            'generate_question',
            'generate_questions_batch'
        ]

    def _generate_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate next Socratic question based on project context.

        Args:
            data: {
                'project_id': str,
                'session_id': str
            }

        Returns:
            {'success': bool, 'question': dict}
        """
        project_id = data.get('project_id')
        session_id = data.get('session_id')

        if not project_id or not session_id:
            return {
                'success': False,
                'error': 'project_id and session_id are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Load project context
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                'success': False,
                'error': f'Project not found: {project_id}',
                'error_code': 'PROJECT_NOT_FOUND'
            }

        # Load existing specifications
        existing_specs = self.db.query(Specification).filter(
            Specification.project_id == project_id
        ).all()

        # Load previous questions
        previous_questions = self.db.query(Question).filter(
            Question.project_id == project_id
        ).order_by(Question.created_at.desc()).limit(10).all()

        # Calculate coverage per category
        coverage = self._calculate_coverage(existing_specs)

        # Identify next category to focus on (lowest coverage)
        next_category = self._identify_next_category(coverage)

        # Build prompt for Claude
        prompt = self._build_question_generation_prompt(
            project, existing_specs, previous_questions, next_category
        )

        # Call Claude API
        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        import json
        question_data = json.loads(response.content[0].text)

        # Save question
        question = Question(
            project_id=project_id,
            session_id=session_id,
            text=question_data['text'],
            category=question_data['category'],
            context=question_data.get('context'),
            quality_score=1.0  # Phase 5 will add quality analysis
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)

        self.logger.info(f"Generated question {question.id} for project {project_id}")

        return {
            'success': True,
            'question': question.to_dict(),
            'question_id': question.id
        }

    def _calculate_coverage(self, specs: List[Specification]) -> Dict[str, float]:
        """Calculate coverage percentage per category"""
        max_per_category = {
            QuestionCategory.GOALS: 10,
            QuestionCategory.REQUIREMENTS: 15,
            QuestionCategory.TECH_STACK: 12,
            QuestionCategory.SCALABILITY: 8,
            QuestionCategory.SECURITY: 10,
            QuestionCategory.PERFORMANCE: 8,
            QuestionCategory.TESTING: 8,
            QuestionCategory.MONITORING: 6,
            QuestionCategory.DATA_RETENTION: 5,
            QuestionCategory.DISASTER_RECOVERY: 8
        }

        # Count specs per category
        spec_counts = {}
        for spec in specs:
            category = spec.category
            spec_counts[category] = spec_counts.get(category, 0) + 1

        # Calculate coverage
        coverage = {}
        for category, max_count in max_per_category.items():
            count = spec_counts.get(category, 0)
            coverage[category] = min(count / max_count, 1.0) * 100

        return coverage

    def _identify_next_category(self, coverage: Dict) -> QuestionCategory:
        """Identify category with lowest coverage"""
        if not coverage:
            return QuestionCategory.GOALS

        return min(coverage, key=coverage.get)

    def _build_question_generation_prompt(
        self,
        project: Project,
        specs: List[Specification],
        previous_questions: List[Question],
        next_category: QuestionCategory
    ) -> str:
        """Build prompt for Claude to generate question"""
        prompt = f"""You are a Socratic counselor helping gather requirements for a software project.

PROJECT CONTEXT:
- Name: {project.name}
- Description: {project.description}
- Phase: {project.phase.value}
- Maturity: {project.maturity_score}%

EXISTING SPECIFICATIONS:
{self._format_specs(specs)}

PREVIOUS QUESTIONS ASKED:
{self._format_questions(previous_questions)}

NEXT FOCUS AREA: {next_category.value}

TASK:
Generate the next question focusing on: {next_category.value}

REQUIREMENTS:
1. Ask about ONE specific aspect of {next_category.value}
2. Keep question concise and clear
3. Avoid assuming solutions (no "should we use X?")
4. Make it open-ended to encourage detailed answers
5. Provide context about why this matters

Return JSON format:
{{
  "text": "the question text",
  "category": "{next_category.value}",
  "context": "brief explanation of why this question matters"
}}
"""
        return prompt

    def _format_specs(self, specs: List[Specification]) -> str:
        """Format specs for prompt"""
        if not specs:
            return "None yet"

        lines = []
        for spec in specs[:20]:  # Limit to prevent huge prompts
            lines.append(f"- {spec.category.value}: {spec.key} = {spec.value}")
        return "\n".join(lines)

    def _format_questions(self, questions: List[Question]) -> str:
        """Format questions for prompt"""
        if not questions:
            return "None yet"

        lines = []
        for q in questions[:10]:
            lines.append(f"- [{q.category.value}] {q.text}")
        return "\n".join(lines)
```

**Interconnection:**
- Depends on: Project (exists), Session (active), Specification (previous answers)
- Provides to: ContextAnalyzerAgent (question context), User (via API)

---

### 5. ContextAnalyzerAgent

**File:** `backend/app/agents/context.py`

```python
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.project import Project
from app.models.session import Session
from app.models.question import Question
from app.models.specification import Specification

class ContextAnalyzerAgent(BaseAgent):
    """Extracts specifications from user answers"""

    def get_capabilities(self) -> List[str]:
        return [
            'extract_specifications',
            'analyze_context'
        ]

    def _extract_specifications(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specifications from user answer.

        Args:
            data: {
                'session_id': str,
                'question_id': str,
                'answer': str,
                'user_id': str
            }

        Returns:
            {'success': bool, 'specs_extracted': int, 'specifications': list}
        """
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        answer = data.get('answer')

        # Validate
        if not all([session_id, question_id, answer]):
            return {
                'success': False,
                'error': 'session_id, question_id, and answer are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Load context
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return {
                'success': False,
                'error': f'Session not found: {session_id}',
                'error_code': 'SESSION_NOT_FOUND'
            }

        project = self.db.query(Project).filter(Project.id == session.project_id).first()
        question = self.db.query(Question).filter(Question.id == question_id).first()

        # Load existing specs
        existing_specs = self.db.query(Specification).filter(
            Specification.project_id == project.id
        ).all()

        # Build extraction prompt
        prompt = self._build_extraction_prompt(question, answer, existing_specs)

        # Call Claude API
        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        import json
        extracted_specs = json.loads(response.content[0].text)

        # NOTE: Phase 3 will add conflict detection HERE
        # For now, save directly

        # Save specifications
        saved_specs = []
        for spec_data in extracted_specs:
            spec = Specification(
                project_id=project.id,
                category=spec_data['category'],
                key=spec_data['key'],
                value=spec_data['value'],
                source='socratic_question',
                source_id=question_id,
                confidence=spec_data.get('confidence', 0.9),
                reasoning=spec_data.get('reasoning')
            )
            self.db.add(spec)
            saved_specs.append(spec)

        self.db.commit()

        # Update maturity
        new_maturity = self._calculate_maturity(project.id)
        project.maturity_score = new_maturity
        self.db.commit()

        self.logger.info(f"Extracted {len(saved_specs)} specs from answer to question {question_id}")

        return {
            'success': True,
            'specs_extracted': len(saved_specs),
            'specifications': [s.to_dict() for s in saved_specs],
            'maturity_score': new_maturity
        }

    def _build_extraction_prompt(
        self,
        question: Question,
        answer: str,
        existing_specs: List[Specification]
    ) -> str:
        """Build prompt for spec extraction"""
        prompt = f"""Extract structured specifications from the user's answer.

QUESTION ASKED:
"{question.text}"

USER ANSWER:
"{answer}"

EXISTING SPECIFICATIONS:
{self._format_existing_specs(existing_specs[:30])}

TASK:
Extract ALL specifications mentioned in the answer. Return JSON array:
[
  {{
    "category": "{question.category.value}",
    "key": "descriptive_key",
    "value": "the actual value/requirement",
    "confidence": 0.0-1.0,
    "reasoning": "why this was extracted"
  }}
]

IMPORTANT:
- Include EVERY piece of information, even implied
- Assign confidence based on how explicit it is
- Use snake_case for keys
- Be specific with values
"""
        return prompt

    def _format_existing_specs(self, specs: List[Specification]) -> str:
        """Format existing specs for prompt"""
        if not specs:
            return "None yet"

        lines = []
        for spec in specs:
            lines.append(f"- {spec.category.value}.{spec.key} = {spec.value}")
        return "\n".join(lines)

    def _calculate_maturity(self, project_id: str) -> float:
        """Calculate project maturity based on spec coverage"""
        specs = self.db.query(Specification).filter(
            Specification.project_id == project_id
        ).all()

        # Weight per category
        max_per_category = {
            'goals': 10, 'requirements': 15, 'tech_stack': 12,
            'scalability': 8, 'security': 10, 'performance': 8,
            'testing': 8, 'monitoring': 6, 'data_retention': 5,
            'disaster_recovery': 8
        }
        total_weight = sum(max_per_category.values())  # 90

        # Count per category
        category_scores = {}
        for spec in specs:
            category = spec.category.value
            if category not in category_scores:
                category_scores[category] = 0
            # Add confidence-weighted score
            category_scores[category] += spec.confidence

        # Calculate maturity
        total_score = 0
        for category, max_score in max_per_category.items():
            score = min(category_scores.get(category, 0), max_score)
            total_score += score

        maturity = (total_score / total_weight) * 100
        return round(maturity, 2)
```

**Data Flow:**
```
User answers question
     ↓
API: POST /api/sessions/{id}/answer
     ↓
orchestrator.route_request('context', 'extract_specifications', {…})
     ↓
ContextAnalyzerAgent._extract_specifications()
     ↓
1. Load question + answer + existing specs
2. Call Claude API to extract structured specs
3. [Phase 3: Check conflicts HERE]
4. Save specs to database
5. Update project.maturity_score
     ↓
Return: {'specs_extracted': N, 'maturity_score': X%}
```

---

## 🧪 Testing Requirements

**File:** `backend/tests/test_phase_2_core_agents.py`

```python
import pytest
from app.agents.project import ProjectManagerAgent
from app.agents.socratic import SocraticCounselorAgent
from app.agents.context import ContextAnalyzerAgent
from app.models.project import Project
from app.models.question import Question
from app.models.specification import Specification

def test_project_manager_create():
    """Test can create project"""
    services = get_test_services()
    agent = ProjectManagerAgent("project", "Project Manager", services)
    orchestrator = AgentOrchestrator(services)
    orchestrator.register_agent(agent)

    result = orchestrator.route_request('project', 'create_project', {
        'user_id': test_user.id,
        'name': 'Test Project',
        'description': 'Test description'
    })

    assert result['success'] == True
    assert 'project_id' in result
    assert result['project']['maturity_score'] == 0.0

def test_socratic_generate_question():
    """Test can generate question"""
    services = get_test_services()
    agent = SocraticCounselorAgent("socratic", "Socratic Counselor", services)

    result = agent.process_request('generate_question', {
        'project_id': test_project.id,
        'session_id': test_session.id
    })

    assert result['success'] == True
    assert 'question' in result
    assert result['question']['text'] is not None
    assert result['question']['category'] in [c.value for c in QuestionCategory]

def test_context_extract_specs():
    """Test can extract specifications"""
    services = get_test_services()
    agent = ContextAnalyzerAgent("context", "Context Analyzer", services)

    result = agent.process_request('extract_specifications', {
        'session_id': test_session.id,
        'question_id': test_question.id,
        'answer': 'I want to use Python with FastAPI for the backend API'
    })

    assert result['success'] == True
    assert result['specs_extracted'] > 0
    assert len(result['specifications']) > 0
    # Should extract: language=Python, framework=FastAPI

def test_full_workflow():
    """Integration test: Create project → Ask question → Submit answer → Extract specs"""
    # 1. Create project
    result = orchestrator.route_request('project', 'create_project', {...})
    project_id = result['project_id']

    # 2. Generate question
    result = orchestrator.route_request('socratic', 'generate_question', {
        'project_id': project_id, 'session_id': session_id
    })
    question_id = result['question_id']

    # 3. Submit answer and extract specs
    result = orchestrator.route_request('context', 'extract_specifications', {
        'question_id': question_id,
        'answer': 'I want an e-commerce platform for local artisans...'
    })

    assert result['success'] == True
    assert result['specs_extracted'] > 0
    assert result['maturity_score'] > 0
```

**Test Coverage Required:** Minimum 90%

---

## ✅ Verification Checklist

- [ ] Can create ProjectManagerAgent and register with orchestrator
- [ ] Can create project via orchestrator
- [ ] Project saved to database with correct fields
- [ ] Can create SocraticCounselorAgent and register
- [ ] Can generate question via Claude API
- [ ] Question saved to database
- [ ] Question targets lowest-coverage category
- [ ] Can create ContextAnalyzerAgent and register
- [ ] Can extract specs from answer via Claude API
- [ ] Specs saved to database
- [ ] Maturity score updated after spec extraction
- [ ] Integration test passes: Create → Ask → Answer → Specs saved
- [ ] All tests pass with ≥90% coverage

---

## 🎯 Success Criteria

Phase 2 complete when:
1. ✅ All 3 agents working
2. ✅ Full Socratic workflow functional
3. ✅ Specs extracted and saved
4. ✅ Maturity calculation working
5. ✅ Integration test passes
6. ✅ All verification items checked

---

**Previous Phase:** [PHASE_1.md](PHASE_1.md) - Infrastructure
**Next Phase:** [PHASE_3.md](PHASE_3.md) - Conflict Detection

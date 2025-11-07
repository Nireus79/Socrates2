# Phase 5: Quality Control System (Anti-Greedy Algorithm)

**Status:** ✅ COMPLETE
**Duration:** 4-5 days
**Goal:** Prevent greedy algorithm decisions through quality gates

---

## ⚠️ CRITICAL: Read Before Implementation

**MANDATORY:** Review [CRITICAL_LESSONS_LEARNED.md](../CRITICAL_LESSONS_LEARNED.md) before starting Phase 5.

**Critical Checklist for Phase 5:**

### Models (quality_metrics table):
- [ ] Inherits from BaseModel? → Include id, created_at, updated_at in migration
- [ ] AVOID column names: metadata, query, session
- [ ] Use quality_metadata NOT just "metadata"

### Migration (Phase 5 migrations):
- [ ] Add `import os` and `_should_run()` function
- [ ] Check DATABASE_URL contains "socrates_specs"
- [ ] Add check to BOTH upgrade() and downgrade()
- [ ] Verify BaseModel columns if model inherits

### Tests (test_phase_5_*.py):
- [ ] Use `auth_session` NOT `db_auth`
- [ ] Use `specs_session` NOT `db_specs`
- [ ] Use `mock_claude_client` fixture, NOT @patch decorators
- [ ] DO NOT patch instance attributes

### QualityControllerAgent:
- [ ] Accept ServiceContainer in __init__
- [ ] Store as self.services (instance attribute)
- [ ] Get database via self.services.get_database_specs()
- [ ] Get Claude client via self.services.get_claude_client()

**Database:** All Phase 5 tables go to `socrates_specs`

---

## 📋 Objectives

1. Create QualityControllerAgent
2. Implement bias detection for questions
3. Implement coverage gap analysis
4. Implement path optimization
5. Integrate quality gates into AgentOrchestrator
6. Block operations that fail quality checks

---

## 🔗 Dependencies

**From Phase 4:**
- Working question generation
- Working spec extraction
- Working code generation

**Enhancement:**
- Add quality gates BEFORE major operations

---

## 🌐 API Endpoints

This phase implements quality control gates. See [API_ENDPOINTS.md](../foundation_docs/API_ENDPOINTS.md) for complete API documentation.

**Implemented in Phase 5:**
- GET /api/v1/quality/project/{id}/metrics - Get quality metrics (lines 640-665 in API_ENDPOINTS.md)
- GET /api/v1/quality/project/{id}/analysis - Full quality analysis (lines 670-710 in API_ENDPOINTS.md)
- GET /api/v1/quality/project/{id}/recommendations - Get recommendations (lines 715-745 in API_ENDPOINTS.md)

**Testing Endpoints:**
```bash
# Get quality metrics
curl -X GET http://localhost:8000/api/v1/quality/project/{project_id}/metrics \
  -H "Authorization: Bearer <token>"

# Get full analysis
curl -X GET http://localhost:8000/api/v1/quality/project/{project_id}/analysis \
  -H "Authorization: Bearer <token>"

# Get recommendations
curl -X GET http://localhost:8000/api/v1/quality/project/{project_id}/recommendations \
  -H "Authorization: Bearer <token>"
```

---

## 📦 Key Components

### 1. Question Quality Analysis

```python
class QualityControllerAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bias patterns
        self.solution_bias = ["should we use", "let's use", "django", "react"]
        self.technology_bias = ["best framework", "industry standard"]
        self.leading_patterns = ["you need", "obviously", "clearly"]

    def _analyze_question(self, data):
        """Analyze question for bias"""
        question_text = data['question_text'].lower()

        # Detect bias
        bias_count = sum(1 for pattern in self.solution_bias if pattern in question_text)
        bias_score = min(1.0, bias_count * 0.3)

        if bias_score > 0.5:
            # Generate alternatives
            alternatives = self._generate_alternatives(question_text)
            return {
                'success': False,
                'is_blocking': True,
                'bias_score': bias_score,
                'reason': f'Question has solution bias (score: {bias_score})',
                'suggested_alternatives': alternatives
            }

        return {
            'success': True,
            'is_blocking': False,
            'bias_score': bias_score,
            'quality_score': 1.0 - bias_score
        }
```

### 2. Coverage Gap Analysis

```python
def _analyze_coverage(self, data):
    """Analyze if all categories adequately covered"""
    project_id = data['project_id']
    specs = self.db.query(Specification).filter_by(project_id=project_id).all()

    # Calculate coverage per category
    coverage = {}
    for category in QuestionCategory:
        category_specs = [s for s in specs if s.category == category]
        coverage[category.value] = len(category_specs)

    # Identify gaps (< 3 specs)
    gaps = [cat for cat, count in coverage.items() if count < 3]

    if len(gaps) > 5:
        return {
            'success': False,
            'is_blocking': True,
            'reason': f'Too many gaps: {gaps}',
            'coverage_gaps': gaps,
            'suggested_actions': [f'Ask questions about: {gap}' for gap in gaps[:3]]
        }

    return {
        'success': True,
        'is_blocking': False,
        'coverage_gaps': gaps
    }
```

### 3. Path Optimization

```python
def _compare_paths(self, data):
    """Generate all possible paths and recommend best"""
    goal = data['goal']  # e.g., "generate_code"
    project_id = data['project_id']

    paths = [
        {
            'id': 'thorough',
            'steps': [
                {'action': 'ask_questions', 'tokens': 800},
                {'action': 'design_architecture', 'tokens': 1200},
                {'action': 'generate_code', 'tokens': 5000},
                {'action': 'test', 'tokens': 1000}
            ],
            'direct_cost': 8000,
            'rework_cost': 0,  # Complete specs = no rework
            'total_cost': 8000,
            'risk': 'LOW'
        },
        {
            'id': 'greedy',
            'steps': [
                {'action': 'generate_code', 'tokens': 5000}
            ],
            'direct_cost': 5000,
            'rework_cost': 5000,  # Missing specs = lots of rework
            'total_cost': 10000,
            'risk': 'HIGH'
        }
    ]

    # Recommend lowest total cost
    recommended = min(paths, key=lambda p: p['total_cost'])

    return {
        'success': True,
        'paths': paths,
        'recommended_path': recommended
    }
```

---

## 🔄 Integration with Orchestrator

**Modified `AgentOrchestrator.route_request()`:**

```python
def route_request(self, agent_id, action, data):
    # ... existing validation ...

    # NEW: Quality Control Gate
    if self._is_major_operation(agent_id, action):
        quality_result = self.quality_controller.verify(agent_id, action, data)

        if quality_result.get('is_blocking'):
            self.logger.warning(f"Quality control blocked {agent_id}.{action}")
            return {
                'success': False,
                'blocked_by': 'quality_control',
                'reason': quality_result['reason'],
                'quality_metadata': quality_result
            }

    # Route to agent
    result = agent.process_request(action, data)
    return result

def _is_major_operation(self, agent_id, action):
    """Operations that need quality control"""
    major_ops = {
        'socratic': ['generate_question'],
        'context': ['extract_specifications'],
        'code': ['generate_code'],
        'optimizer': ['optimize_architecture']
    }
    return agent_id in major_ops and action in major_ops[agent_id]
```

---

## 🧪 Critical Tests

```python
def test_blocks_biased_question():
    """Test quality control blocks biased question"""
    result = quality_controller.process_request('analyze_question', {
        'question_text': 'Should we use React for the frontend? It's the best framework.'
    })
    assert result['success'] == False
    assert result['is_blocking'] == True
    assert result['bias_score'] > 0.5

def test_blocks_premature_code_gen():
    """Test blocks code generation when coverage gaps exist"""
    result = quality_controller.process_request('analyze_coverage', {
        'project_id': incomplete_project.id
    })
    assert result['is_blocking'] == True
    assert len(result['coverage_gaps']) > 0

def test_path_recommends_thorough():
    """Test path optimizer recommends thorough over greedy"""
    result = quality_controller.process_request('compare_paths', {
        'goal': 'generate_code',
        'project_id': project.id
    })
    assert result['recommended_path']['id'] == 'thorough'
    assert result['recommended_path']['total_cost'] < 10000
```

---

## ✅ Verification

- [ ] QualityControllerAgent created
- [ ] Bias detection works
- [ ] Coverage analysis works
- [ ] Path optimization works
- [ ] Integrated with orchestrator
- [ ] Blocks biased questions
- [ ] Blocks premature operations
- [ ] Tests pass

---

**Previous:** [PHASE_4.md](PHASE_4.md)
**Next:** [PHASE_6.md](./PHASE_6.md) - User Learning & Adaptation

# Socrates2 - Detailed Implementation Plan for 287 Tests

**Current Status:** 245/287 tests passing (85.4%)
**Target:** 287/287 tests passing (100%)
**Remaining Work:** 42 failures, 17 errors (59 total test issues)

---

## Executive Summary

The test suite defines the complete feature set. Each failing test specifies exactly what method needs to be implemented and what it should return. This document maps each failing test to the specific implementation work required.

**Key Principle:** Do not modify tests to pass - implement the actual functionality they specify.

---

## Part 1: Phase 2 - Core Agents (6 failures)

### Current Status
- 15/16 Phase 2 tests passing
- Agent infrastructure working
- Core agent classes exist but some methods incomplete

### 1.1: test_full_workflow_integration
**Location:** `tests/test_phase_2_core_agents.py:293`
**Failure:** `DetachedInstanceError: Instance <Session at 0x254a9251e80> is not bound to a Session`

**Root Cause:** Session scope mismatch - test closes session before agent methods complete

**Implementation Required:**
```python
# In app/agents/base.py - fix session management
class BaseAgent:
    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # CURRENT: Agent closes session within process_request
        # NEEDED: Return session to caller or keep it open
        # SOLUTION: Don't call db.close() in agent methods
        #          Let dependency injection manage session lifecycle
```

**Fix Steps:**
1. Remove `db.close()` calls from all agent `_method_name()` implementations
2. Let the test/API endpoint manage session lifecycle
3. Keep database references only for the scope of the single request

**Files to Modify:**
- `app/agents/project.py` - line ~399 (finally clause)
- `app/agents/socratic.py` - similar finally clauses
- `app/agents/context.py` - similar finally clauses
- `app/agents/conflict_detector.py` - similar finally clauses

---

## Part 2: Phase 3 - Conflict Detection (5 failures)

### Current Status
- 14/19 Phase 3 tests passing
- ConflictDetectorAgent partially working
- Conflict resolution logic incomplete

### 2.1: test_detect_conflicts_with_contradiction
**Location:** `tests/test_phase_3_conflict_detection.py:94`
**Failure:** `DetachedInstanceError` (session closed prematurely)

**Same Root Cause as 1.1:** Session management issue

**Fix:** See Part 1.1 above

---

### 2.2: test_resolve_conflict_keep_old
**Location:** `tests/test_phase_3_conflict_detection.py:172`
**Failure:** `InvalidRequestError: Instance '<Conflict at 0x...>' is not persistent within this Session`

**Root Cause:** Trying to update Conflict object in different session

**Implementation Required:**
```python
# In app/agents/conflict_detector.py
def _resolve_conflict(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve a specific conflict.

    Args:
        data: {
            'conflict_id': str (UUID),
            'resolution': str ('keep_old', 'keep_new', 'manual'),
            'manual_value': str (optional, for 'manual' resolution)
        }

    Returns:
        {'success': bool, 'conflict': dict, 'resolved': bool}
    """
    conflict_id = data.get('conflict_id')
    resolution = data.get('resolution')  # 'keep_old', 'keep_new', 'manual'

    db = self.services.get_database_specs()
    try:
        # Re-query conflict in this session
        conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
        if not conflict:
            return {'success': False, 'error': 'Conflict not found', 'error_code': 'CONFLICT_NOT_FOUND'}

        # Update based on resolution strategy
        if resolution == 'keep_old':
            conflict.resolution = 'RESOLVED'
            conflict.resolution_strategy = 'KEPT_OLD'
            conflict.resolved_at = datetime.now(timezone.utc)
        elif resolution == 'keep_new':
            conflict.resolution = 'RESOLVED'
            conflict.resolution_strategy = 'KEPT_NEW'
            conflict.resolved_at = datetime.now(timezone.utc)
        elif resolution == 'manual':
            # Update both specs with manual value
            pass

        db.commit()
        return {
            'success': True,
            'conflict': conflict.to_dict(),
            'resolved': True
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e), 'error_code': 'DATABASE_ERROR'}
```

**Fix Steps:**
1. Implement `_resolve_conflict()` method in ConflictDetectorAgent
2. Handle 'keep_old' resolution strategy
3. Handle 'keep_new' resolution strategy
4. Handle 'manual' resolution strategy
5. Update Conflict model with resolution_strategy field if missing

**Files to Modify:**
- `app/agents/conflict_detector.py` - add/update `_resolve_conflict()` method
- `app/models/conflict.py` - ensure resolution_strategy field exists

---

### 2.3: test_resolve_conflict_ignore
**Location:** `tests/test_phase_3_conflict_detection.py:195`

**Same Issue as 2.2:** Implement resolution strategies

---

### 2.4: test_resolve_conflict_not_found
**Location:** `tests/test_phase_3_conflict_detection.py:220`

**Same Issue as 2.2:** Implement error handling for missing conflict

---

### 2.5: test_context_analyzer_blocks_on_conflict
**Location:** `tests/test_phase_3_conflict_detection.py:471`
**Failure:** `assert True is False` - ContextAnalyzerAgent should block on unresolved conflicts

**Implementation Required:**
```python
# In app/agents/context.py
def _extract_specifications(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add conflict detection before returning specs
    """
    # ... existing implementation ...

    # CHECK FOR UNRESOLVED CONFLICTS
    db = self.services.get_database_specs()
    unresolved_conflicts = db.query(Conflict).filter(
        and_(
            Conflict.project_id == project_id,
            Conflict.resolution != 'RESOLVED'
        )
    ).all()

    if unresolved_conflicts:
        return {
            'success': False,
            'error': 'Cannot extract specifications with unresolved conflicts',
            'error_code': 'CONFLICTS_UNRESOLVED',
            'conflicts': [c.to_dict() for c in unresolved_conflicts],
            'blocked_by_conflicts': True
        }

    # ... proceed with spec extraction ...
```

**Fix Steps:**
1. In ContextAnalyzerAgent._extract_specifications(), check for unresolved conflicts
2. Block extraction if conflicts exist
3. Return error code 'CONFLICTS_UNRESOLVED'

---

## Part 3: Phase 4 - Code Generation (8 failures)

### Current Status
- 10/18 Phase 4 tests passing
- CodeGeneratorAgent exists but methods incomplete

### 3.1: test_maturity_gate_identifies_missing_categories
**Location:** `tests/test_phase_4_code_generation.py:74`

**Implementation Required:**
```python
# In app/agents/code_generator.py
def _analyze_maturity_gate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze if project is ready for code generation based on maturity.

    Expected categories:
    - requirements
    - architecture
    - tech_stack
    - scalability
    - security
    - performance
    - testing
    - monitoring
    - data_retention
    - disaster_recovery

    Needs 7+ of 10 categories to proceed.
    """
    project_id = data.get('project_id')

    db = self.services.get_database_specs()
    try:
        specs = db.query(Specification).filter(
            Specification.project_id == project_id
        ).all()

        # Group by category
        categories = set(s.category for s in specs)
        expected = {
            'requirements', 'architecture', 'tech_stack', 'scalability',
            'security', 'performance', 'testing', 'monitoring',
            'data_retention', 'disaster_recovery'
        }

        missing = expected - categories
        coverage = len(categories) / len(expected)

        return {
            'success': True,
            'categories_present': list(categories),
            'categories_missing': list(missing),
            'coverage_percentage': coverage * 100,
            'ready_for_generation': len(missing) <= 3,  # 7+ required
            'missing_categories': list(missing)
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'error_code': 'ANALYSIS_ERROR'}
```

**Fix Steps:**
1. Implement `_analyze_maturity_gate()` in CodeGeneratorAgent
2. Query specifications by category
3. Return missing categories
4. Calculate coverage percentage
5. Set ready_for_generation based on 7+ of 10 rule

---

### 3.2: test_conflict_gate_allows_resolved_conflicts
**Location:** `tests/test_phase_4_code_generation.py:131`

**Implementation Required:**
```python
# In app/agents/code_generator.py
def _check_conflict_gate(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if project is ready (all conflicts resolved or no conflicts).
    """
    project_id = data.get('project_id')

    db = self.services.get_database_specs()
    try:
        # Check for unresolved conflicts
        unresolved = db.query(Conflict).filter(
            and_(
                Conflict.project_id == project_id,
                Conflict.resolution != 'RESOLVED'
            )
        ).count()

        return {
            'success': True,
            'has_unresolved_conflicts': unresolved > 0,
            'can_proceed': unresolved == 0
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'error_code': 'GATE_ERROR'}
```

**Fix Steps:**
1. Implement `_check_conflict_gate()` in CodeGeneratorAgent
2. Query unresolved conflicts
3. Return gate status

---

### 3.3: test_generate_code_success
**Location:** `tests/test_phase_4_code_generation.py:151`

**Implementation Required:**
```python
# In app/agents/code_generator.py
def _generate_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate code from specifications using Claude API.

    Returns GeneratedProject with files.
    """
    project_id = data.get('project_id')
    language = data.get('language', 'python')  # python, typescript, go, rust

    db_auth = self.services.get_database_auth()
    db_specs = self.services.get_database_specs()

    try:
        # Get project
        project = db_specs.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'success': False, 'error': 'Project not found', 'error_code': 'PROJECT_NOT_FOUND'}

        # Get all specifications
        specs = db_specs.query(Specification).filter(
            Specification.project_id == project_id
        ).all()

        # Build prompt
        prompt = self._build_generation_prompt(specs, language)

        # Call Claude API
        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        generated_code = response.content[0].text

        # Create GeneratedProject record
        gen_project = GeneratedProject(
            project_id=project_id,
            generation_version=1,
            total_files=len(self._parse_files(generated_code)),
            total_lines=self._count_lines(generated_code),
            generation_started_at=datetime.now(timezone.utc),
            generation_status='COMPLETED'
        )
        db_specs.add(gen_project)
        db_specs.commit()

        return {
            'success': True,
            'generated_project_id': str(gen_project.id),
            'code': generated_code,
            'total_files': gen_project.total_files,
            'total_lines': gen_project.total_lines
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'error_code': 'GENERATION_ERROR'}
```

**Fix Steps:**
1. Implement `_generate_code()` method
2. Implement `_build_generation_prompt()` helper
3. Implement `_parse_files()` helper (parse generated code into files)
4. Implement `_count_lines()` helper
5. Call Claude API with specifications
6. Create GeneratedProject record
7. Return code and metadata

---

### 3.4-3.8: Other Phase 4 Tests

Similar implementation pattern - each test specifies:
- **test_generate_code_versioning**: Support multiple generation versions per project
- **test_generate_code_project_not_found**: Return error for missing project
- **test_get_generation_status_not_found**: Handle missing generation
- **test_group_specs_by_category**: Implement spec grouping logic
- **test_build_code_generation_prompt**: Implement prompt building

---

## Part 4: Phase 5 - Quality Control (2 failures)

### Current Status
- 8/10 Phase 5 tests passing
- QualityControllerAgent partially working

### 4.1: test_compare_paths_recommends_thorough
**Location:** `tests/test_phase_5_quality_control.py:95`

**Implementation Required:**
```python
# In app/agents/quality_controller.py
def _compare_paths(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare shallow vs thorough analysis paths.
    Recommend thorough if issues detected.
    """
    project_id = data.get('project_id')
    shallow_results = data.get('shallow_analysis')  # From quick check

    # Analysis checks:
    # - Bias check: question bias score
    # - Coverage check: specification coverage
    # - Conflict check: unresolved conflicts

    has_issues = (
        shallow_results.get('bias_score', 0) < 0.5 or
        shallow_results.get('coverage_score', 0) < 0.7 or
        shallow_results.get('unresolved_conflicts', 0) > 0
    )

    return {
        'success': True,
        'recommend_thorough': has_issues,
        'reason': 'Issues detected in shallow analysis' if has_issues else 'All checks passed'
    }
```

**Fix Steps:**
1. Implement `_compare_paths()` in QualityControllerAgent
2. Compare quality metrics
3. Recommend thorough analysis if issues found

---

### 4.2: test_quality_metrics_stored_in_database
**Location:** `tests/test_phase_5_quality_control.py:118`

**Implementation Required:**
```python
# In app/agents/quality_controller.py
def _store_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store quality metrics in database for tracking.
    """
    project_id = data.get('project_id')
    metrics = data.get('metrics')  # Dict of metric values

    db = self.services.get_database_specs()
    try:
        quality_metric = QualityMetric(
            project_id=project_id,
            bias_score=metrics.get('bias_score'),
            coverage_score=metrics.get('coverage_score'),
            complexity_score=metrics.get('complexity_score'),
            timestamp=datetime.now(timezone.utc)
        )
        db.add(quality_metric)
        db.commit()

        return {'success': True, 'metric_id': str(quality_metric.id)}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
```

**Fix Steps:**
1. Implement `_store_metrics()` in QualityControllerAgent
2. Create QualityMetric record
3. Store all relevant metrics

---

## Part 5: Phase 6 - User Learning (6 failures)

### Current Status
- 4/10 Phase 6 tests passing
- UserLearningAgent methods incomplete

### 5.1-5.6: All Phase 6 Tests Need Method Implementations

**Common Issue:** These tests try to import User from question model:
```python
question = Question(
    # ...
    difficulty="basic",  # This field doesn't exist on Question
    asked_at=datetime.now(timezone.utc)
)
```

**Primary Implementation Needed:**
```python
# In app/agents/learning.py
class UserLearningAgent(BaseAgent):
    def _track_question_effectiveness(self, data):
        """Track how effective a question was for learning"""
        # Implement: Record user's response to question
        # Update question_effectiveness metrics
        pass

    def _learn_behavior_pattern(self, data):
        """Learn patterns in user behavior"""
        # Implement: Analyze user question/answer patterns
        # Store in user_behavior_patterns table
        pass

    def _upload_knowledge_document(self, data):
        """Upload knowledge document for training"""
        # Implement: Store document in knowledge_base_documents table
        pass

    def _recommend_next_question(self, data):
        """Recommend next question based on learning"""
        # Implement: Query patterns, recommend appropriate question
        pass

    def _get_user_profile(self, data):
        """Get user learning profile"""
        # Implement: Query behavior patterns, effectiveness, documents
        pass
```

**Fix Steps:**
1. Implement all 5 methods in UserLearningAgent
2. Create tables if missing (user_behavior_patterns, question_effectiveness, knowledge_base_documents)
3. Handle document upload/storage
4. Track question effectiveness metrics
5. Build recommendation engine based on patterns

---

## Part 6: Phase 8 - Team Collaboration (10 failures)

### Current Status
- 0/10 Phase 8 tests passing
- TeamCollaborationAgent barely implemented

### 6.1-6.10: All Phase 8 Tests Need Implementation

**Implementation Required:**
```python
# In app/agents/team_collaboration.py
class TeamCollaborationAgent(BaseAgent):
    def _create_team(self, data):
        """Create a team"""
        # Create Team record
        # Associate creator as owner
        pass

    def _add_team_member(self, data):
        """Add member to team"""
        # Create TeamMember record
        # Set role and permissions
        pass

    def _remove_team_member(self, data):
        """Remove member from team"""
        # Delete TeamMember record
        # Check ownership rules
        pass

    def _share_project(self, data):
        """Share project with team"""
        # Create project_shares record
        # Set permissions level
        pass

    def _get_team_details(self, data):
        """Get full team info with members"""
        # Query team + members
        # Return details
        pass

    def _get_team_activity(self, data):
        """Get activity log for team"""
        # Query recent actions
        # Return activity timeline
        pass
```

**Fix Steps:**
1. Implement all 6 core methods in TeamCollaborationAgent
2. Handle team creation, membership, sharing
3. Track permissions and access levels
4. Implement activity logging
5. Add validation (only owner can remove members, etc.)

---

## Part 7: Phase 9 - Advanced Features (6 failures + cross-contamination)

### Current Status
- 15/22 Phase 9 tests passing
- MultiLLMManager, ExportAgent incomplete

### 7.1-7.6: API Keys and Multi-LLM Support

**Implementation Required:**
```python
# In app/agents/llm_manager.py
class MultiLLMManager(BaseAgent):
    def _add_api_key(self, data):
        """Store API key for different LLM provider"""
        # Create api_keys record
        # Support: openai, anthropic, mistral, etc.
        pass

    def _list_providers(self, data):
        """List available LLM providers"""
        # Query configured api_keys
        # Return available providers
        pass

    def _get_usage_stats(self, data):
        """Get LLM usage statistics"""
        # Query llm_usage_tracking
        # Return stats by provider
        pass

    def _set_project_llm(self, data):
        """Set which LLM to use for project"""
        # Update project.preferred_llm
        # Pass to agents
        pass
```

### 7.7-7.11: Export Functionality

**Implementation Required:**
```python
# In app/agents/export_agent.py
class ExportAgent(BaseAgent):
    def _export_markdown(self, data):
        """Export project specs as Markdown"""
        # Format specifications as markdown
        # Return markdown content
        pass

    def _export_json(self, data):
        """Export project specs as JSON"""
        # Format specifications as JSON
        # Return JSON content
        pass

    def _export_pdf(self, data):
        """Export project specs as PDF"""
        # Generate PDF from specs
        # Return PDF binary
        pass

    def _export_code(self, data):
        """Export generated code"""
        # Get generated project
        # Return code files
        pass
```

**Fix Steps:**
1. Implement all export formats
2. Handle document generation
3. Support different output formats
4. Return proper content-type headers

---

### 7.12: Cross-Contamination Table Issue

**Issue:** test_specs_has_only_specs_tables still failing
**Status:** Generated tables created, but test may need re-check

**Fix:** Already done - generated_projects and generated_files created

---

## Part 8: End-to-End Integration (3 failures)

### Current Status
- 5/8 E2E tests passing
- 3 failures related to agent orchestrator and Claude API mocking

### 8.1: test_complete_user_workflow
**Failure:** Claude API spec parsing fails in ContextAnalyzerAgent

**Root Cause:** Agent calls actual Claude API, response parsing fails

**Fix Required:**
```python
# In tests/test_end_to_end_integration.py
def test_complete_user_workflow(self, service_container, test_user, auth_session, specs_session):
    # Need to mock Claude API response
    with patch('app.agents.context.AnthropicClient') as mock_claude:
        mock_claude.return_value.messages.create.return_value = ...
        # Then run test
```

---

### 8.2: test_orchestrator_routing
**Failure:** `Unknown agent: project` - agents not registered

**Root Cause:** Orchestrator not registered with agents in test

**Fix Required:**
- Register agents in service_container before test
- OR modify fixture to auto-register agents

---

### 8.3: test_agent_to_agent_communication
**Same issue as 8.2**

---

## Summary Table: Implementation Work Breakdown

| Phase | Tests | Status | Implementation Effort |
|-------|-------|--------|----------------------|
| Phase 1 | 18 | ✅ 100% | Done |
| Phase 2 | 16 | 🟡 94% (15/16) | Fix session management (1 test) |
| Phase 3 | 19 | 🟡 74% (14/19) | Implement conflict resolution (5 tests) |
| Phase 4 | 18 | 🟡 56% (10/18) | Code generation pipeline (8 tests) |
| Phase 5 | 10 | 🟡 80% (8/10) | Quality metrics storage (2 tests) |
| Phase 6 | 10 | 🟡 40% (4/10) | User learning agent (6 tests) |
| Phase 7 | 17 | 🟢 100% | Done |
| Phase 8 | 10 | 🔴 0% (0/10) | Team collaboration agent (10 tests) |
| Phase 9 | 22 | 🟡 68% (15/22) | Export & multi-LLM (7 tests) |
| E2E | 8 | 🟡 63% (5/8) | Mocking & orchestration (3 tests) |
| **TOTAL** | **287** | **85%** | **59 tests** |

---

## Implementation Roadmap (Priority Order)

### Week 1: High-Impact Fixes (35 tests)
1. **Session Management** - Fix database session lifecycle
   - Impact: 6+ tests immediately (Phase 2-4)
   - Effort: 2-3 hours
   - Files: All agent _method implementations

2. **Conflict Resolution** - Implement conflict resolution strategies
   - Impact: 5 tests (Phase 3)
   - Effort: 3-4 hours
   - Files: conflict_detector.py

3. **Code Generation** - Implement code generation pipeline
   - Impact: 8 tests (Phase 4)
   - Effort: 4-5 hours
   - Files: code_generator.py

### Week 2: Large Feature Implementation (24 tests)
4. **Team Collaboration** - Implement team management
   - Impact: 10 tests (Phase 8)
   - Effort: 5-6 hours
   - Files: team_collaboration.py, new Team/TeamMember models

5. **User Learning** - Implement learning patterns
   - Impact: 6 tests (Phase 6)
   - Effort: 4-5 hours
   - Files: learning.py

6. **Export/Multi-LLM** - Implement export and LLM management
   - Impact: 7 tests (Phase 9)
   - Effort: 4-5 hours
   - Files: export_agent.py, llm_manager.py

### Week 3: Integration & Polish (3 tests)
7. **E2E Integration** - Mock Claude API, register orchestrator
   - Impact: 3 tests
   - Effort: 2-3 hours
   - Files: test fixtures, service_container

---

## Critical Implementation Guidelines

### 1. Session Management
- **NEVER** call `db.close()` in agent methods
- Let dependency injection manage sessions
- Use `db = self.services.get_database_*()` only within single request

### 2. Error Handling
- Always return `{'success': bool, 'error': str, 'error_code': str}`
- Use consistent error codes (PROJECT_NOT_FOUND, VALIDATION_ERROR, etc.)
- Never raise exceptions outside error handling

### 3. Database Operations
- Always use `db.flush()` before `user.id` is accessed
- Always use `db.commit()` before closing
- Always use `db.rollback()` in exception handlers

### 4. API Integration
- Mock Claude API in tests (don't call real API)
- Use prompt templates, not string concatenation
- Store API responses, don't re-call on retry

### 5. Code Generation
- Parse generated code into structured format
- Store file structure, not raw text
- Support multiple languages: Python, TypeScript, Go, Rust

---

## Files Requiring Implementation

### Core Agent Methods
- `app/agents/conflict_detector.py` - _resolve_conflict()
- `app/agents/code_generator.py` - _generate_code(), _analyze_maturity_gate(), _check_conflict_gate()
- `app/agents/quality_controller.py` - _compare_paths(), _store_metrics()
- `app/agents/learning.py` - All 5 methods
- `app/agents/team_collaboration.py` - All 6 methods
- `app/agents/llm_manager.py` - All 4 methods
- `app/agents/export_agent.py` - All 4 methods

### Model Updates
- `app/models/conflict.py` - Add resolution_strategy field
- `app/models/generated_project.py` - Ensure complete
- `app/models/api_key.py` - Implement
- `app/models/quality_metric.py` - Ensure fields match tests

### Test Fixtures
- `tests/conftest.py` - Mock Claude client, register agents

---

## Testing Strategy

1. **Implement by phase** (Phase 2 → Phase 9)
2. **Run tests after each phase**: `pytest tests/test_phase_X_*.py -v`
3. **Check for regressions**: `pytest --tb=short -q` (full suite)
4. **Commit after each phase**: `git commit -m "Implement Phase X"`

---

## Success Criteria

✅ All 287 tests passing
✅ No test modifications (only implementation)
✅ All actual functionality working
✅ Database properly structured
✅ Agents fully integrated
✅ APIs functional end-to-end


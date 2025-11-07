# CRITICAL-001 Fix Guide: Add Rollback Handling to All Agents

**Issue:** Agents perform database commits without try/except/rollback handling
**Severity:** CRITICAL (P0)
**Status:** 🔴 NOT YET FIXED (template provided)
**Estimated Time:** 1-2 hours

---

## Problem Summary

All agents that perform database operations call `db.commit()` without error handling. If a commit fails, the database session enters an inconsistent state and subsequent operations fail.

**Current Pattern (UNSAFE):**
```python
def _create_project(self, data):
    db = self.services.get_database_specs()
    project = Project(...)
    db.add(project)
    db.commit()  # ❌ NO error handling
    db.refresh(project)
    return {'success': True, 'project': project.to_dict()}
```

---

## Required Fix Pattern

**Pattern 1: For Simple Operations**
```python
def _create_project(self, data):
    db = self.services.get_database_specs()
    try:
        project = Project(...)
        db.add(project)
        db.commit()
        db.refresh(project)

        return {'success': True, 'project': project.to_dict()}

    except Exception as e:
        self.logger.error(f"Error creating project: {e}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'error': f'Failed to create project: {str(e)}',
            'error_code': 'DATABASE_ERROR'
        }
    finally:
        db.close()  # Important: Close session after use
```

**Pattern 2: For Complex Operations with Multiple Commits**
```python
def _complex_operation(self, data):
    db_auth = self.services.get_database_auth()
    db_specs = self.services.get_database_specs()

    try:
        # Operation 1
        user = db_auth.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError("User not found")

        # Operation 2
        project = Project(...)
        db_specs.add(project)
        db_specs.commit()

        # Operation 3
        spec = Specification(...)
        db_specs.add(spec)
        db_specs.commit()

        return {'success': True}

    except ValueError as e:
        # Validation errors - don't rollback (no changes made)
        self.logger.warning(f"Validation error: {e}")
        return {'success': False, 'error': str(e), 'error_code': 'VALIDATION_ERROR'}

    except Exception as e:
        # Database errors - rollback both sessions
        self.logger.error(f"Database error: {e}", exc_info=True)
        db_auth.rollback()
        db_specs.rollback()
        return {'success': False, 'error': str(e), 'error_code': 'DATABASE_ERROR'}

    finally:
        # Always close sessions
        db_auth.close()
        db_specs.close()
```

---

## Files That Need Fixing

### 1. backend/app/agents/project.py

**Methods to fix:**
- `_create_project()` - line ~84
- `_update_project()` - line ~170
- `_delete_project()` - line ~210
- `_update_maturity()` - line ~250

**Example for _create_project:**
```python
def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

    db_auth = self.services.get_database_auth()
    db_specs = self.services.get_database_specs()

    try:
        # Check user exists (in socrates_auth database)
        user = db_auth.query(User).filter(User.id == user_id).first()
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
            current_phase='discovery',
            maturity_score=0,
            status='active'
        )

        db_specs.add(project)
        db_specs.commit()
        db_specs.refresh(project)

        self.logger.info(f"Created project: {project.id} for user: {user_id}")

        return {
            'success': True,
            'project_id': str(project.id),
            'project': project.to_dict()
        }

    except Exception as e:
        self.logger.error(f"Error creating project: {e}", exc_info=True)
        db_specs.rollback()
        return {
            'success': False,
            'error': f'Failed to create project: {str(e)}',
            'error_code': 'DATABASE_ERROR'
        }

    finally:
        db_auth.close()
        db_specs.close()
```

---

### 2. backend/app/agents/socratic.py

**Methods to fix:**
- `_generate_question()` - saves Question to database
- Any method that calls `db.commit()`

**Pattern:**
```python
def _generate_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
    db = self.services.get_database_specs()

    try:
        # ... question generation logic ...

        question = Question(...)
        db.add(question)
        db.commit()
        db.refresh(question)

        return {'success': True, 'question': question.to_dict()}

    except Exception as e:
        self.logger.error(f"Error generating question: {e}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'error': f'Failed to generate question: {str(e)}',
            'error_code': 'DATABASE_ERROR'
        }

    finally:
        db.close()
```

---

### 3. backend/app/agents/context.py

**Methods to fix:**
- `_extract_specifications()` - creates multiple Specification records
- Updates project maturity score

**Pattern:**
```python
def _extract_specifications(self, data: Dict[str, Any]) -> Dict[str, Any]:
    db = self.services.get_database_specs()

    try:
        # Load entities
        session = db.query(Session).filter_by(id=session_id).first()
        question = db.query(Question).filter_by(id=question_id).first()

        # Create conversation history
        conv = ConversationHistory(...)
        db.add(conv)

        # Extract specifications (potentially multiple)
        specs = self._call_claude_to_extract(answer, question.category)

        for spec_data in specs:
            spec = Specification(...)
            db.add(spec)

        # Update project maturity
        project.maturity_score = self._calculate_maturity(project_id, db)

        # Commit all changes at once
        db.commit()

        return {'success': True, 'specs_extracted': len(specs)}

    except Exception as e:
        self.logger.error(f"Error extracting specifications: {e}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'error': f'Failed to extract specifications: {str(e)}',
            'error_code': 'DATABASE_ERROR'
        }

    finally:
        db.close()
```

---

### 4. backend/app/agents/conflict_detector.py

**Methods to fix:**
- `_detect_conflicts()` - creates Conflict records
- `_resolve_conflict()` - updates Conflict status

**Pattern:**
Same as above - wrap db operations in try/except/finally

---

### 5. backend/app/agents/code_generator.py

**Methods to fix:**
- `_generate_code()` - creates GeneratedProject and GeneratedFile records

**Pattern:**
Same as above - wrap db operations in try/except/finally

---

### 6. backend/app/agents/team_collaboration.py

**Methods to fix:**
- `_create_team()` - creates Team
- `_add_team_member()` - creates TeamMember
- `_remove_team_member()` - deletes TeamMember
- `_create_team_project()` - creates Project
- `_share_project()` - creates ProjectShare

**Pattern:**
Same as above - wrap db operations in try/except/finally

---

### 7. backend/app/agents/quality_controller.py

**Methods to fix:**
- `_calculate_metrics()` - creates/updates QualityMetric records

**Pattern:**
Same as above - wrap db operations in try/except/finally

---

## Verification Steps

After applying fixes to all agents:

### 1. Code Review
```bash
# Check all agents have try/except
cd backend/app/agents
grep -n "db.commit()" *.py

# For each commit, verify it has:
# - try block before commit
# - except block after commit with rollback
# - finally block with db.close()
```

### 2. Test Each Agent Method
```python
# Example test
def test_project_creation_rollback():
    """Test that failed project creation rolls back cleanly"""
    # Mock db.commit() to raise exception
    with patch.object(Session, 'commit', side_effect=Exception("Database error")):
        result = agent._create_project({'user_id': 'test', 'name': 'Test'})

        assert result['success'] == False
        assert result['error_code'] == 'DATABASE_ERROR'
        # Verify rollback was called
        # Verify no partial data in database
```

### 3. Integration Test
```python
def test_concurrent_operations():
    """Test that concurrent operations don't share sessions"""
    # Create 10 projects simultaneously
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(create_project, f"Project {i}")
            for i in range(10)
        ]

        results = [f.result() for f in futures]

    # All should succeed
    assert all(r['success'] for r in results)
    # All should have unique IDs
    ids = [r['project_id'] for r in results]
    assert len(ids) == len(set(ids))
```

---

## Checklist

- [ ] Fix project.py (4 methods)
- [ ] Fix socratic.py
- [ ] Fix context.py
- [ ] Fix conflict_detector.py
- [ ] Fix code_generator.py
- [ ] Fix team_collaboration.py (5 methods)
- [ ] Fix quality_controller.py
- [ ] Verify all db.commit() calls have error handling
- [ ] Verify all sessions are closed in finally blocks
- [ ] Run integration tests
- [ ] Load test with concurrent requests

---

## Additional Improvements (Optional)

### Create Base Agent Helper Method

Add to `backend/app/agents/base.py`:

```python
from contextlib import contextmanager
from sqlalchemy.orm import Session

class BaseAgent:
    # ... existing code ...

    @contextmanager
    def db_transaction(self, db: Session):
        """
        Context manager for safe database transactions.

        Usage:
            with self.db_transaction(db) as session:
                project = Project(...)
                session.add(project)
                # Commit happens automatically if no exception
                # Rollback happens automatically on exception
        """
        try:
            yield db
            db.commit()
        except Exception as e:
            self.logger.error(f"Database transaction failed: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()
```

Then agents can use:
```python
def _create_project(self, data):
    db = self.services.get_database_specs()

    with self.db_transaction(db):
        project = Project(...)
        db.add(project)
        # Auto-commit, auto-rollback, auto-close

    return {'success': True, 'project': project.to_dict()}
```

---

## Estimated Time

- Review and understand pattern: 15 minutes
- Fix project.py: 20 minutes
- Fix socratic.py: 15 minutes
- Fix context.py: 20 minutes
- Fix conflict_detector.py: 15 minutes
- Fix code_generator.py: 15 minutes
- Fix team_collaboration.py: 25 minutes
- Fix quality_controller.py: 10 minutes
- Testing and verification: 30 minutes

**Total: ~2.5 hours**

If implementing helper method: add 1 hour

---

## Priority

**CRITICAL - Must be fixed before deployment**

Without these fixes:
- Database connection leaks will occur
- Application will hang after ~10-20 requests
- Partial data commits will corrupt database
- Concurrent requests will cause race conditions

**Status:** 🔴 Awaiting implementation

---

**Last Updated:** 2025-11-07
**Created By:** System Audit
**Assigned To:** Development Team

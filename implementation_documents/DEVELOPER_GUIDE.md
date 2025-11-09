# Socrates2 Developer Quick-Start Guide

**Last Updated:** November 9, 2025
**Test Status:** 245/287 passing (85.4%)

---

## Quick Navigation

- **Full Implementation Plan:** See `IMPLEMENTATION_PLAN.md` for detailed work breakdown
- **Test Results:** Run `pytest --tb=short -q` for current status
- **Architecture:** See `CLAUDE.md` for system overview

---

## How to Add an Agent Method

### 1. Understand the Test
Every method has a corresponding test that specifies:
- What input it takes
- What output it should return
- What error codes to use

**Example:** Find the test first
```bash
# Look for the test that calls your method
grep -r "your_method_name" tests/
```

### 2. Read the Test Specification
```python
# Example from tests/test_phase_3_conflict_detection.py
def test_resolve_conflict_keep_old(service_container, complete_user_and_project):
    """Test resolving a conflict by keeping old value"""
    agent = ConflictDetectorAgent("conflict", "ConflictDetectorAgent", service_container)

    # Create a conflict
    specs_db = service_container.get_database_specs()
    conflict = Conflict(
        project_id=complete_user_and_project['project'].id,
        old_value="PostgreSQL",
        new_value="MongoDB",
        resolution="UNRESOLVED"
    )
    specs_db.add(conflict)
    specs_db.commit()

    # Test the method
    result = agent.process_request('resolve_conflict', {
        'conflict_id': str(conflict.id),
        'resolution': 'keep_old'
    })

    # Assert expected behavior
    assert result['success'] is True
    assert result['resolved'] is True
    assert result['conflict']['resolution'] == 'RESOLVED'
```

### 3. Implement the Method in the Agent

**File Location:** `app/agents/{agent_name}.py`

**Template:**
```python
def _resolve_conflict(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve a specific conflict.

    Args:
        data: {
            'conflict_id': str (UUID),
            'resolution': str ('keep_old', 'keep_new', 'manual')
        }

    Returns:
        {'success': bool, 'conflict': dict, 'resolved': bool}
    """
    # STEP 1: Validate input
    conflict_id = data.get('conflict_id')
    resolution = data.get('resolution')

    if not conflict_id or not resolution:
        return {
            'success': False,
            'error': 'conflict_id and resolution are required',
            'error_code': 'VALIDATION_ERROR'
        }

    # STEP 2: Get database
    db = self.services.get_database_specs()

    try:
        # STEP 3: Query entity
        conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
        if not conflict:
            return {
                'success': False,
                'error': f'Conflict not found: {conflict_id}',
                'error_code': 'CONFLICT_NOT_FOUND'
            }

        # STEP 4: Business logic
        if resolution == 'keep_old':
            conflict.resolution = 'RESOLVED'
            conflict.resolution_strategy = 'KEPT_OLD'
            conflict.resolved_at = datetime.now(timezone.utc)

        # STEP 5: Persist changes
        db.commit()

        # STEP 6: Return success
        return {
            'success': True,
            'conflict': conflict.to_dict(),
            'resolved': True
        }

    except Exception as e:
        # STEP 7: Handle errors
        self.logger.error(f"Error resolving conflict: {e}", exc_info=True)
        db.rollback()
        return {
            'success': False,
            'error': f'Failed to resolve conflict: {str(e)}',
            'error_code': 'DATABASE_ERROR'
        }

    # NEVER close the session!
    # The caller (API endpoint or test) owns the session lifecycle
```

### 4. Register Method in Agent

The method must be:
1. Named as `_method_name()` (with underscore prefix)
2. Called via `process_request('method_name', data)` (without underscore)

**In BaseAgent.process_request():**
```python
def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Convert action name to method name (add underscore)
    method_name = f'_{action}'

    if hasattr(self, method_name):
        method = getattr(self, method_name)
        return method(data)

    # Error handling if method doesn't exist
    return {'success': False, 'error': 'Action not found'}
```

### 5. Run the Test

```bash
# Run just your test
pytest tests/test_phase_3_conflict_detection.py::test_resolve_conflict_keep_old -v

# Run all tests for your phase
pytest tests/test_phase_3_*.py -v

# Check for regressions
pytest --tb=short -q
```

---

## Database Session Management

### ✅ DO THIS
```python
def _my_method(self, data: Dict[str, Any]) -> Dict[str, Any]:
    db = self.services.get_database_specs()

    try:
        # Your code here
        entity = db.query(MyModel).filter(...).first()
        entity.field = new_value
        db.commit()

        return {'success': True, ...}

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}

    # ✅ DON'T CLOSE THE SESSION
    # Let the test/API endpoint manage its lifecycle
```

### ❌ DON'T DO THIS
```python
def _my_method(self, data: Dict[str, Any]) -> Dict[str, Any]:
    db = self.services.get_database_specs()

    try:
        # ...
        return {'success': True, ...}
    finally:
        db.close()  # ❌ WRONG! This breaks tests
```

### Why?
- Tests use **function-scoped sessions** that are re-used across operations
- If agent closes the session, subsequent operations fail
- The test/API endpoint is responsible for closing the session

---

## Standard Error Codes

Use these error codes consistently:

| Error Code | Meaning | HTTP Status |
|------------|---------|-------------|
| VALIDATION_ERROR | Missing required field | 400 |
| NOT_FOUND | Entity doesn't exist (PROJECT_NOT_FOUND, etc.) | 404 |
| PERMISSION_ERROR | User lacks permission | 403 |
| DATABASE_ERROR | Database operation failed | 500 |
| CONFLICT_UNRESOLVED | Conflicts block operation | 400 |
| ANALYSIS_ERROR | Analysis/computation failed | 500 |
| GENERATION_ERROR | Code/content generation failed | 500 |

---

## Testing Checklist

Before committing, verify:

```bash
# ✅ Run failing test
pytest tests/test_phase_X_*.py::test_your_test_name -v

# ✅ Run entire phase
pytest tests/test_phase_X_*.py -v

# ✅ Check for regressions (full suite)
pytest --tb=short -q

# ✅ Verify count increased
# Should see: "N passed" where N > previous

# ✅ Commit with clear message
git commit -m "Implement Phase X: method_name feature"
```

---

## Agent Structure

Each agent follows this pattern:

```python
class MyAgent(BaseAgent):
    """Brief description"""

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        super().__init__(agent_id, name, services)
        self.logger = services.get_logger(f"agent.{agent_id}")

    def get_capabilities(self) -> List[str]:
        """List all action/method names (without underscore)"""
        return [
            'method_one',
            'method_two',
            'method_three'
        ]

    def _method_one(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement method_one"""
        # Standard pattern (see previous sections)
        pass

    def _method_two(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement method_two"""
        pass
```

---

## Database Access Patterns

### Query a Single Entity
```python
entity = db.query(Model).filter(Model.id == entity_id).first()
if not entity:
    return {'success': False, 'error': 'Not found', 'error_code': 'NOT_FOUND'}
```

### Query Multiple Entities
```python
entities = db.query(Model).filter(Model.category == category).all()
return {
    'success': True,
    'entities': [e.to_dict() for e in entities],
    'count': len(entities)
}
```

### Create New Entity
```python
new_entity = Model(
    field1=data['field1'],
    field2=data['field2']
)
db.add(new_entity)
db.flush()  # Get ID before commit
entity_id = str(new_entity.id)
db.commit()  # Persist
```

### Update Existing Entity
```python
entity = db.query(Model).filter(Model.id == entity_id).first()
if not entity:
    return {'success': False, 'error': 'Not found', 'error_code': 'NOT_FOUND'}

entity.field = new_value
entity.updated_at = datetime.now(timezone.utc)
db.commit()
```

### Delete Entity
```python
entity = db.query(Model).filter(Model.id == entity_id).first()
if not entity:
    return {'success': False, 'error': 'Not found', 'error_code': 'NOT_FOUND'}

db.delete(entity)
db.commit()
```

---

## Testing with Fixtures

Available fixtures in `tests/conftest.py`:

```python
def my_test(service_container, test_user, test_project, auth_session, specs_session):
    """
    service_container: ServiceContainer with test databases
    test_user: Pre-created user in auth DB
    test_project: Pre-created project in specs DB
    auth_session: SQLAlchemy session for auth DB
    specs_session: SQLAlchemy session for specs DB
    """
    # Example: Create additional test data
    from app.models.conflict import Conflict

    conflict = Conflict(
        project_id=test_project.id,
        old_value="value1",
        new_value="value2"
    )
    specs_session.add(conflict)
    specs_session.commit()

    # Now call your agent
    agent = MyAgent("agent_id", "Agent Name", service_container)
    result = agent.process_request('my_method', {
        'conflict_id': str(conflict.id)
    })

    assert result['success'] is True
```

---

## Common Issues & Solutions

### Issue 1: "DetachedInstanceError: Instance is not bound to a Session"

**Cause:** You're accessing a model attribute after the session closed

**Solution:**
```python
# ❌ WRONG
entity = db.query(Model).filter(...).first()
db.close()  # Session closed!
id = str(entity.id)  # ❌ Error: entity detached

# ✅ RIGHT
entity = db.query(Model).filter(...).first()
id = str(entity.id)  # Get ID while session open
db.close()  # Don't do this anyway!
```

### Issue 2: "No changes detected in mapped instance"

**Cause:** SQLAlchemy doesn't see your changes

**Solution:**
```python
# ✅ Make sure to assign to attributes
entity.field = new_value  # Direct assignment
db.commit()  # Commit changes

# Mark entity as dirty if needed
db.add(entity)  # Re-add if modified elsewhere
```

### Issue 3: "Instance is not persistent within this Session"

**Cause:** Trying to use object from different session

**Solution:**
```python
# ❌ WRONG
old_entity = old_session.query(Model).filter(...).first()
new_session.add(old_entity)  # ❌ Wrong session!

# ✅ RIGHT
entity_id = old_entity.id
new_entity = new_session.query(Model).filter(Model.id == entity_id).first()
new_session.add(new_entity)  # ✅ Correct session
```

---

## Code Style Guidelines

Follow these patterns for consistency:

### Logging
```python
self.logger.info(f"Starting {action}")
self.logger.debug(f"Processing {entity.id}")
self.logger.error(f"Error: {e}", exc_info=True)
```

### Type Hints
```python
def _method_name(self, data: Dict[str, Any]) -> Dict[str, Any]:
    result: List[str] = []
    count: int = len(items)
    return {'success': True}
```

### Imports
Group imports in this order:
1. Standard library (datetime, json, etc.)
2. Third-party (sqlalchemy, anthropic, etc.)
3. Local modules (from app.models, from ..core, etc.)

---

## Quick Reference: Agent Files

```
app/agents/
├── base.py                    # BaseAgent class (read-only)
├── orchestrator.py            # AgentOrchestrator (read-only)
├── project.py                 # ProjectManagerAgent (DONE)
├── socratic.py                # SocraticCounselorAgent (mostly done)
├── context.py                 # ContextAnalyzerAgent (mostly done)
├── conflict_detector.py       # ConflictDetectorAgent (NEEDS: resolve_conflict)
├── code_generator.py          # CodeGeneratorAgent (NEEDS: generate_code, maturity_gate)
├── quality_controller.py      # QualityControllerAgent (NEEDS: compare_paths, store_metrics)
├── learning.py                # UserLearningAgent (NEEDS: all methods)
├── team_collaboration.py      # TeamCollaborationAgent (NEEDS: all methods)
├── llm_manager.py             # MultiLLMManager (NEEDS: all methods)
├── export_agent.py            # ExportAgent (NEEDS: all methods)
└── direct_chat.py             # DirectChatAgent (DONE)
```

---

## Performance Tips

1. **Batch queries when possible**
   ```python
   # ✅ Good
   entities = db.query(Model).filter(Model.type == type).all()

   # ❌ Slow
   for item in items:
       entity = db.query(Model).filter(Model.id == item).first()
   ```

2. **Use indexes**
   ```python
   # In model definition
   __table_args__ = (
       Index('idx_project_id', 'project_id'),
       Index('idx_status', 'status'),
   )
   ```

3. **Limit data in responses**
   ```python
   # ✅ Only return needed fields
   return {'success': True, 'entities': [e.to_dict() for e in entities]}

   # ❌ Don't return raw objects
   return {'success': True, 'entities': entities}
   ```

---

## Help & Resources

- **Architecture Questions:** See `CLAUDE.md`
- **Implementation Details:** See `IMPLEMENTATION_PLAN.md`
- **Database Schema:** Check migration files in `alembic/versions/`
- **Model Definitions:** See `app/models/`
- **Test Examples:** See `tests/test_phase_*_*.py`

---

## Next Steps

1. Read `IMPLEMENTATION_PLAN.md` for your assigned phase
2. Find the failing tests: `pytest tests/test_phase_X_*.py -v`
3. Read each test specification
4. Implement the required method following the pattern above
5. Run tests to verify
6. Commit with clear message
7. Move to next test

**Happy coding! 🚀**


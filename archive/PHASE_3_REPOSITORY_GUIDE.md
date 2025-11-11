# Phase 3: Repository/Data Access Layer Guide

**Version:** 1.0
**Date:** November 11, 2025
**Status:** Implementation Complete

---

## Quick Start

### Basic Usage

```python
from app.core.database import get_db_auth, get_db_specs
from app.repositories import RepositoryService

# Get sessions (FastAPI dependency injection)
auth_session = next(get_db_auth())
specs_session = next(get_db_specs())

# Create service
service = RepositoryService(auth_session, specs_session)

# Create user
user = service.users.create_user(
    email='test@example.com',
    username='testuser',
    hashed_password='hashed...',
    name='Test',
    surname='User'
)

# Query user
user = service.users.get_by_email('test@example.com')

# Create project
project = service.projects.create_project(
    user_id=user.id,
    name='My Project',
    description='Test project'
)

# Commit all changes
service.commit_all()

# Close sessions
service.close()
```

### With Context Manager

```python
with RepositoryService(auth_session, specs_session) as service:
    user = service.users.create_user(...)
    project = service.projects.create_project(...)
    # Auto-commits on success, rolls back on error
```

---

## Repository Architecture

### Base Repository

All repositories inherit from `BaseRepository[T]` which provides:

**CRUD Operations:**
```python
# Create
instance = repo.create(**kwargs)
instances = repo.bulk_create([{...}, {...}])

# Read
instance = repo.get_by_id(id)
instance = repo.get_by_field('email', 'test@example.com')
instances = repo.list(skip=0, limit=100)
instances = repo.list_by_field('status', 'active')

# Update
instance = repo.update(id, field='value')
instance, created = repo.get_or_create(defaults={...}, **filter)

# Delete
success = repo.delete(id)

# Query
exists = repo.exists(id)
count = repo.count()
count = repo.count_by_field('status', 'active')
```

**Ordering & Pagination:**
```python
instances = repo.list_ordered(
    order_by='created_at',
    ascending=False,
    skip=0,
    limit=100
)
```

**Transaction Management:**
```python
repo.commit()  # Persist changes
repo.rollback()  # Discard changes
repo.refresh(instance)  # Reload from DB
```

---

## AUTH Database Repositories

### UserRepository

```python
# Basic operations
user = service.users.create_user(
    email='test@example.com',
    username='testuser',
    hashed_password='bcrypt_hash',
    name='Test',
    surname='User'
)

# Query by field
user = service.users.get_by_email('test@example.com')
user = service.users.get_by_username('testuser')

# List operations
active_users = service.users.get_active_users(limit=50)
verified_users = service.users.get_verified_users(limit=50)

# Check existence
exists = service.users.user_exists_by_email('test@example.com')
exists = service.users.user_exists_by_username('testuser')

# Update operations
user = service.users.verify_user(user_id)
user = service.users.deactivate_user(user_id)
user = service.users.activate_user(user_id)
user = service.users.update_password(user_id, new_hashed_password)
user = service.users.set_role(user_id, 'admin')
```

### RefreshTokenRepository

```python
# Create token
token = service.refresh_tokens.create(
    user_id=user_id,
    token='jwt_token_string',
    expires_at=datetime.utcnow() + timedelta(days=7)
)

# Query token
token = service.refresh_tokens.get_by_token('jwt_token_string')

# Get user tokens
all_tokens = service.refresh_tokens.get_user_tokens(user_id)
valid_tokens = service.refresh_tokens.get_valid_tokens(user_id)

# Revoke operations
success = service.refresh_tokens.revoke_token(token_id)
revoked_count = service.refresh_tokens.revoke_user_tokens(user_id)

# Cleanup
deleted_count = service.refresh_tokens.cleanup_expired_tokens()
```

### AdminRoleRepository

```python
# Create role
role = service.admin_roles.create(
    name='super_admin',
    description='Full system access',
    permissions=['users:*', 'admin:*'],
    is_system_role=True
)

# Query roles
role = service.admin_roles.get_by_name('super_admin')
system_roles = service.admin_roles.get_system_roles()
custom_roles = service.admin_roles.get_custom_roles()

# Check existence
exists = service.admin_roles.role_exists('super_admin')
```

### AdminUserRepository

```python
# Assign role
admin_user = service.admin_users.assign_role(
    user_id=user_id,
    role_id=role_id,
    granted_by_id=admin_id,
    reason='Promotion to admin'
)

# Query admin assignments
roles = service.admin_users.get_user_roles(user_id)
admin_users = service.admin_users.get_active_admin_users()

# Check admin status
is_admin = service.admin_users.is_admin(user_id)

# Revoke operations
admin_user = service.admin_users.revoke_role(admin_user_id)
revoked_count = service.admin_users.revoke_user_all_roles(user_id)
```

---

## SPECS Database Repositories

### ProjectRepository

```python
# Create project
project = service.projects.create_project(
    user_id=user_id,
    name='Project Name',
    description='Project description'
)

# Query projects
projects = service.projects.get_user_projects(user_id, limit=50)
projects = service.projects.get_user_active_projects(user_id)
projects = service.projects.get_active_projects(limit=100)
projects = service.projects.get_projects_by_phase('discovery')
recent = service.projects.get_recent_projects(limit=10)
recent_user = service.projects.get_user_recent_projects(user_id, limit=10)

# Update operations
project = service.projects.update_project_phase(project_id, 'specification')
project = service.projects.update_project_status(project_id, 'active')
project = service.projects.update_maturity_level(project_id, 75)
project = service.projects.archive_project(project_id)
project = service.projects.complete_project(project_id)

# Count operations
count = service.projects.count_user_projects(user_id)
active_count = service.projects.count_active_projects()
```

### SessionRepository

```python
# Create session
session = service.sessions.create_session(
    project_id=project_id,
    user_id=user_id,
    title='Setup Session'
)

# Query sessions
sessions = service.sessions.get_project_sessions(project_id, limit=50)
sessions = service.sessions.get_user_sessions(user_id)
active = service.sessions.get_active_sessions(project_id)
recent = service.sessions.get_recent_sessions(project_id, limit=10)

# Message tracking
session = service.sessions.increment_message_count(session_id)

# Session status
session = service.sessions.close_session(session_id)
session = service.sessions.archive_session(session_id)

# Count
count = service.sessions.count_project_sessions(project_id)
```

### ConversationHistoryRepository

```python
# Add message
message = service.conversation_history.add_message(
    session_id=session_id,
    role='user',  # 'user', 'assistant', 'system'
    content='User question or message',
    message_type='question'
)

# Get messages
messages = service.conversation_history.get_session_messages(session_id, limit=100)
user_msgs = service.conversation_history.get_user_messages(session_id)
assistant_msgs = service.conversation_history.get_assistant_messages(session_id)

# Count
count = service.conversation_history.count_session_messages(session_id)
```

### QuestionRepository

```python
# Create question
question = service.questions.create_question(
    project_id=project_id,
    text='What is the main purpose?',
    category='functional',
    priority='high'
)

# Query questions
questions = service.questions.get_project_questions(project_id)
questions = service.questions.get_session_questions(session_id)
pending = service.questions.get_pending_questions(project_id)
answered = service.questions.get_answered_questions(project_id)
high_priority = service.questions.get_high_priority_questions(project_id)

# Update question
question = service.questions.answer_question(question_id, 'The answer is...')
question = service.questions.skip_question(question_id)
question = service.questions.resolve_question(question_id)
question = service.questions.update_question_priority(question_id, 'critical')

# Count
pending_count = service.questions.count_pending_questions(project_id)
answered_count = service.questions.count_answered_questions(project_id)
```

### SpecificationRepository

```python
# Create specification
spec = service.specifications.create_specification(
    project_id=project_id,
    key='database_type',
    value='PostgreSQL',
    spec_type='functional'
)

# Query specifications
specs = service.specifications.get_project_specifications(project_id)
spec = service.specifications.get_specification_by_key(project_id, 'database_type')
approved = service.specifications.get_approved_specifications(project_id)
drafts = service.specifications.get_draft_specifications(project_id)

# Update specification
spec = service.specifications.update_specification_value(spec_id, 'MySQL')
spec = service.specifications.approve_specification(spec_id)
spec = service.specifications.implement_specification(spec_id)
spec = service.specifications.deprecate_specification(spec_id)

# Versioning
spec_v2 = service.specifications.create_specification_version(
    project_id=project_id,
    key='database_type',
    value='MongoDB'
)
history = service.specifications.get_specification_history(project_id, 'database_type')

# Count
count = service.specifications.count_project_specifications(project_id)
approved_count = service.specifications.count_approved_specifications(project_id)
```

### TeamRepository

```python
# Create team
team = service.teams.create_team(
    owner_id=user_id,
    name='My Team',
    description='Team description'
)

# Query teams
teams = service.teams.get_user_teams(user_id)
teams = service.teams.get_active_teams()
team = service.teams.get_team_by_name('My Team')
recent = service.teams.get_recent_teams(limit=10)

# Update team
team = service.teams.update_team_name(team_id, 'New Name')
team = service.teams.update_team_description(team_id, 'New description')

# Member count tracking
team = service.teams.increment_member_count(team_id)
team = service.teams.decrement_member_count(team_id)

# Project count tracking
team = service.teams.increment_project_count(team_id)

# Archive
team = service.teams.archive_team(team_id)

# Count
active_count = service.teams.count_active_teams()
```

### TeamMemberRepository

```python
# Add member
member = service.team_members.add_member(
    team_id=team_id,
    user_id=new_user_id,
    role='member',
    permission_level='write',
    invited_by_id=inviter_id
)

# Query members
members = service.team_members.get_team_members(team_id)
active = service.team_members.get_active_members(team_id)
user_teams = service.team_members.get_user_teams_as_member(user_id)

# Check membership
is_member = service.team_members.is_team_member(team_id, user_id)
role = service.team_members.get_member_role(team_id, user_id)

# Update member
member = service.team_members.update_member_role(member_id, 'admin')
member = service.team_members.update_member_permission(member_id, 'admin')

# Remove member
member = service.team_members.remove_member(member_id)

# Count
count = service.team_members.count_team_members(team_id)
```

---

## Common Patterns

### Create and Verify

```python
# Create and get by field
user = service.users.create_user(
    email='new@example.com',
    username='newuser',
    hashed_password='hash',
    name='New',
    surname='User'
)
service.commit_all()

# Verify it was created
user = service.users.get_by_email('new@example.com')
assert user is not None
```

### Bulk Operations

```python
# Bulk create
users_data = [
    {'email': 'user1@example.com', 'username': 'user1', ...},
    {'email': 'user2@example.com', 'username': 'user2', ...},
]
users = service.users.bulk_create(users_data)
service.commit_all()
```

### Get or Create

```python
# Get existing or create new
user, created = service.users.get_or_create(
    defaults={'name': 'Test', 'surname': 'User'},
    email='test@example.com'
)

if created:
    print('User was created')
else:
    print('User already exists')
```

### Update Multiple

```python
# Deactivate all users
all_users = service.users.list(limit=10000)
for user in all_users:
    service.users.deactivate_user(user.id)
service.commit_all()
```

### Transaction with Rollback

```python
try:
    user = service.users.create_user(...)
    project = service.projects.create_project(user_id=user.id, ...)
    service.commit_all()
except Exception as e:
    service.rollback_all()
    raise
```

---

## Error Handling

### Common Errors

**Field Uniqueness Violations:**
```python
try:
    user = service.users.create_user(
        email='existing@example.com',  # Already exists
        ...
    )
    service.commit_all()
except Exception as e:
    service.rollback_all()
    # Handle duplicate email
```

**Foreign Key Violations:**
```python
try:
    member = service.team_members.add_member(
        team_id=invalid_team_id,  # Doesn't exist
        user_id=user_id
    )
    service.commit_all()
except Exception as e:
    service.rollback_all()
    # Handle invalid team
```

**Invalid Updates:**
```python
# Trying to update non-existent record
user = service.users.update(invalid_id, name='New Name')
if user is None:
    # Record not found
    pass
```

---

## Performance Tips

1. **Use Pagination**
   ```python
   # Instead of fetching all
   users = service.users.list(skip=0, limit=100)
   ```

2. **Use Field Filters**
   ```python
   # Instead of listing all and filtering in Python
   active = service.users.list_by_field('is_active', True)
   ```

3. **Use Counts**
   ```python
   # Instead of listing and counting
   count = service.users.count_by_field('status', 'active')
   ```

4. **Batch Commits**
   ```python
   # Commit once after multiple operations
   for i in range(100):
       service.users.create_user(...)
   service.commit_all()  # Single commit
   ```

5. **Use Ordering**
   ```python
   # Get most recent with ordering
   recent = service.projects.list_ordered(
       order_by='created_at',
       ascending=False,
       limit=10
   )
   ```

---

## Integration with FastAPI

### Dependency Injection

```python
from fastapi import Depends
from app.core.database import get_db_auth, get_db_specs
from app.repositories import RepositoryService

def get_repository_service(
    auth_session = Depends(get_db_auth),
    specs_session = Depends(get_db_specs)
) -> RepositoryService:
    return RepositoryService(auth_session, specs_session)

# Use in endpoint
@app.post("/api/v1/users")
def create_user(
    email: str,
    username: str,
    password: str,
    service: RepositoryService = Depends(get_repository_service)
):
    user = service.users.create_user(
        email=email,
        username=username,
        hashed_password=User.hash_password(password)
    )
    service.commit_all()
    return user
```

---

## Testing

### Test Example

```python
def test_create_user(auth_session):
    repo = UserRepository(auth_session)

    user = repo.create_user(
        email='test@example.com',
        username='test',
        hashed_password='hash',
        name='Test'
    )
    repo.commit()

    # Verify
    assert user.id is not None
    assert user.email == 'test@example.com'

    # Query back
    queried = repo.get_by_email('test@example.com')
    assert queried.id == user.id
```

---

## Files

**Repository Files:**
- `app/repositories/base_repository.py` - Base class with CRUD operations
- `app/repositories/user_repository.py` - User, RefreshToken, AdminRole, AdminUser
- `app/repositories/project_repository.py` - Project operations
- `app/repositories/session_repository.py` - Session and ConversationHistory
- `app/repositories/question_repository.py` - Question operations
- `app/repositories/specification_repository.py` - Specification operations
- `app/repositories/team_repository.py` - Team and TeamMember
- `app/repositories/repository_service.py` - Service container

---

**Last Updated:** November 11, 2025

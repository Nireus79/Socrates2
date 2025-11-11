# Quick Start: Database Migrations

**For:** Developers new to Socrates
**Time:** 5 minutes to read

---

## TL;DR

### Run Migrations (First Time)

```bash
cd backend
python scripts/run_migrations_safe.py
```

Expected output:
```
✅ socrates_auth: 002 (head)
✅ socrates_specs: 009 (head)
```

**Done!** Your databases are ready.

---

## What Just Happened?

✅ Created `socrates_auth` database with 6 tables
✅ Created `socrates_specs` database with 25 tables
✅ Set up 200+ performance indexes
✅ Established all relationships

---

## Basic Commands

### Check Status
```bash
python scripts/run_migrations_safe.py --check-status
```

### Run Only AUTH (users, admin)
```bash
python scripts/run_migrations_safe.py --auth-only
```

### Run Only SPECS (projects, specifications, etc.)
```bash
python scripts/run_migrations_safe.py --specs-only
```

---

## What Tables Were Created?

### socrates_auth (User & Admin)
```
users                 - User accounts
refresh_tokens        - JWT tokens
admin_roles          - Admin role templates
admin_users          - User ↔ Role assignments
admin_audit_logs     - Admin action audit trail
alembic_version      - Migration tracking
```

### socrates_specs (Projects & Data)
```
projects             - Project metadata
sessions             - Conversation sessions
questions            - Specification questions
specifications       - Key-value specs
conversation_history - Chat history
conflicts            - Identified conflicts
generated_projects   - Generated code projects
generated_files      - Generated source files
quality_metrics      - Quality scores
user_behavior_patterns - User analytics
question_effectiveness - Q&A effectiveness
knowledge_base_documents - RAG documents
teams                - Team definitions
team_members         - Team membership
project_shares       - Sharing permissions
api_keys             - API key storage
llm_usage_tracking   - LLM request tracking
subscriptions        - Billing plans
invoices             - Billing records
analytics_metrics    - Dashboard metrics
document_chunks      - RAG chunks
notification_preferences - User notification settings
activity_logs        - Audit trail
project_invitations  - Collaboration invites
alembic_version      - Migration tracking
```

---

## Database Connection

### Environment Variables

Set these in your `.env` file:

```bash
# Required for migrations
DATABASE_URL_AUTH=postgresql://postgres:password@localhost:5432/socrates_auth
DATABASE_URL_SPECS=postgresql://postgres:password@localhost:5432/socrates_specs
```

### In Python Code

```python
from app.core.database import auth_engine, specs_engine, auth_session, specs_session

# Use auth_session for users/admin tables
user = auth_session.query(User).filter_by(email='user@example.com').first()

# Use specs_session for project/spec tables
project = specs_session.query(Project).filter_by(id=project_id).first()
```

---

## Common Tasks

### Add a New User

```python
from app.models import User
from app.core.database import auth_session

user = User(
    email='newuser@example.com',
    username='newuser',
    name='New',
    surname='User',
    hashed_password=User.hash_password('password')
)
auth_session.add(user)
auth_session.commit()
```

### Create a Project

```python
from app.models import Project
from app.core.database import specs_session
from uuid import UUID

user_id = UUID('...')  # From socrates_auth.users

project = Project(
    user_id=user_id,
    name='My Project',
    description='Project description',
    phase='discovery',
    status='active'
)
specs_session.add(project)
specs_session.commit()
```

### Query Projects

```python
# Get user's projects
projects = specs_session.query(Project).filter(
    Project.user_id == user_id,
    Project.status == 'active'
).all()

# Get single project
project = specs_session.query(Project).filter_by(id=project_id).first()
```

---

## Important Details

### Database Separation

Socrates uses **two separate databases** for different purposes:

| Database | Purpose | Tables |
|---|---|---|
| socrates_auth | User authentication | users, refresh_tokens, admin_* |
| socrates_specs | Projects & specs | projects, sessions, questions, etc. |

**Use the right session for each operation!**

### UUID Primary Keys

All tables use UUID (not auto-increment integers):

```python
# UUIDs are generated automatically
user_id = user.id  # Returns UUID object
# Convert to string when needed
user_id_str = str(user.id)
```

### Timestamps

All tables have `created_at` and `updated_at` (automatically set):

```python
project = Project(...)
specs_session.add(project)
specs_session.commit()

print(project.created_at)  # Automatically set by database
print(project.updated_at)  # Automatically set by database
```

### Cross-Database References

Some tables reference users but don't enforce foreign keys:

```python
# In specs database
project = Project(
    user_id=some_uuid,  # References socrates_auth.users.id
    # No FK constraint - validate in application code
)
```

---

## If Something Goes Wrong

### "Foreign key constraint fails"
Ensure parent record exists before creating child.

### "Connection refused"
Check DATABASE_URL_AUTH and DATABASE_URL_SPECS environment variables.

### "table already exists"
Migrations are idempotent - safe to run multiple times.

### "FAILED: password authentication failed"
Check your PostgreSQL password and connection string.

---

## Need More Details?

**For complete schema reference:**
→ See `DATABASE_SCHEMA_REFERENCE.md`

**For migration operations:**
→ See `MIGRATION_IMPLEMENTATION_GUIDE.md`

**For why things are designed this way:**
→ See `MIGRATION_REDESIGN_COMPLETE.md`

---

## Pro Tips

1. **Always use sessions consistently** - Don't mix auth and specs sessions
2. **Commit after each logical operation** - Not after every add
3. **Use transactions for multi-table operations** - For data consistency
4. **Check indexes before filtering** - They're already created
5. **Validate cross-DB refs in code** - No FK constraints between databases

---

## What's Next?

Once migrations are running:

1. Create SQLAlchemy models (if not already done)
2. Build API endpoints with FastAPI
3. Implement business logic
4. Write tests
5. Deploy!

---

**Version:** 1.0
**Last Updated:** November 11, 2025

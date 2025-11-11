# Migration Audit Report - Socrates
**Date:** November 11, 2025
**Status:** Phase 1 - Audit Complete

---

## Executive Summary

The socrates-ai library defines **19 core SQLAlchemy models** that require proper database schema. Current 38 migrations create these tables but with architectural issues.

**Key Findings:**
- ✅ All 19 library models have corresponding migrations
- ❌ Type inconsistencies (UUID vs VARCHAR issues)
- ❌ Mixed database assignments (wrong target databases)
- ❌ Fragmented into 38 migrations instead of logical groups
- ✅ All tables properly defined in models

---

## Part 1: Library Models Analysis

### Core Models (19 Total)

#### AUTH DATABASE (Should contain)
1. **User** - users table
   - Columns: id (UUID), email, hashed_password, role, status, name, surname, username
   - PK: id (UUID)
   - Type consistency: ✅ GOOD

#### SPECS DATABASE (Should contain)
18 models:
1. **Project** - projects table
2. **Session** - sessions table
3. **Question** - questions table
4. **Specification** - specifications table
5. **ConversationHistory** - conversation_history table
6. **Conflict** - conflicts table
7. **GeneratedProject** - generated_projects table
8. **GeneratedFile** - generated_files table
9. **QualityMetric** - quality_metrics table
10. **UserBehaviorPattern** - user_behavior_patterns table
11. **QuestionEffectiveness** - question_effectiveness table
12. **KnowledgeBaseDocument** - knowledge_base_documents table
13. **Team** - teams table
14. **TeamMember** - team_members table
15. **ProjectShare** - project_shares table
16. **APIKey** - api_keys table
17. **LLMUsageTracking** - llm_usage_tracking table
18. **BaseModel** - basemodel table (abstract)

---

## Part 2: Current Migration Mapping

### Migration Assignment Analysis

**AUTH DATABASE (5 migrations):**
- 001: users table ✅
- 002: refresh_tokens table ✅
- 020: Add user identity fields ✅
- 027: Add subscription fields ✅
- 036: notification_preferences ❌ (Should be specs or separate)

**SPECS DATABASE (33 migrations):**
- 003-010: Core tables (projects, sessions, questions, specifications, etc) ✅
- 011-019: Extended tables (quality metrics, teams, api_keys, etc) ✅
- 021-034: Modifications and new features (analytics, billing, admin, etc) ✅
- 035-038: Additional features (documents, notifications, activity logs, invitations) ✅

**Assignment Issues:**
- 031-033: admin_roles, admin_users, admin_audit_logs
  - Logically belong in AUTH (user management)
  - Currently assigned to SPECS ❌
  - Type mismatch: Using VARCHAR(36) instead of UUID ❌

---

## Part 3: Type Consistency Analysis

### Current Issues

**Problem 1: Admin Tables Type Mismatch**
```
Current (WRONG):
- admin_roles.id: VARCHAR(36)
- admin_users.id: VARCHAR(36)
- admin_users.user_id: VARCHAR(36) -> references users.id (UUID)

Expected (RIGHT):
- admin_roles.id: UUID
- admin_users.id: UUID
- admin_users.user_id: UUID -> references users.id (UUID)
```

**Problem 2: Cross-Database References**
- Projects (specs) reference users (auth) via creator_id, owner_id
- Cannot use direct foreign keys across databases
- Solution: Documented application-level integrity

**Problem 3: Inconsistent ID Types**
- Most tables: UUID (correct)
- Admin tables: VARCHAR(36) (wrong)
- Needs standardization

---

## Part 4: Consolidated Migration Design

### Proposed Structure: 10 Migrations Total

#### AUTH DATABASE: 3 Migrations

**AUTH_001: Initial Auth Schema**
```
Tables:
- users (UUID, complete schema)
- refresh_tokens (JWT management)

Indexes:
- users(email) - unique
- users(username) - unique
- users(status)
- refresh_tokens(user_id)
```

**AUTH_002: Admin Management**
```
Tables:
- admin_roles (UUID, permissions array)
- admin_users (UUID, FK to users & admin_roles)
- admin_audit_logs (audit trail)

Indexes:
- admin_users(user_id)
- admin_users(role_id)
- admin_audit_logs(admin_id)
```

**AUTH_003: Subscription & Billing Fields**
```
Modifications to users table:
- ADD subscription_tier (VARCHAR 20)
- ADD stripe_customer_id (VARCHAR 255)
- ADD trial_ends_at (TIMESTAMP)
- ADD subscription_status (VARCHAR 20)

Indexes:
- users(subscription_tier)
- users(stripe_customer_id)
```

#### SPECS DATABASE: 7 Migrations

**SPECS_001: Core Specification Tables**
```
Tables:
- projects (UUID, complete)
- sessions (UUID, complete)
- questions (UUID, complete)
- specifications (UUID, complete, with key/value)
- conversation_history (UUID, complete)
- conflicts (UUID, complete)

All with UUID primary keys and consistent types
All with proper timestamps
Cross-database refs: user_id, creator_id (no FK constraint)
```

**SPECS_002: Generated Content**
```
Tables:
- generated_projects (UUID)
- generated_files (UUID)

References: projects.id (UUID)
```

**SPECS_003: Tracking & Analytics**
```
Tables:
- quality_metrics (UUID)
- user_behavior_patterns (UUID)
- question_effectiveness (UUID)
- knowledge_base_documents (UUID)

All UUID, consistent types
Includes embedding support (TEXT or pgvector optional)
```

**SPECS_004: Collaboration & Sharing**
```
Tables:
- teams (UUID)
- team_members (UUID, FK to teams & users ref)
- project_shares (UUID, FK to projects & users ref)

All UUID primary keys
User references: cross-database (no FK)
```

**SPECS_005: API & LLM Integration**
```
Tables:
- api_keys (UUID, encrypted values)
- llm_usage_tracking (UUID)
- subscriptions (UUID, Stripe integration)
- invoices (UUID, billing records)

All UUID, consistent types
Includes JSON metadata fields
```

**SPECS_006: Analytics & Search**
```
Tables:
- analytics_metrics (UUID, for tracking)
- document_chunks (UUID, for RAG/search)
- notification_preferences (UUID, user settings)

All UUID primary keys
Includes JSONB for flexible data
```

**SPECS_007: Activity & Project Management**
```
Tables:
- activity_logs (UUID, audit trail)
- project_invitations (UUID, collaboration invites)

Indexes:
- activity_logs(resource_type, resource_id)
- project_invitations(project_id, status)

Optional features (pgvector, etc) gracefully skipped
```

---

## Part 5: Key Design Decisions

### 1. ID Types
**Decision:** All IDs use UUID (postgresql.UUID)
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```
- **Benefit:** Consistent, secure, globally unique
- **Avoids:** VARCHAR(36) confusion, type mismatches
- **Supports:** Distributed systems, better security

### 2. Cross-Database References
**Decision:** No direct foreign keys between databases
```python
# In specs database, reference users:
user_id: UUID  # No FK constraint, documented as reference to auth.users.id
```
- **Benefit:** Loose coupling, database independence, scalability
- **Trade-off:** Application-level referential integrity
- **Documented:** Clear comments in migrations and models

### 3. Timestamps
**Decision:** All use `DateTime(timezone=True)` with server defaults
```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```
- **Benefit:** Timezone-aware, database-managed, consistent
- **Supports:** Multi-region deployment

### 4. Optional Features
**Decision:** pgvector and advanced analytics gracefully skip if unavailable
```python
# In migration 026 (optional):
try:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    # Create pgvector-dependent tables
except:
    # Skip on Windows development
    pass
```

### 5. Alembic Branching
**Decision:** Use branch labels for auth vs specs
```python
# In each migration file:
branch_labels = ('auth',) or ('specs',)
```
- **Benefit:** Proper multi-database Alembic support
- **Commands:** `alembic upgrade auth@head` or `alembic upgrade specs@head`
- **Status tracking:** `alembic history`

---

## Part 6: Validation Against Library Compatibility

### Model → Migration Mapping

| Library Model | Migration | Status | Notes |
|---|---|---|---|
| User | AUTH_001 | ✅ | Complete |
| Project | SPECS_001 | ✅ | Complete |
| Session | SPECS_001 | ✅ | Complete |
| Question | SPECS_001 | ✅ | Complete |
| Specification | SPECS_001 | ✅ | Complete with key/value |
| ConversationHistory | SPECS_001 | ✅ | Complete |
| Conflict | SPECS_001 | ✅ | Complete |
| GeneratedProject | SPECS_002 | ✅ | Complete |
| GeneratedFile | SPECS_002 | ✅ | Complete |
| QualityMetric | SPECS_003 | ✅ | Complete |
| UserBehaviorPattern | SPECS_003 | ✅ | Complete |
| QuestionEffectiveness | SPECS_003 | ✅ | Complete |
| KnowledgeBaseDocument | SPECS_003 | ✅ | Complete |
| Team | SPECS_004 | ✅ | Complete |
| TeamMember | SPECS_004 | ✅ | Complete |
| ProjectShare | SPECS_004 | ✅ | Complete |
| APIKey | SPECS_005 | ✅ | Complete |
| LLMUsageTracking | SPECS_005 | ✅ | Complete |
| BaseModel | (implicit) | ✅ | Abstract, no table |

**Compatibility Score:** 19/19 models have migrations ✅

---

## Part 7: Issues to Fix in New Migrations

### Type Consistency
- [ ] All IDs use UUID, not VARCHAR(36)
- [ ] All timestamps use DateTime(timezone=True)
- [ ] No mixed type references

### Database Assignment
- [ ] Admin tables (031-033) move to AUTH database
- [ ] notification_preferences (036) clarify target
- [ ] All specs tables in SPECS database

### Schema Quality
- [ ] Proper indexes on foreign keys
- [ ] Proper indexes on filtered queries
- [ ] Unique constraints where needed
- [ ] Server defaults for timestamps

### Documentation
- [ ] Each migration has clear docstring
- [ ] Cross-database references documented
- [ ] Design decisions explained
- [ ] pgvector and optional features marked

---

## Part 8: Implementation Roadmap

### Current State (38 migrations)
- ❌ Type inconsistencies
- ❌ Wrong database assignments
- ❌ Fragmented logic
- ✅ All tables present

### Target State (10 migrations)
- ✅ Consistent UUID types
- ✅ Correct database assignments
- ✅ Consolidated logic
- ✅ All tables present
- ✅ Proper Alembic branching
- ✅ Library compatible

### Effort
- Phase 2 (Design): 20 minutes
- Phase 3 (Implementation): 30 minutes
- Phase 4 (Testing): 15 minutes
- Phase 5 (Documentation): 10 minutes
- **Total:** ~75 minutes

---

## Part 9: Risks & Mitigation

| Risk | Mitigation |
|---|---|
| Breaking existing deployments | Keep old migrations in archive/ for reference |
| Test failures during rebuild | Run full test suite after each migration |
| Cross-database FK errors | Document app-level integrity in code |
| pgvector not available | Graceful skip with try/except |
| Type migration data issues | Start fresh on clean databases |

---

## Conclusion

**The 19 library models are properly designed and match the migrations needed.** The consolidation from 38 → 10 migrations will:

1. **Fix type inconsistencies** (all UUID)
2. **Fix database assignments** (auth vs specs clear)
3. **Improve maintainability** (fewer, clearer migrations)
4. **Add Alembic branching** (proper multi-DB support)
5. **Ensure library compatibility** (schema matches models exactly)

**Ready for Phase 2: Design Clean Schema**

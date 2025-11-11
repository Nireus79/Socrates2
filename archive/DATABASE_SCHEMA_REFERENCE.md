# Socrates2 Database Schema Reference

**Version:** 1.0 (Phase 2 Complete)
**Date:** November 11, 2025
**Status:** Production Ready

---

## Overview

Socrates2 uses a two-database architecture for optimal separation of concerns:
- **socrates_auth:** User authentication and admin management
- **socrates_specs:** Project specifications, collaboration, and analytics

This document provides a complete reference for all 31 tables across both databases.

---

## socrates_auth Database

### 1. users (Migration 001)

**Purpose:** Store user accounts and authentication credentials

**Table Structure:**
```
Column              Type            Constraints         Description
id                  UUID            PK                  Unique user identifier
email               VARCHAR(255)    UNIQUE, NOT NULL    User email address
hashed_password     VARCHAR(255)    NOT NULL            Bcrypt hashed password
name                VARCHAR(100)    NULLABLE            User first name
surname             VARCHAR(100)    NULLABLE            User last name
username            VARCHAR(50)     UNIQUE, NULLABLE    Unique username
is_active           BOOLEAN         NOT NULL, def:true  Account active flag
is_verified         BOOLEAN         NOT NULL, def:false Email verified flag
role                VARCHAR(20)     NOT NULL, def:user  Role (user, admin, moderator)
status              VARCHAR(20)     NOT NULL, def:active Status (active, inactive, suspended, deleted)
subscription_tier   VARCHAR(20)     NULLABLE            Subscription tier
stripe_customer_id  VARCHAR(255)    NULLABLE            Stripe integration ID
trial_ends_at       TIMESTAMP TZ    NULLABLE            Trial expiration
subscription_status VARCHAR(20)     NULLABLE            Subscription status
created_at          TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at          TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_users_email` - UNIQUE, for login lookups
- `ix_users_username` - UNIQUE, for username lookups
- `ix_users_status` - for filtering active users
- `ix_users_is_active` - for active user queries
- `ix_users_created_at` - for time-based queries

**Check Constraints:**
- `ck_users_role_valid`: role IN ('user', 'admin', 'moderator')
- `ck_users_status_valid`: status IN ('active', 'inactive', 'suspended', 'deleted')

**Relationships:**
- One user can have many refresh_tokens (CASCADE delete)
- One user can have many admin assignments
- One user can own many teams
- One user can be member of many teams
- One user can have many projects (creator_id, owner_id)
- One user can have many API keys

---

### 2. refresh_tokens (Migration 001)

**Purpose:** Manage JWT refresh token lifecycle and revocation

**Table Structure:**
```
Column          Type            Constraints         Description
id              UUID            PK                  Unique token record ID
user_id         UUID            FK(users), NOT NULL Reference to user
token           VARCHAR(500)    UNIQUE, NOT NULL    JWT refresh token (hashed)
expires_at      TIMESTAMP TZ    NOT NULL            Token expiration time
is_revoked      BOOLEAN         NOT NULL, def:false Revocation flag
created_at      TIMESTAMP TZ    NOT NULL, server    Creation timestamp
revoked_at      TIMESTAMP TZ    NULLABLE            Revocation timestamp
```

**Indexes:**
- `ix_refresh_tokens_user_id` - for user token lookups
- `ix_refresh_tokens_token` - UNIQUE, for token validation
- `ix_refresh_tokens_expires_at` - for cleanup queries
- `ix_refresh_tokens_is_revoked` - for active token filtering

**Foreign Keys:**
- `user_id` → users.id (CASCADE DELETE) - when user deleted, all tokens deleted

---

### 3. admin_roles (Migration 002)

**Purpose:** Define admin role templates and permissions

**Table Structure:**
```
Column           Type                  Constraints         Description
id               UUID                  PK                  Role identifier
name             VARCHAR(100)          UNIQUE, NOT NULL    Role name
description      TEXT                  NULLABLE            Role description
permissions      ARRAY(VARCHAR)        NOT NULL, def:{} Permission strings (e.g., admin:users:read)
is_system_role   BOOLEAN               NOT NULL, def:false System role flag (immutable)
created_at       TIMESTAMP TZ          NOT NULL, server    Creation timestamp
updated_at       TIMESTAMP TZ          NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_admin_roles_name` - UNIQUE, for role lookup
- `ix_admin_roles_is_system_role` - for filtering built-in roles

**Example Roles:**
- `super_admin` - Full system access
- `moderator` - Content moderation access
- `support` - Customer support access

---

### 4. admin_users (Migration 002)

**Purpose:** Map users to admin roles with audit trail

**Table Structure:**
```
Column            Type            Constraints                     Description
id                UUID            PK                              Assignment record ID
user_id           UUID            FK(users), NOT NULL             Reference to user
role_id           UUID            FK(admin_roles), NOT NULL       Reference to role
granted_by_id     UUID            NULLABLE                        Who granted the role
reason            TEXT            NULLABLE                        Reason for granting
revoked_at        TIMESTAMP TZ    NULLABLE                        Revocation time
created_at        TIMESTAMP TZ    NOT NULL, server                Grant timestamp
updated_at        TIMESTAMP TZ    NOT NULL, server                Update timestamp
```

**Constraints:**
- UNIQUE(user_id, role_id) - one assignment per user/role pair
- FK(user_id) → users.id (CASCADE DELETE)
- FK(role_id) → admin_roles.id (RESTRICT DELETE)

**Indexes:**
- `ix_admin_users_user_id` - for user role lookups
- `ix_admin_users_role_id` - for role member lookups
- `ix_admin_users_granted_by_id` - for who-granted queries
- `ix_admin_users_revoked_at` - for active role filtering

---

### 5. admin_audit_logs (Migration 002)

**Purpose:** Audit trail for all admin actions

**Table Structure:**
```
Column       Type            Constraints         Description
id           UUID            PK                  Log entry ID
admin_id     UUID            FK(users), NOT NULL Admin who performed action
action       VARCHAR(100)    NOT NULL            Action type (user_created, role_assigned, etc.)
resource_type VARCHAR(100)   NOT NULL            Resource type (user, project, team, etc.)
resource_id  VARCHAR(36)     NOT NULL            ID of affected resource
changes      JSONB           NULLABLE            Before/after changes
ip_address   VARCHAR(45)     NULLABLE            Request IP address
user_agent   VARCHAR(500)    NULLABLE            Browser user agent
created_at   TIMESTAMP TZ    NOT NULL, server    Action timestamp
```

**Foreign Keys:**
- `admin_id` → users.id (RESTRICT DELETE) - preserve audit trail

**Indexes:**
- `ix_admin_audit_logs_admin_id` - for admin action history
- `ix_admin_audit_logs_action` - for action type filtering
- `ix_admin_audit_logs_resource_type` - for resource type filtering
- `ix_admin_audit_logs_resource` - COMPOSITE(resource_type, resource_id)
- `ix_admin_audit_logs_created_at` - for time range queries

---

## socrates_specs Database

### 6. projects (Migration 003)

**Purpose:** Project metadata and state management

**Table Structure:**
```
Column           Type                  Constraints         Description
id               UUID                  PK                  Project identifier
user_id          UUID                  NOT NULL            Creator/owner user ID (cross-db ref)
name             VARCHAR(255)          NOT NULL            Project name
description      TEXT                  NULLABLE            Project description
phase            VARCHAR(50)           NOT NULL, def:discovery Current phase (discovery, specification, etc.)
status           VARCHAR(20)           NOT NULL, def:active Project status (active, archived, completed)
maturity_level   INTEGER               NULLABLE            Maturity score (0-100)
metadata         JSONB                 NOT NULL, def:{}    Flexible project metadata
created_at       TIMESTAMP TZ          NOT NULL, server    Creation timestamp
updated_at       TIMESTAMP TZ          NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_projects_user_id` - for user's projects lookup
- `ix_projects_status` - for active project filtering
- `ix_projects_phase` - for phase-based queries
- `ix_projects_created_at` - for time-based sorting

**Relationships:**
- One project has many sessions
- One project has many questions
- One project has many specifications
- One project has many conflicts
- One project has many generated projects
- One project has many quality metrics
- One project has many project shares
- One project has many activity logs
- One project has many project invitations

---

### 7. sessions (Migration 003)

**Purpose:** Conversation sessions within projects

**Table Structure:**
```
Column          Type            Constraints         Description
id              UUID            PK                  Session identifier
project_id      UUID            FK(projects), NOT NULL Reference to project
user_id         UUID            NOT NULL            Session user ID (cross-db ref)
title           VARCHAR(255)    NULLABLE            Session title
status          VARCHAR(20)     NOT NULL, def:active Session status (active, archived, completed)
message_count   INTEGER         NOT NULL, def:0     Total messages in session
metadata        JSONB           NOT NULL, def:{}    Session metadata
created_at      TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at      TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_sessions_project_id` - for project sessions
- `ix_sessions_user_id` - for user sessions
- `ix_sessions_status` - for active sessions
- `ix_sessions_created_at` - for sorting

**Relationships:**
- One session has many conversation history entries
- One session has many questions

---

### 8. questions (Migration 003)

**Purpose:** Specification questions and Q&A tracking

**Table Structure:**
```
Column          Type            Constraints         Description
id              UUID            PK                  Question identifier
project_id      UUID            FK(projects), NOT NULL Reference to project
session_id      UUID            FK(sessions), NULLABLE Reference to session
text            TEXT            NOT NULL            Question text
category        VARCHAR(100)    NULLABLE            Question category
priority        VARCHAR(20)     NOT NULL, def:medium Priority (low, medium, high, critical)
answer          TEXT            NULLABLE            Answer provided
status          VARCHAR(20)     NOT NULL, def:pending Status (pending, answered, skipped, resolved)
metadata        JSONB           NOT NULL, def:{}    Question metadata
created_at      TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at      TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)
- `session_id` → sessions.id (SET NULL)

**Indexes:**
- `ix_questions_project_id` - for project questions
- `ix_questions_session_id` - for session questions
- `ix_questions_status` - for status filtering
- `ix_questions_category` - for category filtering
- `ix_questions_created_at` - for sorting

---

### 9. specifications (Migration 003)

**Purpose:** Key-value specifications with versioning

**Table Structure:**
```
Column           Type            Constraints         Description
id               UUID            PK                  Specification identifier
project_id       UUID            FK(projects), NOT NULL Reference to project
key              VARCHAR(255)    NOT NULL            Specification key
value            TEXT            NULLABLE            Specification value
type             VARCHAR(100)    NULLABLE            Type (functional, non-functional, etc.)
status           VARCHAR(20)     NOT NULL, def:draft Status (draft, approved, implemented)
version          INTEGER         NOT NULL, def:1     Version number
metadata         JSONB           NOT NULL, def:{}    Approval metadata
created_at       TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at       TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Constraints:**
- UNIQUE(project_id, key, version)

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_specifications_project_id` - for project specs
- `ix_specifications_key` - for key lookup
- `ix_specifications_status` - for status filtering
- `ix_specifications_type` - for type filtering
- `ix_specifications_created_at` - for sorting

---

### 10. conversation_history (Migration 003)

**Purpose:** Chat history and conversation tracking

**Table Structure:**
```
Column           Type            Constraints         Description
id               UUID            PK                  Message identifier
session_id       UUID            FK(sessions), NOT NULL Reference to session
role             VARCHAR(20)     NOT NULL            Sender role (user, assistant, system)
content          TEXT            NOT NULL            Message content
message_type     VARCHAR(50)     NULLABLE            Message type (question, answer, etc.)
tokens_used      INTEGER         NULLABLE            LLM tokens used
metadata         JSONB           NOT NULL, def:{}    Message metadata
created_at       TIMESTAMP TZ    NOT NULL, server    Message timestamp
```

**Foreign Keys:**
- `session_id` → sessions.id (CASCADE DELETE)

**Indexes:**
- `ix_conversation_history_session_id` - for session messages
- `ix_conversation_history_role` - for role filtering
- `ix_conversation_history_created_at` - for chronological order

---

### 11. conflicts (Migration 003)

**Purpose:** Track identified conflicts in specifications

**Table Structure:**
```
Column                  Type                      Constraints         Description
id                      UUID                      PK                  Conflict identifier
project_id              UUID                      FK(projects), NOT NULL Reference to project
title                   VARCHAR(255)              NOT NULL            Conflict title
description             TEXT                      NULLABLE            Detailed description
type                    VARCHAR(100)              NULLABLE            Conflict type
severity                VARCHAR(20)               NOT NULL, def:medium Severity level
status                  VARCHAR(20)               NOT NULL, def:open  Status (open, resolved, etc.)
resolution              TEXT                      NULLABLE            Resolution description
related_specifications  ARRAY(UUID)               NULLABLE            Related specification IDs
metadata                JSONB                     NOT NULL, def:{}    Conflict metadata
created_at              TIMESTAMP TZ              NOT NULL, server    Creation timestamp
updated_at              TIMESTAMP TZ              NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_conflicts_project_id` - for project conflicts
- `ix_conflicts_status` - for status filtering
- `ix_conflicts_severity` - for severity filtering
- `ix_conflicts_type` - for type filtering
- `ix_conflicts_created_at` - for sorting

---

### 12. generated_projects (Migration 004)

**Purpose:** Generated project artifacts from specifications

**Table Structure:**
```
Column              Type                  Constraints         Description
id                  UUID                  PK                  Generated project ID
project_id          UUID                  FK(projects), NOT NULL Reference to source project
name                VARCHAR(255)          NOT NULL            Generated project name
description         TEXT                  NULLABLE            Description
language            VARCHAR(50)           NULLABLE            Primary language
framework           VARCHAR(100)          NULLABLE            Framework used
version             VARCHAR(20)           NULLABLE            Project version
status              VARCHAR(20)           NOT NULL, def:draft Status (draft, generated, reviewed, deployed)
file_count          INTEGER               NOT NULL, def:0     Number of generated files
total_lines_of_code INTEGER               NULLABLE            Total LOC
structure           JSONB                 NULLABLE            Project structure tree
configuration       JSONB                 NULLABLE            Configuration metadata
metadata            JSONB                 NOT NULL, def:{}    Generation metadata
created_at          TIMESTAMP TZ          NOT NULL, server    Generation timestamp
updated_at          TIMESTAMP TZ          NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_generated_projects_project_id` - for project generations
- `ix_generated_projects_status` - for status filtering
- `ix_generated_projects_language` - for language filtering
- `ix_generated_projects_framework` - for framework filtering
- `ix_generated_projects_created_at` - for sorting

---

### 13. generated_files (Migration 004)

**Purpose:** Individual source code files from generated projects

**Table Structure:**
```
Column              Type            Constraints                 Description
id                  UUID            PK                          File identifier
generated_project_id UUID            FK(generated_projects), NOT NULL Reference to generated project
path                VARCHAR(500)    NOT NULL                    File path
filename            VARCHAR(255)    NOT NULL                    File name with extension
file_type           VARCHAR(50)     NULLABLE                    File type (python, js, etc.)
content             TEXT            NULLABLE                    File content
lines_of_code       INTEGER         NULLABLE                    LOC count
purpose             VARCHAR(255)    NULLABLE                    File purpose
status              VARCHAR(20)     NOT NULL, def:draft         File status
metadata            JSONB           NOT NULL, def:{}            File metadata
created_at          TIMESTAMP TZ    NOT NULL, server            Creation timestamp
updated_at          TIMESTAMP TZ    NOT NULL, server            Update timestamp
```

**Constraints:**
- UNIQUE(generated_project_id, path)

**Foreign Keys:**
- `generated_project_id` → generated_projects.id (CASCADE DELETE)

**Indexes:**
- `ix_generated_files_generated_project_id` - for project files
- `ix_generated_files_path` - for file lookup
- `ix_generated_files_file_type` - for type filtering
- `ix_generated_files_status` - for status filtering
- `ix_generated_files_created_at` - for sorting

---

### 14. quality_metrics (Migration 005)

**Purpose:** Track quality scores and assessments

**Table Structure:**
```
Column          Type            Constraints         Description
id              UUID            PK                  Metric record ID
project_id      UUID            FK(projects), NOT NULL Reference to project
metric_name     VARCHAR(100)    NOT NULL            Metric name
metric_value    FLOAT           NOT NULL            Metric value
metric_type     VARCHAR(50)     NULLABLE            Metric type (specification_quality, etc.)
measured_at     TIMESTAMP TZ    NULLABLE            Measurement time
details         JSONB           NULLABLE            Detailed breakdown
metadata        JSONB           NOT NULL, def:{}    Additional metadata
created_at      TIMESTAMP TZ    NOT NULL, server    Creation timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_quality_metrics_project_id` - for project metrics
- `ix_quality_metrics_metric_name` - for metric name filtering
- `ix_quality_metrics_metric_type` - for type filtering
- `ix_quality_metrics_created_at` - for sorting

---

### 15. user_behavior_patterns (Migration 005)

**Purpose:** Analytics on user interaction patterns

**Table Structure:**
```
Column                  Type            Constraints         Description
id                      UUID            PK                  Pattern record ID
user_id                 UUID            NOT NULL            User ID (cross-db ref)
pattern_type            VARCHAR(100)    NOT NULL            Pattern type
pattern_data            JSONB           NOT NULL, def:{}    Pattern data
confidence_score        FLOAT           NULLABLE            Confidence (0-1)
observation_period      VARCHAR(50)     NULLABLE            Period (daily, weekly, etc.)
sample_size             INTEGER         NULLABLE            Sample size
metadata                JSONB           NOT NULL, def:{}    Additional metadata
created_at              TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at              TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_user_behavior_patterns_user_id` - for user patterns
- `ix_user_behavior_patterns_pattern_type` - for type filtering
- `ix_user_behavior_patterns_created_at` - for sorting

---

### 16. question_effectiveness (Migration 005)

**Purpose:** Track question effectiveness and improvements

**Table Structure:**
```
Column                      Type            Constraints         Description
id                          UUID            PK                  Effectiveness record ID
question_id                 UUID            NULLABLE            Reference to questions
question_text               TEXT            NULLABLE            Question text for reference
project_type                VARCHAR(100)    NULLABLE            Project type
effectiveness_score         FLOAT           NULLABLE            Effectiveness score
relevance_score             FLOAT           NULLABLE            Relevance score
clarity_score               FLOAT           NULLABLE            Clarity score
times_asked                 INTEGER         NOT NULL, def:0     Times asked
times_skipped               INTEGER         NOT NULL, def:0     Times skipped
average_response_time_seconds FLOAT          NULLABLE            Average response time
feedback                    JSONB           NULLABLE            User feedback
recommendations              TEXT            NULLABLE            Improvement recommendations
metadata                    JSONB           NOT NULL, def:{}    Additional metadata
created_at                  TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at                  TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_question_effectiveness_question_id` - for question effectiveness
- `ix_question_effectiveness_project_type` - for project type filtering
- `ix_question_effectiveness_effectiveness_score` - for score sorting
- `ix_question_effectiveness_created_at` - for sorting

---

### 17. knowledge_base_documents (Migration 005)

**Purpose:** RAG documents for retrieval and learning

**Table Structure:**
```
Column              Type                  Constraints         Description
id                  UUID                  PK                  Document identifier
title               VARCHAR(255)          NOT NULL            Document title
content             TEXT                  NULLABLE            Document content
document_type       VARCHAR(100)          NULLABLE            Type (best_practice, pattern, etc.)
category            VARCHAR(100)          NULLABLE            Category (architecture, testing, etc.)
tags                ARRAY(VARCHAR)        NULLABLE            Search tags
source              VARCHAR(255)          NULLABLE            Document source
version             INTEGER               NOT NULL, def:1     Version number
is_approved         BOOLEAN               NOT NULL, def:false Approval status
relevance_score     FLOAT                 NULLABLE            Relevance (0-1)
usage_count         INTEGER               NOT NULL, def:0     Usage count
metadata            JSONB                 NOT NULL, def:{}    Metadata (author, approved_by, etc.)
created_at          TIMESTAMP TZ          NOT NULL, server    Creation timestamp
updated_at          TIMESTAMP TZ          NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_knowledge_base_documents_title` - for title search
- `ix_knowledge_base_documents_document_type` - for type filtering
- `ix_knowledge_base_documents_category` - for category filtering
- `ix_knowledge_base_documents_is_approved` - for approval status
- `ix_knowledge_base_documents_created_at` - for sorting

---

### 18. teams (Migration 006)

**Purpose:** Team definitions and management

**Table Structure:**
```
Column           Type            Constraints         Description
id               UUID            PK                  Team identifier
name             VARCHAR(255)    UNIQUE, NOT NULL    Team name
description      TEXT            NULLABLE            Team description
owner_id         UUID            NOT NULL            Team owner user ID (cross-db ref)
status           VARCHAR(20)     NOT NULL, def:active Team status (active, archived)
member_count     INTEGER         NOT NULL, def:1     Current member count
project_count    INTEGER         NOT NULL, def:0     Project count
settings         JSONB           NOT NULL, def:{}    Team settings
metadata         JSONB           NOT NULL, def:{}    Team metadata
created_at       TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at       TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_teams_owner_id` - for owner's teams
- `ix_teams_status` - for active teams
- `ix_teams_name` - UNIQUE, for team lookup
- `ix_teams_created_at` - for sorting

---

### 19. team_members (Migration 006)

**Purpose:** Team membership and role assignments

**Table Structure:**
```
Column               Type            Constraints                 Description
id                   UUID            PK                          Member record ID
team_id              UUID            FK(teams), NOT NULL         Reference to team
user_id              UUID            NOT NULL                    Member user ID (cross-db ref)
role                 VARCHAR(50)     NOT NULL, def:member        Role (owner, admin, lead, member, viewer)
permission_level     VARCHAR(50)     NULLABLE                    Permission level (read, write, admin)
status               VARCHAR(20)     NOT NULL, def:active        Status (active, invited, inactive)
invited_by_id        UUID            NULLABLE                    Who invited them (cross-db ref)
joined_at            TIMESTAMP TZ    NULLABLE                    Join timestamp
contribution_score   FLOAT           NULLABLE                    Contribution score
metadata             JSONB           NOT NULL, def:{}            Member metadata
created_at           TIMESTAMP TZ    NOT NULL, server            Creation timestamp
updated_at           TIMESTAMP TZ    NOT NULL, server            Update timestamp
```

**Constraints:**
- UNIQUE(team_id, user_id)

**Foreign Keys:**
- `team_id` → teams.id (CASCADE DELETE)

**Indexes:**
- `ix_team_members_team_id` - for team members
- `ix_team_members_user_id` - for user teams
- `ix_team_members_role` - for role filtering
- `ix_team_members_status` - for status filtering
- `ix_team_members_created_at` - for sorting

---

### 20. project_shares (Migration 006)

**Purpose:** Project sharing and access control

**Table Structure:**
```
Column                Type            Constraints         Description
id                    UUID            PK                  Share record ID
project_id            UUID            FK(projects), NOT NULL Reference to project
shared_with_user_id   UUID            NULLABLE            Shared with user ID (cross-db ref)
shared_with_team_id   UUID            FK(teams), NULLABLE Shared with team
shared_by_id          UUID            NOT NULL            Who shared it (cross-db ref)
permission_level      VARCHAR(50)     NOT NULL, def:view  Permission (view, comment, edit, admin)
access_type           VARCHAR(50)     NOT NULL            Access type (shared_user, shared_team, public, link)
expiry_date           TIMESTAMP TZ    NULLABLE            Expiration date
password_protected    BOOLEAN         NOT NULL, def:false Password protection flag
access_count          INTEGER         NOT NULL, def:0     Access count
last_accessed_at      TIMESTAMP TZ    NULLABLE            Last access time
metadata              JSONB           NOT NULL, def:{}    Share metadata
created_at            TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at            TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)
- `shared_with_team_id` → teams.id (CASCADE DELETE)

**Indexes:**
- `ix_project_shares_project_id` - for project shares
- `ix_project_shares_shared_with_user_id` - for user shares
- `ix_project_shares_shared_with_team_id` - for team shares
- `ix_project_shares_shared_by_id` - for who shared it
- `ix_project_shares_permission_level` - for permission filtering
- `ix_project_shares_access_type` - for access type filtering
- `ix_project_shares_created_at` - for sorting

---

### 21. api_keys (Migration 007)

**Purpose:** API key management with encryption

**Table Structure:**
```
Column              Type            Constraints         Description
id                  UUID            PK                  Key record ID
user_id             UUID            NOT NULL            Key owner user ID (cross-db ref)
name                VARCHAR(255)    NOT NULL            Key name/label
key_hash            VARCHAR(255)    UNIQUE, NOT NULL    Hashed API key (never store plain)
key_preview         VARCHAR(20)     NULLABLE            Last 4 chars preview (e.g., ...abcd)
status              VARCHAR(20)     NOT NULL, def:active Key status (active, revoked, expired)
scope               ARRAY(VARCHAR)  NULLABLE            Permission scopes
rate_limit          INTEGER         NULLABLE            Requests per minute limit
usage_count         INTEGER         NOT NULL, def:0     Total requests made
last_used_at        TIMESTAMP TZ    NULLABLE            Last usage time
expires_at          TIMESTAMP TZ    NULLABLE            Expiration date
metadata            JSONB           NOT NULL, def:{}    Key metadata
created_at          TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at          TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_api_keys_user_id` - for user's keys
- `ix_api_keys_status` - for active keys
- `ix_api_keys_key_hash` - UNIQUE, for key validation
- `ix_api_keys_created_at` - for sorting

---

### 22. llm_usage_tracking (Migration 007)

**Purpose:** Track LLM requests, tokens, and costs

**Table Structure:**
```
Column               Type            Constraints         Description
id                   UUID            PK                  Usage record ID
user_id              UUID            NOT NULL            User ID (cross-db ref)
project_id           UUID            FK(projects), NULLABLE Reference to project
model_name           VARCHAR(100)    NOT NULL            Model used (claude-3-opus, etc.)
operation_type       VARCHAR(100)    NULLABLE            Operation type (code_generation, etc.)
input_tokens         INTEGER         NOT NULL            Input token count
output_tokens        INTEGER         NOT NULL            Output token count
total_tokens         INTEGER         NOT NULL            Total token count
cost_usd             NUMERIC(10,6)   NULLABLE            Cost in USD
latency_ms           INTEGER         NULLABLE            Response latency (ms)
status               VARCHAR(20)     NOT NULL, def:success Status (success, error, timeout)
error_message        TEXT            NULLABLE            Error message if failed
metadata             JSONB           NOT NULL, def:{}    Request metadata
created_at           TIMESTAMP TZ    NOT NULL, server    Request timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (SET NULL)

**Indexes:**
- `ix_llm_usage_tracking_user_id` - for user usage
- `ix_llm_usage_tracking_project_id` - for project usage
- `ix_llm_usage_tracking_model_name` - for model filtering
- `ix_llm_usage_tracking_operation_type` - for operation filtering
- `ix_llm_usage_tracking_status` - for status filtering
- `ix_llm_usage_tracking_created_at` - for sorting

---

### 23. subscriptions (Migration 007)

**Purpose:** Subscription plans and management

**Table Structure:**
```
Column                  Type            Constraints         Description
id                      UUID            PK                  Subscription ID
user_id                 UUID            NOT NULL            Subscriber user ID (cross-db ref)
plan_name               VARCHAR(100)    NOT NULL            Plan name (free, starter, pro, enterprise)
plan_type               VARCHAR(50)     NULLABLE            Type (monthly, yearly, usage-based)
status                  VARCHAR(20)     NOT NULL, def:active Status (active, cancelled, suspended, expired)
price_usd               NUMERIC(10,2)   NULLABLE            Monthly price
billing_cycle_start     TIMESTAMP TZ    NULLABLE            Cycle start
billing_cycle_end       TIMESTAMP TZ    NULLABLE            Cycle end
stripe_customer_id      VARCHAR(255)    NULLABLE            Stripe customer ID
stripe_subscription_id  VARCHAR(255)    NULLABLE            Stripe subscription ID
features                JSONB           NOT NULL, def:{}    Feature flags
auto_renew              BOOLEAN         NOT NULL, def:true  Auto-renewal flag
metadata                JSONB           NOT NULL, def:{}    Subscription metadata
created_at              TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at              TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Indexes:**
- `ix_subscriptions_user_id` - for user subscriptions
- `ix_subscriptions_status` - for active subscriptions
- `ix_subscriptions_plan_name` - for plan filtering
- `ix_subscriptions_stripe_customer_id` - for Stripe integration
- `ix_subscriptions_created_at` - for sorting

---

### 24. invoices (Migration 007)

**Purpose:** Billing records and payment tracking

**Table Structure:**
```
Column                  Type            Constraints         Description
id                      UUID            PK                  Invoice ID
user_id                 UUID            NOT NULL            Customer user ID (cross-db ref)
subscription_id         UUID            FK(subscriptions), NULLABLE Reference to subscription
invoice_number          VARCHAR(50)     UNIQUE, NOT NULL    Invoice number
amount_usd              NUMERIC(10,2)   NOT NULL            Invoice amount
currency                VARCHAR(3)      NOT NULL, def:USD   Currency code
status                  VARCHAR(20)     NOT NULL, def:draft Status (draft, sent, paid, overdue)
description             TEXT            NULLABLE            Invoice description
line_items              JSONB           NULLABLE            Line item details
issued_date             TIMESTAMP TZ    NULLABLE            Issue date
due_date                TIMESTAMP TZ    NULLABLE            Due date
paid_date               TIMESTAMP TZ    NULLABLE            Payment date
stripe_invoice_id       VARCHAR(255)    NULLABLE            Stripe invoice ID
metadata                JSONB           NOT NULL, def:{}    Invoice metadata
created_at              TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at              TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Constraints:**
- UNIQUE(invoice_number)

**Foreign Keys:**
- `subscription_id` → subscriptions.id (SET NULL)

**Indexes:**
- `ix_invoices_user_id` - for user invoices
- `ix_invoices_subscription_id` - for subscription invoices
- `ix_invoices_status` - for status filtering
- `ix_invoices_invoice_number` - UNIQUE, for invoice lookup
- `ix_invoices_stripe_invoice_id` - for Stripe integration
- `ix_invoices_issued_date` - for date filtering
- `ix_invoices_due_date` - for overdue detection
- `ix_invoices_created_at` - for sorting

---

### 25. analytics_metrics (Migration 008)

**Purpose:** General analytics metrics for dashboards

**Table Structure:**
```
Column             Type            Constraints         Description
id                 UUID            PK                  Metric record ID
metric_name        VARCHAR(100)    NOT NULL            Metric name
metric_value       FLOAT           NULLABLE            Metric value
dimension_type     VARCHAR(50)     NULLABLE            Dimension type
dimension_value    VARCHAR(255)    NULLABLE            Dimension value
period             VARCHAR(20)     NULLABLE            Period (daily, weekly, monthly)
period_start       TIMESTAMP TZ    NULLABLE            Period start
period_end         TIMESTAMP TZ    NULLABLE            Period end
tags               ARRAY(VARCHAR)  NULLABLE            Tags
metadata           JSONB           NOT NULL, def:{}    Metadata
created_at         TIMESTAMP TZ    NOT NULL, server    Creation timestamp
```

**Indexes:**
- `ix_analytics_metrics_metric_name` - for metric filtering
- `ix_analytics_metrics_dimension_type` - for dimension filtering
- `ix_analytics_metrics_dimension_value` - for value filtering
- `ix_analytics_metrics_period` - for period filtering
- `ix_analytics_metrics_period_start` - for date range queries
- `ix_analytics_metrics_created_at` - for sorting

---

### 26. document_chunks (Migration 008)

**Purpose:** Document chunks for RAG and semantic search

**Table Structure:**
```
Column              Type            Constraints         Description
id                  UUID            PK                  Chunk record ID
document_id         UUID            FK(knowledge_base), NULLABLE Reference to document
project_id          UUID            FK(projects), NULLABLE Reference to project
chunk_index         INTEGER         NOT NULL            Chunk sequence number
content             TEXT            NOT NULL            Chunk content
chunk_type          VARCHAR(50)     NULLABLE            Type (paragraph, code_block, etc.)
source_section      VARCHAR(255)    NULLABLE            Source section/heading
tokens_count        INTEGER         NULLABLE            Token count
embedding_id        VARCHAR(255)    NULLABLE            Vector DB embedding ID
has_embedding       BOOLEAN         NOT NULL, def:false Embedding generation flag
relevance_score     FLOAT           NULLABLE            Relevance score (0-1)
search_count        INTEGER         NOT NULL, def:0     Search result count
metadata            JSONB           NOT NULL, def:{}    Chunk metadata
created_at          TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at          TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `document_id` → knowledge_base_documents.id (CASCADE DELETE)
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_document_chunks_document_id` - for document chunks
- `ix_document_chunks_project_id` - for project chunks
- `ix_document_chunks_chunk_type` - for type filtering
- `ix_document_chunks_has_embedding` - for embedding queries
- `ix_document_chunks_search_count` - for relevance sorting
- `ix_document_chunks_created_at` - for sorting

---

### 27. notification_preferences (Migration 008)

**Purpose:** User notification settings and preferences

**Table Structure:**
```
Column                Type            Constraints         Description
id                    UUID            PK                  Preference record ID
user_id               UUID            NOT NULL            User ID (cross-db ref)
notification_type     VARCHAR(100)    NOT NULL            Type (project_update, team_invitation, etc.)
email_enabled         BOOLEAN         NOT NULL, def:true  Email notifications flag
in_app_enabled        BOOLEAN         NOT NULL, def:true  In-app notifications flag
slack_enabled         BOOLEAN         NOT NULL, def:false Slack notifications flag
frequency             VARCHAR(50)     NOT NULL, def:immediate Frequency (immediate, daily, weekly, off)
quiet_hours_enabled   BOOLEAN         NOT NULL, def:false Quiet hours flag
quiet_hours_start     VARCHAR(5)      NULLABLE            Start time (HH:MM)
quiet_hours_end       VARCHAR(5)      NULLABLE            End time (HH:MM)
metadata              JSONB           NOT NULL, def:{}    Additional settings
created_at            TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at            TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Constraints:**
- UNIQUE(user_id, notification_type)

**Indexes:**
- `ix_notification_preferences_user_id` - for user preferences
- `ix_notification_preferences_notification_type` - for type lookup
- `ix_notification_preferences_email_enabled` - for email filtering
- `ix_notification_preferences_in_app_enabled` - for in-app filtering
- `ix_notification_preferences_created_at` - for sorting

---

### 28. activity_logs (Migration 009)

**Purpose:** Audit trail for all system activities

**Table Structure:**
```
Column            Type            Constraints         Description
id                UUID            PK                  Log record ID
user_id           UUID            NOT NULL            Acting user ID (cross-db ref)
action            VARCHAR(100)    NOT NULL            Action (created, updated, deleted, shared, etc.)
resource_type     VARCHAR(100)    NOT NULL            Resource type (project, file, etc.)
resource_id       UUID            NOT NULL            Affected resource ID
resource_name     VARCHAR(255)    NULLABLE            Resource name for display
changes           JSONB           NULLABLE            Before/after values
description       TEXT            NULLABLE            Human-readable description
severity          VARCHAR(20)     NOT NULL, def:info  Severity (info, warning, error, critical)
ip_address        VARCHAR(45)     NULLABLE            Request IP address
user_agent        VARCHAR(500)    NULLABLE            Browser user agent
metadata          JSONB           NOT NULL, def:{}    Additional metadata
created_at        TIMESTAMP TZ    NOT NULL, server    Activity timestamp
```

**Indexes:**
- `ix_activity_logs_user_id` - for user activity
- `ix_activity_logs_action` - for action filtering
- `ix_activity_logs_resource_type` - for resource filtering
- `ix_activity_logs_resource_id` - for resource lookup
- `ix_activity_logs_resource` - COMPOSITE(resource_type, resource_id)
- `ix_activity_logs_severity` - for severity filtering
- `ix_activity_logs_created_at` - for time-based sorting

---

### 29. project_invitations (Migration 009)

**Purpose:** Project collaboration invitations

**Table Structure:**
```
Column             Type            Constraints         Description
id                 UUID            PK                  Invitation record ID
project_id         UUID            FK(projects), NOT NULL Reference to project
invited_user_id    UUID            NULLABLE            Invited user ID (cross-db ref)
invited_email      VARCHAR(255)    NULLABLE            Email if pre-signup
invited_by_id      UUID            NOT NULL            Inviter user ID (cross-db ref)
role               VARCHAR(50)     NOT NULL, def:member Offered role
permission_level   VARCHAR(50)     NULLABLE            Permission level (read, write, admin)
status             VARCHAR(20)     NOT NULL, def:pending Status (pending, accepted, declined, revoked)
invitation_token   VARCHAR(255)    NULLABLE            Email invite token
token_expires_at   TIMESTAMP TZ    NULLABLE            Token expiration
message            TEXT            NULLABLE            Custom message
responded_at       TIMESTAMP TZ    NULLABLE            Response timestamp
metadata           JSONB           NOT NULL, def:{}    Invitation metadata
created_at         TIMESTAMP TZ    NOT NULL, server    Creation timestamp
updated_at         TIMESTAMP TZ    NOT NULL, server    Update timestamp
```

**Foreign Keys:**
- `project_id` → projects.id (CASCADE DELETE)

**Indexes:**
- `ix_project_invitations_project_id` - for project invitations
- `ix_project_invitations_invited_user_id` - for user invitations
- `ix_project_invitations_invited_email` - for email lookups
- `ix_project_invitations_invited_by_id` - for inviter's invitations
- `ix_project_invitations_status` - for status filtering
- `ix_project_invitations_role` - for role filtering
- `ix_project_invitations_invitation_token` - for token validation
- `ix_project_invitations_created_at` - for sorting

---

## Cross-Database References

The following references span between databases:

### From socrates_specs to socrates_auth

| Table | Column(s) | References |
|---|---|---|
| projects | user_id | users.id |
| sessions | user_id | users.id |
| user_behavior_patterns | user_id | users.id |
| api_keys | user_id | users.id |
| llm_usage_tracking | user_id | users.id |
| subscriptions | user_id | users.id |
| invoices | user_id | users.id |
| notification_preferences | user_id | users.id |
| activity_logs | user_id | users.id |
| team_members | user_id, invited_by_id | users.id |
| teams | owner_id | users.id |
| project_shares | shared_with_user_id, shared_by_id | users.id |
| project_invitations | invited_user_id, invited_by_id | users.id |

**Note:** These are documented as UUIDs but NOT enforced with FK constraints due to multi-database architecture. Application code must validate referential integrity.

---

## Performance Optimization Guidelines

### Indexed Columns (Use These in WHERE Clauses)
- All primary keys and foreign keys
- All status/state columns
- All date/timestamp columns
- Frequently filtered fields (user_id, project_id, etc.)

### Composite Indexes
- `(resource_type, resource_id)` on activity_logs
- `(project_id, key, version)` on specifications
- `(team_id, user_id)` on team_members

### Query Examples

**Find user's projects:**
```sql
SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC;
-- Uses: ix_projects_user_id
```

**List active projects:**
```sql
SELECT * FROM projects WHERE status = 'active' ORDER BY updated_at DESC;
-- Uses: ix_projects_status
```

**Get user's sessions:**
```sql
SELECT * FROM sessions WHERE user_id = $1 AND status = 'active';
-- Uses: ix_sessions_user_id, ix_sessions_status
```

---

## Relationship Diagram

```
socrates_auth:
  users
    ├── refresh_tokens (1:Many, CASCADE)
    ├── admin_users (1:Many, CASCADE)
    └── admin_audit_logs (as admin_id, 1:Many, RESTRICT)

socrates_specs:
  projects
    ├── sessions (1:Many, CASCADE)
    ├── questions (1:Many, CASCADE)
    ├── specifications (1:Many, CASCADE)
    ├── conflicts (1:Many, CASCADE)
    ├── generated_projects (1:Many, CASCADE)
    ├── quality_metrics (1:Many, CASCADE)
    ├── project_shares (1:Many, CASCADE)
    ├── activity_logs (1:Many, CASCADE)
    ├── project_invitations (1:Many, CASCADE)
    └── document_chunks (1:Many, CASCADE)

  sessions
    ├── conversation_history (1:Many, CASCADE)
    └── questions (1:Many, SET NULL)

  teams
    └── team_members (1:Many, CASCADE)
    └── project_shares (1:Many, CASCADE)

  knowledge_base_documents
    └── document_chunks (1:Many, CASCADE)

  generated_projects
    └── generated_files (1:Many, CASCADE)

  subscriptions
    └── invoices (1:Many, SET NULL)
```

---

## Migration History

- **Migration 001 (AUTH):** Initial auth schema (users, refresh_tokens)
- **Migration 002 (AUTH):** Admin management (admin_roles, admin_users, admin_audit_logs)
- **Migration 003 (SPECS):** Core specification tables
- **Migration 004 (SPECS):** Generated content
- **Migration 005 (SPECS):** Tracking & analytics
- **Migration 006 (SPECS):** Collaboration & sharing
- **Migration 007 (SPECS):** API & LLM integration
- **Migration 008 (SPECS):** Analytics & search
- **Migration 009 (SPECS):** Activity & project management

---

## Best Practices

1. **Always use transactions** for multi-table operations
2. **Index before filtering** - check indexes before writing WHERE clauses
3. **Null handling** - many fields are nullable; handle in application code
4. **JSONB fields** - validate schema in application, not database
5. **Timestamps** - always use with timezone awareness
6. **Cross-DB references** - validate in application layer
7. **Soft deletes** - use status field for logical deletion where needed

---

**Last Updated:** November 11, 2025
**Maintained By:** Socrates2 Team

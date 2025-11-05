# DATABASE SCHEMA - COMPLETE

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟡 MEDIUM - Must complete before Phase 2 implementation

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Two-Database Architecture](#two-database-architecture)
3. [Phase 0-2 Tables (MVP)](#phase-0-2-tables-mvp)
4. [Phase 3 Tables (Multi-LLM)](#phase-3-tables-multi-llm)
5. [Phase 4 Tables (Code Generation)](#phase-4-tables-code-generation)
6. [Phase 5 Tables (User Learning)](#phase-5-tables-user-learning)
7. [Phase 6 Tables (Team Collaboration)](#phase-6-tables-team-collaboration)
8. [Indexes](#indexes)
9. [Migration Strategy](#migration-strategy)
10. [Schema Diagrams](#schema-diagrams)

---

## OVERVIEW

This document defines the COMPLETE database schema for Socrates2, including:
- ✅ **Phase 0-2 (MVP)**: Tables implemented immediately
- 📋 **Phase 3-6 (Future)**: Tables documented now, implemented later

### Why Document Future Schemas Now?

1. **Prevents Breaking Changes**: Know what's coming, design MVP schema to accommodate
2. **Prevents Refactoring**: Add new tables, don't modify existing ones
3. **Clear Vision**: Team understands full system architecture
4. **Migration Planning**: Know what migrations will be needed

---

## TWO-DATABASE ARCHITECTURE

### Database 1: socrates_auth

**Purpose:** User authentication, authorization, security
**Size:** Small (~10-50 MB)
**Access:** Restrictive
**Backup:** Frequent (daily)

**Tables:**
- users
- refresh_tokens
- password_reset_requests
- audit_logs
- user_rules (Phase 1)
- api_keys (Phase 3)
- teams (Phase 6)
- team_members (Phase 6)
- team_invitations (Phase 6)

---

### Database 2: socrates_specs

**Purpose:** Projects, specifications, conversations, all project data
**Size:** Large (~100 MB - 10 GB+)
**Access:** More permissive
**Backup:** Frequent (hourly incremental)

**Tables:**
- projects
- sessions
- specifications
- conversation_history
- questions
- conflicts
- quality_metrics
- maturity_tracking
- test_results (Phase 2)
- llm_usage_tracking (Phase 3)
- generated_projects (Phase 4)
- generated_files (Phase 4)
- user_behavior_patterns (Phase 5)
- question_effectiveness (Phase 5)
- knowledge_base_documents (Phase 5)
- project_shares (Phase 6)

---

## PHASE 0-2 TABLES (MVP)

### socrates_auth Database

#### Table: users

```sql
-- User accounts for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,

    -- Indexes
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_email_lowercase CHECK (email = LOWER(email))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;

COMMENT ON TABLE users IS 'User accounts for authentication';
COMMENT ON COLUMN users.id IS 'Unique user identifier (UUID)';
COMMENT ON COLUMN users.email IS 'User email address (unique, lowercase)';
COMMENT ON COLUMN users.password_hash IS 'Hashed password (bcrypt)';
COMMENT ON COLUMN users.is_active IS 'Account active status';
COMMENT ON COLUMN users.is_verified IS 'Email verification status';
```

#### Table: refresh_tokens

```sql
-- Refresh tokens for JWT authentication
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,  -- Matches JWT "jti" claim
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT false,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT refresh_tokens_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_revoked ON refresh_tokens(revoked) WHERE revoked = false;

COMMENT ON TABLE refresh_tokens IS 'Refresh tokens for JWT authentication';
COMMENT ON COLUMN refresh_tokens.id IS 'Token ID (matches JWT jti claim)';
COMMENT ON COLUMN refresh_tokens.revoked IS 'Token revocation status';
```

#### Table: password_reset_requests

```sql
-- Password reset requests
CREATE TABLE password_reset_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN NOT NULL DEFAULT false,
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT password_reset_requests_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_password_reset_requests_token ON password_reset_requests(token);
CREATE INDEX idx_password_reset_requests_expires_at ON password_reset_requests(expires_at);
CREATE INDEX idx_password_reset_requests_used ON password_reset_requests(used) WHERE used = false;

COMMENT ON TABLE password_reset_requests IS 'Password reset requests (single-use tokens)';
```

#### Table: audit_logs

```sql
-- Security audit logs
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT audit_logs_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

COMMENT ON TABLE audit_logs IS 'Security audit logs (login, logout, password changes, etc.)';
COMMENT ON COLUMN audit_logs.action IS 'Action performed (e.g., user.login, user.logout)';
```

#### Table: user_rules (Phase 1)

```sql
-- User-defined rules for Quality Control
CREATE TABLE user_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rules JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT user_rules_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT user_rules_user_unique UNIQUE (user_id)
);

CREATE INDEX idx_user_rules_user_id ON user_rules(user_id);

COMMENT ON TABLE user_rules IS 'User-defined rules for Quality Control system';
COMMENT ON COLUMN user_rules.rules IS 'Rules as JSON (e.g., {"prefer_postgres": true})';

-- Example rules structure:
-- {
--   "never_assume": true,
--   "always_check": true,
--   "prefer_postgres": true,
--   "min_test_coverage": 0.8,
--   "communication_style": "technical"
-- }
```

---

### socrates_specs Database

#### Table: projects

```sql
-- User projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- References users(id) in socrates_auth
    name VARCHAR(255) NOT NULL,
    description TEXT,
    current_phase VARCHAR(50) NOT NULL DEFAULT 'discovery',
    maturity_score INTEGER NOT NULL DEFAULT 0,  -- 0-100
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMP,

    CONSTRAINT projects_maturity_range CHECK (maturity_score >= 0 AND maturity_score <= 100),
    CONSTRAINT projects_phase_valid CHECK (
        current_phase IN ('discovery', 'analysis', 'design', 'implementation')
    )
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_projects_archived_at ON projects(archived_at) WHERE archived_at IS NULL;
CREATE INDEX idx_projects_current_phase ON projects(current_phase);

COMMENT ON TABLE projects IS 'User projects';
COMMENT ON COLUMN projects.current_phase IS 'Current workflow phase (discovery/analysis/design/implementation)';
COMMENT ON COLUMN projects.maturity_score IS 'Overall maturity score (0-100)';
```

#### Table: sessions

```sql
-- Chat sessions within projects
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    mode VARCHAR(50) NOT NULL DEFAULT 'socratic',  -- socratic or direct_chat
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,

    CONSTRAINT sessions_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT sessions_mode_valid CHECK (mode IN ('socratic', 'direct_chat'))
);

CREATE INDEX idx_sessions_project_id ON sessions(project_id);
CREATE INDEX idx_sessions_started_at ON sessions(started_at DESC);

COMMENT ON TABLE sessions IS 'Chat sessions within projects';
COMMENT ON COLUMN sessions.mode IS 'Chat mode (socratic questioning or direct chat)';
```

#### Table: specifications

```sql
-- Extracted specifications from conversations
CREATE TABLE specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,  -- user_input, extracted, inferred
    confidence DECIMAL(3,2),  -- 0.00-1.00
    is_current BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    superseded_at TIMESTAMP,
    superseded_by UUID REFERENCES specifications(id) ON DELETE SET NULL,

    CONSTRAINT specifications_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT specifications_session_fk FOREIGN KEY (session_id)
        REFERENCES sessions(id) ON DELETE SET NULL,
    CONSTRAINT specifications_confidence_range CHECK (
        confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
    )
);

CREATE INDEX idx_specifications_project_id ON specifications(project_id);
CREATE INDEX idx_specifications_category ON specifications(category);
CREATE INDEX idx_specifications_is_current ON specifications(is_current) WHERE is_current = true;
CREATE INDEX idx_specifications_created_at ON specifications(created_at DESC);

COMMENT ON TABLE specifications IS 'Extracted specifications from conversations';
COMMENT ON COLUMN specifications.confidence IS 'Confidence score (0.00-1.00) for extracted specs';
COMMENT ON COLUMN specifications.is_current IS 'Current version flag (superseded specs have false)';
```

#### Table: conversation_history

```sql
-- Complete conversation history
CREATE TABLE conversation_history (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT conversation_history_session_fk FOREIGN KEY (session_id)
        REFERENCES sessions(id) ON DELETE CASCADE,
    CONSTRAINT conversation_history_role_valid CHECK (
        role IN ('user', 'assistant', 'system')
    )
);

CREATE INDEX idx_conversation_history_session_id ON conversation_history(session_id);
CREATE INDEX idx_conversation_history_timestamp ON conversation_history(timestamp);

COMMENT ON TABLE conversation_history IS 'Complete conversation history for all sessions';
COMMENT ON COLUMN conversation_history.role IS 'Message role (user/assistant/system)';
```

#### Table: questions

```sql
-- Questions asked by Socratic counselor
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    session_id UUID NOT NULL,
    text TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- goals, requirements, tech_stack, scalability, security, performance, testing, monitoring, data_retention, disaster_recovery
    context TEXT,  -- Why this question matters
    quality_score DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT questions_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT questions_session_fk FOREIGN KEY (session_id)
        REFERENCES sessions(id) ON DELETE CASCADE,
    CONSTRAINT questions_quality_score_valid CHECK (
        quality_score >= 0.00 AND quality_score <= 1.00
    )
);

CREATE INDEX idx_questions_project_id ON questions(project_id);
CREATE INDEX idx_questions_session_id ON questions(session_id);
CREATE INDEX idx_questions_category ON questions(category);
CREATE INDEX idx_questions_created_at ON questions(created_at);

COMMENT ON TABLE questions IS 'Questions generated by SocraticCounselorAgent';
COMMENT ON COLUMN questions.category IS 'Question category matching specification categories';
COMMENT ON COLUMN questions.context IS 'Explanation of why this question is important';
COMMENT ON COLUMN questions.quality_score IS 'Quality score from QualityControllerAgent (0.00-1.00)';
```

#### Table: conflicts

```sql
-- Detected conflicts in specifications
CREATE TABLE conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- technology, requirement, timeline, resource
    description TEXT NOT NULL,
    spec_ids UUID[] NOT NULL,  -- Array of conflicting specification IDs
    severity VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- open, resolved, ignored
    resolution TEXT,
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by_user BOOLEAN DEFAULT false,

    CONSTRAINT conflicts_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT conflicts_type_valid CHECK (
        type IN ('technology', 'requirement', 'timeline', 'resource')
    ),
    CONSTRAINT conflicts_severity_valid CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT conflicts_status_valid CHECK (
        status IN ('open', 'resolved', 'ignored')
    )
);

CREATE INDEX idx_conflicts_project_id ON conflicts(project_id);
CREATE INDEX idx_conflicts_status ON conflicts(status) WHERE status = 'open';
CREATE INDEX idx_conflicts_severity ON conflicts(severity);
CREATE INDEX idx_conflicts_detected_at ON conflicts(detected_at DESC);

COMMENT ON TABLE conflicts IS 'Detected conflicts in specifications';
COMMENT ON COLUMN conflicts.spec_ids IS 'Array of conflicting specification IDs';
COMMENT ON COLUMN conflicts.resolution IS 'How conflict was resolved (user decision)';
```

#### Table: quality_metrics

```sql
-- Quality Control metrics and decisions
CREATE TABLE quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    threshold DECIMAL(10,2),
    passed BOOLEAN NOT NULL,
    details JSONB,
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT quality_metrics_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_quality_metrics_project_id ON quality_metrics(project_id);
CREATE INDEX idx_quality_metrics_type ON quality_metrics(metric_type);
CREATE INDEX idx_quality_metrics_calculated_at ON quality_metrics(calculated_at DESC);

COMMENT ON TABLE quality_metrics IS 'Quality Control metrics and validation results';
COMMENT ON COLUMN quality_metrics.metric_type IS 'Type of metric (e.g., maturity, coverage, conflicts)';
```

#### Table: maturity_tracking

```sql
-- Maturity tracking per category
CREATE TABLE maturity_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    score INTEGER NOT NULL,  -- 0-100
    details JSONB,
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT maturity_tracking_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT maturity_tracking_score_range CHECK (score >= 0 AND score <= 100)
);

CREATE INDEX idx_maturity_tracking_project_id ON maturity_tracking(project_id);
CREATE INDEX idx_maturity_tracking_category ON maturity_tracking(category);
CREATE INDEX idx_maturity_tracking_calculated_at ON maturity_tracking(calculated_at DESC);

COMMENT ON TABLE maturity_tracking IS 'Maturity tracking per category (12 categories)';
COMMENT ON COLUMN maturity_tracking.category IS 'Maturity category (e.g., requirements, goals, tech_stack)';
```

#### Table: test_results (Phase 2)

```sql
-- Real-time compatibility testing results
CREATE TABLE test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    test_type VARCHAR(50) NOT NULL,  -- compatibility, integration, unit
    technology_stack JSONB NOT NULL,
    test_status VARCHAR(20) NOT NULL,  -- pending, running, passed, failed
    results JSONB,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    CONSTRAINT test_results_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT test_results_status_valid CHECK (
        test_status IN ('pending', 'running', 'passed', 'failed')
    )
);

CREATE INDEX idx_test_results_project_id ON test_results(project_id);
CREATE INDEX idx_test_results_status ON test_results(test_status);
CREATE INDEX idx_test_results_started_at ON test_results(started_at DESC);

COMMENT ON TABLE test_results IS 'Real-time compatibility testing results (Design phase)';
COMMENT ON COLUMN test_results.technology_stack IS 'Technologies tested (e.g., {"python": "3.12", "postgres": "15"})';
```

---

## PHASE 3 TABLES (MULTI-LLM)

### socrates_auth Database

#### Table: api_keys (Phase 3)

```sql
-- LLM API keys per user
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- claude, openai, gemini, ollama
    api_key_encrypted TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP,

    CONSTRAINT api_keys_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT api_keys_provider_valid CHECK (
        provider IN ('claude', 'openai', 'gemini', 'ollama', 'other')
    ),
    CONSTRAINT api_keys_user_provider_unique UNIQUE (user_id, provider)
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_provider ON api_keys(provider);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active) WHERE is_active = true;

COMMENT ON TABLE api_keys IS 'LLM API keys per user (Phase 3: Multi-LLM support)';
COMMENT ON COLUMN api_keys.api_key_encrypted IS 'Encrypted API key (AES-256)';
```

---

### socrates_specs Database

#### Table: llm_usage_tracking (Phase 3)

```sql
-- LLM API usage tracking
CREATE TABLE llm_usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,  -- References users(id) in socrates_auth
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    cost_usd DECIMAL(10,6),
    latency_ms INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT llm_usage_tracking_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE SET NULL,
    CONSTRAINT llm_usage_tracking_session_fk FOREIGN KEY (session_id)
        REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX idx_llm_usage_tracking_user_id ON llm_usage_tracking(user_id);
CREATE INDEX idx_llm_usage_tracking_project_id ON llm_usage_tracking(project_id);
CREATE INDEX idx_llm_usage_tracking_provider ON llm_usage_tracking(provider);
CREATE INDEX idx_llm_usage_tracking_timestamp ON llm_usage_tracking(timestamp DESC);

COMMENT ON TABLE llm_usage_tracking IS 'LLM API usage tracking for cost monitoring (Phase 3)';
COMMENT ON COLUMN llm_usage_tracking.cost_usd IS 'Estimated cost in USD';
```

---

## PHASE 4 TABLES (CODE GENERATION)

### socrates_specs Database

#### Table: generated_projects (Phase 4)

```sql
-- Generated project metadata
CREATE TABLE generated_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    generation_version INTEGER NOT NULL DEFAULT 1,
    total_files INTEGER NOT NULL,
    total_lines INTEGER NOT NULL,
    test_coverage DECIMAL(5,2),
    quality_score INTEGER,
    traceability_score INTEGER,  -- % of specs implemented
    download_url TEXT,
    generation_started_at TIMESTAMP NOT NULL,
    generation_completed_at TIMESTAMP,
    generation_status VARCHAR(20) NOT NULL,  -- pending, in_progress, completed, failed
    error_message TEXT,

    CONSTRAINT generated_projects_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT generated_projects_status_valid CHECK (
        generation_status IN ('pending', 'in_progress', 'completed', 'failed')
    ),
    CONSTRAINT generated_projects_version_unique UNIQUE (project_id, generation_version)
);

CREATE INDEX idx_generated_projects_project_id ON generated_projects(project_id);
CREATE INDEX idx_generated_projects_status ON generated_projects(generation_status);
CREATE INDEX idx_generated_projects_completed_at ON generated_projects(generation_completed_at DESC);

COMMENT ON TABLE generated_projects IS 'Generated project metadata (Phase 4: Project Generation)';
COMMENT ON COLUMN generated_projects.generation_version IS 'Generation version (incremental if re-generated)';
```

#### Table: generated_files (Phase 4)

```sql
-- Individual generated files
CREATE TABLE generated_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_project_id UUID NOT NULL REFERENCES generated_projects(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_content TEXT,
    file_size INTEGER,
    spec_ids UUID[],  -- Specifications that led to this file
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT generated_files_project_fk FOREIGN KEY (generated_project_id)
        REFERENCES generated_projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_generated_files_project_id ON generated_files(generated_project_id);
CREATE INDEX idx_generated_files_file_path ON generated_files(file_path);

COMMENT ON TABLE generated_files IS 'Individual generated files (Phase 4)';
COMMENT ON COLUMN generated_files.spec_ids IS 'Specifications that led to this file (traceability)';
```

---

## PHASE 5 TABLES (USER LEARNING)

### socrates_specs Database

#### Table: user_behavior_patterns (Phase 5)

```sql
-- Learned user behavior patterns
CREATE TABLE user_behavior_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- References users(id) in socrates_auth
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,  -- 0.00-1.00
    learned_from_projects UUID[],
    learned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT user_behavior_patterns_confidence_range CHECK (
        confidence >= 0 AND confidence <= 1
    )
);

CREATE INDEX idx_user_behavior_patterns_user_id ON user_behavior_patterns(user_id);
CREATE INDEX idx_user_behavior_patterns_type ON user_behavior_patterns(pattern_type);
CREATE INDEX idx_user_behavior_patterns_confidence ON user_behavior_patterns(confidence DESC);

COMMENT ON TABLE user_behavior_patterns IS 'Learned user behavior patterns (Phase 5: User Learning)';
COMMENT ON COLUMN user_behavior_patterns.pattern_type IS 'Pattern type (e.g., communication_style, detail_level)';

-- Example pattern_data:
-- {
--   "communication_style": "technical",
--   "preferred_detail_level": "comprehensive",
--   "response_length_preference": "detailed",
--   "technical_expertise": 0.85
-- }
```

#### Table: question_effectiveness (Phase 5)

```sql
-- Question effectiveness tracking
CREATE TABLE question_effectiveness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- References users(id) in socrates_auth
    question_template_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    times_asked INTEGER NOT NULL DEFAULT 0,
    times_answered_well INTEGER NOT NULL DEFAULT 0,
    average_answer_length INTEGER,
    average_spec_extraction_count DECIMAL(5,2),
    effectiveness_score DECIMAL(3,2),  -- 0.00-1.00
    last_asked_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT question_effectiveness_score_range CHECK (
        effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)
    ),
    CONSTRAINT question_effectiveness_unique UNIQUE (user_id, question_template_id)
);

CREATE INDEX idx_question_effectiveness_user_id ON question_effectiveness(user_id);
CREATE INDEX idx_question_effectiveness_role ON question_effectiveness(role);
CREATE INDEX idx_question_effectiveness_score ON question_effectiveness(effectiveness_score DESC);

COMMENT ON TABLE question_effectiveness IS 'Question effectiveness tracking per user (Phase 5)';
COMMENT ON COLUMN question_effectiveness.effectiveness_score IS 'How effective question is for this user (0.00-1.00)';
```

#### Table: knowledge_base_documents (Phase 5)

```sql
-- Knowledge base documents (uploaded by users)
CREATE TABLE knowledge_base_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,  -- References users(id) in socrates_auth
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    content TEXT,
    embedding vector(384),  -- Sentence embedding for semantic search
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT knowledge_base_documents_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_knowledge_base_documents_project_id ON knowledge_base_documents(project_id);
CREATE INDEX idx_knowledge_base_documents_user_id ON knowledge_base_documents(user_id);
CREATE INDEX idx_knowledge_base_documents_uploaded_at ON knowledge_base_documents(uploaded_at DESC);

-- Vector similarity index (for semantic search)
-- CREATE INDEX idx_knowledge_base_documents_embedding
--     ON knowledge_base_documents USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);

COMMENT ON TABLE knowledge_base_documents IS 'Knowledge base documents per project (Phase 5)';
COMMENT ON COLUMN knowledge_base_documents.embedding IS 'Sentence embedding for semantic search (384 dimensions)';
```

---

## PHASE 6 TABLES (TEAM COLLABORATION)

### socrates_auth Database

#### Table: teams (Phase 6)

```sql
-- Teams for collaborative projects
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT teams_created_by_fk FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_teams_created_by ON teams(created_by);
CREATE INDEX idx_teams_created_at ON teams(created_at DESC);

COMMENT ON TABLE teams IS 'Teams for collaborative projects (Phase 6: Team Collaboration)';
```

#### Table: team_members (Phase 6)

```sql
-- Team membership
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- owner, lead, developer, viewer
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT team_members_team_fk FOREIGN KEY (team_id)
        REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT team_members_user_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT team_members_role_valid CHECK (
        role IN ('owner', 'lead', 'developer', 'viewer')
    ),
    CONSTRAINT team_members_unique UNIQUE (team_id, user_id)
);

CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_role ON team_members(role);

COMMENT ON TABLE team_members IS 'Team membership with roles (Phase 6)';
COMMENT ON COLUMN team_members.role IS 'Member role (owner/lead/developer/viewer)';
```

#### Table: team_invitations (Phase 6)

```sql
-- Team invitations
CREATE TABLE team_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invited_email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    accepted BOOLEAN NOT NULL DEFAULT false,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT team_invitations_team_fk FOREIGN KEY (team_id)
        REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT team_invitations_invited_by_fk FOREIGN KEY (invited_by)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT team_invitations_role_valid CHECK (
        role IN ('lead', 'developer', 'viewer')
    )
);

CREATE INDEX idx_team_invitations_team_id ON team_invitations(team_id);
CREATE INDEX idx_team_invitations_token ON team_invitations(token);
CREATE INDEX idx_team_invitations_accepted ON team_invitations(accepted) WHERE accepted = false;

COMMENT ON TABLE team_invitations IS 'Team invitations (Phase 6)';
```

---

### socrates_specs Database

#### Table: project_shares (Phase 6)

```sql
-- Project sharing with teams
CREATE TABLE project_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    team_id UUID NOT NULL,  -- References teams(id) in socrates_auth
    shared_by UUID NOT NULL,  -- References users(id) in socrates_auth
    permission_level VARCHAR(20) NOT NULL,  -- read, write, admin
    shared_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT project_shares_project_fk FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT project_shares_permission_valid CHECK (
        permission_level IN ('read', 'write', 'admin')
    ),
    CONSTRAINT project_shares_unique UNIQUE (project_id, team_id)
);

CREATE INDEX idx_project_shares_project_id ON project_shares(project_id);
CREATE INDEX idx_project_shares_team_id ON project_shares(team_id);
CREATE INDEX idx_project_shares_permission ON project_shares(permission_level);

COMMENT ON TABLE project_shares IS 'Project sharing with teams (Phase 6)';
```

---

## INDEXES

### Summary of All Indexes

**Phase 0-2 (MVP): 58 indexes**
- users: 4 indexes
- refresh_tokens: 3 indexes
- password_reset_requests: 3 indexes
- audit_logs: 4 indexes
- user_rules: 1 index
- projects: 4 indexes
- sessions: 2 indexes
- specifications: 4 indexes
- conversation_history: 2 indexes
- conflicts: 4 indexes
- quality_metrics: 3 indexes
- maturity_tracking: 3 indexes
- test_results: 3 indexes

**Phase 3-6 (Future): 27 indexes**
- api_keys: 3 indexes
- llm_usage_tracking: 4 indexes
- generated_projects: 3 indexes
- generated_files: 2 indexes
- user_behavior_patterns: 3 indexes
- question_effectiveness: 3 indexes
- knowledge_base_documents: 4 indexes (including vector index)
- teams: 2 indexes
- team_members: 3 indexes
- team_invitations: 3 indexes
- project_shares: 3 indexes

**Total: 85 indexes**

---

## MIGRATION STRATEGY

### Phase 0-2 (MVP) Migrations

```bash
# Migration 001: Create socrates_auth tables (Phase 0)
alembic revision --autogenerate -m "Create auth tables: users, refresh_tokens, password_reset_requests, audit_logs"

# Migration 002: Create socrates_specs tables (Phase 0)
alembic revision --autogenerate -m "Create specs tables: projects, sessions, specifications, conversation_history"

# Migration 003: Create conflict & quality tables (Phase 1)
alembic revision --autogenerate -m "Create conflict detection and quality control tables"

# Migration 004: Add user_rules table (Phase 1)
alembic revision --autogenerate -m "Add user_rules table for Quality Control"

# Migration 005: Add test_results table (Phase 2)
alembic revision --autogenerate -m "Add test_results table for compatibility testing"
```

### Phase 3 Migrations (Multi-LLM)

```bash
# Migration 006: Add api_keys table (Phase 3)
alembic revision --autogenerate -m "Add api_keys table for multi-LLM support"

# Migration 007: Add llm_usage_tracking table (Phase 3)
alembic revision --autogenerate -m "Add llm_usage_tracking table for cost monitoring"
```

### Phase 4 Migrations (Code Generation)

```bash
# Migration 008: Add project generation tables (Phase 4)
alembic revision --autogenerate -m "Add generated_projects and generated_files tables"
```

### Phase 5 Migrations (User Learning)

```bash
# Migration 009: Add user learning tables (Phase 5)
alembic revision --autogenerate -m "Add user_behavior_patterns and question_effectiveness tables"

# Migration 010: Add knowledge base table (Phase 5)
alembic revision --autogenerate -m "Add knowledge_base_documents table"

# Migration 011: Add pgvector extension (Phase 5)
alembic revision -m "Enable pgvector extension for semantic search"
# Content:
# op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

# Migration 012: Add vector embedding column (Phase 5)
alembic revision --autogenerate -m "Add embedding vector column to knowledge_base_documents"
```

### Phase 6 Migrations (Team Collaboration)

```bash
# Migration 013: Add team tables (Phase 6)
alembic revision --autogenerate -m "Add teams, team_members, team_invitations tables"

# Migration 014: Add project sharing (Phase 6)
alembic revision --autogenerate -m "Add project_shares table for team collaboration"
```

---

## SCHEMA DIAGRAMS

### MVP Schema (Phase 0-2)

```
socrates_auth Database:
┌──────────┐       ┌──────────────────┐
│  users   │──────<│ refresh_tokens   │
└──────────┘       └──────────────────┘
     │
     └────────────<│ password_reset_  │
                   │    requests      │
                   └──────────────────┘
     │
     └────────────<│ audit_logs       │
                   └──────────────────┘
     │
     └────────────<│ user_rules       │
                   └──────────────────┘

socrates_specs Database:
┌──────────┐       ┌──────────┐       ┌──────────────────┐
│ projects │──────<│ sessions │──────<│ conversation_    │
│          │       │          │       │    history       │
└──────────┘       └──────────┘       └──────────────────┘
     │                  │
     │                  └────────────<│ specifications   │
     │                                └──────────────────┘
     │
     └────────────<│ conflicts        │
     │             └──────────────────┘
     │
     └────────────<│ quality_metrics  │
     │             └──────────────────┘
     │
     └────────────<│ maturity_tracking│
     │             └──────────────────┘
     │
     └────────────<│ test_results     │
                   └──────────────────┘
```

---

## VERIFICATION CHECKLIST

Before Phase 0 implementation:

- [ ] Review all Phase 0-2 (MVP) table definitions
- [ ] Verify two-database architecture makes sense
- [ ] Verify foreign key relationships correct
- [ ] Verify all constraints make sense
- [ ] Verify indexes cover common queries
- [ ] Verify Phase 3-6 tables don't conflict with MVP
- [ ] Verify migration strategy is clear
- [ ] Approve schema or request changes

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This complete schema ensures MVP implementation is future-proof and Phase 3-6 additions are non-breaking.*

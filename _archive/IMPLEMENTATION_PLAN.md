# Complete Implementation Plan - All Phases

**Objective:** Make the CLI fully functional with the backend, add LLM selection, and enable IDE integration

**Status:** Starting implementation
**Total Scope:**
- SocratesAPI client methods (150+)
- LLM selection system
- IDE integration framework
- Full testing and verification

---

## Phase 1: API Client Implementation (SocratesAPI)

### Current State
- SocratesAPI class exists in Socrates.py
- Basic auth methods implemented (register, login, logout)
- Some project/session methods exist
- Missing ~130+ methods needed by CLI commands

### Tasks

#### 1.1 Authentication Methods ✓ (mostly done)
- [x] register
- [x] login
- [x] logout
- [ ] whoami (get current user info)
- [ ] change_password
- [ ] request_password_reset
- [ ] verify_email

#### 1.2 Project Management Methods
- [ ] create_project
- [ ] list_projects
- [ ] get_project
- [ ] update_project
- [ ] delete_project
- [ ] archive_project
- [ ] restore_project
- [ ] add_project_member
- [ ] remove_project_member
- [ ] list_project_members
- [ ] change_member_role
- [ ] share_project_with_team

#### 1.3 Session Methods
- [ ] start_session
- [ ] list_sessions
- [ ] get_session
- [ ] end_session
- [ ] select_session
- [ ] get_current_session

#### 1.4 Team Methods
- [ ] create_team
- [ ] list_teams
- [ ] get_team
- [ ] update_team
- [ ] delete_team
- [ ] invite_to_team
- [ ] add_team_member
- [ ] remove_team_member
- [ ] list_team_members
- [ ] change_team_member_role

#### 1.5 Specification Methods
- [ ] list_specifications
- [ ] create_specification
- [ ] get_specification
- [ ] update_specification
- [ ] delete_specification
- [ ] approve_specification
- [ ] implement_specification
- [ ] reject_specification

#### 1.6 Document Methods
- [ ] upload_document
- [ ] list_documents
- [ ] get_document
- [ ] delete_document
- [ ] semantic_search (documents)

#### 1.7 Domain & Template Methods
- [ ] list_domains
- [ ] get_domain
- [ ] get_templates
- [ ] get_template
- [ ] apply_template

#### 1.8 Code Generation Methods
- [ ] generate_code
- [ ] list_code_generations
- [ ] get_code_generation_status
- [ ] download_generated_code

#### 1.9 Question Methods
- [ ] list_domain_questions
- [ ] create_custom_question
- [ ] get_question
- [ ] submit_question_answer
- [ ] get_question_answer

#### 1.10 Workflow Methods
- [ ] list_workflows
- [ ] get_workflow
- [ ] start_workflow
- [ ] get_workflow_status

#### 1.11 Export Methods
- [ ] list_export_formats
- [ ] generate_export
- [ ] download_export
- [ ] schedule_export
- [ ] list_exports

#### 1.12 Admin Methods
- [ ] get_system_health
- [ ] get_system_stats
- [ ] list_all_users
- [ ] get_user_info
- [ ] change_user_role
- [ ] disable_user
- [ ] enable_user
- [ ] get_system_config
- [ ] set_system_config

#### 1.13 Analytics Methods
- [ ] get_analytics_dashboard
- [ ] get_project_analytics
- [ ] get_user_analytics
- [ ] export_analytics

#### 1.14 Quality Methods
- [ ] run_quality_checks
- [ ] get_quality_metrics
- [ ] get_quality_gates
- [ ] set_quality_gate
- [ ] enable_quality_gate
- [ ] disable_quality_gate
- [ ] generate_quality_report

#### 1.15 Notification Methods
- [ ] list_notifications
- [ ] get_notification_settings
- [ ] update_notification_setting
- [ ] mark_notification_read
- [ ] mark_all_notifications_read
- [ ] subscribe_to_notifications

#### 1.16 Conflict Methods
- [ ] detect_conflicts
- [ ] list_conflicts
- [ ] get_conflict
- [ ] resolve_conflict
- [ ] analyze_conflict_patterns

#### 1.17 Search Methods
- [ ] text_search
- [ ] semantic_search
- [ ] search_specifications
- [ ] advanced_search

#### 1.18 Insights Methods
- [ ] get_project_insights
- [ ] analyze_specification_gaps
- [ ] analyze_project_risks
- [ ] get_project_recommendations

#### 1.19 GitHub Methods
- [ ] get_github_connection_status
- [ ] connect_github
- [ ] import_from_github
- [ ] analyze_github_repo
- [ ] sync_with_github

#### 1.20 Collaboration Methods
- [ ] get_collaboration_status
- [ ] get_activity_log
- [ ] get_team_activity

---

## Phase 2: LLM Selection System

### Architecture
```
User selects LLM/Model
        ↓
/llm select <provider:model>
        ↓
Store in user config/database
        ↓
All LLM calls check selected model
        ↓
Route through appropriate provider
```

### Components

#### 2.1 Backend LLM Router
**File:** app/core/llm_router.py
- MultiLLMProvider class
- Provider registry (Anthropic, OpenAI, etc.)
- Model selection logic
- Request routing

#### 2.2 Database Schema
**File:** Alembic migration
- Add llm_provider column to User/Session table
- Add default_llm_model setting
- Store last used model

#### 2.3 API Endpoints
**File:** app/api/llm_endpoints.py
- GET /api/v1/llm/available-models
- GET /api/v1/llm/current-model
- POST /api/v1/llm/select-model
- GET /api/v1/llm/costs (show cost per model)
- GET /api/v1/llm/usage (show usage per model)

#### 2.4 CLI Commands
**File:** cli/commands/llm.py
- `/llm list` - Show available models
- `/llm current` - Show selected model
- `/llm select <model>` - Choose model
- `/llm usage` - Show LLM usage stats
- `/llm costs` - Show cost estimates

#### 2.5 Configuration
**File:** app/core/config.py
- Add LLM settings
- Support multiple API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
- Rate limits per model

---

## Phase 3: IDE Integration Framework

### Architecture
```
IDE (VS Code, PyCharm, etc.)
        ↓
IDE Extension/Plugin
        ↓
Calls CLI subprocess OR embeds library
        ↓
SocratesAPI HTTP client
        ↓
Backend FastAPI
```

### Components

#### 3.1 CLI as Library
**File:** socrates_cli_lib.py
- Expose CLI as Python library
- Can be imported in IDE extensions
- Methods: execute_command(), get_command_help(), etc.

#### 3.2 VS Code Extension Framework
**File:** ide_integration/vscode/
- package.json - Extension manifest
- src/extension.ts - Extension entry point
- src/socrates.ts - CLI wrapper
- Commands registered in VS Code

#### 3.3 PyCharm Plugin Framework
**File:** ide_integration/pycharm/
- plugin.xml - Plugin manifest
- src/com/socrates/SocratesAction.java
- IDE integration points

#### 3.4 Generic IDE Bridge
**File:** ide_integration/cli_bridge.py
- Expose REST server on localhost:8888
- IDE can call HTTP instead of subprocess
- WebSocket for real-time updates

---

## Phase 4: Testing & Verification

### 4.1 Unit Tests
- Test each API method in isolation
- Test CLI command parsing
- Test error handling

### 4.2 Integration Tests
- Test CLI ↔ Backend communication
- Test LLM selection routing
- Test auth token refresh

### 4.3 End-to-End Tests
- Register → Create Project → Session → Export
- Team workflow (invite → join → collaborate)
- Code generation workflow
- GitHub import workflow

### 4.4 Manual Testing
- Test all 112+ CLI commands
- Test IDE integration
- Test LLM switching
- Test error scenarios

---

## Implementation Order

### Week 1: API Client Methods
1. Map existing backend endpoints
2. Implement all missing SocratesAPI methods
3. Test basic API connectivity

### Week 2: LLM System
1. Create LLM router backend
2. Database migrations
3. API endpoints for LLM selection
4. CLI commands for LLM management

### Week 3: IDE Integration
1. Create CLI library wrapper
2. VS Code extension skeleton
3. PyCharm plugin skeleton
4. CLI bridge server

### Week 4: Testing & Polish
1. Comprehensive testing
2. Error handling refinement
3. Documentation
4. Release

---

## Success Criteria

### API Client
- [x] All 150+ methods implemented
- [ ] Each method tested
- [ ] Error handling complete
- [ ] Token refresh working

### LLM System
- [ ] Users can select LLM/model
- [ ] Selection persists
- [ ] Backend routes to correct provider
- [ ] Cost tracking works

### IDE Integration
- [ ] CLI can be called from IDE
- [ ] Commands executable from IDE
- [ ] Results displayed in IDE
- [ ] Real-time updates work

### Testing
- [ ] All 112+ CLI commands work
- [ ] All user journeys complete
- [ ] Error handling tested
- [ ] Performance acceptable

---

## Files to Create/Modify

### New API Methods (Socrates.py)
- Add ~130+ methods to SocratesAPI class
- Organize into logical groups
- Comprehensive docstrings

### New Backend Components
- app/core/llm_router.py
- app/api/llm_endpoints.py
- app/migrations/*/llm_model_selection.py

### New CLI Components
- cli/commands/llm.py
- socrates_cli_lib.py
- ide_integration/cli_bridge.py

### IDE Extensions
- ide_integration/vscode/*
- ide_integration/pycharm/*

### Tests
- tests/test_api_client.py
- tests/test_llm_router.py
- tests/test_cli_commands.py
- tests/test_ide_integration.py

---

## Current Status
- [x] CLI command modules created (21 modules)
- [x] SocratesAPI client skeleton exists
- [ ] API methods to implement
- [ ] LLM system to build
- [ ] IDE integration to create
- [ ] Tests to write

**Next:** Start Phase 1 - Implement all SocratesAPI methods

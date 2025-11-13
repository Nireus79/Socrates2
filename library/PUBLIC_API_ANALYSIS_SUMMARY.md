# PUBLIC API ANALYSIS FOR SOCRATES-AI LIBRARY

## CRITICAL MISSING EXPORTS (Not currently in public API)

### CORE INFRASTRUCTURE (MUST HAVE)
1. ServiceContainer - Central dependency injection container (core/dependencies.py)
   - Methods: get_database_auth(), get_database_specs(), get_logger(), get_config(), get_claude_client(), get_orchestrator(), get_nlu_service()

2. Settings & Config (core/config.py)
   - Settings class - Pydantic settings loader
   - get_settings() - Factory function
   - settings - Global instance

3. Database Sessions (core/database.py)
   - SessionLocalAuth, SessionLocalSpecs - Session factories
   - ScopedSessionAuth, ScopedSessionSpecs - Thread-safe sessions
   - get_db_auth(), get_db_specs() - Dependency injection helpers
   - Base - SQLAlchemy declarative base
   - engine_auth, engine_specs - Database engines

4. Security & JWT (core/security.py)
   - create_access_token() - Generate JWT tokens
   - decode_access_token() - Validate JWT tokens
   - get_current_user(), get_current_active_user(), get_current_admin_user() - Auth dependencies
   - create_refresh_token(), validate_refresh_token() - Refresh token management
   - oauth2_scheme - OAuth2 scheme for FastAPI

### PURE BUSINESS LOGIC ENGINES (Library-Ready, NO Database)
5. QuestionGenerator (core/question_engine.py)
   - Methods: calculate_coverage(), identify_gaps(), generate()
   - Constants: QUESTION_CATEGORIES, CATEGORY_TARGETS

6. ConflictDetectionEngine (core/conflict_engine.py)
   - Methods: detect_conflicts(), build_conflict_detection_prompt()
   - Enums: ConflictType (CONTRADICTION, INCONSISTENCY, DEPENDENCY, REDUNDANCY)
   - Enums: ConflictSeverity (LOW, MEDIUM, HIGH)

7. BiasDetectionEngine (core/quality_engine.py)
   - Methods: detect_bias_in_question(), analyze_coverage()
   - Bias types: solution_bias, technology_bias, leading_question

8. LearningEngine (core/learning_engine.py)
   - Methods: build_user_profile(), calculate_learning_metrics(), predict_difficulty()
   - Factory: create_learning_engine()

9. NLUService (core/nlu_service.py)
   - Methods: parse_intent(), handle_conversation()
   - Dataclass: Intent (is_operation, operation, params, response)
   - Factory: create_nlu_service()

### DATA MODELS (Plain Dataclasses - Database Independent)
10. ProjectData - Plain project data
11. SpecificationData - Plain specification data
12. QuestionData - Plain question data
13. ConflictData - Plain conflict data
14. BiasAnalysisResult - Bias analysis output
15. CoverageAnalysisResult - Coverage analysis output
16. MaturityScore - Maturity calculation output
17. UserBehaviorData - User learning profile

### CONVERSION FUNCTIONS (Bridge between DB and Plain Models)
18. project_db_to_data() - SQLAlchemy Project -> ProjectData
19. spec_db_to_data() - SQLAlchemy Specification -> SpecificationData
20. question_db_to_data() - SQLAlchemy Question -> QuestionData
21. conflict_db_to_data() - SQLAlchemy Conflict -> ConflictData
22. specs_db_to_data() - Batch convert specs
23. questions_db_to_data() - Batch convert questions
24. conflicts_db_to_data() - Batch convert conflicts
25. conversation_db_to_api_message() - ConversationHistory -> API format

### SUBSCRIPTION & USAGE MANAGEMENT
26. SubscriptionTier Enum - FREE, PRO, TEAM, ENTERPRISE
27. TIER_LIMITS Dict - Feature limits per tier
28. UsageLimitError Exception - When limits exceeded
29. UsageLimiter Class - Check user limits

### RATE LIMITING
30. RateLimiter Class - In-memory rate limiter
31. get_rate_limiter() - Get global instance
32. reset_rate_limiter() - Reset for testing

### ACTION LOGGING
33. ActionLogger Class - Centralized action logging
34. initialize_action_logger() - Initialize system
35. toggle_action_logging() - Enable/disable at runtime
36. log_auth(), log_project(), log_session(), log_specs() - Domain-specific loggers
37. log_agent(), log_llm(), log_question(), log_conflict() - More loggers
38. log_database(), log_error(), log_warning() - System loggers

### VALIDATORS
39. validate_email() - Email format validation

### DOMAIN BASE (Currently Partial)
40. SeverityLevel Enum - ERROR, WARNING, INFO (in backend.app.base but incomplete)
41. ConflictRule Dataclass - Domain rule definition
42. QualityIssue Dataclass - Quality issue structure
43. QualityAnalyzer Dataclass - Analyzer definition
44. ExportFormat Dataclass - Export format structure
45. Question Dataclass - Socratic question structure

### AGENT CONTEXT (Missing)
46. AgentContext Class - Agent execution context
47. ConversationContext Class - Conversation state management

---

## WHAT'S ALREADY AVAILABLE (Good News!)

✅ All 29+ SQLAlchemy models (User, Project, Specification, etc.)
✅ All 7 domain implementations (Programming, DataEngineering, Architecture, etc.)
✅ All 9 agent implementations (ProjectManager, SocraticCounselor, etc.)
✅ BaseDomain abstract class
✅ DomainRegistry and get_domain_registry()
✅ BaseAgent abstract class
✅ AgentOrchestrator and factories
✅ MultiLLMManager

---

## PRIORITY CLASSIFICATION

🔴 CRITICAL (MUST ADD - Foundation for library use):
- ServiceContainer, Settings, database sessions
- All JWT security functions
- All plain dataclasses and conversions
- NLUService and Intent

🟠 HIGH (Should add soon):
- Pure business logic engines (Question, Conflict, Bias, Learning)
- Subscription/usage management
- Rate limiting

🟡 MEDIUM (Nice to have):
- Action logging utilities
- Validators
- Agent context classes

---

## RECOMMENDED CREATION ORDER

1. First: Create socrates/__init__.py with CRITICAL exports
   - Focus on foundation (ServiceContainer, Settings, security)
   - All dataclasses
   - All pure engines

2. Second: Export subscription/usage management

3. Third: Export logging and rate limiting utilities

4. Fourth: Create comprehensive documentation with examples

---

## KEY INSIGHT

Most pure business logic engines (QuestionGenerator, ConflictDetectionEngine, BiasDetectionEngine, LearningEngine) have ZERO database dependencies - they're perfect candidates for extraction to a separate library that doesn't require database setup.

These could be published separately as `socrates-core` for users who just want the question generation and conflict detection logic without the full backend.


"""
Socrates Library - Public API

Re-exports core engines, services, and infrastructure from app.core for external use.
This provides a clean public interface for agents, libraries, and external code.

Internal: app.core.* (implementation)
Public: socrates.* (API)

Structure:
1. Core Infrastructure - Configuration, DI, Database
2. Security - Authentication, JWT, OAuth2
3. Pure Business Logic Engines - Question generation, conflict detection, etc.
4. Data Models - Plain dataclasses for business objects
5. Conversion Functions - Bridge between DB models and plain models
6. NLU Service - Natural language understanding for conversations
7. Constants & Enums - Available operations, conflict types, etc.
"""

__version__ = "0.2.0"

# ============================================================================
# Phase 1a: PURE LOGIC EXPORTS (No config or database required)
# ============================================================================
# These can be imported and used without any environment configuration

# ============================================================================
# 1. Pure Business Logic Engines (Database-independent)
# ============================================================================

from app.core.question_engine import (
    QuestionGenerator,
    QUESTION_CATEGORIES,
    CATEGORY_TARGETS,
    create_question_generator,
)

from app.core.conflict_engine import (
    ConflictDetectionEngine,
    ConflictType,
    ConflictSeverity,
    create_conflict_detection_engine,
)

from app.core.quality_engine import BiasDetectionEngine

from app.core.learning_engine import (
    LearningEngine,
    create_learning_engine,
)

# ============================================================================
# 2. Data Models (Plain Dataclasses - Database Independent)
# ============================================================================

from app.core.models import (
    ProjectData,
    SpecificationData,
    QuestionData,
    ConflictData,
    UserBehaviorData,
    BiasAnalysisResult,
    CoverageAnalysisResult,
    MaturityScore,
)

# ============================================================================
# 3. Conversion Functions (Bridge between DB models and plain models)
# ============================================================================

from app.core.models import (
    project_db_to_data,
    spec_db_to_data,
    question_db_to_data,
    conflict_db_to_data,
    specs_db_to_data,
    questions_db_to_data,
    conflicts_db_to_data,
)

# ============================================================================
# Phase 1b: INFRASTRUCTURE EXPORTS (Requires environment configuration)
# ============================================================================
# These require .env or environment variables to be configured before use:
# - DATABASE_URL_AUTH
# - DATABASE_URL_SPECS
# - SECRET_KEY
# - ANTHROPIC_API_KEY
#
# To use these, call setup_environment() or configure via environment variables first.
# See Phase 1b documentation for details.

# Configuration & Dependency Injection
from app.core.config import Settings, get_settings
from app.core.dependencies import ServiceContainer

# Database connections
from app.core.database import (
    engine_auth, engine_specs, SessionLocalAuth, SessionLocalSpecs,
    ScopedSessionAuth, ScopedSessionSpecs, Base, get_db_auth, get_db_specs,
    init_db, close_db_connections,
)

# Security & JWT
from app.core.security import (
    create_access_token, decode_access_token, create_refresh_token,
    validate_refresh_token, get_current_user, get_current_active_user,
    get_current_admin_user, oauth2_scheme,
)

# NLU Service
from app.core.nlu_service import NLUService, Intent, create_nlu_service

# ============================================================================
# Phase 2: ADVANCED FEATURES EXPORTS (Some require configuration)
# ============================================================================

# Subscription & Usage Management (requires settings)
# from app.core.subscription_tiers import SubscriptionTier, TIER_LIMITS
# from app.core.usage_limits import UsageLimitError, UsageLimiter

# Rate Limiting
# from app.core.rate_limiting import RateLimiter, get_rate_limiter

# Action Logging
# from app.core.action_logger import (
#     ActionLogger, initialize_action_logger, toggle_action_logging,
#     log_auth, log_project, log_session, log_specs, log_agent,
#     log_llm, log_question, log_conflict, log_database, log_error, log_warning,
# )

# Validators
# from app.core.validators import validate_email

# ============================================================================
# Phase 3: FRAMEWORK EXPORTS (Requires configuration)
# ============================================================================

# Domain Framework (requires configuration)
# from app.domains import (
#     ProgrammingDomain, DataEngineeringDomain, ArchitectureDomain,
#     TestingDomain, BusinessDomain, SecurityDomain, DevOpsDomain,
#     BaseDomain, DomainRegistry, get_domain_registry,
# )

# Agent Framework (requires configuration)
# from app.agents import (
#     ProjectManagerAgent, SocraticCounselorAgent, ContextAnalyzerAgent,
#     ConflictDetectorAgent, CodeGeneratorAgent, QualityControllerAgent,
#     ExportAgent, TeamCollaborationAgent, UserLearningAgent,
#     DirectChatAgent, GitHubIntegrationAgent, BaseAgent,
#     AgentOrchestrator, get_orchestrator, reset_orchestrator, MultiLLMManager,
# )

# Domain Base Models
# from app.base import (
#     SeverityLevel, Question, ExportFormat, ConflictRule, QualityAnalyzer, QualityIssue,
# )

# Database Models
# from app.models import (
#     User, RefreshToken, AdminRole, AdminUser, AdminAuditLog,
#     Project, Session, Question as QuestionModel, Specification,
#     ConversationHistory, Conflict, GeneratedProject, GeneratedFile,
#     QualityMetric, UserBehaviorPattern, QuestionEffectiveness,
#     KnowledgeBaseDocument, LLMUsageTracking, AnalyticsMetrics,
#     Team, TeamMember, ProjectShare, ProjectCollaborator,
#     ProjectInvitation, ProjectOwnershipHistory, APIKey, Subscription,
#     Invoice, DocumentChunk, NotificationPreferences, ActivityLog,
# )

# ============================================================================
# Public API - All Exports
# ============================================================================

__all__ = [
    "__version__",

    # ========== PHASE 1a: PURE LOGIC (No configuration required) ==========

    # Pure Business Logic Engines
    "QuestionGenerator",
    "QUESTION_CATEGORIES",
    "CATEGORY_TARGETS",
    "create_question_generator",

    "ConflictDetectionEngine",
    "ConflictType",
    "ConflictSeverity",
    "create_conflict_detection_engine",

    "BiasDetectionEngine",

    "LearningEngine",
    "create_learning_engine",

    # Data Models (Plain dataclasses)
    "ProjectData",
    "SpecificationData",
    "QuestionData",
    "ConflictData",
    "UserBehaviorData",
    "BiasAnalysisResult",
    "CoverageAnalysisResult",
    "MaturityScore",

    # Conversion Functions
    "project_db_to_data",
    "spec_db_to_data",
    "question_db_to_data",
    "conflict_db_to_data",
    "specs_db_to_data",
    "questions_db_to_data",
    "conflicts_db_to_data",

    # ========== PHASE 1b: INFRASTRUCTURE (Requires configuration) ==========

    # Configuration
    "Settings",
    "get_settings",
    "ServiceContainer",

    # Database
    "engine_auth",
    "engine_specs",
    "SessionLocalAuth",
    "SessionLocalSpecs",
    "ScopedSessionAuth",
    "ScopedSessionSpecs",
    "Base",
    "get_db_auth",
    "get_db_specs",
    "init_db",
    "close_db_connections",

    # Security
    "create_access_token",
    "decode_access_token",
    "create_refresh_token",
    "validate_refresh_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "oauth2_scheme",

    # NLU Service
    "NLUService",
    "Intent",
    "create_nlu_service",

    # ========== PHASE 2: ADVANCED FEATURES (Requires configuration - commented out) ==========
    # Uncomment and configure environment to use:
    # "SubscriptionTier", "TIER_LIMITS", "UsageLimitError", "UsageLimiter",
    # "RateLimiter", "get_rate_limiter",
    # "ActionLogger", "initialize_action_logger", "toggle_action_logging",
    # "log_auth", "log_project", "log_session", "log_specs", "log_agent",
    # "log_llm", "log_question", "log_conflict", "log_database", "log_error", "log_warning",
    # "validate_email",

    # ========== PHASE 3: FRAMEWORK (Requires configuration - commented out) ==========
    # Uncomment and configure environment to use:
    # "ProgrammingDomain", "DataEngineeringDomain", "ArchitectureDomain",
    # "TestingDomain", "BusinessDomain", "SecurityDomain", "DevOpsDomain",
    # "BaseDomain", "DomainRegistry", "get_domain_registry",
    # "ProjectManagerAgent", "SocraticCounselorAgent", "ContextAnalyzerAgent",
    # "ConflictDetectorAgent", "CodeGeneratorAgent", "QualityControllerAgent",
    # "ExportAgent", "TeamCollaborationAgent", "UserLearningAgent",
    # "DirectChatAgent", "GitHubIntegrationAgent", "BaseAgent", "AgentOrchestrator",
    # "get_orchestrator", "reset_orchestrator", "MultiLLMManager",
    # "SeverityLevel", "Question", "ExportFormat", "ConflictRule",
    # "QualityAnalyzer", "QualityIssue",
    # [All database models...]
]

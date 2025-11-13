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
# Phase 2: ADVANCED FEATURES EXPORTS (Requires configuration)
# ============================================================================

# Subscription & Usage Management
from app.core.subscription_tiers import SubscriptionTier, TIER_LIMITS
from app.core.usage_limits import UsageLimitError, UsageLimiter

# Rate Limiting
from app.core.rate_limiting import RateLimiter, get_rate_limiter

# Action Logging
from app.core.action_logger import (
    ActionLogger, initialize_action_logger, toggle_action_logging,
    log_auth, log_project, log_session, log_specs, log_agent,
    log_llm, log_question, log_conflict, log_database, log_error, log_warning,
)

# Validators
from app.core.validators import (
    validate_email, validate_password, validate_username,
    validate_project_name, validate_team_name,
)

# ============================================================================
# Phase 3: FRAMEWORK EXPORTS (Fully operational)
# ============================================================================

# Domain Framework
from app.domains import (
    ProgrammingDomain, DataEngineeringDomain, ArchitectureDomain,
    TestingDomain, BusinessDomain, SecurityDomain, DevOpsDomain,
    BaseDomain, DomainRegistry, get_domain_registry,
)

# Agent Framework (14 agents + orchestrator)
# NOTE: Agent imports are deferred to __getattr__ to avoid circular imports
# Agents import from socrates package, creating circular dependency if imported here
# See __getattr__ function at end of file for lazy loading implementation
_agent_imports = {
    'ProjectManagerAgent', 'SocraticCounselorAgent', 'ContextAnalyzerAgent',
    'ConflictDetectorAgent', 'CodeGeneratorAgent', 'ExportAgent',
    'TeamCollaborationAgent', 'GitHubIntegrationAgent', 'BaseAgent',
    'AgentOrchestrator', 'get_orchestrator', 'reset_orchestrator', 'MultiLLMManager',
}

# Domain Base Models
from app.base import (
    SeverityLevel, Question, ExportFormat, ConflictRule, QualityAnalyzer,
)

# Database Models (33 models across 2 databases)
from app.models import (
    # Auth Database Models
    User, RefreshToken, AdminRole, AdminUser, AdminAuditLog,
    # Core Specs Models
    Project, Session, Question as QuestionModel, Specification,
    ConversationHistory, Conflict,
    # Generated Content
    GeneratedProject, GeneratedFile,
    # Analytics & Tracking
    QualityMetric, UserBehaviorPattern, QuestionEffectiveness,
    KnowledgeBaseDocument, LLMUsageTracking,
    # Collaboration
    Team, TeamMember, ProjectShare,
    # API & Billing
    APIKey, Subscription, Invoice,
    # Analytics & Search
    AnalyticsMetrics, DocumentChunk, NotificationPreferences,
    # Activity Management
    ActivityLog, ProjectInvitation,
    # Base
    BaseModel,
)

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

    # ========== PHASE 2: ADVANCED FEATURES (Requires configuration) ==========

    # Subscription & Usage Management
    "SubscriptionTier",
    "TIER_LIMITS",
    "UsageLimitError",
    "UsageLimiter",

    # Rate Limiting
    "RateLimiter",
    "get_rate_limiter",

    # Action Logging
    "ActionLogger",
    "initialize_action_logger",
    "toggle_action_logging",
    "log_auth",
    "log_project",
    "log_session",
    "log_specs",
    "log_agent",
    "log_llm",
    "log_question",
    "log_conflict",
    "log_database",
    "log_error",
    "log_warning",

    # Validators
    "validate_email",
    "validate_password",
    "validate_username",
    "validate_project_name",
    "validate_team_name",

    # ========== PHASE 3: FRAMEWORK (Fully operational) ==========

    # Domain Framework
    "BaseDomain",
    "DomainRegistry",
    "get_domain_registry",
    "ProgrammingDomain",
    "DataEngineeringDomain",
    "ArchitectureDomain",
    "TestingDomain",
    "BusinessDomain",
    "SecurityDomain",
    "DevOpsDomain",

    # Agent Framework (13 specialized agents + orchestrator + multi-LLM)
    "BaseAgent",
    "ProjectManagerAgent",
    "SocraticCounselorAgent",
    "ContextAnalyzerAgent",
    "ConflictDetectorAgent",
    "CodeGeneratorAgent",
    "ExportAgent",
    "TeamCollaborationAgent",
    "GitHubIntegrationAgent",
    "MultiLLMManager",
    "AgentOrchestrator",
    "get_orchestrator",
    "reset_orchestrator",

    # Domain Base Models
    "SeverityLevel",
    "Question",
    "ExportFormat",
    "ConflictRule",
    "QualityAnalyzer",

    # Database Models - Auth (5)
    "User",
    "RefreshToken",
    "AdminRole",
    "AdminUser",
    "AdminAuditLog",

    # Database Models - Core (6)
    "Project",
    "Session",
    "QuestionModel",
    "Specification",
    "ConversationHistory",
    "Conflict",

    # Database Models - Generated Content (2)
    "GeneratedProject",
    "GeneratedFile",

    # Database Models - Analytics & Tracking (4)
    "QualityMetric",
    "UserBehaviorPattern",
    "QuestionEffectiveness",
    "KnowledgeBaseDocument",
    "LLMUsageTracking",

    # Database Models - Collaboration (3)
    "Team",
    "TeamMember",
    "ProjectShare",

    # Database Models - API & Billing (3)
    "APIKey",
    "Subscription",
    "Invoice",

    # Database Models - Analytics & Search (3)
    "AnalyticsMetrics",
    "DocumentChunk",
    "NotificationPreferences",

    # Database Models - Activity Management (2)
    "ActivityLog",
    "ProjectInvitation",

    # Database Models - Base
    "BaseModel",
]


# ============================================================================
# LAZY LOADING IMPLEMENTATION - Avoid Circular Imports
# ============================================================================
# Module-level __getattr__ to support lazy loading of agents
# This prevents circular import: socrates/__init__.py <-> app/agents/*.py


def __getattr__(name: str):
    """
    Lazy load agent and orchestrator imports to avoid circular dependency.

    Agents import from socrates package (Phase 1a pure logic):
        from socrates import ConflictDetectionEngine, SpecificationData, etc.

    But socrates package exports agents (Phase 3 framework):
        from socrates import ProjectManagerAgent, etc.

    This creates a circular import when evaluated at module load time.

    Solution: This __getattr__ function intercepts attribute access.
    Agents are only imported when explicitly requested, not at module load.

    This pattern is safe in Python 3.7+ and is documented in PEP 562.
    """
    if name in _agent_imports:
        # Import all agents (this won't create circular import since
        # the agents module won't try to import socrates until it's fully loaded)
        from app.agents import (
            ProjectManagerAgent,
            SocraticCounselorAgent,
            ContextAnalyzerAgent,
            ConflictDetectorAgent,
            CodeGeneratorAgent,
            ExportAgent,
            TeamCollaborationAgent,
            GitHubIntegrationAgent,
            BaseAgent,
            AgentOrchestrator,
            get_orchestrator,
            reset_orchestrator,
            MultiLLMManager,
        )

        # Map requested name to actual import
        agents_map = {
            "ProjectManagerAgent": ProjectManagerAgent,
            "SocraticCounselorAgent": SocraticCounselorAgent,
            "ContextAnalyzerAgent": ContextAnalyzerAgent,
            "ConflictDetectorAgent": ConflictDetectorAgent,
            "CodeGeneratorAgent": CodeGeneratorAgent,
            "ExportAgent": ExportAgent,
            "TeamCollaborationAgent": TeamCollaborationAgent,
            "GitHubIntegrationAgent": GitHubIntegrationAgent,
            "BaseAgent": BaseAgent,
            "AgentOrchestrator": AgentOrchestrator,
            "get_orchestrator": get_orchestrator,
            "reset_orchestrator": reset_orchestrator,
            "MultiLLMManager": MultiLLMManager,
        }

        return agents_map[name]

    # If name not in _agent_imports, raise AttributeError
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

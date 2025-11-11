"""
SQLAlchemy Models for Socrates2

This module exports all models for both socrates_auth and socrates_specs databases.
Each model corresponds to a table created by the Alembic migrations.
"""

# AUTH Database Models
from .user import User
from .refresh_token import RefreshToken
from .admin_role import AdminRole
from .admin_user import AdminUser
from .admin_audit_log import AdminAuditLog

# SPECS Database Models - Core
from .project import Project
from .session import Session
from .question import Question
from .specification import Specification
from .conversation_history import ConversationHistory
from .conflict import Conflict

# SPECS Database Models - Generated Content
from .generated_project import GeneratedProject
from .generated_file import GeneratedFile

# SPECS Database Models - Analytics & Tracking
from .quality_metric import QualityMetric
from .user_behavior_pattern import UserBehaviorPattern
from .question_effectiveness import QuestionEffectiveness
from .knowledge_base_document import KnowledgeBaseDocument

# SPECS Database Models - Collaboration
from .team import Team
from .team_member import TeamMember
from .project_share import ProjectShare

# SPECS Database Models - API & LLM Integration
from .api_key import APIKey
from .llm_usage_tracking import LLMUsageTracking
from .subscription import Subscription
from .invoice import Invoice

# SPECS Database Models - Analytics & Search
from .analytics_metrics import AnalyticsMetrics
from .document_chunk import DocumentChunk
from .notification_preferences import NotificationPreferences

# SPECS Database Models - Activity & Management
from .activity_log import ActivityLog
from .project_invitation import ProjectInvitation

# Base
from .base import BaseModel

__all__ = [
    # Base
    'BaseModel',

    # AUTH Database
    'User',
    'RefreshToken',
    'AdminRole',
    'AdminUser',
    'AdminAuditLog',

    # SPECS Database - Core
    'Project',
    'Session',
    'Question',
    'Specification',
    'ConversationHistory',
    'Conflict',

    # SPECS Database - Generated Content
    'GeneratedProject',
    'GeneratedFile',

    # SPECS Database - Analytics & Tracking
    'QualityMetric',
    'UserBehaviorPattern',
    'QuestionEffectiveness',
    'KnowledgeBaseDocument',

    # SPECS Database - Collaboration
    'Team',
    'TeamMember',
    'ProjectShare',

    # SPECS Database - API & LLM Integration
    'APIKey',
    'LLMUsageTracking',
    'Subscription',
    'Invoice',

    # SPECS Database - Analytics & Search
    'AnalyticsMetrics',
    'DocumentChunk',
    'NotificationPreferences',

    # SPECS Database - Activity & Management
    'ActivityLog',
    'ProjectInvitation',
]

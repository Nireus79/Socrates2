"""
Socrates AI - Public API Package

This package provides the public interface for the Socrates AI system.
It re-exports core engines, models, and utilities from the app module.

For internal use within the application, prefer importing directly from app.core,
app.domains, etc. This package is primarily for external integrations and tests.
"""

# Package version
__version__ = "0.2.0"
__author__ = "Socrates Team"
__license__ = "MIT"

# Core Engines - Primary public API
from app.core.question_engine import QuestionGenerator
from app.core.conflict_engine import ConflictDetectionEngine
from app.core.quality_engine import BiasDetectionEngine
from app.core.learning_engine import LearningEngine

# Data Models
from app.core.models import (
    ProjectData,
    QuestionData,
    SpecificationData,
    ConflictData,
    BiasAnalysisResult,
    CoverageAnalysisResult,
    MaturityScore,
    UserBehaviorData,
)

# Data conversion utilities
from app.core.models import (
    project_db_to_data,
    spec_db_to_data,
    question_db_to_data,
    conflict_db_to_data,
    specs_db_to_data,
    questions_db_to_data,
    conflicts_db_to_data,
    conversation_db_to_api_message,
)

# Domain registry
from app.domains.registry import (
    DomainRegistry,
    get_domain_registry,
    register_domain,
)

# Individual domains
from app.domains.programming import ProgrammingDomain
from app.domains.architecture import ArchitectureDomain
from app.domains.testing import TestingDomain
from app.domains.business import BusinessDomain
from app.domains.data_engineering import DataEngineeringDomain
from app.domains.security import SecurityDomain
from app.domains.devops import DevOpsDomain

# Re-export base classes
from app.base.base_domain import BaseDomain
from app.base.models import Question, ExportFormat, ConflictRule, QualityAnalyzer

__all__ = [
    # Version
    "__version__",

    # Core Engines
    "QuestionGenerator",
    "ConflictDetectionEngine",
    "BiasDetectionEngine",
    "LearningEngine",

    # Data Models
    "ProjectData",
    "QuestionData",
    "SpecificationData",
    "ConflictData",
    "BiasAnalysisResult",
    "CoverageAnalysisResult",
    "MaturityScore",
    "UserBehaviorData",

    # Data Conversion Functions
    "project_db_to_data",
    "spec_db_to_data",
    "question_db_to_data",
    "conflict_db_to_data",
    "specs_db_to_data",
    "questions_db_to_data",
    "conflicts_db_to_data",
    "conversation_db_to_api_message",

    # Domain System
    "DomainRegistry",
    "get_domain_registry",
    "register_domain",

    # Domains
    "ProgrammingDomain",
    "ArchitectureDomain",
    "TestingDomain",
    "BusinessDomain",
    "DataEngineeringDomain",
    "SecurityDomain",
    "DevOpsDomain",

    # Base Classes
    "BaseDomain",
    "Question",
    "ExportFormat",
    "ConflictRule",
    "QualityAnalyzer",
]

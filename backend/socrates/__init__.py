"""
Socrates Library - Public API

Re-exports core engines and data models from app.core for external use.
This provides a clean public interface for agents and external code.

Internal: app.core.* (implementation)
Public: socrates.* (API)
"""

__version__ = "0.2.0"

# ============================================================================
# Core Engines
# ============================================================================

from app.core.question_engine import QuestionGenerator
from app.core.conflict_engine import ConflictDetectionEngine
from app.core.quality_engine import BiasDetectionEngine
from app.core.learning_engine import LearningEngine

# ============================================================================
# Data Models
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
# Conversion Functions
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
# Public API
# ============================================================================

__all__ = [
    # Engines
    "QuestionGenerator",
    "ConflictDetectionEngine",
    "BiasDetectionEngine",
    "LearningEngine",
    # Data Models
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
]

"""
Base classes and enums for Socrates framework.

Provides abstract base classes, data models, and enumerations used throughout
the framework for analyzers, exporters, domains, and quality metrics.
"""

from .base_domain import BaseDomain
from .models import (
    ConflictRule,
    ExportFormat,
    Question,
    QualityAnalyzer,
    SeverityLevel,
)

__all__ = [
    "BaseDomain",
    "ConflictRule",
    "ExportFormat",
    "Question",
    "QualityAnalyzer",
    "SeverityLevel",
]

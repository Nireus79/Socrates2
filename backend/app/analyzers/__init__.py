"""
Quality Analyzer Engine for Socrates.

Provides the analyzer template engine for managing, filtering, and validating
quality analyzers across specifications and domains.
"""

from .engine import QualityAnalyzerEngine, get_analyzer_engine

__all__ = [
    "QualityAnalyzerEngine",
    "get_analyzer_engine",
]

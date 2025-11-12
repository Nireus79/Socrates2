"""
Programming Domain Module

Re-exports the ProgrammingDomain from the domains package for convenient access.
This module provides the Programming domain implementation for the Socratic question
system, including programming-specific questions, quality rules, and export templates.

Usage:
    from app.programming import ProgrammingDomain

    domain = ProgrammingDomain()
    questions = domain.get_questions()
"""

from app.domains.programming import ProgrammingDomain

__all__ = ["ProgrammingDomain"]

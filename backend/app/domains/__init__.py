"""
Multi-domain system for Socrates2.

Enables Socrates2 to work with any knowledge domain:
- Programming (current)
- Technical Documentation
- Book Writing
- Business Planning
- Marketing
- Academic Research
- And many more...

Core components:
- BaseDomain: Abstract base for all domains
- DomainRegistry: Central registry of available domains
- Question engine: Domain-specific questions
- Conflict engine: Domain-specific rules
- Export engine: Domain-specific outputs
- Analyzer engine: Domain-specific quality checks
"""

from .base import BaseDomain
from .registry import DomainRegistry, get_domain_registry
from .programming import ProgrammingDomain
from .data_engineering import DataEngineeringDomain
from .architecture import ArchitectureDomain
from .testing import TestingDomain

__all__ = [
    "BaseDomain",
    "DomainRegistry",
    "get_domain_registry",
    "ProgrammingDomain",
    "DataEngineeringDomain",
    "ArchitectureDomain",
    "TestingDomain",
]

"""
Rules Domain Module

Re-exports the ConflictRuleEngine and related utilities from the domains package.
This module provides the conflict detection and resolution rules system that helps
identify and resolve conflicts between specifications across different domains.

Usage:
    from app.rules import ConflictRuleEngine, get_rule_engine

    engine = get_rule_engine()
    rules = engine.get_all_rules()
    programming_rules = engine.filter_by_domain("programming")
"""

from app.domains.rules import (
    ConflictRuleEngine,
    get_rule_engine,
)

__all__ = [
    "ConflictRuleEngine",
    "get_rule_engine",
]

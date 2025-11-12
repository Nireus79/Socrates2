"""
Domain Registry Module

Re-exports the DomainRegistry and related utilities from the domains package.
This module provides the central registry for all knowledge domains, allowing
registration, lookup, and management of domain implementations across the system.

Usage:
    from app.registry import DomainRegistry, get_domain_registry, register_domain

    registry = get_domain_registry()
    programming_domain = registry.get_domain("programming")
    all_domains = registry.get_all_domains()
"""

from app.domains.registry import (
    DomainRegistry,
    get_domain_registry,
    register_domain,
)

__all__ = [
    "DomainRegistry",
    "get_domain_registry",
    "register_domain",
]

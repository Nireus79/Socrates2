"""
Domain registry system for Socrates2.

Central registry that manages all available knowledge domains.
Supports registration, discovery, and lifecycle management of domains.
"""

import logging
from typing import Dict, Optional, Type
from .base import BaseDomain

logger = logging.getLogger(__name__)


class DomainRegistry:
    """
    Central registry for all Socrates2 knowledge domains.

    Singleton that manages domain registration, lookup, and metadata.

    Usage:
        registry = DomainRegistry()
        registry.register("programming", ProgrammingDomain)
        domain = registry.get_domain("programming")
    """

    _instance: Optional['DomainRegistry'] = None
    _domains: Dict[str, Type[BaseDomain]] = {}
    _instances: Dict[str, BaseDomain] = {}

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, domain_id: str, domain_class: Type[BaseDomain]) -> None:
        """
        Register a domain class.

        Args:
            domain_id: Unique identifier for the domain (e.g., "programming", "book_writing")
            domain_class: Class inheriting from BaseDomain

        Raises:
            ValueError: If domain_id already registered or class invalid

        Example:
            registry.register("programming", ProgrammingDomain)
        """
        if domain_id in self._domains:
            raise ValueError(f"Domain '{domain_id}' already registered")

        if not issubclass(domain_class, BaseDomain):
            raise ValueError(f"Domain class must inherit from BaseDomain")

        self._domains[domain_id] = domain_class
        logger.info(f"Registered domain: {domain_id} ({domain_class.__name__})")

    def get_domain(self, domain_id: str) -> BaseDomain:
        """
        Get a domain instance by ID.

        Uses lazy instantiation and caching for performance.

        Args:
            domain_id: Domain identifier

        Returns:
            BaseDomain instance

        Raises:
            ValueError: If domain not found

        Example:
            domain = registry.get_domain("programming")
            questions = domain.get_questions()
        """
        if domain_id not in self._domains:
            raise ValueError(
                f"Domain '{domain_id}' not found. "
                f"Available domains: {', '.join(self.list_domain_ids())}"
            )

        # Return cached instance if available
        if domain_id not in self._instances:
            domain_class = self._domains[domain_id]
            self._instances[domain_id] = domain_class()
            logger.info(f"Instantiated domain: {domain_id}")

        return self._instances[domain_id]

    def has_domain(self, domain_id: str) -> bool:
        """Check if a domain is registered."""
        return domain_id in self._domains

    def list_domain_ids(self) -> list[str]:
        """Get list of all registered domain IDs."""
        return list(self._domains.keys())

    def list_domains(self) -> Dict[str, BaseDomain]:
        """Get all domain instances."""
        result = {}
        for domain_id in self.list_domain_ids():
            result[domain_id] = self.get_domain(domain_id)
        return result

    def get_domain_count(self) -> int:
        """Get number of registered domains."""
        return len(self._domains)

    def unregister(self, domain_id: str) -> None:
        """
        Unregister a domain (for testing).

        Args:
            domain_id: Domain to unregister

        Raises:
            ValueError: If domain not found
        """
        if domain_id not in self._domains:
            raise ValueError(f"Domain '{domain_id}' not registered")

        del self._domains[domain_id]
        if domain_id in self._instances:
            del self._instances[domain_id]

        logger.info(f"Unregistered domain: {domain_id}")

    def clear(self) -> None:
        """Clear all registered domains (for testing)."""
        self._domains.clear()
        self._instances.clear()
        logger.info("Cleared all domains")

    def to_dict(self) -> Dict:
        """Get registry metadata as dictionary."""
        domains = {}
        for domain_id in self.list_domain_ids():
            domain = self.get_domain(domain_id)
            domains[domain_id] = {
                "name": domain.name,
                "version": domain.version,
                "description": domain.description,
                "categories": domain.get_categories(),
                "questions": len(domain.get_questions()),
                "exporters": len(domain.get_export_formats()),
                "rules": len(domain.get_conflict_rules()),
            }

        return {
            "domain_count": self.get_domain_count(),
            "domains": domains,
        }


# Global singleton instance
_global_registry: Optional[DomainRegistry] = None


def get_domain_registry() -> DomainRegistry:
    """
    Get the global domain registry instance.

    This is the primary way to access domains throughout the application.

    Returns:
        DomainRegistry singleton

    Example:
        registry = get_domain_registry()
        domain = registry.get_domain("programming")
        questions = domain.get_questions()
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = DomainRegistry()
    return _global_registry


def register_domain(domain_id: str, domain_class: Type[BaseDomain]) -> None:
    """
    Register a domain with the global registry.

    Convenience function for domain registration.

    Args:
        domain_id: Unique domain identifier
        domain_class: Class inheriting from BaseDomain

    Example:
        register_domain("programming", ProgrammingDomain)
    """
    get_domain_registry().register(domain_id, domain_class)


def register_all_domains() -> None:
    """
    Register all available Socrates2 domains.

    Should be called during application initialization to ensure all domains are available.
    """
    from .programming import ProgrammingDomain
    from .data_engineering import DataEngineeringDomain
    from .architecture import ArchitectureDomain
    from .testing import TestingDomain

    registry = get_domain_registry()

    # Register all available domains
    registry.register("programming", ProgrammingDomain)
    registry.register("data_engineering", DataEngineeringDomain)
    registry.register("architecture", ArchitectureDomain)
    registry.register("testing", TestingDomain)

    logger.info(f"Registered {registry.get_domain_count()} domains")

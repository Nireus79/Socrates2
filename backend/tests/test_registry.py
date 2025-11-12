"""Tests for DomainRegistry system."""

import pytest

from app.base import BaseDomain
from app.registry import DomainRegistry, get_domain_registry, register_domain


class SimpleDomain(BaseDomain):
    """Simple test domain."""

    domain_id = "simple"
    name = "Simple Domain"
    version = "1.0.0"

    def get_categories(self):
        return ["test"]

    def get_questions(self):
        return []

    def get_export_formats(self):
        return []

    def get_conflict_rules(self):
        return []

    def get_quality_analyzers(self):
        return []


class AnotherDomain(BaseDomain):
    """Another test domain."""

    domain_id = "another"
    name = "Another Domain"
    version = "2.0.0"

    def get_categories(self):
        return ["test2"]

    def get_questions(self):
        return []

    def get_export_formats(self):
        return []

    def get_conflict_rules(self):
        return []

    def get_quality_analyzers(self):
        return []


class TestDomainRegistry:
    """Test DomainRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        reg = DomainRegistry()
        reg.clear()
        return reg

    def test_registry_is_singleton(self):
        """Test that DomainRegistry is a singleton."""
        reg1 = DomainRegistry()
        reg2 = DomainRegistry()
        assert reg1 is reg2

    def test_register_domain(self, registry):
        """Test registering a domain."""
        registry.register("simple", SimpleDomain)
        assert registry.has_domain("simple")

    def test_register_duplicate_raises_error(self, registry):
        """Test that registering duplicate domain raises error."""
        registry.register("simple", SimpleDomain)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("simple", SimpleDomain)

    def test_register_invalid_class_raises_error(self, registry):
        """Test that registering non-BaseDomain class raises error."""

        class NotADomain:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseDomain"):
            registry.register("invalid", NotADomain)

    def test_get_domain(self, registry):
        """Test getting a domain."""
        registry.register("simple", SimpleDomain)
        domain = registry.get_domain("simple")
        assert domain.domain_id == "simple"
        assert domain.name == "Simple Domain"

    def test_get_nonexistent_domain_raises_error(self, registry):
        """Test that getting non-existent domain raises error."""
        with pytest.raises(ValueError, match="not found"):
            registry.get_domain("nonexistent")

    def test_domain_lazy_instantiation(self, registry):
        """Test that domains are lazily instantiated."""
        registry.register("simple", SimpleDomain)
        # Register but don't access yet
        assert "simple" not in registry._instances
        # Access domain
        domain1 = registry.get_domain("simple")
        assert "simple" in registry._instances
        # Getting again should return cached instance
        domain2 = registry.get_domain("simple")
        assert domain1 is domain2

    def test_has_domain(self, registry):
        """Test checking if domain exists."""
        registry.register("simple", SimpleDomain)
        assert registry.has_domain("simple")
        assert not registry.has_domain("nonexistent")

    def test_list_domain_ids(self, registry):
        """Test listing all domain IDs."""
        registry.register("simple", SimpleDomain)
        registry.register("another", AnotherDomain)
        ids = registry.list_domain_ids()
        assert "simple" in ids
        assert "another" in ids
        assert len(ids) == 2

    def test_list_domains(self, registry):
        """Test listing all domains."""
        registry.register("simple", SimpleDomain)
        registry.register("another", AnotherDomain)
        domains = registry.list_domains()
        assert len(domains) == 2
        assert "simple" in domains
        assert domains["simple"].domain_id == "simple"

    def test_get_domain_count(self, registry):
        """Test getting domain count."""
        assert registry.get_domain_count() == 0
        registry.register("simple", SimpleDomain)
        assert registry.get_domain_count() == 1
        registry.register("another", AnotherDomain)
        assert registry.get_domain_count() == 2

    def test_unregister(self, registry):
        """Test unregistering a domain."""
        registry.register("simple", SimpleDomain)
        assert registry.has_domain("simple")
        registry.unregister("simple")
        assert not registry.has_domain("simple")

    def test_unregister_nonexistent_raises_error(self, registry):
        """Test that unregistering non-existent domain raises error."""
        with pytest.raises(ValueError):
            registry.unregister("nonexistent")

    def test_clear(self, registry):
        """Test clearing all domains."""
        registry.register("simple", SimpleDomain)
        registry.register("another", AnotherDomain)
        assert registry.get_domain_count() == 2
        registry.clear()
        assert registry.get_domain_count() == 0

    def test_to_dict(self, registry):
        """Test converting registry to dict."""
        registry.register("simple", SimpleDomain)
        data = registry.to_dict()
        assert data["domain_count"] == 1
        assert "simple" in data["domains"]
        assert data["domains"]["simple"]["name"] == "Simple Domain"


class TestGlobalFunctions:
    """Test global registry functions."""

    def test_get_domain_registry(self):
        """Test getting global registry."""
        reg1 = get_domain_registry()
        reg2 = get_domain_registry()
        assert reg1 is reg2

    def test_register_domain_global(self):
        """Test registering domain globally."""
        # Clear first
        get_domain_registry().clear()
        register_domain("simple", SimpleDomain)
        registry = get_domain_registry()
        assert registry.has_domain("simple")
        domain = registry.get_domain("simple")
        assert domain.domain_id == "simple"

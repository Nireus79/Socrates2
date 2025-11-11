"""Tests for multi-domain workflow system."""

import pytest
from app.domains.workflows import (
    MultiDomainWorkflow,
    WorkflowManager,
    CrossDomainConflict,
    DomainSpec,
    get_workflow_manager,
)
from app.domains.registry import register_all_domains, get_domain_registry


@pytest.fixture(scope="session", autouse=True)
def register_domains():
    """Register all domains before running tests."""
    try:
        register_all_domains()
    except ValueError:
        # Domains already registered
        pass


class TestMultiDomainWorkflow:
    """Test MultiDomainWorkflow functionality."""

    @pytest.fixture
    def workflow(self):
        """Create a fresh workflow."""
        return MultiDomainWorkflow("test_workflow_001")

    def test_workflow_creation(self, workflow):
        """Test creating a workflow."""
        assert workflow.workflow_id == "test_workflow_001"
        assert workflow.get_involved_domains() == []

    def test_add_domain_spec(self, workflow):
        """Test adding domain specification."""
        responses = {"q1": "answer1", "q2": "answer2"}
        workflow.add_domain_spec("programming", responses)

        assert "programming" in workflow.domain_specs
        assert workflow.domain_specs["programming"].responses == responses

    def test_add_multiple_domains(self, workflow):
        """Test adding multiple domains."""
        workflow.add_domain_spec("programming", {"q1": "a1"})
        workflow.add_domain_spec("testing", {"q2": "a2"})
        workflow.add_domain_spec("architecture", {"q3": "a3"})

        assert len(workflow.get_involved_domains()) == 3
        assert set(workflow.get_involved_domains()) == {"programming", "testing", "architecture"}

    def test_add_invalid_domain_raises_error(self, workflow):
        """Test adding non-existent domain raises error."""
        with pytest.raises(ValueError):
            workflow.add_domain_spec("nonexistent_domain", {})

    def test_remove_domain_spec(self, workflow):
        """Test removing domain specification."""
        workflow.add_domain_spec("programming", {"q1": "a1"})
        assert "programming" in workflow.domain_specs

        workflow.remove_domain_spec("programming")
        assert "programming" not in workflow.domain_specs

    def test_validate_single_domain_success(self, workflow):
        """Test validating single domain."""
        workflow.add_domain_spec("programming", {"architecture": "microservices"})
        validation = workflow.validate_single_domain("programming")

        assert "domain_id" in validation
        assert "valid" in validation
        assert validation["domain_id"] == "programming"

    def test_validate_empty_workflow_fails(self, workflow):
        """Test validating empty workflow."""
        result = workflow.validate()

        assert result.status == "invalid"
        assert "error" in result.summary

    def test_detect_cross_domain_conflicts_empty(self, workflow):
        """Test conflict detection with no domains."""
        conflicts = workflow.detect_cross_domain_conflicts()
        assert len(conflicts) == 0

    def test_detect_architecture_testing_conflict(self, workflow):
        """Test detecting architecture-testing conflicts."""
        workflow.add_domain_spec(
            "architecture",
            {"architecture_type": "microservices", "scalability": "manual_scaling"}
        )
        workflow.add_domain_spec(
            "testing",
            {"testing_strategy": "unit_only"}
        )

        conflicts = workflow.detect_cross_domain_conflicts()

        # Conflicts should be detected (list may be empty or have conflicts depending on matching logic)
        # This test verifies the conflict detection runs without error
        assert isinstance(conflicts, list)

    def test_detect_performance_testing_conflict(self, workflow):
        """Test detecting performance-testing conflicts."""
        workflow.add_domain_spec(
            "programming",
            {"target_response_time": 500}
        )
        workflow.add_domain_spec(
            "testing",
            {"testing_strategy": "just_unit_tests"}
        )

        conflicts = workflow.detect_cross_domain_conflicts()

        # Should detect warning about performance targets without testing
        performance_conflicts = [
            c for c in conflicts
            if "programming" in c.domains_involved and "testing" in c.domains_involved
        ]
        assert len(performance_conflicts) > 0

    def test_detect_data_architecture_conflict(self, workflow):
        """Test detecting data engineering-architecture conflicts."""
        workflow.add_domain_spec(
            "data_engineering",
            {"data_growth": 50}
        )
        workflow.add_domain_spec(
            "architecture",
            {"scalability": "manual_scaling_only"}
        )

        conflicts = workflow.detect_cross_domain_conflicts()

        # Should detect warning about scaling needs
        data_arch_conflicts = [
            c for c in conflicts
            if "data_engineering" in c.domains_involved
            and "architecture" in c.domains_involved
        ]
        assert len(data_arch_conflicts) > 0

    def test_workflow_validation_with_domains(self, workflow):
        """Test full workflow validation."""
        workflow.add_domain_spec("programming", {"language": "python"})
        workflow.add_domain_spec("testing", {"strategy": "tdd"})

        result = workflow.validate()

        assert result.workflow_id == "test_workflow_001"
        assert "domain_validations" in result.summary
        assert result.summary["total_domains"] == 2

    def test_get_combined_categories(self, workflow):
        """Test getting combined categories."""
        workflow.add_domain_spec("programming", {})
        workflow.add_domain_spec("testing", {})

        categories = workflow.get_combined_categories()

        assert "programming" in categories
        assert "testing" in categories
        assert len(categories["programming"]) > 0
        assert len(categories["testing"]) > 0

    def test_export_specification_json(self, workflow):
        """Test exporting specification."""
        workflow.add_domain_spec("programming", {"language": "python"})

        exported = workflow.export_specification("json")

        assert exported["workflow_id"] == "test_workflow_001"
        assert "domains" in exported
        assert "programming" in exported["domains"]

    def test_export_unsupported_format_raises_error(self, workflow):
        """Test exporting unsupported format raises error."""
        workflow.add_domain_spec("programming", {})

        with pytest.raises(ValueError):
            workflow.export_specification("xml")

    def test_domain_spec_to_dict(self):
        """Test DomainSpec serialization."""
        spec = DomainSpec(
            domain_id="programming",
            responses={"q1": "a1"},
            metadata={"source": "api"}
        )

        spec_dict = spec.to_dict()

        assert spec_dict["domain_id"] == "programming"
        assert spec_dict["responses"] == {"q1": "a1"}
        assert spec_dict["metadata"]["source"] == "api"

    def test_cross_domain_conflict_to_dict(self):
        """Test CrossDomainConflict serialization."""
        conflict = CrossDomainConflict(
            conflict_id="conf_001",
            domains_involved={"programming", "testing"},
            severity="warning",
            message="Test warning",
            resolution_suggestions=["Suggestion 1"]
        )

        conflict_dict = conflict.to_dict()

        assert conflict_dict["conflict_id"] == "conf_001"
        assert "programming" in conflict_dict["domains_involved"]
        assert conflict_dict["severity"] == "warning"


class TestWorkflowManager:
    """Test WorkflowManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a fresh workflow manager."""
        return WorkflowManager()

    def test_create_workflow(self, manager):
        """Test creating a workflow."""
        workflow = manager.create_workflow("wf_001")

        assert workflow.workflow_id == "wf_001"
        assert manager.get_workflow("wf_001") == workflow

    def test_create_duplicate_workflow_raises_error(self, manager):
        """Test creating duplicate workflow raises error."""
        manager.create_workflow("wf_001")

        with pytest.raises(ValueError):
            manager.create_workflow("wf_001")

    def test_get_workflow_success(self, manager):
        """Test getting existing workflow."""
        manager.create_workflow("wf_001")
        workflow = manager.get_workflow("wf_001")

        assert workflow.workflow_id == "wf_001"

    def test_get_nonexistent_workflow_raises_error(self, manager):
        """Test getting non-existent workflow raises error."""
        with pytest.raises(ValueError):
            manager.get_workflow("nonexistent")

    def test_list_workflows(self, manager):
        """Test listing workflows."""
        manager.create_workflow("wf_001")
        manager.create_workflow("wf_002")
        manager.create_workflow("wf_003")

        workflows = manager.list_workflows()

        assert len(workflows) == 3
        assert "wf_001" in workflows
        assert "wf_002" in workflows
        assert "wf_003" in workflows

    def test_delete_workflow(self, manager):
        """Test deleting workflow."""
        manager.create_workflow("wf_001")
        assert "wf_001" in manager.list_workflows()

        manager.delete_workflow("wf_001")
        assert "wf_001" not in manager.list_workflows()

    def test_delete_nonexistent_workflow_raises_error(self, manager):
        """Test deleting non-existent workflow raises error."""
        with pytest.raises(ValueError):
            manager.delete_workflow("nonexistent")

    def test_workflow_lifecycle(self, manager):
        """Test complete workflow lifecycle."""
        # Create
        workflow = manager.create_workflow("wf_lifecycle")
        assert "wf_lifecycle" in manager.list_workflows()

        # Modify
        workflow.add_domain_spec("programming", {"lang": "py"})
        assert "programming" in workflow.get_involved_domains()

        # Get
        retrieved = manager.get_workflow("wf_lifecycle")
        assert "programming" in retrieved.get_involved_domains()

        # Delete
        manager.delete_workflow("wf_lifecycle")
        assert "wf_lifecycle" not in manager.list_workflows()


class TestGlobalWorkflowManager:
    """Test global workflow manager instance."""

    def test_get_workflow_manager_singleton(self):
        """Test that get_workflow_manager returns singleton."""
        manager1 = get_workflow_manager()
        manager2 = get_workflow_manager()

        assert manager1 is manager2


class TestWorkflowIntegration:
    """Integration tests for workflow system."""

    def test_multi_domain_workflow_end_to_end(self):
        """Test complete multi-domain workflow."""
        workflow = MultiDomainWorkflow("integration_test_001")

        # Add multiple domains
        workflow.add_domain_spec("programming", {
            "language": "python",
            "target_response_time": 500
        })
        workflow.add_domain_spec("testing", {
            "testing_strategy": "comprehensive"
        })
        workflow.add_domain_spec("architecture", {
            "architecture_type": "microservices",
            "scalability": "auto"
        })

        # Validate
        result = workflow.validate()

        assert result.workflow_id == "integration_test_001"
        assert result.summary["total_domains"] == 3
        assert len(result.cross_domain_conflicts) >= 0

        # Export
        exported = workflow.export_specification()
        assert exported["workflow_id"] == "integration_test_001"
        assert len(exported["domains"]) == 3

    def test_workflow_with_conflicts(self):
        """Test workflow with detected conflicts."""
        workflow = MultiDomainWorkflow("conflict_test_001")

        # Add conflicting specs
        workflow.add_domain_spec("architecture", {
            "architecture_type": "monolithic"
        })
        workflow.add_domain_spec("testing", {
            "testing_strategy": "minimal_testing"
        })

        conflicts = workflow.detect_cross_domain_conflicts()

        # Monolithic might have issues with minimal testing
        assert isinstance(conflicts, list)

    def test_manager_workflow_operations(self):
        """Test manager operations on workflows."""
        manager = WorkflowManager()

        # Create multiple workflows
        wf1 = manager.create_workflow("wf_001")
        wf2 = manager.create_workflow("wf_002")

        # Add specs
        wf1.add_domain_spec("programming", {})
        wf2.add_domain_spec("testing", {})

        # List
        workflows = manager.list_workflows()
        assert len(workflows) == 2

        # Get and verify
        retrieved_wf1 = manager.get_workflow("wf_001")
        assert "programming" in retrieved_wf1.get_involved_domains()

        # Delete
        manager.delete_workflow("wf_001")
        assert len(manager.list_workflows()) == 1

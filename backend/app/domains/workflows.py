"""
Multi-domain workflow system for Socrates2.

Enables combining specifications from multiple domains with unified validation,
cross-domain conflict detection, and composite specification generation.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseDomain, ConflictRule
from .registry import get_domain_registry

logger = logging.getLogger(__name__)


@dataclass
class DomainSpec:
    """Specification for a single domain in a workflow."""

    domain_id: str
    responses: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "domain_id": self.domain_id,
            "responses": self.responses,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CrossDomainConflict:
    """Represents a conflict detected across multiple domains."""

    conflict_id: str
    domains_involved: Set[str]
    severity: str  # "error", "warning", "info"
    message: str
    related_rules: List[str] = field(default_factory=list)
    resolution_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conflict_id": self.conflict_id,
            "domains_involved": list(self.domains_involved),
            "severity": self.severity,
            "message": self.message,
            "related_rules": self.related_rules,
            "resolution_suggestions": self.resolution_suggestions,
        }


@dataclass
class WorkflowResult:
    """Result of a multi-domain workflow validation."""

    workflow_id: str
    status: str  # "valid", "invalid", "warnings"
    domain_specs: Dict[str, DomainSpec]
    cross_domain_conflicts: List[CrossDomainConflict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_valid(self) -> bool:
        """Check if workflow is valid (no errors)."""
        return self.status != "invalid"

    def has_warnings(self) -> bool:
        """Check if workflow has warnings."""
        return any(c.severity == "warning" for c in self.cross_domain_conflicts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "domain_specs": {k: v.to_dict() for k, v in self.domain_specs.items()},
            "cross_domain_conflicts": [c.to_dict() for c in self.cross_domain_conflicts],
            "summary": self.summary,
            "generated_at": self.generated_at,
        }


class MultiDomainWorkflow:
    """
    Multi-domain workflow orchestrator.

    Manages specifications across multiple domains with unified validation,
    conflict detection, and composite specification generation.

    Usage:
        workflow = MultiDomainWorkflow("workflow_001")
        workflow.add_domain_spec("programming", {"language": "python"})
        workflow.add_domain_spec("testing", {"strategy": "tdd"})
        result = workflow.validate()
    """

    def __init__(self, workflow_id: str):
        """
        Initialize a multi-domain workflow.

        Args:
            workflow_id: Unique identifier for this workflow
        """
        self.workflow_id = workflow_id
        self.domain_specs: Dict[str, DomainSpec] = {}
        self.registry = get_domain_registry()

    def add_domain_spec(
        self,
        domain_id: str,
        responses: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> None:
        """
        Add a domain specification to the workflow.

        Args:
            domain_id: ID of the domain
            responses: Responses/answers from domain questions
            metadata: Optional metadata about the specification

        Raises:
            ValueError: If domain not found
        """
        if not self.registry.has_domain(domain_id):
            raise ValueError(f"Domain '{domain_id}' not found in registry")

        self.domain_specs[domain_id] = DomainSpec(
            domain_id=domain_id,
            responses=responses,
            metadata=metadata or {},
        )
        logger.info(f"Added domain spec for '{domain_id}' to workflow '{self.workflow_id}'")

    def remove_domain_spec(self, domain_id: str) -> None:
        """
        Remove a domain specification from the workflow.

        Args:
            domain_id: ID of the domain to remove
        """
        if domain_id in self.domain_specs:
            del self.domain_specs[domain_id]
            logger.info(f"Removed domain spec for '{domain_id}' from workflow '{self.workflow_id}'")

    def get_involved_domains(self) -> List[str]:
        """Get list of domains in this workflow."""
        return list(self.domain_specs.keys())

    def validate_single_domain(self, domain_id: str) -> Dict[str, Any]:
        """
        Validate a single domain specification.

        Args:
            domain_id: Domain to validate

        Returns:
            Validation result with any errors/warnings
        """
        if domain_id not in self.domain_specs:
            return {"valid": False, "error": f"Domain spec '{domain_id}' not found"}

        domain = self.registry.get_domain(domain_id)
        rules = domain.get_conflict_rules()

        # Simple validation: check if required questions are answered
        questions = domain.get_questions()
        responses = self.domain_specs[domain_id].responses

        missing_questions = [q for q in questions if q.question_id not in responses]
        answered_questions = [q for q in questions if q.question_id in responses]

        return {
            "domain_id": domain_id,
            "valid": len(missing_questions) == 0,
            "answered_questions": len(answered_questions),
            "missing_questions": [q.question_id for q in missing_questions],
            "rules_available": len(rules),
        }

    def detect_cross_domain_conflicts(self) -> List[CrossDomainConflict]:
        """
        Detect conflicts across multiple domains.

        Returns:
            List of detected cross-domain conflicts
        """
        conflicts = []

        # Check for architecture/testing consistency
        if "architecture" in self.domain_specs and "testing" in self.domain_specs:
            arch_spec = self.domain_specs["architecture"]
            test_spec = self.domain_specs["testing"]

            # Check if testing strategy matches architecture
            if "architecture_type" in arch_spec.responses and "testing_strategy" in test_spec.responses:
                arch_type = arch_spec.responses.get("architecture_type", "").lower()
                test_strategy = test_spec.responses.get("testing_strategy", "").lower()

                # Microservices need comprehensive testing
                if "microservice" in arch_type and "unit" not in test_strategy:
                    conflicts.append(
                        CrossDomainConflict(
                            conflict_id=f"{self.workflow_id}_arch_test_001",
                            domains_involved={"architecture", "testing"},
                            severity="warning",
                            message="Microservices architecture requires comprehensive testing strategy",
                            resolution_suggestions=[
                                "Consider adding integration and end-to-end testing to your strategy",
                                "Implement contract testing between services",
                            ],
                        )
                    )

        # Check for performance/testing consistency
        if "programming" in self.domain_specs and "testing" in self.domain_specs:
            prog_spec = self.domain_specs["programming"]
            test_spec = self.domain_specs["testing"]

            # Check if performance testing is planned
            if "target_response_time" in prog_spec.responses:
                target_time = prog_spec.responses.get("target_response_time", 0)
                if target_time > 0 and "performance_testing" not in test_spec.responses:
                    conflicts.append(
                        CrossDomainConflict(
                            conflict_id=f"{self.workflow_id}_perf_test_001",
                            domains_involved={"programming", "testing"},
                            severity="warning",
                            message="Performance targets defined but no performance testing planned",
                            resolution_suggestions=[
                                "Add load testing to validate performance targets",
                                "Define acceptable latency thresholds",
                            ],
                        )
                    )

        # Check for data engineering/architecture consistency
        if "data_engineering" in self.domain_specs and "architecture" in self.domain_specs:
            data_spec = self.domain_specs["data_engineering"]
            arch_spec = self.domain_specs["architecture"]

            # Check if scalability matches
            if "data_growth" in data_spec.responses and "scalability" in arch_spec.responses:
                growth = data_spec.responses.get("data_growth", 0)
                scalability = arch_spec.responses.get("scalability", "").lower()

                if growth > 30 and "auto" not in scalability:
                    conflicts.append(
                        CrossDomainConflict(
                            conflict_id=f"{self.workflow_id}_data_arch_001",
                            domains_involved={"data_engineering", "architecture"},
                            severity="warning",
                            message="High data growth requires auto-scaling architecture",
                            resolution_suggestions=[
                                "Implement auto-scaling for your data pipeline",
                                "Use cloud-native solutions for elastic scaling",
                            ],
                        )
                    )

        return conflicts

    def validate(self) -> WorkflowResult:
        """
        Validate the entire multi-domain workflow.

        Returns:
            WorkflowResult with validation status and conflicts
        """
        if not self.domain_specs:
            return WorkflowResult(
                workflow_id=self.workflow_id,
                status="invalid",
                domain_specs={},
                summary={"error": "No domain specifications added"},
            )

        # Validate each domain
        domain_validations = {}
        has_errors = False

        for domain_id in self.get_involved_domains():
            validation = self.validate_single_domain(domain_id)
            domain_validations[domain_id] = validation

            if not validation.get("valid", False):
                has_errors = True

        # Detect cross-domain conflicts
        conflicts = self.detect_cross_domain_conflicts()

        # Determine overall status
        if has_errors:
            status = "invalid"
        elif conflicts and any(c.severity == "error" for c in conflicts):
            status = "invalid"
        elif conflicts:
            status = "warnings"
        else:
            status = "valid"

        # Build summary
        summary = {
            "total_domains": len(self.domain_specs),
            "domains_involved": self.get_involved_domains(),
            "total_questions_answered": sum(
                v.get("answered_questions", 0) for v in domain_validations.values()
            ),
            "total_questions_missing": sum(
                len(v.get("missing_questions", [])) for v in domain_validations.values()
            ),
            "cross_domain_conflicts": len(conflicts),
            "domain_validations": domain_validations,
        }

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=status,
            domain_specs=self.domain_specs,
            cross_domain_conflicts=conflicts,
            summary=summary,
        )

    def get_combined_categories(self) -> Dict[str, Set[str]]:
        """
        Get all categories across all domains in workflow.

        Returns:
            Dictionary mapping domains to their categories
        """
        combined = {}

        for domain_id in self.get_involved_domains():
            domain = self.registry.get_domain(domain_id)
            combined[domain_id] = set(domain.get_categories())

        return combined

    def export_specification(self, format_id: str = "json") -> Dict[str, Any]:
        """
        Export the workflow specification in a specific format.

        Args:
            format_id: Format to export in (default: "json")

        Returns:
            Exported specification
        """
        if format_id != "json":
            raise ValueError(f"Format '{format_id}' not supported. Supported formats: json")

        return {
            "workflow_id": self.workflow_id,
            "created_at": datetime.now().isoformat(),
            "domains": {
                domain_id: {
                    "spec": spec.to_dict(),
                    "domain_metadata": self.registry.get_domain(domain_id).get_metadata()
                    if self.registry.has_domain(domain_id)
                    else {},
                }
                for domain_id, spec in self.domain_specs.items()
            },
        }


class WorkflowManager:
    """
    Manages multi-domain workflows.

    Provides storage, retrieval, and lifecycle management of workflows.
    """

    def __init__(self):
        """Initialize workflow manager."""
        self._workflows: Dict[str, MultiDomainWorkflow] = {}

    def create_workflow(self, workflow_id: str) -> MultiDomainWorkflow:
        """
        Create a new workflow.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            New MultiDomainWorkflow instance

        Raises:
            ValueError: If workflow ID already exists
        """
        if workflow_id in self._workflows:
            raise ValueError(f"Workflow '{workflow_id}' already exists")

        workflow = MultiDomainWorkflow(workflow_id)
        self._workflows[workflow_id] = workflow
        logger.info(f"Created workflow '{workflow_id}'")

        return workflow

    def get_workflow(self, workflow_id: str) -> MultiDomainWorkflow:
        """
        Get an existing workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            MultiDomainWorkflow instance

        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        return self._workflows[workflow_id]

    def list_workflows(self) -> List[str]:
        """Get list of all workflow IDs."""
        return list(self._workflows.keys())

    def delete_workflow(self, workflow_id: str) -> None:
        """
        Delete a workflow.

        Args:
            workflow_id: ID of the workflow to delete

        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        del self._workflows[workflow_id]
        logger.info(f"Deleted workflow '{workflow_id}'")


# Global workflow manager instance
_global_workflow_manager: WorkflowManager = WorkflowManager()


def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager."""
    return _global_workflow_manager

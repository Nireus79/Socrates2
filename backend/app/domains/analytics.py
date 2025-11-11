"""
Advanced analytics system for Socrates2 domains.

Tracks domain usage, metrics, and provides analytics and reporting capabilities.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


@dataclass
class DomainMetric:
    """Represents a single metric for domain usage."""

    domain_id: str
    metric_name: str
    metric_value: Any
    metric_type: str  # "counter", "gauge", "timer", "histogram"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "domain_id": self.domain_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_type": self.metric_type,
            "timestamp": self.timestamp,
        }


@dataclass
class WorkflowAnalytics:
    """Analytics for a single workflow."""

    workflow_id: str
    domains_involved: Set[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validated_at: str = ""
    validation_duration_ms: float = 0.0
    conflicts_detected: int = 0
    specification_questions_answered: int = 0
    specification_completeness: float = 0.0  # 0-100%
    quality_score: float = 0.0  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "workflow_id": self.workflow_id,
            "domains_involved": list(self.domains_involved),
            "created_at": self.created_at,
            "validated_at": self.validated_at,
            "validation_duration_ms": self.validation_duration_ms,
            "conflicts_detected": self.conflicts_detected,
            "specification_questions_answered": self.specification_questions_answered,
            "specification_completeness": self.specification_completeness,
            "quality_score": self.quality_score,
        }


class DomainAnalytics:
    """
    Tracks and analyzes domain usage metrics.

    Provides insights into domain adoption, question answering patterns,
    and system health.

    Usage:
        analytics = DomainAnalytics()
        analytics.track_domain_access("programming")
        analytics.track_question_answered("programming", "q1")
        report = analytics.get_domain_report("programming")
    """

    def __init__(self):
        """Initialize analytics engine."""
        self.domain_access_count: Dict[str, int] = defaultdict(int)
        self.domain_questions_answered: Dict[str, Set[str]] = defaultdict(set)
        self.domain_exports_generated: Dict[str, int] = defaultdict(int)
        self.domain_conflicts_detected: Dict[str, int] = defaultdict(int)
        self.workflow_analytics: Dict[str, WorkflowAnalytics] = {}
        self.metrics: List[DomainMetric] = []
        self.created_at = datetime.now().isoformat()

    def track_domain_access(self, domain_id: str) -> None:
        """
        Track domain access.

        Args:
            domain_id: Domain that was accessed
        """
        self.domain_access_count[domain_id] += 1
        self.metrics.append(
            DomainMetric(
                domain_id=domain_id,
                metric_name="domain_access",
                metric_value=1,
                metric_type="counter",
            )
        )
        logger.debug(f"Tracked domain access: {domain_id}")

    def track_question_answered(self, domain_id: str, question_id: str) -> None:
        """
        Track question answered in a domain.

        Args:
            domain_id: Domain containing the question
            question_id: Question ID that was answered
        """
        self.domain_questions_answered[domain_id].add(question_id)
        self.metrics.append(
            DomainMetric(
                domain_id=domain_id,
                metric_name="question_answered",
                metric_value=question_id,
                metric_type="counter",
            )
        )
        logger.debug(f"Tracked question answered: {domain_id}/{question_id}")

    def track_export_generated(self, domain_id: str, format_id: str) -> None:
        """
        Track export generation.

        Args:
            domain_id: Domain that was exported
            format_id: Export format used
        """
        self.domain_exports_generated[domain_id] += 1
        self.metrics.append(
            DomainMetric(
                domain_id=domain_id,
                metric_name="export_generated",
                metric_value=format_id,
                metric_type="counter",
            )
        )
        logger.debug(f"Tracked export generated: {domain_id}/{format_id}")

    def track_conflict_detected(self, domain_id: str, conflict_id: str) -> None:
        """
        Track conflict detection.

        Args:
            domain_id: Domain where conflict was detected
            conflict_id: Conflict ID
        """
        self.domain_conflicts_detected[domain_id] += 1
        self.metrics.append(
            DomainMetric(
                domain_id=domain_id,
                metric_name="conflict_detected",
                metric_value=conflict_id,
                metric_type="counter",
            )
        )
        logger.debug(f"Tracked conflict detected: {domain_id}/{conflict_id}")

    def track_workflow_analytics(self, analytics: WorkflowAnalytics) -> None:
        """
        Track workflow analytics.

        Args:
            analytics: Workflow analytics to track
        """
        self.workflow_analytics[analytics.workflow_id] = analytics
        logger.debug(f"Tracked workflow analytics: {analytics.workflow_id}")

    def get_domain_report(self, domain_id: str) -> Dict[str, Any]:
        """
        Get analytics report for a specific domain.

        Args:
            domain_id: Domain to report on

        Returns:
            Domain analytics report
        """
        return {
            "domain_id": domain_id,
            "access_count": self.domain_access_count.get(domain_id, 0),
            "questions_answered": len(self.domain_questions_answered.get(domain_id, set())),
            "exports_generated": self.domain_exports_generated.get(domain_id, 0),
            "conflicts_detected": self.domain_conflicts_detected.get(domain_id, 0),
        }

    def get_domain_metrics(self, domain_id: str) -> List[DomainMetric]:
        """
        Get all metrics for a domain.

        Args:
            domain_id: Domain to get metrics for

        Returns:
            List of metrics for the domain
        """
        return [m for m in self.metrics if m.domain_id == domain_id]

    def get_overall_report(self) -> Dict[str, Any]:
        """
        Get overall analytics report for all domains.

        Returns:
            Overall analytics report
        """
        total_domain_accesses = sum(self.domain_access_count.values())
        total_questions_answered = sum(len(v) for v in self.domain_questions_answered.values())
        total_exports = sum(self.domain_exports_generated.values())
        total_conflicts = sum(self.domain_conflicts_detected.values())
        domains_used = set(self.domain_access_count.keys())

        return {
            "created_at": self.created_at,
            "total_domain_accesses": total_domain_accesses,
            "total_questions_answered": total_questions_answered,
            "total_exports_generated": total_exports,
            "total_conflicts_detected": total_conflicts,
            "unique_domains_used": list(domains_used),
            "unique_domains_count": len(domains_used),
            "domain_reports": {
                domain_id: self.get_domain_report(domain_id) for domain_id in domains_used
            },
            "workflows_tracked": len(self.workflow_analytics),
        }

    def get_most_used_domains(self, limit: int = 10) -> List[tuple]:
        """
        Get most used domains.

        Args:
            limit: Maximum number of domains to return

        Returns:
            List of (domain_id, access_count) tuples sorted by usage
        """
        sorted_domains = sorted(self.domain_access_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_domains[:limit]

    def get_most_answered_questions(self, domain_id: str, limit: int = 10) -> List[str]:
        """
        Get most answered questions in a domain.

        Args:
            domain_id: Domain to analyze
            limit: Maximum number of questions to return

        Returns:
            List of question IDs
        """
        return list(self.domain_questions_answered.get(domain_id, set()))[:limit]

    def get_workflow_report(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get analytics report for a specific workflow.

        Args:
            workflow_id: Workflow to report on

        Returns:
            Workflow analytics report
        """
        if workflow_id not in self.workflow_analytics:
            return {"error": f"Workflow '{workflow_id}' not found"}

        return self.workflow_analytics[workflow_id].to_dict()

    def get_quality_summary(self) -> Dict[str, Any]:
        """
        Get quality summary across all workflows.

        Returns:
            Quality metrics summary
        """
        if not self.workflow_analytics:
            return {"average_quality_score": 0, "workflows_analyzed": 0}

        quality_scores = [w.quality_score for w in self.workflow_analytics.values()]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        average_completeness = (
            sum(w.specification_completeness for w in self.workflow_analytics.values())
            / len(self.workflow_analytics)
            if self.workflow_analytics
            else 0
        )

        return {
            "workflows_analyzed": len(self.workflow_analytics),
            "average_quality_score": round(average_quality, 2),
            "average_completeness": round(average_completeness, 2),
            "total_conflicts_across_workflows": sum(
                w.conflicts_detected for w in self.workflow_analytics.values()
            ),
        }

    def export_analytics(self, format_id: str = "json") -> Dict[str, Any]:
        """
        Export analytics in a specific format.

        Args:
            format_id: Format to export in (default: "json")

        Returns:
            Exported analytics

        Raises:
            ValueError: If format is not supported
        """
        if format_id != "json":
            raise ValueError(f"Format '{format_id}' not supported. Supported formats: json")

        return {
            "export_timestamp": datetime.now().isoformat(),
            "overall_report": self.get_overall_report(),
            "quality_summary": self.get_quality_summary(),
            "most_used_domains": [
                {"domain_id": d[0], "access_count": d[1]} for d in self.get_most_used_domains()
            ],
            "total_metrics_collected": len(self.metrics),
        }

    def clear_metrics(self) -> None:
        """Clear all collected metrics (use with caution)."""
        self.metrics.clear()
        self.domain_access_count.clear()
        self.domain_questions_answered.clear()
        self.domain_exports_generated.clear()
        self.domain_conflicts_detected.clear()
        self.workflow_analytics.clear()
        logger.warning("All analytics metrics have been cleared")


# Global analytics instance
_global_analytics: DomainAnalytics = DomainAnalytics()


def get_domain_analytics() -> DomainAnalytics:
    """Get the global domain analytics instance."""
    return _global_analytics

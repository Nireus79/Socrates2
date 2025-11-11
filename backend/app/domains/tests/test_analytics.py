"""Tests for analytics system."""

import pytest
from app.domains.analytics import (
    DomainAnalytics,
    DomainMetric,
    WorkflowAnalytics,
    get_domain_analytics,
)


class TestDomainMetric:
    """Test DomainMetric dataclass."""

    def test_create_metric(self):
        """Test creating a metric."""
        metric = DomainMetric(
            domain_id="programming",
            metric_name="domain_access",
            metric_value=1,
            metric_type="counter"
        )

        assert metric.domain_id == "programming"
        assert metric.metric_name == "domain_access"
        assert metric.metric_value == 1
        assert metric.metric_type == "counter"
        assert metric.timestamp is not None

    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        metric = DomainMetric(
            domain_id="programming",
            metric_name="domain_access",
            metric_value=1,
            metric_type="counter"
        )

        metric_dict = metric.to_dict()

        assert metric_dict["domain_id"] == "programming"
        assert metric_dict["metric_name"] == "domain_access"
        assert metric_dict["metric_value"] == 1
        assert metric_dict["metric_type"] == "counter"
        assert "timestamp" in metric_dict


class TestWorkflowAnalytics:
    """Test WorkflowAnalytics dataclass."""

    def test_create_workflow_analytics(self):
        """Test creating workflow analytics."""
        analytics = WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming", "testing"}
        )

        assert analytics.workflow_id == "wf_001"
        assert analytics.domains_involved == {"programming", "testing"}
        assert analytics.validation_duration_ms == 0.0
        assert analytics.conflicts_detected == 0
        assert analytics.quality_score == 0.0

    def test_workflow_analytics_to_dict(self):
        """Test converting workflow analytics to dictionary."""
        analytics = WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming", "testing"},
            validation_duration_ms=150.5,
            conflicts_detected=2,
            quality_score=85.5,
            specification_completeness=90.0
        )

        analytics_dict = analytics.to_dict()

        assert analytics_dict["workflow_id"] == "wf_001"
        assert "programming" in analytics_dict["domains_involved"]
        assert analytics_dict["validation_duration_ms"] == 150.5
        assert analytics_dict["conflicts_detected"] == 2
        assert analytics_dict["quality_score"] == 85.5
        assert analytics_dict["specification_completeness"] == 90.0


class TestDomainAnalytics:
    """Test DomainAnalytics functionality."""

    @pytest.fixture
    def analytics(self):
        """Create a fresh analytics instance."""
        return DomainAnalytics()

    def test_initialization(self, analytics):
        """Test analytics initialization."""
        assert analytics.domain_access_count == {}
        assert analytics.domain_questions_answered == {}
        assert analytics.domain_exports_generated == {}
        assert analytics.domain_conflicts_detected == {}
        assert analytics.workflow_analytics == {}
        assert analytics.metrics == []

    def test_track_domain_access(self, analytics):
        """Test tracking domain access."""
        analytics.track_domain_access("programming")

        assert analytics.domain_access_count["programming"] == 1
        assert len(analytics.metrics) == 1

    def test_track_multiple_accesses(self, analytics):
        """Test tracking multiple accesses."""
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_domain_access("testing")

        assert analytics.domain_access_count["programming"] == 2
        assert analytics.domain_access_count["testing"] == 1
        assert len(analytics.metrics) == 3

    def test_track_question_answered(self, analytics):
        """Test tracking answered questions."""
        analytics.track_question_answered("programming", "q1")
        analytics.track_question_answered("programming", "q2")

        assert len(analytics.domain_questions_answered["programming"]) == 2
        assert "q1" in analytics.domain_questions_answered["programming"]
        assert "q2" in analytics.domain_questions_answered["programming"]

    def test_track_export_generated(self, analytics):
        """Test tracking generated exports."""
        analytics.track_export_generated("programming", "python")
        analytics.track_export_generated("programming", "javascript")

        assert analytics.domain_exports_generated["programming"] == 2

    def test_track_conflict_detected(self, analytics):
        """Test tracking detected conflicts."""
        analytics.track_conflict_detected("programming", "conflict_001")
        analytics.track_conflict_detected("programming", "conflict_002")

        assert analytics.domain_conflicts_detected["programming"] == 2

    def test_track_workflow_analytics(self, analytics):
        """Test tracking workflow analytics."""
        workflow_analytics = WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming", "testing"}
        )

        analytics.track_workflow_analytics(workflow_analytics)

        assert "wf_001" in analytics.workflow_analytics
        assert analytics.workflow_analytics["wf_001"].workflow_id == "wf_001"

    def test_get_domain_report(self, analytics):
        """Test getting domain report."""
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_question_answered("programming", "q1")
        analytics.track_export_generated("programming", "python")
        analytics.track_conflict_detected("programming", "conf_001")

        report = analytics.get_domain_report("programming")

        assert report["domain_id"] == "programming"
        assert report["access_count"] == 2
        assert report["questions_answered"] == 1
        assert report["exports_generated"] == 1
        assert report["conflicts_detected"] == 1

    def test_get_domain_metrics(self, analytics):
        """Test getting all metrics for a domain."""
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_question_answered("programming", "q1")

        metrics = analytics.get_domain_metrics("programming")

        assert len(metrics) == 3
        assert all(m.domain_id == "programming" for m in metrics)

    def test_get_overall_report(self, analytics):
        """Test getting overall analytics report."""
        # Track multiple domains
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_domain_access("testing")
        analytics.track_question_answered("programming", "q1")
        analytics.track_question_answered("testing", "q2")
        analytics.track_export_generated("programming", "python")
        analytics.track_conflict_detected("testing", "conf_001")

        # Track a workflow
        workflow_analytics = WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming", "testing"}
        )
        analytics.track_workflow_analytics(workflow_analytics)

        report = analytics.get_overall_report()

        assert report["total_domain_accesses"] == 3
        assert report["total_questions_answered"] == 2
        assert report["total_exports_generated"] == 1
        assert report["total_conflicts_detected"] == 1
        assert report["unique_domains_count"] == 2
        assert set(report["unique_domains_used"]) == {"programming", "testing"}
        assert len(report["domain_reports"]) == 2
        assert report["workflows_tracked"] == 1

    def test_get_most_used_domains(self, analytics):
        """Test getting most used domains ranking."""
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_domain_access("testing")
        analytics.track_domain_access("testing")
        analytics.track_domain_access("architecture")

        most_used = analytics.get_most_used_domains(limit=10)

        assert len(most_used) == 3
        assert most_used[0] == ("programming", 3)
        assert most_used[1] == ("testing", 2)
        assert most_used[2] == ("architecture", 1)

    def test_get_most_used_domains_with_limit(self, analytics):
        """Test getting most used domains with limit."""
        for i in range(5):
            analytics.track_domain_access("programming")
        for i in range(4):
            analytics.track_domain_access("testing")
        for i in range(3):
            analytics.track_domain_access("architecture")
        for i in range(2):
            analytics.track_domain_access("data_engineering")

        most_used = analytics.get_most_used_domains(limit=2)

        assert len(most_used) == 2
        assert most_used[0][0] == "programming"
        assert most_used[1][0] == "testing"

    def test_get_most_answered_questions(self, analytics):
        """Test getting most answered questions."""
        analytics.track_question_answered("programming", "q1")
        analytics.track_question_answered("programming", "q2")
        analytics.track_question_answered("programming", "q3")
        analytics.track_question_answered("testing", "q4")

        questions = analytics.get_most_answered_questions("programming", limit=10)

        assert len(questions) == 3
        assert "q1" in questions
        assert "q2" in questions
        assert "q3" in questions

    def test_get_workflow_report(self, analytics):
        """Test getting workflow report."""
        workflow_analytics = WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming", "testing"},
            validation_duration_ms=250.0,
            conflicts_detected=1,
            quality_score=85.0
        )
        analytics.track_workflow_analytics(workflow_analytics)

        report = analytics.get_workflow_report("wf_001")

        assert report["workflow_id"] == "wf_001"
        assert "programming" in report["domains_involved"]
        assert report["validation_duration_ms"] == 250.0
        assert report["conflicts_detected"] == 1
        assert report["quality_score"] == 85.0

    def test_get_workflow_report_not_found(self, analytics):
        """Test getting non-existent workflow report."""
        report = analytics.get_workflow_report("nonexistent")

        assert "error" in report
        assert "not found" in report["error"]

    def test_get_quality_summary_empty(self, analytics):
        """Test getting quality summary when no workflows tracked."""
        summary = analytics.get_quality_summary()

        assert summary["workflows_analyzed"] == 0
        assert summary["average_quality_score"] == 0
        # When empty, only these keys are returned
        assert "average_completeness" not in summary or summary.get("average_completeness", 0) == 0

    def test_get_quality_summary(self, analytics):
        """Test getting quality summary with workflows."""
        analytics.track_workflow_analytics(WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming"},
            quality_score=90.0,
            specification_completeness=85.0,
            conflicts_detected=1
        ))
        analytics.track_workflow_analytics(WorkflowAnalytics(
            workflow_id="wf_002",
            domains_involved={"testing"},
            quality_score=80.0,
            specification_completeness=75.0,
            conflicts_detected=2
        ))

        summary = analytics.get_quality_summary()

        assert summary["workflows_analyzed"] == 2
        assert summary["average_quality_score"] == 85.0
        assert summary["average_completeness"] == 80.0
        assert summary["total_conflicts_across_workflows"] == 3

    def test_export_analytics_json(self, analytics):
        """Test exporting analytics as JSON."""
        analytics.track_domain_access("programming")
        analytics.track_question_answered("programming", "q1")
        analytics.track_workflow_analytics(WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming"},
            quality_score=85.0
        ))

        exported = analytics.export_analytics("json")

        assert "export_timestamp" in exported
        assert "overall_report" in exported
        assert "quality_summary" in exported
        assert "most_used_domains" in exported
        assert "total_metrics_collected" in exported
        # Each track_* call creates a metric: domain_access + question_answered = 2
        assert exported["total_metrics_collected"] == 2

    def test_export_analytics_unsupported_format(self, analytics):
        """Test exporting unsupported format raises error."""
        with pytest.raises(ValueError):
            analytics.export_analytics("xml")

    def test_clear_metrics(self, analytics):
        """Test clearing all metrics."""
        analytics.track_domain_access("programming")
        analytics.track_question_answered("programming", "q1")
        analytics.track_workflow_analytics(WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming"}
        ))

        assert len(analytics.metrics) == 2
        assert len(analytics.domain_access_count) > 0

        analytics.clear_metrics()

        assert len(analytics.metrics) == 0
        assert len(analytics.domain_access_count) == 0
        assert len(analytics.domain_questions_answered) == 0
        assert len(analytics.domain_exports_generated) == 0
        assert len(analytics.domain_conflicts_detected) == 0
        assert len(analytics.workflow_analytics) == 0


class TestGlobalAnalyticsInstance:
    """Test global analytics instance."""

    def test_get_domain_analytics_singleton(self):
        """Test that get_domain_analytics returns singleton."""
        analytics1 = get_domain_analytics()
        analytics2 = get_domain_analytics()

        assert analytics1 is analytics2

    def test_global_analytics_persistence(self):
        """Test that global analytics persists data across calls."""
        analytics = get_domain_analytics()

        # Clear any existing data
        analytics.clear_metrics()

        # Track something
        analytics.track_domain_access("programming")

        # Get analytics again and verify data persisted
        analytics2 = get_domain_analytics()
        assert analytics2.domain_access_count["programming"] == 1


class TestAnalyticsIntegration:
    """Integration tests for analytics system."""

    def test_complete_analytics_workflow(self):
        """Test complete analytics workflow."""
        analytics = DomainAnalytics()

        # Simulate multi-domain workflow
        # Domain 1: Programming
        analytics.track_domain_access("programming")
        analytics.track_domain_access("programming")
        analytics.track_question_answered("programming", "q1")
        analytics.track_question_answered("programming", "q2")
        analytics.track_export_generated("programming", "python")
        analytics.track_export_generated("programming", "javascript")

        # Domain 2: Testing
        analytics.track_domain_access("testing")
        analytics.track_question_answered("testing", "q3")
        analytics.track_export_generated("testing", "pytest")
        analytics.track_conflict_detected("testing", "conf_001")

        # Domain 3: Architecture
        analytics.track_domain_access("architecture")
        analytics.track_conflict_detected("architecture", "conf_002")
        analytics.track_conflict_detected("architecture", "conf_003")

        # Track workflow
        workflow_analytics = WorkflowAnalytics(
            workflow_id="wf_001",
            domains_involved={"programming", "testing", "architecture"},
            validation_duration_ms=350.5,
            conflicts_detected=3,
            specification_questions_answered=3,
            specification_completeness=75.0,
            quality_score=80.0
        )
        analytics.track_workflow_analytics(workflow_analytics)

        # Verify overall report
        overall = analytics.get_overall_report()
        assert overall["total_domain_accesses"] == 4
        assert overall["total_questions_answered"] == 3
        assert overall["total_exports_generated"] == 3
        assert overall["total_conflicts_detected"] == 3
        assert overall["unique_domains_count"] == 3
        assert overall["workflows_tracked"] == 1

        # Verify domain reports
        prog_report = analytics.get_domain_report("programming")
        assert prog_report["access_count"] == 2
        assert prog_report["questions_answered"] == 2
        assert prog_report["exports_generated"] == 2

        # Verify most used domains
        most_used = analytics.get_most_used_domains(limit=5)
        assert most_used[0][0] == "programming"
        assert most_used[0][1] == 2

        # Verify workflow report
        workflow_report = analytics.get_workflow_report("wf_001")
        assert workflow_report["quality_score"] == 80.0
        assert workflow_report["conflicts_detected"] == 3

        # Verify quality summary
        quality = analytics.get_quality_summary()
        assert quality["workflows_analyzed"] == 1
        assert quality["average_quality_score"] == 80.0
        assert quality["average_completeness"] == 75.0

        # Verify export
        exported = analytics.export_analytics("json")
        assert "overall_report" in exported
        assert "quality_summary" in exported
        # Metrics: 2 domain_accesses + 2 questions + 2 exports (programming)
        # + 1 access + 1 question + 1 export + 1 conflict (testing)
        # + 1 access + 2 conflicts (architecture) = 13 total
        assert exported["total_metrics_collected"] == 13

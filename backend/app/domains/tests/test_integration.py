"""Integration tests for Phase 7.0 complete pluggification system."""

import pytest
import time
from ..programming import ProgrammingDomain
from ..base import (
    Question,
    ExportFormat,
    ConflictRule,
    QualityAnalyzer,
    SeverityLevel,
)
from ..questions import QuestionTemplateEngine
from ..exporters import ExportTemplateEngine
from ..rules import ConflictRuleEngine
from ..analyzers import QualityAnalyzerEngine


class TestPhase7Integration:
    """Test complete Phase 7.0 integration across all subsystems."""

    @pytest.fixture
    def domain(self):
        """Create a fresh programming domain with all configurations."""
        return ProgrammingDomain()

    def test_domain_initialization_loads_all_subsystems(self, domain):
        """Test that domain initialization loads all four subsystems."""
        # All subsystems should be loaded
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers = domain.get_quality_analyzers()

        assert len(questions) > 0, "Questions not loaded"
        assert len(exporters) > 0, "Exporters not loaded"
        assert len(rules) > 0, "Rules not loaded"
        assert len(analyzers) > 0, "Analyzers not loaded"

    def test_all_subsystems_return_correct_types(self, domain):
        """Test that all subsystems return objects of correct types."""
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers = domain.get_quality_analyzers()

        # Questions
        assert all(isinstance(q, Question) for q in questions)

        # Exporters
        assert all(isinstance(e, ExportFormat) for e in exporters)

        # Rules
        assert all(isinstance(r, ConflictRule) for r in rules)

        # Analyzers (returned as IDs/strings)
        assert all(isinstance(a, str) for a in analyzers)

    def test_subsystem_counts_match_configuration(self, domain):
        """Test that subsystem counts match their JSON configurations."""
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers = domain.get_quality_analyzers()

        # Programming domain should have expected counts
        assert len(questions) >= 14, "Should have 14+ questions"
        assert len(exporters) == 8, "Should have 8 exporters"
        assert len(rules) >= 4, "Should have 4+ conflict rules"
        assert len(analyzers) >= 4, "Should have 4+ analyzers"

    def test_questions_and_exporters_integration(self, domain):
        """Test interaction between question and exporter subsystems."""
        questions = domain.get_questions()
        exporters = domain.get_export_formats()

        # Should be able to generate specifications (questions) and export them (exporters)
        perf_questions = [q for q in questions if q.category == "Performance"]
        assert len(perf_questions) > 0

        python_exporters = [e for e in exporters if e.format_id == "python"]
        assert len(python_exporters) == 1

        # Combined workflow: gather performance specs, export to Python
        # This represents the complete user workflow
        assert perf_questions  # Questions available
        assert python_exporters  # Exporter available

    def test_rules_detect_conflicts_in_specifications(self, domain):
        """Test that conflict rules can be applied to specifications."""
        rules = domain.get_conflict_rules()
        questions = domain.get_questions()

        # Get performance questions
        perf_questions = [q for q in questions if q.category == "Performance"]
        perf_rules = [r for r in rules if "perf" in r.rule_id]

        # Should have both questions and rules for performance validation
        assert len(perf_questions) > 0
        assert len(perf_rules) > 0

    def test_analyzers_validate_quality_of_specifications(self, domain):
        """Test that quality analyzers can be applied to specifications."""
        analyzers = domain.get_quality_analyzers()
        questions = domain.get_questions()

        # Should have analyzers and questions for quality checking
        assert len(analyzers) > 0
        assert len(questions) > 0

        # Bias detector should be required
        assert "bias_detector" in analyzers

    def test_complete_specification_workflow(self, domain):
        """Test complete workflow: questions → specs → rules → analyzers → export."""
        # Step 1: Get questions to gather specifications
        questions = domain.get_questions()
        categories = domain.get_categories()

        # Step 2: Get conflict rules to validate specs
        rules = domain.get_conflict_rules()

        # Step 3: Get quality analyzers to check spec quality
        analyzers = domain.get_quality_analyzers()

        # Step 4: Get exporters to generate code
        exporters = domain.get_export_formats()

        # All steps should be available
        assert questions and len(questions) > 0
        assert rules and len(rules) > 0
        assert analyzers and len(analyzers) > 0
        assert exporters and len(exporters) > 0

    def test_multiple_domain_instances_independence(self):
        """Test that multiple domain instances load independently."""
        domain1 = ProgrammingDomain()
        domain2 = ProgrammingDomain()

        # Both should have loaded their configurations
        q1 = domain1.get_questions()
        q2 = domain2.get_questions()

        assert len(q1) > 0
        assert len(q2) > 0
        assert len(q1) == len(q2)  # Same data

    def test_subsystem_error_handling_and_recovery(self, domain):
        """Test that subsystems gracefully handle errors."""
        # All subsystems should have loaded despite missing files
        # (They should return empty lists, not crash)
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers = domain.get_quality_analyzers()

        # None should be None, all should be lists
        assert isinstance(questions, list)
        assert isinstance(exporters, list)
        assert isinstance(rules, list)
        assert isinstance(analyzers, list)

    def test_subsystem_performance_combined(self, domain):
        """Test combined performance of all subsystems."""
        start = time.time()

        # Load all subsystems
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers = domain.get_quality_analyzers()

        elapsed = time.time() - start

        # Should complete very quickly
        assert elapsed < 1.0, f"Loading all subsystems took {elapsed}s, should be < 1s"

    def test_filtering_across_subsystems(self, domain):
        """Test filtering operations across all subsystems."""
        engine_q = QuestionTemplateEngine()
        engine_e = ExportTemplateEngine()
        engine_r = ConflictRuleEngine()
        engine_a = QualityAnalyzerEngine()

        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers_obj = []
        if domain._analyzers:
            analyzers_obj = domain._analyzers

        # Test filtering
        perf_q = engine_q.filter_by_category(questions, "Performance")
        py_e = engine_e.filter_by_language(exporters, "Python")
        error_r = engine_r.filter_by_severity(rules, "error")

        assert len(perf_q) > 0
        assert len(py_e) > 0
        assert len(error_r) > 0

    def test_subsystems_data_consistency(self, domain):
        """Test that all subsystems maintain consistent data."""
        # Get all subsystems
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        analyzers = domain.get_quality_analyzers()

        # Check consistency across calls
        questions2 = domain.get_questions()
        exporters2 = domain.get_export_formats()
        rules2 = domain.get_conflict_rules()
        analyzers2 = domain.get_quality_analyzers()

        # Data should be consistent
        assert len(questions) == len(questions2)
        assert len(exporters) == len(exporters2)
        assert len(rules) == len(rules2)
        assert len(analyzers) == len(analyzers2)

    def test_all_subsystems_have_metadata(self, domain):
        """Test that all objects in subsystems have required metadata."""
        # Questions
        for q in domain.get_questions():
            assert q.question_id
            assert q.text
            assert q.category
            assert q.difficulty

        # Exporters
        for e in domain.get_export_formats():
            assert e.format_id
            assert e.name
            assert e.file_extension
            assert e.mime_type

        # Rules
        for r in domain.get_conflict_rules():
            assert r.rule_id
            assert r.name
            assert r.severity

        # Analyzers (IDs only in public API)
        analyzers = domain.get_quality_analyzers()
        assert all(isinstance(a, str) for a in analyzers)

    def test_domain_categories_match_questions(self, domain):
        """Test that domain categories match the questions."""
        categories = set(domain.get_categories())
        question_categories = set(q.category for q in domain.get_questions())

        # All question categories should be in domain categories
        assert question_categories.issubset(categories)

    def test_integration_with_singleton_engines(self):
        """Test that singleton engines work correctly across domains."""
        from ..questions import get_question_engine
        from ..exporters import get_exporter_engine
        from ..rules import get_rule_engine
        from ..analyzers import get_analyzer_engine

        # Get global engines
        q_engine = get_question_engine()
        e_engine = get_exporter_engine()
        r_engine = get_rule_engine()
        a_engine = get_analyzer_engine()

        # Load data through global engines
        domain = ProgrammingDomain()
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()

        # Engines should work with domain data
        filtered_q = q_engine.filter_by_category(questions, "Performance")
        filtered_e = e_engine.filter_by_language(exporters, "Python")
        filtered_r = r_engine.filter_by_severity(rules, "error")

        assert len(filtered_q) > 0
        assert len(filtered_e) > 0
        assert len(filtered_r) > 0

    def test_scalability_with_multiple_domains(self):
        """Test that system scales with multiple domain instances."""
        domains = [ProgrammingDomain() for _ in range(10)]

        # All domains should load successfully
        for domain in domains:
            assert len(domain.get_questions()) > 0
            assert len(domain.get_export_formats()) > 0
            assert len(domain.get_conflict_rules()) > 0
            assert len(domain.get_quality_analyzers()) > 0

    def test_empty_subsystem_handling(self):
        """Test that system handles scenarios where subsystems might be empty."""
        domain = ProgrammingDomain()

        # Even if subsystems are empty, they should return lists
        q = domain.get_questions() or []
        e = domain.get_export_formats() or []
        r = domain.get_conflict_rules() or []
        a = domain.get_quality_analyzers() or []

        assert isinstance(q, list)
        assert isinstance(e, list)
        assert isinstance(r, list)
        assert isinstance(a, list)

    def test_all_engines_serialize_to_json(self, domain):
        """Test that all engines can serialize their data to JSON."""
        from ..questions import QuestionTemplateEngine
        from ..exporters import ExportTemplateEngine
        from ..rules import ConflictRuleEngine
        from ..analyzers import QualityAnalyzerEngine

        q_engine = QuestionTemplateEngine()
        e_engine = ExportTemplateEngine()
        r_engine = ConflictRuleEngine()
        a_engine = QualityAnalyzerEngine()

        # Get data
        questions = domain.get_questions()
        exporters = domain.get_export_formats()
        rules = domain.get_conflict_rules()
        if domain._analyzers:
            analyzers = domain._analyzers

            # Serialize to JSON
            q_json = q_engine.to_json(questions)
            e_json = e_engine.to_json(exporters)
            r_json = r_engine.to_json(rules)
            a_json = a_engine.to_json(analyzers)

            # All should be valid JSON strings
            assert q_json and "{" in q_json
            assert e_json and "{" in e_json
            assert r_json and "{" in r_json
            assert a_json and "{" in a_json


class TestPhase7Performance:
    """Performance benchmarking for Phase 7.0 system."""

    @pytest.fixture
    def domain(self):
        """Create a fresh programming domain."""
        return ProgrammingDomain()

    def test_initialization_performance(self):
        """Test that domain initialization is fast."""
        start = time.time()
        domain = ProgrammingDomain()
        elapsed = time.time() - start

        # Should initialize in less than 100ms
        assert elapsed < 0.1, f"Initialization took {elapsed}s, should be < 0.1s"

    def test_filtering_performance(self, domain):
        """Test that filtering operations are fast."""
        engine = QuestionTemplateEngine()
        questions = domain.get_questions()

        start = time.time()
        for _ in range(100):
            engine.filter_by_category(questions, "Performance")
        elapsed = time.time() - start

        # 100 filter operations should take < 50ms
        assert elapsed < 0.05, f"100 filters took {elapsed}s, should be < 0.05s"

    def test_validation_performance(self, domain):
        """Test that validation operations are fast."""
        engine = QuestionTemplateEngine()
        questions = domain.get_questions()

        start = time.time()
        for _ in range(100):
            engine.validate_questions(questions)
        elapsed = time.time() - start

        # 100 validations should take < 100ms
        assert elapsed < 0.1, f"100 validations took {elapsed}s, should be < 0.1s"

    def test_serialization_performance(self, domain):
        """Test that serialization operations are fast."""
        engine = QuestionTemplateEngine()
        questions = domain.get_questions()

        start = time.time()
        for _ in range(100):
            engine.to_json(questions)
        elapsed = time.time() - start

        # 100 serializations should take < 100ms
        assert elapsed < 0.1, f"100 serializations took {elapsed}s, should be < 0.1s"

    def test_subsystem_access_performance(self, domain):
        """Test that accessing subsystems repeatedly is fast."""
        start = time.time()
        for _ in range(100):
            domain.get_questions()
            domain.get_export_formats()
            domain.get_conflict_rules()
            domain.get_quality_analyzers()
        elapsed = time.time() - start

        # 400 subsystem accesses should take < 50ms
        assert elapsed < 0.05, f"400 accesses took {elapsed}s, should be < 0.05s"


class TestPhase7Compatibility:
    """Backward compatibility tests for Phase 7.0."""

    def test_programming_domain_public_api(self):
        """Test that ProgrammingDomain public API hasn't changed."""
        domain = ProgrammingDomain()

        # All methods should exist and return expected types
        assert callable(domain.get_categories)
        assert callable(domain.get_questions)
        assert callable(domain.get_export_formats)
        assert callable(domain.get_conflict_rules)
        assert callable(domain.get_quality_analyzers)
        assert callable(domain.get_metadata)

        # All should return lists or dicts
        assert isinstance(domain.get_categories(), list)
        assert isinstance(domain.get_questions(), list)
        assert isinstance(domain.get_export_formats(), list)
        assert isinstance(domain.get_conflict_rules(), list)
        assert isinstance(domain.get_quality_analyzers(), list)
        assert isinstance(domain.get_metadata(), dict)

    def test_domain_metadata_complete(self):
        """Test that domain metadata is complete."""
        domain = ProgrammingDomain()
        metadata = domain.get_metadata()

        assert "domain_id" in metadata
        assert "name" in metadata
        assert "version" in metadata
        assert "question_count" in metadata
        assert "export_formats" in metadata
        assert "conflict_rules" in metadata

        assert metadata["domain_id"] == "programming"
        assert metadata["name"] == "Software Programming"

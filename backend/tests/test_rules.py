"""Tests for conflict rule engine."""

import json

import pytest

from app.base import ConflictRule, SeverityLevel
from app.rules import ConflictRuleEngine, get_rule_engine


class TestConflictRuleEngine:
    """Test ConflictRuleEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create a fresh rule engine."""
        return ConflictRuleEngine()

    @pytest.fixture
    def sample_rules_data(self):
        """Sample rule data for testing."""
        return [
            {
                "rule_id": "perf_conflict",
                "name": "Performance Consistency",
                "description": "Response time requirements must be consistent",
                "condition": "response_time specs must not contradict",
                "severity": "error",
                "message": "Conflicting response time specs",
            },
            {
                "rule_id": "sec_conflict",
                "name": "Security Consistency",
                "description": "Security standards must align",
                "condition": "encryption specs must be compatible",
                "severity": "error",
                "message": "Conflicting security specs",
            },
            {
                "rule_id": "scale_warning",
                "name": "Scalability Planning",
                "description": "Scalability approach must be feasible",
                "condition": "throughput and resources must align",
                "severity": "warning",
                "message": "Scalability specs may be unrealistic",
            },
        ]

    def test_load_rules_from_dict(self, engine, sample_rules_data):
        """Test loading rules from dictionary."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        assert len(rules) == 3
        assert rules[0].rule_id == "perf_conflict"
        assert rules[1].severity == SeverityLevel.ERROR
        assert rules[2].severity == SeverityLevel.WARNING

    def test_load_rules_invalid_data(self, engine):
        """Test loading rule with missing required fields."""
        invalid_data = [{"rule_id": "perf_conflict"}]  # Missing required fields
        # This will load but with None values, which should be caught by validation
        rules = engine.load_rules_from_dict(invalid_data)
        errors = engine.validate_rules(rules)
        assert len(errors) > 0  # Should have validation errors

    def test_filter_by_severity_error(self, engine, sample_rules_data):
        """Test filtering rules by error severity."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        error_rules = engine.filter_by_severity(rules, "error")
        assert len(error_rules) == 2
        assert all(r.severity == SeverityLevel.ERROR for r in error_rules)

    def test_filter_by_severity_warning(self, engine, sample_rules_data):
        """Test filtering rules by warning severity."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        warning_rules = engine.filter_by_severity(rules, "warning")
        assert len(warning_rules) == 1
        assert warning_rules[0].severity == SeverityLevel.WARNING

    def test_filter_by_severity_case_insensitive(self, engine, sample_rules_data):
        """Test severity filter is case insensitive."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        error_rules = engine.filter_by_severity(rules, "ERROR")
        assert len(error_rules) == 2

    def test_filter_by_category(self, engine, sample_rules_data):
        """Test filtering rules by category."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        perf_rules = engine.filter_by_category(rules, "perf")
        assert len(perf_rules) == 1
        assert perf_rules[0].rule_id == "perf_conflict"

    def test_filter_by_category_multiple_matches(self, engine):
        """Test filtering category with multiple rules."""
        data = [
            {
                "rule_id": "perf_response",
                "name": "Response Time",
                "description": "Response time rules",
                "condition": "test",
                "severity": "error",
                "message": "test",
            },
            {
                "rule_id": "perf_throughput",
                "name": "Throughput",
                "description": "Throughput rules",
                "condition": "test",
                "severity": "error",
                "message": "test",
            },
        ]
        rules = engine.load_rules_from_dict(data)
        perf_rules = engine.filter_by_category(rules, "perf")
        assert len(perf_rules) == 2

    def test_filter_by_pattern(self, engine, sample_rules_data):
        """Test filtering rules by pattern matching."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        consistency_rules = engine.filter_by_pattern(rules, "consistency")
        assert len(consistency_rules) == 2
        assert all("Consistency" in r.name for r in consistency_rules)

    def test_filter_by_pattern_case_insensitive(self, engine, sample_rules_data):
        """Test pattern filter is case insensitive."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        consistency_rules = engine.filter_by_pattern(rules, "CONSISTENCY")
        assert len(consistency_rules) == 2

    def test_filter_by_pattern_description(self, engine, sample_rules_data):
        """Test pattern matching in description."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        must_rules = engine.filter_by_pattern(rules, "must")
        assert len(must_rules) >= 2

    def test_validate_rules_success(self, engine, sample_rules_data):
        """Test validating correct rules."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        errors = engine.validate_rules(rules)
        assert len(errors) == 0

    def test_validate_rules_duplicate_ids(self, engine):
        """Test validation catches duplicate rule IDs."""
        data = [
            {
                "rule_id": "perf_conflict",
                "name": "Performance",
                "description": "Description",
                "condition": "condition",
                "severity": "error",
                "message": "message",
            },
            {
                "rule_id": "perf_conflict",
                "name": "Performance 2",
                "description": "Description 2",
                "condition": "condition 2",
                "severity": "error",
                "message": "message 2",
            },
        ]
        rules = engine.load_rules_from_dict(data)
        errors = engine.validate_rules(rules)
        assert any("Duplicate" in e for e in errors)

    def test_validate_rules_missing_fields(self, engine):
        """Test validation catches missing required fields."""
        data = [
            {
                "rule_id": "perf_conflict",
                "name": "Performance",
                # Missing description
                "condition": "condition",
                "severity": "error",
                "message": "message",
            },
        ]
        rules = engine.load_rules_from_dict(data)
        errors = engine.validate_rules(rules)
        assert any("missing description" in e for e in errors)

    def test_validate_rules_all_fields_missing(self, engine):
        """Test validation catches all missing required fields."""
        data = [
            {
                "rule_id": "perf_conflict",
                # Missing name, description, condition, severity, message
            },
        ]
        rules = engine.load_rules_from_dict(data)
        errors = engine.validate_rules(rules)
        assert len(errors) >= 4  # At least 4 missing fields

    def test_get_rules_by_category(self, engine, sample_rules_data):
        """Test grouping rules by category."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        categories = engine.get_rules_by_category(rules)
        assert "perf" in categories
        assert "sec" in categories
        assert "scale" in categories
        assert len(categories["perf"]) == 1

    def test_get_rules_by_severity(self, engine, sample_rules_data):
        """Test grouping rules by severity."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        severity_groups = engine.get_rules_by_severity(rules)
        assert "error" in severity_groups
        assert "warning" in severity_groups
        assert len(severity_groups["error"]) == 2
        assert len(severity_groups["warning"]) == 1

    def test_get_rules_by_severity_only_errors(self, engine):
        """Test severity grouping with only error rules."""
        data = [
            {
                "rule_id": "rule1",
                "name": "Rule 1",
                "description": "Description",
                "condition": "condition",
                "severity": "error",
                "message": "message",
            },
        ]
        rules = engine.load_rules_from_dict(data)
        severity_groups = engine.get_rules_by_severity(rules)
        assert "error" in severity_groups
        assert "warning" not in severity_groups  # Empty group removed

    def test_to_dict(self, engine, sample_rules_data):
        """Test converting rules to dict."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        dict_list = engine.to_dict(rules)
        assert len(dict_list) == 3
        assert dict_list[0]["rule_id"] == "perf_conflict"
        assert dict_list[2]["severity"] == "warning"

    def test_to_json(self, engine, sample_rules_data):
        """Test converting rules to JSON."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        json_str = engine.to_json(rules)
        parsed = json.loads(json_str)
        assert len(parsed) == 3
        assert parsed[0]["rule_id"] == "perf_conflict"

    def test_save_and_load_json(self, engine, sample_rules_data, tmp_path):
        """Test saving and loading rules from JSON."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        filepath = tmp_path / "rules.json"

        # Save
        engine.save_to_json(rules, str(filepath))
        assert filepath.exists()

        # Load
        loaded_rules = engine.load_rules_from_json(str(filepath))
        assert len(loaded_rules) == 3
        assert loaded_rules[0].rule_id == "perf_conflict"
        assert loaded_rules[2].severity == SeverityLevel.WARNING

    def test_load_rules_from_json_invalid_file(self, engine):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            engine.load_rules_from_json("/nonexistent/path.json")

    def test_load_rules_from_json_not_array(self, engine, tmp_path):
        """Test loading from JSON that isn't an array raises error."""
        filepath = tmp_path / "rules.json"
        filepath.write_text('{"rule_id": "perf_conflict"}')  # Object, not array
        with pytest.raises(ValueError):
            engine.load_rules_from_json(str(filepath))

    def test_rule_format_fields(self, engine, sample_rules_data):
        """Test ConflictRule fields are properly set."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        rule = rules[0]
        assert rule.rule_id == "perf_conflict"
        assert rule.name == "Performance Consistency"
        assert rule.description == "Response time requirements must be consistent"
        assert rule.condition == "response_time specs must not contradict"
        assert rule.severity == SeverityLevel.ERROR
        assert rule.message == "Conflicting response time specs"

    def test_severity_levels_all_present(self, engine):
        """Test engine handles all severity levels."""
        data = [
            {
                "rule_id": "error_rule",
                "name": "Error Rule",
                "description": "desc",
                "condition": "cond",
                "severity": "error",
                "message": "msg",
            },
            {
                "rule_id": "warning_rule",
                "name": "Warning Rule",
                "description": "desc",
                "condition": "cond",
                "severity": "warning",
                "message": "msg",
            },
            {
                "rule_id": "info_rule",
                "name": "Info Rule",
                "description": "desc",
                "condition": "cond",
                "severity": "info",
                "message": "msg",
            },
        ]
        rules = engine.load_rules_from_dict(data)
        assert len(rules) == 3
        severities = {r.severity for r in rules}
        assert SeverityLevel.ERROR in severities
        assert SeverityLevel.WARNING in severities
        assert SeverityLevel.INFO in severities

    def test_filter_chain_severity_then_category(self, engine, sample_rules_data):
        """Test chaining multiple filters."""
        rules = engine.load_rules_from_dict(sample_rules_data)
        # Filter by error severity
        error_rules = engine.filter_by_severity(rules, "error")
        # Then by perf category
        perf_errors = engine.filter_by_category(error_rules, "perf")
        assert len(perf_errors) == 1
        assert perf_errors[0].rule_id == "perf_conflict"

    def test_large_rule_set(self, engine):
        """Test engine handles large number of rules efficiently."""
        data = [
            {
                "rule_id": f"rule_{i}",
                "name": f"Rule {i}",
                "description": f"Rule {i} description",
                "condition": f"Rule {i} condition",
                "severity": "error" if i % 2 == 0 else "warning",
                "message": f"Rule {i} message",
            }
            for i in range(50)
        ]
        rules = engine.load_rules_from_dict(data)
        assert len(rules) == 50
        errors = engine.validate_rules(rules)
        assert len(errors) == 0

    def test_multiple_rules_same_category(self, engine):
        """Test grouping multiple rules in same category."""
        data = [
            {
                "rule_id": "perf_response",
                "name": "Response Time",
                "description": "desc",
                "condition": "cond",
                "severity": "error",
                "message": "msg",
            },
            {
                "rule_id": "perf_throughput",
                "name": "Throughput",
                "description": "desc",
                "condition": "cond",
                "severity": "error",
                "message": "msg",
            },
            {
                "rule_id": "perf_memory",
                "name": "Memory",
                "description": "desc",
                "condition": "cond",
                "severity": "warning",
                "message": "msg",
            },
        ]
        rules = engine.load_rules_from_dict(data)
        categories = engine.get_rules_by_category(rules)
        assert len(categories["perf"]) == 3


class TestGlobalRuleEngine:
    """Test global rule engine instance."""

    def test_get_rule_engine_singleton(self):
        """Test that get_rule_engine returns singleton."""
        engine1 = get_rule_engine()
        engine2 = get_rule_engine()
        assert engine1 is engine2


class TestProgrammingDomainRules:
    """Test programming domain rule loading."""

    def test_programming_rules_load(self):
        """Test that programming rules load correctly."""
        engine = ConflictRuleEngine()
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        rules = domain.get_conflict_rules()

        assert len(rules) >= 4
        assert all(isinstance(r, ConflictRule) for r in rules)

    def test_programming_rules_have_required_fields(self):
        """Test that all rules have required fields."""
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        rules = domain.get_conflict_rules()

        for rule in rules:
            assert rule.rule_id
            assert rule.name
            assert rule.description
            assert rule.condition
            assert rule.message
            assert rule.severity

    def test_programming_rules_unique_ids(self):
        """Test that all rule IDs are unique."""
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        rules = domain.get_conflict_rules()
        rule_ids = [r.rule_id for r in rules]
        assert len(rule_ids) == len(set(rule_ids))

    def test_programming_rules_validation(self):
        """Test that rules configuration validates correctly."""
        engine = ConflictRuleEngine()
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        rules = domain.get_conflict_rules()
        errors = engine.validate_rules(rules)

        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_programming_rules_have_severity_levels(self):
        """Test that rules have appropriate severity levels."""
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        rules = domain.get_conflict_rules()

        severities = {r.severity for r in rules}
        # Should have at least one error and one warning
        assert any(r.severity == SeverityLevel.ERROR for r in rules)

    def test_programming_rules_categories(self):
        """Test that rules span multiple categories."""
        from app.programming import ProgrammingDomain

        domain = ProgrammingDomain()
        rules = domain.get_conflict_rules()
        engine = ConflictRuleEngine()
        categories = engine.get_rules_by_category(rules)

        # Should have at least 2 different categories
        assert len(categories) >= 2

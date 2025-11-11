"""Tests for quality analyzer engine."""

import pytest
import json
from pathlib import Path
from ..analyzers import QualityAnalyzerEngine, get_analyzer_engine
from ..base import QualityAnalyzer


class TestQualityAnalyzerEngine:
    """Test QualityAnalyzerEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create a fresh analyzer engine."""
        return QualityAnalyzerEngine()

    @pytest.fixture
    def sample_analyzers_data(self):
        """Sample analyzer data for testing."""
        return [
            {
                "analyzer_id": "bias_detector",
                "name": "Bias Detector",
                "description": "Detects potential bias in specifications",
                "analyzer_type": "bias_detector",
                "enabled": True,
                "required": True,
                "tags": ["universal"],
            },
            {
                "analyzer_id": "performance_validator",
                "name": "Performance Validator",
                "description": "Validates performance specifications",
                "analyzer_type": "performance_validator",
                "enabled": True,
                "required": False,
                "tags": ["programming", "performance"],
            },
            {
                "analyzer_id": "security_validator",
                "name": "Security Validator",
                "description": "Validates security requirements",
                "analyzer_type": "security_validator",
                "enabled": False,
                "required": False,
                "tags": ["programming", "security"],
            },
        ]

    def test_load_analyzers_from_dict(self, engine, sample_analyzers_data):
        """Test loading analyzers from dictionary."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        assert len(analyzers) == 3
        assert analyzers[0].analyzer_id == "bias_detector"
        assert analyzers[1].required is False
        assert analyzers[2].enabled is False

    def test_load_analyzers_invalid_data(self, engine):
        """Test loading analyzer with missing required fields."""
        invalid_data = [{"analyzer_id": "bias_detector"}]  # Missing required fields
        analyzers = engine.load_analyzers_from_dict(invalid_data)
        errors = engine.validate_analyzers(analyzers)
        assert len(errors) > 0  # Should have validation errors

    def test_filter_by_enabled(self, engine, sample_analyzers_data):
        """Test filtering analyzers by enabled status."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        enabled = engine.filter_by_enabled(analyzers, True)
        assert len(enabled) == 2
        assert all(a.enabled for a in enabled)

    def test_filter_by_disabled(self, engine, sample_analyzers_data):
        """Test filtering for disabled analyzers."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        disabled = engine.filter_by_enabled(analyzers, False)
        assert len(disabled) == 1
        assert disabled[0].analyzer_id == "security_validator"

    def test_filter_by_required(self, engine, sample_analyzers_data):
        """Test filtering analyzers by required status."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        required = engine.filter_by_required(analyzers, True)
        assert len(required) == 1
        assert required[0].analyzer_id == "bias_detector"

    def test_filter_by_optional(self, engine, sample_analyzers_data):
        """Test filtering for optional analyzers."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        optional = engine.filter_by_required(analyzers, False)
        assert len(optional) == 2
        assert all(not a.required for a in optional)

    def test_filter_by_tag(self, engine, sample_analyzers_data):
        """Test filtering analyzers by tag."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        programming = engine.filter_by_tag(analyzers, "programming")
        assert len(programming) == 2
        assert all("programming" in a.tags for a in programming)

    def test_filter_by_tag_universal(self, engine, sample_analyzers_data):
        """Test filtering by universal tag."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        universal = engine.filter_by_tag(analyzers, "universal")
        assert len(universal) == 1
        assert universal[0].analyzer_id == "bias_detector"

    def test_filter_by_type(self, engine, sample_analyzers_data):
        """Test filtering analyzers by type."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        bias = engine.filter_by_type(analyzers, "bias_detector")
        assert len(bias) == 1
        assert bias[0].analyzer_id == "bias_detector"

    def test_validate_analyzers_success(self, engine, sample_analyzers_data):
        """Test validating correct analyzers."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        errors = engine.validate_analyzers(analyzers)
        assert len(errors) == 0

    def test_validate_analyzers_duplicate_ids(self, engine):
        """Test validation catches duplicate analyzer IDs."""
        data = [
            {
                "analyzer_id": "bias_detector",
                "name": "Bias Detector",
                "description": "desc",
                "analyzer_type": "bias_detector",
                "enabled": True,
                "required": False,
                "tags": [],
            },
            {
                "analyzer_id": "bias_detector",
                "name": "Bias Detector 2",
                "description": "desc2",
                "analyzer_type": "bias_detector",
                "enabled": True,
                "required": False,
                "tags": [],
            },
        ]
        analyzers = engine.load_analyzers_from_dict(data)
        errors = engine.validate_analyzers(analyzers)
        assert any("Duplicate" in e for e in errors)

    def test_validate_analyzers_missing_fields(self, engine):
        """Test validation catches missing required fields."""
        data = [
            {
                "analyzer_id": "bias_detector",
                # Missing name
                "description": "desc",
                "analyzer_type": "bias_detector",
                "enabled": True,
                "required": False,
                "tags": [],
            },
        ]
        analyzers = engine.load_analyzers_from_dict(data)
        errors = engine.validate_analyzers(analyzers)
        assert any("missing name" in e for e in errors)

    def test_get_analyzers_by_tag(self, engine, sample_analyzers_data):
        """Test grouping analyzers by tag."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        tags = engine.get_analyzers_by_tag(analyzers)
        assert "universal" in tags
        assert "programming" in tags
        assert "security" in tags
        assert len(tags["programming"]) == 2

    def test_get_enabled_analyzers(self, engine, sample_analyzers_data):
        """Test getting all enabled analyzers."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        enabled = engine.get_enabled_analyzers(analyzers)
        assert len(enabled) == 2
        assert all(a.enabled for a in enabled)

    def test_get_required_analyzers(self, engine, sample_analyzers_data):
        """Test getting all required analyzers."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        required = engine.get_required_analyzers(analyzers)
        assert len(required) == 1
        assert required[0].analyzer_id == "bias_detector"

    def test_get_optional_analyzers(self, engine, sample_analyzers_data):
        """Test getting all optional analyzers."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        optional = engine.get_optional_analyzers(analyzers)
        assert len(optional) == 2
        assert all(not a.required for a in optional)

    def test_to_dict(self, engine, sample_analyzers_data):
        """Test converting analyzers to dict."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        dict_list = engine.to_dict(analyzers)
        assert len(dict_list) == 3
        assert dict_list[0]["analyzer_id"] == "bias_detector"
        assert dict_list[2]["enabled"] is False

    def test_to_json(self, engine, sample_analyzers_data):
        """Test converting analyzers to JSON."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        json_str = engine.to_json(analyzers)
        parsed = json.loads(json_str)
        assert len(parsed) == 3
        assert parsed[0]["analyzer_id"] == "bias_detector"

    def test_save_and_load_json(self, engine, sample_analyzers_data, tmp_path):
        """Test saving and loading analyzers from JSON."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        filepath = tmp_path / "analyzers.json"

        # Save
        engine.save_to_json(analyzers, str(filepath))
        assert filepath.exists()

        # Load
        loaded_analyzers = engine.load_analyzers_from_json(str(filepath))
        assert len(loaded_analyzers) == 3
        assert loaded_analyzers[0].analyzer_id == "bias_detector"
        assert loaded_analyzers[2].enabled is False

    def test_load_analyzers_from_json_invalid_file(self, engine):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            engine.load_analyzers_from_json("/nonexistent/path.json")

    def test_load_analyzers_from_json_not_array(self, engine, tmp_path):
        """Test loading from JSON that isn't an array raises error."""
        filepath = tmp_path / "analyzers.json"
        filepath.write_text('{"analyzer_id": "bias_detector"}')  # Object, not array
        with pytest.raises(ValueError):
            engine.load_analyzers_from_json(str(filepath))

    def test_analyzer_format_fields(self, engine, sample_analyzers_data):
        """Test QualityAnalyzer fields are properly set."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        analyzer = analyzers[0]
        assert analyzer.analyzer_id == "bias_detector"
        assert analyzer.name == "Bias Detector"
        assert analyzer.description == "Detects potential bias in specifications"
        assert analyzer.analyzer_type == "bias_detector"
        assert analyzer.enabled is True
        assert analyzer.required is True
        assert "universal" in analyzer.tags

    def test_multiple_analyzers_same_tag(self, engine):
        """Test multiple analyzers with same tag."""
        data = [
            {
                "analyzer_id": "perf1",
                "name": "Performance 1",
                "description": "desc",
                "analyzer_type": "perf1",
                "enabled": True,
                "required": False,
                "tags": ["performance"],
            },
            {
                "analyzer_id": "perf2",
                "name": "Performance 2",
                "description": "desc",
                "analyzer_type": "perf2",
                "enabled": True,
                "required": False,
                "tags": ["performance"],
            },
        ]
        analyzers = engine.load_analyzers_from_dict(data)
        perf_analyzers = engine.filter_by_tag(analyzers, "performance")
        assert len(perf_analyzers) == 2

    def test_filter_chain_enabled_and_required(self, engine, sample_analyzers_data):
        """Test chaining multiple filters."""
        analyzers = engine.load_analyzers_from_dict(sample_analyzers_data)
        # Filter by enabled
        enabled = engine.filter_by_enabled(analyzers, True)
        # Then by required
        required = engine.filter_by_required(enabled, True)
        assert len(required) == 1
        assert required[0].analyzer_id == "bias_detector"

    def test_large_analyzer_set(self, engine):
        """Test engine handles large number of analyzers efficiently."""
        data = [
            {
                "analyzer_id": f"analyzer_{i}",
                "name": f"Analyzer {i}",
                "description": f"Analyzer {i} description",
                "analyzer_type": f"type_{i}",
                "enabled": i % 2 == 0,
                "required": i < 5,
                "tags": [f"tag_{i % 3}"],
            }
            for i in range(50)
        ]
        analyzers = engine.load_analyzers_from_dict(data)
        assert len(analyzers) == 50
        errors = engine.validate_analyzers(analyzers)
        assert len(errors) == 0


class TestGlobalAnalyzerEngine:
    """Test global analyzer engine instance."""

    def test_get_analyzer_engine_singleton(self):
        """Test that get_analyzer_engine returns singleton."""
        engine1 = get_analyzer_engine()
        engine2 = get_analyzer_engine()
        assert engine1 is engine2


class TestProgrammingDomainAnalyzers:
    """Test programming domain analyzer loading."""

    def test_programming_analyzers_load(self):
        """Test that programming analyzers load correctly."""
        engine = QualityAnalyzerEngine()
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        analyzers = domain.get_quality_analyzers()

        # Should return list of analyzer IDs (strings) or QualityAnalyzer objects
        assert len(analyzers) >= 4

    def test_programming_analyzers_configuration(self):
        """Test that programming domain uses configuration."""
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        analyzers = domain.get_quality_analyzers()

        # Check that expected analyzers are present
        analyzer_ids = set()
        if analyzers and isinstance(analyzers[0], QualityAnalyzer):
            analyzer_ids = {a.analyzer_id for a in analyzers}
        else:
            analyzer_ids = set(analyzers)

        assert "bias_detector" in analyzer_ids
        assert "performance_validator" in analyzer_ids
        assert "security_validator" in analyzer_ids

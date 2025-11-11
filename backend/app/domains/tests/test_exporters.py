"""Tests for exporter template engine."""

import json

import pytest

from ..base import ExportFormat
from ..exporters import ExportTemplateEngine, get_exporter_engine


class TestExportTemplateEngine:
    """Test ExportTemplateEngine functionality."""

    @pytest.fixture
    def engine(self):
        """Create a fresh exporter engine."""
        return ExportTemplateEngine()

    @pytest.fixture
    def sample_exporters_data(self):
        """Sample exporter data for testing."""
        return [
            {
                "format_id": "python",
                "name": "Python",
                "description": "Python class generation",
                "file_extension": ".py",
                "mime_type": "text/x-python",
                "template_id": "python_class",
            },
            {
                "format_id": "javascript",
                "name": "JavaScript",
                "description": "JavaScript class generation",
                "file_extension": ".js",
                "mime_type": "text/javascript",
                "template_id": "js_class",
            },
            {
                "format_id": "go",
                "name": "Go",
                "description": "Go struct generation",
                "file_extension": ".go",
                "mime_type": "text/x-go",
                "template_id": "go_struct",
            },
        ]

    def test_load_exporters_from_dict(self, engine, sample_exporters_data):
        """Test loading exporters from dictionary."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        assert len(exporters) == 3
        assert exporters[0].format_id == "python"
        assert exporters[1].name == "JavaScript"
        assert exporters[2].file_extension == ".go"

    def test_load_exporters_invalid_data(self, engine):
        """Test loading exporter with missing required fields."""
        invalid_data = [{"format_id": "python"}]  # Missing required fields
        # This will load but with None values, which should be caught by validation
        exporters = engine.load_exporters_from_dict(invalid_data)
        errors = engine.validate_exporters(exporters)
        assert len(errors) > 0  # Should have validation errors

    def test_filter_by_language(self, engine, sample_exporters_data):
        """Test filtering exporters by language."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        py = engine.filter_by_language(exporters, "Python")
        assert len(py) == 1
        assert py[0].format_id == "python"

    def test_filter_by_language_case_insensitive(self, engine, sample_exporters_data):
        """Test language filter is case insensitive."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        py = engine.filter_by_language(exporters, "PYTHON")
        assert len(py) == 1

    def test_filter_by_extension(self, engine, sample_exporters_data):
        """Test filtering exporters by file extension."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        py_files = engine.filter_by_extension(exporters, ".py")
        assert len(py_files) == 1
        assert py_files[0].format_id == "python"

    def test_filter_by_extension_without_dot(self, engine, sample_exporters_data):
        """Test extension filter works without leading dot."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        py_files = engine.filter_by_extension(exporters, "py")
        assert len(py_files) == 1
        assert py_files[0].format_id == "python"

    def test_filter_by_mime_type(self, engine, sample_exporters_data):
        """Test filtering exporters by MIME type."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        py_files = engine.filter_by_mime_type(exporters, "text/x-python")
        assert len(py_files) == 1
        assert py_files[0].format_id == "python"

    def test_filter_by_category_compiled(self, engine, sample_exporters_data):
        """Test filtering by compiled languages category."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        compiled = engine.filter_by_category(exporters, "compiled")
        compiled_ids = {e.format_id for e in compiled}
        assert "go" in compiled_ids
        assert "python" not in compiled_ids
        assert "javascript" not in compiled_ids

    def test_filter_by_category_scripted(self, engine, sample_exporters_data):
        """Test filtering by scripted languages category."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        scripted = engine.filter_by_category(exporters, "scripted")
        scripted_ids = {e.format_id for e in scripted}
        assert "python" in scripted_ids
        assert "javascript" in scripted_ids
        assert "go" not in scripted_ids

    def test_filter_by_category_static(self, engine, sample_exporters_data):
        """Test filtering by static typing category."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        static = engine.filter_by_category(exporters, "static")
        static_ids = {e.format_id for e in static}
        assert "go" in static_ids
        assert "python" not in static_ids

    def test_filter_by_invalid_category(self, engine, sample_exporters_data):
        """Test filtering by invalid category returns empty list."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        result = engine.filter_by_category(exporters, "nonexistent")
        assert len(result) == 0

    def test_validate_exporters_success(self, engine, sample_exporters_data):
        """Test validating correct exporters."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        errors = engine.validate_exporters(exporters)
        assert len(errors) == 0

    def test_validate_exporters_duplicate_format_ids(self, engine):
        """Test validation catches duplicate format IDs."""
        data = [
            {
                "format_id": "python",
                "name": "Python",
                "description": "Python",
                "file_extension": ".py",
                "mime_type": "text/x-python",
                "template_id": "python_class",
            },
            {
                "format_id": "python",
                "name": "Python 2",
                "description": "Python 2",
                "file_extension": ".py",
                "mime_type": "text/x-python",
                "template_id": "python_class_v2",
            },
        ]
        exporters = engine.load_exporters_from_dict(data)
        errors = engine.validate_exporters(exporters)
        assert any("Duplicate" in e and "format" in e for e in errors)

    def test_validate_exporters_duplicate_template_ids(self, engine):
        """Test validation catches duplicate template IDs."""
        data = [
            {
                "format_id": "python",
                "name": "Python",
                "description": "Python",
                "file_extension": ".py",
                "mime_type": "text/x-python",
                "template_id": "generic_class",
            },
            {
                "format_id": "javascript",
                "name": "JavaScript",
                "description": "JavaScript",
                "file_extension": ".js",
                "mime_type": "text/javascript",
                "template_id": "generic_class",
            },
        ]
        exporters = engine.load_exporters_from_dict(data)
        errors = engine.validate_exporters(exporters)
        assert any("Duplicate" in e and "template" in e for e in errors)

    def test_validate_exporters_missing_fields(self, engine):
        """Test validation catches missing required fields."""
        data = [
            {
                "format_id": "python",
                "name": "Python",
                "description": "Python",
                # Missing file_extension
                "mime_type": "text/x-python",
                "template_id": "python_class",
            },
        ]
        exporters = engine.load_exporters_from_dict(data)
        errors = engine.validate_exporters(exporters)
        assert any("missing file_extension" in e for e in errors)

    def test_validate_exporters_bad_extension_format(self, engine):
        """Test validation catches bad file extension format."""
        data = [
            {
                "format_id": "python",
                "name": "Python",
                "description": "Python",
                "file_extension": "py",  # Missing leading dot
                "mime_type": "text/x-python",
                "template_id": "python_class",
            },
        ]
        exporters = engine.load_exporters_from_dict(data)
        errors = engine.validate_exporters(exporters)
        assert any("must start with dot" in e for e in errors)

    def test_validate_exporters_invalid_mime_type(self, engine):
        """Test validation catches invalid MIME types."""
        data = [
            {
                "format_id": "python",
                "name": "Python",
                "description": "Python",
                "file_extension": ".py",
                "mime_type": "invalid-mime",  # Invalid format
                "template_id": "python_class",
            },
        ]
        exporters = engine.load_exporters_from_dict(data)
        errors = engine.validate_exporters(exporters)
        assert any("invalid MIME type" in e for e in errors)

    def test_get_exporters_by_language_family(self, engine, sample_exporters_data):
        """Test grouping exporters by language family."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        families = engine.get_exporters_by_language_family(exporters)
        assert "python" in families
        assert "javascript" in families
        assert "go" in families
        assert len(families["python"]) == 1
        assert families["python"][0].format_id == "python"

    def test_to_dict(self, engine, sample_exporters_data):
        """Test converting exporters to dict."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        dict_list = engine.to_dict(exporters)
        assert len(dict_list) == 3
        assert dict_list[0]["format_id"] == "python"
        assert dict_list[1]["name"] == "JavaScript"

    def test_to_json(self, engine, sample_exporters_data):
        """Test converting exporters to JSON."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        json_str = engine.to_json(exporters)
        parsed = json.loads(json_str)
        assert len(parsed) == 3
        assert parsed[0]["format_id"] == "python"

    def test_save_and_load_json(self, engine, sample_exporters_data, tmp_path):
        """Test saving and loading exporters from JSON."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        filepath = tmp_path / "exporters.json"

        # Save
        engine.save_to_json(exporters, str(filepath))
        assert filepath.exists()

        # Load
        loaded_exporters = engine.load_exporters_from_json(str(filepath))
        assert len(loaded_exporters) == 3
        assert loaded_exporters[0].format_id == "python"
        assert loaded_exporters[1].name == "JavaScript"

    def test_load_exporters_from_json_invalid_file(self, engine):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            engine.load_exporters_from_json("/nonexistent/path.json")

    def test_load_exporters_from_json_not_array(self, engine, tmp_path):
        """Test loading from JSON that isn't an array raises error."""
        filepath = tmp_path / "exporters.json"
        filepath.write_text('{"format_id": "python"}')  # Object, not array
        with pytest.raises(ValueError):
            engine.load_exporters_from_json(str(filepath))

    def test_exporter_format_fields(self, engine, sample_exporters_data):
        """Test ExportFormat fields are properly set."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        exp = exporters[0]
        assert exp.format_id == "python"
        assert exp.name == "Python"
        assert exp.description == "Python class generation"
        assert exp.file_extension == ".py"
        assert exp.mime_type == "text/x-python"
        assert exp.template_id == "python_class"

    def test_multiple_exporters_same_language_family(self, engine):
        """Test engine groups multiple exporters under same language family."""
        data = [
            {
                "format_id": "javascript_es5",
                "name": "JavaScript ES5",
                "description": "ES5 generation",
                "file_extension": ".js",
                "mime_type": "text/javascript",
                "template_id": "js_class_es5",
            },
            {
                "format_id": "javascript_es6",
                "name": "JavaScript ES6",
                "description": "ES6 generation",
                "file_extension": ".js",
                "mime_type": "text/javascript",
                "template_id": "js_class_es6",
            },
        ]
        exporters = engine.load_exporters_from_dict(data)
        families = engine.get_exporters_by_language_family(exporters)
        # Both should be grouped under "javascript" family
        assert "javascript" in families
        assert len(families["javascript"]) == 2
        assert any(e.format_id == "javascript_es5" for e in families["javascript"])
        assert any(e.format_id == "javascript_es6" for e in families["javascript"])

    def test_filter_chain_language_then_extension(self, engine, sample_exporters_data):
        """Test chaining multiple filters."""
        exporters = engine.load_exporters_from_dict(sample_exporters_data)
        # Filter by scripted languages
        scripted = engine.filter_by_category(exporters, "scripted")
        # Then by Python extension
        py = engine.filter_by_extension(scripted, ".py")
        assert len(py) == 1
        assert py[0].format_id == "python"

    def test_large_exporter_set(self, engine):
        """Test engine handles large number of exporters efficiently."""
        data = [
            {
                "format_id": f"lang_{i}",
                "name": f"Language {i}",
                "description": f"Language {i} export",
                "file_extension": f".lang{i}",
                "mime_type": f"text/x-lang{i}",
                "template_id": f"template_{i}",
            }
            for i in range(100)
        ]
        exporters = engine.load_exporters_from_dict(data)
        assert len(exporters) == 100
        errors = engine.validate_exporters(exporters)
        assert len(errors) == 0


class TestGlobalExporterEngine:
    """Test global exporter engine instance."""

    def test_get_exporter_engine_singleton(self):
        """Test that get_exporter_engine returns singleton."""
        engine1 = get_exporter_engine()
        engine2 = get_exporter_engine()
        assert engine1 is engine2


class TestProgrammingDomainExporters:
    """Test programming domain exporter loading."""

    def test_programming_exporters_load(self):
        """Test that programming exporters load correctly."""
        engine = ExportTemplateEngine()
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()

        assert len(exporters) == 8
        assert all(isinstance(e, ExportFormat) for e in exporters)

    def test_programming_exporters_have_all_languages(self):
        """Test that all expected languages are available."""
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()
        format_ids = {e.format_id for e in exporters}

        expected = {"python", "javascript", "typescript", "go", "java", "rust", "csharp", "kotlin"}
        assert format_ids == expected

    def test_programming_exporters_template_ids(self):
        """Test that template IDs are properly defined."""
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()
        template_ids = {e.template_id for e in exporters}

        assert len(template_ids) == 8  # All unique
        assert all(tid for tid in template_ids)  # All non-empty

    def test_programming_exporters_file_extensions(self):
        """Test that file extensions are correct."""
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()

        extension_map = {e.format_id: e.file_extension for e in exporters}
        assert extension_map["python"] == ".py"
        assert extension_map["javascript"] == ".js"
        assert extension_map["typescript"] == ".ts"
        assert extension_map["go"] == ".go"
        assert extension_map["java"] == ".java"
        assert extension_map["rust"] == ".rs"
        assert extension_map["csharp"] == ".cs"
        assert extension_map["kotlin"] == ".kt"

    def test_programming_exporters_mime_types(self):
        """Test that MIME types are valid."""
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()

        for e in exporters:
            assert e.mime_type
            assert "/" in e.mime_type
            assert any(
                e.mime_type.startswith(prefix)
                for prefix in ["text/", "application/", "image/", "audio/", "video/"]
            )

    def test_programming_exporters_descriptions(self):
        """Test that all exporters have descriptions."""
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()

        for e in exporters:
            assert e.description
            assert len(e.description) > 10
            assert e.name.lower() in e.description.lower()

    def test_programming_exporters_validation(self):
        """Test that exported configuration validates correctly."""
        engine = ExportTemplateEngine()
        from ..programming import ProgrammingDomain

        domain = ProgrammingDomain()
        exporters = domain.get_export_formats()
        errors = engine.validate_exporters(exporters)

        assert len(errors) == 0, f"Validation errors: {errors}"

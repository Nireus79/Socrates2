"""
Test that critical package fixes are working correctly.

These tests verify:
1. Entry point fix - pyproject.toml is correct
2. Package structure - socrates module is installable
3. Import functionality - socrates module can be imported
4. Circular dependency fix - requirements.txt is clean
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEntryPointFix:
    """Test that entry point has been fixed in pyproject.toml"""

    def test_pyproject_no_broken_entry_point(self):
        """Verify pyproject.toml doesn't have broken 'app.cli:main' entry point"""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject_path.read_text()
        
        # Should NOT have the broken entry point
        assert 'socrates = "app.cli:main"' not in content, \
            "Broken entry point 'app.cli:main' still exists in pyproject.toml"
        
    def test_pyproject_has_package_explanation(self):
        """Verify pyproject.toml explains the CLI approach"""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject_path.read_text()
        
        # Should explain the new approach
        assert "Socrates.py" in content or "python -m app.cli" in content, \
            "pyproject.toml missing documentation about CLI usage"


class TestCircularDependencyFix:
    """Test that circular dependency has been fixed"""

    def test_requirements_no_circular_dependency(self):
        """Verify requirements.txt doesn't mention 'socrates-ai' in comments"""
        req_path = Path(__file__).parent.parent / "requirements.txt"
        content = req_path.read_text()
        
        # Should NOT have confusing circular dependency comment
        assert "socrates-ai is installed from the local backend directory via setup.py" not in content, \
            "Circular dependency comment still in requirements.txt"
        
    def test_requirements_has_local_install(self):
        """Verify requirements.txt uses local -e . installation"""
        req_path = Path(__file__).parent.parent / "requirements.txt"
        content = req_path.read_text()
        
        assert "-e ." in content, \
            "Local installation marker '-e .' not found in requirements.txt"


class TestSocratesModuleStructure:
    """Test that socrates public API module exists and is structured correctly"""

    def test_socrates_module_exists(self):
        """Verify socrates/__init__.py exists"""
        socrates_init = Path(__file__).parent.parent / "socrates" / "__init__.py"
        assert socrates_init.exists(), \
            "socrates/__init__.py not found"

    def test_socrates_module_is_in_pyproject(self):
        """Verify pyproject.toml includes 'socrates' in packages"""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject_path.read_text()
        
        assert 'packages = ["app", "socrates"]' in content, \
            "pyproject.toml doesn't declare both 'app' and 'socrates' packages"

    def test_socrates_version_defined(self):
        """Verify socrates/__init__.py defines __version__"""
        socrates_init = Path(__file__).parent.parent / "socrates" / "__init__.py"
        content = socrates_init.read_text()
        
        assert "__version__" in content, \
            "socrates/__init__.py missing __version__ definition"


class TestSocratesImports:
    """Test that socrates module can be imported and has expected exports"""

    def test_import_socrates(self):
        """Verify socrates module can be imported"""
        try:
            import socrates
            assert socrates is not None
        except ImportError as e:
            pytest.fail(f"Cannot import socrates module: {e}")

    def test_socrates_has_version(self):
        """Verify socrates module exports __version__"""
        import socrates
        assert hasattr(socrates, "__version__"), \
            "socrates module missing __version__"
        assert isinstance(socrates.__version__, str), \
            "__version__ should be a string"

    def test_socrates_exports_engines(self):
        """Verify socrates exports all core engines"""
        import socrates
        
        expected_engines = [
            "QuestionGenerator",
            "ConflictDetectionEngine",
            "BiasDetectionEngine",
            "LearningEngine",
        ]
        
        for engine in expected_engines:
            assert hasattr(socrates, engine), \
                f"socrates missing export: {engine}"

    def test_socrates_exports_models(self):
        """Verify socrates exports all data models"""
        import socrates
        
        expected_models = [
            "ProjectData",
            "SpecificationData",
            "QuestionData",
            "ConflictData",
            "UserBehaviorData",
        ]
        
        for model in expected_models:
            assert hasattr(socrates, model), \
                f"socrates missing export: {model}"

    def test_socrates_exports_conversions(self):
        """Verify socrates exports conversion functions"""
        import socrates
        
        expected_functions = [
            "project_db_to_data",
            "spec_db_to_data",
            "question_db_to_data",
            "conflict_db_to_data",
            "specs_db_to_data",
            "questions_db_to_data",
        ]
        
        for func in expected_functions:
            assert hasattr(socrates, func), \
                f"socrates missing export: {func}"

    def test_socrates_has_all_in_all(self):
        """Verify socrates defines __all__ for explicit exports"""
        import socrates
        assert hasattr(socrates, "__all__"), \
            "socrates module missing __all__ definition"
        assert len(socrates.__all__) > 10, \
            "__all__ should contain multiple exports"


class TestAgentImports:
    """Test that agents can import from socrates"""

    def test_agent_imports_work(self):
        """Verify agents can import from socrates (not just app.core)"""
        # This would require loading agent modules
        # For now, just verify the socrates module is properly structured
        try:
            from socrates import QuestionGenerator, UserBehaviorData
            assert QuestionGenerator is not None
            assert UserBehaviorData is not None
        except ImportError as e:
            pytest.fail(f"Cannot import from socrates: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

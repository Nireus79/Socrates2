"""
Tests for Socrates library integration with Socrates2.

Tests that the Socrates library (socrates-ai) is properly integrated
and can be imported and used in the application.
"""

import pytest


@pytest.mark.unit
class TestSocratesLibraryImports:
    """Test that Socrates library can be imported."""

    def test_socrates_library_installed(self):
        """Test that socrates-ai library is installed."""
        try:
            import socrates
            assert socrates is not None
        except ImportError:
            pytest.fail("socrates-ai library not installed")

    def test_question_generator_importable(self):
        """Test that QuestionGenerator can be imported from socrates."""
        from socrates import QuestionGenerator
        assert QuestionGenerator is not None

    def test_conflict_engine_importable(self):
        """Test that ConflictDetectionEngine can be imported from socrates."""
        from socrates import ConflictDetectionEngine
        assert ConflictDetectionEngine is not None

    def test_bias_detection_engine_importable(self):
        """Test that BiasDetectionEngine can be imported from socrates."""
        from socrates import BiasDetectionEngine
        assert BiasDetectionEngine is not None

    def test_learning_engine_importable(self):
        """Test that LearningEngine can be imported from socrates."""
        from socrates import LearningEngine
        assert LearningEngine is not None


@pytest.mark.unit
class TestSocratesDataModels:
    """Test that Socrates data models can be imported."""

    def test_project_data_importable(self):
        """Test that ProjectData can be imported."""
        from socrates import ProjectData
        assert ProjectData is not None

    def test_specification_data_importable(self):
        """Test that SpecificationData can be imported."""
        from socrates import SpecificationData
        assert SpecificationData is not None

    def test_question_data_importable(self):
        """Test that QuestionData can be imported."""
        from socrates import QuestionData
        assert QuestionData is not None

    def test_conflict_data_importable(self):
        """Test that ConflictData can be imported."""
        from socrates import ConflictData
        assert ConflictData is not None


@pytest.mark.unit
class TestSocratesConversionFunctions:
    """Test that Socrates conversion functions can be imported."""

    def test_project_conversion_function_importable(self):
        """Test that project_db_to_data conversion function exists."""
        from socrates import project_db_to_data
        assert project_db_to_data is not None

    def test_specification_conversion_function_importable(self):
        """Test that spec_db_to_data conversion function exists."""
        from socrates import spec_db_to_data
        assert spec_db_to_data is not None

    def test_question_conversion_function_importable(self):
        """Test that question_db_to_data conversion function exists."""
        from socrates import question_db_to_data
        assert question_db_to_data is not None

    def test_conflict_conversion_function_importable(self):
        """Test that conflict_db_to_data conversion function exists."""
        from socrates import conflict_db_to_data
        assert conflict_db_to_data is not None


@pytest.mark.unit
class TestSocratesLibraryVersion:
    """Test Socrates library version information."""

    def test_socrates_has_version(self):
        """Test that socrates library has version information."""
        import socrates
        assert hasattr(socrates, "__version__")
        version = socrates.__version__
        assert version is not None
        assert len(version) > 0

    def test_version_format_valid(self):
        """Test that version follows semantic versioning."""
        import socrates
        version = socrates.__version__
        # Should be in format X.Y.Z
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor


@pytest.mark.unit
class TestQuestionGeneratorUsage:
    """Test using QuestionGenerator from Socrates library."""

    def test_question_generator_can_be_instantiated(self):
        """Test that QuestionGenerator can be created."""
        from socrates import QuestionGenerator
        gen = QuestionGenerator()
        assert gen is not None

    def test_question_generator_has_coverage_method(self):
        """Test that QuestionGenerator has calculate_coverage method."""
        from socrates import QuestionGenerator
        gen = QuestionGenerator()
        assert hasattr(gen, "calculate_coverage")
        assert callable(gen.calculate_coverage)

    def test_question_generator_has_identify_next_category(self):
        """Test that QuestionGenerator has identify_next_category method."""
        from socrates import QuestionGenerator
        gen = QuestionGenerator()
        assert hasattr(gen, "identify_next_category")
        assert callable(gen.identify_next_category)

    def test_question_generator_has_build_prompt_method(self):
        """Test that QuestionGenerator has build_question_generation_prompt method."""
        from socrates import QuestionGenerator
        gen = QuestionGenerator()
        assert hasattr(gen, "build_question_generation_prompt")
        assert callable(gen.build_question_generation_prompt)


@pytest.mark.unit
class TestConflictDetectionEngineUsage:
    """Test using ConflictDetectionEngine from Socrates library."""

    def test_conflict_engine_can_be_instantiated(self):
        """Test that ConflictDetectionEngine can be created."""
        from socrates import ConflictDetectionEngine
        engine = ConflictDetectionEngine()
        assert engine is not None

    def test_conflict_engine_has_detection_method(self):
        """Test that ConflictDetectionEngine has detection methods."""
        from socrates import ConflictDetectionEngine
        engine = ConflictDetectionEngine()
        assert hasattr(engine, "build_conflict_detection_prompt")
        assert callable(engine.build_conflict_detection_prompt)


@pytest.mark.unit
class TestBiasDetectionEngineUsage:
    """Test using BiasDetectionEngine from Socrates library."""

    def test_bias_engine_can_be_instantiated(self):
        """Test that BiasDetectionEngine can be created."""
        from socrates import BiasDetectionEngine
        engine = BiasDetectionEngine()
        assert engine is not None

    def test_bias_engine_has_detection_methods(self):
        """Test that BiasDetectionEngine has detection methods."""
        from socrates import BiasDetectionEngine
        engine = BiasDetectionEngine()
        assert hasattr(engine, "detect_bias_in_question")
        assert callable(engine.detect_bias_in_question)


@pytest.mark.unit
class TestLearningEngineUsage:
    """Test using LearningEngine from Socrates library."""

    def test_learning_engine_can_be_instantiated(self):
        """Test that LearningEngine can be created."""
        from socrates import LearningEngine
        engine = LearningEngine()
        assert engine is not None

    def test_learning_engine_has_profiling_methods(self):
        """Test that LearningEngine has user profiling methods."""
        from socrates import LearningEngine
        engine = LearningEngine()
        assert hasattr(engine, "build_user_profile")
        assert callable(engine.build_user_profile)


@pytest.mark.unit
class TestSocratesLibraryIntegration:
    """Test overall Socrates library integration."""

    def test_all_engines_available(self):
        """Test that all core engines are available."""
        from socrates import (
            QuestionGenerator,
            ConflictDetectionEngine,
            BiasDetectionEngine,
            LearningEngine
        )
        assert QuestionGenerator is not None
        assert ConflictDetectionEngine is not None
        assert BiasDetectionEngine is not None
        assert LearningEngine is not None

    def test_all_data_models_available(self):
        """Test that all data models are available."""
        from socrates import (
            ProjectData,
            SpecificationData,
            QuestionData,
            ConflictData
        )
        assert ProjectData is not None
        assert SpecificationData is not None
        assert QuestionData is not None
        assert ConflictData is not None

    def test_library_in_requirements(self):
        """Test that socrates-ai is in requirements.txt."""
        try:
            with open("/home/user/Socrates2/backend/requirements.txt", "r") as f:
                content = f.read()
                assert "socrates" in content.lower()
        except FileNotFoundError:
            pytest.skip("requirements.txt not found")

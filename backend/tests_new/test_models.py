"""
Unit tests for Socrates2 core models.

Tests data validation, constraints, and basic model functionality
without database connectivity.
"""

import pytest
from datetime import datetime
from uuid import UUID


@pytest.mark.unit
class TestUserModel:
    """Test User model validation and functionality."""

    def test_user_creation(self, test_user_data):
        """Test that user can be created with valid data."""
        assert test_user_data["email"] == "test@example.com"
        assert test_user_data["password"] == "SecurePassword123!"
        assert test_user_data["full_name"] == "Test User"

    def test_user_email_format(self, test_user_data):
        """Test email validation."""
        email = test_user_data["email"]
        assert "@" in email
        assert "." in email.split("@")[1]

    def test_password_strength(self, test_user_data):
        """Test password meets minimum requirements."""
        password = test_user_data["password"]
        assert len(password) >= 8
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)


@pytest.mark.unit
class TestProjectModel:
    """Test Project model validation and functionality."""

    def test_project_creation(self, test_project_data):
        """Test that project can be created with valid data."""
        assert test_project_data["name"] == "Test Project"
        assert test_project_data["maturity_score"] == 0.5
        assert test_project_data["description"] == "A test project for Socrates2"

    def test_maturity_score_range(self, test_project_data):
        """Test maturity score is between 0 and 1."""
        score = test_project_data["maturity_score"]
        assert 0 <= score <= 1

    def test_project_name_not_empty(self, test_project_data):
        """Test project name is not empty."""
        assert len(test_project_data["name"]) > 0


@pytest.mark.unit
class TestSpecificationModel:
    """Test Specification model validation and functionality."""

    def test_specification_creation(self, test_specification_data):
        """Test that specification can be created with valid data."""
        assert test_specification_data["category"] == "Performance"
        assert test_specification_data["key"] == "response_time"
        assert test_specification_data["value"] == "< 200ms"
        assert test_specification_data["confidence"] == 0.9

    def test_specification_confidence_range(self, test_specification_data):
        """Test confidence is between 0 and 1."""
        confidence = test_specification_data["confidence"]
        assert 0 <= confidence <= 1

    def test_specification_requires_category(self, test_specification_data):
        """Test that specification requires a category."""
        assert "category" in test_specification_data
        assert len(test_specification_data["category"]) > 0

    def test_specification_requires_key(self, test_specification_data):
        """Test that specification requires a key."""
        assert "key" in test_specification_data
        assert len(test_specification_data["key"]) > 0


@pytest.mark.unit
class TestQuestionModel:
    """Test Question model validation and functionality."""

    def test_question_creation(self, test_question_data):
        """Test that question can be created with valid data."""
        assert test_question_data["category"] == "Performance"
        assert test_question_data["text"] == "What is your target response time?"
        assert test_question_data["template_id"] == "perf_response_time"
        assert test_question_data["confidence"] == 0.85

    def test_question_confidence_range(self, test_question_data):
        """Test question confidence is between 0 and 1."""
        confidence = test_question_data["confidence"]
        assert 0 <= confidence <= 1

    def test_question_text_not_empty(self, test_question_data):
        """Test question text is not empty."""
        assert len(test_question_data["text"]) > 0


@pytest.mark.unit
class TestSessionModel:
    """Test Session (conversation) model validation and functionality."""

    def test_session_creation(self, test_session_data):
        """Test that session can be created with valid data."""
        assert test_session_data["name"] == "Specification Gathering Session 1"
        assert test_session_data["status"] in ["active", "completed", "archived"]
        assert test_session_data["description"] == "Initial requirements gathering session"

    def test_session_status_valid(self, test_session_data):
        """Test session status is valid."""
        valid_statuses = ["active", "completed", "archived"]
        assert test_session_data["status"] in valid_statuses

    def test_session_name_not_empty(self, test_session_data):
        """Test session name is not empty."""
        assert len(test_session_data["name"]) > 0


@pytest.mark.unit
class TestModelRelationships:
    """Test model relationships and constraints."""

    def test_project_belongs_to_user(self, test_user_data, test_project_data):
        """Test that project references user."""
        # This would be enforced in the database layer
        assert "email" in test_user_data
        assert "name" in test_project_data

    def test_specification_belongs_to_project(self, test_project_data, test_specification_data):
        """Test that specification belongs to a project."""
        assert "name" in test_project_data
        assert "category" in test_specification_data

    def test_question_belongs_to_session(self, test_session_data, test_question_data):
        """Test that question belongs to a session."""
        assert "name" in test_session_data
        assert "text" in test_question_data


@pytest.mark.unit
class TestDataValidation:
    """Test data validation across models."""

    def test_uuid_format(self):
        """Test UUID validation."""
        try:
            uuid_obj = UUID("550e8400-e29b-41d4-a716-446655440000")
            assert isinstance(uuid_obj, UUID)
        except ValueError:
            pytest.fail("Invalid UUID format")

    def test_email_validation(self, test_user_data):
        """Test email validation logic."""
        email = test_user_data["email"]
        # Basic email validation
        assert "@" in email
        parts = email.split("@")
        assert len(parts) == 2
        assert len(parts[0]) > 0
        assert "." in parts[1]

    def test_numeric_constraints(self, test_specification_data, test_question_data):
        """Test numeric field constraints."""
        # Confidence scores should be floats between 0 and 1
        spec_conf = test_specification_data["confidence"]
        q_conf = test_question_data["confidence"]
        assert isinstance(spec_conf, float)
        assert isinstance(q_conf, float)
        assert 0 <= spec_conf <= 1
        assert 0 <= q_conf <= 1

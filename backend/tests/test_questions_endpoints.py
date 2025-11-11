"""
Comprehensive tests for questions endpoints.

Tests:
- List questions by domain
- List questions by category
- Get question details
- Question filtering
- Question search
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestQuestionListing:
    """Test question listing endpoint."""

    def test_list_all_questions_success(self, test_client, authenticated_user):
        """Test getting list of all questions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_questions_requires_auth(self, test_client):
        """Test listing questions requires authentication."""
        response = test_client.get("/api/v1/questions")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_list_questions_by_domain(self, test_client, authenticated_user):
        """Test filtering questions by domain."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?domain=architecture",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_questions_by_category(self, test_client, authenticated_user):
        """Test filtering questions by category."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?category=performance",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_list_questions_pagination(self, test_client, authenticated_user):
        """Test pagination of questions list."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?skip=0&limit=10",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


@pytest.mark.api
class TestQuestionRetrieval:
    """Test getting individual question details."""

    def test_get_question_success(self, test_client, authenticated_user):
        """Test getting question details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Get list first
        list_response = test_client.get(
            "/api/v1/questions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        questions = list_response.json()
        if len(questions) > 0:
            question_id = questions[0].get("id")
            response = test_client.get(
                f"/api/v1/questions/{question_id}",
                headers={"Authorization": f"Bearer {authenticated_user['token']}"}
            )
            assert response.status_code == status.HTTP_200_OK

    def test_question_details_structure(self, test_client, authenticated_user):
        """Test that question details have expected structure."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        questions = response.json()
        if len(questions) > 0:
            question = questions[0]
            # Questions should have at least basic fields
            assert isinstance(question, dict)
            # Check for expected fields (varies by implementation)
            assert any(key in question for key in ["id", "question_id", "text"])


@pytest.mark.api
class TestQuestionFiltering:
    """Test question filtering and search."""

    def test_search_questions(self, test_client, authenticated_user):
        """Test searching questions by text."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?search=architecture",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_filter_questions_multiple_criteria(self, test_client, authenticated_user):
        """Test filtering questions with multiple criteria."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?domain=architecture&category=design&skip=0&limit=5",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_invalid_filter_parameter(self, test_client, authenticated_user):
        """Test handling of invalid filter parameter."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?invalid_param=value",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either ignore unknown params or reject with 422
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_negative_limit_parameter(self, test_client, authenticated_user):
        """Test handling of negative limit parameter."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?limit=-5",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either reject or treat as positive
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_zero_limit_parameter(self, test_client, authenticated_user):
        """Test handling of zero limit parameter."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?limit=0",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either reject or return empty list
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.api
class TestQuestionDomains:
    """Test questions across different domains."""

    def test_list_programming_domain_questions(self, test_client, authenticated_user):
        """Test getting programming domain questions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?domain=programming",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_list_architecture_domain_questions(self, test_client, authenticated_user):
        """Test getting architecture domain questions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?domain=architecture",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_list_testing_domain_questions(self, test_client, authenticated_user):
        """Test getting testing domain questions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?domain=testing",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

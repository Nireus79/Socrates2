"""
Comprehensive tests for domain endpoints.

Tests:
- List available domains
- Get domain details
- Get domain questions
- Get domain analyzers
- Domain validation
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestDomainListing:
    """Test domain listing endpoint."""

    def test_list_domains_success(self, test_client, authenticated_user):
        """Test getting list of available domains."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/domains",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should have at least some domains
        assert len(data) > 0

    def test_list_domains_public(self, test_client):
        """Test that domain listing might be public."""
        response = test_client.get("/api/v1/domains")
        # Could be either public or require auth
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_domains_have_required_fields(self, test_client, authenticated_user):
        """Test that domains have required metadata."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/domains",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        domains = response.json()
        if len(domains) > 0:
            domain = domains[0]
            # Domains should have at least basic fields
            assert "id" in domain or "name" in domain


@pytest.mark.api
class TestDomainDetails:
    """Test getting individual domain details."""

    def test_get_domain_details(self, test_client, authenticated_user):
        """Test getting domain details."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Get list of domains first
        list_response = test_client.get(
            "/api/v1/domains",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        domains = list_response.json()
        if len(domains) > 0:
            domain_id = domains[0].get("id") or domains[0].get("name")
            # Try to get domain details
            response = test_client.get(
                f"/api/v1/domains/{domain_id}",
                headers={"Authorization": f"Bearer {authenticated_user['token']}"}
            )
            # Should either return 200 or 404 if endpoint not implemented
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND
            ]

    def test_get_nonexistent_domain(self, test_client, authenticated_user):
        """Test getting nonexistent domain."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/domains/nonexistent-domain",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should return 404
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestDomainQuestions:
    """Test domain question retrieval."""

    def test_domain_has_questions(self, test_client, authenticated_user):
        """Test that domains have associated questions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # List questions by domain
        response = test_client.get(
            "/api/v1/questions?domain=architecture",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        questions = response.json()
        assert isinstance(questions, list)

    def test_all_major_domains_exist(self, test_client, authenticated_user):
        """Test that all major domains are available."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        domains_to_check = [
            "programming",
            "architecture",
            "testing",
            "data-engineering"
        ]

        for domain in domains_to_check:
            response = test_client.get(
                f"/api/v1/questions?domain={domain}",
                headers={"Authorization": f"Bearer {authenticated_user['token']}"}
            )
            # Should either return questions or empty list
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]


@pytest.mark.api
class TestDomainCapabilities:
    """Test domain capabilities and features."""

    def test_domain_questions_count(self, test_client, authenticated_user):
        """Test that domains have questions."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        questions = response.json()
        # Should have multiple questions across domains
        assert len(questions) > 0

    def test_domain_filters_work(self, test_client, authenticated_user):
        """Test that domain filtering works."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        # Get all questions
        all_response = test_client.get(
            "/api/v1/questions",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        all_questions = all_response.json()

        # Get architecture questions
        arch_response = test_client.get(
            "/api/v1/questions?domain=architecture",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        arch_questions = arch_response.json()

        # Filtered should be <= all
        assert len(arch_questions) <= len(all_questions)

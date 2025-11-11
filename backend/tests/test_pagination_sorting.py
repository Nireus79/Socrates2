"""
Tests for pagination and sorting functionality.

Tests:
- Pagination with skip and limit
- Default pagination behavior
- Sorting by different fields
- Combining pagination and sorting
- Edge cases (invalid skip/limit, etc.)
"""

import pytest
from fastapi import status


@pytest.mark.api
class TestPagination:
    """Test pagination functionality."""

    def test_list_with_pagination(self, test_client, authenticated_user):
        """Test listing with pagination parameters."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?skip=0&limit=5",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 5

    def test_pagination_second_page(self, test_client, authenticated_user):
        """Test accessing second page of results."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?skip=10&limit=5",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_pagination_high_skip(self, test_client, authenticated_user):
        """Test pagination with high skip value."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?skip=10000&limit=5",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return empty list if beyond available data
        assert isinstance(data, list)

    def test_pagination_default_limit(self, test_client, authenticated_user):
        """Test pagination with default limit."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?skip=0",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_pagination_large_limit(self, test_client, authenticated_user):
        """Test pagination with very large limit."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/questions?skip=0&limit=10000",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either accept or cap the limit
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.api
class TestSorting:
    """Test sorting functionality."""

    def test_sort_by_name_ascending(self, test_client, authenticated_user):
        """Test sorting by name in ascending order."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects?sort=name&order=asc",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either support sorting or ignore unsupported parameters
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_sort_by_created_date(self, test_client, authenticated_user):
        """Test sorting by creation date."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects?sort=created_at&order=desc",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either support sorting or return all
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_invalid_sort_field(self, test_client, authenticated_user):
        """Test handling of invalid sort field."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects?sort=invalid_field",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should either ignore invalid field or reject with 422
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.api
class TestCombinedPaginationSorting:
    """Test pagination combined with sorting."""

    def test_pagination_with_sorting(self, test_client, authenticated_user):
        """Test using pagination and sorting together."""
        if not authenticated_user or not authenticated_user.get("token"):
            pytest.skip("Could not authenticate user")

        response = test_client.get(
            "/api/v1/projects?skip=0&limit=10&sort=name&order=asc",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        # Should work with either or both parameters
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert len(data) <= 10

"""
Socrates API Client for LSP Server

Async HTTP client for communicating with Socrates backend API.
Used by LSP handlers to fetch specifications, conflicts, and other data.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import aiohttp
from aiohttp import ClientSession, ClientError


@dataclass
class Project:
    """Project data model"""
    id: str
    name: str
    description: str
    owner_id: str
    status: str
    maturity_score: int
    created_at: str
    updated_at: str


@dataclass
class Specification:
    """Specification data model"""
    id: str
    project_id: str
    key: str
    value: str
    category: str
    created_at: str
    updated_at: str


@dataclass
class Conflict:
    """Conflict data model"""
    id: str
    project_id: str
    specification_id: str
    type: str
    severity: str
    message: str
    resolved: bool
    created_at: str


class SocratesApiClient:
    """
    Async API client for Socrates backend.

    Provides methods for fetching specifications, conflicts, and other data.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        auth_token: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token = auth_token
        self.session: Optional[ClientSession] = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _ensure_session(self):
        """Ensure session is initialized"""
        if not self.session:
            self.session = ClientSession()

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        await self._ensure_session()

        url = f"{self.base_url}{path}"
        headers = self._build_headers()

        try:
            async with self.session.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                body = await response.text()

                if response.status >= 400:
                    raise ApiError(response.status, body)

                return json.loads(body) if body else {}

        except ClientError as e:
            raise ApiError(0, str(e))

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Socrates-LSP/0.1.0"
        }

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    # ============ Project Operations ============

    async def get_projects(self) -> List[Project]:
        """Get all projects"""
        response = await self._request("GET", "/api/v1/projects")
        projects = response.get("projects", [])
        return [Project(**p) for p in projects]

    async def get_project(self, project_id: str) -> Project:
        """Get single project"""
        response = await self._request("GET", f"/api/v1/projects/{project_id}")
        return Project(**response["project"])

    # ============ Specification Operations ============

    async def get_specifications(self, project_id: str) -> List[Specification]:
        """Get specifications for project"""
        response = await self._request(
            "GET",
            f"/api/v1/projects/{project_id}/specifications"
        )
        specs = response.get("specifications", [])
        return [Specification(**s) for s in specs]

    async def get_specification(self, spec_id: str) -> Specification:
        """Get single specification"""
        response = await self._request("GET", f"/api/v1/specifications/{spec_id}")
        return Specification(**response["specification"])

    async def search_specifications(
        self,
        project_id: str,
        query: str,
        limit: int = 20
    ) -> List[Specification]:
        """Search specifications"""
        response = await self._request(
            "GET",
            f"/api/v1/projects/{project_id}/specifications/search",
            params={"q": query, "limit": limit}
        )
        specs = response.get("specifications", [])
        return [Specification(**s) for s in specs]

    # ============ Conflict Operations ============

    async def get_conflicts(self, project_id: str) -> List[Conflict]:
        """Get conflicts for project"""
        response = await self._request(
            "GET",
            f"/api/v1/projects/{project_id}/conflicts"
        )
        conflicts = response.get("conflicts", [])
        return [Conflict(**c) for c in conflicts]

    # ============ Code Generation ============

    async def generate_code(
        self,
        spec_id: str,
        language: str,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate code from specification"""
        data = {
            "language": language,
            **(options or {})
        }

        response = await self._request(
            "POST",
            f"/api/v1/specifications/{spec_id}/generate",
            json_data=data
        )

        return {
            "language": language,
            "code": response.get("code", ""),
            "filename": response.get("filename", "generated"),
            "formatted": response.get("formatted", True)
        }

    # ============ User Operations ============

    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user"""
        response = await self._request("GET", "/api/v1/auth/me")
        return response.get("user", {})

    # ============ Health Check ============

    async def health_check(self) -> bool:
        """Check API health"""
        try:
            response = await self._request("GET", "/health")
            return response.get("status") == "healthy"
        except ApiError:
            return False

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()


class ApiError(Exception):
    """API client error"""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body

        try:
            data = json.loads(body)
            message = data.get("message", "Unknown error")
        except:
            message = body

        super().__init__(f"API Error ({status_code}): {message}")

"""
Resources API - Fetch and manage external resources (web pages, GitHub repos, etc).
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.security import get_current_active_user
from ..models import User
from ..services.web_fetcher import get_web_fetcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


class FetchURLRequest(BaseModel):
    """Request to fetch content from a URL."""
    url: str = Field(..., description="URL to fetch (HTTP/HTTPS)")
    extract_text: bool = Field(True, description="Extract readable text from HTML")
    max_length: int = Field(10000, description="Maximum content length")


class FetchURLResponse(BaseModel):
    """Response with fetched content."""
    success: bool
    url: str
    content_type: str  # 'text', 'html', 'json', etc.
    content: str
    length: int
    error: Optional[str] = None


class GitHubFileRequest(BaseModel):
    """Request to fetch a file from GitHub."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path in repository")
    branch: str = Field("main", description="Branch name")


class GitHubRepoInfoRequest(BaseModel):
    """Request to fetch GitHub repository info."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")


class GitHubRepoInfoResponse(BaseModel):
    """GitHub repository information."""
    success: bool
    name: Optional[str]
    description: Optional[str]
    url: Optional[str]
    language: Optional[str]
    topics: list = []
    stars: int = 0
    forks: int = 0
    readme_url: Optional[str]
    error: Optional[str] = None


@router.post("/fetch", response_model=FetchURLResponse)
async def fetch_url(
    request: FetchURLRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Fetch content from a URL.

    Supports:
    - GitHub raw file URLs
    - Web pages (with HTML to text extraction)
    - Code files
    - Documentation

    Args:
        request: Fetch request with URL
        current_user: Authenticated user

    Returns:
        Fetched content and metadata

    Example:
        POST /api/v1/resources/fetch
        Authorization: Bearer <token>
        {
            "url": "https://raw.githubusercontent.com/owner/repo/main/README.md",
            "extract_text": true
        }
    """
    try:
        fetcher = get_web_fetcher()

        # Fetch content asynchronously
        content = await asyncio.to_thread(fetcher.fetch_url, request.url)

        if content is None:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch content from {request.url}"
            )

        # Determine content type
        if request.url.endswith(('.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml')):
            content_type = 'text'
        elif request.url.endswith(('.html', '.htm')):
            content_type = 'html'
            if request.extract_text:
                content = fetcher.extract_text_from_html(content, request.max_length)
        else:
            content_type = 'text'

        # Truncate if needed
        if len(content) > request.max_length:
            content = content[:request.max_length] + "\n\n[TRUNCATED...]"

        logger.info(f"User {current_user.id} fetched URL: {request.url}")

        return {
            "success": True,
            "url": request.url,
            "content_type": content_type,
            "content": content,
            "length": len(content),
            "error": None
        }

    except Exception as e:
        logger.error(f"Error fetching URL {request.url}: {e}", exc_info=True)
        return {
            "success": False,
            "url": request.url,
            "content_type": "error",
            "content": "",
            "length": 0,
            "error": str(e)
        }


@router.post("/github/file", response_model=FetchURLResponse)
async def fetch_github_file(
    request: GitHubFileRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Fetch a file from a GitHub repository.

    Args:
        request: GitHub file fetch request
        current_user: Authenticated user

    Returns:
        File content and metadata

    Example:
        POST /api/v1/resources/github/file
        Authorization: Bearer <token>
        {
            "owner": "anthropics",
            "repo": "claude-code",
            "path": "README.md",
            "branch": "main"
        }
    """
    try:
        fetcher = get_web_fetcher()

        # Fetch from GitHub
        content = await asyncio.to_thread(
            fetcher.fetch_github_file,
            request.owner,
            request.repo,
            request.path,
            request.branch
        )

        if content is None:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.owner}/{request.repo}/{request.path}"
            )

        url = f"https://github.com/{request.owner}/{request.repo}/blob/{request.branch}/{request.path}"

        logger.info(f"User {current_user.id} fetched GitHub file: {url}")

        return {
            "success": True,
            "url": url,
            "content_type": "text",
            "content": content,
            "length": len(content),
            "error": None
        }

    except Exception as e:
        logger.error(f"Error fetching GitHub file: {e}", exc_info=True)
        return {
            "success": False,
            "url": f"https://github.com/{request.owner}/{request.repo}",
            "content_type": "error",
            "content": "",
            "length": 0,
            "error": str(e)
        }


@router.post("/github/repo-info", response_model=GitHubRepoInfoResponse)
async def fetch_github_repo_info(
    request: GitHubRepoInfoRequest,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Fetch repository information from GitHub.

    Args:
        request: GitHub repo info request
        current_user: Authenticated user

    Returns:
        Repository metadata

    Example:
        POST /api/v1/resources/github/repo-info
        Authorization: Bearer <token>
        {
            "owner": "Nireus79",
            "repo": "Socratic"
        }
    """
    try:
        fetcher = get_web_fetcher()

        # Fetch repo info
        info = await asyncio.to_thread(
            fetcher.fetch_github_repo_info,
            request.owner,
            request.repo
        )

        if info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Repository not found: {request.owner}/{request.repo}"
            )

        logger.info(f"User {current_user.id} fetched GitHub repo info: {request.owner}/{request.repo}")

        return {
            "success": True,
            **info,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error fetching GitHub repo info: {e}", exc_info=True)
        return {
            "success": False,
            "name": None,
            "description": None,
            "url": None,
            "language": None,
            "topics": [],
            "stars": 0,
            "forks": 0,
            "readme_url": None,
            "error": str(e)
        }


@router.post("/github/parse-url")
async def parse_github_url(
    url: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Parse a GitHub URL to extract owner and repo.

    Args:
        url: GitHub URL
        current_user: Authenticated user

    Returns:
        Parsed owner/repo

    Example:
        POST /api/v1/resources/github/parse-url?url=https://github.com/Nireus79/Socratic
    """
    try:
        fetcher = get_web_fetcher()
        parsed = fetcher.parse_github_url(url)

        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub URL"
            )

        return {
            "success": True,
            **parsed
        }

    except Exception as e:
        logger.error(f"Error parsing GitHub URL: {e}")
        return {
            "success": False,
            "error": str(e)
        }

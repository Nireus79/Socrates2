"""
Web Fetching Service - Fetch and parse content from URLs.

Supports:
- GitHub repository content
- Web pages (HTML to text conversion)
- Code files
- Documentation
"""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class WebFetcherService:
    """Service for fetching and parsing web content."""

    def __init__(self, timeout: int = 30):
        """
        Initialize web fetcher.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    async def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Content as string, or None if fetch fails
        """
        try:
            if not self._is_valid_url(url):
                logger.warning(f"Invalid URL: {url}")
                return None

            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = self.client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

            return response.text

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def fetch_github_file(self, owner: str, repo: str, path: str, branch: str = "main") -> Optional[str]:
        """
        Fetch a file from GitHub repository using raw GitHub URL.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            branch: Branch name (default: main)

        Returns:
            File content as string, or None if fetch fails
        """
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        return await self.fetch_url(raw_url)

    async def fetch_github_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Fetch repository information from GitHub API.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository info dict, or None if fetch fails
        """
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {'User-Agent': 'Socrates/1.0'}

            response = self.client.get(api_url, headers=headers)
            response.raise_for_status()

            data = response.json()
            return {
                'name': data.get('name'),
                'description': data.get('description'),
                'url': data.get('html_url'),
                'language': data.get('language'),
                'topics': data.get('topics', []),
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'readme_url': f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
            }

        except Exception as e:
            logger.error(f"Error fetching GitHub repo info for {owner}/{repo}: {e}")
            return None

    def extract_text_from_html(self, html: str, max_length: int = 10000) -> str:
        """
        Extract readable text from HTML content.

        Args:
            html: HTML content
            max_length: Maximum length of extracted text

        Returns:
            Extracted text
        """
        try:
            # Try to import beautifulsoup4 if available
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')

                # Remove script and style elements
                for script in soup(['script', 'style']):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)

            except ImportError:
                logger.warning("beautifulsoup4 not installed, falling back to simple text extraction")
                # Fallback: simple text extraction
                import re
                # Remove HTML tags
                text = re.sub('<[^<]+?>', '', html)
                # Decode HTML entities
                text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + '...'

            return text

        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return html[:max_length]

    def parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse GitHub repository URL to extract owner and repo.

        Args:
            url: GitHub URL (e.g., https://github.com/owner/repo)

        Returns:
            Dict with 'owner' and 'repo' keys, or None if not a valid GitHub URL
        """
        try:
            parsed = urlparse(url)

            # Check if it's a GitHub URL
            if 'github.com' not in parsed.netloc:
                return None

            # Extract owner/repo from path
            parts = parsed.path.strip('/').split('/')
            if len(parts) < 2:
                return None

            owner = parts[0]
            repo = parts[1].replace('.git', '')

            return {
                'owner': owner,
                'repo': repo,
                'url': f"https://github.com/{owner}/{repo}"
            }

        except Exception as e:
            logger.error(f"Error parsing GitHub URL {url}: {e}")
            return None

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ('http', 'https'), parsed.netloc])
        except Exception:
            return False

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()


# Singleton instance
_web_fetcher: Optional[WebFetcherService] = None


def get_web_fetcher() -> WebFetcherService:
    """
    Get or create web fetcher service.

    Returns:
        WebFetcherService instance
    """
    global _web_fetcher
    if _web_fetcher is None:
        _web_fetcher = WebFetcherService()
    return _web_fetcher

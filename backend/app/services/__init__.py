"""Services package - Business logic and external integrations."""

from .web_fetcher import WebFetcherService, get_web_fetcher

__all__ = [
    'WebFetcherService',
    'get_web_fetcher',
]

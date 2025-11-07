"""
ServiceContainer for dependency injection.

Provides centralized access to:
- Database sessions
- Logging
- Configuration
- Claude API client
- Agent Orchestrator

⚠️  NO FALLBACKS - All dependencies are REQUIRED.
Missing dependencies raise clear errors instead of returning None.
"""
from typing import Optional, TYPE_CHECKING
import logging
from anthropic import Anthropic
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocalAuth, SessionLocalSpecs

if TYPE_CHECKING:
    from ..agents.orchestrator import AgentOrchestrator


class ServiceContainer:
    """
    Central service container for dependency injection.

    Design principles:
    - NO fallback returns (no {} or None)
    - Raises exceptions if dependencies missing
    - Lazy loading (create on first use)
    - Thread-safe (each request gets its own sessions)

    Used by:
    - All agents via BaseAgent.__init__()
    - API endpoints for orchestrator access
    """

    def __init__(self):
        self._db_session_auth: Optional[Session] = None
        self._db_session_specs: Optional[Session] = None
        self._claude_client: Optional[Anthropic] = None
        self._logger_cache: dict = {}
        self._orchestrator: Optional['AgentOrchestrator'] = None

    def get_database_auth(self) -> Session:
        """
        Get auth database session.

        Returns:
            SQLAlchemy session for socrates_auth database

        Raises:
            Exception: If database connection fails
        """
        if self._db_session_auth is None:
            try:
                self._db_session_auth = SessionLocalAuth()
            except Exception as e:
                raise RuntimeError(f"Failed to create auth database session: {e}")

        return self._db_session_auth

    def get_database_specs(self) -> Session:
        """
        Get specs database session.

        Returns:
            SQLAlchemy session for socrates_specs database

        Raises:
            Exception: If database connection fails
        """
        if self._db_session_specs is None:
            try:
                self._db_session_specs = SessionLocalSpecs()
            except Exception as e:
                raise RuntimeError(f"Failed to create specs database session: {e}")

        return self._db_session_specs

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get logger instance.

        Args:
            name: Logger name (typically module name or agent ID)

        Returns:
            Configured logger instance
        """
        if name not in self._logger_cache:
            logger = logging.getLogger(name)

            # Only configure if not already configured
            if not logger.handlers:
                logger.setLevel(getattr(logging, settings.LOG_LEVEL))

                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)

            self._logger_cache[name] = logger

        return self._logger_cache[name]

    def get_config(self) -> dict:
        """
        Get configuration dictionary.

        Returns:
            Configuration as dictionary

        Raises:
            ValueError: If settings not properly configured
        """
        try:
            return settings.model_dump()
        except Exception as e:
            raise ValueError(f"Failed to get configuration: {e}")

    def get_claude_client(self) -> Anthropic:
        """
        Get Claude API client.

        Returns:
            Anthropic client instance

        Raises:
            ValueError: If ANTHROPIC_API_KEY not set
            Exception: If client creation fails
        """
        if self._claude_client is None:
            api_key = settings.ANTHROPIC_API_KEY

            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set in environment. "
                    "Please add it to your .env file."
                )

            try:
                self._claude_client = Anthropic(api_key=api_key)
            except Exception as e:
                raise RuntimeError(f"Failed to create Claude API client: {e}")

        return self._claude_client

    def get_orchestrator(self) -> 'AgentOrchestrator':
        """
        Get Agent Orchestrator instance.

        Returns:
            AgentOrchestrator instance

        Raises:
            RuntimeError: If orchestrator creation fails
        """
        if self._orchestrator is None:
            try:
                from ..agents.orchestrator import AgentOrchestrator
                self._orchestrator = AgentOrchestrator(self)
            except Exception as e:
                raise RuntimeError(f"Failed to create orchestrator: {e}")

        return self._orchestrator

    def close(self):
        """
        Clean up resources.
        Call this when request handling is complete.
        """
        if self._db_session_auth:
            self._db_session_auth.close()
            self._db_session_auth = None

        if self._db_session_specs:
            self._db_session_specs.close()
            self._db_session_specs = None


# Global singleton instance
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """
    Get global service container instance.

    Returns:
        ServiceContainer singleton

    Note: For request-scoped containers, create new instances
    instead of using this global singleton.
    """
    global _service_container

    if _service_container is None:
        _service_container = ServiceContainer()

    return _service_container


def reset_service_container():
    """
    Reset global service container.
    Useful for testing to ensure clean state.
    """
    global _service_container

    if _service_container is not None:
        _service_container.close()
        _service_container = None

"""
BaseAgent - Abstract base class for all agents.

Provides:
- Dependency injection via ServiceContainer
- Standardized request processing
- Built-in error handling
- Statistics tracking
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.core.dependencies import ServiceContainer


class BaseAgent(ABC):
    """
    Base class for all agents.

    Design principles:
    - REQUIRED dependencies (no fallbacks)
    - Standardized request/response format
    - Built-in error handling
    - Statistics tracking

    Subclasses must implement:
    - get_capabilities(): List capabilities this agent provides
    - _<action>() methods: One per capability

    Used by:
    - Phase 2+: All agent implementations
    - AgentOrchestrator: Routes requests to agents
    """

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        """
        Initialize base agent.

        Args:
            agent_id: Unique agent identifier (e.g., 'project_manager')
            name: Human-readable agent name (e.g., 'Project Manager Agent')
            services: ServiceContainer instance (REQUIRED)

        Raises:
            ValueError: If services is None
        """
        if services is None:
            raise ValueError(
                f"ServiceContainer is required for agent '{agent_id}'. "
                "Cannot create agent without dependencies."
            )

        self.agent_id = agent_id
        self.name = name
        self.services = services

        # Get dependencies (will raise if not available)
        self.logger = services.get_logger(f"agent.{agent_id}")
        self.config = services.get_config()

        # Note: Claude client and database sessions are available via:
        # - self.services.get_claude_client()
        # - self.services.get_database_auth()
        # - self.services.get_database_specs()

        # Statistics tracking
        self.stats = {
            'requests_processed': 0,
            'requests_succeeded': 0,
            'requests_failed': 0,
            'errors_encountered': 0,
            'last_activity': None,
            'created_at': datetime.utcnow().isoformat()
        }

        self.logger.info(f"Agent '{self.name}' initialized (ID: {self.agent_id})")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides.

        Returns:
            List of action names (e.g., ['create_project', 'list_projects'])

        Example:
            def get_capabilities(self):
                return ['create_project', 'update_project', 'delete_project']
        """
        pass

    def process_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request by routing to the appropriate method.

        Request flow:
        1. Validate action exists
        2. Call _<action>() method
        3. Track statistics
        4. Handle errors

        Args:
            action: Action to perform (must be in get_capabilities())
            data: Request data dictionary

        Returns:
            Response dictionary:
            - On success: {'success': True, 'data': <result>}
            - On failure: {'success': False, 'error': <message>, 'error_code': <code>}

        Example:
            result = agent.process_request('create_project', {
                'name': 'My Project',
                'description': 'A test project'
            })
        """
        self.stats['requests_processed'] += 1
        self.stats['last_activity'] = datetime.utcnow().isoformat()

        # Validate action is supported
        capabilities = self.get_capabilities()
        if action not in capabilities:
            self.stats['requests_failed'] += 1
            return {
                'success': False,
                'error': f"Unknown action '{action}' for agent '{self.agent_id}'",
                'error_code': 'UNKNOWN_ACTION',
                'available_capabilities': capabilities
            }

        # Route to method (e.g., action='create_project' → _create_project())
        method_name = f"_{action}"
        if not hasattr(self, method_name):
            self.stats['requests_failed'] += 1
            self.logger.error(
                f"Action '{action}' is listed in capabilities but "
                f"method '{method_name}' not implemented"
            )
            return {
                'success': False,
                'error': f"Action '{action}' not implemented",
                'error_code': 'NOT_IMPLEMENTED'
            }

        # Execute method
        try:
            method = getattr(self, method_name)
            self.logger.info(f"Processing {self.agent_id}.{action}")

            result = method(data)

            # Ensure result has proper format
            if not isinstance(result, dict):
                self.logger.warning(
                    f"Method {method_name} returned non-dict result: {type(result)}"
                )
                result = {'data': result}

            if 'success' not in result:
                result['success'] = True

            self.stats['requests_succeeded'] += 1
            return result

        except Exception as e:
            self.stats['requests_failed'] += 1
            self.stats['errors_encountered'] += 1
            self.logger.error(
                f"Error in {self.agent_id}.{action}: {str(e)}",
                exc_info=True
            )

            return {
                'success': False,
                'error': str(e),
                'error_code': 'AGENT_ERROR',
                'agent_id': self.agent_id,
                'action': action
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Dictionary with agent info and statistics
        """
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'capabilities': self.get_capabilities(),
            'stats': self.stats
        }

    def __repr__(self):
        """String representation of agent"""
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.name})>"

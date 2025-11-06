"""
AgentOrchestrator - Central coordinator for all agents.

Responsibilities:
- Agent registration
- Request routing to appropriate agent
- Capability validation
- Statistics aggregation
- Future: Quality control integration (Phase 5)
"""
from typing import Dict, Any, List, Optional
import logging

from ..core.dependencies import ServiceContainer
from .base import BaseAgent


class AgentOrchestrator:
    """
    Central orchestrator for all agents.

    Design:
    - Register agents on startup
    - Route requests to correct agent
    - Validate agent capabilities
    - Provide system-wide statistics

    Used by:
    - API endpoints: Route user requests to agents
    - Phase 2+: Manages ProjectManager, SocraticAgent, ContextAgent
    - Phase 5: Integrates with quality control system
    """

    def __init__(self, services: ServiceContainer):
        """
        Initialize orchestrator.

        Args:
            services: ServiceContainer instance
        """
        self.services = services
        self.logger = services.get_logger("orchestrator")
        self.agents: Dict[str, BaseAgent] = {}

        self.logger.info("AgentOrchestrator initialized")

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator.

        Args:
            agent: BaseAgent instance to register

        Raises:
            TypeError: If agent is not a BaseAgent
            ValueError: If agent_id already registered
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError(
                f"Agent must inherit from BaseAgent, got {type(agent)}"
            )

        if agent.agent_id in self.agents:
            raise ValueError(
                f"Agent with ID '{agent.agent_id}' is already registered"
            )

        self.agents[agent.agent_id] = agent

        capabilities = agent.get_capabilities()
        self.logger.info(
            f"Registered agent: {agent.agent_id} ({agent.name})"
        )
        self.logger.info(
            f"  Capabilities: {', '.join(capabilities)}"
        )

    def unregister_agent(self, agent_id: str):
        """
        Unregister an agent.

        Args:
            agent_id: ID of agent to unregister

        Raises:
            KeyError: If agent not found
        """
        if agent_id not in self.agents:
            raise KeyError(f"Agent '{agent_id}' not registered")

        agent = self.agents.pop(agent_id)
        self.logger.info(f"Unregistered agent: {agent_id}")

    def route_request(
        self,
        agent_id: str,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to appropriate agent.

        Args:
            agent_id: ID of agent to route to
            action: Action to perform
            data: Request data

        Returns:
            Response from agent:
            - On success: {'success': True, 'data': <result>}
            - On failure: {'success': False, 'error': <message>, 'error_code': <code>}
        """
        # Validate agent exists
        if agent_id not in self.agents:
            available_agents = list(self.agents.keys())
            self.logger.warning(
                f"Request to unknown agent '{agent_id}'. "
                f"Available: {available_agents}"
            )
            return {
                'success': False,
                'error': f"Unknown agent: {agent_id}",
                'error_code': 'UNKNOWN_AGENT',
                'available_agents': available_agents
            }

        agent = self.agents[agent_id]

        # Validate capability
        capabilities = agent.get_capabilities()
        if action not in capabilities:
            self.logger.warning(
                f"Agent '{agent_id}' does not support action '{action}'"
            )
            return {
                'success': False,
                'error': f"Agent '{agent_id}' does not support action '{action}'",
                'error_code': 'UNSUPPORTED_ACTION',
                'available_capabilities': capabilities
            }

        # Route to agent
        self.logger.info(f"Routing to {agent_id}.{action}")

        try:
            result = agent.process_request(action, data)
            return result

        except Exception as e:
            self.logger.error(
                f"Error routing to {agent_id}.{action}: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'error': f"Orchestrator error: {str(e)}",
                'error_code': 'ORCHESTRATOR_ERROR',
                'agent_id': agent_id,
                'action': action
            }

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered agents.

        Returns:
            List of agent info dictionaries
        """
        return [
            {
                'agent_id': agent.agent_id,
                'name': agent.name,
                'capabilities': agent.get_capabilities(),
                'stats': agent.stats
            }
            for agent in self.agents.values()
        ]

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            BaseAgent instance or None if not found
        """
        return self.agents.get(agent_id)

    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """
        Get all capabilities across all agents.

        Returns:
            Dictionary mapping agent_id → list of capabilities
        """
        return {
            agent_id: agent.get_capabilities()
            for agent_id, agent in self.agents.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.

        Returns:
            Dictionary with:
            - total_agents: Number of registered agents
            - agents: List of agent stats
            - total_requests: Sum of all requests across agents
        """
        agent_stats = [agent.get_stats() for agent in self.agents.values()]

        total_requests = sum(
            agent['stats']['requests_processed']
            for agent in agent_stats
        )

        return {
            'total_agents': len(self.agents),
            'agents': agent_stats,
            'total_requests': total_requests
        }


# Global singleton instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """
    Get global orchestrator instance.

    Returns:
        AgentOrchestrator singleton

    Note: For testing, use reset_orchestrator() to clean state
    """
    global _orchestrator

    if _orchestrator is None:
        from ..core.dependencies import get_service_container
        services = get_service_container()
        _orchestrator = AgentOrchestrator(services)

    return _orchestrator


def reset_orchestrator():
    """
    Reset global orchestrator.
    Useful for testing to ensure clean state.
    """
    global _orchestrator
    _orchestrator = None

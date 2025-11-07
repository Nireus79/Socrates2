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
        self.quality_controller = None  # Will be set after registration

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

        # Store reference to quality controller if registered
        if agent.agent_id == 'quality':
            self.quality_controller = agent
            self.logger.info("Quality Controller registered - quality gates enabled")

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

        # Quality Control Gate (Phase 5)
        if self.quality_controller and self._is_major_operation(agent_id, action):
            self.logger.info(f"Applying quality gates to {agent_id}.{action}")
            quality_result = self.quality_controller.process_request(
                'verify_operation',
                {
                    'agent_id': agent_id,
                    'action': action,
                    'operation_data': data
                }
            )

            if quality_result.get('is_blocking'):
                self.logger.warning(
                    f"Quality control BLOCKED {agent_id}.{action}: "
                    f"{quality_result['reason']}"
                )
                return {
                    'success': False,
                    'blocked_by': 'quality_control',
                    'reason': quality_result['reason'],
                    'quality_checks': quality_result.get('quality_checks', {}),
                    'error_code': 'QUALITY_GATE_FAILED'
                }

            self.logger.info(
                f"Quality gates passed for {agent_id}.{action}"
            )

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

    def _is_major_operation(self, agent_id: str, action: str) -> bool:
        """
        Determine if an operation needs quality control.

        Major operations that need quality gates:
        - socratic.generate_question: Check for bias
        - code.generate_code: Check coverage
        - context.extract_specifications: (optional, could add later)

        Args:
            agent_id: Agent identifier
            action: Action being performed

        Returns:
            True if quality control is needed
        """
        major_ops = {
            'socratic': ['generate_question'],
            'code': ['generate_code'],
        }

        return agent_id in major_ops and action in major_ops[agent_id]

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

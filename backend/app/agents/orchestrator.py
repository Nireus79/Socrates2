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

    def __init__(self, services: Optional[ServiceContainer] = None):
        """
        Initialize orchestrator.

        Args:
            services: ServiceContainer instance (optional, creates default if not provided)
        """
        if services is None:
            services = ServiceContainer()

        self.services = services
        self.logger = services.get_logger("orchestrator")
        self.agents: Dict[str, BaseAgent] = {}
        self.quality_controller = None  # Will be set after registration

        self.logger.info("AgentOrchestrator initialized")

    def register_agent(self, agent):
        """
        Register an agent with the orchestrator.

        Args:
            agent: BaseAgent instance to register (or mock for testing)

        Raises:
            ValueError: If agent_id already registered or agent lacks required attributes
        """
        # Check agent has required attributes (agent_id and name or agent_name)
        if not hasattr(agent, 'agent_id'):
            raise ValueError(f"Agent must have 'agent_id' attribute")

        if not (hasattr(agent, 'name') or hasattr(agent, 'agent_name')):
            raise ValueError(f"Agent must have 'name' or 'agent_name' attribute")

        if agent.agent_id in self.agents:
            raise ValueError(
                f"Agent with ID '{agent.agent_id}' is already registered"
            )

        self.agents[agent.agent_id] = agent

        # Store reference to quality controller if registered
        if agent.agent_id == 'quality':
            self.quality_controller = agent
            self.logger.info("Quality Controller registered - quality gates enabled")

        # Get agent name (try both name and agent_name for compatibility)
        agent_name = getattr(agent, 'name', None) or getattr(agent, 'agent_name', 'Unknown')

        # Try to get capabilities if available (for logging)
        try:
            capabilities = agent.get_capabilities()
            self.logger.info(
                f"Registered agent: {agent.agent_id} ({agent_name})"
            )
            self.logger.info(
                f"  Capabilities: {', '.join(capabilities)}"
            )
        except (AttributeError, TypeError):
            # Mock agents may not have get_capabilities or it might not be callable
            self.logger.info(
                f"Registered agent: {agent.agent_id} ({agent_name})"
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

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID (alias for get_agent_by_id).

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        return self.get_agent_by_id(agent_id)

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


def set_orchestrator(orchestrator: "AgentOrchestrator") -> None:
    """
    Set the global orchestrator instance.
    Useful for testing to inject a test orchestrator with test services.

    Args:
        orchestrator: The orchestrator instance to use globally
    """
    global _orchestrator
    _orchestrator = orchestrator


def initialize_default_agents(orchestrator: Optional[AgentOrchestrator] = None) -> AgentOrchestrator:
    """
    Initialize and register all default agents.

    This function registers all agents with the orchestrator and can be called:
    - From FastAPI lifespan context (app startup)
    - From tests to set up agent orchestration
    - Manually to reset the orchestrator with agents

    Args:
        orchestrator: Optional orchestrator instance. If None, uses/creates the global one.

    Returns:
        The orchestrator instance with agents registered
    """
    if orchestrator is None:
        orchestrator = get_orchestrator()

    # Skip if agents already registered
    if len(orchestrator.agents) > 0:
        orchestrator.logger.debug(f"Agents already registered: {list(orchestrator.agents.keys())}")
        return orchestrator

    # Import all agent classes
    from .project import ProjectManagerAgent
    from .socratic import SocraticCounselorAgent
    from .context import ContextAnalyzerAgent
    from .conflict_detector import ConflictDetectorAgent
    from .code_generator import CodeGeneratorAgent
    from .quality_controller import QualityControllerAgent
    from .user_learning import UserLearningAgent
    from .direct_chat import DirectChatAgent
    from .team_collaboration import TeamCollaborationAgent
    from .export import ExportAgent
    from .multi_llm import MultiLLMManager
    from .github_integration import GitHubIntegrationAgent

    services = orchestrator.services

    # Create all agents
    pm_agent = ProjectManagerAgent("project", "Project Manager", services)
    socratic_agent = SocraticCounselorAgent("socratic", "Socratic Counselor", services)
    context_agent = ContextAnalyzerAgent("context", "Context Analyzer", services)
    conflict_agent = ConflictDetectorAgent("conflict", "Conflict Detector", services)
    code_gen_agent = CodeGeneratorAgent("code_generator", "Code Generator", services)
    quality_agent = QualityControllerAgent("quality", "Quality Controller", services)
    learning_agent = UserLearningAgent("learning", "User Learning", services)
    direct_chat_agent = DirectChatAgent("direct_chat", "Direct Chat", services)
    team_agent = TeamCollaborationAgent("team", "Team Collaboration", services)
    export_agent = ExportAgent("export", "Export Agent", services)
    llm_agent = MultiLLMManager("llm", "Multi-LLM Manager", services)
    github_agent = GitHubIntegrationAgent("github", "GitHub Integration", services)

    # Register all agents (quality agent first for proper controller setup)
    orchestrator.register_agent(pm_agent)
    orchestrator.register_agent(socratic_agent)
    orchestrator.register_agent(context_agent)
    orchestrator.register_agent(conflict_agent)
    orchestrator.register_agent(code_gen_agent)
    orchestrator.register_agent(quality_agent)
    orchestrator.register_agent(learning_agent)
    orchestrator.register_agent(direct_chat_agent)
    orchestrator.register_agent(team_agent)
    orchestrator.register_agent(export_agent)
    orchestrator.register_agent(llm_agent)
    orchestrator.register_agent(github_agent)

    orchestrator.logger.info("AgentOrchestrator initialized with default agents")
    orchestrator.logger.info(f"Registered agents: {list(orchestrator.agents.keys())}")

    return orchestrator

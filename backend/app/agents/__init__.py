"""
Agent system (BaseAgent, Orchestrator, and all agent implementations)
"""
from .base import BaseAgent
from .code_generator import CodeGeneratorAgent
from .conflict_detector import ConflictDetectorAgent
from .context import ContextAnalyzerAgent
from .export import ExportAgent
from .github_integration import GitHubIntegrationAgent
from .multi_llm import MultiLLMManager
from .orchestrator import AgentOrchestrator, get_orchestrator, reset_orchestrator
from .project import ProjectManagerAgent
from .socratic import SocraticCounselorAgent
from .team_collaboration import TeamCollaborationAgent

__all__ = [
    'BaseAgent',
    'AgentOrchestrator',
    'get_orchestrator',
    'reset_orchestrator',
    'ProjectManagerAgent',
    'SocraticCounselorAgent',
    'ContextAnalyzerAgent',
    'ConflictDetectorAgent',
    'CodeGeneratorAgent',
    'TeamCollaborationAgent',
    'ExportAgent',
    'MultiLLMManager',
    'GitHubIntegrationAgent',
]

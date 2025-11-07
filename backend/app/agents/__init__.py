"""
Agent system (BaseAgent, Orchestrator, and all agent implementations)
"""
from .base import BaseAgent
from .orchestrator import AgentOrchestrator, get_orchestrator, reset_orchestrator
from .project import ProjectManagerAgent
from .socratic import SocraticCounselorAgent
from .context import ContextAnalyzerAgent
from .conflict_detector import ConflictDetectorAgent
from .code_generator import CodeGeneratorAgent
from .team_collaboration import TeamCollaborationAgent
from .export import ExportAgent
from .multi_llm import MultiLLMManager
from .github_integration import GitHubIntegrationAgent

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

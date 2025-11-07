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
]

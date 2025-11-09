"""
Main FastAPI application.

Socrates2 - AI-Powered Specification Assistant
Phase 1: Infrastructure Foundation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Callable, Optional
import logging

from .core.config import settings
from .core.database import close_db_connections
from .api import auth, admin, projects, sessions, conflicts, code_generation, quality, teams
from .api import export_endpoints, llm_endpoints, github_endpoints
from .api import search, insights, templates

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _register_default_agents():
    """
    Register all agents with the orchestrator.
    This is the default startup behavior.
    """
    from .agents.orchestrator import get_orchestrator
    from .agents.project import ProjectManagerAgent
    from .agents.socratic import SocraticCounselorAgent
    from .agents.context import ContextAnalyzerAgent
    from .agents.conflict_detector import ConflictDetectorAgent
    from .agents.code_generator import CodeGeneratorAgent
    from .agents.quality_controller import QualityControllerAgent
    from .agents.user_learning import UserLearningAgent
    from .agents.direct_chat import DirectChatAgent
    from .agents.team_collaboration import TeamCollaborationAgent
    from .agents.export import ExportAgent
    from .agents.multi_llm import MultiLLMManager
    from .agents.github_integration import GitHubIntegrationAgent
    from .core.dependencies import get_service_container

    orchestrator = get_orchestrator()
    services = get_service_container()

    # Register all agents
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

    orchestrator.register_agent(pm_agent)
    orchestrator.register_agent(socratic_agent)
    orchestrator.register_agent(context_agent)
    orchestrator.register_agent(conflict_agent)
    orchestrator.register_agent(code_gen_agent)
    orchestrator.register_agent(quality_agent)  # Register quality agent before learning
    orchestrator.register_agent(learning_agent)
    orchestrator.register_agent(direct_chat_agent)
    orchestrator.register_agent(team_agent)
    orchestrator.register_agent(export_agent)
    orchestrator.register_agent(llm_agent)
    orchestrator.register_agent(github_agent)

    logger.info("AgentOrchestrator initialized")
    logger.info(f"Registered agents: {list(orchestrator.agents.keys())}")


def create_app(register_agents_fn: Optional[Callable] = None) -> FastAPI:
    """
    Create FastAPI application with configurable agent registration.

    This allows tests to inject custom agent registration logic without
    modifying the main app or using mocks/patches.

    Args:
        register_agents_fn: Optional custom function to register agents.
                           If None, uses default agent registration.

    Returns:
        Configured FastAPI application
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Application lifespan context manager.
        Handles startup and shutdown events.
        """
        # Startup
        logger.info("Starting Socrates2 API...")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Debug mode: {settings.DEBUG}")

        # Initialize orchestrator and register agents
        if register_agents_fn:
            # Use injected agent registration function
            register_agents_fn()
        else:
            # Use default agent registration
            _register_default_agents()

        yield

        # Shutdown
        logger.info("Shutting down Socrates2 API...")
        close_db_connections()
        logger.info("Database connections closed")

    # Create FastAPI application
    app = FastAPI(
        title="Socrates2 API",
        description="AI-Powered Specification Assistant",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.DEBUG
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]  # Standard FastAPI middleware pattern, type checker limitation
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(projects.router)
    app.include_router(sessions.router)
    app.include_router(conflicts.router)
    app.include_router(code_generation.router)
    app.include_router(quality.router)
    app.include_router(teams.router)
    app.include_router(export_endpoints.router)
    app.include_router(llm_endpoints.router)
    app.include_router(github_endpoints.router)
    app.include_router(search.router)
    app.include_router(insights.router)
    app.include_router(templates.router)

    return app


# Create default app instance (used by uvicorn in production)
app = create_app()


@app.get("/")
def root():
    """
    Root endpoint.

    Returns:
        Welcome message with API info
    """
    return {
        "message": "Socrates2 API",
        "version": "0.1.0",
        "phase": "Phase 1 - Infrastructure Foundation",
        "docs": "/docs",
        "health": "/api/v1/admin/health"
    }


@app.get("/api/v1/info")
def api_info():
    """
    API information endpoint.

    Returns:
        Detailed API information
    """
    from .agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    agent_info = orchestrator.get_all_agents()

    return {
        "api": {
            "title": "Socrates2 API",
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
            "phase": "Phase 1"
        },
        "agents": {
            "total": len(agent_info),
            "registered": [agent['agent_id'] for agent in agent_info]
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

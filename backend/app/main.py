"""
Main FastAPI application.

Socrates2 - AI-Powered Specification Assistant
Phase 1: Infrastructure Foundation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .core.database import close_db_connections
from .api import auth, admin

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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

    # Initialize orchestrator (will be done when first accessed)
    from .agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    logger.info("AgentOrchestrator initialized")
    logger.info(f"Registered agents: {list(orchestrator.agents.keys())}")

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
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)


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

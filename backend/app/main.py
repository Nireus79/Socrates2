"""
Main FastAPI application.

Socrates2 - AI-Powered Specification Assistant
Phase 7.0+: Pluggifiable Domain Architecture (COMPLETE)
Phase 7.2: Domain API Integration (IN PROGRESS)
"""
import logging
from contextlib import asynccontextmanager
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from .api import (
    admin,
    analytics,
    auth,
    billing,
    code_generation,
    collaboration,
    conflicts,
    documents,
    domains,
    export,
    export_endpoints,
    github_endpoints,
    insights,
    jobs,
    llm_endpoints,
    notifications,
    projects,
    quality,
    resources,
    search,
    sessions,
    teams,
    templates,
    workflows,
)
from .api.error_handlers import (
    general_exception_handler,
    http_exception_handler,
    validation_error_handler,
)
from .core.action_logger import initialize_action_logger
from .core.config import settings
from .core.database import close_db_connections
from .core.sentry_config import init_sentry

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
    from .agents.orchestrator import initialize_default_agents
    initialize_default_agents()
    logger.info("AgentOrchestrator initialized with default agents")


def _initialize_job_scheduler():
    """
    Initialize the background job scheduler.
    Registers all scheduled tasks.
    """
    from .jobs import aggregate_daily_analytics, cleanup_old_sessions
    from .services.job_scheduler import get_scheduler

    scheduler = get_scheduler()
    scheduler.start()

    # Register jobs
    # Daily analytics aggregation at 2 AM UTC
    scheduler.add_job(
        aggregate_daily_analytics,
        trigger="cron",
        job_id="daily_analytics_aggregation",
        name="Daily Analytics Aggregation",
        hour=2,
        minute=0,
        timezone="UTC"
    )

    # Session cleanup at 3 AM UTC
    scheduler.add_job(
        cleanup_old_sessions,
        trigger="cron",
        job_id="cleanup_old_sessions",
        name="Clean Up Old Sessions",
        hour=3,
        minute=0,
        timezone="UTC"
    )

    logger.info("Background job scheduler initialized with registered jobs")


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
    # Initialize Sentry error tracking before creating the app
    init_sentry()

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

        # Initialize action logging with configuration
        initialize_action_logger(
            enabled=settings.ACTION_LOGGING_ENABLED,
            log_level=settings.ACTION_LOG_LEVEL
        )
        logger.info(f"Action logging: {'ENABLED' if settings.ACTION_LOGGING_ENABLED else 'DISABLED'}")

        # Initialize background job scheduler
        _initialize_job_scheduler()

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

        # Shutdown job scheduler
        from .services.job_scheduler import get_scheduler
        scheduler = get_scheduler()
        if scheduler.is_running:
            scheduler.stop()
            logger.info("Job scheduler stopped")

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
    app.include_router(resources.router)
    app.include_router(jobs.router)
    app.include_router(billing.router)
    app.include_router(documents.router)
    app.include_router(notifications.router)
    app.include_router(export.router)
    app.include_router(collaboration.router)
    app.include_router(domains.router)
    app.include_router(workflows.router)
    app.include_router(analytics.router)

    # Register exception handlers for error tracking and proper response formatting
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

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
        "phase": "Phase 7.4 - Advanced Analytics System",
        "domains_infrastructure": "Phase 7.0 (Complete - 197 tests passing)",
        "domains_api": "Phase 7.2 (Complete)",
        "workflows": "Phase 7.3 (Complete - 29 tests passing)",
        "analytics": "Phase 7.4 (In Development)",
        "docs": "/docs",
        "domains_endpoint": "/api/v1/domains",
        "workflows_endpoint": "/api/v1/workflows",
        "analytics_endpoint": "/api/v1/analytics",
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
            "phase": "Phase 7.4 - Advanced Analytics System",
            "domains": {
                "infrastructure": "Phase 7.0 (COMPLETE - 197 tests)",
                "api_integration": "Phase 7.2 (COMPLETE)",
                "workflows": "Phase 7.3 (COMPLETE - 29 tests)",
                "analytics": "Phase 7.4 (IN PROGRESS)",
                "total_tests": "226 passing"
            }
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

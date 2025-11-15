"""
Database configuration and session management.

⚠️  CRITICAL: This file implements SAFE session management to prevent
data loss bug that killed the previous attempt.

Previous bug: Session closed before commit synced to disk → Zero data persistence
Solution: Explicit commit BEFORE closing + proper session lifecycle management
"""
import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

# Global engine caches - lazily initialized on first access
_engine_auth = None
_engine_specs = None


# Create two engines for two-database architecture
# SQLite doesn't support pool_size/max_overflow, so detect and configure appropriately
def _create_engine(url: str):
    """Create SQLAlchemy engine with appropriate pooling for database type."""
    engine_kwargs = {
        "echo": settings.DEBUG,  # Log SQL in debug mode
    }

    # Only use pooling parameters for PostgreSQL, not SQLite
    if url and not url.startswith("sqlite"):
        engine_kwargs.update({
            "pool_pre_ping": True,  # Verify connections before using
            "pool_size": 20,  # INCREASED: Handle LLM calls that hold connections
            "max_overflow": 40,  # INCREASED: Allow more concurrent LLM operations
            "pool_recycle": 3600,  # Recycle connections after 1 hour to prevent stale connections
        })
    elif url and url.startswith("sqlite"):
        # SQLite-specific settings for in-memory testing
        if ":memory:" in url:
            engine_kwargs.update({
                "connect_args": {"check_same_thread": False},
                "poolclass": None,  # Don't use connection pooling for memory DB
            })

    return create_engine(url, **engine_kwargs)


def _get_engine_auth():
    """Get or create auth engine (lazy initialization)."""
    global _engine_auth
    if _engine_auth is None:
        try:
            _engine_auth = _create_engine(settings.DATABASE_URL_AUTH)
            _register_event_listeners(_engine_auth, "Auth")
        except Exception as e:
            logger.warning(f"Failed to create auth engine: {e}. You may need Phase 1b configuration.")
            _engine_auth = None
    return _engine_auth


def _get_engine_specs():
    """Get or create specs engine (lazy initialization)."""
    global _engine_specs
    if _engine_specs is None:
        try:
            _engine_specs = _create_engine(settings.DATABASE_URL_SPECS)
            _register_event_listeners(_engine_specs, "Specs")
        except Exception as e:
            logger.warning(f"Failed to create specs engine: {e}. You may need Phase 1b configuration.")
            _engine_specs = None
    return _engine_specs


# Create property-like access to engines
class _LazyEngineProxy:
    """Proxy that defers engine creation until first use."""

    def __init__(self, getter_func):
        self._getter = getter_func
        self._engine = None

    def __getattr__(self, name):
        if self._engine is None:
            self._engine = self._getter()
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. "
                "Phase 1b requires DATABASE_URL configuration. "
                "See Phase 1b documentation for setup."
            )
        return getattr(self._engine, name)


engine_auth = _LazyEngineProxy(_get_engine_auth)
engine_specs = _LazyEngineProxy(_get_engine_specs)

# Create session factories
SessionLocalAuth = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_auth
)

SessionLocalSpecs = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_specs
)

# Create scoped sessions for thread-safe access
ScopedSessionAuth = scoped_session(SessionLocalAuth)
ScopedSessionSpecs = scoped_session(SessionLocalSpecs)

# Declarative base for models
Base = declarative_base()


def get_db_auth() -> Generator[Session, None, None]:
    """
    Get auth database session with SAFE lifecycle management.

    ✅ SAFE: Commits explicitly before closing
    ✅ SAFE: Rolls back on exception
    ✅ SAFE: Always closes session

    ⚠️  CRITICAL: This pattern prevents the archive killer bug where
    sessions closed before data synced to disk.
    """
    db = SessionLocalAuth()
    try:
        yield db
        # ✅ EXPLICIT COMMIT before closing
        # This ensures data is synced to disk before session ends
        db.commit()
    except Exception as e:
        logger.error(f"Database error in auth session: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def get_db_specs() -> Generator[Session, None, None]:
    """
    Get specs database session with SAFE lifecycle management.

    ✅ SAFE: Commits explicitly before closing
    ✅ SAFE: Rolls back on exception
    ✅ SAFE: Always closes session

    ⚠️  CRITICAL: This pattern prevents the archive killer bug where
    sessions closed before data synced to disk.
    """
    db = SessionLocalSpecs()
    try:
        yield db
        # ✅ EXPLICIT COMMIT before closing
        # This ensures data is synced to disk before session ends
        db.commit()
    except Exception as e:
        logger.error(f"Database error in specs session: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


# Event listeners for connection pool debugging (registered lazily when engines are created)
def _register_event_listeners(engine, engine_name: str):
    """Register event listeners for an engine (called when engine is first created)."""
    try:
        def on_connect(dbapi_conn, connection_record):
            logger.debug(f"{engine_name} database connection established")

        event.listens_for(engine, "connect")(on_connect)
    except Exception as e:
        logger.debug(f"Could not register event listener for {engine_name}: {e}")


def init_db():
    """
    Initialize database tables.
    This is for testing only - production uses Alembic migrations.
    """
    Base.metadata.create_all(bind=engine_auth)
    Base.metadata.create_all(bind=engine_specs)
    logger.info("Database tables initialized")


def close_db_connections():
    """
    Close all database connections.
    Call this on application shutdown.
    """
    engine_auth.dispose()
    engine_specs.dispose()
    ScopedSessionAuth.remove()
    ScopedSessionSpecs.remove()
    logger.info("Database connections closed")

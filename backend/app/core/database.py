"""
Database configuration and session management.

⚠️  CRITICAL: This file implements SAFE session management to prevent
data loss bug that killed the previous attempt.

Previous bug: Session closed before commit synced to disk → Zero data persistence
Solution: Explicit commit BEFORE closing + proper session lifecycle management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

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
            "pool_size": 5,
            "max_overflow": 10,
        })
    elif url and url.startswith("sqlite"):
        # SQLite-specific settings for in-memory testing
        if ":memory:" in url:
            engine_kwargs.update({
                "connect_args": {"check_same_thread": False},
                "poolclass": None,  # Don't use connection pooling for memory DB
            })

    return create_engine(url, **engine_kwargs)

engine_auth = _create_engine(settings.DATABASE_URL_AUTH)

engine_specs = _create_engine(settings.DATABASE_URL_SPECS)

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


# Event listeners for connection pool debugging
@event.listens_for(engine_auth, "connect")
def receive_connect_auth(dbapi_conn, connection_record):
    """Log when new auth database connection is created"""
    logger.debug("Auth database connection established")


@event.listens_for(engine_specs, "connect")
def receive_connect_specs(dbapi_conn, connection_record):
    """Log when new specs database connection is created"""
    logger.debug("Specs database connection established")


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

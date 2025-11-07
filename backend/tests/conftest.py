"""
Pytest configuration and fixtures for Socrates2 tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def database_url_auth():
    """Get auth database URL from environment"""
    url = os.getenv("DATABASE_URL_AUTH")
    if not url:
        pytest.skip("DATABASE_URL_AUTH not set in environment")
    return url


@pytest.fixture(scope="session")
def database_url_specs():
    """Get specs database URL from environment"""
    url = os.getenv("DATABASE_URL_SPECS")
    if not url:
        pytest.skip("DATABASE_URL_SPECS not set in environment")
    return url


@pytest.fixture(scope="session")
def auth_engine(database_url_auth):
    """Create SQLAlchemy engine for auth database"""
    engine = create_engine(database_url_auth)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def specs_engine(database_url_specs):
    """Create SQLAlchemy engine for specs database"""
    engine = create_engine(database_url_specs)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def auth_session(auth_engine):
    """Create a database session for auth database (with rollback)"""
    connection = auth_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def specs_session(specs_engine):
    """Create a database session for specs database (with rollback)"""
    connection = specs_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude API client for testing"""
    from unittest.mock import Mock
    return Mock()

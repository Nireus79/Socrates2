"""
Core application components (config, database, security)

This package contains core infrastructure:
- config: Application settings
- database: Database connections and sessions
- security: Authentication and authorization
- dependencies: Dependency injection container

Import directly from submodules using relative imports:
    from .config import settings
    from .database import get_db_auth
    from .security import create_access_token
"""

# Don't import everything here - it causes circular imports
# Let modules import what they need directly using relative imports

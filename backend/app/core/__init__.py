"""
Core application components (config, database, security)

This package contains core infrastructure:
- config: Application settings
- database: Database connections and sessions
- security: Authentication and authorization
- dependencies: Dependency injection container

Import directly from submodules, not from this __init__.py:
    from app.core.config import settings
    from app.core.database import get_db_auth
    from app.core.security import create_access_token
"""

# Don't import everything here - it causes circular imports
# Let modules import what they need directly:
#   from app.core.config import settings
#   from app.core.database import get_db_auth
#   etc.

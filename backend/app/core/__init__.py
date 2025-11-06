"""
Core application components (config, database, security)
"""
from app.core.config import settings, get_settings
from app.core.database import (
    get_db_auth,
    get_db_specs,
    engine_auth,
    engine_specs,
    Base,
    init_db,
    close_db_connections
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    get_current_active_user,
    get_current_admin_user
)
from app.core.dependencies import (
    ServiceContainer,
    get_service_container,
    reset_service_container
)

__all__ = [
    'settings',
    'get_settings',
    'get_db_auth',
    'get_db_specs',
    'engine_auth',
    'engine_specs',
    'Base',
    'init_db',
    'close_db_connections',
    'create_access_token',
    'decode_access_token',
    'get_current_user',
    'get_current_active_user',
    'get_current_admin_user',
    'ServiceContainer',
    'get_service_container',
    'reset_service_container',
]

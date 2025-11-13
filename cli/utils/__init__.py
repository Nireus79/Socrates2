"""
Shared utilities for CLI commands.

Contains common functions, constants, and utilities used by all command modules.
"""

from cli.utils.constants import (
    DOMAINS,
    ROLES,
    PROJECT_STATUSES,
    SESSION_MODES,
    MESSAGE_SUCCESS,
    MESSAGE_ERROR,
    MESSAGE_WARNING,
)
from cli.utils.helpers import (
    format_uuid,
    truncate_string,
    is_valid_uuid,
    parse_datetime,
    format_datetime,
)
from cli.utils.prompts import (
    prompt_choice,
    prompt_confirm,
    prompt_text,
    prompt_email,
    select_from_list,
)
from cli.utils.table_formatter import (
    create_table,
    format_project_table,
    format_session_table,
    format_team_table,
)

__all__ = [
    # Constants
    "DOMAINS",
    "ROLES",
    "PROJECT_STATUSES",
    "SESSION_MODES",
    "MESSAGE_SUCCESS",
    "MESSAGE_ERROR",
    "MESSAGE_WARNING",
    # Helpers
    "format_uuid",
    "truncate_string",
    "is_valid_uuid",
    "parse_datetime",
    "format_datetime",
    # Prompts
    "prompt_choice",
    "prompt_confirm",
    "prompt_text",
    "prompt_email",
    "select_from_list",
    # Tables
    "create_table",
    "format_project_table",
    "format_session_table",
    "format_team_table",
]

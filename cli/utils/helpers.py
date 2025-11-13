"""
Helper functions shared across all CLI commands.

Contains utility functions for string formatting, UUID handling, date/time operations, etc.
"""

import uuid
from datetime import datetime
from typing import Optional


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def format_uuid(value: str, length: int = 8) -> str:
    """
    Format UUID for display (show first N characters).

    Args:
        value: UUID string
        length: Number of characters to show

    Returns:
        Formatted UUID string
    """
    if not value:
        return "N/A"
    return value[:length]


def truncate_string(value: str, max_length: int = 50) -> str:
    """
    Truncate string to max length with ellipsis.

    Args:
        value: String to truncate
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if not value:
        return ""
    if len(value) <= max_length:
        return value
    return value[:max_length - 3] + "..."


def parse_datetime(value: str) -> Optional[datetime]:
    """
    Parse ISO format datetime string.

    Args:
        value: ISO format datetime string

    Returns:
        datetime object or None if parsing fails
    """
    if not value:
        return None

    try:
        # Handle ISO format with timezone
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        # Try parsing with timezone
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            # Try without timezone
            return datetime.fromisoformat(value)

    except (ValueError, TypeError):
        return None


def format_datetime(value: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime for display.

    Args:
        value: datetime object
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    if not value:
        return "N/A"

    if isinstance(value, str):
        value = parse_datetime(value)
        if not value:
            return "N/A"

    return value.strftime(format_str)


def format_time_ago(value: Optional[datetime]) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").

    Args:
        value: datetime object

    Returns:
        Relative time string
    """
    if not value:
        return "N/A"

    if isinstance(value, str):
        value = parse_datetime(value)
        if not value:
            return "N/A"

    now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
    delta = now - value

    seconds = delta.total_seconds()
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"


def slugify(value: str) -> str:
    """
    Convert string to slug format (lowercase, hyphens).

    Args:
        value: String to slugify

    Returns:
        Slugified string
    """
    if not value:
        return ""

    return value.lower().replace(" ", "-").replace("_", "-")


def pluralize(word: str, count: int) -> str:
    """
    Pluralize word if count != 1.

    Args:
        word: Word to pluralize
        count: Count

    Returns:
        Word (possibly pluralized)
    """
    if count == 1:
        return word
    # Simple pluralization - doesn't handle all cases
    if word.endswith("y"):
        return word[:-1] + "ies"
    return word + "s"


def format_bytes(size_bytes: int) -> str:
    """
    Format bytes as human-readable size.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f}TB"


def parse_choice_input(input_str: str, max_choices: int) -> Optional[int]:
    """
    Parse user input as a choice number.

    Args:
        input_str: User input string
        max_choices: Maximum valid choice number

    Returns:
        Choice number (1-indexed) or None if invalid
    """
    try:
        choice = int(input_str)
        if 1 <= choice <= max_choices:
            return choice
        return None
    except (ValueError, TypeError):
        return None

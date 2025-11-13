"""
Input validation utilities for Socrates.

Provides validators for emails, passwords, usernames, project names, and other user inputs.
"""

import re


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise

    Validation rules:
    - Must contain exactly one @ symbol
    - Must have non-empty local part (before @)
    - Must have non-empty domain part (after @)
    - Domain must contain at least one dot (.)
    - Must not contain spaces
    """
    if not email or not isinstance(email, str):
        return False

    # Check for spaces
    if " " in email:
        return False

    # Must have exactly one @
    if email.count("@") != 1:
        return False

    # Split into local and domain
    local, domain = email.split("@")

    # Both parts must be non-empty
    if not local or not domain:
        return False

    # Domain must have at least one dot
    if "." not in domain:
        return False

    return True


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.

    Validation rules:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character (!@#$%^&*)
    - Must not contain spaces
    """
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string"

    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Check for spaces
    if " " in password:
        return False, "Password must not contain spaces"

    # Check for uppercase
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    # Check for lowercase
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    # Check for digit
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    # Check for special character
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>?/\\|`~]", password):
        return False, "Password must contain at least one special character (!@#$%^&*)"

    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.

    Validation rules:
    - Minimum 3 characters
    - Maximum 30 characters
    - Only alphanumeric characters, underscores, and hyphens
    - Must start with letter or number
    - Must not contain spaces
    """
    if not username or not isinstance(username, str):
        return False, "Username must be a non-empty string"

    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 30:
        return False, "Username must not exceed 30 characters"

    # Check for spaces
    if " " in username:
        return False, "Username must not contain spaces"

    # Check format: alphanumeric, underscore, hyphen
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", username):
        return False, "Username must start with letter or number and contain only alphanumeric characters, underscores, and hyphens"

    return True, ""


def validate_project_name(project_name: str) -> tuple[bool, str]:
    """
    Validate project name format.

    Args:
        project_name: Project name to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.

    Validation rules:
    - Minimum 3 characters
    - Maximum 100 characters
    - Alphanumeric, spaces, underscores, hyphens, parentheses allowed
    - Must not start or end with space or special character
    """
    if not project_name or not isinstance(project_name, str):
        return False, "Project name must be a non-empty string"

    # Check length
    if len(project_name) < 3:
        return False, "Project name must be at least 3 characters long"

    if len(project_name) > 100:
        return False, "Project name must not exceed 100 characters"

    # Check format: alphanumeric, spaces, underscores, hyphens, parentheses
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\s_\-()]*[a-zA-Z0-9)]$", project_name):
        return False, "Project name must start and end with alphanumeric character and contain only letters, numbers, spaces, underscores, hyphens, and parentheses"

    # Check for multiple consecutive spaces
    if "  " in project_name:
        return False, "Project name must not contain multiple consecutive spaces"

    return True, ""


def validate_team_name(team_name: str) -> tuple[bool, str]:
    """
    Validate team name format.

    Args:
        team_name: Team name to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.

    Validation rules:
    - Minimum 2 characters
    - Maximum 50 characters
    - Alphanumeric, spaces, underscores, hyphens allowed
    - Must not start or end with space or special character
    """
    if not team_name or not isinstance(team_name, str):
        return False, "Team name must be a non-empty string"

    # Check length
    if len(team_name) < 2:
        return False, "Team name must be at least 2 characters long"

    if len(team_name) > 50:
        return False, "Team name must not exceed 50 characters"

    # Check format: alphanumeric, spaces, underscores, hyphens
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\s_-]*[a-zA-Z0-9]$", team_name):
        return False, "Team name must start and end with alphanumeric character and contain only letters, numbers, spaces, underscores, and hyphens"

    # Check for multiple consecutive spaces
    if "  " in team_name:
        return False, "Team name must not contain multiple consecutive spaces"

    return True, ""

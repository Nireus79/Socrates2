"""
Input validation utilities for Socrates.

Provides validators for emails, passwords, and other user inputs.
"""


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

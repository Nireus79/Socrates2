"""
Input validation and sanitization utilities.

Provides comprehensive validation for common input patterns:
- Email addresses
- File uploads
- Text content (messages, descriptions)
- UUIDs and IDs
- Enum values
- Pagination parameters
"""
import logging
import re
from typing import List, Optional

from email_validator import EmailNotValidError, validate_email

logger = logging.getLogger(__name__)

# Constants for validation
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

MAX_MESSAGE_LENGTH = 10000
MAX_DESCRIPTION_LENGTH = 5000
MAX_EMAIL_LENGTH = 255
MAX_NAME_LENGTH = 255

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# File type whitelist
ALLOWED_FILE_TYPES = {
    'pdf': 'application/pdf',
    'txt': 'text/plain',
    'json': 'application/json',
    'csv': 'text/csv',
    'md': 'text/markdown',
    'yaml': 'application/yaml',
    'yml': 'application/yaml',
}


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ValidationService:
    """Comprehensive input validation service."""

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate and normalize email address.

        Args:
            email: Email address to validate

        Returns:
            Normalized email address

        Raises:
            ValidationError: If email is invalid
        """
        if not email or len(email) > MAX_EMAIL_LENGTH:
            raise ValidationError(f"Email must be between 1 and {MAX_EMAIL_LENGTH} characters")

        try:
            # Validate and normalize using email_validator
            valid_email = validate_email(email, check_deliverability=False)
            return valid_email.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {str(e)}")

    @staticmethod
    def validate_password(password: str) -> None:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )

        if len(password) > MAX_PASSWORD_LENGTH:
            raise ValidationError(
                f"Password must be no more than {MAX_PASSWORD_LENGTH} characters"
            )

        # Check for at least one number
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number")

        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")

        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")

    @staticmethod
    def validate_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
        """
        Validate and sanitize text message.

        Args:
            message: Message to validate
            max_length: Maximum allowed length

        Returns:
            Sanitized message

        Raises:
            ValidationError: If message is invalid
        """
        if not message:
            raise ValidationError("Message cannot be empty")

        if len(message) > max_length:
            raise ValidationError(
                f"Message cannot exceed {max_length} characters"
            )

        # Strip whitespace
        sanitized = message.strip()

        if not sanitized:
            raise ValidationError("Message cannot contain only whitespace")

        return sanitized

    @staticmethod
    def validate_description(description: str) -> str:
        """
        Validate and sanitize description text.

        Args:
            description: Description to validate

        Returns:
            Sanitized description

        Raises:
            ValidationError: If description is invalid
        """
        return ValidationService.validate_message(
            description,
            max_length=MAX_DESCRIPTION_LENGTH
        )

    @staticmethod
    def validate_name(name: str) -> str:
        """
        Validate name/title string.

        Args:
            name: Name to validate

        Returns:
            Sanitized name

        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Name must be a non-empty string")

        if len(name) > MAX_NAME_LENGTH:
            raise ValidationError(
                f"Name cannot exceed {MAX_NAME_LENGTH} characters"
            )

        sanitized = name.strip()

        if not sanitized:
            raise ValidationError("Name cannot contain only whitespace")

        # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s\-_.]+$", sanitized):
            raise ValidationError(
                "Name can only contain letters, numbers, spaces, hyphens, underscores, and periods"
            )

        return sanitized

    @staticmethod
    def validate_file_upload(
        filename: str,
        file_size: int,
        allowed_types: Optional[List[str]] = None
    ) -> tuple[str, str]:
        """
        Validate file upload.

        Args:
            filename: Name of the uploaded file
            file_size: Size of file in bytes
            allowed_types: List of allowed file extensions (default: ALLOWED_FILE_TYPES.keys())

        Returns:
            Tuple of (filename, file_type)

        Raises:
            ValidationError: If file is invalid
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")

        # Get file extension
        parts = filename.rsplit('.', 1)
        if len(parts) < 2:
            raise ValidationError("File must have an extension")

        file_ext = parts[1].lower()

        # Validate file type
        if allowed_types is None:
            allowed_types = list(ALLOWED_FILE_TYPES.keys())

        if file_ext not in allowed_types:
            raise ValidationError(
                f"File type '.{file_ext}' not allowed. Allowed types: {', '.join(allowed_types)}"
            )

        # Validate file size
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File size cannot exceed {MAX_FILE_SIZE_MB} MB"
            )

        if file_size == 0:
            raise ValidationError("File cannot be empty")

        # Sanitize filename
        safe_filename = re.sub(r'[^\w\-_.]+', '_', filename)

        file_type = ALLOWED_FILE_TYPES.get(file_ext, 'application/octet-stream')

        return safe_filename, file_type

    @staticmethod
    def validate_pagination(
        skip: int,
        limit: int,
        max_limit: int = 100
    ) -> tuple[int, int]:
        """
        Validate pagination parameters.

        Args:
            skip: Number of items to skip
            limit: Number of items to return
            max_limit: Maximum allowed limit

        Returns:
            Tuple of (skip, limit)

        Raises:
            ValidationError: If parameters are invalid
        """
        if skip < 0:
            raise ValidationError("skip must be >= 0")

        if limit < 1:
            raise ValidationError("limit must be >= 1")

        if limit > max_limit:
            raise ValidationError(
                f"limit cannot exceed {max_limit}"
            )

        return skip, limit

    @staticmethod
    def validate_enum_value(
        value: str,
        allowed_values: List[str],
        field_name: str = "value"
    ) -> str:
        """
        Validate that value is one of allowed values.

        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Field name for error message

        Returns:
            Validated value

        Raises:
            ValidationError: If value is not allowed
        """
        if value not in allowed_values:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(allowed_values)}"
            )

        return value

    @staticmethod
    def validate_uuid(uuid_str: str) -> str:
        """
        Validate UUID format.

        Args:
            uuid_str: UUID string to validate

        Returns:
            Validated UUID string

        Raises:
            ValidationError: If UUID is invalid
        """
        if not uuid_str:
            raise ValidationError("UUID cannot be empty")

        # UUID v4 regex pattern
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'

        if not re.match(uuid_pattern, str(uuid_str).lower()):
            raise ValidationError("Invalid UUID format")

        return str(uuid_str)

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Remove HTML tags from text.

        Args:
            text: Text potentially containing HTML

        Returns:
            HTML-safe text
        """
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Decode common HTML entities
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        return clean_text.strip()

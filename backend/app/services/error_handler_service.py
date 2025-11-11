"""
Standardized error handling service for consistent API error responses.

Provides:
- Error code constants
- Error response formatting
- Logging with proper context
- Error categorization
"""
import logging
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Authentication & Authorization (401, 403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"

    # Validation (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_UUID = "INVALID_UUID"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"

    # Not Found (404)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"

    # Conflict (409)
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"

    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"

    # Server Error (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Business Logic (422)
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    INVALID_STATE = "INVALID_STATE"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class APIError(HTTPException):
    """
    Custom API error with standard format.

    Inherits from HTTPException for FastAPI integration.
    """

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        detail: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API error.

        Args:
            status_code: HTTP status code
            error_code: Error code enum value
            message: Human-readable error message
            detail: Additional detail/description
            context: Additional context for logging
        """
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.context = context or {}

        # Format response body
        response_body = {
            "error": error_code.value,
            "message": message
        }

        if detail:
            response_body["detail"] = detail

        # Call parent with formatted detail
        super().__init__(
            status_code=status_code,
            detail=response_body
        )

    def __str__(self):
        return f"{self.error_code.value}: {self.message}"


class ErrorHandler:
    """Utility class for consistent error handling."""

    @staticmethod
    def unauthorized(message: str = "Not authenticated") -> APIError:
        """Return 401 Unauthorized error."""
        return APIError(
            status_code=401,
            error_code=ErrorCode.UNAUTHORIZED,
            message=message
        )

    @staticmethod
    def forbidden(message: str = "Access denied") -> APIError:
        """Return 403 Forbidden error."""
        return APIError(
            status_code=403,
            error_code=ErrorCode.FORBIDDEN,
            message=message
        )

    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        detail: Optional[str] = None
    ) -> APIError:
        """Return 400 Validation error."""
        return APIError(
            status_code=400,
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            detail=detail
        )

    @staticmethod
    def invalid_input(field: str, reason: str) -> APIError:
        """Return 400 Invalid input error."""
        return APIError(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            message=f"Invalid value for '{field}'",
            detail=reason
        )

    @staticmethod
    def not_found(resource_type: str, resource_id: Optional[str] = None) -> APIError:
        """Return 404 Not Found error."""
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"

        return APIError(
            status_code=404,
            error_code=ErrorCode.NOT_FOUND,
            message=message
        )

    @staticmethod
    def conflict(message: str, detail: Optional[str] = None) -> APIError:
        """Return 409 Conflict error."""
        return APIError(
            status_code=409,
            error_code=ErrorCode.CONFLICT,
            message=message,
            detail=detail
        )

    @staticmethod
    def duplicate_resource(resource_type: str, detail: Optional[str] = None) -> APIError:
        """Return 409 Duplicate resource error."""
        return APIError(
            status_code=409,
            error_code=ErrorCode.DUPLICATE_RESOURCE,
            message=f"{resource_type} already exists",
            detail=detail
        )

    @staticmethod
    def rate_limited(reset_after: Optional[int] = None) -> APIError:
        """Return 429 Rate limit exceeded error."""
        detail = None
        if reset_after:
            detail = f"Try again in {reset_after} seconds"

        return APIError(
            status_code=429,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Too many requests",
            detail=detail
        )

    @staticmethod
    def internal_error(message: str = "Internal server error") -> APIError:
        """Return 500 Internal Server Error."""
        return APIError(
            status_code=500,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=message
        )

    @staticmethod
    def database_error(operation: str, context: Optional[Dict] = None) -> APIError:
        """Return 500 Database error."""
        return APIError(
            status_code=500,
            error_code=ErrorCode.DATABASE_ERROR,
            message=f"Database {operation} failed",
            context=context
        )

    @staticmethod
    def log_error(
        error_code: ErrorCode,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error"
    ) -> None:
        """
        Log an error with context.

        Args:
            error_code: Error code enum
            message: Error message
            exception: Optional exception object
            context: Additional context dictionary
            level: Logging level (debug, info, warning, error, critical)
        """
        log_func = getattr(logger, level, logger.error)

        log_message = f"[{error_code.value}] {message}"

        if context:
            log_message += f" | Context: {context}"

        if exception:
            log_message += f" | Exception: {str(exception)}"
            log_func(log_message, exc_info=exception)
        else:
            log_func(log_message)

    @staticmethod
    def handle_database_error(
        exception: Exception,
        operation: str = "operation"
    ) -> APIError:
        """
        Handle database errors with appropriate responses.

        Args:
            exception: SQLAlchemy or database exception
            operation: Description of operation being performed

        Returns:
            APIError with appropriate status code and message
        """
        error_message = str(exception)

        if isinstance(exception, SQLAlchemyError):
            logger.error(
                f"Database error during {operation}: {error_message}",
                exc_info=exception
            )

            # Check for specific error types
            if "unique constraint" in error_message.lower():
                return ErrorHandler.duplicate_resource("Resource")
            elif "foreign key constraint" in error_message.lower():
                return ErrorHandler.conflict(
                    "Cannot perform operation due to related data",
                    detail="Please remove or update related items first"
                )

        return ErrorHandler.database_error(operation)

    @staticmethod
    def wrap_database_operation(
        operation_name: str,
        db_session: Any,
        safe_on_error: bool = True
    ):
        """
        Context manager for database operations with error handling.

        Args:
            operation_name: Name of operation for logging
            db_session: SQLAlchemy session
            safe_on_error: Whether to rollback on error

        Example:
            try:
                with ErrorHandler.wrap_database_operation("create_user", db):
                    new_user = User(email="test@example.com")
                    db.add(new_user)
                    db.commit()
            except APIError as e:
                return error_response
        """
        class DatabaseOperationContext:
            def __enter__(self):
                return db_session

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    if safe_on_error:
                        try:
                            db_session.rollback()
                        except Exception:
                            pass
                    logger.error(
                        f"Database operation '{operation_name}' failed: {exc_val}",
                        exc_info=exc_val
                    )
                    return False  # Re-raise the exception
                return True

        return DatabaseOperationContext()

"""
Unified API response wrapper service.

Provides:
- Standardized response format for all API endpoints
- Consistent error handling with logging
- Success/failure response wrapping
- Type-safe response models
"""
import logging
from typing import Any, Dict, Optional, TypeVar, Generic

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """Standardized success response wrapper."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response wrapper."""
    success: bool = False
    error: str
    message: str
    detail: Optional[str] = None
    status_code: int


class ResponseWrapper:
    """Utility class for wrapping API responses."""

    @staticmethod
    def success(
        data: Optional[Any] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Wrap a successful response.

        Args:
            data: Response data (can be dict, model, or any object)
            message: Optional success message
            **kwargs: Additional fields to include in response

        Returns:
            Dict with success=True and data
        """
        response = {
            "success": True,
            "message": message or "Operation successful"
        }

        # Handle different data types
        if data is not None:
            if isinstance(data, dict):
                response["data"] = data
            elif hasattr(data, "model_dump"):
                # Pydantic model
                response["data"] = data.model_dump()
            elif hasattr(data, "__dict__"):
                # SQLAlchemy model or dataclass
                response["data"] = data.__dict__
            else:
                response["data"] = data

        # Add any additional fields
        response.update(kwargs)

        return response

    @staticmethod
    def error(
        error_code: str,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Wrap an error response with logging.

        Args:
            error_code: Error code (e.g., "VALIDATION_ERROR")
            message: Human-readable error message
            status_code: HTTP status code
            detail: Additional detail/description
            **kwargs: Additional fields to include

        Returns:
            Dict with success=False and error details
        """
        response = {
            "success": False,
            "error": error_code,
            "message": message,
            "status_code": status_code
        }

        if detail:
            response["detail"] = detail

        response.update(kwargs)

        # Log the error
        log_msg = f"[{error_code}] {message}"
        if detail:
            log_msg += f" | {detail}"
        logger.error(log_msg)

        return response

    @staticmethod
    def success_or_error(
        success: bool,
        data: Optional[Any] = None,
        error_code: Optional[str] = None,
        message: Optional[str] = None,
        status_code: int = 500,
        detail: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Wrap response based on success flag.

        Args:
            success: Whether operation was successful
            data: Response data if successful
            error_code: Error code if failed
            message: Message (success or error)
            status_code: HTTP status code if error
            detail: Additional detail if error
            **kwargs: Additional fields

        Returns:
            Wrapped success or error response
        """
        if success:
            return ResponseWrapper.success(data=data, message=message, **kwargs)
        else:
            return ResponseWrapper.error(
                error_code=error_code or "UNKNOWN_ERROR",
                message=message or "Operation failed",
                status_code=status_code,
                detail=detail,
                **kwargs
            )

    @staticmethod
    def validation_error(
        field: str,
        reason: str,
        value: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Wrap a validation error response.

        Args:
            field: Field name that failed validation
            reason: Reason for validation failure
            value: The invalid value (optional, for debugging)

        Returns:
            Error response dict
        """
        detail = f"Invalid value for '{field}': {reason}"
        if value is not None:
            detail += f" (received: {value})"

        return ResponseWrapper.error(
            error_code="VALIDATION_ERROR",
            message=f"Validation failed for field '{field}'",
            status_code=400,
            detail=detail,
            field=field
        )

    @staticmethod
    def not_found(resource_type: str, resource_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Wrap a not found error response.

        Args:
            resource_type: Type of resource (e.g., "Project")
            resource_id: ID of resource that wasn't found

        Returns:
            Error response dict
        """
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"

        return ResponseWrapper.error(
            error_code="NOT_FOUND",
            message=message,
            status_code=404,
            resource_type=resource_type,
            resource_id=resource_id
        )

    @staticmethod
    def unauthorized(message: str = "Not authenticated") -> Dict[str, Any]:
        """Wrap an unauthorized error response."""
        return ResponseWrapper.error(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=401
        )

    @staticmethod
    def forbidden(message: str = "Access denied") -> Dict[str, Any]:
        """Wrap a forbidden error response."""
        return ResponseWrapper.error(
            error_code="FORBIDDEN",
            message=message,
            status_code=403
        )

    @staticmethod
    def conflict(message: str, detail: Optional[str] = None) -> Dict[str, Any]:
        """Wrap a conflict error response."""
        return ResponseWrapper.error(
            error_code="CONFLICT",
            message=message,
            status_code=409,
            detail=detail
        )

    @staticmethod
    def internal_error(message: str = "Internal server error", exception: Optional[Exception] = None) -> Dict[str, Any]:
        """
        Wrap an internal server error response.

        Args:
            message: Error message
            exception: Optional exception for logging

        Returns:
            Error response dict
        """
        detail = None
        if exception:
            detail = str(exception)
            logger.error(f"Internal server error: {detail}", exc_info=exception)

        return ResponseWrapper.error(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=500,
            detail=detail
        )

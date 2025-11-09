# ERROR HANDLING STRATEGY

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🟡 MEDIUM - Implement during Phase 0-1

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Error Categories](#error-categories)
3. [Error Response Format](#error-response-format)
4. [HTTP Status Codes](#http-status-codes)
5. [Error Codes](#error-codes)
6. [Logging Strategy](#logging-strategy)
7. [User-Friendly Messages](#user-friendly-messages)
8. [Retry Logic](#retry-logic)
9. [Error Recovery](#error-recovery)

---

## OVERVIEW

**Goal:** Consistent, user-friendly, debuggable error handling.

### Principles

1. **Fail Gracefully**: Never expose stack traces to users
2. **Log Everything**: Errors logged with full context
3. **User-Friendly**: Clear, actionable error messages
4. **Debuggable**: Enough information for developers
5. **Retry Transient Errors**: Auto-retry for network/LLM errors

---

## ERROR CATEGORIES

### 1. Client Errors (400s)

User-caused errors: validation failures, authentication issues

```python
class ValidationError(Exception):
    """Invalid input from user."""
    http_status = 400

class AuthenticationError(Exception):
    """Authentication failed."""
    http_status = 401

class PermissionError(Exception):
    """Insufficient permissions."""
    http_status = 403

class NotFoundError(Exception):
    """Resource not found."""
    http_status = 404
```

### 2. Server Errors (500s)

System-caused errors: database failures, LLM errors

```python
class DatabaseError(Exception):
    """Database operation failed."""
    http_status = 500

class LLMError(Exception):
    """LLM API call failed."""
    http_status = 500

class ConfigurationError(Exception):
    """System misconfiguration."""
    http_status = 500
```

### 3. Transient Errors

Temporary failures that should be retried

```python
class TransientError(Exception):
    """Temporary failure, retry recommended."""
    http_status = 503
    retry_after = 5  # seconds

class RateLimitError(TransientError):
    """Rate limit exceeded."""
    retry_after = 60
```

---

## ERROR RESPONSE FORMAT

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email format is invalid",
    "details": {
      "field": "email",
      "value": "not-an-email"
    },
    "request_id": "req_abc123",
    "timestamp": "2025-11-05T10:30:00Z"
  }
}
```

### Implementation

```python
# middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorResponse:
    """Standard error response."""

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = 500,
        details: dict = None,
        request_id: str = None
    ):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
                "timestamp": self.timestamp
            }
        }

    def to_response(self):
        return JSONResponse(
            status_code=self.http_status,
            content=self.to_dict()
        )
```

---

## HTTP STATUS CODES

```python
# Standard status codes
STATUS_CODES = {
    # Success
    200: "OK",
    201: "Created",
    204: "No Content",

    # Client Errors
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",

    # Server Errors
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}
```

---

## ERROR CODES

```python
# Error codes (application-specific)
ERROR_CODES = {
    # Authentication
    "AUTH_001": "Invalid credentials",
    "AUTH_002": "Token expired",
    "AUTH_003": "Token invalid",
    "AUTH_004": "Insufficient permissions",

    # Validation
    "VAL_001": "Email format invalid",
    "VAL_002": "Password too weak",
    "VAL_003": "Required field missing",
    "VAL_004": "Invalid enum value",

    # Business Logic
    "BIZ_001": "Project not found",
    "BIZ_002": "Session already ended",
    "BIZ_003": "Cannot advance phase (maturity < 100%)",
    "BIZ_004": "Conflict must be resolved first",

    # LLM Errors
    "LLM_001": "LLM API call failed",
    "LLM_002": "LLM rate limit exceeded",
    "LLM_003": "LLM timeout",
    "LLM_004": "Invalid LLM response",

    # Database
    "DB_001": "Database connection failed",
    "DB_002": "Database query failed",
    "DB_003": "Constraint violation",

    # System
    "SYS_001": "Configuration error",
    "SYS_002": "Service unavailable",
}
```

---

## LOGGING STRATEGY

```python
# config/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure logging for production."""

    # JSON formatter for structured logs
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s'
    )
    log_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(log_handler)

# Usage
logger.error(
    "Database query failed",
    extra={
        "error_code": "DB_002",
        "request_id": request.state.request_id,
        "user_id": request.state.user_id,
        "query": "SELECT * FROM projects WHERE id = :id",
        "exception": str(e)
    }
)
```

---

## USER-FRIENDLY MESSAGES

```python
# utils/error_messages.py

def get_user_friendly_message(error_code: str) -> str:
    """Convert error code to user-friendly message."""

    messages = {
        "AUTH_001": "The email or password you entered is incorrect. Please try again.",
        "AUTH_002": "Your session has expired. Please log in again.",
        "VAL_001": "Please enter a valid email address.",
        "VAL_002": "Password must be at least 12 characters with uppercase, lowercase, digit, and special character.",
        "BIZ_003": "Cannot advance to next phase yet. Please complete all required sections (currently at {maturity}% maturity).",
        "LLM_002": "AI service is experiencing high demand. Please try again in a moment.",
        "DB_001": "We're experiencing technical difficulties. Please try again shortly.",
    }

    return messages.get(error_code, "An unexpected error occurred. Please try again.")
```

---

## RETRY LOGIC

```python
# utils/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

# Retry decorator for transient errors
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TransientError, RateLimitError)),
    reraise=True
)
def call_llm_with_retry(llm_service, prompt):
    """Call LLM with automatic retry on transient errors."""
    try:
        return llm_service.generate(prompt)
    except RateLimitError as e:
        logger.warning(f"LLM rate limit exceeded, retrying...", extra={"error": str(e)})
        raise
    except LLMError as e:
        logger.error(f"LLM call failed: {str(e)}")
        raise TransientError("LLM service temporarily unavailable")
```

---

## ERROR RECOVERY

```python
# middleware/error_middleware.py

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""

    # Generate request ID
    request_id = str(uuid.uuid4())

    # Log error with full context
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, "user_id", None),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "stack_trace": traceback.format_exc()
        },
        exc_info=True
    )

    # Return user-friendly error
    return ErrorResponse(
        code="SYS_001",
        message="An unexpected error occurred. We've been notified and are working on it.",
        http_status=500,
        details={"request_id": request_id}
    ).to_response()
```

---

**Document Status:** ✅ Complete
**Date:** November 5, 2025

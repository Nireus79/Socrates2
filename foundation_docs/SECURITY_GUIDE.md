# SECURITY GUIDE

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🔴 CRITICAL - Must complete before Phase 0

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Security Principles](#security-principles)
3. [Authentication System](#authentication-system)
4. [Password Security](#password-security)
5. [JWT Token Management](#jwt-token-management)
6. [API Key Management](#api-key-management)
7. [Input Validation](#input-validation)
8. [SQL Injection Prevention](#sql-injection-prevention)
9. [XSS Prevention](#xss-prevention)
10. [CORS Configuration](#cors-configuration)
11. [Rate Limiting](#rate-limiting)
12. [Secrets Management](#secrets-management)
13. [Audit Logging](#audit-logging)
14. [Security Testing](#security-testing)
15. [Incident Response](#incident-response)

---

## OVERVIEW

**Security is non-negotiable.** Socrates2 handles sensitive data:
- User credentials and authentication tokens
- Project specifications and proprietary business logic
- LLM API keys (expensive if compromised)
- Conversation history (potentially confidential)

### Security Goals

1. **Protect User Data**: Passwords hashed, tokens encrypted, data isolated
2. **Prevent Unauthorized Access**: Strong authentication, authorization checks
3. **Prevent Common Attacks**: SQL injection, XSS, CSRF, brute force
4. **Detect & Respond**: Audit logging, anomaly detection, incident response
5. **Secure by Default**: Safe defaults, explicit opt-in for risky operations

---

## SECURITY PRINCIPLES

### Principle 1: Defense in Depth

**Multiple layers of security**

- Authentication (who are you?)
- Authorization (what can you do?)
- Input validation (is this safe?)
- Output encoding (prevent XSS)
- Rate limiting (prevent abuse)
- Audit logging (detect attacks)

### Principle 2: Least Privilege

**Users get minimum permissions needed**

- Default: Read-only access
- Explicit grants for write operations
- Database users have limited permissions
- API keys have scoped access

### Principle 3: Fail Securely

**Errors don't leak information**

```python
# ❌ BAD: Leaks information
except Exception as e:
    return {"error": f"Database error: {str(e)}"}
    # Attacker learns: "Table 'users' does not exist"

# ✅ GOOD: Generic error message
except Exception as e:
    logger.error(f"Database error: {str(e)}")
    return {"error": "An error occurred. Please try again."}
```

### Principle 4: Secure by Default

**Safe defaults, explicit opt-in for risky operations**

```python
# ✅ GOOD: Defaults are secure
class Settings:
    DEBUG = False  # Production default
    HTTPS_ONLY = True
    SECURE_COOKIES = True
    RATE_LIMIT_ENABLED = True
```

### Principle 5: Keep It Simple

**Complexity is the enemy of security**

- Use proven libraries (bcrypt, python-jose)
- Don't implement custom crypto
- Clear code is auditable code

---

## AUTHENTICATION SYSTEM

### Architecture

**Two-database pattern for security isolation:**

```
┌─────────────────────────────────────────┐
│ socrates_auth Database                  │
│ - users (id, email, password_hash)      │
│ - sessions (token, user_id, expires)    │
│ - user_rules (user settings)            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ socrates_specs Database                 │
│ - projects (id, user_id, name)          │
│ - specifications (id, project_id)       │
│ - conversation_history (id, session_id) │
└─────────────────────────────────────────┘
```

**Why separate?**
- Auth breach ≠ specs breach
- Different backup/encryption policies
- Compliance separation (GDPR, SOC2)

### User Model

```python
# models/user.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"
```

### Registration Flow

```python
# services/auth_service.py
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models.user import User
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, email: str, password: str) -> User:
        """
        Register a new user.

        Security checks:
        1. Email format validation
        2. Email uniqueness
        3. Password strength validation
        4. Password hashing (bcrypt)

        Args:
            email: User email
            password: Plain-text password

        Returns:
            User object

        Raises:
            ValueError: If validation fails
        """
        # Validate email format
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")

        # Check email uniqueness
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        # Validate password strength
        if not self._is_strong_password(password):
            raise ValueError(
                "Password must be at least 12 characters, "
                "with uppercase, lowercase, digit, and special character"
            )

        # Hash password
        password_hash = pwd_context.hash(password)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,  # Require email verification
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_strong_password(self, password: str) -> bool:
        """
        Validate password strength.

        Requirements:
        - Minimum 12 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        if len(password) < 12:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special
```

### Login Flow

```python
# services/auth_service.py (continued)

def login(self, email: str, password: str) -> dict:
    """
    Authenticate user and return tokens.

    Security checks:
    1. User exists and is active
    2. Password verification (bcrypt)
    3. Rate limiting (prevent brute force)
    4. Audit logging

    Args:
        email: User email
        password: Plain-text password

    Returns:
        dict with access_token and refresh_token

    Raises:
        ValueError: If authentication fails
    """
    # Find user
    user = self.db.query(User).filter(User.email == email).first()

    if not user:
        # ⚠️ Don't leak "user not found" vs "wrong password"
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Account is deactivated")

    # Verify password
    if not pwd_context.verify(password, user.password_hash):
        # Log failed attempt for rate limiting
        self._log_failed_login(email)
        raise ValueError("Invalid email or password")

    # Update last login
    user.last_login_at = datetime.utcnow()
    self.db.commit()

    # Generate tokens
    access_token = self._create_access_token(user)
    refresh_token = self._create_refresh_token(user)

    # Log successful login
    self._log_successful_login(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
```

---

## PASSWORD SECURITY

### Why bcrypt?

- ✅ **Slow by design**: Prevents brute-force attacks
- ✅ **Salt built-in**: Each password gets unique salt
- ✅ **Adaptive cost**: Can increase rounds as hardware improves
- ✅ **Battle-tested**: Industry standard for 20+ years

### Password Hashing

```python
from passlib.context import CryptContext

# Configure bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor (2^12 iterations)
)

# Hash password
password_hash = pwd_context.hash("MySecurePassword123!")
# Output: $2b$12$KIXl5W8Z... (60 characters)

# Verify password
is_valid = pwd_context.verify("MySecurePassword123!", password_hash)
# True

is_valid = pwd_context.verify("WrongPassword", password_hash)
# False
```

### Password Strength Requirements

**Minimum Requirements:**

| Requirement | Value | Why |
|-------------|-------|-----|
| **Length** | 12 characters | Brute-force resistance |
| **Uppercase** | At least 1 | Character diversity |
| **Lowercase** | At least 1 | Character diversity |
| **Digit** | At least 1 | Character diversity |
| **Special** | At least 1 | Character diversity |

**Recommended:**

- 16+ characters
- No common passwords (use dictionary check)
- No personal information (name, birthday, etc.)
- No keyboard patterns (qwerty, 123456, etc.)

### Password Reset Flow

```python
def request_password_reset(self, email: str):
    """
    Send password reset email.

    Security:
    1. Don't leak if email exists
    2. Token expires in 1 hour
    3. Token is single-use
    4. Rate limit requests
    """
    user = self.db.query(User).filter(User.email == email).first()

    # ⚠️ Always return success (don't leak user existence)
    if not user:
        return {"message": "If email exists, reset link was sent"}

    # Generate secure token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Store token
    reset_request = PasswordResetRequest(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
        used=False,
    )
    self.db.add(reset_request)
    self.db.commit()

    # Send email (not implemented here)
    # send_email(user.email, reset_token)

    return {"message": "If email exists, reset link was sent"}

def reset_password(self, token: str, new_password: str):
    """
    Reset password using token.

    Security:
    1. Token must exist and not be expired
    2. Token is single-use
    3. New password must meet strength requirements
    """
    # Find token
    reset_request = (
        self.db.query(PasswordResetRequest)
        .filter(
            PasswordResetRequest.token == token,
            PasswordResetRequest.used == False,
            PasswordResetRequest.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not reset_request:
        raise ValueError("Invalid or expired reset token")

    # Validate new password
    if not self._is_strong_password(new_password):
        raise ValueError("Password does not meet strength requirements")

    # Update password
    user = self.db.query(User).filter(User.id == reset_request.user_id).first()
    user.password_hash = pwd_context.hash(new_password)

    # Mark token as used
    reset_request.used = True
    reset_request.used_at = datetime.utcnow()

    self.db.commit()

    return {"message": "Password reset successful"}
```

---

## JWT TOKEN MANAGEMENT

### Token Architecture

**Two token types:**

1. **Access Token** (short-lived, 30 minutes)
   - Used for API requests
   - Contains user_id, email, permissions
   - Cannot be revoked (expires quickly)

2. **Refresh Token** (long-lived, 7 days)
   - Used to get new access tokens
   - Stored in database (can be revoked)
   - HttpOnly cookie (XSS protection)

### JWT Configuration

```python
# config/settings.py
import os

class Settings:
    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Min 32 characters
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # Security
    BCRYPT_ROUNDS = 12

    def validate(self):
        """Validate JWT secret key strength."""
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY is required")

        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
```

### Access Token Creation

```python
# services/auth_service.py
from jose import jwt
from datetime import datetime, timedelta
from config.settings import settings

def _create_access_token(self, user: User) -> str:
    """
    Create JWT access token.

    Token payload:
    - sub: user_id
    - email: user email
    - type: "access"
    - exp: expiration timestamp
    - iat: issued at timestamp
    """
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.utcnow() + expires_delta

    payload = {
        "sub": str(user.id),  # Subject (user ID)
        "email": user.email,
        "type": "access",
        "exp": expires_at,  # Expiration
        "iat": datetime.utcnow(),  # Issued at
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token

def _create_refresh_token(self, user: User) -> str:
    """
    Create JWT refresh token and store in database.

    Refresh tokens are:
    1. Stored in database (can be revoked)
    2. Longer-lived (7 days)
    3. Single-purpose (can only refresh access tokens)
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expires_at = datetime.utcnow() + expires_delta

    # Generate unique token ID
    token_id = str(uuid.uuid4())

    payload = {
        "sub": str(user.id),
        "jti": token_id,  # JWT ID (unique identifier)
        "type": "refresh",
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    # Store in database (for revocation)
    refresh_token_record = RefreshToken(
        id=token_id,
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        revoked=False,
    )
    self.db.add(refresh_token_record)
    self.db.commit()

    return token
```

### Token Verification

```python
# middleware/auth_middleware.py
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from config.settings import settings

async def verify_access_token(request: Request):
    """
    Verify JWT access token from Authorization header.

    Security checks:
    1. Token exists
    2. Token format is valid
    3. Token signature is valid
    4. Token is not expired
    5. Token type is "access"
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = auth_header.replace("Bearer ", "")

    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # Extract user info
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Attach to request
        request.state.user_id = user_id
        request.state.email = email

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Usage in FastAPI
from fastapi import Depends

@app.get("/api/projects")
async def get_projects(request: Request = Depends(verify_access_token)):
    user_id = request.state.user_id
    # ... fetch projects for user
```

### Token Refresh Flow

```python
# api/routes/auth.py
from fastapi import APIRouter, HTTPException, Response

router = APIRouter()

@router.post("/refresh")
async def refresh_access_token(refresh_token: str, response: Response):
    """
    Exchange refresh token for new access token.

    Security:
    1. Verify refresh token signature
    2. Check token exists in database (not revoked)
    3. Check token not expired
    4. Generate new access token
    5. Optionally rotate refresh token
    """
    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        token_id = payload.get("jti")
        user_id = payload.get("sub")

        # Check token in database
        db_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.id == token_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not db_token:
            raise HTTPException(status_code=401, detail="Invalid or revoked token")

        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # Generate new access token
        new_access_token = auth_service._create_access_token(user)

        # Optional: Rotate refresh token (more secure)
        # db_token.revoked = True
        # new_refresh_token = auth_service._create_refresh_token(user)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Token Revocation

```python
def revoke_refresh_token(self, token_id: str):
    """
    Revoke a refresh token (logout).

    Security:
    - Access tokens cannot be revoked (expire quickly)
    - Refresh tokens can be revoked (stored in database)
    """
    token = self.db.query(RefreshToken).filter(RefreshToken.id == token_id).first()

    if token:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
        self.db.commit()

def revoke_all_user_tokens(self, user_id: str):
    """
    Revoke all refresh tokens for a user (logout all devices).

    Use cases:
    - Password reset
    - Account security breach
    - User requests logout from all devices
    """
    tokens = (
        self.db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
        .all()
    )

    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.utcnow()

    self.db.commit()
```

---

## API KEY MANAGEMENT

### Storing API Keys

**✅ CORRECT: Environment Variables**

```bash
# .env file (NEVER commit to git)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    def validate(self):
        """Ensure API keys are present."""
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")
```

**❌ WRONG: Hardcoded in Code**

```python
# ❌ NEVER DO THIS
ANTHROPIC_API_KEY = "sk-ant-api03-abc123..."  # BAD!
```

### API Key Rotation

```python
def rotate_llm_api_key(self, provider: str, new_key: str):
    """
    Rotate LLM API key.

    Steps:
    1. Validate new key (test API call)
    2. Update .env file
    3. Reload settings
    4. Log rotation event
    5. Invalidate old key with provider
    """
    # Test new key
    if not self._test_api_key(provider, new_key):
        raise ValueError("New API key is invalid")

    # Update .env file
    self._update_env_file(f"{provider.upper()}_API_KEY", new_key)

    # Log rotation
    logger.info(f"API key rotated for provider: {provider}")

    # Reload settings
    load_dotenv(override=True)
```

---

## INPUT VALIDATION

### Pydantic Models for Validation

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class UserRegistrationRequest(BaseModel):
    """User registration request validation."""

    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=12, max_length=128)

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain special character")
        return v

class ProjectCreateRequest(BaseModel):
    """Project creation request validation."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

    @validator("name")
    def validate_name(cls, v):
        """Validate project name doesn't contain dangerous characters."""
        dangerous = ["<", ">", "\"", "'", "&", ";", "|"]
        if any(char in v for char in dangerous):
            raise ValueError("Project name contains invalid characters")
        return v.strip()
```

---

## SQL INJECTION PREVENTION

### ✅ CORRECT: SQLAlchemy ORM

```python
# ✅ SAFE: SQLAlchemy parameterizes queries automatically
def get_user_by_email(email: str):
    user = db.query(User).filter(User.email == email).first()
    return user

# ✅ SAFE: Even with user input
email_input = request.json.get("email")
user = db.query(User).filter(User.email == email_input).first()
```

### ❌ WRONG: Raw SQL with String Formatting

```python
# ❌ DANGEROUS: SQL injection vulnerability
def get_user_by_email_unsafe(email: str):
    query = f"SELECT * FROM users WHERE email = '{email}'"
    result = db.execute(query)
    # Attacker input: "admin@example.com' OR '1'='1"
    # SQL: SELECT * FROM users WHERE email = 'admin@example.com' OR '1'='1'
    # Result: Returns all users!
```

### ✅ CORRECT: Raw SQL with Parameters

```python
# ✅ SAFE: Use parameterized queries if you must use raw SQL
def get_user_by_email_safe(email: str):
    query = "SELECT * FROM users WHERE email = :email"
    result = db.execute(text(query), {"email": email})
    return result.fetchone()
```

---

## XSS PREVENTION

### Output Encoding

```python
from fastapi import Response
from fastapi.responses import JSONResponse
import html

def get_project(project_id: str):
    """Return project data (XSS-safe)."""
    project = db.query(Project).filter(Project.id == project_id).first()

    # FastAPI automatically escapes JSON
    return {
        "id": project.id,
        "name": project.name,  # Automatically escaped in JSON
        "description": project.description,
    }

# If returning HTML (rare in API):
def render_html_safe(content: str):
    """Escape HTML to prevent XSS."""
    safe_content = html.escape(content)
    return Response(content=safe_content, media_type="text/html")
```

---

## CORS CONFIGURATION

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),  # ["http://localhost:3000"]
    allow_credentials=True,  # Allow cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,  # Cache preflight requests for 10 minutes
)
```

---

## RATE LIMITING

```python
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict

# Simple in-memory rate limiter (use Redis for production)
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is allowed.

        Args:
            identifier: User ID or IP address
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)

        # Remove old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True

rate_limiter = RateLimiter()

# Middleware
async def rate_limit_middleware(request: Request, call_next):
    """Rate limit API requests."""
    identifier = request.state.user_id if hasattr(request.state, "user_id") else request.client.host

    # 100 requests per minute per user/IP
    if not rate_limiter.is_allowed(identifier, max_requests=100, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    response = await call_next(request)
    return response
```

---

## SECRETS MANAGEMENT

### Generate Strong Secrets

```bash
# Generate SECRET_KEY (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: xK8pL2mN4qR6sT8vW0yA2bC4dE6fG8hJ0kL2mN4pQ6r

# Generate SECRET_KEY (OpenSSL)
openssl rand -base64 32
```

### .gitignore (Critical)

```bash
# .gitignore
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
credentials.json
```

---

## AUDIT LOGGING

```python
# services/audit_service.py
from models.audit_log import AuditLog
from sqlalchemy.orm import Session
from datetime import datetime
import json

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
        ip_address: str,
    ):
        """
        Log security-relevant event.

        Events to log:
        - User login/logout
        - Password changes
        - Project creation/deletion
        - Failed authentication attempts
        - Rate limit violations
        - API errors
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details),
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
        )

        self.db.add(log)
        self.db.commit()

# Usage
audit_service.log_event(
    user_id=user.id,
    action="user.login",
    resource_type="user",
    resource_id=str(user.id),
    details={"email": user.email},
    ip_address=request.client.host,
)
```

---

## SECURITY TESTING

### Security Test Checklist

- [ ] **Authentication bypass**: Try accessing protected endpoints without token
- [ ] **SQL injection**: Try injecting SQL in all input fields
- [ ] **XSS**: Try injecting `<script>alert('XSS')</script>`
- [ ] **CSRF**: Try making requests without proper tokens
- [ ] **Rate limiting**: Try exceeding rate limits
- [ ] **Password strength**: Try weak passwords
- [ ] **Token expiration**: Verify tokens expire correctly
- [ ] **Token revocation**: Verify revoked tokens don't work

---

## INCIDENT RESPONSE

### If Security Breach Detected:

1. **Contain**: Revoke all tokens, disable affected accounts
2. **Investigate**: Review audit logs, identify scope
3. **Notify**: Inform affected users (legal requirement)
4. **Remediate**: Fix vulnerability, deploy patch
5. **Monitor**: Watch for repeat attacks

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This document ensures Socrates2 follows security best practices from day 1.*

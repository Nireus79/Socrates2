"""
Authentication API endpoints.

Provides:
- User registration
- User login (JWT token generation)
- Logout
- Token refresh
- Current user info
"""
from datetime import timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ..core.action_logger import log_auth
from ..core.config import settings
from ..core.database import get_db_auth, get_db_specs
from ..core.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_current_user,
    validate_refresh_token,
)
from ..models.user import User
from ..repositories import RepositoryService

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Dependency for repository service
def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    """Get repository service with both database sessions."""
    return RepositoryService(auth_session, specs_session)


# Pydantic schemas for request/response
class RegisterRequest(BaseModel):
    """User registration request"""
    name: str = Field(..., min_length=2, max_length=100)
    surname: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=100)
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John",
                "surname": "Doe",
                "username": "johndoe",
                "password": "SecurePassword123!",
                "email": "john@example.com"
            }
        }


class RegisterResponse(BaseModel):
    """User registration response"""
    message: str
    user_id: str
    username: str
    name: str
    surname: str
    email: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "User registered successfully",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe",
                "name": "John",
                "surname": "Doe",
                "email": "john@example.com"
            }
        }


class LoginResponse(BaseModel):
    """Login response with JWT token and refresh token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    name: str
    surname: str

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "8Xk5...random...token...string",
                "token_type": "bearer",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe",
                "name": "John",
                "surname": "Doe"
            }
        }


class UserResponse(BaseModel):
    """User information response"""
    id: str
    username: str
    name: str
    surname: str
    email: Optional[str] = None
    is_active: bool
    is_verified: bool
    status: str
    role: str
    created_at: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    service: RepositoryService = Depends(get_repository_service)
) -> RegisterResponse:
    """
    Register a new user.

    Creates a new user account with:
    - Unique username (for login)
    - First and last name
    - Bcrypt-hashed password
    - Optional email address
    - Default role: 'user'
    - Default status: 'active'
    - is_verified: False (requires email verification)

    Args:
        request: Registration data (name, surname, username, password, optional email)
        service: Repository service with database access

    Returns:
        RegisterResponse with user_id, username, and user details

    Raises:
        HTTPException 400: If username or email already exists

    Example:
        POST /api/v1/auth/register
        {
            "name": "John",
            "surname": "Doe",
            "username": "johndoe",
            "password": "SecurePass123!",
            "email": "john@example.com"
        }

        Response 201:
        {
            "message": "User registered successfully",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "johndoe",
            "name": "John",
            "surname": "Doe",
            "email": "john@example.com"
        }
    """
    try:
        # Check if username already exists using repository
        if service.users.user_exists_by_username(request.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Check if email already exists (if provided)
        if request.email and service.users.user_exists_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user using repository
        user = service.users.create_user(
            name=request.name,
            surname=request.surname,
            username=request.username,
            email=request.email,
            hashed_password=User.hash_password(request.password)
        )

        # Commit changes
        service.commit_all()

        # Log the successful registration
        log_auth("User registered", user_id=str(user.id), username=user.username, success=True)

        return RegisterResponse(
            message="User registered successfully",
            user_id=str(user.id),
            username=user.username,
            name=user.name,
            surname=user.surname,
            email=user.email
        )

    except HTTPException:
        service.rollback_all()
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        ) from e


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: RepositoryService = Depends(get_repository_service)
) -> LoginResponse:
    """
    Login and receive JWT access token.

    Validates credentials and returns JWT token for authentication.

    Args:
        form_data: OAuth2 password form (username, password)
        service: Repository service with database access

    Returns:
        LoginResponse with access_token and user info

    Raises:
        HTTPException 401: If credentials are invalid

    Example:
        POST /api/v1/auth/login
        Content-Type: application/x-www-form-urlencoded

        username=johndoe&password=SecurePass123!

        Response 200:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "johndoe",
            "name": "John",
            "surname": "Doe"
        }
    """
    # Find user by username using repository
    user = service.users.get_by_username(form_data.username)

    # Validate user exists and password is correct
    if not user or not user.verify_password(form_data.password):  # type: ignore[arg-type]  # form_data.password exists, type checker limitation
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    # Create refresh token using repository
    refresh_token_obj = service.refresh_tokens.create(
        user_id=user.id,
        token=create_refresh_token(str(user.id), service.auth_session),
        expires_at=None  # Will be set by the model defaults if needed
    )
    service.commit_all()
    refresh_token = refresh_token_obj.token

    # Log successful login
    log_auth("User logged in", user_id=str(user.id), username=user.username, success=True)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        name=user.name,
        surname=user.surname
    )


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Logout current user.

    Note: With JWT, actual logout is handled client-side by discarding the token.
    This endpoint is provided for consistency and future token revocation.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message

    Example:
        POST /api/v1/auth/logout
        Authorization: Bearer <token>

        Response 200:
        {
            "message": "Logged out successfully"
        }
    """
    # Log logout
    log_auth("User logged out", user_id=str(current_user.id), username=current_user.username, success=True)

    # With JWT, client should delete the token
    # Future: Implement token revocation/blacklist
    return {
        "message": "Logged out successfully"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information (excluding hashed_password)

    Example:
        GET /api/v1/auth/me
        Authorization: Bearer <token>

        Response 200:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "johndoe",
            "name": "John",
            "surname": "Doe",
            "email": "john@example.com",
            "is_active": true,
            "is_verified": false,
            "status": "active",
            "role": "user",
            "created_at": "2025-11-06T10:30:00"
        }
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        name=current_user.name,
        surname=current_user.surname,
        email=current_user.email,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        status=current_user.status,
        role=current_user.role,
        created_at=current_user.created_at.isoformat()
    )


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str = Field(..., description="Refresh token from login")


@router.post("/refresh", response_model=LoginResponse)
def refresh_access_token(
    request: RefreshTokenRequest,
    service: RepositoryService = Depends(get_repository_service)
) -> LoginResponse:
    """
    Refresh an access token using a valid refresh token.

    Args:
        request: RefreshTokenRequest with refresh_token
        service: Repository service with database access

    Returns:
        LoginResponse with new access_token and refresh_token

    Raises:
        HTTPException 401: If refresh token is invalid or expired

    Example:
        POST /api/v1/auth/refresh
        {
            "refresh_token": "8Xk5...random...token...string"
        }

        Response 200:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "new...refresh...token...",
            "token_type": "bearer",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "johndoe",
            "name": "John",
            "surname": "Doe"
        }
    """
    try:
        # Validate the refresh token using repository
        user = validate_refresh_token(request.refresh_token, service.auth_session)

        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        # Create new refresh token
        new_refresh_token_obj = service.refresh_tokens.create(
            user_id=user.id,
            token=create_refresh_token(str(user.id), service.auth_session),
            expires_at=None
        )
        service.commit_all()
        new_refresh_token = new_refresh_token_obj.token

        # Log token refresh
        log_auth("Token refreshed", user_id=str(user.id), username=user.username, success=True)

        return LoginResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username,
            name=user.name,
            surname=user.surname
        )

    except HTTPException:
        service.rollback_all()
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

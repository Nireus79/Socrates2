"""
Authentication API endpoints.

Provides:
- User registration
- User login (JWT token generation)
- Logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any
from datetime import timedelta

from app.core.database import get_db_auth
from app.core.security import (
    create_access_token,
    get_current_user,
    get_current_active_user
)
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# Pydantic schemas for request/response
class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class RegisterResponse(BaseModel):
    """User registration response"""
    message: str
    user_id: str
    email: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "User registered successfully",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com"
            }
        }


class LoginResponse(BaseModel):
    """Login response with JWT token"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com"
            }
        }


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: str
    is_active: bool
    is_verified: bool
    status: str
    role: str
    created_at: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db_auth)
) -> RegisterResponse:
    """
    Register a new user.

    Creates a new user account with:
    - Unique email address
    - Bcrypt-hashed password
    - Default role: 'user'
    - Default status: 'active'
    - is_verified: False (requires email verification)

    Args:
        request: Registration data (email, password)
        db: Database session

    Returns:
        RegisterResponse with user_id and email

    Raises:
        HTTPException 400: If email already exists

    Example:
        POST /api/v1/auth/register
        {
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        }

        Response 201:
        {
            "message": "User registered successfully",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "newuser@example.com"
        }
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        email=request.email,
        hashed_password=User.hash_password(request.password),
        is_active=True,
        is_verified=False,
        status='active',
        role='user'
    )

    db.add(user)
    # Commit happens in get_db_auth() dependency

    return RegisterResponse(
        message="User registered successfully",
        user_id=str(user.id),
        email=user.email
    )


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_auth)
) -> LoginResponse:
    """
    Login and receive JWT access token.

    Validates credentials and returns JWT token for authentication.

    Args:
        form_data: OAuth2 password form (username=email, password)
        db: Database session

    Returns:
        LoginResponse with access_token and user info

    Raises:
        HTTPException 401: If credentials are invalid

    Example:
        POST /api/v1/auth/login
        Content-Type: application/x-www-form-urlencoded

        username=user@example.com&password=SecurePass123!

        Response 200:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com"
        }
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()

    # Validate user exists and password is correct
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
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

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        email=user.email
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
            "email": "user@example.com",
            "is_active": true,
            "is_verified": false,
            "status": "active",
            "role": "user",
            "created_at": "2025-11-06T10:30:00"
        }
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        status=current_user.status,
        role=current_user.role,
        created_at=current_user.created_at.isoformat()
    )

"""
Security utilities for JWT token creation and validation.
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..models.refresh_token import RefreshToken
from ..models.user import User
from .config import settings
from .database import get_db_auth

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in token (should include 'sub' with user_id)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload, or None if invalid

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_auth)
) -> User:
    """
    Get current authenticated user from JWT token.
    This is a FastAPI dependency that can be used in endpoints.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Extract user_id from 'sub' claim
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Query user from database by ID
    # Note: user_id comes from the JWT 'sub' claim (stored during login)
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    # Type narrowing: at this point user is definitely not None
    assert user is not None  # Help type checker understand user is User, not None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user  # Type narrowed by assert above


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    Adds additional check that user is active.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to require admin role.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def create_refresh_token(user_id: str, db: Session) -> str:
    """
    Create a refresh token for a user.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        Refresh token string

    Raises:
        HTTPException: If there's an error creating the token
    """
    try:
        # Generate a random token
        token = secrets.token_urlsafe(32)

        # Set expiration to 7 days
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Create refresh token record in database
        # Convert user_id string to UUID if it's a string
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )

        db.add(refresh_token)
        db.commit()

        return token

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create refresh token: {str(e)}"
        )


def validate_refresh_token(token: str, db: Session) -> Optional[User]:
    """
    Validate a refresh token and return the associated user.

    Args:
        token: Refresh token string
        db: Database session

    Returns:
        User object if valid, None otherwise

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Look up the refresh token in the database
        refresh_token_obj = db.query(RefreshToken).filter(
            RefreshToken.token == token
        ).first()

        if not refresh_token_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check if token is expired
        if not refresh_token_obj.is_valid():
            # Delete expired token
            db.delete(refresh_token_obj)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )

        # Get the user
        user = db.query(User).filter(User.id == refresh_token_obj.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating refresh token: {str(e)}"
        )

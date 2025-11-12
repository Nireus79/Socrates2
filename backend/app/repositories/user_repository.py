"""
User Repository for AUTH database operations.

Handles CRUD operations for users, refresh tokens, and admin roles.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User, RefreshToken, AdminRole, AdminUser
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations (socrates_auth database)."""

    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.get_by_field('email', email)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.get_by_field('username', username)

    def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all active users."""
        return self.list_by_field('is_active', True, skip=skip, limit=limit)

    def get_verified_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all email-verified users."""
        return self.list_by_field('is_verified', True, skip=skip, limit=limit)

    def create_user(
        self,
        username: str,
        hashed_password: str,
        name: str = '',
        surname: str = '',
        email: Optional[str] = None,
        **kwargs
    ) -> User:
        """
        Create new user with required fields.

        Args:
            username: User username (unique)
            hashed_password: Bcrypt hashed password
            name: First name
            surname: Last name
            email: User email (unique, optional)
            **kwargs: Additional fields

        Returns:
            Created User instance
        """
        return self.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            name=name,
            surname=surname,
            **kwargs
        )

    def user_exists_by_email(self, email: str) -> bool:
        """Check if user with email exists."""
        return self.count_by_field('email', email) > 0

    def user_exists_by_username(self, username: str) -> bool:
        """Check if user with username exists."""
        return self.count_by_field('username', username) > 0

    def verify_user(self, user_id: UUID) -> Optional[User]:
        """Mark user as email verified."""
        return self.update(user_id, is_verified=True)

    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """Deactivate user account."""
        return self.update(user_id, is_active=False)

    def activate_user(self, user_id: UUID) -> Optional[User]:
        """Activate user account."""
        return self.update(user_id, is_active=True)

    def update_password(self, user_id: UUID, hashed_password: str) -> Optional[User]:
        """Update user's password hash."""
        return self.update(user_id, hashed_password=hashed_password)

    def set_role(self, user_id: UUID, role: str) -> Optional[User]:
        """Update user's role."""
        return self.update(user_id, role=role)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken operations (socrates_auth database)."""

    def __init__(self, session: Session):
        super().__init__(RefreshToken, session)

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token value."""
        return self.get_by_field('token', token)

    def get_user_tokens(self, user_id: UUID) -> list[RefreshToken]:
        """Get all tokens for a user."""
        return self.list_by_field('user_id', user_id)

    def get_valid_tokens(self, user_id: UUID) -> list[RefreshToken]:
        """Get non-revoked tokens for a user."""
        from datetime import datetime, timezone

        tokens = self.get_user_tokens(user_id)
        now = datetime.now(timezone.utc)
        return [t for t in tokens if t.expires_at > now]

    def revoke_token(self, token_id: UUID) -> bool:
        """Mark token as revoked."""
        token = self.get_by_id(token_id)
        if not token:
            return False

        self.update(token_id, is_revoked=True)
        return True

    def revoke_user_tokens(self, user_id: UUID) -> int:
        """Revoke all tokens for a user."""
        tokens = self.get_user_tokens(user_id)
        for token in tokens:
            self.update(token.id, is_revoked=True)
        return len(tokens)

    def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime, timezone

        all_tokens = self.list(limit=10000)
        now = datetime.now(timezone.utc)

        deleted_count = 0
        for token in all_tokens:
            if token.expires_at <= now:
                self.delete(token.id)
                deleted_count += 1

        return deleted_count


class AdminRoleRepository(BaseRepository[AdminRole]):
    """Repository for AdminRole operations."""

    def __init__(self, session: Session):
        super().__init__(AdminRole, session)

    def get_by_name(self, name: str) -> Optional[AdminRole]:
        """Get role by name."""
        return self.get_by_field('name', name)

    def get_system_roles(self) -> list[AdminRole]:
        """Get all built-in system roles."""
        return self.list_by_field('is_system_role', True, limit=1000)

    def get_custom_roles(self) -> list[AdminRole]:
        """Get all custom (non-system) roles."""
        return self.list_by_field('is_system_role', False, limit=1000)

    def role_exists(self, name: str) -> bool:
        """Check if role name exists."""
        return self.count_by_field('name', name) > 0


class AdminUserRepository(BaseRepository[AdminUser]):
    """Repository for AdminUser (user ↔ role mapping) operations."""

    def __init__(self, session: Session):
        super().__init__(AdminUser, session)

    def get_user_roles(self, user_id: UUID) -> list[AdminUser]:
        """Get all admin roles assigned to a user."""
        return self.list_by_field('user_id', user_id, limit=1000)

    def get_active_admin_users(self) -> list[AdminUser]:
        """Get all active admin assignments (not revoked)."""
        from sqlalchemy import and_

        admin_users = self.session.query(self.model_class).filter(
            self.model_class.revoked_at.is_(None)
        ).all()
        return admin_users

    def is_admin(self, user_id: UUID) -> bool:
        """Check if user has any admin role."""
        return self.count_by_field('user_id', user_id) > 0

    def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        granted_by_id: UUID,
        reason: str = ''
    ) -> AdminUser:
        """Assign admin role to user."""
        return self.create(
            user_id=user_id,
            role_id=role_id,
            granted_by_id=granted_by_id,
            reason=reason
        )

    def revoke_role(self, admin_user_id: UUID) -> Optional[AdminUser]:
        """Revoke admin role assignment."""
        from datetime import datetime, timezone
        return self.update(
            admin_user_id,
            revoked_at=datetime.now(timezone.utc)
        )

    def revoke_user_all_roles(self, user_id: UUID) -> int:
        """Revoke all admin roles for a user."""
        from datetime import datetime, timezone

        admin_users = self.get_user_roles(user_id)
        for admin_user in admin_users:
            self.update(
                admin_user.id,
                revoked_at=datetime.now(timezone.utc)
            )
        return len(admin_users)

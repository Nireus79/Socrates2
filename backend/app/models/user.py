"""
User model for authentication database (socrates_auth).
"""
from sqlalchemy import Column, String, Boolean, Index
from passlib.context import CryptContext

from .base import BaseModel

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    """
    User model - stores in socrates_auth database.

    Fields:
    - id: UUID (inherited from BaseModel)
    - name: First name
    - surname: Last name
    - username: Unique username for login (indexed)
    - email: Optional email address (indexed)
    - hashed_password: Bcrypt hashed password
    - is_active: Whether user account is active
    - is_verified: Whether user email is verified
    - status: Account status (active, inactive, suspended)
    - role: User role (user, admin)
    - created_at: Timestamp (inherited from BaseModel)
    - updated_at: Timestamp (inherited from BaseModel)
    """
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_is_active', 'is_active'),
        Index('idx_users_status', 'status'),
    )

    name = Column(
        String(100),
        nullable=False,
        comment="User first name"
    )

    surname = Column(
        String(100),
        nullable=False,
        comment="User last name"
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique username for login"
    )

    email = Column(
        String(255),
        unique=True,
        nullable=True,
        comment="User email address (optional, unique if provided)"
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment="Whether account is active"
    )

    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default='false',
        comment="Whether email is verified"
    )

    status = Column(
        String(20),
        nullable=False,
        default='active',
        server_default='active',
        comment="Account status: active, inactive, suspended"
    )

    role = Column(
        String(20),
        nullable=False,
        default='user',
        server_default='user',
        comment="User role: user, admin"
    )

    def get_full_name(self) -> str:
        """
        Get user's full name.

        Returns:
            Full name (name + surname)
        """
        return f"{self.name} {self.surname}"

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a plain text password against the hashed password.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(password, self.hashed_password)  # type: ignore[arg-type]  # At runtime it's str, type checker doesn't understand SQLAlchemy

    def to_dict(self, exclude_fields: set = None) -> dict:
        """
        Convert user to dictionary, excluding hashed_password by default.

        Args:
            exclude_fields: Additional fields to exclude

        Returns:
            Dictionary representation without sensitive data
        """
        exclude_fields = exclude_fields or set()
        exclude_fields.add('hashed_password')  # Always exclude password
        return super().to_dict(exclude_fields=exclude_fields)

    def __repr__(self):
        """String representation of user"""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

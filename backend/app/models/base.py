"""
Base model class with common fields.
All models inherit from BaseModel to get:
- UUID primary key
- Automatic timestamps (created_at, updated_at)
- to_dict() serialization method
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declared_attr

from ..core.database import Base


class BaseModel(Base):
    """
    Abstract base class for all database models.

    Provides:
    - UUID primary key (not auto-increment integers)
    - Automatic created_at timestamp
    - Automatic updated_at timestamp (updates on modification)
    - to_dict() method for serialization
    - Automatic string-to-UUID conversion for UUID fields
    """
    __abstract__ = True

    @declared_attr
    def __tablename__(self):
        """Generate table name from class name (lowercase)"""
        return self.__name__.lower()

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key (UUID)"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when record was last updated"
    )

    def __init__(self, **kwargs):
        """
        Initialize model instance, converting string UUIDs to UUID objects.

        This allows models to accept both string and UUID objects for UUID fields,
        making the API more flexible.
        """
        # Convert any string UUIDs to UUID objects
        for key, value in kwargs.items():
            if isinstance(value, str) and key.endswith('_id'):
                # Check if the field is defined as a UUID column
                if hasattr(self.__class__, key):
                    col = getattr(self.__class__, key)
                    # Try to convert to UUID if it looks like one
                    try:
                        kwargs[key] = uuid.UUID(value)
                    except (ValueError, AttributeError):
                        # If conversion fails, keep the original value
                        pass

        super().__init__(**kwargs)

    def to_dict(self, exclude_fields: set = None) -> dict:
        """
        Convert model instance to dictionary.

        Args:
            exclude_fields: Set of field names to exclude (e.g., {'hashed_password'})

        Returns:
            Dictionary representation of model
        """
        exclude_fields = exclude_fields or set()
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert UUID and datetime to string for JSON serialization
                if isinstance(value, uuid.UUID):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()

                result[column.name] = value

        return result

    def __repr__(self):
        """String representation of model"""
        return f"<{self.__class__.__name__}(id={self.id})>"

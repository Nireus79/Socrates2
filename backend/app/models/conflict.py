"""
Conflict model for detecting and resolving specification conflicts.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from ..models.base import BaseModel
import enum


class ConflictType(enum.Enum):
    """Type of conflict detected."""
    TECHNOLOGY = "technology"
    REQUIREMENT = "requirement"
    TIMELINE = "timeline"
    RESOURCE = "resource"


class ConflictSeverity(enum.Enum):
    """Severity level of the conflict."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(enum.Enum):
    """Current status of the conflict."""
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class Conflict(BaseModel):
    """
    Model for specification conflicts.

    Tracks when new specifications conflict with existing ones,
    allowing users to resolve contradictions in requirements.
    """
    __tablename__ = "conflicts"

    project_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    type = Column(Enum(ConflictType), nullable=False)
    description = Column(Text, nullable=False)
    spec_ids = Column(ARRAY(String(36)), nullable=False)  # Array of conflicting spec IDs
    severity = Column(Enum(ConflictSeverity), nullable=False, index=True)
    status = Column(Enum(ConflictStatus), nullable=False, default=ConflictStatus.OPEN, index=True)
    resolution = Column(Text, nullable=True)
    detected_at = Column(DateTime, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_user = Column(Boolean, default=False)

    def to_dict(self):  # TODO Signature of method 'Conflict.to_dict()' does not match signature of the base method in class 'BaseModel'
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'project_id': self.project_id,
            'type': self.type.value if self.type else None,
            'description': self.description,
            'spec_ids': self.spec_ids,
            'severity': self.severity.value if self.severity else None,
            'status': self.status.value if self.status else None,
            'resolution': self.resolution,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by_user': self.resolved_by_user
        })
        return base_dict

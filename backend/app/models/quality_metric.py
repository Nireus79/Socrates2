"""
QualityMetric model for quality control metrics and validation results.
"""
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class QualityMetric(Base):
    """
    QualityMetric model - immutable snapshots of quality metrics.
    Stored in socrates_specs database.

    NOTE: Does NOT inherit from BaseModel because quality metrics are immutable snapshots
    that don't need updated_at. Uses calculated_at instead of created_at for semantic clarity.

    Fields:
    - id: UUID primary key
    - project_id: Foreign key to projects table
    - metric_type: Type of metric (maturity, coverage, conflicts, bias, etc.)
    - metric_value: Numeric value of the metric
    - threshold: Threshold value for pass/fail determination
    - passed: Whether the metric passed quality check
    - details: Additional details as JSON
    - calculated_at: Timestamp when metric was calculated
    """
    __tablename__ = "quality_metrics"
    __table_args__ = (
        Index('idx_quality_metrics_project_id', 'project_id'),
        Index('idx_quality_metrics_type', 'metric_type'),
        Index('idx_quality_metrics_calculated_at', 'calculated_at'),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key (UUID)"
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to projects table"
    )

    metric_type = Column(
        String(100),
        nullable=False,
        comment="Type of metric: maturity, coverage, conflicts, bias, path_optimization"
    )

    metric_value = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Numeric value of the metric"
    )

    threshold = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Threshold value for pass/fail determination"
    )

    passed = Column(
        Boolean,
        nullable=False,
        comment="Whether the metric passed quality check"
    )

    details = Column(
        JSONB,
        nullable=True,
        comment="Additional details as JSON (e.g., coverage gaps, bias patterns)"
    )

    calculated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp when metric was calculated"
    )

    # Relationships
    project = relationship("Project", back_populates="quality_metrics")

    def to_dict(self) -> dict:
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'metric_type': self.metric_type,
            'metric_value': float(self.metric_value),
            'threshold': float(self.threshold) if self.threshold else None,
            'passed': self.passed,
            'details': self.details,
            'calculated_at': self.calculated_at.isoformat()
        }

    def __repr__(self):
        """String representation of quality metric"""
        status = "PASSED" if self.passed else "FAILED"
        return f"<QualityMetric(id={self.id}, type={self.metric_type}, value={self.metric_value}, {status})>"

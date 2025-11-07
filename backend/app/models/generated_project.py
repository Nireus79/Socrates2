"""
GeneratedProject model for storing code generation metadata.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, DECIMAL, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class GenerationStatus(enum.Enum):
    """Status of code generation process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedProject(BaseModel):
    """
    Model for generated project metadata.

    Tracks code generation sessions including version, statistics,
    quality metrics, and download information.
    """
    __tablename__ = "generated_projects"

    project_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    generation_version = Column(Integer, nullable=False, default=1)
    total_files = Column(Integer, nullable=False)
    total_lines = Column(Integer, nullable=False)
    test_coverage = Column(DECIMAL(5, 2), nullable=True)
    quality_score = Column(Integer, nullable=True)
    traceability_score = Column(Integer, nullable=True)  # % of specs implemented
    download_url = Column(Text, nullable=True)
    generation_started_at = Column(DateTime, nullable=False, index=True)
    generation_completed_at = Column(DateTime, nullable=True)
    generation_status = Column(Enum(GenerationStatus), nullable=False, default=GenerationStatus.PENDING, index=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    files = relationship("GeneratedFile", back_populates="generated_project", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'project_id': self.project_id,
            'generation_version': self.generation_version,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'test_coverage': float(self.test_coverage) if self.test_coverage else None,
            'quality_score': self.quality_score,
            'traceability_score': self.traceability_score,
            'download_url': self.download_url,
            'generation_started_at': self.generation_started_at.isoformat() if self.generation_started_at else None,
            'generation_completed_at': self.generation_completed_at.isoformat() if self.generation_completed_at else None,
            'generation_status': self.generation_status.value if self.generation_status else None,
            'error_message': self.error_message
        })
        return base_dict

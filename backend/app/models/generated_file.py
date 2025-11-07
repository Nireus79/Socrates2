"""
GeneratedFile model for storing individual generated files.
"""
from sqlalchemy import Column, String, Integer, Text, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class GeneratedFile(BaseModel):
    """
    Model for individual generated files.

    Each file belongs to a generated project and tracks the
    specifications that led to its creation for traceability.
    """
    __tablename__ = "generated_files"

    generated_project_id = Column(String(36), ForeignKey('generated_projects.id', ondelete='CASCADE'), nullable=False, index=True)
    file_path = Column(String(500), nullable=False, index=True)
    file_content = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    spec_ids = Column(ARRAY(String(36)), nullable=True)  # Specifications that led to this file

    # Relationships
    generated_project = relationship("GeneratedProject", back_populates="files")

    def to_dict(self):
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'generated_project_id': self.generated_project_id,
            'file_path': self.file_path,
            'file_content': self.file_content,
            'file_size': self.file_size,
            'spec_ids': self.spec_ids
        })
        return base_dict

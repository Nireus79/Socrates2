"""
KnowledgeBaseDocument model for uploaded knowledge base documents.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class KnowledgeBaseDocument(Base):
    """
    KnowledgeBaseDocument model - uploaded knowledge base documents per project.
    Stored in socrates_specs database.

    NOTE: Does NOT inherit from BaseModel. Has uploaded_at instead of created_at, no updated_at.

    Fields:
    - id: UUID primary key
    - project_id: Foreign key to projects table
    - user_id: References users(id) in socrates_auth
    - filename: Original filename
    - file_size: File size in bytes
    - content_type: MIME type
    - content: Extracted text content
    - embedding: Sentence embedding as JSON array (384 dimensions)
    - uploaded_at: Timestamp when document was uploaded
    """
    __tablename__ = "knowledge_base_documents"
    __table_args__ = (
        Index('idx_knowledge_base_documents_project_id', 'project_id'),
        Index('idx_knowledge_base_documents_user_id', 'user_id'),
        Index('idx_knowledge_base_documents_uploaded_at', 'uploaded_at'),
    )

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="Foreign key to projects table"
    )

    user_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        comment="References users(id) in socrates_auth"
    )

    filename = Column(
        String(255),
        nullable=False,
        comment="Original filename"
    )

    file_size = Column(
        Integer,
        nullable=False,
        comment="File size in bytes"
    )

    content_type = Column(
        String(100),
        nullable=False,
        comment="MIME type (e.g., application/pdf, text/plain)"
    )

    content = Column(
        Text,
        nullable=True,
        comment="Extracted text content from document"
    )

    embedding = Column(
        Text,
        nullable=True,
        comment="Sentence embedding as JSON array (384 dimensions for semantic search)"
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Timestamp when document was uploaded"
    )

    # Relationships
    project = relationship("Project", back_populates="knowledge_base_documents")

    def to_dict(self, exclude_fields: set = None) -> dict:
        """Convert model instance to dictionary for JSON serialization"""
        result = {
            'id': str(self.id),
            'project_id': str(self.project_id),
            'user_id': str(self.user_id),
            'filename': self.filename,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'uploaded_at': self.uploaded_at.isoformat()
            # Note: content and embedding not included in API response for performance
        }

        if exclude_fields:
            result = {k: v for k, v in result.items() if k not in exclude_fields}

        return result

    def __repr__(self):
        """String representation of knowledge base document"""
        return f"<KnowledgeBaseDocument(id={self.id}, filename='{self.filename}', size={self.file_size})>"

"""Document chunk model for RAG embeddings.

Stores individual chunks of documents with their vector embeddings
for semantic search and RAG operations.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .base import BaseModel


class DocumentChunk(BaseModel):
    """Document chunk with embedding vector.

    Represents a single chunk of a larger document, with its text content
    and corresponding OpenAI embedding vector for semantic search.

    Attributes:
        id: Unique identifier (UUID)
        document_id: Foreign key to parent KnowledgeBaseDocument
        chunk_index: Order of chunk within document (0-indexed)
        content: Text content of the chunk (up to ~500 characters)
        embedding_vector: OpenAI embedding vector (1536 dimensions for text-embedding-3-small)
        created_at: Timestamp when chunk was created
    """
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True)
    document_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_base_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding_vector = Column(ARRAY(FLOAT), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index'),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_index": self.chunk_index,
            "content": self.content,
            "has_embedding": self.embedding_vector is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

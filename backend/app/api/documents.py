"""Document management API endpoints.

Handles document upload, listing, deletion, and semantic search
for knowledge base and RAG integration.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
import uuid

from ..core.security import get_current_active_user
from ..core.database import get_db_auth, get_db_specs
from ..models.user import User
from ..models.project import Project
from ..models.knowledge_base_document import KnowledgeBaseDocument
from ..models.document_chunk import DocumentChunk
from ..services.document_parser import DocumentParser
from ..services.embedding_service import EmbeddingService
from ..services.semantic_search_service import SemanticSearchService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# ===== Request/Response Models =====

class DocumentUploadResponse:
    """Response for document upload."""
    success: bool
    document_id: str
    filename: str
    file_size: int
    chunks: int
    embedding_status: str


class DocumentResponse:
    """Response for document details."""
    id: str
    filename: str
    file_size: int
    content_type: str
    uploaded_at: str
    chunks_count: int


class DocumentChunkResponse:
    """Response for document chunk details."""
    id: str
    document_id: str
    chunk_index: int
    content: str
    has_embedding: bool


class SemanticSearchResponse:
    """Response for semantic search results."""
    query: str
    results: List[Dict]
    count: int
    project_id: str


class RAGContextResponse:
    """Response for RAG augmented context."""
    question: str
    answer: str
    context_chunks: List[Dict]
    augmented_prompt: str
    has_context: bool
    chunk_count: int


# ===== Document Upload Endpoints =====

@router.post("/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db_auth: Session = Depends(get_db_auth),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Upload and process document for knowledge base.

    Parses document, extracts text, creates chunks, and generates embeddings.

    Args:
        project_id: Project ID to associate document with
        file: Document file (PDF, DOCX, Markdown, TXT)
        current_user: Authenticated user
        db_auth: Auth database session
        db_specs: Specs database session

    Returns:
        Upload status with document ID and chunk count

    Raises:
        HTTPException: If project not found, parsing fails, or embedding fails

    Example:
        POST /api/v1/documents/upload?project_id=proj_123
        Content-Type: multipart/form-data

        Response:
        {
            "success": true,
            "document_id": "doc_550e8400-e29b-41d4-a716-446655440000",
            "filename": "requirements.pdf",
            "file_size": 102400,
            "chunks": 45,
            "embedding_status": "completed"
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Read file
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="File is empty")

        # Parse document
        try:
            content, chunks = DocumentParser.parse(file.filename, file_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Document parsing failed: {e}")
            raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")

        if not chunks:
            raise HTTPException(status_code=400, detail="No text extracted from document")

        # Generate embeddings
        embedding_status = "pending"
        try:
            embeddings = await EmbeddingService.embed_chunks(chunks)
            embedding_status = "completed"
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            embeddings = [None] * len(chunks)
            embedding_status = "failed"

        # Save document to database
        doc = KnowledgeBaseDocument(
            project_id=project_id,
            user_id=current_user.id,
            filename=file.filename,
            file_size=len(file_bytes),
            content_type=file.content_type or "application/octet-stream",
            content=content
        )
        db_specs.add(doc)
        db_specs.flush()

        # Save chunks with embeddings
        chunk_records = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_record = DocumentChunk(
                id=chunk_id,
                document_id=doc.id,
                chunk_index=i,
                content=chunk_text,
                embedding_vector=embedding
            )
            db_specs.add(chunk_record)
            chunk_records.append(chunk_record)

        db_specs.commit()

        logger.info(
            f"Uploaded document {file.filename} ({len(file_bytes)} bytes) "
            f"with {len(chunks)} chunks for project {project_id}"
        )

        return {
            "success": True,
            "document_id": str(doc.id),
            "filename": file.filename,
            "file_size": len(file_bytes),
            "chunks": len(chunks),
            "embedding_status": embedding_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


# ===== Document Listing & Deletion =====

@router.get("/{project_id}")
async def list_documents(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """List all documents in a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        List of documents with metadata

    Example:
        GET /api/v1/documents/proj_123

        Response:
        {
            "project_id": "proj_123",
            "documents": [
                {
                    "id": "doc_550e8400...",
                    "filename": "requirements.pdf",
                    "file_size": 102400,
                    "content_type": "application/pdf",
                    "uploaded_at": "2025-11-11T10:30:00Z",
                    "chunks_count": 45
                },
                ...
            ]
        }
    """
    try:
        docs = db_specs.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.project_id == project_id,
            KnowledgeBaseDocument.user_id == current_user.id
        ).all()

        # Single query to get chunk counts for all documents (avoid N+1)
        from sqlalchemy import func
        chunk_counts = db_specs.query(
            DocumentChunk.document_id,
            func.count(DocumentChunk.id).label('chunk_count')
        ).group_by(DocumentChunk.document_id).all()

        # Build map of document_id -> chunk_count
        count_map = {doc_id: count for doc_id, count in chunk_counts}

        documents = []
        for doc in docs:
            chunk_count = count_map.get(doc.id, 0)

            documents.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "file_size": doc.file_size,
                "content_type": doc.content_type,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "chunks_count": chunk_count
            })

        return {
            "project_id": project_id,
            "documents": documents,
            "total": len(documents)
        }

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Delete document and associated chunks.

    Args:
        doc_id: Document ID
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Success status

    Raises:
        HTTPException: If document not found

    Note:
        Document chunks are automatically deleted via cascade foreign key.
    """
    try:
        doc = db_specs.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.id == doc_id,
            KnowledgeBaseDocument.user_id == current_user.id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        filename = doc.filename
        db_specs.delete(doc)
        db_specs.commit()

        logger.info(f"Deleted document {filename} ({doc_id})")

        return {
            "success": True,
            "message": f"Document '{filename}' deleted",
            "document_id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


# ===== Semantic Search Endpoints =====

@router.get("/{project_id}/search")
async def semantic_search(
    project_id: str,
    query: str = Query(..., min_length=3),
    top_k: int = Query(5, ge=1, le=20),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Semantic search across project documents.

    Searches for semantically similar chunks using vector embeddings.

    Args:
        project_id: Project ID
        query: Search query
        top_k: Number of results to return
        threshold: Minimum similarity score (0-1)
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        List of matching chunks with similarity scores

    Example:
        GET /api/v1/documents/proj_123/search?query=authentication&top_k=5

        Response:
        {
            "query": "authentication",
            "results": [
                {
                    "chunk_id": "chunk_123...",
                    "document_id": "doc_456...",
                    "filename": "requirements.pdf",
                    "content": "User authentication...",
                    "similarity": 0.92,
                    "chunk_index": 3
                },
                ...
            ],
            "count": 3
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Perform semantic search
        results = await SemanticSearchService.search(
            query=query,
            project_id=project_id,
            top_k=top_k,
            similarity_threshold=threshold,
            db=db_specs
        )

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "project_id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


# ===== RAG Context Endpoints =====

@router.post("/{project_id}/rag/augment")
async def augment_with_rag(
    project_id: str,
    question: str = Query(..., min_length=3),
    answer: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Augment question-answer pair with RAG context.

    Retrieves relevant document chunks and builds augmented prompt
    for improved spec extraction.

    Args:
        project_id: Project ID
        question: User question about requirement
        answer: User's answer to the question
        top_k: Number of context chunks
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Augmented context with chunks and formatted prompt

    Example:
        POST /api/v1/documents/proj_123/rag/augment
        Query params:
          - question=What is the API rate limit?
          - answer=It should be 1000 requests per minute
          - top_k=5

        Response:
        {
            "question": "What is the API rate limit?",
            "answer": "It should be 1000 requests per minute",
            "context_chunks": [
                {
                    "chunk_id": "...",
                    "filename": "api_spec.pdf",
                    "content": "Rate limiting...",
                    "similarity": 0.89
                },
                ...
            ],
            "augmented_prompt": "...",
            "has_context": true,
            "chunk_count": 3
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Augment with RAG
        result = await RAGService.augment_spec_extraction(
            question=question,
            answer=answer,
            project_id=project_id,
            top_k=top_k,
            db=db_specs
        )

        return {
            "question": result["question"],
            "answer": result["answer"],
            "context_chunks": result["context_chunks"],
            "augmented_prompt": result["augmented_prompt"],
            "has_context": result["has_context"],
            "chunk_count": result.get("chunk_count", 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG augmentation failed: {e}")
        raise HTTPException(status_code=500, detail="RAG augmentation failed")


@router.post("/{project_id}/rag/extract-specs")
async def extract_specs_with_rag(
    project_id: str,
    question: str = Query(..., min_length=3),
    answer: str = Query(..., min_length=1),
    spec_type: str = Query("functional", regex="^(functional|non-functional|performance|security)$"),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs)
) -> Dict:
    """Extract specifications with RAG augmentation.

    Full pipeline: retrieve context → augment prompt → extract specs.

    Args:
        project_id: Project ID
        question: User question
        answer: User answer
        spec_type: Type of spec (functional, non-functional, performance, security)
        top_k: Number of context chunks
        current_user: Authenticated user
        db_specs: Specs database session

    Returns:
        Extracted specifications with context information

    Example:
        POST /api/v1/documents/proj_123/rag/extract-specs
        Query params:
          - question=What should happen when user logs in?
          - answer=Should redirect to dashboard and show welcome message
          - spec_type=functional
          - top_k=5

        Response:
        {
            "specs": [
                {
                    "title": "User Login Redirect",
                    "description": "After successful authentication...",
                    "priority": "high",
                    "measurable": true
                },
                ...
            ],
            "context_count": 3,
            "has_context": true,
            "spec_type": "functional"
        }
    """
    try:
        # Verify project ownership
        project = db_specs.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Extract specs with RAG
        result = await RAGService.extract_specs_with_rag(
            question=question,
            answer=answer,
            project_id=project_id,
            spec_type=spec_type,
            db=db_specs
        )

        return {
            "specs": result.get("specs", []),
            "context_count": result.get("context_count", 0),
            "has_context": result.get("has_context", False),
            "spec_type": spec_type,
            "question": question,
            "answer": answer
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spec extraction with RAG failed: {e}")
        raise HTTPException(status_code=500, detail="Spec extraction failed")

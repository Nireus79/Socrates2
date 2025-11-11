"""Semantic search service using pgvector.

Performs similarity searches across document chunks using
vector embeddings stored in pgvector PostgreSQL extension.
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Semantic search using pgvector similarity.

    Searches for semantically similar document chunks using
    cosine similarity on embedding vectors.
    """

    @staticmethod
    async def search(
        query: str,
        project_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        db: Session = None
    ) -> List[Dict[str, any]]:
        """Search for similar document chunks.

        Embeds the query using OpenAI, then searches pgvector
        for the most similar chunks.

        Args:
            query: Query text to search for
            project_id: Project ID to limit search scope
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            db: Database session

        Returns:
            List of matching chunks with similarity scores:
            [
                {
                    "chunk_id": "...",
                    "document_id": "...",
                    "filename": "...",
                    "content": "...",
                    "similarity": 0.92,
                    "chunk_index": 3
                },
                ...
            ]

        Raises:
            Exception: If embedding or search fails
        """
        from .embedding_service import EmbeddingService
        from ..models.document_chunk import DocumentChunk
        from ..models.knowledge_base_documents import KnowledgeBaseDocument

        try:
            # Embed the query
            query_embedding = await EmbeddingService.embed_text(query)
            if not query_embedding:
                logger.warning(f"Failed to embed query: {query}")
                return []

            # Search for similar chunks
            # Note: PostgreSQL pgvector uses <-> operator for cosine distance
            # Distance 0 = identical, 1 = completely different
            # So similarity = 1 - distance
            results = db.query(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                KnowledgeBaseDocument.filename,
                # Calculate cosine distance (1 - dot product for normalized vectors)
                func.cast(
                    1 - func.sum(
                        DocumentChunk.embedding_vector * query_embedding
                    ) / (
                        func.sqrt(func.sum(
                            func.square(DocumentChunk.embedding_vector)
                        )) *
                        func.sqrt(func.sum(
                            func.square(func.array(query_embedding))
                        ))
                    ),
                    float
                ).label('distance')
            ).join(
                KnowledgeBaseDocument,
                DocumentChunk.document_id == KnowledgeBaseDocument.id
            ).filter(
                KnowledgeBaseDocument.project_id == project_id,
                DocumentChunk.embedding_vector.isnot(None)
            ).order_by(
                'distance'
            ).limit(top_k).all()

            # Convert to result format
            search_results = []
            for chunk_id, doc_id, index, content, filename, distance in results:
                similarity = 1 - distance if distance is not None else 0

                if similarity >= similarity_threshold:
                    search_results.append({
                        "chunk_id": str(chunk_id),
                        "document_id": str(doc_id),
                        "filename": filename,
                        "content": content,
                        "similarity": round(similarity, 3),
                        "chunk_index": index
                    })

            logger.info(
                f"Found {len(search_results)} similar chunks "
                f"for query (top {top_k})"
            )
            return search_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    @staticmethod
    async def search_by_embedding(
        embedding: List[float],
        project_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        db: Session = None
    ) -> List[Dict[str, any]]:
        """Search using pre-computed embedding.

        Useful when you already have an embedding and want to avoid
        re-embedding the query.

        Args:
            embedding: Query embedding vector
            project_id: Project ID to limit search scope
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            db: Database session

        Returns:
            List of matching chunks with similarity scores
        """
        from ..models.document_chunk import DocumentChunk
        from ..models.knowledge_base_documents import KnowledgeBaseDocument

        try:
            # Use same logic as search() but with pre-computed embedding
            results = db.query(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                KnowledgeBaseDocument.filename
            ).join(
                KnowledgeBaseDocument,
                DocumentChunk.document_id == KnowledgeBaseDocument.id
            ).filter(
                KnowledgeBaseDocument.project_id == project_id,
                DocumentChunk.embedding_vector.isnot(None)
            ).order_by(
                DocumentChunk.embedding_vector.op('<->')(embedding)
            ).limit(top_k).all()

            search_results = []
            for chunk_id, doc_id, index, content, filename in results:
                search_results.append({
                    "chunk_id": str(chunk_id),
                    "document_id": str(doc_id),
                    "filename": filename,
                    "content": content,
                    "chunk_index": index
                })

            return search_results

        except Exception as e:
            logger.error(f"Search by embedding failed: {e}")
            raise

    @staticmethod
    def search_sync(
        query: str,
        project_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        db: Session = None
    ) -> List[Dict[str, any]]:
        """Synchronous version of search.

        Args:
            query: Query text
            project_id: Project ID
            top_k: Number of results
            similarity_threshold: Min similarity
            db: Database session

        Returns:
            List of matching chunks
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            SemanticSearchService.search(
                query, project_id, top_k, similarity_threshold, db
            )
        )

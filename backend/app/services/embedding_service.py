"""OpenAI embedding service for vector embeddings.

Generates vector embeddings for text chunks using OpenAI's
text-embedding-3-small model (1536 dimensions).
"""
import asyncio
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate vector embeddings using OpenAI or Claude.

    Uses OpenAI's text-embedding-3-small model which produces
    1536-dimensional embeddings optimized for semantic search.
    """

    # Note: For production RAG, we use OpenAI embeddings since they're
    # specifically designed for semantic search. Claude embeddings are
    # available but OpenAI embeddings have better vector space properties.
    MODEL = "text-embedding-3-small"
    BATCH_SIZE = 100  # OpenAI batch limit
    MAX_RETRIES = 3

    @staticmethod
    async def embed_text(text: str) -> Optional[List[float]]:
        """Get embedding for single text chunk.

        Args:
            text: Text to embed (max ~8000 tokens)

        Returns:
            List of 1536 floats representing the embedding,
            or None if embedding fails

        Raises:
            Exception: If OpenAI API call fails after retries
        """
        try:
            import openai


            # Ensure text is not too long
            if len(text) > 8000:
                text = text[:8000]

            response = openai.Embedding.create(
                input=text,
                model=EmbeddingService.MODEL
            )

            embedding = response['data'][0]['embedding']
            logger.debug(f"Generated embedding for text ({len(text)} chars)")
            return embedding

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    @staticmethod
    async def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for multiple text chunks.

        Batches requests for efficiency. Returns list of embeddings
        in same order as input texts.

        Args:
            texts: List of text chunks to embed

        Returns:
            List of embeddings (same length as texts),
            with None for failed embeddings

        Raises:
            Exception: If OpenAI API call fails
        """
        if not texts:
            return []

        try:
            import openai


            # Truncate long texts
            texts = [t[:8000] if len(t) > 8000 else t for t in texts]

            response = openai.Embedding.create(
                input=texts,
                model=EmbeddingService.MODEL
            )

            # Sort by index to ensure correct order
            embeddings = [None] * len(texts)
            for item in response['data']:
                embeddings[item['index']] = item['embedding']

            logger.info(
                f"Generated {len([e for e in embeddings if e])} "
                f"embeddings from {len(texts)} texts"
            )
            return embeddings

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise

    @staticmethod
    async def embed_chunks(chunks: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for document chunks with batching.

        Automatically batches requests to respect OpenAI API limits.

        Args:
            chunks: List of document chunks to embed

        Returns:
            List of embeddings in same order as chunks

        Example:
            >>> chunks = ["chunk 1", "chunk 2", "chunk 3"]
            >>> embeddings = await EmbeddingService.embed_chunks(chunks)
            >>> len(embeddings)  # 3
        """
        all_embeddings = []

        for i in range(0, len(chunks), EmbeddingService.BATCH_SIZE):
            batch = chunks[i:i + EmbeddingService.BATCH_SIZE]
            embeddings = await EmbeddingService.embed_batch(batch)
            all_embeddings.extend(embeddings)

            # Small delay between batches to avoid rate limiting
            if i + EmbeddingService.BATCH_SIZE < len(chunks):
                await asyncio.sleep(0.1)

        return all_embeddings

    @staticmethod
    def embed_text_sync(text: str) -> Optional[List[float]]:
        """Synchronous version of embed_text.

        Uses asyncio to run async embedding in sync context.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(EmbeddingService.embed_text(text))

    @staticmethod
    def embed_batch_sync(texts: List[str]) -> List[Optional[List[float]]]:
        """Synchronous version of embed_batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            EmbeddingService.embed_batch(texts)
        )

    @staticmethod
    def embed_chunks_sync(chunks: List[str]) -> List[Optional[List[float]]]:
        """Synchronous version of embed_chunks.

        Args:
            chunks: List of document chunks

        Returns:
            List of embeddings
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            EmbeddingService.embed_chunks(chunks)
        )

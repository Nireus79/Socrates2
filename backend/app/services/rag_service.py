"""RAG (Retrieval-Augmented Generation) service for spec extraction.

Enhances specification extraction by retrieving relevant document context
and providing it to Claude for more accurate results.
"""
import logging
from typing import Dict, List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for context-aware spec extraction.

    Uses semantic search to find relevant document chunks,
    then augments Claude prompts with retrieved context.
    """

    @staticmethod
    async def augment_spec_extraction(
        question: str,
        answer: str,
        project_id: str,
        top_k: int = 5,
        db: Session = None
    ) -> Dict[str, any]:
        """Augment spec extraction with retrieved context.

        Retrieves relevant document chunks based on the question/answer,
        then returns augmented context for Claude spec extraction.

        Args:
            question: User question about requirement
            answer: User's answer to the question
            project_id: Project ID for scoped search
            top_k: Number of context chunks to retrieve
            db: Database session

        Returns:
            Dictionary with augmented context:
            {
                "question": "...",
                "answer": "...",
                "context_chunks": [
                    {
                        "filename": "requirements.pdf",
                        "content": "...",
                        "similarity": 0.92
                    },
                    ...
                ],
                "augmented_prompt": "...",
                "has_context": true
            }

        Example:
            >>> result = await RAGService.augment_spec_extraction(
            ...     question="What is the API rate limit?",
            ...     answer="It should be 1000 requests per minute",
            ...     project_id="proj_123",
            ...     db=db
            ... )
            >>> augmented_text = result["augmented_prompt"]
        """
        from .semantic_search_service import SemanticSearchService

        try:
            # Search for relevant chunks using the question
            # (The question is more semantically meaningful than the answer)
            context_chunks = await SemanticSearchService.search(
                query=question,
                project_id=project_id,
                top_k=top_k,
                similarity_threshold=0.6,  # Lower threshold for broader context
                db=db
            )

            # If no results from question, try searching by answer
            if not context_chunks and answer:
                context_chunks = await SemanticSearchService.search(
                    query=answer,
                    project_id=project_id,
                    top_k=top_k,
                    similarity_threshold=0.6,
                    db=db
                )

            # Build augmented prompt
            augmented_prompt = RAGService._build_augmented_prompt(
                question, answer, context_chunks
            )

            result = {
                "question": question,
                "answer": answer,
                "context_chunks": context_chunks,
                "augmented_prompt": augmented_prompt,
                "has_context": len(context_chunks) > 0,
                "chunk_count": len(context_chunks)
            }

            logger.info(
                f"Augmented spec extraction with {len(context_chunks)} "
                f"context chunks"
            )

            return result

        except Exception as e:
            logger.error(f"RAG augmentation failed: {e}")
            # Return unaugmented result on error
            return {
                "question": question,
                "answer": answer,
                "context_chunks": [],
                "augmented_prompt": f"Q: {question}\nA: {answer}",
                "has_context": False,
                "error": str(e)
            }

    @staticmethod
    def _build_augmented_prompt(
        question: str,
        answer: str,
        context_chunks: List[Dict[str, any]]
    ) -> str:
        """Build augmented prompt with context chunks.

        Formats the question, answer, and context chunks into a single
        prompt for spec extraction.

        Args:
            question: User question
            answer: User answer
            context_chunks: Retrieved context chunks

        Returns:
            Formatted augmented prompt string
        """
        prompt = f"""Based on the following information, extract clear, measurable specifications:

Question: {question}
Answer: {answer}

"""

        if context_chunks:
            prompt += "Relevant context from project documents:\n"
            prompt += "=" * 50 + "\n\n"

            for i, chunk in enumerate(context_chunks, 1):
                prompt += f"Context {i} (from {chunk['filename']}, "
                prompt += f"similarity: {chunk['similarity']}):\n"
                prompt += chunk['content']
                prompt += "\n\n"

            prompt += "=" * 50 + "\n"
            prompt += "\nUse the above context to inform your specification extraction.\n"

        return prompt

    @staticmethod
    async def extract_specs_with_rag(
        question: str,
        answer: str,
        project_id: str,
        spec_type: str,
        db: Session = None,
        claude_client = None
    ) -> Dict[str, any]:
        """Extract specifications with RAG augmentation.

        Full pipeline: retrieve context → augment prompt → extract specs.

        Args:
            question: User question
            answer: User answer
            project_id: Project ID for context search
            spec_type: Type of spec to extract (functional, non-functional, etc)
            db: Database session
            claude_client: Anthropic Claude client

        Returns:
            Dictionary with extracted specifications and context:
            {
                "specs": [
                    {"title": "...", "description": "...", ...},
                    ...
                ],
                "context_count": 3,
                "has_context": true,
                "spec_type": "functional"
            }
        """
        from ..agents.orchestrator import get_orchestrator

        try:
            # Step 1: Augment with RAG
            augmented_result = await RAGService.augment_spec_extraction(
                question=question,
                answer=answer,
                project_id=project_id,
                top_k=5,
                db=db
            )

            # Step 2: Extract specs using augmented prompt
            orchestrator = get_orchestrator()
            augmented_prompt = augmented_result["augmented_prompt"]

            # Build spec extraction prompt
            extraction_prompt = f"""
You are a software specification expert. Extract {spec_type} specifications from the following:

{augmented_prompt}

Return a JSON array of specifications with:
- title: Clear, concise specification name
- description: Detailed description
- priority: high|medium|low
- measurable: true|false

If no specifications can be extracted, return an empty array [].
"""

            # Call Claude for extraction
            # (This assumes the orchestrator has a method for this)
            specs = []  # Placeholder - would call Claude here
            try:
                response = orchestrator.extract_specifications(
                    text=extraction_prompt,
                    spec_type=spec_type
                )
                specs = response.get("specifications", [])
            except Exception as e:
                logger.warning(f"Spec extraction failed: {e}")
                specs = []

            result = {
                "specs": specs,
                "context_count": augmented_result.get("chunk_count", 0),
                "has_context": augmented_result.get("has_context", False),
                "spec_type": spec_type,
                "augmented_prompt": augmented_prompt,
                "question": question,
                "answer": answer
            }

            logger.info(
                f"Extracted {len(specs)} {spec_type} specs "
                f"with {augmented_result.get('chunk_count', 0)} context chunks"
            )

            return result

        except Exception as e:
            logger.error(f"RAG spec extraction failed: {e}")
            return {
                "specs": [],
                "context_count": 0,
                "has_context": False,
                "spec_type": spec_type,
                "error": str(e)
            }

    @staticmethod
    def augment_spec_extraction_sync(
        question: str,
        answer: str,
        project_id: str,
        top_k: int = 5,
        db: Session = None
    ) -> Dict[str, any]:
        """Synchronous version of augment_spec_extraction.

        Args:
            question: User question
            answer: User answer
            project_id: Project ID
            top_k: Number of chunks
            db: Database session

        Returns:
            Augmented context dictionary
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            RAGService.augment_spec_extraction(
                question, answer, project_id, top_k, db
            )
        )

    @staticmethod
    def extract_specs_with_rag_sync(
        question: str,
        answer: str,
        project_id: str,
        spec_type: str,
        db: Session = None,
        claude_client = None
    ) -> Dict[str, any]:
        """Synchronous version of extract_specs_with_rag.

        Args:
            question: User question
            answer: User answer
            project_id: Project ID
            spec_type: Spec type
            db: Database session
            claude_client: Claude client

        Returns:
            Extracted specs with context
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            RAGService.extract_specs_with_rag(
                question, answer, project_id, spec_type, db, claude_client
            )
        )

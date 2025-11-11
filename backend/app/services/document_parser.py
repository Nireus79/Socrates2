"""Document parsing service for multiple file formats.

Handles parsing of PDF, DOCX, Markdown, and plain text documents,
with support for text chunking with overlap for RAG.
"""
import logging
from io import BytesIO
from typing import List, Tuple

import chardet

logger = logging.getLogger(__name__)


class DocumentParser:
    """Parse documents in multiple formats (PDF, DOCX, Markdown, TXT)."""

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF file.

        Tries pdfplumber first (better text extraction), falls back to PyPDF2.

        Args:
            file_bytes: Raw PDF file bytes

        Returns:
            Extracted text content

        Raises:
            Exception: If PDF parsing fails
        """
        try:
            import pdfplumber

            pdf = pdfplumber.open(BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            pdf.close()
            return text
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")

            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader

                pdf = PdfReader(BytesIO(file_bytes))
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e2:
                logger.error(f"PDF parsing failed with both methods: {e}, {e2}")
                raise

    @staticmethod
    def parse_docx(file_bytes: bytes) -> str:
        """Extract text from Word document (.docx or .doc).

        Args:
            file_bytes: Raw DOCX file bytes

        Returns:
            Extracted text content

        Raises:
            Exception: If DOCX parsing fails
        """
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(BytesIO(file_bytes))
            text = "\n".join([p.text for p in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"DOCX parsing failed: {e}")
            raise

    @staticmethod
    def parse_markdown(file_bytes: bytes) -> str:
        """Parse Markdown file.

        Preserves Markdown structure for semantic understanding.

        Args:
            file_bytes: Raw Markdown file bytes

        Returns:
            Markdown content as string
        """
        try:
            content = file_bytes.decode('utf-8', errors='ignore')
            return content
        except Exception as e:
            logger.error(f"Markdown parsing failed: {e}")
            raise

    @staticmethod
    def parse_plaintext(file_bytes: bytes) -> str:
        """Parse plain text with automatic encoding detection.

        Uses chardet to detect encoding if UTF-8 fails.

        Args:
            file_bytes: Raw text file bytes

        Returns:
            Text content

        Raises:
            Exception: If text parsing fails
        """
        try:
            # Try UTF-8 first
            return file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            # Fallback to charset detection
            try:
                encoding = chardet.detect(file_bytes).get('encoding', 'utf-8')
                return file_bytes.decode(encoding, errors='ignore')
            except Exception as e:
                logger.error(f"Text parsing failed: {e}")
                raise

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks.

        Creates chunks of specified size with overlap to preserve context
        across chunk boundaries.

        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks (filtered to remove empty chunks)

        Example:
            >>> chunks = DocumentParser.chunk_text(
            ...     "Long text...", chunk_size=500, overlap=50
            ... )
            >>> len(chunks)  # Number of chunks created
        """
        if not text or not text.strip():
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()

            if chunk and len(chunk) > 0:
                chunks.append(chunk)

            # Move start by (chunk_size - overlap) for next iteration
            start = end - overlap

        return chunks

    @staticmethod
    def parse(filename: str, file_bytes: bytes) -> Tuple[str, List[str]]:
        """Parse document in any supported format.

        Detects format by file extension and parses accordingly.
        Automatically chunks the extracted text.

        Args:
            filename: Original filename (used to detect format)
            file_bytes: Raw file bytes

        Returns:
            Tuple of (full_text, text_chunks)

        Raises:
            ValueError: If file format is not supported
            Exception: If parsing fails for other reasons

        Example:
            >>> content, chunks = DocumentParser.parse(
            ...     "document.pdf", pdf_bytes
            ... )
            >>> len(chunks)  # Number of chunks
            >>> content[:100]  # First 100 chars of full content
        """
        ext = filename.lower().split('.')[-1]

        # Parse based on file extension
        if ext == 'pdf':
            content = DocumentParser.parse_pdf(file_bytes)
        elif ext in ['docx', 'doc']:
            content = DocumentParser.parse_docx(file_bytes)
        elif ext in ['md', 'markdown']:
            content = DocumentParser.parse_markdown(file_bytes)
        elif ext in ['txt', 'text']:
            content = DocumentParser.parse_plaintext(file_bytes)
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                "Supported formats: PDF, DOCX, Markdown, TXT"
            )

        # Split into chunks
        chunks = DocumentParser.chunk_text(content)

        logger.info(
            f"Parsed {filename}: {len(content)} chars, "
            f"{len(chunks)} chunks"
        )

        return content, chunks

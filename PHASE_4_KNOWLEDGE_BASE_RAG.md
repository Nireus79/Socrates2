# Phase 4: Knowledge Base & RAG Integration Implementation Guide

**Duration:** 6 weeks (45 days)
**Priority:** HIGH (enables intelligent spec extraction)
**Features:** Document Upload (10d) | Vector Embeddings (12d) | Semantic Search (10d) | RAG Integration (13d)

---

## Overview

Add Retrieval-Augmented Generation (RAG) to improve specification extraction accuracy:
1. Document upload (PDF, DOCX, Markdown)
2. Vector embeddings with OpenAI API
3. Semantic search using pgvector
4. RAG-enhanced specification extraction

**Expected Impact:** 40% improvement in spec extraction accuracy

**Dependencies:**
- Phase 1 Week 0 completed (pgvector migration 026)
- OpenAI API key configured
- DocumentChunk table created

---

## Pre-Implementation Checks

### 1. Verify pgvector Installed
```bash
psql -d socrates_specs -c "SELECT * FROM pg_extension WHERE extname='vector';"
# Should show: vector | 0.5.1 | ...
```

### 2. Verify Embedding Column
```bash
psql -d socrates_specs -c "\d knowledge_base_documents" | grep embedding_vector
# Should show: embedding_vector | vector(1536)
```

### 3. Configure OpenAI API Key
```bash
# Add to .env
OPENAI_API_KEY=sk-proj-xxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## Architecture

### Document Flow
```
User uploads PDF/DOCX/MD
  ↓
Extract text from document
  ↓
Split into 500-char chunks (50 char overlap)
  ↓
Embed each chunk (OpenAI API)
  ↓
Store in knowledge_base_documents + document_chunks
  ↓
Create pgvector IVFFlat index
```

### RAG in Spec Extraction
```
User answers question
  ↓
Embed answer using OpenAI
  ↓
Query pgvector for similar chunks (top-5)
  ↓
Build augmented prompt: [question] + [answer] + [relevant_chunks]
  ↓
Send to Claude for spec extraction
  ↓
Extract specs WITH document context
```

---

## Implementation Steps

### Step 1: Document Parsing Libraries (1 day)

**Install dependencies:**
```bash
pip install pypdf2==4.0.1 pdfplumber==0.11.0 python-docx==0.8.11 markdown==3.5.2 chardet==5.2.0
```

### Step 2: Document Parser Service (3 days)

**File:** `backend/app/services/document_parser.py`

```python
from typing import List, Tuple
import logging
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
import markdown

logger = logging.getLogger(__name__)

class DocumentParser:
    """Parse documents (PDF, DOCX, Markdown, TXT)"""

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF"""
        try:
            # Try pdfplumber first (better text extraction)
            pdf = pdfplumber.open(BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            # Fallback to PyPDF2
            pdf = PyPDF2.PdfReader(BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text

    @staticmethod
    def parse_docx(file_bytes: bytes) -> str:
        """Extract text from Word document"""
        doc = DocxDocument(BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])

    @staticmethod
    def parse_markdown(file_bytes: bytes) -> str:
        """Parse Markdown file"""
        content = file_bytes.decode('utf-8', errors='ignore')
        # Convert to HTML then extract text (preserves structure)
        return content

    @staticmethod
    def parse_plaintext(file_bytes: bytes) -> str:
        """Parse plain text with encoding detection"""
        import chardet
        encoding = chardet.detect(file_bytes)['encoding'] or 'utf-8'
        return file_bytes.decode(encoding, errors='ignore')

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())

            # Move start by (chunk_size - overlap) for next iteration
            start = end - overlap

        return [c for c in chunks if len(c.strip()) > 0]

    @staticmethod
    def parse(filename: str, file_bytes: bytes) -> Tuple[str, List[str]]:
        """Parse any document format"""
        ext = filename.lower().split('.')[-1]

        if ext == 'pdf':
            content = DocumentParser.parse_pdf(file_bytes)
        elif ext in ['docx', 'doc']:
            content = DocumentParser.parse_docx(file_bytes)
        elif ext in ['md', 'markdown']:
            content = DocumentParser.parse_markdown(file_bytes)
        elif ext in ['txt', 'text']:
            content = DocumentParser.parse_plaintext(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Split into chunks
        chunks = DocumentParser.chunk_text(content)

        return content, chunks
```

### Step 3: OpenAI Embedding Service (3 days)

**File:** `backend/app/services/embedding_service.py`

```python
from typing import List
import openai
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

class EmbeddingService:
    """Generate vector embeddings using OpenAI"""

    MODEL = "text-embedding-3-small"  # 1536 dimensions
    BATCH_SIZE = 100  # Process in batches to avoid API limits

    @staticmethod
    async def embed_text(text: str) -> List[float]:
        """Get embedding for single text"""
        try:
            response = openai.Embedding.create(
                input=text,
                model=EmbeddingService.MODEL
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    @staticmethod
    async def embed_batch(texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        if not texts:
            return []

        try:
            response = openai.Embedding.create(
                input=texts,
                model=EmbeddingService.MODEL
            )

            # Sort by index to ensure correct order
            embeddings = [None] * len(texts)
            for item in response['data']:
                embeddings[item['index']] = item['embedding']

            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise

    @staticmethod
    async def embed_chunks(chunks: List[str]) -> List[List[float]]:
        """Embed document chunks with batching"""
        all_embeddings = []

        for i in range(0, len(chunks), EmbeddingService.BATCH_SIZE):
            batch = chunks[i:i + EmbeddingService.BATCH_SIZE]
            embeddings = await EmbeddingService.embed_batch(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings
```

### Step 4: Document Upload API (3 days)

**File:** `backend/app/api/documents.py`

```python
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from ..core.security import get_current_active_user
from ..core.dependencies import get_db_specs
from ..models import KnowledgeBaseDocument, Project
from ..services.document_parser import DocumentParser
from ..services.embedding_service import EmbeddingService
import uuid

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    project_id: str,
    file: UploadFile,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """Upload and process document"""

    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Read file
    file_bytes = await file.read()

    # Parse document
    try:
        content, chunks = DocumentParser.parse(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")

    # Generate embeddings
    try:
        embeddings = await EmbeddingService.embed_batch(chunks)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding service failed")

    # Save to database
    doc = KnowledgeBaseDocument(
        project_id=project_id,
        user_id=current_user.id,
        filename=file.filename,
        file_size=len(file_bytes),
        content_type=file.content_type or "application/octet-stream",
        content=content
    )
    db.add(doc)
    db.flush()  # Get doc.id

    # Save chunks with embeddings
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_record = DocumentChunk(
            document_id=doc.id,
            chunk_index=i,
            content=chunk,
            embedding_vector=embedding
        )
        db.add(chunk_record)

    db.commit()

    return {
        "success": True,
        "document_id": str(doc.id),
        "filename": doc.filename,
        "chunks": len(chunks),
        "size": len(file_bytes)
    }

@router.get("/{project_id}")
async def list_documents(
    project_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """List documents in project"""

    docs = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.project_id == project_id,
        KnowledgeBaseDocument.user_id == current_user.id
    ).all()

    return [d.to_dict() for d in docs]

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """Delete document and chunks"""

    doc = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.id == doc_id,
        KnowledgeBaseDocument.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404)

    # Chunks deleted via cascade
    db.delete(doc)
    db.commit()

    return {"success": True}
```

### Step 5: Semantic Search Service (3 days)

**File:** `backend/app/services/search_service_rag.py`

```python
from typing import List, Optional
from sqlalchemy import func
from ..services.embedding_service import EmbeddingService

class SemanticSearchService:
    """Semantic search using pgvector"""

    @staticmethod
    async def search(
        query: str,
        project_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        db: Session = None
    ) -> List[DocumentChunk]:
        """Find similar chunks using cosine similarity"""

        # Embed query
        query_embedding = await EmbeddingService.embed_text(query)

        # Query pgvector
        chunks = db.query(
            DocumentChunk,
            (1 - (DocumentChunk.embedding_vector.op('<->')(query_embedding))).label('similarity')
        ).join(
            KnowledgeBaseDocument
        ).filter(
            KnowledgeBaseDocument.project_id == project_id,
            (1 - (DocumentChunk.embedding_vector.op('<->')( query_embedding))) >= similarity_threshold
        ).order_by(
            'similarity'
        ).limit(top_k).all()

        return [(chunk, float(sim)) for chunk, sim in chunks]

@router.post("/search")
async def search_documents(
    project_id: str,
    query: str,
    top_k: int = 5,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
):
    """Search documents semantically"""

    results = await SemanticSearchService.search(
        query=query,
        project_id=project_id,
        top_k=top_k,
        db=db
    )

    return {
        "query": query,
        "results": [
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "content": chunk.content,
                "similarity": sim,
                "chunk_index": chunk.chunk_index
            }
            for chunk, sim in results
        ],
        "total": len(results)
    }
```

### Step 6: RAG Integration (4 days)

**Update:** `backend/app/agents/context.py`

```python
# In _extract_specifications() method

# NEW: Retrieve relevant documents
relevant_chunks = await SemanticSearchService.search(
    query=answer,
    project_id=project.id,
    top_k=5,
    db=db
)

# Build augmented prompt with context
context_text = "\n".join([
    f"Document chunk {i}: {chunk.content}"
    for i, (chunk, _) in enumerate(relevant_chunks, 1)
])

augmented_prompt = f"""
Extract specifications from the user's answer.

QUESTION: {question.text}

ANSWER: {answer}

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{context_text}

Extract specifications in JSON format:
{{
    "specifications": [
        {{"key": "...", "value": "...", "category": "...", "content": "..."}},
        ...
    ]
}}
"""

# Extract using Claude with augmented context
response = await self.claude_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    messages=[{"role": "user", "content": augmented_prompt}]
)
```

### Step 7: Testing (2 days)

**Test Steps:**
```bash
# 1. Upload PDF
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "project_id=xxx" \
  -F "file=@spec.pdf"

# 2. Verify chunks created
SELECT COUNT(*) FROM document_chunks WHERE document_id = 'xxx';
# Should show: N chunks

# 3. Test semantic search
curl -X POST http://localhost:8000/api/v1/documents/search \
  -H "Content-Type: application/json" \
  -d '{"project_id": "xxx", "query": "authentication methods"}'

# 4. Verify RAG in context extraction
# Answer question, check if specs extract better with doc context
```

---

## Database Changes

**New Table:** DocumentChunk

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("knowledge_base_documents.id"), ondelete='CASCADE')
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding_vector = Column(Vector(1536))
```

**Migration:** `035_create_document_chunks_table.py`

---

## Cost Analysis

**OpenAI Embedding Costs:**
- Model: text-embedding-3-small (1536 dimensions)
- Rate: $0.02 per 1 million tokens
- Average: 5 tokens per chunk
- Cost per 1000 chunks: $0.10
- Estimated monthly (1M chunks): $100

**Storage:**
- Per chunk: ~500 chars = 1KB
- Per embedding: 1536 floats × 4 bytes = 6KB
- Total: ~7KB per chunk
- 1M chunks = 7GB (~$0.08/month)

**Total:** ~$100/month for 1M documents

---

## Testing Checklist

- [ ] PDF parsing extracts text correctly
- [ ] DOCX parsing works
- [ ] Markdown parsing works
- [ ] Chunks created with correct overlap (50 chars)
- [ ] Embeddings generated (1536 dimensions)
- [ ] pgvector IVFFlat index performs <500ms queries
- [ ] Semantic search returns relevant chunks
- [ ] RAG integration improves spec accuracy
- [ ] Delete cascade removes chunks when doc deleted

---

## Next Phase

Once Phase 4 completes: Move to **Phase 5 (Feature Gaps)** for 27 additional missing features.

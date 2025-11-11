# Knowledge Base & RAG Integration Roadmap for Socrates

**Date:** November 10, 2025
**Status:** Planning Phase - Not Yet Implemented
**Priority:** High (Phase 2+)
**Estimated Impact:** Enables document-based spec extraction, 40% accuracy improvement

---

## Executive Summary

Socrates currently works with **user-provided specifications** only. Adding a Knowledge Base with RAG (Retrieval-Augmented Generation) would enable:
- 📚 **Document Upload**: Users upload design docs, API specs, requirements
- 🔍 **Semantic Search**: Find relevant specifications using natural language
- 🤖 **Context-Aware Extraction**: Claude uses uploaded docs for more accurate specs
- 📊 **Automatic Indexing**: PDF, DOCX, Markdown automatically indexed and searchable

---

## Current State vs Desired State

### ❌ Current Architecture (Text-Only)
```
User Input (typed)
    ↓
Claude API (no context)
    ↓
Extracted Specifications
```

**Limitation:** Claude has no access to existing documentation, only user's typed answers.

### ✅ Desired State (RAG-Powered)
```
User Input (typed)
    ↓
Semantic Search: "Find relevant documents"
    ↓
Vector Database (retrieval)
    ↓
Top 5 relevant document chunks
    ↓
Claude API (with context from docs)
    ↓
More accurate, context-aware specifications
```

---

## What Exists in Codebase

### ✅ Text Search
- `backend/app/api/search.py`: Basic PostgreSQL full-text search
- Searches projects, specifications, questions only
- **Does NOT support documents**

### ❌ Missing Components
1. **Document Upload**: No file upload endpoints
2. **PDF Parsing**: No PDF parsing libraries
3. **Vector Database**: No embeddings or vector search
4. **Document Chunking**: No text splitting/chunking
5. **Embedding Models**: No embedding service
6. **RAG Integration**: No retrieval in spec extraction

---

## Phase 1: Basic Document Upload & Storage

### 🎯 Goals
1. Users can upload documents (PDF, DOCX, TXT, MD)
2. Documents stored and indexed in database
3. Manual viewing of uploaded documents
4. Basic file management

### 📋 Implementation

#### 1. Database Schema
```python
# New models
class Document(Base):
    """Uploaded document metadata."""
    __tablename__ = "documents"

    id: UUID = Column(PG_UUID, primary_key=True)
    project_id: UUID = Column(ForeignKey("projects.id"))
    user_id: UUID = Column(ForeignKey("users.id"))

    file_name: str
    file_type: str  # "pdf", "docx", "txt", "md"
    file_size: int

    content: Text  # Full extracted text
    metadata: JSONB  # {pages: 10, language: "en", ...}

    upload_date: DateTime
    indexed_at: DateTime  # When embedded and indexed


class DocumentChunk(Base):
    """Text chunks for embedding and search."""
    __tablename__ = "document_chunks"

    id: UUID
    document_id: UUID = ForeignKey("documents.id")

    chunk_index: int  # Order in document
    content: Text  # Chunk text
    char_offset: int  # Position in original document

    # Will add embeddings in Phase 2
    embedding: Vector  # 1536-dim for OpenAI embeddings


class DocumentSource(Base):
    """Specification source tracking."""
    __tablename__ = "specification_sources"

    id: UUID
    specification_id: UUID
    document_id: UUID  # Optional: which doc this spec came from
    chunk_id: UUID  # Optional: which chunk
    retrieval_score: float  # Relevance score when retrieved
```

#### 2. Document Upload Endpoint
```python
# POST /api/v1/projects/{project_id}/documents/upload

class DocumentUploadRequest:
    file: UploadFile
    description: Optional[str]
    category: Optional[str]  # "requirements", "design", "api_spec", etc.

# Returns:
{
    "success": bool,
    "document_id": str,
    "file_name": str,
    "file_size": int,
    "pages": int,  # for PDFs
    "estimated_chunks": int,
    "status": "uploaded"  # Will be "indexing" after Phase 2
}
```

#### 3. Document Parsing Service
```python
# app/services/document_parser.py

class DocumentParser:
    """Parse various document formats."""

    async def parse_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF."""
        # Uses: pypdf2 or pdfplumber

    async def parse_docx(self, file_bytes: bytes) -> str:
        """Extract text from Word document."""
        # Uses: python-docx

    async def parse_markdown(self, file_bytes: bytes) -> str:
        """Parse Markdown file."""
        # Extract text + metadata from headers

    async def parse_plaintext(self, file_bytes: bytes) -> str:
        """Plain text."""
        # Decode and validate encoding

    async def chunk_text(self, text: str, chunk_size=500, overlap=50):
        """Split text into overlapping chunks."""
        # Returns: List[DocumentChunk]
```

### 📦 Dependencies to Add
```
# requirements.txt additions
pypdf2==4.0.1           # PDF parsing
pdfplumber==0.11.0      # Alternative PDF (better text extraction)
python-docx==0.8.11     # Word document parsing
markdown==3.5.2         # Markdown parsing
chardet==5.2.0          # Encoding detection
```

### ⏱️ Estimated Time: 1 week

---

## Phase 2: Vector Embeddings & Semantic Search

### 🎯 Goals
1. Generate embeddings for document chunks
2. Store in vector database
3. Enable semantic search
4. Find relevant documents for specs

### 📋 Implementation

#### 1. Embedding Service
```python
# app/services/embedding_service.py

class EmbeddingService:
    """Generate and manage embeddings."""

    async def embed_text(self, text: str) -> List[float]:
        """Get embedding for text (1536 dimensions)."""
        # Uses: OpenAI embeddings API
        # Cost: $0.02 per 1M tokens

    async def embed_chunks(self, chunks: List[str]) -> List[Vector]:
        """Batch embed multiple chunks."""
        # Parallel requests for efficiency

    async def similarity_search(self, query: str, top_k=5) -> List[DocumentChunk]:
        """Find similar chunks using vector similarity."""
        # Uses: pgvector PostgreSQL extension
```

#### 2. Vector Database Setup
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector column to DocumentChunk
ALTER TABLE document_chunks ADD COLUMN embedding vector(1536);

-- Create index for fast search
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

#### 3. Semantic Search Endpoint
```python
# POST /api/v1/projects/{project_id}/documents/search

class DocumentSearchRequest:
    query: str  # "How do we handle authentication?"
    top_k: int = 5
    similarity_threshold: float = 0.7

# Returns:
{
    "query": "How do we handle authentication?",
    "results": [
        {
            "document_id": "...",
            "chunk_id": "...",
            "file_name": "API_Spec_v2.md",
            "content": "...",  # First 300 chars
            "similarity_score": 0.89,
            "source_page": 5  # For PDFs
        },
        ...
    ]
}
```

#### 4. Integrate RAG into Spec Extraction
```python
# In ContextAnalyzerAgent._extract_specifications()

# NEW: Retrieve relevant documents
retrieval_service = self.services.get_retrieval_service()
relevant_chunks = await retrieval_service.search(
    query=answer,  # User's answer to question
    project_id=project.id,
    top_k=5
)

# Build augmented prompt with retrieved context
augmented_prompt = f"""
Extract specifications from user answer.

RELEVANT CONTEXT FROM PROJECT DOCUMENTS:
{format_retrieved_chunks(relevant_chunks)}

QUESTION: {question.text}
ANSWER: {answer}

...extract specs...
"""

# Rest of spec extraction
extracted_specs = await claude.extract(augmented_prompt)
```

### 📦 Dependencies
```
openai>=1.0.0              # Embedding API
pgvector>=0.1.0            # PostgreSQL vector support
langchain>=0.1.0           # Embedding & retrieval utilities (optional)
```

### ⏱️ Estimated Time: 1.5-2 weeks

---

## Phase 3: Advanced RAG Features

### 🎯 Goals
1. Document summarization
2. Automatic categorization
3. Cross-document linking
4. Q&A over documents

### 📋 Features

#### 1. Document Summarization
```python
# POST /api/v1/documents/{doc_id}/summarize

# Uses Claude to summarize document
# Returns: {summary: str, key_points: List[str]}
```

#### 2. Automatic Q&A
```python
# POST /api/v1/documents/{doc_id}/ask

class DocumentQARequest:
    question: str  # "What are the authentication methods?"

# Uses: Retrieval + Claude for accurate answers
# Returns: {answer: str, source_chunks: List[str]}
```

#### 3. Document Linking
```python
# Auto-detect references between documents
# Example: API spec references authentication spec
# Creates: DocumentReference records

class DocumentReference:
    from_doc_id: UUID
    to_doc_id: UUID
    reference_type: str  # "references", "extends", "supersedes"
    chunks: List[str]  # Linking chunks
```

#### 4. Multi-Document RAG
```python
# Retrieve and aggregate from multiple documents
# Example: "Show me all performance requirements"
# Returns: Combined specs from multiple docs
```

### ⏱️ Estimated Time: 2-3 weeks

---

## Phase 4: Automated Knowledge Base

### 🎯 Goals
1. Auto-import from GitHub (clone, parse docs)
2. Auto-index popular libraries (FastAPI docs, React, etc.)
3. Continuous synchronization
4. Version tracking

### 📋 Features

#### 1. GitHub Docs Integration
```python
# POST /api/v1/knowledge-base/import-github

class GitHubImportRequest:
    owner: str
    repo: str
    docs_path: str  # e.g., "docs/", "README.md"
    recursive: bool

# Automatically:
# - Clone repository (or fetch via API)
# - Find and parse all docs
# - Create documents in knowledge base
# - Link to GitHub for version tracking
```

#### 2. Public Library Docs
```python
# Popular libraries to auto-index:
# - FastAPI documentation
# - React documentation
# - PostgreSQL docs
# - Docker documentation
# - AWS documentation

# Create: PredefinedKnowledgeBase
# Users can optionally enable integration
# Docs stored separately (not in project)
# But searchable for context
```

#### 3. Version Tracking
```python
class DocumentVersion:
    document_id: UUID
    version_number: int
    git_ref: str  # branch, tag, or commit hash
    indexed_at: DateTime
    chunk_embeddings_version: int
    # Track which version of embeddings were used
```

### ⏱️ Estimated Time: 3-4 weeks

---

## Implementation Timeline

```
Timeline:
│
├─ Week 1        Phase 1: Document Upload (350 LOC)
├─ Week 2-3      Phase 2: Vector Search (400 LOC)
├─ Week 4-5      Phase 3: Advanced RAG (300 LOC)
└─ Week 6-9      Phase 4: Auto Knowledge Base (500 LOC)

Total: ~1600 LOC, 9 weeks
```

---

## Cost Analysis

### Infrastructure
| Component | Cost | Notes |
|-----------|------|-------|
| PostgreSQL pgvector | Free | Open source extension |
| OpenAI Embeddings | $0.02/1M tokens | ~$20/month for typical use |
| Vector Search | Free | Included in PostgreSQL |
| Document Storage | ~$10/TB/year | S3-equivalent pricing |

### Development
- Phase 1: $5-8k (basic upload)
- Phase 2: $10-15k (embeddings + RAG)
- Phase 3: $8-12k (advanced features)
- Phase 4: $12-18k (automation)
- **Total: ~$40-50k** (or 8-10 weeks @ $5k/week)

---

## Success Metrics

- [  ] Users can upload documents successfully
- [  ] Vector search returns relevant chunks (>80% accuracy)
- [  ] RAG improves spec extraction by >30%
- [  ] Latency <2s for retrieval
- [  ] Support for all major doc formats
- [  ] 95% uptime for embedding service
- [  ] Vector DB scales to 1M+ chunks

---

## Security & Privacy

1. **Data Isolation**: Each project's documents isolated
2. **Access Control**: Only project members can view
3. **Encryption**: Documents encrypted at rest
4. **API Key Security**: OpenAI keys stored securely
5. **Compliance**: Audit logging for document access
6. **PII Handling**: Detection and masking of sensitive data

---

## References

- [OpenAI Embeddings API](https://platform.openai.com/docs/api-reference/embeddings)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [LangChain Documentation](https://docs.langchain.com/)
- [Semantic Search Concepts](https://en.wikipedia.org/wiki/Semantic_search)
- [RAG Survey Paper](https://arxiv.org/abs/2312.10997)

---

## Next Steps

1. **Immediate** (This week): Finalize Phase 1 design
2. **Short-term** (Next 2 weeks): Implement Phase 1 upload
3. **Medium-term** (Weeks 3-4): Phase 2 embeddings
4. **Long-term** (Weeks 5+): Phases 3-4

---

## Open Questions

- Should we use OpenAI embeddings or open-source alternatives?
- How to handle large documents (>100MB)?
- Should we support real-time document indexing?
- How to handle PDFs with images/tables?
- Should embeddings be project-specific or shared?

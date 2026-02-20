"""Text chunking service for memory-safe RAG.

Chunks text into 400-800 token segments with 50 token overlap.
Never loads full documents into memory at query time.
"""
import re
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.services.ai.local_llm import get_embedding_local


# Memory limits
MAX_CHUNK_TOKENS = 800
MIN_CHUNK_TOKENS = 400
OVERLAP_TOKENS = 50
MAX_CHUNKS_RETRIEVED = 8
MAX_PDF_PAGES = 50


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def chunk_text(text: str, max_tokens: int = MAX_CHUNK_TOKENS, overlap: int = OVERLAP_TOKENS) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks of max_tokens size.
    
    Returns list of dicts with chunk_text, token_count, and chunk_index.
    """
    if not text or not text.strip():
        return []
    
    # Split by paragraphs first, then sentences
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        para_tokens = estimate_tokens(para)
        
        # If single paragraph exceeds max, split by sentences
        if para_tokens > max_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)
                
                if current_tokens + sent_tokens > max_tokens and current_chunk:
                    # Save current chunk
                    chunks.append({
                        "chunk_index": chunk_index,
                        "chunk_text": current_chunk.strip(),
                        "token_count": current_tokens,
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-overlap * 4:] if len(current_chunk) > overlap * 4 else ""
                    current_chunk = overlap_text + " " + sentence
                    current_tokens = estimate_tokens(current_chunk)
                else:
                    current_chunk += " " + sentence
                    current_tokens += sent_tokens
        else:
            # Check if adding paragraph exceeds limit
            if current_tokens + para_tokens > max_tokens and current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_text": current_chunk.strip(),
                    "token_count": current_tokens,
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap * 4:] if len(current_chunk) > overlap * 4 else ""
                current_chunk = overlap_text + "\n\n" + para
                current_tokens = estimate_tokens(current_chunk)
            else:
                current_chunk += "\n\n" + para
                current_tokens += para_tokens
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": current_chunk.strip(),
            "token_count": current_tokens,
        })
    
    return chunks


async def ingest_document(
    db: AsyncSession,
    document_id: UUID,
    text: str,
    metadata: Dict[str, Any] = None,
) -> int:
    """Chunk document text and store with embeddings.
    
    Returns number of chunks created.
    """
    # Delete existing chunks for this document
    await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    
    # Chunk the text
    chunks = chunk_text(text)
    
    if not chunks:
        return 0
    
    # Create chunk records with embeddings
    chunk_count = 0
    for chunk_data in chunks:
        # Generate embedding
        try:
            embedding = await get_embedding_local(chunk_data["chunk_text"][:2000])
        except Exception:
            embedding = None
        
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_data["chunk_index"],
            chunk_text=chunk_data["chunk_text"],
            token_count=chunk_data["token_count"],
            embedding=embedding,
            chunk_metadata=metadata or {},
        )
        db.add(chunk)
        chunk_count += 1
    
    await db.commit()
    return chunk_count


async def retrieve_relevant_chunks(
    db: AsyncSession,
    query: str,
    document_ids: List[UUID] = None,
    project_id: UUID = None,
    max_chunks: int = MAX_CHUNKS_RETRIEVED,
) -> List[Dict[str, Any]]:
    """Retrieve top-K relevant chunks using pgvector similarity search.
    
    NEVER loads full index into memory - uses PostgreSQL for search.
    """
    # Get query embedding
    try:
        query_embedding = await get_embedding_local(query[:1000])
    except Exception:
        return []
    
    if query_embedding is None:
        return []
    
    # Build query with vector similarity
    # Using pgvector's <-> operator (L2 distance) or <=> (cosine distance)
    from sqlalchemy import text
    
    if document_ids:
        doc_ids_str = ",".join(f"'{str(d)}'" for d in document_ids)
        sql = text(f"""
            SELECT id, document_id, chunk_text, token_count, chunk_metadata,
                   embedding <=> :query_embedding AS distance
            FROM document_chunks
            WHERE document_id IN ({doc_ids_str})
            AND embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :max_chunks
        """)
    else:
        sql = text("""
            SELECT id, document_id, chunk_text, token_count, chunk_metadata,
                   embedding <=> :query_embedding AS distance
            FROM document_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :max_chunks
        """)
    
    result = await db.execute(
        sql,
        {"query_embedding": str(query_embedding), "max_chunks": max_chunks}
    )
    rows = result.fetchall()
    
    return [
        {
            "id": str(row.id),
            "document_id": str(row.document_id),
            "chunk_text": row.chunk_text,
            "token_count": row.token_count,
            "chunk_metadata": row.chunk_metadata,
            "distance": row.distance,
        }
        for row in rows
    ]

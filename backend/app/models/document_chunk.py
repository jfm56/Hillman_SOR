import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin


class DocumentChunk(Base, TimestampMixin):
    """Memory-safe document chunks for RAG retrieval.
    
    Instead of loading full documents into memory, we store chunked text
    with embeddings and retrieve only the top-K relevant chunks at query time.
    """
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk content (max 800 tokens ≈ ~3200 chars)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    
    # Vector embedding for similarity search (1536 for OpenAI, 768 for nomic-embed-text)
    embedding = Column(Vector(768), nullable=True)
    
    # Extra data for filtering
    chunk_metadata = Column(JSONB, default={})  # page_number, section_type, etc.
    
    # Relationships
    document = relationship("Document", backref="chunks")
